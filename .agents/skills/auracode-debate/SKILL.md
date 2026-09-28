---
name: auracode-debate
description: Orquestrador de debate agêntico com contenção. Realiza discussões multi-agente em subagentes isolados para evitar degradação de contexto.
---

# Aura Code — Debate Agêntico com Contenção (`auracode-debate`)

O `auracode-debate` implementa a dinâmica colaborativa de equipes de IA (*Party Mode Seguro*), onde 3 especialistas debatem abordagens técnicas em contextos isolados para prevenir a "Dumb Zone" (>100k tokens) e entregam uma síntese didática com analogias cotidianas para decisão humana.

---

## 🎭 Os 3 Papéis do Debate

1. **O Arquiteto (`auracode-forward`):** Propõe a implementação elegante e desacoplada em Clean Architecture (`domain/`, `usecases/`, `adapters/`).
2. **O Auditor (`auracode-adversary`):** Atua como Red-Team, apontando riscos STRIDE, vazamento de recursos (`leaks`), injeções (`sec`) e testes com oráculos viciados.
3. **O Clarificador (`auracode-clarify`):** Traduz o embate em linguagem simples para leigos com analogias do mundo físico e monta o menu de escolha (Opção A vs Opção B).

---

## ⚙️ Conectividade e Modelos

O motor suporta conexão direta com endpoints de IA compatíveis com a API OpenAI (OpenAI, Ollama, Groq, OpenRouter, vLLM, LM Studio) ou análise contextual determinística caso esteja offline:

- `OPENAI_API_KEY` ou `AURA_LLM_API_KEY`: Chave da API do modelo.
- `AURA_LLM_BASE_URL` ou `OPENAI_BASE_URL`: Endpoint (ex: `http://localhost:11434/v1` para Ollama local).
- `AURA_LLM_MODEL`: Modelo a utilizar (padrão: `gpt-4o-mini`).

---

## 🛠️ Comandos

```bash
# Iniciar debate estruturado sobre uma funcionalidade ou documento SDD
auracode debate "Implementação de autenticação JWT vs Sessão"

# Executar debate com saída JSON
auracode debate "Estratégia de Cache Redis vs Local" --json
```

No chat interativo da IDE, o assistente pode ainda orquestrar os 3 subagentes em turnos sequenciais separados para aprofundamento dialético.

