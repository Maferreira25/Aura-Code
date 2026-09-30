import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.dogfood_assurance import dogfood_repository

from tools.assurance_state import (
    advance_state,
    apply_continuous_regression,
    evaluate_gate,
    import_assessment,
    import_audit_result,
    load_gate_policy,
    load_profile_controls,
    new_state,
    normalize_status,
    record_actor,
    record_control,
    register_finding,
    start_remediation,
    validate_state,
    mark_remediation_implemented,
    revalidate_finding,
)

ROOT = Path(__file__).resolve().parents[1]


class AssuranceStateTests(unittest.TestCase):
    def satisfy_gate(self, state, target):
        gate = next(item for item in load_gate_policy(ROOT)["gates"] if item["target_stage"] == target)
        profile = set(load_profile_controls(state["assurance_level"], ROOT))
        for control_id in gate.get("required_controls", []):
            if control_id in profile:
                record_control(state, control_id, "PASS", [f"evidence/{control_id}.txt"])

    def test_unknown_required_control_blocks(self):
        state = new_state("demo", "AL1")
        result = evaluate_gate(state, "RISK_CLASSIFIED", ROOT)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("GOV-01", result["unknown_controls"])

    def test_pass_without_evidence_blocks(self):
        state = new_state("demo", "AL1")
        record_control(state, "GOV-01", "PASS")
        result = evaluate_gate(state, "RISK_CLASSIFIED", ROOT)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("PASS requires evidence", "\n".join(result["reasons"]))

    def test_g0_allows_with_evidence(self):
        state = new_state("demo", "AL1")
        record_control(state, "GOV-01", "PASS", ["risk.md"])
        result = advance_state(state, "RISK_CLASSIFIED", ROOT)
        self.assertEqual(result["decision"], "ALLOW")
        self.assertEqual(state["current_stage"], "RISK_CLASSIFIED")

    def test_non_sequential_transition_blocks(self):
        state = new_state("demo", "AL1")
        self.satisfy_gate(state, "REQUIREMENTS_VERIFIED")
        result = evaluate_gate(state, "REQUIREMENTS_VERIFIED", ROOT)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("non-sequential transition", "\n".join(result["reasons"]))

    def test_same_implementer_and_verifier_blocks_al2(self):
        state = new_state("demo", "AL2")
        state["current_stage"] = "IMPLEMENTATION"
        self.satisfy_gate(state, "VERIFICATION")
        record_actor(state, "implementer", "agent-a", "AI_AGENT", "session-a", "model-x")
        record_actor(state, "verifier", "agent-a", "AI_AGENT", "session-b", "model-y")
        result = evaluate_gate(state, "VERIFICATION", ROOT)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("must be different actors", "\n".join(result["reasons"]))

    def test_separate_agents_allow_al2_even_same_model(self):
        state = new_state("demo", "AL2")
        state["current_stage"] = "IMPLEMENTATION"
        self.satisfy_gate(state, "VERIFICATION")
        record_actor(state, "implementer", "agent-a", "AI_AGENT", "session-a", "model-x")
        record_actor(state, "verifier", "agent-b", "AI_AGENT", "session-b", "model-x")
        result = evaluate_gate(state, "VERIFICATION", ROOT)
        self.assertEqual(result["decision"], "ALLOW")

    def test_same_ai_model_blocks_strong_independence_al3(self):
        state = new_state("demo", "AL3")
        state["current_stage"] = "IMPLEMENTATION"
        self.satisfy_gate(state, "VERIFICATION")
        record_actor(state, "implementer", "agent-a", "AI_AGENT", "session-a", "model-x")
        record_actor(state, "verifier", "agent-b", "AI_AGENT", "session-b", "model-x")
        result = evaluate_gate(state, "VERIFICATION", ROOT)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("different model_id", "\n".join(result["reasons"]))

    def test_different_ai_models_allow_strong_independence_al3(self):
        state = new_state("demo", "AL3")
        state["current_stage"] = "IMPLEMENTATION"
        self.satisfy_gate(state, "VERIFICATION")
        record_actor(state, "implementer", "agent-a", "AI_AGENT", "session-a", "model-x")
        record_actor(state, "verifier", "agent-b", "AI_AGENT", "session-b", "model-y")
        result = evaluate_gate(state, "VERIFICATION", ROOT)
        self.assertEqual(result["decision"], "ALLOW")

    def test_same_implementer_and_auditor_blocks_security_gate(self):
        state = new_state("demo", "AL2")
        state["current_stage"] = "VERIFICATION"
        self.satisfy_gate(state, "SECURITY_VERIFIED")
        record_actor(state, "implementer", "agent-a", "AI_AGENT", "session-a", "model-x")
        record_actor(state, "auditor", "agent-a", "AI_AGENT", "session-c", "model-y")
        result = evaluate_gate(state, "SECURITY_VERIFIED", ROOT)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("must be different actors", "\n".join(result["reasons"]))

    def test_legacy_not_assessed_maps_to_unknown(self):
        self.assertEqual(normalize_status("NOT_ASSESSED"), "UNKNOWN")

    def test_remediator_cannot_self_revalidate(self):
        state = new_state("demo", "AL2")
        register_finding(state, "AUD-001", "HIGH", "Example", status="CONFIRMED", evidence=["audit.md"])
        record_actor(state, "remediator", "agent-fix", "AI_AGENT", "fix-session", "model-x")
        start_remediation(state, "AUD-001", ["plan.md"])
        mark_remediation_implemented(state, "AUD-001", ["patch.diff", "test.txt"])
        record_actor(state, "revalidator", "agent-fix", "AI_AGENT", "verify-session", "model-y")
        with self.assertRaisesRegex(ValueError, "must be different actors"):
            revalidate_finding(state, "AUD-001", "PASS", ["retest.txt"])

    def test_independent_revalidator_resolves_finding(self):
        state = new_state("demo", "AL2")
        finding = register_finding(state, "AUD-002", "HIGH", "Example", status="CONFIRMED", evidence=["audit.md"])
        record_actor(state, "remediator", "agent-fix", "AI_AGENT", "fix-session", "model-x")
        start_remediation(state, "AUD-002", ["plan.md"])
        mark_remediation_implemented(state, "AUD-002", ["patch.diff", "test.txt"])
        record_actor(state, "revalidator", "agent-review", "AI_AGENT", "review-session", "model-x")
        revalidate_finding(state, "AUD-002", "PASS", ["retest.txt"])
        self.assertEqual(finding["status"], "RESOLVED")
        self.assertEqual(finding["revalidation"]["result"], "PASS")

    def test_same_model_revalidator_blocks_al3(self):
        state = new_state("demo", "AL3")
        register_finding(state, "AUD-003", "HIGH", "Example", status="CONFIRMED", evidence=["audit.md"])
        record_actor(state, "remediator", "agent-fix", "AI_AGENT", "fix-session", "model-x")
        start_remediation(state, "AUD-003", ["plan.md"])
        mark_remediation_implemented(state, "AUD-003", ["patch.diff", "test.txt"])
        record_actor(state, "revalidator", "agent-review", "AI_AGENT", "review-session", "model-x")
        with self.assertRaisesRegex(ValueError, "different model_id"):
            revalidate_finding(state, "AUD-003", "PASS", ["retest.txt"])

    def test_failed_revalidation_reopens_finding(self):
        state = new_state("demo", "AL2")
        finding = register_finding(state, "AUD-004", "HIGH", "Example", status="CONFIRMED", evidence=["audit.md"])
        record_actor(state, "remediator", "agent-fix", "AI_AGENT", "fix-session", "model-x")
        start_remediation(state, "AUD-004", ["plan.md"])
        mark_remediation_implemented(state, "AUD-004", ["patch.diff", "test.txt"])
        record_actor(state, "revalidator", "agent-review", "AI_AGENT", "review-session", "model-x")
        revalidate_finding(state, "AUD-004", "FAIL", ["retest-failed.txt"])
        self.assertEqual(finding["status"], "REVALIDATION_FAILED")

    def test_import_assessment_downgrades_invalid_pass_to_unknown(self):
        state = new_state("demo", "AL1")
        assessment = {
            "framework_version": "0.3.0.dev0",
            "assurance_level": "AL1",
            "project": "demo",
            "assessor": "test",
            "controls": {
                "GOV-01": {"status": "PASS", "evidence": ["missing-evidence.txt"]}
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            result = import_assessment(state, assessment, Path(tmp), ROOT)
        self.assertIn("GOV-01", result["downgraded_to_unknown"])
        self.assertEqual(state["controls"]["GOV-01"]["status"], "UNKNOWN")

    def test_import_assessment_preserves_verified_pass(self):
        state = new_state("demo", "AL1")
        assessment = {
            "framework_version": "0.3.0.dev0",
            "assurance_level": "AL1",
            "project": "demo",
            "assessor": "test",
            "controls": {
                "GOV-01": {"status": "PASS", "evidence": ["risk.md"]}
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "risk.md").write_text("evidence", encoding="utf-8")
            import_assessment(state, assessment, Path(tmp), ROOT)
        self.assertEqual(state["controls"]["GOV-01"]["status"], "PASS")

    def test_auracode_dogfood_blocks_verification_without_independent_actors(self):
        state = new_state("auracode", "AL2", "0.3.0.dev0")
        assessment = __import__("json").loads(
            (ROOT / "self-assessment.json").read_text(encoding="utf-8")
        )
        imported = import_assessment(state, assessment, ROOT, ROOT)
        self.assertEqual(imported["downgraded_to_unknown"], [])

        for target in (
            "RISK_CLASSIFIED",
            "REQUIREMENTS_VERIFIED",
            "ARCHITECTURE_VERIFIED",
            "IMPLEMENTATION",
        ):
            result = advance_state(state, target, ROOT)
            self.assertEqual(result["decision"], "ALLOW", result["reasons"])

        blocked = evaluate_gate(state, "VERIFICATION", ROOT)
        self.assertEqual(blocked["decision"], "BLOCK")
        self.assertIn("missing actor provenance for 'implementer'", blocked["reasons"])
        self.assertIn("missing actor provenance for 'verifier'", blocked["reasons"])

    def test_continuous_regression_reopens_and_blocks_gate(self):
        state = new_state("demo", "AL1")
        record_control(state, "GOV-01", "PASS", ["risk.md"])
        comparison = {
            "decision": "BLOCK",
            "blockers": ["control regression ARC-01: PASS -> UNKNOWN"],
        }
        finding = apply_continuous_regression(state, comparison, ["compare.json"])
        self.assertIsNotNone(finding)
        self.assertEqual(state["assurance_status"], "REOPENED")
        blocked = evaluate_gate(state, "RISK_CLASSIFIED", ROOT)
        self.assertEqual(blocked["decision"], "BLOCK")
        self.assertIn("assurance status is REOPENED", "\n".join(blocked["reasons"]))

    def test_independent_revalidation_restores_active_when_last_material_finding_closes(self):
        state = new_state("demo", "AL2")
        comparison = {
            "decision": "BLOCK",
            "blockers": ["new open HIGH findings: 0 -> 1"],
        }
        finding = apply_continuous_regression(state, comparison, ["compare.json"])
        self.assertIsNotNone(finding)
        finding_id = finding["id"]
        record_actor(state, "remediator", "agent-fix", "AI_AGENT", "fix-session", "model-x")
        start_remediation(state, finding_id, ["plan.md"])
        mark_remediation_implemented(state, finding_id, ["patch.diff", "test.txt"])
        record_actor(state, "revalidator", "agent-review", "AI_AGENT", "review-session", "model-x")
        revalidate_finding(state, finding_id, "PASS", ["retest.txt"])
        self.assertEqual(state["assurance_status"], "ACTIVE")

    def test_clean_audit_records_history_without_blanket_control_pass(self):
        state = new_state("demo", "AL2")
        result = import_audit_result(
            state,
            {
                "status": "PASS",
                "guarantees": {
                    "security": {"status": "PASS"},
                    "architecture": {"status": "PASS"},
                },
            },
            ["audit.json"],
        )
        self.assertIsNone(result["finding_id"])
        self.assertEqual(state["assurance_status"], "ACTIVE")
        self.assertEqual(state["controls"], {})
        self.assertEqual(len(state["audit_history"]), 1)

    def test_failed_audit_creates_blocking_finding_and_reopens_assurance(self):
        state = new_state("demo", "AL2")
        result = import_audit_result(
            state,
            {
                "status": "FAIL",
                "guarantees": {
                    "security": {"status": "FAIL"},
                    "architecture": {"status": "PASS"},
                },
            },
            ["audit.json"],
        )
        self.assertIsNotNone(result["finding_id"])
        self.assertEqual(state["assurance_status"], "REOPENED")
        finding = state["open_findings"][0]
        self.assertEqual(finding["severity"], "HIGH")
        self.assertEqual(finding["source"], "AUDIT_ENGINE")
        self.assertEqual(finding["failed_guarantees"], ["security"])

    @patch("tools.dogfood_assurance.audit_workspace")
    def test_dogfood_blocks_at_verification_without_actor_provenance(self, mock_audit):
        mock_audit.return_value = {
            "status": "PASS",
            "guarantees": {
                "architecture": {"status": "PASS"},
                "security": {"status": "PASS"},
                "test_integrity": {"status": "PASS"},
            },
        }
        report = dogfood_repository(
            ROOT,
            ROOT / "self-assessment.json",
            ROOT,
        )
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["blocked_at"], "VERIFICATION")
        self.assertEqual(report["current_stage"], "IMPLEMENTATION")
        reasons = "\n".join(report["transitions"][-1]["reasons"])
        self.assertIn("missing actor provenance for 'implementer'", reasons)
        self.assertIn("missing actor provenance for 'verifier'", reasons)

    def test_validate_state_rejects_malformed_findings(self):
        state = new_state("demo", "AL2")
        state["open_findings"] = [{"id": "X", "severity": "HIGH", "status": "INVALID"}]
        errors = validate_state(state)
        self.assertTrue(any("invalid status" in error for error in errors))

    def test_validate_state_rejects_non_array_audit_history(self):
        state = new_state("demo", "AL2")
        state["audit_history"] = {}
        errors = validate_state(state)
        self.assertIn("audit_history must be an array", errors)

    def test_validate_state_rejects_malformed_transition_history(self):
        state = new_state("demo", "AL2")
        state["transition_history"] = ["not-an-object"]
        errors = validate_state(state)
        self.assertIn("transition_history entries must be objects", errors)

    def test_agt02_catalog_matches_gate_independence_policy(self):
        catalog = __import__("json").loads(
            (ROOT / "controls" / "catalog.json").read_text(encoding="utf-8")
        )
        agt02 = next(item for item in catalog["controls"] if item["id"] == "AGT-02")
        gates = load_gate_policy(ROOT)["gates"]
        verification = next(item for item in gates if item["target_stage"] == "VERIFICATION")
        self.assertIn("AGT-02", verification["required_controls"])
        self.assertEqual(verification["independence_from_level"], "AL2")
        self.assertEqual(verification["strong_model_independence_from_level"], "AL3")
        requirement = agt02["requirement"]
        self.assertIn("distinct actors", requirement)
        self.assertIn("distinct sessions", requirement)
        self.assertIn("distinct model identities", requirement)

    def test_validate_state_rejects_missing_required_root_field(self):
        state = new_state("demo", "AL2")
        del state["actors"]
        errors = validate_state(state)
        self.assertIn("missing required state field: actors", errors)

    def test_validate_state_rejects_unknown_root_field(self):
        state = new_state("demo", "AL2")
        state["unexpected"] = True
        errors = validate_state(state)
        self.assertIn("unknown state field: unexpected", errors)


if __name__ == "__main__":
    unittest.main()
