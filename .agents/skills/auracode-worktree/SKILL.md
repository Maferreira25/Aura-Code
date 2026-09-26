---
name: auracode-worktree
description: Isolamento físico de branches em diretórios paralelos para agentes de IA, evitando sujeira na branch de trabalho do desenvolvedor.
---

# Aura Code — Isolamento Físico de Branches (`auracode-worktree`)

O `auracode-worktree` gerencia diretórios de trabalho paralelos do Git (`.auracode/worktrees/<task>`), garantindo que o agente desenvolva em um ambiente isolado sem corromper a branch ativa do usuário.

---

## 🏗️ Fluxo de Trabalho

1. **Criação de Worktree:** O agente cria uma branch e diretório físico dedicado para a tarefa.
2. **Execução Isolada:** Todas as edições e testes ocorrem exclusivamente dentro da pasta isolada.
3. **Merge e Limpeza:** Após aprovação e validação AST, a branch é mesclada na branch alvo e o diretório temporário é excluído.

---

## 🛠️ Comandos

```bash
# Criar diretório isolado para tarefa
auracode worktree create --task auth-feature

# Listar worktrees ativos
auracode worktree list

# Mesclar tarefa aprovada
auracode worktree merge --task auth-feature

# Limpar e remover worktree
auracode worktree clean --task auth-feature
```
