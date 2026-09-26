#!/usr/bin/env python3
"""Comprehensive Unit Test Suite for AuraCode Adversarial Assurance Debate Flow.

Verifies the 3-phase debate protocol (Proponent -> Adversary -> Arbiter),
physical world analogy synthesis, human authority reminders, and skill definitions.
"""

import json
import unittest
from pathlib import Path

from tools.adversarial_debate import AdversarialDebateRunner


class TestAdversarialFlow(unittest.TestCase):
    """Test suite for adversarial assurance debate."""

    def setUp(self):
        self.root_dir = Path(__file__).resolve().parents[1]
        self.runner = AdversarialDebateRunner(workspace_dir=self.root_dir)

    def test_adversarial_debate_execution(self):
        topic = "Estratégia de Cache Redis vs Local"
        res = self.runner.run_debate(topic)

        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["topic"], topic)
        self.assertEqual(res["phases_executed"], 3)

        debate = res["debate"]
        self.assertIn("phase_1_proponent", debate)
        self.assertIn("phase_2_adversary", debate)
        self.assertIn("phase_3_arbiter", debate)

        # Phase 1: Proponent
        p1 = debate["phase_1_proponent"]
        self.assertIn("Clean Architecture", p1["focus"])
        self.assertIn("domain", p1["argument"])
        self.assertIn("domain", p1["layers_involved"])

        # Phase 2: Adversary
        p2 = debate["phase_2_adversary"]
        self.assertGreater(len(p2["objections"]), 0)

        # Phase 3: Arbiter
        p3 = debate["phase_3_arbiter"]
        self.assertIn("physical_analogy", p3)
        self.assertGreater(len(p3["decision_menu"]), 1)
        self.assertIn("decisão final pertence exclusivamente a você", p3["human_authority_reminder"].lower())

    def test_debate_skills_and_protocol_exist(self):
        # Protocol schema
        protocol_path = self.root_dir / "templates" / "debate" / "debate_protocol.json"
        self.assertTrue(protocol_path.exists())
        protocol_data = json.loads(protocol_path.read_text(encoding="utf-8"))
        self.assertIn("protocol", protocol_data)
        self.assertEqual(len(protocol_data["phases"]), 3)

        # Skills
        debate_skill = self.root_dir / ".agents" / "skills" / "auracode-debate" / "SKILL.md"
        self.assertTrue(debate_skill.exists())
        adv_skill = self.root_dir / ".agents" / "skills" / "auracode-adversary" / "SKILL.md"
        self.assertTrue(adv_skill.exists())


if __name__ == "__main__":
    unittest.main()
