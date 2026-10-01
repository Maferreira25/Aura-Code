import hashlib
import json
import tempfile
import unittest
from pathlib import Path

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
    validate_p4_plan,
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


def p2_pairing():
    return {
        "model_family": "model-family",
        "model_display_name": "Model X",
        "agent": "Agent X",
        "reasoning_effort": "medium",
    }


def p2_plan():
    return {
        "study_id": "P2-X",
        "preregistered": True,
        "private_or_fresh_split": True,
        "arms": ["A0", "A1", "A2"],
        "scenarios": p2_scenarios(),
        "repetitions_per_arm": 5,
        "private_split_commitment_sha256": "a" * 64,
        "model_agent_pairings": [p2_pairing()],
    }


def p2_runs(repetitions=5):
    runs = []
    for scenario in p2_scenarios():
        for arm in ("A0", "A1", "A2"):
            for repetition in range(repetitions):
                runs.append({
                    "run_id": f"{scenario['id']}-{arm}-r{repetition + 1}",
                    "arm": arm,
                    "scenario_id": scenario["id"],
                    "model_display_name": "Model X",
                    "agent": "Agent X",
                    "reasoning_effort": "medium",
                    "qualified_success": True,
                    "public_tests_passed": True,
                    "protected_tests_passed": True,
                    "evaluator_integrity": True,
                })
    return runs


def registry():
    return {
        "benchmarks": [
            {"id": "B1", "name": "One"},
            {"id": "B2", "name": "Two"},
        ]
    }


class MaturityStudiesTests(unittest.TestCase):
    def test_valid_p2_plan_is_not_a_result(self):
        plan = p2_plan()
        result = validate_p2_plan(plan)
        self.assertEqual(result["status"], "VALID")
        self.assertEqual(result["expected_attempts"], 450)

        as_result = validate_p2_result(plan)
        self.assertEqual(as_result["status"], "INVALID")
        self.assertFalse(as_result["completed"])

    def test_complete_p2_result_is_bound_to_preregistration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = p2_plan()
            plan_path = root / "p2-plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            plan_hash = hashlib.sha256(plan_path.read_bytes()).hexdigest()
            data = {
                "study": "P2",
                "preregistered": True,
                "private_or_fresh_split": True,
                "preregistration_path": "p2-plan.json",
                "preregistration_sha256": plan_hash,
                "private_split_commitment_sha256": "a" * 64,
                "completed": True,
                "scenarios": p2_scenarios(),
                "repetitions_per_arm": 5,
                "model_agent_pairings": [p2_pairing()],
                "expected_attempts": 450,
                "runs": p2_runs(),
            }
            result = validate_p2_result(data, root=root)
            self.assertEqual(result["status"], "VALID", result["errors"])
            self.assertTrue(result["completed"])
            self.assertEqual(result["run_count"], 450)

    def test_p2_result_cannot_shrink_frozen_sample_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = p2_plan()
            plan_path = root / "p2-plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            plan_hash = hashlib.sha256(plan_path.read_bytes()).hexdigest()
            data = {
                "study": "P2",
                "preregistered": True,
                "private_or_fresh_split": True,
                "preregistration_path": "p2-plan.json",
                "preregistration_sha256": plan_hash,
                "private_split_commitment_sha256": "a" * 64,
                "completed": True,
                "scenarios": p2_scenarios(),
                "repetitions_per_arm": 5,
                "model_agent_pairings": [p2_pairing()],
                "expected_attempts": 90,
                "runs": p2_runs(repetitions=1),
            }
            result = validate_p2_result(data, root=root)
            self.assertEqual(result["status"], "INVALID")
            errors = "\n".join(result["errors"])
            self.assertIn("expected_attempts must equal frozen design size 450", errors)
            self.assertIn("P2 incomplete: observed 90/450 attempts", errors)

    def test_p2_result_rejects_tampered_preregistration_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / "p2-plan.json"
            plan_path.write_text(json.dumps(p2_plan()), encoding="utf-8")
            data = {
                "study": "P2",
                "preregistered": True,
                "private_or_fresh_split": True,
                "preregistration_path": "p2-plan.json",
                "preregistration_sha256": "b" * 64,
                "private_split_commitment_sha256": "a" * 64,
                "completed": True,
                "scenarios": p2_scenarios(),
                "repetitions_per_arm": 5,
                "model_agent_pairings": [p2_pairing()],
                "expected_attempts": 450,
                "runs": p2_runs(),
            }
            result = validate_p2_result(data, root=root)
            self.assertEqual(result["status"], "INVALID")
            self.assertIn("preregistration hash mismatch", "\n".join(result["errors"]))

    def test_p2_result_rejects_inconsistent_qualified_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = p2_plan()
            plan_path = root / "p2-plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            plan_hash = hashlib.sha256(plan_path.read_bytes()).hexdigest()
            runs = p2_runs()
            runs[0]["protected_tests_passed"] = False
            data = {
                "study": "P2",
                "preregistered": True,
                "private_or_fresh_split": True,
                "preregistration_path": "p2-plan.json",
                "preregistration_sha256": plan_hash,
                "private_split_commitment_sha256": "a" * 64,
                "completed": True,
                "scenarios": p2_scenarios(),
                "repetitions_per_arm": 5,
                "model_agent_pairings": [p2_pairing()],
                "expected_attempts": 450,
                "runs": runs,
            }
            result = validate_p2_result(data, root=root)
            self.assertEqual(result["status"], "INVALID")
            self.assertIn("Qualified Success formula mismatch", "\n".join(result["errors"]))

    def test_p3_plan_requires_license_revision_and_commitment(self):
        plan = {
            "study_id": "P3-X",
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
                    "upstream_revision": "abc123",
                    "task_subset_commitment_sha256": "c" * 64,
                    "attempts_per_arm": 5,
                }
            ],
            "combine_heterogeneous_scores": False,
        }
        result = validate_p3_plan(plan, registry())
        self.assertEqual(result["status"], "VALID", result["errors"])
        self.assertIn("single benchmark family", result["warnings"][0])

    def test_p3_result_is_bound_to_two_frozen_benchmark_families(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = {
                "study_id": "P3-X",
                "preregistered": True,
                "arms": ["A0", "A1", "A2"],
                "model_agent_pairing": {
                    "model_display_name": "Model X",
                    "agent": "Agent X",
                    "reasoning_effort": "medium",
                },
                "benchmarks": [
                    {
                        "id": bid,
                        "license_verified": True,
                        "upstream_revision": f"rev-{bid}",
                        "task_subset_commitment_sha256": ch * 64,
                        "attempts_per_arm": 5,
                    }
                    for bid, ch in (("B1", "c"), ("B2", "d"))
                ],
                "combine_heterogeneous_scores": False,
            }
            plan_path = root / "p3-plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            plan_hash = hashlib.sha256(plan_path.read_bytes()).hexdigest()
            result_data = {
                "study": "P3",
                "preregistered": True,
                "preregistration_path": "p3-plan.json",
                "preregistration_sha256": plan_hash,
                "model_agent_pairing": plan["model_agent_pairing"],
                "benchmarks": [
                    {
                        "id": item["id"],
                        "license_verified": True,
                        "upstream_revision": item["upstream_revision"],
                        "task_subset_commitment_sha256": item["task_subset_commitment_sha256"],
                        "completed": True,
                        "arms": {
                            arm: {"attempts": 5, "qualified_successes": 4}
                            for arm in ("A0", "A1", "A2")
                        },
                    }
                    for item in plan["benchmarks"]
                ],
            }
            result = validate_p3_result(result_data, registry(), root=root)
            self.assertEqual(result["status"], "VALID", result["errors"])
            self.assertEqual(result["benchmark_count"], 2)

    def test_valid_p4_result_is_bound_to_frozen_operational_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = {
                "study_id": "P4-X",
                "preregistered": True,
                "service_id": "svc",
                "revision": "abc",
                "environment": "staging",
                "acceptance_criteria": {
                    "load": {"success_criteria": "SLO holds", "target_rps": 100, "duration_minutes": 10},
                    "soak": {"success_criteria": "No growth", "duration_minutes": 60},
                    "rollback": {"success_criteria": "Rollback succeeds"},
                    "recovery": {"success_criteria": "Recovery succeeds"},
                    "observability": {"success_criteria": "Signals present"},
                },
            }
            self.assertEqual(validate_p4_plan(plan)["status"], "VALID")
            plan_path = root / "p4-plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            plan_hash = hashlib.sha256(plan_path.read_bytes()).hexdigest()
            evidence = ["report.json"]
            data = {
                "study": "P4",
                "preregistered": True,
                "preregistration_path": "p4-plan.json",
                "preregistration_sha256": plan_hash,
                "service_id": "svc",
                "revision": "abc",
                "environment": "staging",
                "load": {"status": "PASS", "evidence": evidence, "target_rps": 100, "duration_minutes": 10},
                "soak": {"status": "PASS", "evidence": evidence, "duration_minutes": 60},
                "rollback": {"status": "PASS", "evidence": evidence},
                "recovery": {"status": "PASS", "evidence": evidence},
                "observability": {"status": "PASS", "evidence": evidence},
            }
            result = validate_p4_result(data, root=root)
            self.assertEqual(result["status"], "VALID", result["errors"])
            self.assertTrue(result["operational_complete"])

    def test_p4_stable_evidence_rejects_failed_dimension(self):
        data = {
            "study": "P4",
            "preregistered": True,
            "preregistration_path": "plan.json",
            "preregistration_sha256": "a" * 64,
            "service_id": "svc",
            "revision": "abc",
            "environment": "staging",
            "load": {"status": "FAIL", "evidence": ["load.json"]},
            "soak": {"status": "PASS", "evidence": ["soak.json"]},
            "rollback": {"status": "PASS", "evidence": ["rollback.json"]},
            "recovery": {"status": "PASS", "evidence": ["recovery.json"]},
            "observability": {"status": "PASS", "evidence": ["obs.json"]},
        }
        result = validate_p4_result(data)
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("load.status must be PASS", "\n".join(result["errors"]))

    def test_inter_rater_computes_agreement_without_claiming_correctness(self):
        data = {
            "assurance_level": "AL1",
            "control_ids": ["C1", "C2", "C3"],
            "assessors": [
                {"id": "r1", "independence_attestation": True, "implementation_role": False},
                {"id": "r2", "independence_attestation": True, "implementation_role": False},
            ],
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
            "public_corpus": False,
            "corpus_commitment_sha256": "e" * 64,
            "independent_labels": True,
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
            "public_corpus": False,
            "corpus_commitment_sha256": "e" * 64,
            "independent_labels": True,
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

    def test_public_multilang_baseline_is_not_maturity_eligible(self):
        data = {
            "preregistered": True,
            "public_corpus": True,
            "revision": "abc123",
            "acceptance_thresholds": {"min_recall": 1.0, "max_false_positive_rate": 0.0},
            "languages": {
                "python": {
                    "cases": 2, "true_positive": 1, "true_negative": 1,
                    "false_positive": 0, "false_negative": 0,
                    "parser_available": True, "engine": "python-ast", "evidence": ["p.json"]
                },
                "typescript": {
                    "cases": 2, "true_positive": 1, "true_negative": 1,
                    "false_positive": 0, "false_negative": 0,
                    "parser_available": True, "engine": "tree-sitter-typescript", "evidence": ["t.json"]
                },
            },
        }
        maturity = validate_multilang_qualification(data)
        self.assertEqual(maturity["status"], "INVALID")
        baseline = validate_multilang_qualification(data, allow_public_baseline=True)
        self.assertEqual(baseline["status"], "VALID")
        self.assertFalse(baseline["maturity_eligible"])

    def test_independent_security_audit_rejects_open_high(self):
        data = {
            "independence_attestation": True,
            "implementation_role": False,
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
