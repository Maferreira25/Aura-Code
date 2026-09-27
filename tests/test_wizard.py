#!/usr/bin/env python3
"""Comprehensive Unit Test Suite for AuraCode Interactive Briefing Wizard.

Verifies interactive requirements collection, non-technical analogy prompts,
proper template scaffolding across all profiles, and customization of specifications.
"""

import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from tools.wizard import AuraWizard, BriefingIncompleteError


class TestAuraWizard(unittest.TestCase):
    """Test suite for interactive briefing wizard."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_wizard_run_micro_profile(self):
        mock_inputs = [
            "1",                           # Perfil: 1 (micro)
            "ScriptLimpeza",              # Nome do projeto
            "Limpar arquivos temporários", # Missão
            "Apenas administradores",      # Quem vai usar
            "A",                           # Armário A (arquivo local)
            "Sem exclusão permanente"      # Exclusões
        ]

        wiz = AuraWizard(workspace_dir=self.temp_dir, inputs=mock_inputs)
        res = wiz.run()

        self.assertTrue(res["success"])
        self.assertEqual(res["profile"], "micro")
        self.assertEqual(res["project_name"], "ScriptLimpeza")

        sdd_dir = self.temp_dir / "_auracode_sdd"
        self.assertTrue(sdd_dir.exists())
        task_spec = sdd_dir / "01_task_spec.md"
        self.assertTrue(task_spec.exists())
        content = task_spec.read_text(encoding="utf-8")
        self.assertIn("ScriptLimpeza", content)
        self.assertIn("Limpar arquivos temporários", content)

    def test_wizard_run_lite_profile(self):
        mock_inputs = [
            "2",                           # Perfil: 2 (lite)
            "AgendadorSimples",           # Nome do projeto
            "Marcar consultas médicas",   # Missão
            "Pacientes e recepcionistas",  # Quem vai usar
            "B",                           # Armário B (banco estruturado)
            "Sem pagamento online"        # Exclusões
        ]

        wiz = AuraWizard(workspace_dir=self.temp_dir, inputs=mock_inputs)
        res = wiz.run()

        self.assertTrue(res["success"])
        self.assertEqual(res["profile"], "lite")

        sdd_dir = self.temp_dir / "_auracode_sdd"
        self.assertTrue(sdd_dir.exists())
        self.assertEqual(len(list(sdd_dir.glob("*.md"))), 3)
        spec1 = sdd_dir / "01_visao_e_regras.md"
        self.assertTrue(spec1.exists())
        content = spec1.read_text(encoding="utf-8")
        self.assertIn("AgendadorSimples", content)
        self.assertIn("Marcar consultas médicas", content)

    def test_wizard_run_standard_profile(self):
        mock_inputs = [
            "3",                           # Perfil: 3 (standard)
            "PortalEmpresa",              # Nome do projeto
            "Gerenciar pedidos e estoque",# Missão
            "Equipe de vendas e clientes",# Quem vai usar
            "C",                           # Armário C
            "Sem emissão fiscal direta"   # Exclusões
        ]

        wiz = AuraWizard(workspace_dir=self.temp_dir, inputs=mock_inputs)
        res = wiz.run()

        self.assertTrue(res["success"])
        self.assertEqual(res["profile"], "standard")

        sdd_dir = self.temp_dir / "_auracode_sdd"
        self.assertEqual(len(list(sdd_dir.glob("*.md"))), 7)
        spec1 = sdd_dir / "01_visao_geral_e_negocio.md"
        self.assertTrue(spec1.exists())
        content = spec1.read_text(encoding="utf-8")
        self.assertIn("PortalEmpresa", content)

    def test_wizard_creates_draft_without_claiming_clarity_or_approval(self):
        mock_inputs = [
            "4",
            "ProjetoAuditavel",
            "Organizar trabalho de uma equipe",
            "Proprietários, membros e visitantes",
            "B",
            "Sem cobrança",
        ]
        output = StringIO()

        with redirect_stdout(output):
            result = AuraWizard(workspace_dir=self.temp_dir, inputs=mock_inputs).run()

        rendered = output.getvalue()
        self.assertTrue(result["success"])
        self.assertEqual(result["briefing_status"], "DRAFT")
        self.assertEqual(result["clarity_status"], "NOT_RUN")
        self.assertFalse(result["approved"])
        self.assertFalse(result["construction_allowed"])
        self.assertIn("RASCUNHO", rendered)
        self.assertIn("NOT_RUN", rendered)
        self.assertNotIn("100% DE CLAREZA", rendered)
        self.assertNotIn("especificações prontas e revisadas", rendered)
        self.assertNotIn("inicie a construção", rendered)

    def test_wizard_never_defaults_a_missing_business_decision(self):
        wizard = AuraWizard(workspace_dir=self.temp_dir, inputs=[""])

        with self.assertRaises(BriefingIncompleteError):
            wizard.run()

        self.assertFalse((self.temp_dir / "_auracode_sdd").exists())


if __name__ == "__main__":
    unittest.main()
