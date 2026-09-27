#!/usr/bin/env python3
"""AuraCode Interactive Briefing Wizard (TUI).

Guides lay/non-technical users through structured, zero-presumption requirements
interviews using everyday physical analogies and generates draft House Blueprints (SDD).
The wizard never treats a short interview or a generated template as proof of clarity.
Zero external runtime dependencies (Pure Python Standard Library).
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class BriefingIncompleteError(RuntimeError):
    """Raised when a required user decision is missing or invalid."""


class AuraWizard:
    """Interactive non-technical requirements briefing assistant."""

    def __init__(self, workspace_dir: Optional[Path] = None, inputs: Optional[List[str]] = None):
        self.workspace = workspace_dir if workspace_dir else Path.cwd()
        self.inputs = list(inputs) if inputs is not None else None
        self.input_index = 0

    def _prompt(self, message: str, default: str = "") -> str:
        """Read input from interactive user or mock input list."""
        if self.inputs is not None:
            if self.input_index < len(self.inputs):
                val = self.inputs[self.input_index]
                self.input_index += 1
                return val if val.strip() else default
            return default
        try:
            val = input(f"{message} " + (f"[{default}]: " if default else ": "))
            return val.strip() if val.strip() else default
        except (EOFError, KeyboardInterrupt):
            print("\nOperação cancelada pelo usuário.")
            sys.exit(0)

    def _required_prompt(self, message: str) -> str:
        """Ask until the user supplies a decision; never invent a default."""
        while True:
            value = self._prompt(message).strip()
            if value:
                return value
            print(">> Esta decisão é obrigatória e não será preenchida pela IA.")
            if self.inputs is not None and self.input_index >= len(self.inputs):
                raise BriefingIncompleteError(f"Decisão obrigatória ausente: {message}")

    def _choice_prompt(self, message: str, allowed: Dict[str, str]) -> str:
        """Require an explicit menu choice without silently selecting an option."""
        while True:
            choice = self._required_prompt(message).upper()
            if choice in allowed:
                return choice
            print(f">> Escolha inválida. Opções permitidas: {', '.join(allowed)}.")
            if self.inputs is not None and self.input_index >= len(self.inputs):
                raise BriefingIncompleteError(f"Escolha obrigatória inválida: {message}")

    def print_banner(self) -> None:
        banner = """
================================================================================
   AURA CODE -- ASSISTENTE DE CONSTRUÇÃO DE SOFTWARE PARA PESSOAS LEIGAS
================================================================================
  "Construindo seu software como se constrói uma casa de engenharia sênior:
   planejando a planta completa antes de assentar o primeiro tijolo."
================================================================================
"""
        print(banner)

    def run(self) -> Dict[str, Any]:
        self.print_banner()

        print("ETAPA 1 DE 5: ESCOLHA DO PORTE DA CONSTRUÇÃO (PERFIL DE GARANTIA)")
        print("Qual o tamanho da obra que você deseja construir?")
        print("  1 - Micro (AL1): Uma reforma rápida ou script utilitário (1 documento).")
        print("  2 - Lite (AL2): Um protótipo / MVP funcional para validar ideia (3 documentos).")
        print("  3 - Standard (AL3): Uma casa completa / Aplicação web profissional (7 cadernos).")
        print("  4 - Enterprise (AL4): Um edifício corporativo / Sistema de alta criticidade (15 cadernos).")
        
        profile_map = {
            "1": "micro",
            "2": "lite",
            "3": "standard",
            "4": "enterprise"
        }
        choice = self._choice_prompt("Escolha uma opção (1 a 4)", profile_map)
        profile = profile_map[choice]
        print(f"\n>> Perfil selecionado: {profile.upper()}\n")

        print("ETAPA 2 DE 5: IDENTIFICAÇÃO E MISSÃO DO PROJETO")
        project_name = self._required_prompt("Qual o nome do seu projeto ou sistema?")
        print("\nImagine que você está explicando para uma pessoa amiga que não entende de tecnologia:")
        mission = self._required_prompt("O que esse sistema vai fazer na prática?")

        print("\nETAPA 3 DE 5: QUEM VAI USAR (PERFIS DE ACESSO)")
        print("Pense nas pessoas autorizadas a entrar no prédio:")
        users_desc = self._required_prompt(
            "Quem usará o sistema? (Ex: clientes que só visualizam, operadores e gerente administrador)"
        )

        print("\nETAPA 4 DE 5: ONDE OS DADOS FICAM GUARDADOS (O ARMÁRIO INTELIGENTE)")
        print("Como suas informações devem ser guardadas?")
        print("  A - Arquivo local simples (como uma planilha ou gaveta rápida)")
        print("  B - Banco de dados estruturado (como um armário de fichas seguro com chave)")
        print("  C - Nuvem corporativa com backup automático")
        storage_choice = self._choice_prompt(
            "Escolha o armário (A, B ou C)",
            {"A": "local", "B": "database", "C": "cloud"},
        )

        print("\nETAPA 5 DE 5: O QUE O SISTEMA NÃO DEVE FAZER (EXCLUSÕES DE ESCOPO)")
        print("Para evitar que a IA invente coisas caras ou desnecessárias:")
        exclusions = self._required_prompt(
            "Existe algo que você NÃO quer neste momento? "
            "(Ex: pagamentos com cartão, envio de SMS; responda 'nenhum' se for sua decisão)"
        )

        print("\n================================================================================")
        print(">> GERANDO A PLANTA DA CASA EM _auracode_sdd/...")
        print("================================================================================")

        # Scaffolding target directories and templates
        from tools.assurance import setup_auracode_environment
        setup_auracode_environment(profile=profile, copy_templates=True, target_dir=self.workspace)
        sdd_dir = self.workspace / "_auracode_sdd"

        # Customize the first spec with collected plain-language data
        customization_note = f"""

---
### Informações do Briefing Coletadas no Assistente

- **Nome do Projeto:** {project_name}
- **Missão Prática:** {mission}
- **Pessoas Autorizadas:** {users_desc}
- **Modelo de Armazenamento:** Opção {storage_choice}
- **Exclusões Explícitas:** {exclusions}
- **Perfil de Garantia Ativo:** {profile.upper()}
"""

        first_spec = None
        if profile == "micro":
            first_spec = sdd_dir / "01_task_spec.md"
        elif profile == "lite":
            first_spec = sdd_dir / "01_visao_e_regras.md"
        elif profile in ("standard", "basic"):
            first_spec = sdd_dir / "01_visao_geral_e_negocio.md"
        elif profile == "enterprise":
            first_spec = sdd_dir / "01_PRD.md"

        if first_spec and first_spec.exists():
            existing = first_spec.read_text(encoding="utf-8")
            first_spec.write_text(existing + customization_note, encoding="utf-8")

        print(">> RASCUNHO DA PLANTA GERADO COM SUCESSO!")
        print(f">> Localização: {sdd_dir}")
        print("\n>> CLAREZA: NOT_RUN — o questionário curto não comprova requisitos completos.")
        print("A planta continua como RASCUNHO e ainda não está aprovada para construção.")
        print("Próximo passo: revise todos os cadernos, esclareça as decisões obrigatórias e execute `auracode ambiguity .`.")
        print("Mesmo com a varredura limpa, a construção só pode começar após aprovação humana explícita da revisão exata.")

        return {
            "success": True,
            "briefing_status": "DRAFT",
            "clarity_status": "NOT_RUN",
            "approved": False,
            "construction_allowed": False,
            "project_name": project_name,
            "profile": profile,
            "mission": mission,
            "sdd_directory": str(sdd_dir),
            "files_created": [f.name for f in sdd_dir.glob("*.md")]
        }


def main() -> None:
    wizard = AuraWizard()
    try:
        res = wizard.run()
    except BriefingIncompleteError as exc:
        print(f"\nBRIEFING INCOMPLETO: {exc}")
        sys.exit(1)
    sys.exit(0 if res.get("success") else 1)


if __name__ == "__main__":
    main()
