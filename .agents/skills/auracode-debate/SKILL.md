---
name: auracode-debate
description: Orquestrador de debate agêntico com contenção. Realiza discussões multi-agente em subagentes isolados para evitar degradação de contexto.
---

# Aura Code — Debate Agêntico com Contenção (`auracode-debate`)

O `auracode-debate` implementa a dinâmica colaborativa de equipes de IA (*Party Mode Seguro*), onde especialistas debatem diferentes abordagens sem estourar o limite de tokens da janela principal.

---

## 🎭 Os 3 Papéis do Debate

1. **O Arquiteto (`auracode-forward`):** Propõe a implementação elegante e modular em Clean Architecture.
2. **O Auditor (`auracode-adversary`):** Desafia a proposta apontando vulnerabilidades, vazamentos e oráculos viciados.
3. **O Clarificador (`auracode-clarify`):** Sintetiza o debate em linguagem simples com analogias cotidianas e apresenta as opções para a pessoa usuária decidir.

---

## 🛠️ Comandos

```bash
# Iniciar debate estruturado sobre uma funcionalidade ou documento SDD
auracode debate "Implementação de autenticação JWT vs Sessão"

# Executar debate com saída JSON
auracode debate "Estratégia de Cache" --json
```
