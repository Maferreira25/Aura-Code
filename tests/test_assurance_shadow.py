#!/usr/bin/env python3
"""Shadow-mode integration tests for canonical assurance continuity."""

import json
import tempfile
import unittest
from pathlib import Path

from tools.assess import assess_data
from tools.audit import audit_workspace


class TestAuditCanonicalShadow(unittest.TestCase):
    def test_missing_target_never_emits_canonical_pass(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "does-not-exist"
            result = audit_workspace(missing)

        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(len(result["canonical_results"]), 7)
        self.assertTrue(all(item["status"] == "NOT_TESTED" for item in result["canonical_results"]))
        self.assertFalse(any(item["status"] == "PASS" for item in result["canonical_results"]))

    def test_unverified_guarantees_remain_not_tested(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "app.py").write_text(
                "def add(a: int, b: int) -> int:\n    return a + b\n",
                encoding="utf-8",
            )
            result = audit_workspace(root)

        canonical = {item["check_id"]: item["status"] for item in result["canonical_results"]}
        self.assertEqual(canonical["test-integrity"], "NOT_TESTED")
        self.assertEqual(canonical["architecture"], "NOT_TESTED")
        self.assertEqual(canonical["requirements-ambiguity"], "NOT_TESTED")


class TestAssessCanonicalStates(unittest.TestCase):
    def _root_with_single_control_profile(self, td: str) -> Path:
        root = Path(td)
        profiles = root / "profiles"
        profiles.mkdir()
        (profiles / "al1.json").write_text(
            json.dumps(
                {
                    "framework_version": "test",
                    "assurance_level": "AL1",
                    "included_controls": ["INT-01"],
                }
            ),
            encoding="utf-8",
        )
        return root

    def test_inconclusive_blocks_profile(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root_with_single_control_profile(td)
            result = assess_data(
                {
                    "project": "p",
                    "assurance_level": "AL1",
                    "controls": {"INT-01": {"status": "INCONCLUSIVE"}},
                },
                root=root,
                verify_evidence_paths=False,
            )

        self.assertFalse(result["success"])
        self.assertEqual(result["blocked"][0]["status"], "INCONCLUSIVE")

    def test_stale_blocks_profile(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root_with_single_control_profile(td)
            result = assess_data(
                {
                    "project": "p",
                    "assurance_level": "AL1",
                    "controls": {"INT-01": {"status": "STALE"}},
                },
                root=root,
                verify_evidence_paths=False,
            )

        self.assertFalse(result["success"])
        self.assertEqual(result["blocked"][0]["status"], "STALE")

    def test_waiver_is_explicit_but_does_not_satisfy_profile(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root_with_single_control_profile(td)
            result = assess_data(
                {
                    "project": "p",
                    "assurance_level": "AL1",
                    "controls": {
                        "INT-01": {
                            "status": "WAIVED",
                            "rationale": "Temporary accepted risk.",
                            "waiver": "WAIVER-001",
                        }
                    },
                },
                root=root,
                verify_evidence_paths=False,
            )

        self.assertFalse(result["success"])
        self.assertEqual(result["waived"], ["INT-01"])

    def test_not_applicable_requires_rationale(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root_with_single_control_profile(td)
            invalid = assess_data(
                {
                    "project": "p",
                    "assurance_level": "AL1",
                    "controls": {"INT-01": {"status": "NOT_APPLICABLE"}},
                },
                root=root,
                verify_evidence_paths=False,
            )
            valid = assess_data(
                {
                    "project": "p",
                    "assurance_level": "AL1",
                    "controls": {
                        "INT-01": {
                            "status": "NOT_APPLICABLE",
                            "rationale": "Control does not apply to this target.",
                        }
                    },
                },
                root=root,
                verify_evidence_paths=False,
            )

        self.assertFalse(invalid["success"])
        self.assertIn("INT-01", invalid["invalid_na"])
        self.assertTrue(valid["success"])


if __name__ == "__main__":
    unittest.main()
