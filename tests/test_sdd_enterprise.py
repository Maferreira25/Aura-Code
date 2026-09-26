#!/usr/bin/env python3
"""Comprehensive Unit Test Suite for SDD Enterprise Specifications (15 specs) and Basic (7 specs).

Verifies catalog completeness, template integrity, mandatory architectural sections,
invariants, ADRs, TDD clauses, and workspace initialization profiles.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from tools.assurance import setup_auracode_environment

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

EXPECTED_BASIC_SPECS = [
    "01_visao_geral_e_negocio.md",
    "02_arquitetura_e_componentes.md",
    "03_modelo_de_dados_e_armazenamento.md",
    "04_seguranca_e_permissoes.md",
    "05_apis_e_integracoes.md",
    "06_interface_e_design_system.md",
    "07_nivel_de_garantia_e_testes.md",
]


class TestSddEnterprise(unittest.TestCase):
    """Test suite for SDD modular specifications."""

    def setUp(self):
        self.root_dir = Path(__file__).resolve().parents[1]
        self.templates_enterprise = self.root_dir / "templates" / "sdd" / "enterprise"
        self.templates_basic = self.root_dir / "templates" / "sdd" / "basic"
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_enterprise_specs_exist_and_complete(self):
        self.assertTrue(self.templates_enterprise.exists())
        for spec_name in EXPECTED_ENTERPRISE_SPECS:
            spec_file = self.templates_enterprise / spec_name
            self.assertTrue(spec_file.exists(), f"Missing enterprise spec: {spec_name}")
            self.assertGreater(spec_file.stat().st_size, 200, f"Enterprise spec too short: {spec_name}")

    def test_basic_specs_exist_and_complete(self):
        self.assertTrue(self.templates_basic.exists())
        for spec_name in EXPECTED_BASIC_SPECS:
            spec_file = self.templates_basic / spec_name
            self.assertTrue(spec_file.exists(), f"Missing basic spec: {spec_name}")

    def test_critical_sections_in_enterprise_specs(self):
        # 02_RULES.md must define domain invariants and state transitions
        rules_text = (self.templates_enterprise / "02_RULES.md").read_text(encoding="utf-8")
        self.assertIn("Invariantes de Domínio", rules_text)
        self.assertIn("Regras de Transição de Estado", rules_text)

        # 03_ARCHITECTURE.md must define Clean Architecture layers and ADRs
        arch_text = (self.templates_enterprise / "03_ARCHITECTURE.md").read_text(encoding="utf-8")
        self.assertIn("Clean Architecture", arch_text)
        self.assertIn("ADR-001", arch_text)

        # 07_EDGE_CASES.md must cover race conditions and timeouts
        edge_text = (self.templates_enterprise / "07_EDGE_CASES.md").read_text(encoding="utf-8")
        self.assertIn("Concorrência", edge_text)
        self.assertIn("EC-01", edge_text)

        # 09_TEST_PLAN.md must define test immutability clause for agents
        test_text = (self.templates_enterprise / "09_TEST_PLAN.md").read_text(encoding="utf-8")
        self.assertIn("TDD", test_text)
        self.assertIn("NUNCA tem permissão para alterar arquivos de teste", test_text)

        # 11_TELEMETRY.md must define JSON structured logs and RED method
        telem_text = (self.templates_enterprise / "11_TELEMETRY.md").read_text(encoding="utf-8")
        self.assertIn("Logs Estruturados (JSON)", telem_text)
        self.assertIn("Método RED", telem_text)

    def test_setup_environment_with_enterprise_profile(self):
        setup_auracode_environment(profile="enterprise", copy_templates=True, target_dir=self.temp_dir)
        sdd_dir = self.temp_dir / "_auracode_sdd"
        self.assertTrue(sdd_dir.exists())

        files_in_sdd = sorted([f.name for f in sdd_dir.glob("*.md")])
        self.assertEqual(len(files_in_sdd), 15)
        self.assertEqual(files_in_sdd, sorted(EXPECTED_ENTERPRISE_SPECS))

    def test_setup_environment_with_basic_profile(self):
        setup_auracode_environment(profile="basic", copy_templates=True, target_dir=self.temp_dir)
        sdd_dir = self.temp_dir / "_auracode_sdd"
        self.assertTrue(sdd_dir.exists())

        files_in_sdd = sorted([f.name for f in sdd_dir.glob("*.md")])
        self.assertEqual(len(files_in_sdd), 7)
        self.assertEqual(files_in_sdd, sorted(EXPECTED_BASIC_SPECS))


if __name__ == "__main__":
    unittest.main()
