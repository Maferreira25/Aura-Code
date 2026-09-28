#!/usr/bin/env python3
"""
AuraCode Brainstorm Engine (auracode-brainstorm).
Helps lay users mature an initial raw idea, transforming abstract desires into
concrete prioritized features (Essenciais, Desejáveis, Futuras) and a pre-mortem risk analysis
before drafting the House Blueprint (Planta Teórica).
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


def _call_llm(system_prompt: str, user_prompt: str, base_url: str, api_key: str, model: str, timeout: float = 15.0) -> Optional[str]:
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3
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


class BrainstormEngine:
    """Ideation and feature prioritization engine for early-stage software concepts."""

    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = (workspace_dir or Path.cwd()).resolve()
        self.api_key = os.environ.get("AURA_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
        self.base_url = os.environ.get("AURA_LLM_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        self.model = os.environ.get("AURA_LLM_MODEL") or "gpt-4o-mini"

    def brainstorm(self, raw_idea: str) -> Dict[str, Any]:
        """Process raw user idea into prioritized features and pre-mortem risks."""
        idea = raw_idea.strip()
        if not idea:
            idea = "Sistema web de gestão e agendamento de serviços"

        if self.api_key or "localhost" in self.base_url or "127.0.0.1" in self.base_url:
            llm_res = self._brainstorm_with_llm(idea)
            if llm_res:
                return llm_res

        return self._brainstorm_deterministic(idea)

    def _brainstorm_with_llm(self, idea: str) -> Optional[Dict[str, Any]]:
        sys_prompt = (
            "Você é o Agente de Ideação (auracode-brainstorm) do Aura Code Framework. "
            "Sua missão é ajudar uma pessoa leiga a estruturar uma ideia bruta em: "
            "1. Visão simples do produto em linguagem cotidiana; "
            "2. Três níveis de prioridade de recursos: "
            "   - essential (o que não pode faltar no primeiro dia); "
            "   - desirable (o que seria ótimo ter logo em seguida); "
            "   - future (ideias avançadas para fases posteriores); "
            "3. Pre-mortem didático (riscos operacionais ou de uso que poderiam dar errado). "
            "Responda estritamente em JSON com as chaves: vision, essential (lista), desirable (lista), future (lista), premortem_risks (lista)."
        )
        usr_prompt = f"Estruture e amadureça a seguinte ideia de software: '{idea}'"
        raw = _call_llm(sys_prompt, usr_prompt, self.base_url, self.api_key, self.model)
        if not raw:
            return None

        try:
            clean = raw.strip().removeprefix("```json").removesuffix("```").strip()
            data = json.loads(clean)
            data["mode"] = "llm_agent"
            data["raw_idea"] = idea
            return data
        except Exception:
            return None

    def _brainstorm_deterministic(self, idea: str) -> Dict[str, Any]:
        """Offline deterministic brainstorm synthesis with senior product heuristics."""
        return {
            "mode": "deterministic_heuristics",
            "raw_idea": idea,
            "vision": f"Construir uma solução simples, segura e direta ao ponto para atender à necessidade: '{idea}'.",
            "essential": [
                "Cadastro e autenticação segura de usuários (login básico e controle de acesso).",
                "Armazenamento persistente e organizado dos dados principais da aplicação.",
                "Interface limpa para consulta, criação e edição dos registros essenciais."
            ],
            "desirable": [
                "Exportação de relatórios ou resumos em formato legível.",
                "Filtros de busca rápida para localizar itens cadastrados com facilidade.",
                "Notificações ou alertas simples sobre prazos ou alterações de status."
            ],
            "future": [
                "Integração com meios de pagamento ou emissão automática de cobranças.",
                "Painel com gráficos analíticos de desempenho e métricas avançadas.",
                "Aplicativo móvel nativo ou sincronização em tempo real entre filiais."
            ],
            "premortem_risks": [
                "Complexidade desnecessária no primeiro lançamento: tentar abraçar o mundo antes de validar o básico.",
                "Perda de dados por falta de rotina de backup estruturada.",
                "Interface confusa que exija treinamento demorado para os usuários finais."
            ],
            "next_step": "Executar 'auracode wizard' ou 'auracode clarify' para transformar este escopo na Planta Teórica (_auracode_sdd/)."
        }

    def save_brainstorm(self, result: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """Persist brainstorm synthesis to _auracode_sdd/brainstorm.md."""
        out_dir = self.workspace_dir / "_auracode_sdd"
        out_dir.mkdir(parents=True, exist_ok=True)
        dest = output_path or (out_dir / "00_brainstorm_ideacao.md")

        md_lines = [
            f"# Aura Code — Ideação e Amadurecimento do Produto (`auracode-brainstorm`)",
            f"",
            f"> **Ideia Original:** {result.get('raw_idea')}",
            f"> **Motor de Geração:** {result.get('mode')}",
            f"",
            f"---",
            f"",
            f"## 🌟 Visão do Produto",
            f"{result.get('vision')}",
            f"",
            f"---",
            f"",
            f"## 🎯 Priorização de Funcionalidades",
            f"",
            f"### 1. Essenciais (O que não pode faltar no primeiro dia)",
        ]
        for f in result.get("essential", []):
            md_lines.append(f"- [x] **Essencial:** {f}")

        md_lines.append(f"\n### 2. Desejáveis (Para a próxima etapa imediata)")
        for f in result.get("desirable", []):
            md_lines.append(f"- [ ] **Desejável:** {f}")

        md_lines.append(f"\n### 3. Futuras (Para versões posteriores)")
        for f in result.get("future", []):
            md_lines.append(f"- [ ] **Futuro:** {f}")

        md_lines.append(f"\n---\n\n## ⚠️ Pre-Mortem Didático (O que poderia dar errado se não cuidarmos)")
        for r in result.get("premortem_risks", []):
            md_lines.append(f"- ⚠️ {r}")

        md_lines.extend([
            f"",
            f"---",
            f"",
            f"## 🚀 Próximo Passo Recomendado",
            f"{result.get('next_step', 'Executar `auracode wizard` para gerar a Planta da Casa.')}",
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
    idea = " ".join(args).strip() if args else "Aplicativo de gestão para pequenas empresas"

    engine = BrainstormEngine()
    res = engine.brainstorm(idea)

    if save_file:
        saved_path = engine.save_brainstorm(res)
        res["saved_to"] = str(saved_path)

    if is_json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(f"\n=======================================================")
        print(f"   AURA CODE — IDEAÇÃO E BRAINSTORMING DE PRODUTO")
        print(f"=======================================================")
        print(f"Ideia: {res.get('raw_idea')}")
        print(f"Visão: {res.get('vision')}\n")

        print(">> FUNCIONALIDADES ESSENCIAIS (Dia 1):")
        for f in res.get("essential", []):
            print(f" [x] {f}")

        print("\n>> FUNCIONALIDADES DESEJÁVEIS:")
        for f in res.get("desirable", []):
            print(f" [ ] {f}")

        print("\n>> RISCOS PRE-MORTEM:")
        for r in res.get("premortem_risks", []):
            print(f" ! {r}")

        if save_file:
            print(f"\nDocumento de ideação salvo em: {res.get('saved_to')}")


if __name__ == "__main__":
    main()
