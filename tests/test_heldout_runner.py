#!/usr/bin/env python3
"""Tests for generalized held-out evaluation."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.heldout_runner import evaluate_held_out


class FakeRunner:
    backend_name = "fake"

    def __init__(self, response, *, strong=True, mutate=None):
        self.response = response
        self.is_strong_isolation = strong
        self.mutate = mutate

    def run_tests(self, workspace, test_dir, **kwargs):
        if self.mutate:
            self.mutate(Path(workspace), Path(test_dir))
        return dict(self.response)


class TestHeldOutRunner(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.workspace = self.root / "candidate"
        self.suite = self.root / "protected-suite"
        self.workspace.mkdir()
        self.suite.mkdir()
        (self.workspace / "app.py").write_text(
            "def add(a, b):\n    return a + b\n",
            encoding="utf-8",
        )
        self._write_suite()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write_suite(self, test_content=None):
        (self.suite / "suite.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "suite_id": "HO-AUTH-001",
                    "title": "Protected acceptance",
                    "category": "SECURITY",
                    "requirements": ["REQ-AUTH-001"],
                    "test_glob": "test*.py",
                    "disclosure": "REQUIREMENT_ONLY",
                    "timeout_seconds": 10,
                }
            ),
            encoding="utf-8",
        )
        (self.suite / "test_hidden.py").write_text(
            test_content
            or "import unittest\n"
            "from app import add\n"
            "class Hidden(unittest.TestCase):\n"
            "    def test_hidden_boundary(self):\n"
            "        self.assertEqual(add(2, 3), 5)\n",
            encoding="utf-8",
        )

    def test_passing_held_out_suite_allows_progression(self):
        fake = FakeRunner(
            {
                "returncode": 0,
                "stdout": "secret test name must not leak",
                "stderr": "",
                "timed_out": False,
                "backend": "fake",
                "oracle_tampering_detected": False,
            }
        )
        with patch("tools.heldout_runner.get_runner", return_value=fake):
            result = evaluate_held_out(self.workspace, self.suite)

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["progression"]["state"], "READY")
        self.assertNotIn("stdout", result)
        self.assertNotIn("stderr", result)
        self.assertNotIn("secret test name", json.dumps(result))

    def test_failed_held_out_suite_blocks_without_details(self):
        fake = FakeRunner(
            {
                "returncode": 1,
                "stdout": "Hidden.test_secret_case",
                "stderr": "AssertionError: expected secret",
                "timed_out": False,
                "backend": "fake",
                "oracle_tampering_detected": False,
            }
        )
        with patch("tools.heldout_runner.get_runner", return_value=fake):
            result = evaluate_held_out(self.workspace, self.suite)

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failure_category"], "HELD_OUT_TEST_FAILURE")
        self.assertEqual(result["progression"]["state"], "BLOCKED")
        serialized = json.dumps(result)
        self.assertNotIn("Hidden.test_secret_case", serialized)
        self.assertNotIn("expected secret", serialized)

    def test_missing_suite_is_not_tested(self):
        result = evaluate_held_out(self.workspace, self.root / "missing-suite")
        self.assertEqual(result["status"], "NOT_TESTED")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_suite_inside_workspace_is_rejected(self):
        internal = self.workspace / "validation" / "held_out"
        internal.mkdir(parents=True)
        result = evaluate_held_out(self.workspace, internal)
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_suite_without_matching_tests_is_not_tested(self):
        (self.suite / "test_hidden.py").unlink()
        result = evaluate_held_out(self.workspace, self.suite)
        self.assertEqual(result["status"], "NOT_TESTED")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_timeout_is_error(self):
        fake = FakeRunner(
            {
                "returncode": 124,
                "stdout": "",
                "stderr": "timeout",
                "timed_out": True,
                "backend": "fake",
                "oracle_tampering_detected": False,
            }
        )
        with patch("tools.heldout_runner.get_runner", return_value=fake):
            result = evaluate_held_out(self.workspace, self.suite)
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["failure_category"], "TIMEOUT")

    def test_oracle_tampering_is_fail(self):
        fake = FakeRunner(
            {
                "returncode": 101,
                "stdout": "",
                "stderr": "ORACLE_TAMPERING_DETECTED",
                "timed_out": False,
                "backend": "fake",
                "oracle_tampering_detected": True,
            }
        )
        with patch("tools.heldout_runner.get_runner", return_value=fake):
            result = evaluate_held_out(self.workspace, self.suite)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failure_category"], "ORACLE_TAMPERING")

    def test_workspace_side_effect_is_error(self):
        def mutate_workspace(workspace, _test_dir):
            (workspace / "tampered.txt").write_text("changed", encoding="utf-8")

        fake = FakeRunner(
            {
                "returncode": 0,
                "stdout": "",
                "stderr": "",
                "timed_out": False,
                "backend": "fake",
                "oracle_tampering_detected": False,
            },
            mutate=mutate_workspace,
        )
        with patch("tools.heldout_runner.get_runner", return_value=fake):
            result = evaluate_held_out(self.workspace, self.suite)
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["failure_category"], "EVALUATION_SIDE_EFFECT")

    def test_suite_mutation_is_error(self):
        def mutate_suite(_workspace, test_dir):
            (test_dir / "test_hidden.py").write_text("# tampered\n", encoding="utf-8")

        fake = FakeRunner(
            {
                "returncode": 0,
                "stdout": "",
                "stderr": "",
                "timed_out": False,
                "backend": "fake",
                "oracle_tampering_detected": False,
            },
            mutate=mutate_suite,
        )
        with patch("tools.heldout_runner.get_runner", return_value=fake):
            result = evaluate_held_out(self.workspace, self.suite)
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["failure_category"], "EVALUATOR_INTEGRITY")


class TestHeldOutSchema(unittest.TestCase):
    def test_schema_is_strict(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "schemas" / "held-out-suite.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
