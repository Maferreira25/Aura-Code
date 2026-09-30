#!/usr/bin/env python3
"""Tests for Aura Code deterministic fuzzing engine."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.fuzz_engine import evaluate_fuzz_suite, generate_inputs, load_fuzz_suite


class TestFuzzEngine(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        (self.root / "target.py").write_text(
            "def parse(value):\n"
            "    if isinstance(value, str) and 'CRASHME' in value:\n"
            "        raise RuntimeError('boom')\n"
            "    return value\n",
            encoding="utf-8",
        )
        self.manifest = self.root / "fuzz-suite.json"
        self.manifest.write_text(json.dumps({
            "schema_version": "1.0.0",
            "suite_id": "FUZZ-PARSER-001",
            "title": "Parser fuzz",
            "requirements": ["REQ-PARSER-001"],
            "adapter": "python-callable",
            "target": "target:parse",
            "corpus": ["hello"],
            "seed": 12345,
            "iterations": 5,
            "timeout_seconds": 2
        }), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_input_generation_is_reproducible(self):
        a = generate_inputs([{"x": 1}, "abc"], 42, 10)
        b = generate_inputs([{"x": 1}, "abc"], 42, 10)
        self.assertEqual(a, b)

    def test_safe_target_passes(self):
        result = evaluate_fuzz_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["progression"]["state"], "READY")
        self.assertEqual(result["seed"], 12345)

    def test_crashing_generated_input_is_fail_and_preserved(self):
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        data["corpus"] = ["CRASHME"]
        data["iterations"] = 1
        self.manifest.write_text(json.dumps(data), encoding="utf-8")
        with patch("tools.fuzz_engine.generate_inputs", return_value=["CRASHME"]):
            result = evaluate_fuzz_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["progression"]["state"], "BLOCKED")
        self.assertEqual(result["findings"][0]["input"], "CRASHME")
        self.assertEqual(result["findings"][0]["outcome"], "CRASH")

    def test_timeout_is_finding_and_fail(self):
        with patch("tools.fuzz_engine.generate_inputs", return_value=["x"]), patch(
            "tools.fuzz_engine._invoke", return_value=("TIMEOUT", "")
        ):
            result = evaluate_fuzz_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["findings"][0]["outcome"], "TIMEOUT")

    def test_evaluator_error_is_error(self):
        with patch("tools.fuzz_engine.generate_inputs", return_value=["x"]), patch(
            "tools.fuzz_engine._invoke", return_value=("EVALUATOR_ERROR", "runner failed")
        ):
            result = evaluate_fuzz_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_invalid_callable_is_rejected(self):
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        data["target"] = "target:parse;rm"
        self.manifest.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_fuzz_suite(self.manifest)

    def test_empty_corpus_is_rejected(self):
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        data["corpus"] = []
        self.manifest.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_fuzz_suite(self.manifest)


class TestFuzzSchema(unittest.TestCase):
    def test_schema_is_strict(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "schemas" / "fuzz-suite.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
