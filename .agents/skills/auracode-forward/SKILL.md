---
name: auracode-forward
description: Orquestrador da fase de programação do Aura Code. Executa a construção da aplicação a partir da Planta Teórica aprovada em _auracode_sdd/, aplicando Clean Architecture e verificadores AST.
---

# Aura Code — Programação e Execução (`auracode-forward`)

O `auracode-forward` traz o sistema à vida (subir paredes, encanamento e fiação da casa), transformando a Planta Teórica em código executável com Clean Architecture e garantias estáticas de qualidade.

---

## 🔒 Pré-Requisitos Rígidos de Execução

Antes de criar qualquer pasta de código ou arquivo de programação, verifique:
1. O diretório `_auracode_sdd/` contém os 7 arquivos de especificações teóricas?
2. A Planta Teórica foi explicitamente apresentada e autorizada pelo usuário?

Se qualquer um desses itens falhar: **Interrompa a execução**, avise o usuário e redirecione para o `/auracode-new`.

---

## 🏗️ Passo a Passo da Execução

0. **Isolamento Físico via Git Worktree (Recomendado)**:
   - Para não sujar a branch do desenvolvedor com código intermediário, isole o ambiente:
     `auracode worktree create <nome-da-tarefa>`
   - O agente opera dentro da pasta física isolada em `.auracode/worktrees/<tarefa>`.
   - Ao finalizar e auditar, execute o merge atômico: `auracode worktree merge <nome-da-tarefa>`.

1. **Scaffolding da Estrutura Clean Architecture**:
   - Cria as camadas da aplicação:
     - `domain/`: Entidades puras e regras essenciais de negócio.
     - `usecases/`: Casos de uso e orquestração de fluxos.
     - `adapters/`: Controladores, apresentadores e conversores.
     - `infrastructure/`: Implementação de banco de dados, APIs externas e UI/web app.
     - `tests/`: Suíte de testes automatizados com pytest.

2. **Programação Cirúrgica Orientada a Especificação**:
   - Desenvolve arquivo por arquivo seguindo exatamente o que foi acordado em `_auracode_sdd/`.
   - Limite de 500 linhas de alteração por iteração.

3. **Verificação de Qualidade AST Contínua**:
   Após implementar cada componente, roda internamente os motores da CLI:
   - `auracode slop .` (Garantir zero stubs ou código morto)
   - `auracode leaks .` (Garantir que arquivos e conexões são fechados)
   - `auracode sec .` (Garantir zero riscos de injeção de código)
   - `auracode types .` (Garantir tipagem estrita)
   - `auracode arch .` (Garantir que o domain não importa infrastructure)
   - `auracode tests .` (Garantir que os testes possuem asserções válidas)

4. **Polimento Visual da Interface**:
   - Aplica os princípios visuais definidos em `_auracode_sdd/06_interface_e_design_system.md` (Design premium, cores harmoniosas, micro-animações e tipografia moderna).
