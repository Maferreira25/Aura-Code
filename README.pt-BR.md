# AuraCode — Framework Agêntico de Garantia e Confiabilidade de Software

> **AuraCode** (**A**gentic **U**nified **R**eliability & **A**ssurance for **Code**)  
> **Status: 0.1.1 (Beta / Prévia da Comunidade) — Motor de Verificação AST & Governança**  
> **Suporte a Linguagens:** Princípios arquiteturais e controles de governança são agnósticos de linguagem. O motor automatizado de análise estática AST (`auracode`) atualmente inspeciona código **Python (3.9+)**.

[![English](https://img.shields.io/badge/Language-English-blue.svg)](README.md)
[![Licença: MIT](https://img.shields.io/badge/Licen%C3%A7a-MIT-yellow.svg)](LICENSE)

Um framework neutro e baseado em evidências para construção, auditoria e operação de software profissional desenvolvido com auxílio de modelos de linguagem (LLMs) e agentes de codificação autônomos.

---

## 📖 Manifesto: AI Software Assurance for Agentic Development

A inteligência artificial transformou profundamente a engenharia de software. Modelos de linguagem e agentes autônomos já interpretam requisitos, refatoram sistemas, operam ferramentas e geram milhares de linhas de código em segundos. Contudo, essa velocidade introduz uma nova classe de riscos que a engenharia tradicional nunca precisou enfrentar de forma tão acelerada: dependências alucinadas, erosão estrutural progressiva, testes superficiais que apenas validam a própria implementação da IA (*oráculos viciados*), manipulação acidental de ferramentas e o chamado *"AI slop"* (código inflado, stubs esquecidos e abstrações desnecessárias).

Software profissional não é apenas código que compila e funciona no *happy path*. Um sistema comercial precisa resistir a acessos maliciosos, operar sob concorrência, recuperar-se de falhas, proteger dados e continuar sustentável após centenas de iterações.

O **AI Software Assurance Framework for Agentic Development** nasce para fechar essa lacuna. Sua proposta não é pedir que engenheiros confiem cegamente na IA, mas estabelecer uma nova premissa:

> **AI Zero Trust:** Não confie na IA apenas porque a resposta parece correta. Exija evidências.

Em vez de depender de prompts frágeis como *"aja como um engenheiro sênior"*, o framework traduz princípios consolidados de engenharia (alinhados a referências como NIST SSDF, OWASP ASVS/Agentic, CISA Secure by Design, OpenSSF e SLSA) em um **sistema de controles determinísticos e verificáveis**, onde toda asserção da IA precisa responder:
1. *O que precisa ser verdadeiro?*
2. *Que evidência demonstra isso?*
3. *Como essa evidência foi verificada de forma independente?*
4. *Qual condição bloqueia a entrega caso haja falha?*

### Como o AuraCode Opera na Prática

O framework não é uma carta de intenções teórica; é uma **plataforma executável**:

* **Autoridade Humana e Resolução de Ambiguidade (Gate G1):** O usuário mantém a autoridade sobre o *que* o sistema faz; a IA decide *como* implementar. Antes de codificar, qualquer incerteza de negócio, segurança ou custo é apresentada ao usuário em linguagem compreensível — traduzindo complexidade técnica em decisões funcionais (ex.: em vez de perguntar *"SQLite ou Postgres?"*, pergunta *"Os dados ficarão só neste dispositivo ou serão acessados em rede?"*).
* **Motor de Análise Estática Nativo (AST Linters via CLI `auracode`):** Analisadores sintáticos determinísticos inspecionam o código em busca de vícios típicos de LLMs sem depender de outra IA para julgar: caçam código morto e stubs esquecidos (`auracode slop`), detectam vazamentos de arquivos e conexões (`auracode leaks`), verificam vetores de injeção (`auracode sec`), exigem tipagem estrita e limitam diffs cirúrgicos a menos de 500 linhas para barrar refatorações descontroladas.
* **Integração em Tempo Real via MCP (Model Context Protocol):** Um servidor nativo (`auracode mcp`) conecta o framework diretamente a agentes e IDEs modernas (como Antigravity IDE, Cursor, Claude Desktop e VS Code), aplicando salvaguardas enquanto o agente escreve o código, e não apenas no CI/CD.
* **Separação de Papéis com Enxame de Agentes:** A mesma IA que escreve não pode auditar. O ecossistema organiza o trabalho em personas segregadas (*scout* de requisitos, arquiteto, desenvolvedor e auditor de segurança).
* **Proteção contra Adulteração (*Anti-Tampering*) e Sandboxing:** Execuções e testes ocorrem em sandbox protegido (Docker não-root, sem rede e com cotas de recursos). A integridade do próprio framework é selada criptograficamente via hashes SHA-256 (`MANIFEST.json`), impedindo que agentes autônomos desativem os testes ou adulterem os avaliadores.
* **Níveis Progressivos de Garantia (AL1 a AL4):** Da automação local de baixo risco (AL1) a plataformas financeiras críticas (AL4), o rigor dos controles e a exigência de testes (adversariais, mutação, fuzzing e SBOM) escalam proporcionalmente à gravidade do impacto de uma falha.

### Verificação Empírica

Fiel ao princípio de que nenhuma afirmação deve ser aceita sem provas, o projeto inclui uma **suíte experimental de validação** com cenários reais. Agentes autônomos são avaliados com e sem a governança do framework, medindo objetivamente correção funcional, robustez contra ataques, integridade dos testes e custo de verificação.

O futuro da programação com IA não consiste em torcer para que o modelo acerte. Consiste em construir sistemas capazes de **demonstrar com evidências quando ele acertou** — e impedir rigorosamente que um erro chegue à produção quando ele errou.

---

## 🚀 Instalação e Início Rápido

### Opção 1: Execução Instantânea via `uvx` (Sem necessidade de instalação, estilo `npx`)

Execute qualquer comando do AuraCode diretamente em um ambiente temporário isolado, sem precisar clonar o repositório ou configurar ambientes virtuais:

```bash
# Escanear projeto atual para AI slop e exceções silenciadas
uvx --from git+https://github.com/Maferreira25/Aura-Code.git auracode slop .

# Escanear vulnerabilidades de injeção e riscos com shell=True
uvx --from git+https://github.com/Maferreira25/Aura-Code.git auracode sec .

# Iniciar o servidor MCP para Antigravity IDE / Cursor / Claude Desktop
uvx --from git+https://github.com/Maferreira25/Aura-Code.git auracode mcp
```

### Opção 2: Instalação Local via `pip`

Clone e instale o pacote no seu ambiente Python:

```bash
git clone https://github.com/Maferreira25/Aura-Code.git
cd Aura-Code
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
