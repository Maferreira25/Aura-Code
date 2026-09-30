import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "adapters" / "antigravity" / ".agents" / "agents"


class AssuranceAgentBoundaryTests(unittest.TestCase):
    def test_revalidator_is_read_only(self):
        text = (AGENTS / "auracode-revalidator" / "agent.md").read_text(encoding="utf-8")
        self.assertIn("- view_file", text)
        self.assertIn("- grep_search", text)
        for forbidden in ("run_command", "write_to_file", "replace_file_content", "multi_replace_file_content"):
            self.assertNotIn(f"  - {forbidden}", text)

    def test_remediator_can_edit_but_cannot_self_resolve(self):
        text = (AGENTS / "auracode-remediator" / "agent.md").read_text(encoding="utf-8")
        self.assertIn("- replace_file_content", text)
        self.assertIn("- run_command", text)
        self.assertIn("Do not declare a finding RESOLVED", text)
        self.assertIn("IMPLEMENTED_PENDING_REVALIDATION", text)

    def test_legacy_debugger_fix_hands_off_for_revalidation(self):
        text = (AGENTS / "auracode-debugger-fix" / "agent.md").read_text(encoding="utf-8")
        self.assertIn("Independent Revalidation Boundary", text)
        self.assertIn("IMPLEMENTED_PENDING_REVALIDATION", text)


if __name__ == "__main__":
    unittest.main()
