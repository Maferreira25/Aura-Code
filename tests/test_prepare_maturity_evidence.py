import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from validation.tools.prepare_maturity_evidence import prepare_entry


class PrepareMaturityEvidenceTests(unittest.TestCase):
    def _root_with_valid_governance(self, tmp: str) -> tuple[Path, Path]:
        root = Path(tmp)
        (root / "validation").mkdir()
        (root / "GOVERNANCE.md").write_text("adopted", encoding="utf-8")
        package = root / "governance.json"
        package.write_text(
            json.dumps({
                "status": "ADOPTED",
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
        return root, package

    def test_prepare_entry_validates_and_hashes_without_mutating_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, package = self._root_with_valid_governance(tmp)
            result = prepare_entry(
                "MAT-10",
                package,
                "human-reviewer",
                "2026-09-30T12:00:00Z",
                "governance adopted",
                root,
            )
            entry = result["ledger_entry"]
            self.assertEqual(entry["status"], "PASS")
            self.assertEqual(entry["evidence"], ["governance.json"])
            self.assertEqual(
                entry["evidence_sha256"],
                hashlib.sha256(package.read_bytes()).hexdigest(),
            )
            self.assertFalse((root / "validation" / "maturity-evidence.json").exists())
            self.assertIn("does not authenticate", result["claim_boundary"])

    def test_prepare_entry_rejects_invalid_semantic_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "governance.json"
            package.write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                prepare_entry(
                    "MAT-10",
                    package,
                    "reviewer",
                    "2026-09-30T12:00:00Z",
                    "",
                    root,
                )

    def test_prepare_entry_rejects_package_outside_root(self):
        with tempfile.TemporaryDirectory() as tmp_root, tempfile.TemporaryDirectory() as tmp_other:
            root = Path(tmp_root)
            package = Path(tmp_other) / "governance.json"
            package.write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                prepare_entry(
                    "MAT-10",
                    package,
                    "reviewer",
                    "2026-09-30T12:00:00Z",
                    "",
                    root,
                )


if __name__ == "__main__":
    unittest.main()
