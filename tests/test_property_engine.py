#!/usr/bin/env python3
"""Tests for Aura Code Property-Based Testing Engine."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.property_engine import (
    discover_property_tests,
    evaluate_property_suite,
)


class TestPropertyEngine(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _manifest(self, target="test_properties.py", seed=12345):
        return {
            "schema_version": "1.0.0",
            "suite_id": "PROP-MATH-001",
            "requirements": ["REQ-MATH-001"],
            "target": target,
            "seed": seed,
            "timeout_seconds": 30,
        }

    def test_discovers_hypothesis_given_properties(self):
        path = self.root / "test_properties.py"
        path.write_text(
            "from hypothesis import given, strategies as st\n"
            "@given(st.integers())\n"
            "def test_identity(x):\n"
            "    assert x == x\n",
            encoding="utf-8",
        )
        result = discover_property_tests(path)
        self.assertTrue(result["complete"])
        self.assertEqual(result["property_count"], 1)
        self.assertEqual(result["properties"][0]["name"], "test_identity")

    def test_real_property_suite_passes_with_seed(self):
        (self.root / "math_mod.py").write_text(
            "def add(a, b):\n    return a + b\n",
            encoding="utf-8",
        )
        (self.root / "test_properties.py").write_text(
            "from hypothesis import given, strategies as st\n"
            "from math_mod import add\n"
            "@given(st.integers(), st.integers())\n"
            "def test_commutative(a, b):\n"
            "    assert add(a, b) == add(b, a)\n",
            encoding="utf-8",
        )
        result = evaluate_property_suite(self.root, self._manifest())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["seed"], 12345)
        self.assertEqual(result["property_count"], 1)
        self.assertEqual(result["progression"]["state"], "READY")

    def test_failing_property_is_fail_not_error(self):
        (self.root / "math_mod.py").write_text(
            "def subtract(a, b):\n    return a - b\n",
            encoding="utf-8",
        )
        (self.root / "test_properties.py").write_text(
            "from hypothesis import given, strategies as st\n"
            "from math_mod import subtract\n"
            "@given(st.integers(), st.integers())\n"
            "def test_commutative(a, b):\n"
            "    assert subtract(a, b) == subtract(b, a)\n",
            encoding="utf-8",
        )
        result = evaluate_property_suite(self.root, self._manifest(seed=42))
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["canonical_result"]["status"], "FAIL")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_declared_target_without_properties_is_not_tested(self):
        (self.root / "test_properties.py").write_text(
            "def test_example():\n    assert True\n",
            encoding="utf-8",
        )
        result = evaluate_property_suite(self.root, self._manifest())
        self.assertEqual(result["status"], "NOT_TESTED")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_target_escape_is_error(self):
        outside = self.root.parent / "outside_property.py"
        outside.write_text(
            "from hypothesis import given, strategies as st\n"
            "@given(st.integers())\n"
            "def test_x(x): assert x == x\n",
            encoding="utf-8",
        )
        try:
            result = evaluate_property_suite(
                self.root,
                self._manifest(target="../outside_property.py"),
            )
            self.assertEqual(result["status"], "ERROR")
            self.assertEqual(result["progression"]["state"], "BLOCKED")
        finally:
            outside.unlink(missing_ok=True)

    def test_timeout_is_error(self):
        (self.root / "test_properties.py").write_text(
            "from hypothesis import given, strategies as st\n"
            "@given(st.integers())\n"
            "def test_x(x): assert x == x\n",
            encoding="utf-8",
        )
        with patch(
            "tools.property_engine.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["pytest"], timeout=1),
        ):
            result = evaluate_property_suite(self.root, self._manifest())
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_output_is_digest_only(self):
        (self.root / "test_properties.py").write_text(
            "from hypothesis import given, strategies as st\n"
            "@given(st.integers())\n"
            "def test_x(x): assert x == x\n",
            encoding="utf-8",
        )
        fake = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="counterexample secret data",
            stderr="sensitive traceback",
        )
        with patch("tools.property_engine.subprocess.run", return_value=fake):
            result = evaluate_property_suite(self.root, self._manifest())
        serialized = json.dumps(result)
        self.assertNotIn("counterexample secret data", serialized)
        self.assertNotIn("sensitive traceback", serialized)
        self.assertEqual(result["status"], "FAIL")


class TestPropertySchema(unittest.TestCase):
    def test_schema_is_strict(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "schemas" / "property-suite.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
