import json
import unittest
from pathlib import Path

from validation.tools.maturity_readiness import build_readiness, validate_workplan


ROOT = Path(__file__).resolve().parents[1]


class MaturityReadinessTests(unittest.TestCase):
    def test_workplan_covers_exact_maturity_criteria(self):
        criteria = json.loads((ROOT / "validation" / "maturity-criteria.json").read_text(encoding="utf-8"))
        workplan = json.loads((ROOT / "validation" / "maturity-workplan.json").read_text(encoding="utf-8"))
        ids = [item["id"] for item in criteria["criteria"]]
        self.assertEqual(validate_workplan(workplan, ids), [])
        self.assertEqual({item["id"] for item in workplan["criteria"]}, set(ids))

    def test_workplan_is_not_a_pass_source(self):
        workplan = json.loads((ROOT / "validation" / "maturity-workplan.json").read_text(encoding="utf-8"))
        self.assertIn("never a source of PASS", workplan["policy"])
        for item in workplan["criteria"]:
            self.assertTrue(item["human_required"])
            self.assertNotIn("status", item)

    def test_current_readiness_is_fail_closed_and_matches_p1_matrix(self):
        report = build_readiness(ROOT)
        self.assertFalse(report["ready"])
        self.assertEqual(report["decision"], "BLOCK")
        self.assertGreater(report["remaining_count"], 0)
        mat01 = next(item for item in report["remaining"] if item["id"] == "MAT-01")
        self.assertEqual(mat01["p1"]["total_expected"], report["p1"]["total_expected"])
        self.assertEqual(mat01["p1"]["total_missing"], report["p1"]["total_missing"])
        self.assertIn("does not", report["claim_boundary"])

    def test_independence_is_explicit_for_external_decision_criteria(self):
        workplan = json.loads((ROOT / "validation" / "maturity-workplan.json").read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in workplan["criteria"]}
        for cid in ("MAT-06", "MAT-08", "MAT-09", "MAT-10"):
            self.assertTrue(by_id[cid]["independence_required"], cid)


if __name__ == "__main__":
    unittest.main()
