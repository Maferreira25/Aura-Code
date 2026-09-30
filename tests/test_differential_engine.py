#!/usr/bin/env python3
"""Tests for Aura Code Differential Testing Engine."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.differential_engine import evaluate_differential_suite, load_differential_suite


class TestDifferentialEngine(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        (self.root / "candidate.py").write_text(
            "def transform(value):\n    return value * 2\n",
            encoding="utf-8",
        )
        (self.root / "reference.py").write_text(
            "def transform(value):\n    return value * 2\n",
            encoding="utf-8",
        )
        self.manifest = self.root / "differential-suite.json"
        self.manifest.write_text(json.dumps({
            "schema_version": "1.0.0",
            "suite_id": "DIFF-TRANSFORM-001",
            "title": "Candidate vs reference",
            "requirements": ["REQ-TRANSFORM-001"],
            "adapter": "python-callable",
            "candidate": "candidate:transform",
            "reference": "reference:transform",
            "cases": [1, 2, 5],
            "timeout_seconds": 10
        }), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_matching_implementations_pass(self):
        result = evaluate_differential_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["matches"], 3)
        self.assertEqual(result["progression"]["state"], "READY")

    def test_divergence_is_inconclusive_not_fail(self):
        (self.root / "candidate.py").write_text(
            "def transform(value):\n    return value * 3\n",
            encoding="utf-8",
        )
        result = evaluate_differential_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertEqual(result["progression"]["state"], "BLOCKED")
        self.assertGreater(len(result["divergences"]), 0)

    def test_candidate_runtime_error_is_error(self):
        (self.root / "candidate.py").write_text(
            "def transform(value):\n    raise RuntimeError('boom')\n",
            encoding="utf-8",
        )
        result = evaluate_differential_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_invalid_callable_declaration_is_rejected(self):
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        data["candidate"] = "candidate:transform;rm"
        self.manifest.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_differential_suite(self.manifest)

    def test_same_candidate_and_reference_is_rejected(self):
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        data["reference"] = data["candidate"]
        self.manifest.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_differential_suite(self.manifest)

    def test_timeout_is_error(self):
        with patch(
            "tools.differential_engine.subprocess.run",
            side_effect=__import__("subprocess").TimeoutExpired(cmd=["python"], timeout=10),
        ):
            result = evaluate_differential_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "ERROR")

    def test_args_kwargs_case_shape(self):
        (self.root / "candidate.py").write_text(
            "def add(a, b=0):\n    return a + b\n",
            encoding="utf-8",
        )
        (self.root / "reference.py").write_text(
            "def add(a, b=0):\n    return a + b\n",
            encoding="utf-8",
        )
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        data["candidate"] = "candidate:add"
        data["reference"] = "reference:add"
        data["cases"] = [{"__args__": [2], "__kwargs__": {"b": 3}}]
        self.manifest.write_text(json.dumps(data), encoding="utf-8")
        result = evaluate_differential_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "PASS")


class TestDifferentialSchema(unittest.TestCase):
    def test_schema_is_strict(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "schemas" / "differential-suite.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
