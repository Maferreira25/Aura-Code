#!/usr/bin/env python3
"""AuraCode Adversarial Assurance Debate Engine.

Orchestrates structured 3-phase multi-agent debates (Proponent -> Adversary -> Arbiter)
with subagent isolation, preventing context window decay (>100k tokens Dumb Zone)
and translating technical engineering trade-offs into plain-language physical analogies.

Supports real LLM execution via OpenAI-compatible endpoints (OpenAI, Ollama, Groq,
OpenRouter, vLLM) or transparent deterministic rule-based analysis when offline.
Zero external runtime dependencies (Pure Python Standard Library: urllib, json, os).
"""

import sys
import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional, List

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _call_llm(system_prompt: str, user_prompt: str, base_url: str, api_key: str, model: str, timeout: float = 15.0) -> Optional[str]:
    """Invoke an OpenAI-compatible chat completion endpoint using stdlib urllib."""
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 800
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}" if api_key else "Bearer none"
    }

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError, OSError):
        return None


class AdversarialDebateRunner:
    """Executes a structured 3-phase assurance debate on a feature, architecture, or SDD spec."""

    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = workspace_dir or Path.cwd()
        # Configuration for LLM subagents
        self.api_key = os.environ.get("AURA_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
        self.base_url = os.environ.get("AURA_LLM_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        self.model = os.environ.get("AURA_LLM_MODEL") or "gpt-4o-mini"

    def _execute_with_llm(self, topic: str) -> Optional[Dict[str, Any]]:
        """Run genuine 3-phase multi-agent debate using configured LLM subagents."""
        # Subagent 1: Proponent (auracode-forward)
        p1_sys = (
            "Você é o Arquiteto Construtor (auracode-forward) do Aura Code Framework. "
            "Sua missão é propor uma implementação elegante, modular e desacoplada baseada em Clean Architecture "
            "(camadas domain/, usecases/, adapters/, infrastructure/). "
            "Responda estritamente em formato JSON com as chaves: focus, argument, layers_involved (lista), confidence (HIGH|MEDIUM)."
        )
        p1_usr = f"Proponha a solução arquitetural ideal para: '{topic}'"
        p1_raw = _call_llm(p1_sys, p1_usr, self.base_url, self.api_key, self.model)
        if not p1_raw:
            return None

        try:
            clean_json = p1_raw.strip().removeprefix("```json").removesuffix("```").strip()
            p1_data = json.loads(clean_json)
        except Exception:
            p1_data = {
                "focus": "Clean Architecture & Modularidade",
                "argument": p1_raw,
                "layers_involved": ["domain", "usecases", "adapters"],
                "confidence": "HIGH"
            }

        p1_proposal = {
            "role": "Arquiteto Construtor (auracode-forward)",
            "focus": p1_data.get("focus", "Clean Architecture & Modularidade"),
            "argument": p1_data.get("argument", f"Para '{topic}', isolar o domínio em 'domain/' garantindo desacoplamento."),
            "layers_involved": p1_data.get("layers_involved", ["domain", "usecases", "adapters"]),
            "confidence": p1_data.get("confidence", "HIGH")
        }

        # Subagent 2: Adversary (auracode-adversary)
        p2_sys = (
            "Você é o Auditor Adversarial (auracode-adversary) do Aura Code Framework. "
            "Atue como Red-Team rigoroso, procurando falhas STRIDE, vazamento de recursos (leaks), injeções (sec) "
            "e oráculos viciados na proposta do arquiteto. "
            "Responda estritamente em formato JSON com as chaves: focus, objections (lista de 3 strings), severity_assessment."
        )
        p2_usr = f"Conteste criticamente esta proposta para '{topic}':\n{p1_proposal['argument']}"
        p2_raw = _call_llm(p2_sys, p2_usr, self.base_url, self.api_key, self.model)

        if p2_raw:
            try:
                clean_json = p2_raw.strip().removeprefix("```json").removesuffix("```").strip()
                p2_data = json.loads(clean_json)
            except Exception:
                p2_data = {
                    "focus": "Segurança, Oráculos Viciados & Vetores de Falha",
                    "objections": [p2_raw],
                    "severity_assessment": "MEDIUM_DEFENSIVE"
                }
        else:
            p2_data = {
                "focus": "Segurança & Contenção Defensiva",
                "objections": [f"Avaliar possíveis vetores de injeção e vazamento de conexões em '{topic}'."],
                "severity_assessment": "MEDIUM_DEFENSIVE"
            }

        p2_critique = {
            "role": "Auditor Adversarial (auracode-adversary)",
            "focus": p2_data.get("focus", "Segurança, Oráculos Viciados & Vetores de Falha"),
            "objections": p2_data.get("objections", []),
            "severity_assessment": p2_data.get("severity_assessment", "MEDIUM_DEFENSIVE")
        }

        # Subagent 3: Arbiter (auracode-clarify)
        p3_sys = (
            "Você é o Clarificador Didático (auracode-clarify) do Aura Code Framework. "
            "Sua missão é sintetizar o debate entre o Arquiteto e o Auditor para uma pessoa leiga sem termos técnicos. "
            "Crie uma analogia do mundo físico (armário, banco, restaurante, prédio) e monte um menu de 2 escolhas (Opção A vs Opção B) com tradeoffs. "
            "Responda estritamente em formato JSON com as chaves: physical_analogy, decision_menu (lista de 2 objetos com option, description, tradeoff), human_authority_reminder."
        )
        p3_usr = (
            f"Tema: {topic}\n"
            f"Proposta do Arquiteto: {p1_proposal['argument']}\n"
            f"Objeções do Auditor: {json.dumps(p2_critique['objections'], ensure_ascii=False)}"
        )
        p3_raw = _call_llm(p3_sys, p3_usr, self.base_url, self.api_key, self.model)

        if p3_raw:
            try:
                clean_json = p3_raw.strip().removeprefix("```json").removesuffix("```").strip()
                p3_data = json.loads(clean_json)
            except Exception:
                p3_data = {
                    "physical_analogy": p3_raw,
                    "decision_menu": [
                        {"option": "Opção A", "description": "Abordagem rápida", "tradeoff": "Menor blindagem"},
                        {"option": "Opção B", "description": "Abordagem modular estrita", "tradeoff": "Exige mais cadernos"}
                    ],
                    "human_authority_reminder": "A decisão final pertence exclusivamente a você."
                }
        else:
            p3_data = {
                "physical_analogy": f"O tema '{topic}' assemelha-se à organização de um cofre com controle de chaves e conferência na entrada.",
                "decision_menu": [
                    {"option": "Opção A (Simples)", "description": "Implementação direta", "tradeoff": "Menos código, menor blindagem AL3/AL4"},
                    {"option": "Opção B (Garantida)", "description": "Contratos Clean Architecture e testes com mutação", "tradeoff": "Garante zero vazamento"}
                ],
                "human_authority_reminder": "A decisão final pertence exclusivamente a você."
            }

        p3_synthesis = {
            "role": "Clarificador Didático (auracode-clarify)",
            "physical_analogy": p3_data.get("physical_analogy", ""),
            "decision_menu": p3_data.get("decision_menu", []),
            "human_authority_reminder": p3_data.get("human_authority_reminder", "A decisão final pertence exclusivamente a você. A IA está proibida de decidir silenciosamente por qual opção seguir.")
        }

        return {
            "status": "PASS",
            "topic": topic,
            "engine_mode": "llm_subagents",
            "model_used": self.model,
            "phases_executed": 3,
            "debate": {
                "phase_1_proponent": p1_proposal,
                "phase_2_adversary": p2_critique,
                "phase_3_arbiter": p3_synthesis
            }
        }

    def _execute_contextual_rules(self, clean_topic: str) -> Dict[str, Any]:
        """Deterministic, transparent domain analysis when no external LLM is configured."""
        topic_lower = clean_topic.lower()
        
        # Determine domain context
        if any(w in topic_lower for w in ("cache", "redis", "memoria", "memcached")):
            focus = "Estratégia de Cache & Invalidação"
            analogia = "É como uma gaveta rápida na bancada do cozinheiro para temperos frequentes, versus buscar no depósito do fundo toda vez."
            obj1 = "Risco de 'stale cache' (dados desatualizados entregues ao usuário)."
            obj2 = "Possível vazamento de memória ou de conexões caso o pool de clientes Redis não seja fechado."
            obj3 = "Testes que testam apenas o cache local em memória e não exercem falhas de rede."
            opt_a = ("Cache em memória local (Process Cache)", "Mais simples e sem dependência externa.", "Não escala entre múltiplos nós e perde dados no restart.")
            opt_b = ("Cache distribuído (Redis/Key-Value)", "Escalável e com TTL controlado.", "Exige infraestrutura adicional e tratamento de indisponibilidade.")
        elif any(w in topic_lower for w in ("auth", "jwt", "login", "senha", "sessao", "token")):
            focus = "Controle de Acesso & Autenticação"
            analogia = "É como decidir entre uma pulseira de festa intransferível com carimbo (JWT) ou um livro na portaria com o nome dos convidados (Sessão)."
            obj1 = "Tokens JWT sem revogação ativa podem continuar válidos mesmo após logout."
            obj2 = "Risco de vazamento de segredo de assinatura (SECRET_KEY) em repositório."
            obj3 = "Oráculos de teste que asserem apenas presença de token sem validar expiração e assinatura."
            opt_a = ("Sessão em banco de dados/Redis", "Permite revogação instantânea de acessos.", "Requer consulta de I/O em cada requisição.")
            opt_b = ("Token JWT stateless", "Rápido e não consulta banco em toda rota.", "Exige lista de revogação para invalidação de emergência.")
        elif any(w in topic_lower for w in ("sql", "banco", "database", "postgres", "persistencia")):
            focus = "Persistência & Integridade Transacional"
            analogia = "É como um livro-razão contábil onde cada débito e crédito deve ser registrado ao mesmo tempo para não sumir dinheiro."
            obj1 = "Risco de injeção SQL caso parâmetros não usem query parametrizada."
            obj2 = "Conexões órfãs caso não sejam gerenciadas por context managers ('with')."
            obj3 = "Falta de testes cobrindo rollback automático sob falhas parciais."
            opt_a = ("ORM com migrations automáticas", "Produtividade inicial elevada.", "Risco de queries N+1 e complexidade oculta.")
            opt_b = ("Repositório com SQL explícito parametrizado", "Controle total e performance auditável.", "Exige escrita manual de mapeadores.")
        else:
            focus = "Clean Architecture & Modularidade"
            analogia = "Imagine que o sistema é como um Banco com Cofre Forte. O Arquiteto sugere isolar o cofre em uma sala blindada (domain/), enquanto o Auditor confere se os guardas realmente checam crachás na entrada."
            obj1 = "Risco de vazamento de conexões ou recursos caso adaptadores não usem context managers ('with')."
            obj2 = "Possível vetor de injeção se entradas do usuário forem aceitas sem validação e tipagem estrita."
            obj3 = "Risco de testes unitários viciados que apenas asserem True sem verificar regras de negócio sob mutação."
            opt_a = ("Opção A (Simples & Rápida)", "Implementação direta nos controladores.", "Menos código inicial, porém menor blindagem sob auditoria AL3/AL4.")
            opt_b = ("Opção B (Recomendada / Alta Garantia)", "Isolamento sob Clean Architecture e suíte com mutação aprovada.", "Blindagem formal e rastreabilidade total.")

        p1_proposal = {
            "role": "Arquiteto Construtor (auracode-forward)",
            "focus": f"Clean Architecture: {focus}",
            "argument": (
                f"Para '{clean_topic}', a abordagem recomendada é isolar o domínio em 'domain/', "
                "usando portas abstratas (interfaces) e adaptadores específicos em 'adapters/'. "
                "Isso garante desacoplamento de infraestrutura e viabiliza testes isolados."
            ),
            "layers_involved": ["domain", "usecases", "adapters"],
            "confidence": "HIGH"
        }

        p2_critique = {
            "role": "Auditor Adversarial (auracode-adversary)",
            "focus": "Segurança, Oráculos Viciados & Vetores de Falha",
            "objections": [obj1, obj2, obj3],
            "severity_assessment": "MEDIUM_DEFENSIVE"
        }

        p3_synthesis = {
            "role": "Clarificador Didático (auracode-clarify)",
            "physical_analogy": analogia,
            "decision_menu": [
                {
                    "option": opt_a[0],
                    "description": opt_a[1],
                    "tradeoff": opt_a[2]
                },
                {
                    "option": opt_b[0],
                    "description": opt_b[1],
                    "tradeoff": opt_b[2]
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
            "engine_mode": "contextual_rules",
            "note": "Modo de análise contextual ativa. Para debate com subagentes LLM dinâmicos, configure OPENAI_API_KEY ou AURA_LLM_BASE_URL.",
            "phases_executed": 3,
            "debate": {
                "phase_1_proponent": p1_proposal,
                "phase_2_adversary": p2_critique,
                "phase_3_arbiter": p3_synthesis
            }
        }

    def run_debate(self, topic: str) -> Dict[str, Any]:
        """Conducts the 3-phase debate using real LLM subagents if configured, or transparent contextual rules."""
        clean_topic = topic.strip()
        if not clean_topic:
            clean_topic = "Estratégia de Arquitetura e Persistência"

        # If LLM endpoint or key is configured, attempt real subagent execution
        if self.api_key or "localhost" in self.base_url or "127.0.0.1" in self.base_url:
            llm_result = self._execute_with_llm(clean_topic)
            if llm_result:
                return llm_result

        # Transparent fallback to domain-specific contextual rules
        return self._execute_contextual_rules(clean_topic)


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
        print(f">> Tema: {result['topic']}")
        print(f">> Modo de Execução: {result.get('engine_mode', 'standard')} (Fases: {result['phases_executed']})\n")

        d = result["debate"]
        print(f"[FASE 1 - PROPOSTA]: {d['phase_1_proponent']['role']}")
        print(f"  Foco: {d['phase_1_proponent']['focus']}")
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

