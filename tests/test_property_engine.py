#!/usr/bin/env python3
"""Tests for Aura Code Property-Based Testing Engine."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tools.property_engine import evaluate_property_suite


class TestPropertyEngine(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        (self.root / "tests").mkdir()
        self.manifest = self.root / "property-suite.json"
        self.manifest.write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "suite_id": "PROP-ROUNDTRIP-001",
                    "title": "Round trip",
                    "framework": "hypothesis",
                    "requirements": ["REQ-SERIALIZE-001"],
                    "test_target": "tests/test_properties.py",
                    "seed": 424242,
                    "timeout_seconds": 30,
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write_property(self):
        (self.root / "tests" / "test_properties.py").write_text(
            "from hypothesis import given, strategies as st\n"
            "@given(st.integers())\n"
            "def test_roundtrip(value):\n"
            "    assert int(str(value)) == value\n",
            encoding="utf-8",
        )

    def test_missing_property_target_is_not_tested(self):
        with patch("tools.property_engine.importlib.util.find_spec", return_value=object()):
            result = evaluate_property_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "NOT_TESTED")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_plain_example_test_does_not_count_as_property_testing(self):
        (self.root / "tests" / "test_properties.py").write_text(
            "def test_example():\n    assert 1 + 1 == 2\n",
            encoding="utf-8",
        )
        with patch("tools.property_engine.importlib.util.find_spec", return_value=object()):
            result = evaluate_property_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "NOT_TESTED")

    def test_missing_hypothesis_adapter_is_not_tested(self):
        self._write_property()
        with patch("tools.property_engine.importlib.util.find_spec", return_value=None):
            result = evaluate_property_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "NOT_TESTED")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_passing_property_suite_passes_with_recorded_seed(self):
        self._write_property()
        run = MagicMock(returncode=0, stdout="1 passed", stderr="")
        with patch("tools.property_engine.importlib.util.find_spec", return_value=object()), patch(
            "tools.property_engine.subprocess.run", return_value=run
        ) as runner:
            result = evaluate_property_suite(self.root, self.manifest)

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["seed"], 424242)
        self.assertEqual(result["progression"]["state"], "READY")
        command = runner.call_args.args[0]
        self.assertIn("--hypothesis-seed=424242", command)

    def test_falsified_property_is_fail(self):
        self._write_property()
        run = MagicMock(returncode=1, stdout="Falsifying example", stderr="")
        with patch("tools.property_engine.importlib.util.find_spec", return_value=object()), patch(
            "tools.property_engine.subprocess.run", return_value=run
        ):
            result = evaluate_property_suite(self.root, self.manifest)

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failure_category"], "PROPERTY_FALSIFIED")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_timeout_is_error(self):
        self._write_property()
        with patch("tools.property_engine.importlib.util.find_spec", return_value=object()), patch(
            "tools.property_engine.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["pytest"], timeout=30),
        ):
            result = evaluate_property_suite(self.root, self.manifest)

        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_runner_collection_error_is_error(self):
        self._write_property()
        run = MagicMock(returncode=4, stdout="", stderr="collection error")
        with patch("tools.property_engine.importlib.util.find_spec", return_value=object()), patch(
            "tools.property_engine.subprocess.run", return_value=run
        ):
            result = evaluate_property_suite(self.root, self.manifest)

        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["failure_category"], "RUNNER_ERROR")


class TestPropertySchema(unittest.TestCase):
    def test_schema_is_strict(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "schemas" / "property-suite.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
