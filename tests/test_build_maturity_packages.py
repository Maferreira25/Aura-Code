import json
import tempfile
import unittest
from pathlib import Path

from validation.tools.build_maturity_packages import (
    build_burden_package,
    build_p2_package,
    build_replication_package,
)


def p2_plan():
    families = [
        "security",
        "data-integrity",
        "supply-chain",
        "evaluator-integrity",
        "architecture",
        "reliability",
    ]
    return {
        "study_id": "P2-X",
        "preregistered": True,
        "private_or_fresh_split": True,
        "arms": ["A0", "A1", "A2"],
        "repetitions_per_arm": 5,
        "private_split_commitment_sha256": "a" * 64,
        "model_agent_pairings": [{
            "model_family": "family",
            "model_display_name": "Model X",
            "agent": "Agent X",
            "reasoning_effort": "medium",
        }],
        "scenarios": [
            {"id": f"S{i:02d}", "family": families[i % len(families)]}
            for i in range(30)
        ],
    }


class BuildMaturityPackagesTests(unittest.TestCase):
    def test_p2_builder_does_not_invent_missing_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / "p2-plan.json"
            plan_path.write_text(json.dumps(p2_plan()), encoding="utf-8")
            results = root / "results"
            results.mkdir()
            (results / "one.json").write_text(
                json.dumps({
                    "run_id": "p2-x-s00-p1-a0-r1",
                    "arm": "A0",
                    "scenario_id": "S00",
                    "model_display_name": "Model X",
                    "agent": "Agent X",
                    "reasoning_effort": "medium",
                    "qualified_success": True,
                    "public_tests_passed": True,
                    "protected_tests_passed": True,
                    "evaluator_integrity": True,
                }),
                encoding="utf-8",
            )
            package = build_p2_package(root, plan_path, results)
            self.assertFalse(package["completed"])
            self.assertEqual(package["expected_attempts"], 450)
            self.assertEqual(package["builder"]["observed"], 1)
            self.assertEqual(package["builder"]["missing"], 449)
            self.assertEqual(package["validation"]["status"], "INVALID")
            self.assertEqual(len(package["runs"]), 1)

    def test_burden_builder_uses_observed_metrics_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            results = root / "results"
            results.mkdir()
            for arm, seconds, interventions in [
                ("A0", 10, 0),
                ("A1", 12, 1),
                ("A2", 14, 1),
            ]:
                (results / f"{arm}.json").write_text(
                    json.dumps({
                        "run_id": f"{arm}-1",
                        "scenario_id": "S1",
                        "arm": arm,
                        "elapsed_seconds": seconds,
                        "human_interventions": interventions,
                    }),
                    encoding="utf-8",
                )
            calibration = root / "calibration.json"
            calibration.write_text(
                json.dumps({
                    "true_positive": 10,
                    "true_negative": 10,
                    "false_positive": 1,
                    "false_negative": 2,
                }),
                encoding="utf-8",
            )
            package = build_burden_package(results, calibration)
            self.assertEqual(package["validation"]["status"], "VALID")
            a2 = package["validation"]["burden"]["by_arm"]["A2"]["metrics"]
            self.assertEqual(a2["elapsed_seconds"]["observed"], 1)
            self.assertEqual(a2["cost_usd"]["observed"], 0)

    def test_replication_builder_rejects_invalid_p2_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = root / "bad-p2.json"
            bad.write_text(json.dumps({
                "study": "P2",
                "completed": True,
                "runs": [],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid completed P2 package"):
                build_replication_package(root, [bad])


if __name__ == "__main__":
    unittest.main()
