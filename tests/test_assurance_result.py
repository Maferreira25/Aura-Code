#!/usr/bin/env python3
"""Tests for the canonical Aura Code assurance result model."""

import json
import unittest
from pathlib import Path

from tools.assurance_result import (
    AssuranceStatus,
    StageState,
    aggregate_status,
    build_result,
    compare_legacy_and_canonical,
    is_progression_blocked,
    normalize_legacy_status,
    progression_state,
    validate_status,
)


ROOT = Path(__file__).resolve().parents[1]


class TestCanonicalStatus(unittest.TestCase):
    def test_exact_pass_is_valid(self):
        self.assertEqual(validate_status("PASS"), AssuranceStatus.PASS)

    def test_unknown_status_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_status("UNKNOWN")

    def test_case_and_whitespace_spoofing_are_rejected(self):
        for value in ("pass", "Pass", " PASS ", "passed"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_status(value)

    def test_non_string_status_is_rejected(self):
        for value in (None, True, 1, []):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_status(value)

    def test_not_run_maps_to_not_tested(self):
        self.assertEqual(normalize_legacy_status("NOT_RUN"), AssuranceStatus.NOT_TESTED)

    def test_not_assessed_maps_to_not_tested(self):
        self.assertEqual(normalize_legacy_status("NOT_ASSESSED"), AssuranceStatus.NOT_TESTED)

    def test_na_maps_to_not_applicable(self):
        self.assertEqual(normalize_legacy_status("NA"), AssuranceStatus.NOT_APPLICABLE)

    def test_generic_warn_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_legacy_status("WARN")


class TestFailClosedAggregation(unittest.TestCase):
    def test_error_dominates_pass(self):
        self.assertEqual(aggregate_status(["PASS", "ERROR"]), AssuranceStatus.ERROR)

    def test_fail_dominates_pass(self):
        self.assertEqual(aggregate_status(["PASS", "FAIL"]), AssuranceStatus.FAIL)

    def test_stale_blocks_pass(self):
        self.assertEqual(aggregate_status(["PASS", "STALE"]), AssuranceStatus.STALE)

    def test_inconclusive_blocks_pass(self):
        self.assertEqual(aggregate_status(["PASS", "INCONCLUSIVE"]), AssuranceStatus.INCONCLUSIVE)

    def test_not_tested_blocks_pass(self):
        self.assertEqual(aggregate_status(["PASS", "NOT_TESTED"]), AssuranceStatus.NOT_TESTED)

    def test_empty_input_is_not_tested(self):
        self.assertEqual(aggregate_status([]), AssuranceStatus.NOT_TESTED)


class TestAssuranceContinuity(unittest.TestCase):
    def test_fail_blocks_progression(self):
        self.assertTrue(is_progression_blocked("FAIL"))

    def test_absent_verification_blocks_progression(self):
        state = progression_state([])
        self.assertEqual(state["state"], StageState.BLOCKED.value)
        self.assertEqual(state["blocked_by"][0]["status"], "NOT_TESTED")

    def test_error_in_predecessor_blocks_progression(self):
        state = progression_state(
            [{"check_id": "architecture", "status": "ERROR", "reason": "scanner crashed"}]
        )
        self.assertEqual(state["state"], "BLOCKED")

    def test_inconclusive_blocks_progression(self):
        state = progression_state(
            [{"check_id": "requirements", "status": "INCONCLUSIVE", "reason": "ambiguous"}]
        )
        self.assertEqual(state["state"], "BLOCKED")

    def test_stale_blocks_progression(self):
        state = progression_state(
            [{"check_id": "evidence", "status": "STALE", "reason": "source changed"}]
        )
        self.assertEqual(state["state"], "BLOCKED")

    def test_invalid_predecessor_status_fails_closed(self):
        state = progression_state(
            [{"check_id": "legacy", "status": "SKIPPED", "reason": "not known"}]
        )
        self.assertEqual(state["state"], "BLOCKED")
        self.assertEqual(state["blocked_by"][0]["status"], "ERROR")

    def test_pass_allows_progression(self):
        state = progression_state(
            [{"check_id": "architecture", "status": "PASS", "reason": "verified"}]
        )
        self.assertEqual(state["state"], "READY")
        self.assertEqual(state["blocked_by"], [])

    def test_not_applicable_can_progress_after_prior_applicability_decision(self):
        state = progression_state(
            [{"check_id": "python-types", "status": "NOT_APPLICABLE", "reason": "Go project"}]
        )
        self.assertEqual(state["state"], "READY")

    def test_waiver_does_not_progress_without_explicit_authorization(self):
        state = progression_state(
            [{"check_id": "control", "status": "WAIVED", "reason": "risk accepted"}]
        )
        self.assertEqual(state["state"], "BLOCKED")

    def test_waiver_can_progress_only_when_explicitly_authorized(self):
        state = progression_state(
            [{"check_id": "control", "status": "WAIVED", "reason": "risk accepted"}],
            waiver_authorized=True,
        )
        self.assertEqual(state["state"], "READY")


class TestResultBuilder(unittest.TestCase):
    def test_builds_valid_minimum_result(self):
        result = build_result(
            check_id="test-integrity",
            status="PASS",
            producer_tool="check_test_integrity",
            producer_method="python_ast",
            workspace=".",
            reason="Assertions verified.",
        )
        self.assertEqual(result["schema_version"], "1.0.0")
        self.assertTrue(result["result_id"].startswith("AR-"))
        self.assertEqual(result["status"], "PASS")

    def test_empty_reason_is_rejected(self):
        with self.assertRaises(ValueError):
            build_result(
                check_id="test",
                status="PASS",
                producer_tool="tool",
                producer_method="method",
                workspace=".",
                reason="",
            )

    def test_waived_requires_metadata(self):
        with self.assertRaises(ValueError):
            build_result(
                check_id="test",
                status="WAIVED",
                producer_tool="tool",
                producer_method="method",
                workspace=".",
                reason="waived",
            )

    def test_shadow_comparison_detects_divergence(self):
        self.assertEqual(
            compare_legacy_and_canonical("PASS", "INCONCLUSIVE")["status"],
            "SHADOW_MISMATCH",
        )


class TestSchemaContract(unittest.TestCase):
    def test_schema_declares_all_canonical_states(self):
        schema = json.loads(
            (ROOT / "schemas" / "assurance-result.schema.json").read_text(encoding="utf-8")
        )
        states = set(schema["properties"]["status"]["enum"])
        self.assertEqual(states, {item.value for item in AssuranceStatus})

    def test_schema_is_fail_closed_on_additional_properties(self):
        schema = json.loads(
            (ROOT / "schemas" / "assurance-result.schema.json").read_text(encoding="utf-8")
        )
        self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
