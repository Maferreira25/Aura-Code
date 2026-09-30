import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.maturity_gate import _verify_local_evidence, evaluate_maturity
from tools.validate_framework import is_stable_release_version


class MaturityGateTests(unittest.TestCase):
    def _write_minimal_root(self, root: Path, status: str, evidence):
        (root / "validation" / "results").mkdir(parents=True)
        (root / "validation" / "maturity-criteria.json").write_text(
            json.dumps({
                "target": "stable-1.0",
                "criteria": [
                    {"id": "MAT-X", "title": "Synthetic criterion", "mode": "evidence", "required": True}
                ],
            }),
            encoding="utf-8",
        )
        (root / "validation" / "maturity-evidence.json").write_text(
            json.dumps({
                "target": "stable-1.0",
                "criteria": {
                    "MAT-X": {
                        "status": status,
                        "evidence": evidence,
                        "rationale": "synthetic",
                    }
                },
            }),
            encoding="utf-8",
        )

    def test_pass_without_existing_evidence_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_minimal_root(root, "PASS", ["missing.md"])
            report = evaluate_maturity(root)
            self.assertFalse(report["ready"])
            self.assertEqual(report["criteria"][0]["status"], "INVALID_PASS")

    def test_unknown_semantic_criterion_cannot_pass_by_file_existence_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_minimal_root(root, "PASS", ["evidence.json"])
            (root / "evidence.json").write_text("{}", encoding="utf-8")
            report = evaluate_maturity(root)
            self.assertFalse(report["ready"])
            self.assertEqual(report["criteria"][0]["status"], "INVALID_PASS")

    def test_mat10_valid_semantic_evidence_allows_single_criterion_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "validation" / "results").mkdir(parents=True)
            (root / "validation" / "maturity-criteria.json").write_text(
                json.dumps({
                    "target": "stable-1.0",
                    "criteria": [
                        {"id": "MAT-10", "title": "Governance", "mode": "evidence", "required": True}
                    ],
                }),
                encoding="utf-8",
            )
            (root / "validation" / "maturity-evidence.json").write_text(
                json.dumps({
                    "target": "stable-1.0",
                    "criteria": {
                        "MAT-10": {
                            "status": "PASS",
                            "evidence": ["governance.json"],
                            "rationale": "adopted",
                        }
                    },
                }),
                encoding="utf-8",
            )
            (root / "GOVERNANCE.md").write_text("adopted governance", encoding="utf-8")
            governance_payload = {
                "status": "ADOPTED",
                "roles": {
                    "maintainers": ["maintainer-1"],
                    "release_manager": "release-1",
                    "security_response": ["security-1"],
                },
                "normative_change_rule": "PR review",
                "release_authority_rule": "release manager approves",
                "security_response_rule": "security team triages",
                "appeal_rule": "maintainer committee review",
                "evidence": ["GOVERNANCE.md"],
            }
            governance_path = root / "governance.json"
            governance_path.write_text(json.dumps(governance_payload), encoding="utf-8")
            evidence_sha = hashlib.sha256(governance_path.read_bytes()).hexdigest()
            ledger = json.loads((root / "validation" / "maturity-evidence.json").read_text(encoding="utf-8"))
            ledger["criteria"]["MAT-10"].update({
                "reviewed_by": "human-reviewer",
                "reviewed_at": "2026-09-30T00:00:00Z",
                "evidence_sha256": evidence_sha,
            })
            (root / "validation" / "maturity-evidence.json").write_text(json.dumps(ledger), encoding="utf-8")
            report = evaluate_maturity(root)
            self.assertTrue(report["ready"])
            self.assertEqual(report["criteria"][0]["status"], "PASS")

    def test_existing_but_incomplete_mat10_json_is_invalid_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "validation" / "results").mkdir(parents=True)
            (root / "validation" / "maturity-criteria.json").write_text(
                json.dumps({
                    "target": "stable-1.0",
                    "criteria": [
                        {"id": "MAT-10", "title": "Governance", "mode": "evidence", "required": True}
                    ],
                }),
                encoding="utf-8",
            )
            (root / "validation" / "maturity-evidence.json").write_text(
                json.dumps({
                    "target": "stable-1.0",
                    "criteria": {
                        "MAT-10": {
                            "status": "PASS",
                            "evidence": ["governance.json"],
                            "rationale": "claimed",
                        }
                    },
                }),
                encoding="utf-8",
            )
            (root / "governance.json").write_text("{}", encoding="utf-8")
            report = evaluate_maturity(root)
            self.assertFalse(report["ready"])
            self.assertEqual(report["criteria"][0]["status"], "INVALID_PASS")

    def test_external_url_is_not_accepted_as_self_verified_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = _verify_local_evidence(Path(tmp), ["https://example.com/report"])
            self.assertFalse(result["valid"])
            self.assertIn("external/unbounded", result["reason"])

    def test_unknown_required_criterion_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_minimal_root(root, "UNKNOWN", [])
            report = evaluate_maturity(root)
            self.assertFalse(report["ready"])
            self.assertEqual(report["criteria"][0]["status"], "UNKNOWN")

    def test_stable_release_version_detection(self):
        self.assertTrue(is_stable_release_version("1.0.0"))
        self.assertTrue(is_stable_release_version("2.3.4"))
        self.assertFalse(is_stable_release_version("0.3.0.dev0"))
        self.assertFalse(is_stable_release_version("1.0.0rc1"))
        self.assertFalse(is_stable_release_version("1.0.0-dev"))
        self.assertFalse(is_stable_release_version("v1.0.0"))

    def test_mat10_nested_missing_evidence_is_invalid_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "validation" / "results").mkdir(parents=True)
            (root / "validation" / "maturity-criteria.json").write_text(
                json.dumps({
                    "target": "stable-1.0",
                    "criteria": [
                        {"id": "MAT-10", "title": "Governance", "mode": "evidence", "required": True}
                    ],
                }),
                encoding="utf-8",
            )
            (root / "validation" / "maturity-evidence.json").write_text(
                json.dumps({
                    "target": "stable-1.0",
                    "criteria": {
                        "MAT-10": {
                            "status": "PASS",
                            "evidence": ["governance.json"],
                            "rationale": "claimed",
                        }
                    },
                }),
                encoding="utf-8",
            )
            governance_path = root / "governance.json"
            governance_path.write_text(
                json.dumps({
                    "status": "ADOPTED",
                    "roles": {
                        "maintainers": ["maintainer-1"],
                        "release_manager": "release-1",
                        "security_response": ["security-1"],
                    },
                    "normative_change_rule": "PR review",
                    "release_authority_rule": "release manager approves",
                    "security_response_rule": "security team triages",
                    "appeal_rule": "maintainer committee review",
                    "evidence": ["missing-adoption-record.md"],
                }),
                encoding="utf-8",
            )
            evidence_sha = hashlib.sha256(governance_path.read_bytes()).hexdigest()
            ledger = json.loads((root / "validation" / "maturity-evidence.json").read_text(encoding="utf-8"))
            ledger["criteria"]["MAT-10"].update({
                "reviewed_by": "human-reviewer",
                "reviewed_at": "2026-09-30T00:00:00Z",
                "evidence_sha256": evidence_sha,
            })
            (root / "validation" / "maturity-evidence.json").write_text(json.dumps(ledger), encoding="utf-8")
            report = evaluate_maturity(root)
            self.assertFalse(report["ready"])
            self.assertEqual(report["criteria"][0]["status"], "INVALID_PASS")
            self.assertIn("nested evidence files do not exist", report["criteria"][0]["reason"])

    def test_hash_mismatch_is_invalid_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "validation" / "results").mkdir(parents=True)
            (root / "validation" / "maturity-criteria.json").write_text(
                json.dumps({
                    "target": "stable-1.0",
                    "criteria": [
                        {"id": "MAT-10", "title": "Governance", "mode": "evidence", "required": True}
                    ],
                }),
                encoding="utf-8",
            )
            (root / "governance.json").write_text("{}", encoding="utf-8")
            (root / "validation" / "maturity-evidence.json").write_text(
                json.dumps({
                    "target": "stable-1.0",
                    "criteria": {
                        "MAT-10": {
                            "status": "PASS",
                            "evidence": ["governance.json"],
                            "rationale": "claimed",
                            "reviewed_by": "reviewer",
                            "reviewed_at": "2026-09-30T00:00:00Z",
                            "evidence_sha256": "0" * 64,
                        }
                    },
                }),
                encoding="utf-8",
            )
            report = evaluate_maturity(root)
            self.assertFalse(report["ready"])
            self.assertEqual(report["criteria"][0]["status"], "INVALID_PASS")
            self.assertIn("hash mismatch", report["criteria"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
