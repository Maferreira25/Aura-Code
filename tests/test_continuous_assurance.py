import unittest

from tools.continuous_assurance import compare_snapshots


class ContinuousAssuranceTests(unittest.TestCase):
    def base(self):
        return {
            "source_revision": "old",
            "control_statuses": {"ARC-01": "PASS", "SEC-02": "PASS"},
            "open_findings_by_severity": {"CRITICAL": 0, "HIGH": 0},
            "guarantees": {"architecture": "PASS", "security": "PASS", "test_integrity": "PASS"},
            "violations": {"architecture_violations": 0, "test_integrity": 0},
        }

    def test_stable_posture_allows(self):
        previous = self.base()
        current = dict(previous)
        current["source_revision"] = "new"
        result = compare_snapshots(previous, current)
        self.assertEqual(result["decision"], "ALLOW")
        self.assertFalse(result["regression_detected"])

    def test_pass_to_unknown_blocks(self):
        previous = self.base()
        current = self.base()
        current["control_statuses"] = {"ARC-01": "UNKNOWN", "SEC-02": "PASS"}
        result = compare_snapshots(previous, current)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("control regression ARC-01", "\n".join(result["blockers"]))

    def test_new_high_finding_blocks(self):
        previous = self.base()
        current = self.base()
        current["open_findings_by_severity"] = {"CRITICAL": 0, "HIGH": 1}
        result = compare_snapshots(previous, current)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("new open HIGH findings", "\n".join(result["blockers"]))

    def test_architecture_drift_blocks(self):
        previous = self.base()
        current = self.base()
        current["violations"] = {"architecture_violations": 2, "test_integrity": 0}
        result = compare_snapshots(previous, current)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("architecture_violations increased", "\n".join(result["blockers"]))

    def test_pass_to_valid_waiver_is_visible_warning(self):
        previous = self.base()
        current = self.base()
        current["control_statuses"] = {"ARC-01": "WAIVED", "SEC-02": "PASS"}
        result = compare_snapshots(previous, current)
        self.assertEqual(result["decision"], "ALLOW")
        self.assertTrue(result["regression_detected"])
        self.assertIn("assurance weakened ARC-01", "\n".join(result["warnings"]))

    def test_deterministic_guarantee_regression_blocks(self):
        previous = self.base()
        current = self.base()
        current["guarantees"] = {"architecture": "FAIL", "security": "PASS", "test_integrity": "PASS"}
        result = compare_snapshots(previous, current)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("deterministic guarantee regression architecture", "\n".join(result["blockers"]))


if __name__ == "__main__":
    unittest.main()
