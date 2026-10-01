import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from validation.tools.record_maturity_evidence import record_entry


class RecordMaturityEvidenceTests(unittest.TestCase):
    def _fixture(self, tmp: str):
        root = Path(tmp)
        (root / "validation").mkdir()
        (root / "GOVERNANCE.md").write_text("adopted governance", encoding="utf-8")
        ledger = {
            "target": "stable-1.0",
            "updated_at": "2026-09-30",
            "criteria": {
                "MAT-10": {
                    "status": "UNKNOWN",
                    "evidence": [],
                    "rationale": "pending",
                }
            },
        }
        ledger_path = root / "validation" / "maturity-evidence.json"
        ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
        package = root / "governance.json"
        package.write_text(
            json.dumps({
                "status": "ADOPTED",
                "human_adoption_attestation": True,
                "adopted_at": "2026-09-30T12:00:00Z",
                "adopted_by": ["human-authority"],
                "roles": {
                    "maintainers": ["m1"],
                    "release_manager": "r1",
                    "security_response": ["s1"],
                },
                "normative_change_rule": "PR review",
                "release_authority_rule": "release manager",
                "security_response_rule": "security team",
                "appeal_rule": "maintainer committee",
                "evidence": ["GOVERNANCE.md"],
            }),
            encoding="utf-8",
        )
        return root, ledger_path, package

    def test_record_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _, package = self._fixture(tmp)
            with self.assertRaises(ValueError):
                record_entry(
                    "MAT-10", package, "reviewer",
                    "2026-09-30T12:00:00Z", "", root, False
                )

    def test_record_writes_valid_pass_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, ledger_path, package = self._fixture(tmp)
            result = record_entry(
                "MAT-10", package, "reviewer",
                "2026-09-30T12:00:00Z", "reviewed", root, True
            )
            self.assertEqual(result["status"], "RECORDED")
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            entry = ledger["criteria"]["MAT-10"]
            self.assertEqual(entry["status"], "PASS")
            self.assertEqual(entry["reviewed_by"], "reviewer")
            self.assertEqual(
                entry["evidence_sha256"],
                hashlib.sha256(package.read_bytes()).hexdigest(),
            )
            self.assertFalse((root / "validation" / "maturity-evidence.candidate.json").exists())

    def test_same_evidence_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _, package = self._fixture(tmp)
            first = record_entry(
                "MAT-10", package, "reviewer",
                "2026-09-30T12:00:00Z", "reviewed", root, True
            )
            second = record_entry(
                "MAT-10", package, "reviewer",
                "2026-09-30T12:00:00Z", "reviewed", root, True
            )
            self.assertEqual(first["status"], "RECORDED")
            self.assertEqual(second["status"], "UNCHANGED")

    def test_different_evidence_cannot_overwrite_existing_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _, package = self._fixture(tmp)
            record_entry(
                "MAT-10", package, "reviewer",
                "2026-09-30T12:00:00Z", "reviewed", root, True
            )
            payload = json.loads(package.read_text(encoding="utf-8"))
            payload["appeal_rule"] = "different rule"
            package.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "different hash"):
                record_entry(
                    "MAT-10", package, "reviewer-2",
                    "2026-10-01T12:00:00Z", "changed", root, True
                )


if __name__ == "__main__":
    unittest.main()
