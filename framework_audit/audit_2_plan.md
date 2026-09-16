# AUDIT PLAN — AI SOFTWARE ASSURANCE FRAMEWORK FOR AGENTIC DEVELOPMENT

**Audit ID:** `AUD-MASTER-2026-09-12-001`  
**Target Repository:** `c:\ai-software-assurance-framework`  
**Target Snapshot:** Clean Directory Snapshot (No active `.git` worktree)  
**Framework Version:** `0.1.1-draft` (`pyproject.toml`: `0.1.1`, `MANIFEST.json`: `0.1.1-draft`, `validation_suite`: `0.1.1-alpha`)  
**Tree SHA-256 (Excluding `__pycache__` and `.pyc`):** `044be35157a2066e82c06afbd073881fd50df55540946dd08832d0e015fc6e04`  
**Runtime Environment:** Python 3.13.10, Git 2.52.0.windows.1, Windows PowerShell / Command Prompt  
**Auditor Personas:** Principal Software Architect, Staff/Principal Software Engineer, Application & Product Security Engineer, Software Supply Chain Security Engineer, Site Reliability Engineer, Test/Verification Engineer, DevSecOps Engineer, Open Source Maintainer, Security Researcher, AI/Agentic Systems Security Reviewer, Software Assurance Specialist, Research Methodology Reviewer.  
**Audit Policy:** Read-Only on target repository code/docs/fixtures; Adversarial; Evidence-Based ("Assertion is not proof").

---

## 1. Verificação de Snapshot e Versão Auditada

- **Git Status:** Não há repositório Git inicializado na raiz (`fatal: not a git repository`). O workspace constitui um snapshot de diretório descompactado para revisão.
- **Versão Formal:**
  - `VERSION`: `0.1.1-draft`
  - `pyproject.toml`: `version = "0.1.1"`, package `auracode`
  - `MANIFEST.json`: `framework_version = "0.1.1-draft"`, `validation_suite = "0.1.1-alpha"`
  - `controls/catalog.json`: `version = "0.1.1-draft"`
  - `validation/PREREGISTRATION-P1.md`: `Framework version: 0.1.1-draft`, `Validation-suite version: 0.1.1-draft`
- **Integridade Criptográfica do Snapshot:**
  - Contagem total de arquivos no workspace: 399 arquivos (4.555,9 KB).
  - Contagem excluindo arquivos compilados/temporários (`__pycache__` e `.pyc`): 336 arquivos.
  - Hash SHA-256 da árvore limpa de arquivos: `044be35157a2066e82c06afbd073881fd50df55540946dd08832d0e015fc6e04`.

---

## 2. Inventário Forense Completo

### Distribuição por Extensão
- `.json`: 157 arquivos (incluindo schemas, catálogos, profiles, cenários e 97 arquivos residuais de cache do Graphify)
- `.md`: 87 arquivos (documentação normativa, guias, templates de issue, relatórios)
- `.py`: 73 arquivos (código do framework, ferramentas CLI, MCP, runner, cenários e suítes de teste)
- `.pyc`: 63 arquivos (artefatos de compilação em `__pycache__` gerados durante execuções locais)
- `[sem extensão]`: 10 arquivos (incluindo `LICENSE`, `VERSION`, executáveis de cache residual)
- `.txt`: 7 arquivos (arquivos de requirements e listas de chunks)
- `.toml`: 1 arquivo (`pyproject.toml`)
- `.yml`: 1 arquivo (`.github/workflows/validate.yml`)

### Estrutura por Diretório Raiz
1. `.github/` (5 arquivos, 2.157 bytes): templates de issue, PR template, workflow `validate.yml`.
2. `adapters/` (15 arquivos, 12.596 bytes): adaptadores para Antigravity IDE/CLI (`.agents/rules`, `.agents/skills`, `.agents/agents`, `DOCUMENTATION-SOURCES.md`, `GLOBAL_GEMINI.md`, `README.md`) e adaptador genérico (`generic/AGENTS.md`).
3. `controls/` (6 arquivos, 136.664 bytes): `catalog.json` (75 controles), `CATALOG.md`, `domains.md`, `failure-modes.json` (17 modos de falha), `source-registry.json` (23 fontes), `standards-crosswalk.json`.
4. `docs/` (15 arquivos, 29.452 bytes): documentação conceitual e técnica (`FRAMEWORK.md`, `ARCHITECTURE.md`, `VALIDATION.md`, `ASSURANCE-LEVELS.md`, etc.).
5. `framework_audit/` (3 arquivos, 33.639 bytes): relatórios de auditorias anteriores (`first_audit_report.md`, `second_stage_review.md`, `REMEDIATION-LEDGER.md`).
6. `graphify-out/` (97 arquivos, 3.880.716 bytes): **ARQUIVOS RESIDUAIS NÃO RASTREADOS**. Cache de análise AST externa gerado por ferramenta de terceiros, não ignorado pelo `.gitignore`.
7. `profiles/` (4 arquivos, 4.527 bytes): perfis formais de garantia (`al1.json`, `al2.json`, `al3.json`, `al4.json`).
8. `schemas/` (4 arquivos, 6.125 bytes): JSON Schemas (`assessment.schema.json`, `contracts.schema.json`, `control.schema.json`, `profile.schema.json`).
9. `templates/` (10 arquivos, 4.602 bytes): templates de avaliação (`assessment.json`), contratos de arquitetura (`contracts.template.json`), etc.
10. `tests/` (5 arquivos, 32.813 bytes): suíte de testes unitários (`test_framework.py`, `test_validation_suite.py`, `test_v2_governance.py`, `test_security_boundaries.py`, `test_harness_isolation.py`).
11. `tools/` (8 arquivos, 70.599 bytes): utilitários do framework (`assurance.py`, `assurance_mcp.py`, `check_architecture.py`, `check_surgical_diff.py`, `verify_dependencies.py`, `assess.py`, `validate_framework.py`, `__init__.py`).
12. `validation/` (149 arquivos, 184.439 bytes): infraestrutura empírica (`scenarios/public/` com 12 cenários, `reference/public/`, `tools/harness.py`, `tools/runner.py`, `tools/validate_suite.py`, `tools/analyze_results.py`, `results/` com 36 execuções empíricas).

### Anomalias Forenses Identificadas
1. **Divergência Crítica do MANIFEST.json:**
   - O `MANIFEST.json` declara rastrear apenas 183 arquivos da versão v1 inicial.
   - 317 arquivos existentes no disco não constam no manifesto (incluindo todo o ecossistema AuraCode v2: `tools/assurance.py`, `tools/assurance_mcp.py`, `tools/check_architecture.py`, `tools/check_surgical_diff.py`, `tools/verify_dependencies.py`, `validation/tools/runner.py`, `pyproject.toml`, e os 3 novos arquivos de teste).
   - 5 arquivos sofreram alteração após a criação do manifesto gerando colisão de hash SHA-256 (`README.md`, `README.pt-BR.md`, `tools/assess.py`, `validation/README.md`, `validation/tools/harness.py`).
2. **Poluição de Repositório por Ferramenta Externa (`graphify-out/`):**
   - O diretório `graphify-out/` contém 97 arquivos e quase 4 MB de caches JSON gerados por ferramenta externa que não fazem parte do código-fonte e deveriam estar no `.gitignore`.
3. **Contaminação de `.gitignore` vs Resultados Empíricos:**
   - O arquivo `.gitignore` instrui explicitamente a ignorar `validation/results/*.json`, porém 36 arquivos de evidência de benchmark residem fisicamente nesse diretório. Se versionado via Git, os resultados seriam omitidos por padrão.
4. **Artefatos Compilados Python (`.pyc` / `__pycache__`):**
   - 63 arquivos `.pyc` residem em disco dentro de subpastas `__pycache__` nos diretórios de ferramentas e testes.

---

## 3. Linha de Base da Execução de Validadores e Testes

A execução inicial dos validadores e testes existentes no ambiente local (Python 3.13.10) sem qualquer modificação em arquivos produziu o seguinte resultado:

| Ferramenta / Comando | Resultado Observado | Tempo | Status |
| :--- | :--- | :--- | :--- |
| `python tools/validate_framework.py` | Framework validation passed (75 controles, 23 fontes, 17 failure modes, AL1: 14, AL2: 61, AL3: 74, AL4: 75) | 0.08 s | **PASS** |
| `python validation/tools/validate_suite.py` | 10 cenários automatizados: baselines com falha em testes protegidos e soluções de referência aprovadas | 2.85 s | **PASS** |
| `python -m unittest discover -s tests -v` | 57 testes unitários executados e aprovados | 1.70 s | **PASS** |
| `python validation/tools/analyze_results.py` | 36 execuções analisadas: A0=1.000, A1=1.000, A2=1.000 (Diferença A2-A0 = 0.000) | 0.05 s | **PASS** |

---

## 4. Mapa Arquitetural Real

```
[Fontes Externas & Normas] (23 referências em source-registry.json)
       │
       ▼
[Catálogo de Controles] (controls/catalog.json - 75 controles em 11 domínios)
       │
       ├───────────────────────────────┐
       ▼                               ▼
[Perfis de Risco]               [Modos de Falha Empíricos]
al1.json (14)                   (failure-modes.json - 17 falhas)
al2.json (61)                          │
al3.json (74)                          │
al4.json (75)                          │
       │                               │
       ├───────────────────────────────┘
       ▼
[Mecanismo de Validação Estrutural]
tools/validate_framework.py  ◄─── (Checagem léxica, IDs, URLs HTTPS, monotonicidade)
       │
       ▼
[Camada de Enforcement & Ferramental Ativo (AuraCode v2)]
tools/assurance.py (CLI Unificada `auracode`)
       ├── arch ──► tools/check_architecture.py (Linter AST estático, contracts.json)
       ├── deps ──► tools/verify_dependencies.py (Checagem stdlib e consulta PyPI)
       ├── diff ──► tools/check_surgical_diff.py (Inspeção git diff, anti-reward-hacking)
       ├── assess ─► tools/assess.py (Motor de avaliação contra AL1-AL4)
       └── mcp  ──► tools/assurance_mcp.py (Servidor JSON-RPC Stdio MCP para IDE/Agentes)
       │
       ▼
[Adaptadores de Ambiente Agêntico]
adapters/antigravity/ (Rules, Skills e Subagentes para o Antigravity IDE / CLI)
adapters/generic/ (Instruções agênticas genéricas AGENTS.md)
       │
       ▼
[Harness de Avaliação Empírica & Isolamento]
validation/tools/harness.py
       │
       ├──► validation/tools/runner.py
       │       ├── DockerRunner (Isolamento em container descartável)
       │       └── SubprocessSanitizedRunner (Host subprocess sanitizado de secrets)
       │
       ├──► validation/scenarios/public/ (10 cenários automatizados + 2 manuais/longitudinais)
       │       ├── workspace/ (Código base contendo falha semeada)
       │       ├── tests/ (Testes públicos fornecidos ao agente)
       │       └── protected/ (Testes protegidos mantidos fora do alcance do agente)
       │
       └──► validation/results/ (36 JSONs de resultado de avaliação)
               │
               ▼
       validation/tools/analyze_results.py (Análise estatística Wilson 95% e teste pareado)
```

### Trust Boundaries Identificadas:
1. **Boundary do Servidor MCP:** Stdio JSON-RPC conectando o cliente do agente (Antigravity IDE, Cursor, etc.) ao processo Python do host (`tools/assurance_mcp.py`).
2. **Boundary de Avaliação do Candidato:** `validation/tools/runner.py` isolando o código produzido pelo agente em container descartável (`DockerRunner`) ou processo local com variáveis de ambiente filtradas (`SubprocessSanitizedRunner`).
3. **Boundary de Integridade de Testes:** Separação física em diretórios distintos entre testes públicos (`workspace/tests/`) e testes oraculares protegidos (`protected/test_protected.py`).
4. **Boundary de Supply Chain e Rede:** Limitação de chamadas externas de rede à API pública do PyPI (`verify_dependencies.py`) e controle de pinning de GitHub Actions em workflows CI.

---

## 5. Estratégia e Metodologia de Execução das 30 Fases

A auditoria completa será executada de forma autônoma e cobrirá integralmente as 30 fases normativas:

1. **Fase 1 — Inventário Forense:** Reconciliação do `MANIFEST.json`, análise de arquivos gerados e não rastreados.
2. **Fase 2 — Mapa Arquitetural Real:** Confrontação entre a arquitetura descrita em `docs/` e a implementação em `tools/` e `validation/`.
3. **Fase 3 — Design dos Controles:** Auditoria semântica dos 75 controles, análise de ambiguidade, sobreposições e subjetividade.
4. **Fase 4 — Níveis AL1–AL4:** Análise da monotonicidade, proporcionalidade de risco e da anomalia do controle único no AL4.
5. **Fase 5 — Qualidade do Código:** Revisão estática dos scripts em `tools/` e `validation/tools/`, tratamento de exceções, parsing e falha silenciosa de flags CLI (ex: `--json`).
6. **Fase 6 — Validadores:** Auditoria de `validate_framework.py` e `validate_suite.py`, capacidade de detecção de anomalias reais e ausência de validação de schemas JSON.
7. **Fase 7 — Schemas JSON:** Verificação dos schemas em `schemas/` e ausência de enforcement programático via biblioteca `jsonschema`.
8. **Fase 8 — Segurança Tradicional & Threat Modeling:** Vulnerabilidades em execução de subprocessos, caminhos absolutos no MCP, limites de recursos e segurança do host.
9. **Fase 9 — Segurança Agêntica:** Resiliência contra Prompt Injection, Tool Misuse, Reward Hacking e conflitos entre regras globais e regras do framework.
10. **Fase 10 — Especificidade do Antigravity:** Aderência aos padrões oficiais do Antigravity IDE/CLI em 2026, regras, skills e subagentes.
11. **Fase 11 — Suíte de Testes:** Avaliação da profundidade das asserções, cobertura e testes superficiais (ex: checagem de sintaxe de schema).
12. **Fase 12 — Testes Protegidos:** Verificação do mecanismo de isolamento do oráculo e identificação de rotas de bypass em `baseline` e `gold`.
13. **Fase 13 — Benchmark & Validade Científica:** Validade de construto dos 12 cenários, relevância do efeito teto (*ceiling effect*) e separação de braços.
14. **Fase 14 — Isolamento Metodológico A0/A1/A2:** Variáveis de confusão, regras globais do sistema (`RULE[user_global]`) operando sobre o braço A0.
15. **Fase 15 — Análise Estatística:** Avaliação de `analyze_results.py`, tamanho amostral N=12, intervalos de confiança Wilson e diferença nula.
16. **Fase 16 — Contaminação do Benchmark:** Riscos de vazamento em modelos futuros e ausência de geradores dinâmicos de cenários.
17. **Fase 17 — Supply Chain:** Análise de dependências em `pyproject.toml` e pinagens de GitHub Actions (verificação do commit SHA e tag `# v7.0.1`).
18. **Fase 18 — CI/CD:** Auditoria de `.github/workflows/validate.yml`, matriz de sistemas operacionais, permissões e testes omitidos no CI.
19. **Fase 19 — Governança Open Source:** Avaliação de `SECURITY.md`, `CONTRIBUTING.md`, `GOVERNANCE.md`, `ROADMAP.md` e `CHANGELOG.md`.
20. **Fase 20 — Licenciamento:** Compatibilidade da licença MIT e auditoria de propriedade intelectual de código de terceiros.
21. **Fase 21 — Documentação:** Auditoria cruzada entre `README.md`, `README.pt-BR.md`, `docs/` e o código real.
22. **Fase 22 — Claim Audit:** Auditoria factual de todas as alegações de marketing/documentação do projeto.
23. **Fase 23 — Padrões e Referências:** Verificação das 23 fontes em `controls/source-registry.json`.
24. **Fase 24 — Standards Crosswalk:** Avaliação de mappings genéricos em `standards-crosswalk.json` e risco de *citation laundering*.
25. **Fase 25 — Conformidade & Termos Públicos:** Verificação do uso de termos como "compliant" ou "certified".
26. **Fase 26 — Reprodutibilidade:** Verificação de execução independente a partir de clone limpo.
27. **Fase 27 — Portabilidade:** Compatibilidade com Windows, Linux e macOS (separadores de caminho, chamadas de processo).
28. **Fase 28 — Performance & Escalabilidade:** Estimativa de consumo de recursos para grandes volumes de código e cenários.
29. **Fase 29 — Manutenibilidade:** Dívida técnica, acoplamento e facilidade de extensão por novos mantenedores.
30. **Fase 30 — Dogfooding:** Avaliação do próprio framework contra seus próprios padrões de garantia (AL2).

---

## 6. Próximo Passo
Com a conclusão do plano de auditoria, prosseguir imediatamente para a compilação e emissão do **Master Audit Report** completo em `framework_audit_2/master_audit_report.md`.
