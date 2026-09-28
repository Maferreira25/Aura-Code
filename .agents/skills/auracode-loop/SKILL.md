---
name: auracode-loop
description: Runner autônomo baseado na Arquitetura Ralph com anti-dumb-zone e anti-reward-hacking via 5 níveis de verificação AST.
---

# Aura Code — Runner Autônomo sob Arquitetura Ralph (`auracode-loop`)

O `auracode-loop` orquestra iterações de desenvolvimento autônomo baseado na Ralph Architecture (Geoffrey Huntley).

---

## ⚡ Princípios Fundamentais

1. **Anti-Dumb-Zone:** Cada turno é executado em um contexto limpo e fresco guiado pelo estado físico do disco, prevenindo a degradação cognitiva e alucinações que afetam LLMs quando o contexto ultrapassa 100 mil tokens.
2. **Anti-Reward-Hacking:** Cada turno deve ser aprovado sequencialmente em 5 níveis determinísticos:
   - Nível 1: Compilação e Sintaxe
   - Nível 2: Linters AST (arch, slop, leaks, sec, types)
   - Nível 3: Execução de Testes Unitários
   - Nível 4: Integridade Semântica das Asserções
   - Nível 5: Verificação de Dependências e Segurança
3. **Freio de Emergência (Circuit Breaker):** Interrompe automaticamente a execução caso ocorram 3 falhas consecutivas, prevenindo loops infinitos de consumo de tokens.

---

## 🛠️ Comandos

```bash
# Executar loop autônomo por até 10 turnos (suporta --max-turns ou --max-iterations)
auracode loop run --max-turns 10

# Executar despachando cada tarefa para um agente CLI externo
auracode loop run --max-turns 10 --agent-cmd "python ./agent_runner.py"

# Consultar telemetria e estado atual
auracode loop status

# Resetar estado e contadores de falha
auracode loop reset
```
