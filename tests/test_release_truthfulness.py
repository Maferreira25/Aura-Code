#!/usr/bin/env python3
"""Regression tests for truthful versioning and public capability claims."""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleaseTruthfulnessTests(unittest.TestCase):
    def test_all_active_version_sources_match(self) -> None:
        """Package, module, VERSION, README, and changelog must agree."""
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        readme_pt = (ROOT / "README.pt-BR.md").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

        package_version = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
        self.assertIsNotNone(package_version)
        expected = package_version.group(1)

        import auracode
        from tools.version import FRAMEWORK_VERSION

        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), expected)
        self.assertEqual(auracode.__version__, expected)
        self.assertEqual(FRAMEWORK_VERSION, expected)
        self.assertIn(f"Status: {expected}", readme)
        self.assertIn(f"Status: {expected}", readme_pt)
        self.assertIn(f"## {expected} — Unreleased", changelog)

        versioned_json = {
            "MANIFEST.json": "framework_version",
            "contracts.json": "version",
            "self-assessment.json": "framework_version",
            "templates/assessment.json": "framework_version",
            "profiles/al1.json": "framework_version",
            "profiles/al2.json": "framework_version",
            "profiles/al3.json": "framework_version",
            "profiles/al4.json": "framework_version",
            "controls/catalog.json": "version",
            "controls/failure-modes.json": "version",
            "controls/source-registry.json": "version",
            "controls/standards-crosswalk.json": "version",
        }
        for relative_path, field in versioned_json.items():
            with self.subTest(path=relative_path):
                data = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
                self.assertEqual(data[field], expected)

        from tools import assurance_mcp, update_manifest, verify_dependencies

        self.assertEqual(assurance_mcp.SERVER_VERSION, expected)
        self.assertEqual(update_manifest.FRAMEWORK_VERSION, expected)
        self.assertEqual(verify_dependencies.FRAMEWORK_VERSION, expected)

        runtime_modules = (
            "tools/assurance_mcp.py",
            "tools/doctor.py",
            "tools/skill_packages.py",
            "tools/update_manifest.py",
            "tools/verify_dependencies.py",
        )
        for relative_path in runtime_modules:
            with self.subTest(runtime_version_source=relative_path):
                source = (ROOT / relative_path).read_text(encoding="utf-8")
                self.assertNotIn('ROOT / "VERSION"', source)

    def test_readmes_disclose_preview_and_certification_boundary(self) -> None:
        """Public docs must not present the unfinished builder as certified."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        readme_pt = (ROOT / "README.pt-BR.md").read_text(encoding="utf-8")

        self.assertIn("Development Preview", readme)
        self.assertIn("Prévia de Desenvolvimento", readme_pt)
        self.assertIn("not yet an end-to-end certified application builder", readme)
        self.assertIn("ainda não é um construtor de aplicações certificado de ponta a ponta", readme_pt)

        forbidden_english = (
            "Any founder, product owner, or non-technical creator is guided from scratch "
            "to delivering a production-ready, enterprise-grade software system."
        )
        forbidden_portuguese = (
            "Qualquer pessoa — mesmo sem experiência prévia em programação — é guiada do zero "
            "até a entrega de um sistema web ou aplicação profissional pronta para produção."
        )
        self.assertNotIn(forbidden_english, readme)
        self.assertNotIn(forbidden_portuguese, readme_pt)
        self.assertNotIn("**Enterprise Ready:** Modular, auditable, and certified software", readme)
        self.assertNotIn("**Enterprise Ready:** Software auditável, modular e certificado", readme_pt)

    def test_readmes_describe_installation_and_containment_limits(self) -> None:
        """Setup and safety claims must match the development preview that ships."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        readme_pt = (ROOT / "README.pt-BR.md").read_text(encoding="utf-8")

        required_in_both = (
            "auracode doctor",
            "auracode skills verify",
            "auracode skills install .",
            "NOT_RUN",
            "Aura Studio",
        )
        for phrase in required_in_both:
            with self.subTest(required_phrase=phrase):
                self.assertIn(phrase, readme)
                self.assertIn(phrase, readme_pt)

        self.assertIn("official signed distribution", readme)
        self.assertIn("distribuição oficial assinada", readme_pt)

        forbidden_claims = (
            "The Only Prerequisite",
            "O Único Pré-Requisito",
            "Intercepts all tool invocations",
            "Intercepta todas as invocações de ferramentas",
            "All outbound traffic is blocked by default",
            "Todo o tráfego de saída é bloqueado por padrão",
            "Neutralizes indirect prompt injection attacks",
            "Neutraliza ataques de prompt injection indireto",
            "Cryptographic verification against official package registries",
            "Verificação criptográfica nos registros oficiais de pacotes",
            "Complete 22-Command CLI Reference",
            "Catálogo Completo dos 22 Comandos CLI",
            "RESUMO_ENGENHARIA_SOFTWARE_AGENTES_INTELIGENTES.md",
            "suíte estática completa de 20 ferramentas",
        )
        combined = f"{readme}\n{readme_pt}"
        for claim in forbidden_claims:
            with self.subTest(forbidden_claim=claim):
                self.assertNotIn(claim, combined)

    def test_roadmap_marks_current_builder_work_in_progress(self) -> None:
        roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        self.assertIn("## 0.3 — Strategic Usability & Multi-Language Assurance (In Progress)", roadmap)
        self.assertNotIn("## 0.3 — Strategic Usability & Multi-Language Assurance (Completed)", roadmap)

    def test_official_skills_do_not_restore_absolute_or_scored_claims(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ROOT / ".agents" / "skills").glob("*/SKILL.md"))
        )
        forbidden = (
            "Pontuação de Saúde do Projeto",
            "sem risco de vazamento",
            "neutralizando ataques de exfiltração",
            "Garantir zero riscos de injeção",
            "12 verificadores estáticos AST",
            "Executa 12 testes automatizados",
            "até obter 100% de clareza",
            "mantendo 100% de comportamento",
            "garantir que a correção não introduziu",
        )
        for claim in forbidden:
            with self.subTest(claim=claim):
                self.assertNotIn(claim, combined)


if __name__ == "__main__":
    unittest.main()
