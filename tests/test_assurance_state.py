import unittest
from pathlib import Path

from tools.assurance_state import (
    advance_state,
    evaluate_gate,
    load_gate_policy,
    load_profile_controls,
    new_state,
    normalize_status,
    record_actor,
    record_control,
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


if __name__ == "__main__":
    unittest.main()
