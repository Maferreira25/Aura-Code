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

    def test_pass_with_existing_local_evidence_allows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_minimal_root(root, "PASS", ["evidence.md"])
            (root / "evidence.md").write_text("verified", encoding="utf-8")
            report = evaluate_maturity(root)
            self.assertTrue(report["ready"])
            self.assertEqual(report["decision"], "ALLOW")

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


if __name__ == "__main__":
    unittest.main()
