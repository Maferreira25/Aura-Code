import unittest
from pathlib import Path

from validation.tools.p1_matrix import build_matrix
from validation.tools.validate_experiment_evidence import load_results

ROOT = Path(__file__).resolve().parents[1]


class P1MatrixTests(unittest.TestCase):
    def test_repository_matrix_reports_exact_remaining_work(self):
        rows, errors = load_results(ROOT / "validation" / "results")
        self.assertEqual(errors, [])
        matrix = build_matrix(rows)
        self.assertEqual(matrix["total_expected"], 114)
        self.assertEqual(
            matrix["total_complete"] + matrix["total_missing"],
            matrix["total_expected"],
        )
        self.assertGreaterEqual(matrix["total_complete"], 0)
        self.assertGreaterEqual(matrix["total_missing"], 0)

    def test_r2_arm_order_matches_frozen_preregistration(self):
        matrix = build_matrix([])
        entries = [
            item
            for item in matrix["entries"]
            if item["category"] == "automated"
            and item["scenario_id"] == "SEC-AUTHZ-001"
            and item["repetition"] == "r2"
        ]
        ordered = [item["arm"] for item in sorted(entries, key=lambda item: item["execution_order"])]
        self.assertEqual(ordered, ["A1", "A2", "A0"])

    def test_existing_run_is_never_scheduled_as_missing(self):
        rows = [{"run_id": "authz-A0-r1"}]
        matrix = build_matrix(rows)
        entry = next(item for item in matrix["entries"] if item["run_id"] == "authz-A0-r1")
        self.assertEqual(entry["status"], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
