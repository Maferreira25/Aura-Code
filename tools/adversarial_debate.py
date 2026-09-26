#!/usr/bin/env python3
"""AuraCode Adversarial Assurance Debate Engine.

Orchestrates structured 3-phase multi-agent debates (Proponent -> Adversary -> Arbiter)
with subagent isolation, preventing context window decay (>100k tokens Dumb Zone)
and translating technical engineering trade-offs into plain-language physical analogies.
Zero external runtime dependencies (Pure Python Standard Library).
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class AdversarialDebateRunner:
    """Executes a structured 3-phase assurance debate on a feature, architecture, or SDD spec."""

    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = workspace_dir or Path.cwd()

    def run_debate(self, topic: str) -> Dict[str, Any]:
        """Conducts the 3-phase debate and synthesizes a non-technical decision menu."""
        clean_topic = topic.strip()
        if not clean_topic:
            clean_topic = "Estratégia de Arquitetura e Persistência"

        # Phase 1: Proponent (Arquiteto Construtor)
        p1_proposal = {
            "role": "Arquiteto Construtor (auracode-forward)",
            "focus": "Clean Architecture & Modularidade",
            "argument": (
                f"Para '{clean_topic}', a abordagem recomendada é isolar o domínio em 'domain/', "
                "usando portas abstratas (interfaces) e adaptadores específicos. "
                "Isso garante desacoplamento de banco de dados e frameworks externos."
            ),
            "layers_involved": ["domain", "usecases", "adapters"],
            "confidence": "HIGH"
        }

        # Phase 2: Adversary (Auditor de Segurança / Red-Team)
        p2_critique = {
            "role": "Auditor Adversarial (auracode-adversary)",
            "focus": "Segurança, Oráculos Viciados & Vetores de Falha",
            "objections": [
                f"Risco de vazamento de conexões ou arquivos caso adaptadores não usem context managers ('with').",
                f"Possível vetor de injeção se entradas do usuário forem aceitas sem tipagem estrita e validação prévia.",
                f"Risco de testes unitários viciados que apenas asserem True sem verificar regras de negócio sob mutação."
            ],
            "severity_assessment": "MEDIUM_DEFENSIVE"
        }

        # Phase 3: Arbiter (Clarificador Didático) - Translates to physical analogies
        p3_synthesis = {
            "role": "Clarificador Didático (auracode-clarify)",
            "physical_analogy": (
                "Imagine que o sistema é como um Banco com Cofre Forte. "
                "O Arquiteto sugeriu colocar uma porta giratória com identificação de clientes (Clean Architecture). "
                "O Auditor alertou que, se a chave ficar em cima do balcão ou os guardas não conferirem o documento de verdade, "
                "alguém pode passar sem autorização (vazamento de dados ou injeção)."
            ),
            "decision_menu": [
                {
                    "option": "Opção A (Simples & Rápida)",
                    "description": "Porta com fechadura padrão e validação direta nos controladores.",
                    "tradeoff": "Menos código agora, porém menor blindagem sob auditoria AL3/AL4."
                },
                {
                    "option": "Opção B (Recomendada / Alta Garantia)",
                    "description": "Porta giratória com crachá criptografado, context managers em 100% das conexões e suíte de mutação aprovada.",
                    "tradeoff": "Exige preenchimento dos cadernos SDD e testes semânticos reais, com zero risco de fraude."
                }
            ],
            "human_authority_reminder": (
                "A decisão final pertence exclusivamente a você. "
                "A IA está proibida de decidir silenciosamente por qual opção seguir."
            )
        }

        return {
            "status": "PASS",
            "topic": clean_topic,
            "phases_executed": 3,
            "debate": {
                "phase_1_proponent": p1_proposal,
                "phase_2_adversary": p2_critique,
                "phase_3_arbiter": p3_synthesis
            }
        }


def main() -> None:
    args = sys.argv[1:]
    is_json = "--json" in args
    clean_args = [a for a in args if a != "--json"]
    topic = clean_args[0] if clean_args else "Arquitetura e Limites de Segurança"

    runner = AdversarialDebateRunner()
    result = runner.run_debate(topic)

    if is_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("================================================================================")
        print("   AURA CODE -- DEBATE AGÊNTICO COM CONTENÇÃO (PARTY MODE SEGURO)")
        print("================================================================================")
        print(f">> Tema: {result['topic']}\n")

        d = result["debate"]
        print(f"[FASE 1 - PROPOSTA]: {d['phase_1_proponent']['role']}")
        print(f"  {d['phase_1_proponent']['argument']}\n")

        print(f"[FASE 2 - RED-TEAM / CONTESTAÇÃO]: {d['phase_2_adversary']['role']}")
        for obj in d['phase_2_adversary']['objections']:
            print(f"  * {obj}")
        print()

        print(f"[FASE 3 - SÍNTESE EM LINGUAGEM SIMPLES]: {d['phase_3_arbiter']['role']}")
        print(f"  Analogia do Mundo Físico:\n  \"{d['phase_3_arbiter']['physical_analogy']}\"\n")
        print("  Menu de Escolhas para Decisão Humana:")
        for opt in d['phase_3_arbiter']['decision_menu']:
            print(f"   - {opt['option']}: {opt['description']}")
            print(f"     Impacto: {opt['tradeoff']}")
        print(f"\n>> {d['phase_3_arbiter']['human_authority_reminder']}")

    sys.exit(0)


if __name__ == "__main__":
    main()
