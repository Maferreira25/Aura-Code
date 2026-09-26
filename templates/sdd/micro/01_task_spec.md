# Caderno de Especificação Cirúrgica (Perfil Micro — AL1)

> **Perfil Micro:** Destinado a correções cirúrgicas de bugs, scripts rápidos e tarefas atômicas locais (Garantia AL1).  
> **Regra Não-Negociável:** Nenhuma linha de código deve ser modificada antes do preenchimento e aprovação deste caderno.

---

## 1. Identificação da Tarefa e Propósito

- **Nome da Tarefa (Slug):** `[ex: fix-token-expiration / script-backup-diario]`
- **O que precisa ser feito (Linguagem Simples):**
  - Descreva em 2 ou 3 frases simples qual é a missão desta alteração, sem jargões.
- **Nível de Garantia:** AL1 (Utilitário Local / Mudança Cirúrgica).

---

## 2. Comportamento Atual vs. Comportamento Esperado

| Cenário | Comportamento Atual (O que acontece hoje) | Comportamento Esperado (O que deve acontecer) |
| :--- | :--- | :--- |
| **Caso Principal** | `[ex: O sistema lança erro 500 se o token expirar]` | `[ex: O sistema redireciona amigavelmente para a tela de login]` |
| **Caso de Borda** | `[ex: Arquivo vazio causa crash no script]` | `[ex: O script registra um aviso e finaliza com status 0]` |

---

## 3. Limites de Escopo Cirúrgico (Surgical Boundary)

- **Arquivos Autorizados para Edição:**
  - `[caminho/do/arquivo1.py]`
  - `[tests/test_arquivo1.py]`
- **Arquivos Estritamente Proibidos de Tocar:** Todos os demais módulos fora do escopo da tarefa.
- **Limite de Churn:** Máximo de 100 linhas adicionadas/modificadas.
- **Proibições AST:** Proibido introduzir stubs vazios (`pass`), swallows de exceção ou novas dependências externas.

---

## 4. Teste de Reprodução e Critérios de Aceite

- **Teste de Reprodução Obrigatório:**
  - `[Descreva o teste unitário que falha antes da correção e passa após a implementação]`
- **Comando de Verificação:**
  ```bash
  python -m unittest tests/test_[nome].py
  auracode slop .
  auracode diff .
  ```
- **Critério Objetivo de Pronto (DoD):**
  - [ ] Teste unitário aprovado com asserções reais.
  - [ ] Zero violações de linters AST do Aura Code.
  - [ ] Nenhuma alteração fora dos arquivos autorizados.

---

## 5. Diretriz de Tolerância Zero a Presunções

Se durante a implementação a IA encontrar qualquer ambiguidade, caso imprevisto ou necessidade de alterar outros arquivos, **a execução deve parar imediatamente** e a dúvida deve ser apresentada ao usuário em linguagem simples antes de prosseguir.
