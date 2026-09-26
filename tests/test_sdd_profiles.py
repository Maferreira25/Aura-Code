#!/usr/bin/env python3
"""Comprehensive Unit Test Suite for SDD Profiles: Micro, Lite, Standard, and Enterprise.

Verifies that all 4 SDD profiles scaffold the exact expected specifications,
adhere to Zero Presumption directives, and cleanly initialize target workspaces.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from tools.assurance import setup_auracode_environment, main

EXPECTED_MICRO_SPECS = [
    "01_task_spec.md",
]

EXPECTED_LITE_SPECS = [
    "01_visao_e_regras.md",
    "02_arquitetura_e_dados.md",
    "03_testes_e_criterios.md",
]

EXPECTED_STANDARD_SPECS = [
    "01_visao_geral_e_negocio.md",
    "02_arquitetura_e_componentes.md",
    "03_modelo_de_dados_e_armazenamento.md",
    "04_seguranca_e_permissoes.md",
    "05_apis_e_integracoes.md",
    "06_interface_e_design_system.md",
    "07_nivel_de_garantia_e_testes.md",
]

EXPECTED_ENTERPRISE_SPECS = [
    "01_PRD.md",
    "02_RULES.md",
    "03_ARCHITECTURE.md",
    "04_DATA_MODEL.md",
    "05_API_SPEC.md",
    "06_WORKFLOWS.md",
    "07_EDGE_CASES.md",
    "08_SECURITY.md",
    "09_TEST_PLAN.md",
    "10_DESIGN_SYSTEM.md",
    "11_TELEMETRY.md",
    "12_DEPLOY.md",
    "13_DEPENDENCIES.md",
    "14_AGENTS.md",
    "15_GLOSSARY.md",
]


class TestSddProfiles(unittest.TestCase):
    """Test suite for SDD modular profiles."""

    def setUp(self):
        self.root_dir = Path(__file__).resolve().parents[1]
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_micro_specs_exist_and_complete(self):
        templates_micro = self.root_dir / "templates" / "sdd" / "micro"
        self.assertTrue(templates_micro.exists(), "templates/sdd/micro must exist")
        for spec_name in EXPECTED_MICRO_SPECS:
            spec_file = templates_micro / spec_name
            self.assertTrue(spec_file.exists(), f"Missing micro spec: {spec_name}")
            content = spec_file.read_text(encoding="utf-8")
            self.assertIn("Perfil Micro", content)
            self.assertIn("Zero a Presunções", content)
            self.assertIn("Comportamento Atual vs. Comportamento Esperado", content)
            self.assertIn("Limites de Escopo Cirúrgico", content)

    def test_lite_specs_exist_and_complete(self):
        templates_lite = self.root_dir / "templates" / "sdd" / "lite"
        self.assertTrue(templates_lite.exists(), "templates/sdd/lite must exist")
        for spec_name in EXPECTED_LITE_SPECS:
            spec_file = templates_lite / spec_name
            self.assertTrue(spec_file.exists(), f"Missing lite spec: {spec_name}")
            content = spec_file.read_text(encoding="utf-8")
            self.assertIn("Perfil Lite", content)

    def test_setup_environment_with_micro_profile(self):
        setup_auracode_environment(profile="micro", copy_templates=True, target_dir=self.temp_dir)
        sdd_dir = self.temp_dir / "_auracode_sdd"
        self.assertTrue(sdd_dir.exists())
        installed_files = sorted([f.name for f in sdd_dir.glob("*.md")])
        self.assertEqual(installed_files, EXPECTED_MICRO_SPECS)
        self.assertEqual(len(installed_files), 1)

    def test_setup_environment_with_lite_profile(self):
        setup_auracode_environment(profile="lite", copy_templates=True, target_dir=self.temp_dir)
        sdd_dir = self.temp_dir / "_auracode_sdd"
        self.assertTrue(sdd_dir.exists())
        installed_files = sorted([f.name for f in sdd_dir.glob("*.md")])
        self.assertEqual(installed_files, EXPECTED_LITE_SPECS)
        self.assertEqual(len(installed_files), 3)

    def test_setup_environment_with_standard_profile(self):
        setup_auracode_environment(profile="standard", copy_templates=True, target_dir=self.temp_dir)
        sdd_dir = self.temp_dir / "_auracode_sdd"
        self.assertTrue(sdd_dir.exists())
        installed_files = sorted([f.name for f in sdd_dir.glob("*.md")])
        self.assertEqual(installed_files, EXPECTED_STANDARD_SPECS)
        self.assertEqual(len(installed_files), 7)

    def test_setup_environment_with_basic_alias(self):
        setup_auracode_environment(profile="basic", copy_templates=True, target_dir=self.temp_dir)
        sdd_dir = self.temp_dir / "_auracode_sdd"
        self.assertTrue(sdd_dir.exists())
        installed_files = sorted([f.name for f in sdd_dir.glob("*.md")])
        self.assertEqual(installed_files, EXPECTED_STANDARD_SPECS)
        self.assertEqual(len(installed_files), 7)

    def test_setup_environment_with_enterprise_profile(self):
        setup_auracode_environment(profile="enterprise", copy_templates=True, target_dir=self.temp_dir)
        sdd_dir = self.temp_dir / "_auracode_sdd"
        self.assertTrue(sdd_dir.exists())
        installed_files = sorted([f.name for f in sdd_dir.glob("*.md")])
        self.assertEqual(installed_files, EXPECTED_ENTERPRISE_SPECS)
        self.assertEqual(len(installed_files), 15)


if __name__ == "__main__":
    unittest.main()
