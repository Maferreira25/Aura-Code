#!/usr/bin/env python3
"""Tests for Aura Code Differential Testing Engine."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tools.differential_engine import evaluate_differential_suite


class TestDifferentialEngine(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.ref = self.root / "reference.py"
        self.cand = self.root / "candidate.py"
        self.ref.write_text(
            "import json, sys\n"
            "x = json.load(sys.stdin)\n"
            "print(json.dumps({'value': x['a'] + x['b']}))\n",
            encoding="utf-8",
        )
        self.cand.write_text(self.ref.read_text(encoding="utf-8"), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _manifest(self):
        return {
            "schema_version": "1.0.0",
            "suite_id": "DIFF-MATH-001",
            "requirements": ["REQ-MATH-001"],
            "reference_command": [sys.executable, "reference.py"],
            "candidate_command": [sys.executable, "candidate.py"],
            "cases": [{"a": 1, "b": 2}, {"a": -5, "b": 8}],
            "timeout_seconds": 10,
        }

    def test_matching_implementations_pass(self):
        result = evaluate_differential_suite(self.root, self._manifest())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["divergences_count"], 0)
        self.assertEqual(result["progression"]["state"], "READY")

    def test_divergence_is_inconclusive_not_fail(self):
        self.cand.write_text(
            "import json, sys\n"
            "x = json.load(sys.stdin)\n"
            "print(json.dumps({'value': x['a'] - x['b']}))\n",
            encoding="utf-8",
        )
        result = evaluate_differential_suite(self.root, self._manifest())
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertGreater(result["divergences_count"], 0)
        self.assertEqual(result["progression"]["state"], "BLOCKED")
        serialized = json.dumps(result)
        self.assertNotIn('"a": 1', serialized)
        self.assertIn("case_digest", serialized)

    def test_invalid_candidate_json_is_error(self):
        self.cand.write_text("print('not-json')\n", encoding="utf-8")
        result = evaluate_differential_suite(self.root, self._manifest())
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["side"], "candidate")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_reference_failure_is_error(self):
        self.ref.write_text("raise SystemExit(3)\n", encoding="utf-8")
        result = evaluate_differential_suite(self.root, self._manifest())
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["side"], "reference")

    def test_empty_cases_are_not_tested(self):
        manifest = self._manifest()
        manifest["cases"] = []
        result = evaluate_differential_suite(self.root, manifest)
        self.assertEqual(result["status"], "NOT_TESTED")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_commands_are_argument_arrays_not_shell_strings(self):
        manifest = self._manifest()
        manifest["candidate_command"] = "python candidate.py"
        result = evaluate_differential_suite(self.root, manifest)
        self.assertEqual(result["status"], "ERROR")


class TestDifferentialSchema(unittest.TestCase):
    def test_schema_is_strict(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "schemas" / "differential-suite.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
