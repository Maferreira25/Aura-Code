import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / ".agents" / "skills"
TEMPLATES_SDD_DIR = ROOT / "templates" / "sdd"

class AuraCodeSkillsTests(unittest.TestCase):
    def test_skills_exist(self):
        expected_skills = [
            "auracode",
            "auracode-new",
            "auracode-clarify",
            "auracode-brainstorm",
            "auracode-forward",
            "auracode-audit",
            "auracode-debugger",
            "auracode-refactor",
            "auracode-agents-help",
            "auracode-guard",
            "auracode-worktree",
            "auracode-cage",
            "auracode-loop",
            "auracode-debate",
            "auracode-adversary",
        ]
        for skill in expected_skills:
            skill_file = SKILLS_DIR / skill / "SKILL.md"
            self.assertTrue(skill_file.exists(), f"Skill file {skill_file} should exist.")

    def test_skills_contain_zero_presumption_rule(self):
        key_skills = ["auracode", "auracode-new", "auracode-clarify"]
        for skill in key_skills:
            content = (SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8").lower()
            self.assertTrue("presunç" in content or "presumir" in content, f"Skill {skill} must contain Zero Presumption directive.")

    def test_sdd_templates_exist(self):
        expected_templates = [
            "01_visao_geral_e_negocio.md",
            "02_arquitetura_e_componentes.md",
            "03_modelo_de_dados_e_armazenamento.md",
            "04_seguranca_e_permissoes.md",
            "05_apis_e_integracoes.md",
            "06_interface_e_design_system.md",
            "07_nivel_de_garantia_e_testes.md",
        ]
        for tpl in expected_templates:
            tpl_file = TEMPLATES_SDD_DIR / tpl
            self.assertTrue(tpl_file.exists(), f"Template {tpl_file} should exist.")

if __name__ == "__main__":
    unittest.main()
