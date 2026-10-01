import unittest

from validation.tools.maturity_queue import (
    build_p2_queue,
    build_p3_queue,
    build_p4_queue,
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
        "study_id": "P2-TEST",
        "preregistered": True,
        "private_or_fresh_split": True,
        "arms": ["A0", "A1", "A2"],
        "scenarios": [
            {"id": f"S{i:02d}", "family": families[i % len(families)]}
            for i in range(30)
        ],
        "repetitions_per_arm": 5,
        "private_split_commitment_sha256": "a" * 64,
        "model_agent_pairings": [
            {
                "model_family": "family-x",
                "model_display_name": "Model X",
                "agent": "Agent X",
                "reasoning_effort": "medium",
            }
        ],
    }


def p3_plan():
    return {
        "study_id": "P3-TEST",
        "preregistered": True,
        "arms": ["A0", "A1", "A2"],
        "model_agent_pairing": {
            "model_display_name": "Model X",
            "agent": "Agent X",
            "reasoning_effort": "medium",
        },
        "benchmarks": [
            {
                "id": "B1",
                "license_verified": True,
                "upstream_revision": "rev1",
                "task_subset_commitment_sha256": "b" * 64,
                "attempts_per_arm": 2,
            },
            {
                "id": "B2",
                "license_verified": True,
                "upstream_revision": "rev2",
                "task_subset_commitment_sha256": "c" * 64,
                "attempts_per_arm": 1,
            },
        ],
        "combine_heterogeneous_scores": False,
    }


def registry():
    return {"benchmarks": [{"id": "B1"}, {"id": "B2"}]}


def p4_plan():
    return {
        "study_id": "P4-TEST",
        "preregistered": True,
        "service_id": "service-x",
        "revision": "abc123",
        "environment": "staging",
        "acceptance_criteria": {
            "load": {
                "success_criteria": "p95 < 250 ms and error rate < 1%",
                "target_rps": 100,
                "duration_minutes": 10,
            },
            "soak": {
                "success_criteria": "no unbounded resource growth",
                "duration_minutes": 60,
            },
            "rollback": {"success_criteria": "rollback completes without data loss"},
            "recovery": {"success_criteria": "service recovers within frozen RTO"},
            "observability": {"success_criteria": "required SLI signals are emitted"},
        },
    }


class MaturityQueueTests(unittest.TestCase):
    def test_p2_queue_exactly_matches_frozen_cartesian_design(self):
        queue = build_p2_queue(p2_plan())
        self.assertEqual(queue["expected"], 30 * 1 * 5 * 3)
        self.assertEqual(queue["complete"], 0)
        self.assertEqual(queue["missing"], 450)
        self.assertEqual(len({item["run_id"] for item in queue["entries"]}), 450)

    def test_p2_queue_marks_only_observed_run_ids_complete(self):
        plan = p2_plan()
        probe = build_p2_queue(plan)["entries"][0]
        result = {"runs": [{"run_id": probe["run_id"]}]}
        queue = build_p2_queue(plan, result)
        self.assertEqual(queue["complete"], 1)
        self.assertEqual(queue["missing"], 449)

    def test_p3_queue_respects_attempts_per_arm_per_benchmark(self):
        queue = build_p3_queue(p3_plan(), registry())
        self.assertEqual(queue["expected"], (2 + 1) * 3)
        self.assertEqual(queue["missing"], 9)
        b1_a0 = [
            x for x in queue["entries"]
            if x["benchmark_id"] == "B1" and x["arm"] == "A0"
        ]
        self.assertEqual(len(b1_a0), 2)

    def test_p3_queue_uses_aggregate_attempt_count_without_claiming_success(self):
        result = {
            "benchmarks": [
                {
                    "id": "B1",
                    "arms": {
                        "A0": {"attempts": 1, "qualified_successes": 0},
                        "A1": {"attempts": 0, "qualified_successes": 0},
                        "A2": {"attempts": 0, "qualified_successes": 0},
                    },
                }
            ]
        }
        queue = build_p3_queue(p3_plan(), registry(), result)
        self.assertEqual(queue["complete"], 1)
        self.assertIn("interpretation remains separate", queue["claim_boundary"])

    def test_p4_queue_tracks_execution_even_when_dimension_failed(self):
        result = {
            "load": {
                "status": "FAIL",
                "evidence": ["validation/evidence/load.json"],
            }
        }
        queue = build_p4_queue(p4_plan(), result)
        self.assertEqual(queue["expected"], 5)
        self.assertEqual(queue["complete"], 1)
        self.assertEqual(queue["missing"], 4)
        load = next(x for x in queue["entries"] if x["dimension"] == "load")
        self.assertEqual(load["status"], "COMPLETE")
        self.assertIn("does not imply", queue["claim_boundary"])

    def test_invalid_plan_is_rejected_instead_of_generating_queue(self):
        bad = p4_plan()
        bad["preregistered"] = False
        with self.assertRaises(ValueError):
            build_p4_queue(bad)


if __name__ == "__main__":
    unittest.main()
