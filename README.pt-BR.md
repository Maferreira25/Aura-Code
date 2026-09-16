# AuraCode — Framework Agêntico de Garantia e Confiabilidade de Software

> **AuraCode** (**A**gentic **U**nified **R**eliability & **A**ssurance for **Code**)  
> **Status: 0.1.1 — Motor de Governança e Análise Estática AST Pronto para Produção**

Um framework neutro e baseado em evidências para construção, auditoria e operação de software profissional desenvolvido com auxílio de modelos de linguagem (LLMs) e agentes de codificação autônomos.

---

## 🚀 Instalação e Início Rápido

Instale o AuraCode globalmente no seu sistema Python:

```bash
pip install -e .
```

Verifique a instalação:
```bash
auracode --help
```

---

## 🛠️ Suíte Integrada de Verificação AST (`auracode <comando>`)

O AuraCode oferece 12 comandos nativos de verificação estática e governança:

```bash
# 1. Inicializar diretórios locais de trabalho (.auracode, _auracode_*)
auracode init

# 2. Avaliar ambiguidade de requisitos e gerar perguntas não técnicas (Gate G1)
auracode ambiguity .

# 3. Escanear AST para dead code, código inalcançável e erros silenciosos
auracode slop .

# 4. Escanear AST para vazamento de recursos (arquivos, DBs, sockets sem 'with')
auracode leaks .

# 5. Escanear AST para anotações estritas de tipo e proibir o uso de 'Any'
auracode types .

# 6. Analisar integridade da suíte de testes e detectar testes sem asserções
auracode tests .

# 7. Escanear AST para vetores de injeção (eval/exec, shell=True, SQLi)
auracode sec .

# 8. Verificar limites de Clean Architecture via AST
auracode arch .

# 9. Verificar dependências contra o PyPI para evitar alucinações de pacotes
auracode deps .

# 10. Verificar se as alterações do repositório são cirúrgicas (churn < 500 linhas)
auracode diff .

# 11. Avaliar projeto contra um Nível de Garantia (AL1-AL4)
auracode assess assessment.json

# 12. Iniciar servidor stdio Model Context Protocol (MCP) para integração IDE
auracode mcp
```

---

## 🤖 Times de Agentes AuraCode (`adapters/antigravity/.agents/agents/`)

O AuraCode define 12 perfis de agentes com escala de evidência e diálogo não técnico:

1. **`auracode-scout`**: Indexador de workspace e mapeador de dependências.
2. **`auracode-archaeologist`**: Analisador de histórico de commits e contratos legados.
3. **`auracode-architect`**: Guardião da Clean Architecture e aplicador do Gate G1.
4. **`auracode-writer`**: Agente de implementação sem slop e com tipos estritos.
5. **`auracode-reviewer`**: QA autônomo executando toda a suíte `auracode`.
6. **`auracode-clarify`**: Agente anti-presunção gerando perguntas em linguagem leiga com verificação de dúvidas.
7. **`auracode-brainstorm`**: Agente de ideação pré-desenvolvimento com menus de escolha.
8. **`auracode-new`**: Agente de inicialização greenfield com estrutura Clean Architecture (`domain/`, `usecases/`, `adapters/`, `infrastructure/`, `tests/`).
9. **`auracode-debugger-graph`**: Mapeador de grafos de chamada e rastreio causal.
10. **`auracode-debugger`**: Investigador empírico que cria testes falhos antes da correção.
11. **`auracode-debugger-fix`**: Corretor cirúrgico de bugs com diffs mínimos.
12. **`auracode-refactor`**: Especialista em refatoração segura e qualidade de código.

---

## 📜 Licença
Licenciado sob a Licença MIT.
