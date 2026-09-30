import json
import unittest
from pathlib import Path

from validation.tools.validate_experiment_evidence import (
    ARMS,
    AUTOMATED_SCENARIOS,
    REQUIRED_REPETITIONS,
    evaluate_p1,
    load_results,
)

ROOT = Path(__file__).resolve().parents[1]


def _short(scenario):
    return {
        "SEC-AUTHZ-001": "authz",
        "SEC-PATH-001": "path",
        "SEC-FAIL-001": "fail",
        "SEC-SQLI-001": "sqli",
        "SEC-LOG-001": "log",
        "DAT-ATOMIC-001": "atomic",
        "REL-CACHE-001": "cache",
        "REL-IDEMP-001": "idemp",
        "SUP-DEPS-001": "deps",
        "VER-TAMPER-001": "tamper",
    }[scenario]


def _row(scenario, arm, rep, success):
    return {
        "suite_version": "test",
        "scenario_id": scenario,
        "run_id": f"{_short(scenario)}-{arm}-{rep}",
        "pair_id": f"{_short(scenario)}-{rep}",
        "arm": arm,
        "execution_surface": "ide",
        "model_family": "fixed-model",
        "model_display_name": "fixed-model medium",
        "reasoning_effort": "medium",
        "antigravity_version": "fixed-version",
        "artifact_review_policy": "request-review",
        "terminal_execution_policy": "request-review",
        "strict_mode": True,
        "qualified_success": success,
        "public_tests_passed": success,
        "protected_tests_passed": success,
        "evaluator_integrity": True,
        "dimensions": {},
    }


class ExperimentEvidenceTests(unittest.TestCase):
    def test_repository_historical_results_are_incomplete_and_ceilinged(self):
        rows, errors = load_results(ROOT / "validation" / "results")
        self.assertEqual(errors, [])
        report = evaluate_p1(rows)
        self.assertFalse(report["formal_p1_complete"])
        self.assertTrue(report["ceiling_effect"])
        self.assertFalse(report["comparative_signal_interpretable"])
        self.assertFalse(report["headline_effectiveness_claim_allowed"])
        self.assertEqual(report["automated_runs"], 30)

    def test_complete_discriminating_protocol_is_interpretable_but_not_headline_public_evidence(self):
        rows = []
        for scenario in AUTOMATED_SCENARIOS:
            for rep_index, rep in enumerate(REQUIRED_REPETITIONS):
                for arm in ARMS:
                    if arm == "A2":
                        success = True
                    elif arm == "A1":
                        success = rep_index != 0
                    else:
                        success = rep_index == 2
                    rows.append(_row(scenario, arm, rep, success))

        for arm in ARMS:
            for index in range(5):
                rows.append({
                    "scenario_id": "INT-AMBIG-001",
                    "run_id": f"ambig-{arm}-r{index + 1}",
                    "pair_id": f"ambig-r{index + 1}",
                    "arm": arm,
                    "qualified_success": True,
                    "dimensions": {},
                })
            for index in range(3):
                rows.append({
                    "scenario_id": "ARC-EVOL-001",
                    "run_id": f"arcevol-{arm}-seq{index + 1}",
                    "pair_id": f"arcevol-seq{index + 1}",
                    "arm": arm,
                    "qualified_success": True,
                    "dimensions": {},
                })

        report = evaluate_p1(rows)
        self.assertTrue(report["formal_p1_complete"])
        self.assertFalse(report["ceiling_effect"])
        self.assertTrue(report["comparative_signal_interpretable"])
        self.assertFalse(report["headline_effectiveness_claim_allowed"])
        self.assertEqual(report["automated_runs"], 90)

    def test_qs_formula_mismatch_is_invalid(self):
        row = _row("SEC-AUTHZ-001", "A0", "r1", True)
        row["protected_tests_passed"] = False
        report = evaluate_p1([row])
        self.assertIn(row["run_id"], report["invalid_qs_runs"])
        self.assertTrue(report["errors"])


if __name__ == "__main__":
    unittest.main()
