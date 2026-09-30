import unittest

from validation.tools.maturity_studies import (
    analyze_inter_rater,
    cohen_kappa,
    validate_burden_error_result,
    validate_governance_1_0,
    validate_independent_security_audit,
    validate_multilang_qualification,
    validate_p2_plan,
    validate_p2_result,
    validate_p3_plan,
    validate_p3_result,
    validate_p4_result,
    validate_replication_result,
)


def p2_scenarios():
    families = [
        "security",
        "data-integrity",
        "supply-chain",
        "evaluator-integrity",
        "architecture",
        "reliability",
    ]
    return [
        {"id": f"S{i:02d}", "family": families[i % len(families)]}
        for i in range(30)
    ]


def registry():
    return {
        "benchmarks": [
            {"id": "B1", "name": "One"},
            {"id": "B2", "name": "Two"},
        ]
    }


class MaturityStudiesTests(unittest.TestCase):
    def test_valid_p2_plan_is_not_a_result(self):
        plan = {
            "study_id": "P2-X",
            "preregistered": True,
            "private_or_fresh_split": True,
            "arms": ["A0", "A1", "A2"],
            "scenarios": p2_scenarios(),
            "repetitions_per_arm": 5,
            "private_split_commitment_sha256": "a" * 64,
            "model_agent_pairings": [
                {
                    "model_family": "model-family",
                    "model_display_name": "Model X",
                    "agent": "Agent X",
                    "reasoning_effort": "medium",
                }
            ],
        }
        result = validate_p2_plan(plan)
        self.assertEqual(result["status"], "VALID")
        self.assertEqual(result["expected_attempts"], 450)

        as_result = validate_p2_result(plan)
        self.assertEqual(as_result["status"], "INVALID")
        self.assertFalse(as_result["completed"])

    def test_p2_result_requires_full_expected_attempt_count(self):
        runs = []
        for arm in ("A0", "A1", "A2"):
            for index in range(30):
                runs.append({
                    "run_id": f"{arm}-{index}",
                    "arm": arm,
                    "scenario_id": f"S{index:02d}",
                    "model_display_name": "Model X",
                    "agent": "Agent X",
                    "qualified_success": True,
                    "public_tests_passed": True,
                    "protected_tests_passed": True,
                    "evaluator_integrity": True,
                })
        data = {
            "study": "P2",
            "preregistered": True,
            "private_or_fresh_split": True,
            "preregistration_sha256": "b" * 64,
            "completed": True,
            "expected_attempts": 450,
            "runs": runs,
        }
        result = validate_p2_result(data)
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("P2 incomplete: observed 90/450 attempts", result["errors"])

    def test_p2_result_rejects_inconsistent_qualified_success(self):
        runs = []
        for arm in ("A0", "A1", "A2"):
            for index in range(30):
                runs.append({
                    "run_id": f"{arm}-{index}",
                    "arm": arm,
                    "scenario_id": f"S{index:02d}",
                    "model_display_name": "Model X",
                    "agent": "Agent X",
                    "qualified_success": True,
                    "public_tests_passed": True,
                    "protected_tests_passed": True,
                    "evaluator_integrity": True,
                })
        runs[0]["protected_tests_passed"] = False
        data = {
            "study": "P2",
            "preregistered": True,
            "private_or_fresh_split": True,
            "preregistration_sha256": "b" * 64,
            "completed": True,
            "expected_attempts": len(runs),
            "runs": runs,
        }
        result = validate_p2_result(data)
        self.assertEqual(result["status"], "INVALID")
        self.assertTrue(any("Qualified Success formula mismatch" in e for e in result["errors"]))

    def test_p3_plan_requires_license_revision_and_commitment(self):
        plan = {
            "preregistered": True,
            "benchmarks": [
                {
                    "id": "B1",
                    "license_verified": True,
                    "upstream_revision": "abc123",
                    "task_subset_commitment_sha256": "c" * 64,
                }
            ],
            "combine_heterogeneous_scores": False,
        }
        result = validate_p3_plan(plan, registry())
        self.assertEqual(result["status"], "VALID")
        self.assertIn("single benchmark family", result["warnings"][0])

    def test_p3_result_requires_two_completed_benchmark_families(self):
        data = {
            "study": "P3",
            "preregistered": True,
            "benchmarks": [
                {
                    "id": "B1",
                    "license_verified": True,
                    "upstream_revision": "abc",
                    "task_subset_commitment_sha256": "d" * 64,
                    "attempts": 10,
                    "completed": True,
                    "arms": {"A0": {}, "A1": {}, "A2": {}},
                }
            ],
        }
        result = validate_p3_result(data, registry())
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("at least two distinct benchmark families", "\n".join(result["errors"]))

    def test_valid_p4_result_requires_all_operational_dimensions(self):
        evidence = ["report.json"]
        data = {
            "service_id": "svc",
            "revision": "abc",
            "load": {"status": "PASS", "evidence": evidence, "target_rps": 100},
            "soak": {"status": "PASS", "evidence": evidence, "duration_minutes": 60},
            "rollback": {"status": "PASS", "evidence": evidence},
            "recovery": {"status": "PASS", "evidence": evidence},
            "observability": {"status": "PASS", "evidence": evidence},
        }
        result = validate_p4_result(data)
        self.assertEqual(result["status"], "VALID")
        self.assertTrue(result["operational_complete"])

    def test_inter_rater_computes_agreement_without_claiming_correctness(self):
        data = {
            "assessors": [{"id": "r1"}, {"id": "r2"}],
            "ratings": [
                {"control_id": "C1", "assessor_id": "r1", "rating": "PASS"},
                {"control_id": "C1", "assessor_id": "r2", "rating": "PASS"},
                {"control_id": "C2", "assessor_id": "r1", "rating": "FAIL"},
                {"control_id": "C2", "assessor_id": "r2", "rating": "FAIL"},
                {"control_id": "C3", "assessor_id": "r1", "rating": "PASS"},
                {"control_id": "C3", "assessor_id": "r2", "rating": "FAIL"},
            ],
        }
        result = analyze_inter_rater(data)
        self.assertEqual(result["status"], "VALID")
        self.assertEqual(result["paired_controls"], 3)
        self.assertAlmostEqual(result["percent_agreement"], 2 / 3)
        self.assertIn("do not prove control correctness", result["claim_boundary"])

    def test_cohen_kappa_rejects_mismatched_vectors(self):
        with self.assertRaises(ValueError):
            cohen_kappa(["PASS"], ["PASS", "FAIL"])

    def test_replication_requires_distinct_model_agent_pairings(self):
        data = {
            "pairings": [
                {
                    "model_display_name": "Model X",
                    "agent": "Agent X",
                    "study_id": "P2-1",
                    "a0_qs_rate": 0.5,
                    "a2_qs_rate": 0.7,
                    "completed": True,
                },
                {
                    "model_display_name": "Model X",
                    "agent": "Agent X",
                    "study_id": "P2-2",
                    "a0_qs_rate": 0.6,
                    "a2_qs_rate": 0.8,
                    "completed": True,
                },
            ]
        }
        result = validate_replication_result(data)
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("distinct model/agent identities", "\n".join(result["errors"]))

    def test_burden_error_result_requires_measurement_not_zeros_by_default(self):
        data = {
            "results": [
                {"arm": "A0", "elapsed_seconds": 10, "human_interventions": 0},
                {"arm": "A1", "elapsed_seconds": 12, "human_interventions": 1},
                {"arm": "A2", "elapsed_seconds": 14, "human_interventions": 1},
            ],
            "error_calibration": {
                "true_positive": 10,
                "true_negative": 10,
                "false_positive": 1,
                "false_negative": 2,
            },
        }
        result = validate_burden_error_result(data)
        self.assertEqual(result["status"], "VALID")
        self.assertEqual(
            result["burden"]["by_arm"]["A2"]["metrics"]["cost_usd"]["observed"],
            0,
        )

    def test_multilang_qualification_uses_preregistered_thresholds(self):
        data = {
            "preregistered": True,
            "revision": "abc123",
            "acceptance_thresholds": {
                "min_recall": 0.8,
                "max_false_positive_rate": 0.2,
            },
            "languages": {
                "python": {
                    "cases": 20,
                    "true_positive": 9,
                    "true_negative": 9,
                    "false_positive": 1,
                    "false_negative": 1,
                    "parser_available": True,
                    "engine": "python-ast",
                    "evidence": ["python-report.json"],
                },
                "typescript": {
                    "cases": 20,
                    "true_positive": 9,
                    "true_negative": 9,
                    "false_positive": 1,
                    "false_negative": 1,
                    "parser_available": True,
                    "engine": "tree-sitter-typescript",
                    "evidence": ["typescript-report.json"],
                },
            },
        }
        result = validate_multilang_qualification(data)
        self.assertEqual(result["status"], "VALID")

    def test_multilang_qualification_fails_below_frozen_recall(self):
        data = {
            "preregistered": True,
            "revision": "abc123",
            "acceptance_thresholds": {
                "min_recall": 0.9,
                "max_false_positive_rate": 0.2,
            },
            "languages": {
                "python": {
                    "cases": 10,
                    "true_positive": 4,
                    "true_negative": 5,
                    "false_positive": 0,
                    "false_negative": 1,
                    "parser_available": True,
                    "engine": "python-ast",
                    "evidence": ["python-report.json"],
                },
                "typescript": {
                    "cases": 10,
                    "true_positive": 4,
                    "true_negative": 5,
                    "false_positive": 0,
                    "false_negative": 1,
                    "parser_available": True,
                    "engine": "tree-sitter-typescript",
                    "evidence": ["typescript-report.json"],
                },
            },
        }
        result = validate_multilang_qualification(data)
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("recall does not meet", "\n".join(result["errors"]))

    def test_independent_security_audit_rejects_open_high(self):
        data = {
            "independence_attestation": True,
            "assessor_id": "external-reviewer",
            "revision": "abc123",
            "scope": "threat model and supply chain",
            "threat_model": {"status": "PASS", "evidence": ["threat.md"]},
            "supply_chain": {"status": "PASS", "evidence": ["supply.md"]},
            "open_findings": {"critical": 0, "high": 1},
        }
        result = validate_independent_security_audit(data)
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("open high findings must be zero", "\n".join(result["errors"]))

    def test_governance_requires_adopted_release_authority(self):
        result = validate_governance_1_0({
            "status": "DRAFT",
            "roles": {},
            "evidence": [],
        })
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("governance status must be ADOPTED", result["errors"])


if __name__ == "__main__":
    unittest.main()
