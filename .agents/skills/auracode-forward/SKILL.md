---
name: auracode-forward
description: Orquestrador da fase de programação do Aura Code. Executa a construção da aplicação a partir da Planta Teórica aprovada em _auracode_sdd/, aplicando Clean Architecture e verificadores AST.
---

# Aura Code — Programação e Execução (`auracode-forward`)

O `auracode-forward` traz o sistema à vida (subir paredes, encanamento e fiação da casa), transformando a Planta Teórica em código executável com Clean Architecture e garantias estáticas de qualidade.

---

## 🔒 Pré-Requisitos Rígidos de Execução

Antes de criar qualquer pasta de código ou arquivo de programação, verifique:
1. O diretório `_auracode_sdd/` existe e contém as especificações teóricas aprovadas conforme o perfil do projeto?
   - **Perfil `micro` (AL1):** 1 especificação (`01_especificacao_unificada.md` ou `01_task_spec.md`).
   - **Perfil `lite` (AL2):** 3 cadernos essenciais (visão/regras, arquitetura/dados, testes/aceite).
   - **Perfil `standard` (AL3):** 7 cadernos arquiteturais completos.
   - **Perfil `enterprise` (AL4):** 15 cadernos corporativos com ameaças e conformidade estrita.
2. A Planta Teórica foi explicitamente apresentada e autorizada pelo usuário?

Se qualquer um desses itens falhar: **Interrompa a execução**, avise o usuário e redirecione para o `/auracode-new` ou `/auracode-clarify`.

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
   - `auracode slop .` (Procurar stubs, código morto e exceções engolidas no escopo suportado)
   - `auracode leaks .` (Procurar padrões estruturais de recursos não fechados)
   - `auracode sec .` (Procurar vetores de injeção suportados pelo analisador)
   - `auracode types .` (Verificar as regras de tipagem implementadas)
   - `auracode arch .` (Validar o contrato de dependência entre camadas)
   - `auracode tests .` (Verificar a integridade estrutural dos testes)

   Se qualquer garantia retornar `NOT_RUN`, `NOT_APPLICABLE` inesperado ou `ERROR`, interrompa a iteração e explique qual prova está ausente. Resultado limpo não significa ausência universal de defeitos.

4. **Implementação Visual da Interface**:
   - Aplique somente os princípios visuais explicitamente aprovados no caderno de design correspondente ao perfil; não invente cores, animações, tipografia ou estilo.
