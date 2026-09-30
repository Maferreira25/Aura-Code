#!/usr/bin/env python3
"""Tests for Aura Code requirement/invariant traceability."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.assurance_result import build_result
from tools.evidence_engine import create_evidence, write_evidence
from tools.traceability_engine import evaluate_traceability, evaluate_traceability_file


class TestTraceabilityEngine(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Aura Test"], cwd=self.root, check=True)
        (self.root / "app.py").write_text(
            "def authorize(user):\n    return user == 'admin'\n",
            encoding="utf-8",
        )
        (self.root / "test_app.py").write_text(
            "from app import authorize\nassert authorize('admin')\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "baseline"], cwd=self.root, capture_output=True, check=True)

        result = build_result(
            check_id="auth-test",
            status="PASS",
            producer_tool="unittest",
            producer_method="test_execution",
            workspace=str(self.root),
            reason="Authorization test passed.",
        )
        evidence = create_evidence(result, self.root, location="file://evidence/auth.json")
        self.evidence_path = self.root / "_auracode_evidence" / "auth.json"
        write_evidence(evidence, self.evidence_path)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _manifest(self):
        return {
            "schema_version": "1.0.0",
            "requirements": [
                {
                    "requirement_id": "REQ-AUTH-001",
                    "title": "Administrative authorization",
                    "description": "Only authorized administrators may perform the protected action.",
                    "criticality": "CRITICAL",
                    "source": {
                        "document": "_auracode_sdd/02_RULES.md",
                        "locator": "section 3",
                        "approved": True,
                    },
                    "acceptance_criteria": ["Unauthorized access is denied."],
                    "invariants": ["INV-AUTH-001"],
                    "implementation": ["app.py:authorize"],
                    "tests": ["test_app.py"],
                    "evidence": ["_auracode_evidence/auth.json"],
                }
            ],
            "invariants": [
                {
                    "invariant_id": "INV-AUTH-001",
                    "title": "Authorization always enforced",
                    "statement": "Protected operations must reject callers without authorization.",
                    "criticality": "CRITICAL",
                    "verification_mode": "TEST",
                    "requirements": ["REQ-AUTH-001"],
                    "tests": ["test_app.py"],
                    "checks": [],
                    "evidence": ["_auracode_evidence/auth.json"],
                    "human_assurance_required": False,
                }
            ],
        }

    def test_complete_chain_passes(self):
        result = evaluate_traceability(self._manifest(), self.root)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["progression"]["state"], "READY")
        self.assertEqual(result["requirements"][0]["status"], "PASS")
        self.assertEqual(result["invariants"][0]["status"], "PASS")

    def test_requirement_without_test_is_not_tested_and_blocks(self):
        manifest = self._manifest()
        manifest["requirements"][0]["tests"] = []
        result = evaluate_traceability(manifest, self.root)
        self.assertEqual(result["requirements"][0]["status"], "NOT_TESTED")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_invariant_without_verification_is_not_tested_and_blocks(self):
        manifest = self._manifest()
        manifest["invariants"][0]["tests"] = []
        manifest["invariants"][0]["checks"] = []
        result = evaluate_traceability(manifest, self.root)
        self.assertEqual(result["invariants"][0]["status"], "NOT_TESTED")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_unknown_invariant_link_blocks(self):
        manifest = self._manifest()
        manifest["requirements"][0]["invariants"] = ["INV-MISSING-001"]
        result = evaluate_traceability(manifest, self.root)
        self.assertEqual(result["requirements"][0]["status"], "NOT_TESTED")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_unapproved_requirement_source_blocks(self):
        manifest = self._manifest()
        manifest["requirements"][0]["source"]["approved"] = False
        result = evaluate_traceability(manifest, self.root)
        self.assertEqual(result["requirements"][0]["status"], "NOT_TESTED")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_stale_evidence_blocks_requirement_and_invariant(self):
        manifest = self._manifest()
        (self.root / "app.py").write_text(
            "def authorize(user):\n    return True\n",
            encoding="utf-8",
        )
        result = evaluate_traceability(manifest, self.root)
        self.assertEqual(result["requirements"][0]["status"], "STALE")
        self.assertEqual(result["invariants"][0]["status"], "STALE")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_missing_evidence_is_error_and_blocks(self):
        manifest = self._manifest()
        manifest["requirements"][0]["evidence"] = ["_auracode_evidence/missing.json"]
        result = evaluate_traceability(manifest, self.root)
        self.assertEqual(result["requirements"][0]["status"], "ERROR")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_duplicate_requirement_ids_fail_closed(self):
        manifest = self._manifest()
        manifest["requirements"].append(dict(manifest["requirements"][0]))
        result = evaluate_traceability(manifest, self.root)
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_missing_manifest_file_fails_closed(self):
        result = evaluate_traceability_file(
            self.root / "missing-traceability.json",
            self.root,
        )
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["progression"]["state"], "BLOCKED")


class TestTraceabilitySchemas(unittest.TestCase):
    def test_schemas_are_strict(self):
        root = Path(__file__).resolve().parents[1]
        for name in ("requirement.schema.json", "invariant.schema.json", "traceability.schema.json"):
            schema = json.loads((root / "schemas" / name).read_text(encoding="utf-8"))
            self.assertFalse(schema["additionalProperties"], name)


if __name__ == "__main__":
    unittest.main()
