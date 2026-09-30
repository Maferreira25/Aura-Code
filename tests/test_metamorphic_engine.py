#!/usr/bin/env python3
"""Tests for Aura Code Metamorphic Testing Engine."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tools.metamorphic_engine import evaluate_metamorphic_suite, load_metamorphic_suite


class TestMetamorphicEngine(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        (self.root / "tests").mkdir()
        self.target = self.root / "tests" / "test_metamorphic.py"
        self.target.write_text(
            "def test_mr_normalize_idempotent():\n    assert True\n"
            "def test_mr_order_preserved():\n    assert True\n",
            encoding="utf-8",
        )
        self.manifest = self.root / "metamorphic-suite.json"
        self.manifest.write_text(json.dumps({
            "schema_version": "1.0.0",
            "suite_id": "MR-NORMALIZE-001",
            "title": "Normalization relations",
            "requirements": ["REQ-NORMALIZE-001"],
            "test_target": "tests/test_metamorphic.py",
            "relations": [
                {
                    "relation_id": "MR-NORMALIZE-001",
                    "title": "Idempotence",
                    "transformation": "Apply normalization twice.",
                    "expected_relation": "Second result equals first result.",
                    "test_selector": "test_mr_normalize_idempotent"
                },
                {
                    "relation_id": "MR-NORMALIZE-002",
                    "title": "Order preservation",
                    "transformation": "Normalize equivalent ordered inputs.",
                    "expected_relation": "Relative ordering remains unchanged.",
                    "test_selector": "test_mr_order_preserved"
                }
            ],
            "timeout_seconds": 30
        }), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_all_relations_pass(self):
        run = MagicMock(returncode=0, stdout="passed", stderr="")
        with patch("tools.metamorphic_engine.subprocess.run", return_value=run):
            result = evaluate_metamorphic_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["relations_pass"], 2)
        self.assertEqual(result["progression"]["state"], "READY")

    def test_missing_declared_relation_blocks_as_not_tested(self):
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        data["relations"].append({
            "relation_id": "MR-NORMALIZE-003",
            "title": "Missing relation",
            "transformation": "Transform input.",
            "expected_relation": "Output relation holds.",
            "test_selector": "test_mr_missing_relation"
        })
        self.manifest.write_text(json.dumps(data), encoding="utf-8")
        result = evaluate_metamorphic_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "NOT_TESTED")
        self.assertEqual(result["progression"]["state"], "BLOCKED")
        self.assertIn("test_mr_missing_relation", result["missing_selectors"])

    def test_one_violated_relation_fails_suite(self):
        calls = [
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=1, stdout="failed", stderr=""),
        ]
        with patch("tools.metamorphic_engine.subprocess.run", side_effect=calls):
            result = evaluate_metamorphic_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["progression"]["state"], "BLOCKED")
        self.assertEqual(result["relations"][1]["failure_category"], "RELATION_VIOLATED")

    def test_timeout_is_error(self):
        with patch(
            "tools.metamorphic_engine.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["pytest"], timeout=30),
        ):
            result = evaluate_metamorphic_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_runner_collection_error_is_error(self):
        run = MagicMock(returncode=4, stdout="", stderr="collection error")
        with patch("tools.metamorphic_engine.subprocess.run", return_value=run):
            result = evaluate_metamorphic_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "ERROR")

    def test_duplicate_relation_id_is_rejected(self):
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        data["relations"][1]["relation_id"] = data["relations"][0]["relation_id"]
        self.manifest.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_metamorphic_suite(self.manifest)

    def test_target_escape_is_error(self):
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        data["test_target"] = "../outside.py"
        self.manifest.write_text(json.dumps(data), encoding="utf-8")
        result = evaluate_metamorphic_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "ERROR")


class TestMetamorphicSchema(unittest.TestCase):
    def test_schema_is_strict(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "schemas" / "metamorphic-suite.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["properties"]["relations"]["items"]["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
