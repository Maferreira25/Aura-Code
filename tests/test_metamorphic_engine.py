#!/usr/bin/env python3
"""Tests for Aura Code Metamorphic Testing Engine."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.metamorphic_engine import evaluate_metamorphic_suite


class TestMetamorphicEngine(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _manifest(self, target="test_metamorphic.py"):
        return {
            "schema_version": "1.0.0",
            "suite_id": "MR-SORT-001",
            "timeout_seconds": 30,
            "relations": [
                {
                    "relation_id": "MR-SORT-IDEMPOTENT",
                    "requirement_id": "REQ-SORT-001",
                    "description": "Sorting an already sorted sequence must not change the result.",
                    "test_target": target,
                }
            ],
        }

    def test_real_metamorphic_relation_passes(self):
        (self.root / "test_metamorphic.py").write_text(
            "# AURA_MR:MR-SORT-IDEMPOTENT\n"
            "def test_mr_sort_idempotent():\n"
            "    values = [3, 1, 2]\n"
            "    once = sorted(values)\n"
            "    assert sorted(once) == once\n",
            encoding="utf-8",
        )
        result = evaluate_metamorphic_suite(self.root, self._manifest())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["progression"]["state"], "READY")
        self.assertEqual(result["relations"][0]["status"], "PASS")

    def test_violated_relation_is_fail(self):
        (self.root / "test_metamorphic.py").write_text(
            "# AURA_MR:MR-SORT-IDEMPOTENT\n"
            "def test_mr_sort_idempotent():\n"
            "    assert sorted([3, 1, 2]) == [3, 2, 1]\n",
            encoding="utf-8",
        )
        result = evaluate_metamorphic_suite(self.root, self._manifest())
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_missing_relation_marker_is_not_tested(self):
        (self.root / "test_metamorphic.py").write_text(
            "def test_something_else():\n    assert True\n",
            encoding="utf-8",
        )
        result = evaluate_metamorphic_suite(self.root, self._manifest())
        self.assertEqual(result["status"], "NOT_TESTED")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_missing_target_is_not_tested(self):
        result = evaluate_metamorphic_suite(self.root, self._manifest("missing.py"))
        self.assertEqual(result["status"], "NOT_TESTED")

    def test_target_escape_is_error(self):
        result = evaluate_metamorphic_suite(self.root, self._manifest("../outside.py"))
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_empty_relations_are_not_tested(self):
        manifest = self._manifest()
        manifest["relations"] = []
        result = evaluate_metamorphic_suite(self.root, manifest)
        self.assertEqual(result["status"], "NOT_TESTED")


class TestMetamorphicSchema(unittest.TestCase):
    def test_schema_is_strict(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "schemas" / "metamorphic-suite.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["properties"]["relations"]["items"]["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
