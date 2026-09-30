#!/usr/bin/env python3
"""Tests for Aura Code Evidence Engine v2."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.assurance_result import build_result
from tools.evidence_engine import (
    create_evidence,
    verify_evidence,
    verify_evidence_file,
    workspace_hash,
    write_evidence,
)


class TestEvidenceEngine(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Aura Test"], cwd=self.root, check=True)
        (self.root / "app.py").write_text(
            "def add(a: int, b: int) -> int:\n    return a + b\n",
            encoding="utf-8",
        )
        (self.root / "policy.json").write_text('{"threshold": 1}\n', encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "baseline"], cwd=self.root, capture_output=True, check=True)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _result(self):
        return build_result(
            check_id="unit-tests",
            status="PASS",
            producer_tool="unittest",
            producer_method="test_execution",
            workspace=str(self.root),
            reason="All tests passed.",
        )

    def test_workspace_hash_changes_with_source(self):
        before = workspace_hash(self.root)
        (self.root / "app.py").write_text(
            "def add(a: int, b: int) -> int:\n    return a - b\n",
            encoding="utf-8",
        )
        after = workspace_hash(self.root)
        self.assertNotEqual(before, after)

    def test_evidence_is_valid_for_exact_state(self):
        evidence = create_evidence(
            self._result(),
            self.root,
            location="memory://test",
            config_paths=[Path("policy.json")],
            ruleset_paths=[Path("policy.json")],
        )
        verification = verify_evidence(
            evidence,
            self.root,
            config_paths=[Path("policy.json")],
            ruleset_paths=[Path("policy.json")],
        )
        self.assertEqual(verification["status"], "VALID")

    def test_source_change_makes_evidence_stale(self):
        evidence = create_evidence(self._result(), self.root, location="memory://test")
        (self.root / "app.py").write_text(
            "def add(a: int, b: int) -> int:\n    return a - b\n",
            encoding="utf-8",
        )
        verification = verify_evidence(evidence, self.root)
        self.assertEqual(verification["status"], "STALE")
        self.assertIn("workspace_hash", verification["stale_fields"])

    def test_config_change_makes_evidence_stale(self):
        evidence = create_evidence(
            self._result(),
            self.root,
            location="memory://test",
            config_paths=[Path("policy.json")],
        )
        (self.root / "policy.json").write_text('{"threshold": 2}\n', encoding="utf-8")
        verification = verify_evidence(
            evidence,
            self.root,
            config_paths=[Path("policy.json")],
        )
        self.assertEqual(verification["status"], "STALE")
        self.assertIn("config_hash", verification["stale_fields"])

    def test_tampered_result_is_invalid(self):
        evidence = create_evidence(self._result(), self.root, location="memory://test")
        evidence["result"]["status"] = "FAIL"
        verification = verify_evidence(evidence, self.root)
        self.assertEqual(verification["status"], "INVALID")

    def test_tampered_record_is_invalid(self):
        evidence = create_evidence(self._result(), self.root, location="memory://test")
        evidence["description"] = "tampered"
        verification = verify_evidence(evidence, self.root)
        self.assertEqual(verification["status"], "INVALID")

    def test_missing_evidence_file_is_missing(self):
        verification = verify_evidence_file(
            self.root / "missing-evidence.json",
            self.root,
        )
        self.assertEqual(verification["status"], "MISSING")

    def test_write_and_verify_evidence_file(self):
        evidence = create_evidence(self._result(), self.root, location="memory://test")
        out = self.root / "_auracode_evidence" / "evidence.json"
        write_evidence(evidence, out)
        verification = verify_evidence_file(out, self.root)
        self.assertEqual(verification["status"], "VALID")

    def test_path_escape_is_rejected(self):
        outside = self.root.parent / "outside-policy.json"
        outside.write_text("{}\n", encoding="utf-8")
        try:
            with self.assertRaises(ValueError):
                create_evidence(
                    self._result(),
                    self.root,
                    location="memory://test",
                    config_paths=[outside],
                )
        finally:
            outside.unlink(missing_ok=True)


class TestEvidenceSchema(unittest.TestCase):
    def test_schema_is_strict_v2(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "schemas" / "evidence.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], "2.0.0")
        self.assertFalse(schema["additionalProperties"])
        self.assertIn("workspace_hash", schema["properties"]["subject"]["required"])


if __name__ == "__main__":
    unittest.main()
