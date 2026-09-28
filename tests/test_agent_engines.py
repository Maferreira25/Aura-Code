#!/usr/bin/env python3
"""
Unit tests for AuraCode Agent Engines:
- auracode-clarify (ClarifyEngine)
- auracode-brainstorm (BrainstormEngine)
- auracode-forward (ForwardEngine)
- auracode-debugger (DebuggerEngine)
- auracode-refactor (RefactorEngine)
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.clarify_engine import ClarifyEngine
from tools.brainstorm_engine import BrainstormEngine
from tools.forward_engine import ForwardEngine
from tools.debugger_engine import DebuggerEngine
from tools.refactor_engine import RefactorEngine


class TestAgentEngines(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_clarify_engine_deterministic_and_save(self):
        engine = ClarifyEngine(workspace_dir=self.temp_dir)
        res = engine.clarify("Login de usuário e permissões")
        self.assertEqual(res["mode"], "deterministic_analogy_engine")
        self.assertGreater(len(res["questions"]), 0)
        q = res["questions"][0]
        self.assertIn("option_a", q)
        self.assertIn("option_b", q)
        self.assertIn("residual_doubt_prompt", q)

        # Test saving
        saved_file = engine.save_clarification(res)
        self.assertTrue(saved_file.exists())
        content = saved_file.read_text(encoding="utf-8")
        self.assertIn("Briefing de Clarificação de Requisitos", content)
        self.assertIn("Zero Presunção", content)
        self.assertIn("Opção A", content)

    def test_brainstorm_engine_synthesis_and_save(self):
        engine = BrainstormEngine(workspace_dir=self.temp_dir)
        res = engine.brainstorm("Aplicativo de controle financeiro para freelancers")
        self.assertIn("vision", res)
        self.assertGreater(len(res["essential"]), 0)
        self.assertGreater(len(res["desirable"]), 0)
        self.assertGreater(len(res["premortem_risks"]), 0)

        # Test saving
        saved_file = engine.save_brainstorm(res)
        self.assertTrue(saved_file.exists())
        content = saved_file.read_text(encoding="utf-8")
        self.assertIn("Ideação e Amadurecimento do Produto", content)
        self.assertIn("Essenciais", content)

    def test_forward_engine_prerequisites_and_scaffolding(self):
        engine = ForwardEngine(workspace_dir=self.temp_dir)

        # 1. Missing SDD directory -> BLOCKED
        prereqs = engine.check_prerequisites(profile="lite")
        self.assertEqual(prereqs["status"], "BLOCKED")
        self.assertFalse(prereqs["can_build"])

        # 2. Create SDD specs with approval
        sdd_dir = self.temp_dir / "_auracode_sdd"
        sdd_dir.mkdir(parents=True)
        (sdd_dir / "01_spec.md").write_text("# Planta Aprovada pelo Usuario\nStatus: Aprovado\n", encoding="utf-8")
        (sdd_dir / "02_spec.md").write_text("# Arquitetura\n", encoding="utf-8")
        (sdd_dir / "03_spec.md").write_text("# Testes\n", encoding="utf-8")

        prereqs_ok = engine.check_prerequisites(profile="lite")
        self.assertEqual(prereqs_ok["status"], "READY")
        self.assertTrue(prereqs_ok["can_build"])

        # 3. Scaffold Clean Architecture
        scaffold_res = engine.scaffold_clean_architecture()
        self.assertEqual(scaffold_res["status"], "SCAFFOLDED")
        base = Path(scaffold_res["base_directory"])
        for layer in ["domain", "usecases", "adapters", "infrastructure", "tests"]:
            self.assertTrue((base / layer).is_dir())
            self.assertTrue((base / layer / "__init__.py").exists())
        self.assertTrue((base / "contracts.json").exists())

    def test_debugger_engine_registration_and_reproduction(self):
        engine = DebuggerEngine(workspace_dir=self.temp_dir)
        reg = engine.register_bug("bug_test_01", "Erro de autenticação com senha vazia")
        self.assertEqual(reg["status"], "REGISTERED")
        self.assertTrue(Path(reg["bug_file"]).exists())

        test_file = engine.generate_reproduction_test("bug_test_01")
        self.assertTrue(test_file.exists())

        # Test reproduction verification (must fail)
        repro = engine.verify_reproduction("bug_test_01")
        self.assertEqual(repro["status"], "REPRODUCED")
        self.assertTrue(repro["fails_as_expected"])

    def test_refactor_engine_opportunities_and_plan(self):
        # Create sample workspace with a missing type annotation
        (self.temp_dir / "service.py").write_text(
            "def calculate(total):\n    return total * 1.1\n",
            encoding="utf-8"
        )
        engine = RefactorEngine(workspace_dir=self.temp_dir)
        analysis = engine.analyze_opportunities()
        self.assertEqual(analysis["status"], "OPPORTUNITIES_IDENTIFIED")
        self.assertGreater(analysis["type_annotations_missing"], 0)

        plan_file = engine.generate_plan()
        self.assertTrue(plan_file.exists())
        plan_content = plan_file.read_text(encoding="utf-8")
        self.assertIn("Plano de Refatoração Cirúrgica", plan_content)
        self.assertIn("calculate", plan_content)


if __name__ == "__main__":
    unittest.main()
