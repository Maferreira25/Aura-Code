#!/usr/bin/env python3
"""
AuraCode Clarify Engine (auracode-clarify).
Translates ambiguous requirements and technical choices into structured,
dilemma-based comparison menus with physical everyday analogies for lay users.
Ensures zero unspoken presumptions or hidden decisions enter the software blueprint.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Mandatory Layman Physical Analogies
PHYSICAL_ANALOGIES = {
    "database": ("Armário inteligente ou fichário organizado", "Onde as fichas de dados ficam guardadas em segurança"),
    "table": ("Gaveta específica do armário", "Exemplo: Gaveta de Clientes, Gaveta de Pedidos"),
    "record": ("Ficha preenchida dentro da gaveta", "Um único registro de informação de um cliente ou item"),
    "backend": ("A cozinha do restaurante", "Prepara as regras e receitas sem que o cliente veja"),
    "frontend": ("O salão do restaurante e o balcão da loja", "A vitrine onde as pessoas interagem e fazem os pedidos"),
    "api": ("O garçom", "Leva o pedido da mesa até a cozinha e traz a resposta pronta"),
    "auth": ("O crachá ou chave do portão", "Permite que a pessoa entre nas salas certas do prédio"),
    "encryption": ("Cofre trancado com segredo", "Protege os dados para que ninguém sem o segredo consiga ler"),
    "cloud": ("Computador alugado num prédio protegido", "Funciona 24 horas por dia com gerador e backup"),
    "deploy": ("Inauguração e abertura de portas da loja", "Momento em que o sistema começa a receber pessoas de verdade"),
}


def _call_llm(system_prompt: str, user_prompt: str, base_url: str, api_key: str, model: str, timeout: float = 15.0) -> Optional[str]:
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2
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


class ClarifyEngine:
    """Non-technical clarification engine for requirement briefing and ambiguity elimination."""

    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = (workspace_dir or Path.cwd()).resolve()
        self.api_key = os.environ.get("AURA_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
        self.base_url = os.environ.get("AURA_LLM_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        self.model = os.environ.get("AURA_LLM_MODEL") or "gpt-4o-mini"

    def clarify(self, topic_or_requirement: str) -> Dict[str, Any]:
        """Generate structured clarification menus with physical analogies."""
        topic = topic_or_requirement.strip()
        if not topic:
            topic = "Definição de regras de acesso e armazenamento do sistema"

        # Try LLM if configured
        if self.api_key or "localhost" in self.base_url or "127.0.0.1" in self.base_url:
            llm_res = self._clarify_with_llm(topic)
            if llm_res:
                return llm_res

        # Deterministic heuristic engine with zero presumption
        return self._clarify_deterministic(topic)

    def _clarify_with_llm(self, topic: str) -> Optional[Dict[str, Any]]:
        sys_prompt = (
            "Você é o Clarificador Não-Técnico (auracode-clarify) do Aura Code Framework. "
            "Sua regra fundamental é a Tolerância Zero a Presunções. Jamais infira regras silenciosamente. "
            "Traduza dúvidas técnicas em analogias do cotidiano (cozinha, garçom, gaveta de fichas, crachá, chave). "
            "Retorne estritamente um JSON com: context (frase curta), "
            "questions (lista de objetos com: id, topic, analogy_concept, option_a {title, desc, pro, con}, option_b {title, desc, pro, con}, residual_doubt_prompt)."
        )
        usr_prompt = f"Gere as perguntas de clarificação para esta demanda ou requisito: '{topic}'"
        raw = _call_llm(sys_prompt, usr_prompt, self.base_url, self.api_key, self.model)
        if not raw:
            return None

        try:
            clean = raw.strip().removeprefix("```json").removesuffix("```").strip()
            data = json.loads(clean)
            data["mode"] = "llm_agent"
            data["topic"] = topic
            return data
        except Exception:
            return None

    def _clarify_deterministic(self, topic: str) -> Dict[str, Any]:
        """Offline deterministic clarification engine using analogy heuristics."""
        topic_lower = topic.lower()

        questions = []
        if any(w in topic_lower for w in ("login", "auth", "usuario", "senha", "acesso", "permissao", "role")):
            questions.append({
                "id": "Q1_AUTH_METHOD",
                "topic": "Forma de identificação das pessoas usuárias",
                "analogy_concept": "Chave física vs Crachá digital",
                "option_a": {
                    "title": "Opção A: Como uma chave simples (E-mail e Senha tradicional)",
                    "desc": "O usuário digita sua senha memorizada a cada acesso ao prédio.",
                    "pro": "Fácil e familiar para qualquer pessoa.",
                    "con": "Se o usuário esquecer a senha, precisará do fluxo de redefinição."
                },
                "option_b": {
                    "title": "Opção B: Como um código temporário por SMS ou E-mail (Sem senha)",
                    "desc": "O sistema envia um crachá de 6 dígitos que expira em poucos minutos.",
                    "pro": "Ninguém precisa memorizar senhas nem tem senhas roubadas.",
                    "con": "Depende do celular ou e-mail estar disponível no momento do login."
                },
                "residual_doubt_prompt": "Ficou clara essa diferença de segurança ou gostaria de entender mais antes de decidir?"
            })

        if any(w in topic_lower for w in ("dados", "banco", "salvar", "arquivo", "relatorio", "cadastro", "fichario")):
            questions.append({
                "id": "Q2_STORAGE_LOCATION",
                "topic": "Onde guardar os documentos e fichas",
                "analogy_concept": "Gaveta local vs Arquivo blindado na nuvem",
                "option_a": {
                    "title": "Opção A: Como uma pasta no seu computador (Armazenamento Local)",
                    "desc": "Os dados ficam gravados diretamente na mesma máquina onde o programa roda.",
                    "pro": "Não tem custo extra de servidor externo e funciona offline.",
                    "con": "Se o computador estragar ou for roubado, os dados podem ser perdidos sem backup."
                },
                "option_b": {
                    "title": "Opção B: Como um armário de aço em cofre de banco (Banco de Dados na Nuvem)",
                    "desc": "As fichas são guardadas num computador protegido com cópias automáticas todo dia.",
                    "pro": "Acessível de qualquer lugar com proteção contra perdas físicas.",
                    "con": "Exige conexão com a internet e eventual custo de hospedagem."
                },
                "residual_doubt_prompt": "Qual dessas opções atende melhor ao volume que você espera?"
            })

        if not questions:
            # General fallback question for any requirement
            questions.append({
                "id": "Q_GENERAL_SCOPE",
                "topic": f"Limite exato da funcionalidade: {topic}",
                "analogy_concept": "Reforma pontual na sala vs Reforma no prédio inteiro",
                "option_a": {
                    "title": "Opção A: Foco Cirúrgico e Essencial (Versão Enxuta)",
                    "desc": "Implementar apenas o núcleo sem adicionar recursos periféricos agora.",
                    "pro": "Entrega rápida, custo baixo e facilidade de testar.",
                    "con": "Funcionalidades avançadas ficam para uma fase posterior."
                },
                "option_b": {
                    "title": "Opção B: Solução Completa e Abrangente",
                    "desc": "Incluir notificações, logs de auditoria e configurações detalhadas.",
                    "pro": "Fica pronto e robusto para escala imediata.",
                    "con": "Exige mais tempo de validação e testes mais complexos."
                },
                "residual_doubt_prompt": "Qual nível de profundidade você aprova para iniciarmos?"
            })

        return {
            "mode": "deterministic_analogy_engine",
            "topic": topic,
            "context": f"Clarificação estruturada de requisitos para: '{topic}'",
            "analogies_used": [PHYSICAL_ANALOGIES.get("database"), PHYSICAL_ANALOGIES.get("auth")],
            "questions": questions
        }

    def save_clarification(self, result: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """Persist clarification outcome in markdown format for SDD compliance."""
        out_dir = self.workspace_dir / "_auracode_sdd"
        out_dir.mkdir(parents=True, exist_ok=True)
        dest = output_path or (out_dir / "00_clarification_briefing.md")

        md_lines = [
            f"# Aura Code — Briefing de Clarificação de Requisitos",
            f"",
            f"> **Tópico Analisado:** {result.get('topic', 'Geral')}",
            f"> **Motor de Execução:** {result.get('mode', 'deterministic')}",
            f"",
            f"---",
            f"",
            f"## ❓ Questões Decisórias Obrigatórias (Zero Presunção)",
            f"",
        ]

        for q in result.get("questions", []):
            md_lines.extend([
                f"### {q.get('topic')} (`{q.get('id')}`)",
                f"**Conceito Analógico:** {q.get('analogy_concept')}",
                f"",
                f"- **{q.get('option_a', {}).get('title')}**",
                f"  - *Descrição:* {q.get('option_a', {}).get('desc')}",
                f"  - *Vantagem:* {q.get('option_a', {}).get('pro')}",
                f"  - *Atenção:* {q.get('option_a', {}).get('con')}",
                f"",
                f"- **{q.get('option_b', {}).get('title')}**",
                f"  - *Descrição:* {q.get('option_b', {}).get('desc')}",
                f"  - *Vantagem:* {q.get('option_b', {}).get('pro')}",
                f"  - *Atenção:* {q.get('option_b', {}).get('con')}",
                f"",
                f"> **Pergunta Final:** *{q.get('residual_doubt_prompt')}*",
                f"",
                f"---",
                f""
            ])

        with open(dest, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        return dest


def main() -> None:
    args = sys.argv[1:]
    is_json = "--json" in args
    save_file = "--save" in args
    args = [a for a in args if a not in ("--json", "--save")]
    topic = " ".join(args).strip() if args else "Requisitos do Sistema"

    engine = ClarifyEngine()
    res = engine.clarify(topic)

    if save_file:
        saved_path = engine.save_clarification(res)
        res["saved_to"] = str(saved_path)

    if is_json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(f"\n=======================================================")
        print(f"   AURA CODE — CLARIFICAÇÃO E BRIEFING NÃO-TÉCNICO")
        print(f"=======================================================")
        print(f"Tópico: {res.get('topic')}")
        print(f"Motor: {res.get('mode')}\n")
        for q in res.get("questions", []):
            print(f"[{q.get('id')}] {q.get('topic')}")
            print(f"Analogia: {q.get('analogy_concept')}")
            print(f" -> {q.get('option_a', {}).get('title')}")
            print(f"    Vantagem: {q.get('option_a', {}).get('pro')}")
            print(f" -> {q.get('option_b', {}).get('title')}")
            print(f"    Vantagem: {q.get('option_b', {}).get('pro')}")
            print(f">> {q.get('residual_doubt_prompt')}\n")

        if save_file:
            print(f"Briefing salvo em: {res.get('saved_to')}")


if __name__ == "__main__":
    main()
