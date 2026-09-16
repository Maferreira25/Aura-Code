# MASTER AUDIT REPORT
# AUDITORIA PROFUNDA DO AI SOFTWARE ASSURANCE FRAMEWORK FOR AGENTIC DEVELOPMENT

**Audit ID:** `AUD-MASTER-2026-09-12-001`  
**Data da Auditoria:** 2026-09-12  
**Versão Auditada:** `0.1.1-draft` (`pyproject.toml`: `0.1.1`, `MANIFEST.json`: `0.1.1-draft`, `validation_suite`: `0.1.1-alpha`)  
**Identificador do Snapshot:** `044be35157a2066e82c06afbd073881fd50df55540946dd08832d0e015fc6e04` (Clean Tree SHA-256)  
**Ambiente de Execução da Auditoria:** Python 3.13.10, Git 2.52.0.windows.1, Windows OS  
**Status da Auditoria:** Concluída (Fase 1: Read-Only Estrita)

---

## A. EXECUTIVE SUMMARY

O **AI Software Assurance Framework for Agentic Development** (também denominado no ecossistema de código como **AuraCode**) é uma iniciativa técnica ambiciosa e relevante para responder ao problema crítico da governança de software gerado por agentes autônomos e LLMs. O projeto sintetiza conceitos modernos como *AI Zero Trust*, *Evidence Over Confidence*, *Protected Evaluators*, *Held-Out Tests*, *Architectural Continuity* e *Surgical Change Boundaries*.

A auditoria técnica profunda realizada sobre o snapshot `0.1.1-draft` constatou uma base conceitual rigorosa, com um catálogo de 75 controles estruturados em 11 domínios normativos, mapeamento de 17 modos empíricos de falha da literatura recente (2025-2026), isolamento de execução no harness de avaliação (`runner.py`) com opção de container Docker e subprocessos sanitizados, e utilitários úteis de checagem estática AST (`check_architecture.py`), verificação de pacotes no PyPI (`verify_dependencies.py`) e análise de diff (`check_surgical_diff.py`).

No entanto, quando submetido ao próprio princípio que preconiza — **"Afirmação não é prova"** —, o framework exibe falhas técnicas, contradições arquiteturais e lacunas operacionais que impedem sua publicação imediata como uma ferramenta de governança em produção:

1. **Bypass Crítico de Portões em CLI (`--json`):** As ferramentas centrais (`check_architecture.py`, `verify_dependencies.py`, `check_surgical_diff.py`) retornam código de saída `0` quando executadas com a flag `--json`, **mesmo quando violações críticas de integridade, contratos arquiteturais violados ou dependências alucinadas são detectadas**. Isso neutraliza qualquer automação em CI/CD que consuma JSON.
2. **Desconexão do MANIFEST.json:** O manifesto de release rastreia apenas 183 arquivos originais. 317 arquivos existentes no repositório (incluindo todo o código v2 em `tools/`, schemas, templates, suítes de teste ampliadas e resultados empíricos) não estão catalogados, e 5 arquivos rastreados possuem colisão de hash por modificações posteriores.
3. **Avaliação Sem Evidência Real:** O motor de avaliação `tools/assess.py` aprova projetos em AL1-AL4 bastando a presença de `"status": "PASS"`, sem validar a existência, integridade ou suficiência de evidências, e sem aplicar os schemas JSON formais via `jsonschema`.
4. **Bypass de Isolamento em Linhas de Base:** Os comandos de validação de suíte (`baseline` e `gold` em `harness.py`) chamam testes diretamente via host subprocess sem invocar o `runner` isolado, quebrando a fronteira de contenção estabelecida para o candidato.
5. **Inconsistência Estrutural AL1–AL4:** O nível crítico AL4 adiciona **apenas 1 único controle** (`VER-09`) em relação ao AL3, e este controle utiliza linguagem não mandatória (`SHOULD`). Paralelamente, o controle fundamental de testes protegidos (`VER-07`) foi deslocado para AL3, deixando o nível comercial padrão (AL2) desprovido de testes oraculares mantidos fora do alcance do agente.
6. **Fracasso no Dogfooding:** O próprio repositório falha ao ser auditado por suas próprias ferramentas: não possui `contracts.json`, não possui `requirements.txt`, falha na checagem de diff por não ter worktree Git, e não possui um `assessment.json` evidenciando sua própria conformidade.
7. **Inconclusão Científica do Benchmark P1:** Nos 36 runs experimentais, o modelo Gemini 3.8 Flash Medium obteve 100% de sucesso qualificado em todos os três braços (A0 = 1.000, A1 = 1.000, A2 = 1.000, diferença = 0.000). O benchmark sofre de efeito teto severo (*ceiling effect*) e não apresenta suporte empírico à hipótese primária de superioridade estatística do framework frente a agentes não governados em modelos contemporâneos.

---

## B. RELEASE READINESS

### Veredito Oficial: **NO-GO**

O repositório **NÃO DEVE SER PUBLICADO** no estado atual como uma ferramenta estável de governança open source. A publicação prematura induziria adotantes a um falso senso de segurança operacional e compliance.

**Justificativas Mandatórias para o NO-GO:**
- **Falha Funcional de Segurança no CLI (`AUD-SEC-001`):** A flag `--json` retorna exit code 0 na presença de falhas críticas, mascarando erros em automações.
- **Perda de Rastreabilidade e Integridade de Release (`AUD-SUP-001`):** O manifesto criptográfico `MANIFEST.json` está desatualizado em relação a mais de 60% do repositório.
- **Motor de Avaliação Permissivo (`AUD-VER-001`):** O validador aceita asserções cegas como evidência de conformidade.
- **Falha no Teste de Dogfooding (`AUD-DOG-001`):** O repositório não é capaz de rodar seus próprios comandos com sucesso sobre si mesmo.

---

## C. INVENTÁRIO DO REPOSITÓRIO

### Sumário Quantitativo
- **Arquivos Totais:** 399 arquivos (4.555,9 KB)
- **Arquivos Reais Limpos (excluindo `.pyc` e `__pycache__`):** 336 arquivos
- **Arquivos Compilados Residuais (`.pyc`):** 63 arquivos
- **Arquivos de Cache de Ferramenta Externa (`graphify-out/`):** 97 arquivos (3.880.716 bytes)

### Distribuição por Extensão de Arquivo
| Extensão | Quantidade | Observação |
| :--- | :---: | :--- |
| `.json` | 157 | Schemas, perfis, catálogo, cenários, resultados e 97 caches do Graphify |
| `.md` | 87 | Documentação, templates, relatórios e manuais operacionais |
| `.py` | 73 | Código-fonte do framework, ferramentas, testes e cenários |
| `.pyc` | 63 | Caches binários Python não versionados |
| `[sem extensão]` | 10 | Arquivos de controle (`LICENSE`, `VERSION`, executáveis residuais) |
| `.txt` | 7 | Requirements e chunks textuais de ferramentas |
| `.toml` | 1 | Configuração de build (`pyproject.toml`) |
| `.yml` | 1 | Pipeline de CI (`.github/workflows/validate.yml`) |

### Mapeamento Estrutural
- `.github/` (5 arquivos): Configuração de CI e templates de comunidade.
- `adapters/` (15 arquivos): Adaptadores para integração com agentes (Antigravity IDE/CLI e genérico).
- `controls/` (6 arquivos): O núcleo normativo do framework (catálogo, domínios, modos de falha, registro de fontes e crosswalk).
- `docs/` (15 arquivos): Especificações arquiteturais e conceituais da garantia de software.
- `framework_audit/` (3 arquivos): Relatórios históricos da primeira e segunda etapas de revisão e ledger de remediações.
- `graphify-out/` (97 arquivos): **ARTEFATO RESIDUAL NÃO INTEGRADO**. Cache de ferramenta de grafo estático.
- `profiles/` (4 arquivos): Perfis AL1, AL2, AL3 e AL4 definindo inclusão de controles.
- `schemas/` (4 arquivos): Schemas JSON formais para avaliação, contratos, controles e perfis.
- `templates/` (10 arquivos): Modelos para contratos de arquitetura e arquivos de avaliação.
- `tests/` (5 arquivos): Suíte de testes unitários baseada em `unittest`.
- `tools/` (8 arquivos): Ferramentas ativas de assurance (CLI `auracode`, servidor MCP, linters e validadores).
- `validation/` (149 arquivos): Infraestrutura empírica contendo 12 cenários de teste, soluções de referência, harness e 36 resultados experimentais.

---

## D. ARCHITECTURE MAP (ARQUITETURA REAL)

A auditoria inspecionou o código-fonte executável para derivar a arquitetura real do sistema:

```
[Fontes Normativas e Pesquisas] 
(23 referências em controls/source-registry.json)
       │
       ▼
[Catálogo Central de Controles] 
(controls/catalog.json - 75 controles em 11 domínios: INT, ARC, AGT, SEC, VER, SUP, DAT, REL, RLS, OPS, GOV)
       │
       ├─────────────────────────────────────────┐
       ▼                                         ▼
[Perfis de Risco Progressivo]            [Modos de Falha da Literatura]
al1.json (14 controles)                  (controls/failure-modes.json - 17 modos)
al2.json (61 controles)                          │
al3.json (74 controles)                          │
al4.json (75 controles)                          │
       │                                         │
       ├─────────────────────────────────────────┘
       ▼
[Validador Estrutural do Repositório]
tools/validate_framework.py
       │
       ▼
[Camada Ativa de Governança e CLI (AuraCode v2)]
tools/assurance.py (CLI Unificada `auracode`)
       ├── arch ──► tools/check_architecture.py (AST visitor, checagem de camadas e imports)
       ├── deps ──► tools/verify_dependencies.py (Consulta PyPI com orçamento de tempo/pacotes)
       ├── diff ──► tools/check_surgical_diff.py (Git diff numstat sanitizado contra hooks)
       ├── assess ─► tools/assess.py (Verificação de status em assessment JSON contra profile)
       └── mcp  ──► tools/assurance_mcp.py (Servidor JSON-RPC Stdio MCP para conexão com IDEs/Agentes)
       │
       ▼
[Camada de Integração Agêntica]
adapters/antigravity/ (.agents/rules, .agents/skills, .agents/agents, GLOBAL_GEMINI.md)
adapters/generic/ (AGENTS.md)
       │
       ▼
[Harness de Avaliação Empírica e Isolamento]
validation/tools/harness.py
       │
       ├──► validation/tools/runner.py
       │       ├── DockerRunner (Container temporário, sem rede, limites de CPU/Memória/PID)
       │       └── SubprocessSanitizedRunner (Processo local com remoção de variáveis secretas)
       │
       ├──► validation/scenarios/public/ (10 automatizados, 1 ambiguidade, 1 evolução arquitetural)
       │       ├── workspace/ (Código vulnerável/semeado entregue ao agente)
       │       ├── tests/ (Testes públicos visíveis pelo agente)
       │       └── protected/ (Oráculo mantido fora do diretório do agente)
       │
       └──► validation/results/ (36 JSONs contendo outputs e pontuações)
               │
               ▼
       validation/tools/analyze_results.py (Cálculo de Sucesso Qualificado e Intervalo Wilson 95%)
```

### Divergências entre Arquitetura Real e Arquitetura Documentada:
1. **Documentação promete JSON Schema enforcement:** `docs/FRAMEWORK.md` alega que contratos e avaliações são governados por esquemas rigorosos. No código real, **a biblioteca `jsonschema` nem sequer está instalada ou importada**; apenas a sintaxe JSON básica é checada via `json.loads()`.
2. **Falso isolamento em comandos de benchmark:** A documentação declara que a avaliação é estritamente isolada em containers ou subprocessos sanitizados. No entanto, `harness.py` nos comandos `baseline` e `gold` ignora `runner.py` e roda os testes no interpretador do host com o ambiente completo herdado.

---

## E. THREAT MODEL (MODELO DE AMEAÇA DO PRÓPRIO FRAMEWORK)

### 1. Ativos (Assets)
- **Integridade dos Controles e Perfis:** O catálogo normativo e a monotonicidade de AL1–AL4.
- **Oráculo de Testes Protegidos:** Os testes em `validation/scenarios/public/*/protected/`.
- **Integridade do Host do Desenvolvedor/Avaliador:** Processos e arquivos fora do workspace candidato.
- **Artefatos de Release:** O pacote Python distribuível (`auracode`), tags e hashes SHA-256 no GitHub.
- **Credenciais e Segredos do Host:** Chaves de API de modelos, tokens de Git e variáveis de ambiente.

### 2. Atores de Ameaça (Threat Actors)
- **Agente de Codificação Não Confiável / Rogue Agent:** LLM executando modificações no workspace, suscetível a alucinações, trapaça de oráculo (*reward hacking*) ou evasão de restrições.
- **Injeção Indireta de Prompt (Indirect Prompt Injection):** Instruções maliciosas embutidas em código de terceiros, issues ou dependências consumidas pelo agente.
- **Atacante de Supply Chain:** Publicação de pacotes maliciosos com nomes similares no PyPI ou comprometimento de GitHub Actions.
- **Colaborador Malicioso / PR Não Confiável:** Submissão de PR com adulterações sutis nos testes protegidos ou relaxamento de validadores.

### 3. Trust Boundaries e Vetores de Ataque
1. **Boundary MCP Stdio:** O processo do agente comunica-se com `assurance_mcp.py`. Sem a especificação explícita de `--allowed-root`, o agente pode invocar ferramentas MCP para ler qualquer arquivo ou repositório Git na máquina hospedeira.
2. **Boundary do Runner:** O código gerado pelo agente é executado em `runner.py`. Se Docker não estiver ativo e o modo estrito não for exigido, o código roda no host via `SubprocessSanitizedRunner`. Embora variáveis com nomes sensíveis sejam filtradas, o processo tem acesso ao sistema de arquivos local do usuário.
3. **Boundary de Testes:** A integridade depende de o agente não conseguir modificar arquivos fora de `workspace/`. Se um agente tiver acesso ao diretório pai, poderá reescrever os testes protegidos.

---

## F. FINDINGS SUMMARY (TABELA CONSOLIDADA)

| ID | Título | Severidade | Confiança | Domínio | Localização Principal |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **AUD-SEC-001** | Retorno exit code 0 com flag `--json` em falhas de segurança e contratos | **CRITICAL** | High | SEC / CI | `tools/check_architecture.py`, `tools/verify_dependencies.py`, `tools/check_surgical_diff.py` |
| **AUD-SUP-001** | `MANIFEST.json` desatualizado, incompleto e com hashes divergentes | **CRITICAL** | High | SUP / RLS | `MANIFEST.json`, `tools/validate_framework.py` |
| **AUD-VER-001** | Motor `tools/assess.py` aceita controles sem evidência e não aplica schemas | **HIGH** | High | VER / GOV | `tools/assess.py`, `schemas/assessment.schema.json` |
| **AUD-AGT-001** | Bypass do runner isolado em comandos `baseline` e `gold` do harness | **HIGH** | High | AGT / SEC | `validation/tools/harness.py:219-240` |
| **AUD-SCI-001** | Efeito teto severo (100% em A0/A1/A2) e ausência de poder discriminativo no benchmark | **HIGH** | High | SCI / BENCH | `validation/RESULTS-P1-REPORT.md`, `validation/tools/analyze_results.py` |
| **AUD-SEC-002** | Servidor MCP sem contenção de diretório por padrão (`--allowed-root` default None) | **HIGH** | High | SEC / AGT | `tools/assurance_mcp.py:143-154, 384` |
| **AUD-DOG-001** | Falha no dogfooding: repositório não atende aos controles que impõe | **HIGH** | High | GOV / DOG | Raiz do projeto, `tools/assurance.py` |
| **AUD-DES-001** | Desproporcionalidade AL4: apenas 1 controle adicionado com requisito não mandatório (`SHOULD`) | **MEDIUM** | High | DES / ARC | `controls/catalog.json:VER-09`, `profiles/al4.json` |
| **AUD-DES-002** | Contradição entre `AGT-05` (AL2) e deslocamento de `VER-07` para AL3 | **MEDIUM** | High | AGT / VER | `controls/catalog.json:AGT-05, VER-07`, `profiles/al2.json` |
| **AUD-SCH-001** | Schemas JSON operam como documentação morta sem enforcement no código | **MEDIUM** | High | SCH / VER | `schemas/*.schema.json`, `tests/test_v2_governance.py` |
| **AUD-SUP-002** | Workflow CI utiliza tag fictícia `# v7.0.1` e validador aceita SHA arbitrário | **MEDIUM** | High | SUP / CI | `.github/workflows/validate.yml`, `tools/validate_framework.py` |
| **AUD-LNT-001** | Linter AST de arquitetura vulnerável a bypass por importações dinâmicas | **MEDIUM** | High | ARC / SEC | `tools/check_architecture.py:18-53` |
| **AUD-DOC-001** | Relatório de validação estático desatualizado em relação à suíte real de testes | **LOW** | High | DOC | `VALIDATION-REPORT.md` |
| **AUD-CWK-001** | Standards crosswalk mapeia normas inteiras para domínios sem granularidade de requisitos | **LOW** | High | GOV / NORMATIVE | `controls/standards-crosswalk.json` |
| **AUD-RES-001** | Poluição de 97 arquivos residuais de cache de ferramenta externa (`graphify-out/`) | **INFO** | High | CLEANLINESS | Raiz do repositório, `.gitignore` |

---

## G. CRITICAL FINDINGS (DETALHADOS)

### `AUD-SEC-001` — Retorno exit code 0 com flag `--json` em falhas de segurança e contratos
- **SEVERIDADE:** CRITICAL
- **CONFIANÇA:** HIGH CONFIDENCE
- **DOMÍNIO:** SEC / CI / TOOLING
- **LOCALIZAÇÃO:**
  - `tools/check_architecture.py`: linhas 366–368
  - `tools/verify_dependencies.py`: linhas 325–327
  - `tools/check_surgical_diff.py`: linhas 301–303
- **EVIDÊNCIA:**
  Em `tools/check_architecture.py`:
  ```python
  if args.json:
      print(json.dumps(result, indent=2))
  else:
      if result.get("error"):
          sys.exit(2)
      ...
      if result["success"]:
          sys.exit(0)
      else:
          sys.exit(1)
  ```
  O mesmo padrão ocorre em `verify_dependencies.py` e `check_surgical_diff.py`. Quando `--json` é fornecido, a função `main()` imprime a estrutura e retorna sem chamar `sys.exit(1)`. O processo encerra com exit code 0.
  Teste empírico realizado na auditoria:
  `python tools/check_architecture.py --json non_existent_dir` retornou código de saída `0`, mesmo emitindo `{"success": false, "error": "..."}`.
- **DESCRIÇÃO:**
  Sistemas de automação, pipelines de CI/CD (GitHub Actions, GitLab CI) e pre-commit hooks dependem do código de saída do processo para interromper compilações ou bloquear merges em caso de falha. Ao utilizar a flag `--json` (o formato padrão para consumo por ferramentas automatizadas), as três ferramentas de assurance reportam sucesso no nível do sistema operacional, mascarando completamente violações de contrato, injeção de pacotes alucinados ou adulteração de suítes de teste.
- **CENÁRIO:**
  Uma equipe configura um pipeline CI: `auracode arch --json src/ | jq .` ou `auracode deps --json requirements.txt`. Um agente autônomo introduz uma dependência inexistente ou quebra o isolamento de camadas. O pipeline executa, recebe exit code 0 e faz o deploy do software com vulnerabilidade para produção.
- **IMPACTO:**
  Bypass completo de portões de qualidade automatizados. Falsa impressão de garantia que anula a utilidade do framework em pipelines modernos.
- **CAUSA RAIZ:**
  Condicional que encapsula `sys.exit(1 if not success else 0)` exclusivamente dentro do bloco `else:` da formatação de texto humano, esquecendo de finalizar o processo com código de erro após serializar o JSON.
- **CONTROLES AFETADOS:** `ARC-01`, `ARC-02`, `SUP-01`, `VER-01`, `VER-08`, `RLS-01`.
- **RECOMENDAÇÃO:**
  Refatorar `main()` em todas as ferramentas CLI para garantir que o código de saída reflita o resultado booleano independentemente do formato de saída (`sys.exit(0 if result.get("success") else 1)`).
- **VALIDAÇÃO DA CORREÇÃO:**
  Adicionar testes unitários automatizados em `tests/test_v2_governance.py` executando cada ferramenta com `--json` em cenários inválidos e asseverando que o subprocesso retorna código diferente de zero.

---

### `AUD-SUP-001` — `MANIFEST.json` desatualizado, incompleto e com hashes divergentes
- **SEVERIDADE:** CRITICAL
- **CONFIANÇA:** HIGH CONFIDENCE
- **DOMÍNIO:** SUP / RLS / SUPPLY-CHAIN
- **LOCALIZAÇÃO:** `MANIFEST.json`, `tools/validate_framework.py`
- **EVIDÊNCIA:**
  Execução de script de verificação confrontando `MANIFEST.json` com o disco:
  - Arquivos declarados no manifesto: 183.
  - Arquivos limpos reais no disco: 336 (317 arquivos não constam no manifesto).
  - Componentes essenciais ausentes do manifesto: `tools/assurance.py`, `tools/assurance_mcp.py`, `tools/check_architecture.py`, `tools/check_surgical_diff.py`, `tools/verify_dependencies.py`, `validation/tools/runner.py`, `tests/test_security_boundaries.py`, `tests/test_harness_isolation.py`, `tests/test_v2_governance.py`, `pyproject.toml`, `schemas/contracts.schema.json`.
  - Mismatch criptográfico SHA-256 em arquivos rastreados:
    - `README.md` (manifesto: 6136 bytes; disco: 7183 bytes)
    - `README.pt-BR.md` (manifesto: 3282 bytes; disco: 4223 bytes)
    - `tools/assess.py` (manifesto: 1605 bytes; disco: 4912 bytes)
    - `validation/README.md` (manifesto: 3411 bytes; disco: 4141 bytes)
    - `validation/tools/harness.py` (manifesto: 10010 bytes; disco: 12253 bytes)
  - `tools/validate_framework.py` não valida o `MANIFEST.json`.
- **DESCRIÇÃO:**
  O framework preconiza rastreabilidade rigorosa de cadeia de suprimentos (`SUP-01`, `SUP-06`, `RLS-01`), fornecendo um `MANIFEST.json` com hashes SHA-256 de todos os arquivos. No entanto, o arquivo de manifesto reflete uma versão legada. Quando remediações anteriores modificaram `harness.py`, `assess.py` e os novos módulos foram adicionados, o manifesto não foi atualizado. Além disso, o validador interno não possui nenhuma checagem que compare os hashes do manifesto com o estado em disco.
- **CENÁRIO:**
  Um auditor de supply chain ou pipeline de verificação independente baixa o repositório e valida o `MANIFEST.json`. O processo falha imediatamente, indicando adulteração ou descompasso estrutural. Em um cenário real de supply chain, o download seria considerado comprometido.
- **IMPACTO:**
  Quebra de integridade de release e impossibilidade de atestar formalmente que a distribuição não sofreu adulteração. Falha direta na credibilidade do framework perante a comunidade open source.
- **CAUSA RAIZ:**
  Processo manual de geração de release sem automação vinculada ao CI ou ao validador de framework.
- **CONTROLES AFETADOS:** `SUP-01`, `SUP-05`, `SUP-06`, `RLS-01`, `GOV-06`.
- **RECOMENDAÇÃO:**
  1. Criar utilitário `tools/update_manifest.py` para sincronizar o inventário e calcular os hashes SHA-256 de todos os arquivos distribuíveis.
  2. Adicionar em `tools/validate_framework.py` a checagem obrigatória de conformidade do `MANIFEST.json` com falha automática em caso de divergência.
- **VALIDAÇÃO DA CORREÇÃO:**
  `python tools/validate_framework.py` deve falhar se qualquer arquivo for alterado ou adicionado sem atualização do `MANIFEST.json`.

---

## H. HIGH FINDINGS (DETALHADOS)

### `AUD-VER-001` — Motor `tools/assess.py` aceita controles sem evidência e não aplica schemas
- **SEVERIDADE:** HIGH
- **CONFIANÇA:** HIGH CONFIDENCE
- **DOMÍNIO:** VER / GOV / ASSURANCE-ENGINE
- **LOCALIZAÇÃO:** `tools/assess.py`: linhas 46–71, `schemas/assessment.schema.json`
- **EVIDÊNCIA:**
  No loop de avaliação de `tools/assess.py`:
  ```python
  for cid in profile.get("included_controls", []):
      r = results.get(cid, {"status": "NOT_ASSESSED"})
      status = r.get("status", "NOT_ASSESSED") if isinstance(r, dict) else "NOT_ASSESSED"
      if status == "PASS":
          passed.append(cid)
      elif status == "FAIL":
          fail.append(cid)
      elif status == "NA":
          if not isinstance(r, dict) or not r.get("rationale", "").strip():
              bad_na.append(cid)
          else:
              na.append(cid)
  ```
  Se o arquivo JSON contiver:
  `"controls": { "INT-01": {"status": "PASS"}, "SEC-01": {"status": "PASS"}, ... }`
  sem nenhum array `"evidence"`, sem assinaturas, sem logs, sem referências a artefatos e sem campos obrigatórios do schema (`framework_version`, `assessor`), o método retorna `"success": True`.
- **DESCRIÇÃO:**
  O princípio nº 1 do framework é *"Evidence over confidence"*. Contudo, seu próprio motor de conformidade aceita afirmações não comprovadas como válidas para atribuir aprovação a um nível de garantia (AL1 a AL4). O único status que exige justificativa é `"NA"` (`rationale`). Para `"PASS"`, a simples declaração da palavra-chave é suficiente.
- **CENÁRIO:**
  Um agente de IA gera um `assessment.json` sintético com todos os controles marcados como `"PASS"` sem anexar nenhum artefato de prova. O comando `auracode assess assessment.json` retorna que o projeto está em plena conformidade com AL2 Production.
- **IMPACTO:**
  Institucionalização da "auditoria teatral" que o framework pretende combater. Geração de relatórios de conformidade sem qualquer validade técnica real.
- **CAUSA RAIZ:**
  Implementação ingênua do algoritmo de parsing focada unicamente na presença de strings de status, sem integração com validador formal de esquemas.
- **CONTROLES AFETADOS:** `VER-01`, `VER-08`, `GOV-01`, `GOV-08`.
- **RECOMENDAÇÃO:**
  1. Tornar obrigatório o campo `"evidence"` contendo pelo menos um link, hash ou arquivo existente quando o status for `"PASS"`.
  2. Implementar validação estrita contra `schemas/assessment.schema.json`.
- **VALIDAÇÃO DA CORREÇÃO:**
  Criar teste unitário passando assessment com status PASS mas array de evidência vazio e comprovar que o motor rejeita a avaliação.

---

### `AUD-AGT-001` — Bypass do runner isolado em comandos `baseline` e `gold` do harness
- **SEVERIDADE:** HIGH
- **CONFIANÇA:** HIGH CONFIDENCE
- **DOMÍNIO:** AGT / SEC / ISOLATION
- **LOCALIZAÇÃO:** `validation/tools/harness.py`: linhas 52, 71, 219–220, 239–240
- **EVIDÊNCIA:**
  Em `cmd_baseline` (linhas 219–220):
  ```python
  pub_ok, pub = public_tests(ws)
  prot_ok, prot = protected_tests(sdir, ws)
  ```
  Em `cmd_gold` (linhas 239–240):
  ```python
  pub_ok, _ = public_tests(ws)
  prot_ok, _ = protected_tests(sdir, ws)
  ```
  Nas funções `public_tests` e `protected_tests`:
  ```python
  def public_tests(workspace, runner=None):
      ...
      if runner is not None:
          r = runner.run_tests(workspace, tests, timeout=15)
      else:
          r = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], workspace)
  ```
  Quando `runner` é omitido (caso das funções `baseline` e `gold`), o código chama `run()`, que invoca diretamente `subprocess.run` no host com o ambiente do usuário sem nenhuma filtragem de segredos ou contenção de processos.
- **DESCRIÇÃO:**
  O relatório de remediação anterior (REM-001) documentou a criação de `runner.py` para isolar a execução de testes. Embora `cmd_evaluate` tenha sido atualizado para instanciar e passar o `runner`, os comandos `baseline` e `gold` — que são executados a cada rodada de CI através de `python validation/tools/validate_suite.py` — continuaram chamando a implementação legada sem runner.
- **CENÁRIO:**
  Um cenário ou solução de referência malicioso ou comprometido é adicionado via pull request. Ao rodar `validate_suite.py`, o teste é executado no host da máquina do desenvolvedor ou do runner do CI com acesso irrestrito às variáveis de ambiente e arquivos locais.
- **IMPACTO:**
  Quebra da fronteira de isolamento do oráculo e risco de execução arbitrária de código sem contenção durante a validação da suíte.
- **CAUSA RAIZ:**
  Remediação incompleta do achado REM-001, restringindo o uso do `runner` apenas ao comando `evaluate`.
- **CONTROLES AFETADOS:** `AGT-04`, `AGT-05`, `VER-07`, `SEC-04`.
- **RECOMENDAÇÃO:**
  Passar uma instância de `runner` (usando `get_runner()`) em `cmd_baseline` e `cmd_gold` em `harness.py`.
- **VALIDAÇÃO DA CORREÇÃO:**
  Injetar variável simulando segredo no ambiente durante `validate_suite.py` e verificar que nenhum teste de cenário consegue acessá-la.

---

### `AUD-SCI-001` — Efeito teto severo (100% em A0/A1/A2) e ausência de poder discriminativo no benchmark
- **SEVERIDADE:** HIGH
- **CONFIANÇA:** HIGH CONFIDENCE
- **DOMÍNIO:** SCI / BENCH / METHODOLOGY
- **LOCALIZAÇÃO:** `validation/RESULTS-P1-REPORT.md`, `validation/tools/analyze_results.py`
- **EVIDÊNCIA:**
  Saída consolidada de `analyze_results.py`:
  ```text
  Runs: 36
  A0: QS 12/12 = 1.000 (Wilson 95% CI 0.757..1.000)
  A1: QS 12/12 = 1.000 (Wilson 95% CI 0.757..1.000)
  A2: QS 12/12 = 1.000 (Wilson 95% CI 0.757..1.000)
  Matched A2-A0 QS difference: mean=0.000 over 12 pairs
  ```
  Em todas as 36 execuções empíricas, os três braços obtiveram taxa de aprovação idêntica de 100%. A diferença média pareada entre o agente sem framework (A0) e o agente governado pelo framework (A2) é exatamente 0,000.
- **DESCRIÇÃO:**
  A hipótese científica primária do pré-registro (`PREREGISTRATION-P1.md`, Seção 2) afirma categoricamente:
  *"Under matched execution-surface, model, reasoning effort, and budget conditions, A2 will have a higher Qualified Success (QS) probability than A0"*.
  Os dados empíricos refutam a hipótese: não há diferença estatística mensurável. Os cenários do benchmark (SQL injection simples, sanitização de path trivial, idempotência com dicionário) são fáceis demais para modelos com capacidade de raciocínio contemporânea (Gemini 3.8 Flash Medium). Como consequência, o benchmark sofre de *ceiling effect* (efeito teto) total e não tem poder discriminativo.
- **CENÁRIO:**
  Um revisor acadêmico ou equipe corporativa avalia o relatório para decidir sobre a adoção do framework. Ao examinar a seção estatística, conclui que o framework não adicionou nenhuma eficácia mensurável sobre o agente cru, decidindo que o framework introduz apenas sobrecarga operacional.
- **IMPACTO:**
  Ausência de comprovação empírica do valor do framework. Risco de desqualificação metodológica do projeto por afirmações de eficácia não comprovadas nos dados.
- **CAUSA RAIZ:**
  Dificuldade dos cenários calibrada para LLMs legados sem raciocínio explícito, sem atualização para a fronteira atual de capacidades de modelos em 2026.
- **CONTROLES AFETADOS:** `VER-01`, `VER-07`, `GOV-01`.
- **RECOMENDAÇÃO:**
  1. Reconhecer formalmente no `README.md` e em `RESULTS-P1-REPORT.md` que a hipótese de superioridade em taxa de sucesso para este modelo específico não foi suportada.
  2. Desenvolver bateria P2 de cenários de alta complexidade (concorrência real, refatoração de microsserviços, ataques sutis de deserialização e supply chain multimodal).
- **VALIDAÇÃO DA CORREÇÃO:**
  Execução do novo benchmark exibindo curva de separação estatística onde A0 falhe em cenários complexos que A2 resolva via contratos.

---

### `AUD-SEC-002` — Servidor MCP sem contenção de diretório por padrão (`--allowed-root` default None)
- **SEVERIDADE:** HIGH
- **CONFIANÇA:** HIGH CONFIDENCE
- **DOMÍNIO:** SEC / AGT / MCP
- **LOCALIZAÇÃO:** `tools/assurance_mcp.py`: linhas 143–154, 384–388
- **EVIDÊNCIA:**
  Em `tools/assurance_mcp.py`:
  ```python
  def validate_path_in_root(p: Path, root: Optional[Path]) -> Tuple[bool, Optional[str]]:
      if root is None:
          return True, None
      ...
  ```
  No bloco principal CLI:
  ```python
  parser.add_argument("--allowed-root", type=str, default=None, help="Root directory for allowed tool operations")
  ```
  Se o servidor for instanciado sem passar explicitamente `--allowed-root` (o comportamento padrão ao registrar o servidor no arquivo de configuração do MCP de IDEs como Cursor, VS Code ou Antigravity), `root` será `None` e todas as validações de contenção de caminho são ignoradas.
- **DESCRIÇÃO:**
  O achado de segurança NR-2 da auditoria anterior exigia confinamento de caminhos para o servidor MCP. A equipe implementou a função `validate_path_in_root`, mas deixou o padrão permissivo (`None`). Clientes MCP operam frequentemente como subprocessos invocados por ferramentas de desktop. Quando configurado convencionalmente (`python -m tools.assurance_mcp`), o servidor concede ao modelo LLM autoridade para ler e inspecionar qualquer diretório ou arquivo onde o processo Python do usuário tenha acesso de leitura.
- **CENÁRIO:**
  Um desenvolvedor conecta o MCP do AuraCode ao seu IDE. Ao trabalhar em um projeto de teste, um prompt injection indireto em um arquivo de dependências instrui o modelo a chamar `check_surgical_diff(repo_directory="C:/Users/Nome/.ssh")` ou `check_architecture(target_directory="C:/ProjetosConfidenciais")`. O servidor MCP atende à requisição e expõe metadados estruturais na resposta JSON-RPC.
- **IMPACTO:**
  Vazamento de informações do sistema de arquivos do host e violação do princípio do menor privilégio (*Least Privilege*).
- **CAUSA RAIZ:**
  Configuração insegura por padrão (*Insecure by Default*), violando os princípios de *Secure by Design*.
- **CONTROLES AFETADOS:** `AGT-03`, `AGT-04`, `SEC-04`.
- **RECOMENDAÇÃO:**
  Alterar o valor padrão de `--allowed-root` para o diretório de trabalho atual (`Path.cwd().resolve()`), exigindo uma flag explícita caso o usuário deseje deliberadamente autoridade global.
- **VALIDAÇÃO DA CORREÇÃO:**
  Testar via `test_security_boundaries.py` que, na inicialização padrão sem argumentos, chamadas para caminhos fora de `cwd` são terminantemente rejeitadas com erro de permissão.

---

### `AUD-DOG-001` — Falha no dogfooding do próprio framework
- **SEVERIDADE:** HIGH
- **CONFIANÇA:** HIGH CONFIDENCE
- **DOMÍNIO:** GOV / DOGFOODING / QA
- **LOCALIZAÇÃO:** Raiz do repositório, `tools/assurance.py`
- **EVIDÊNCIA:**
  Execução das ferramentas do framework sobre o próprio repositório:
  1. `python tools/check_architecture.py .`  
     -> **FALHA:** `ERROR: No architecture contract file found in C:\ai-software-assurance-framework. Specify --contracts <path>.` (Exit code 1).
  2. `python tools/verify_dependencies.py`  
     -> **FALHA:** `Supply Chain Verification: ... requirements.txt / SUPPLY CHAIN INTEGRITY VIOLATED` (Exit code 1).
  3. `python tools/check_surgical_diff.py .`  
     -> **FALHA:** `ERROR: Git status error in ... fatal: not a git repository` (Exit code 2).
  4. Ausência de qualquer arquivo `assessment.json` formalizando o nível de garantia do próprio projeto.
- **DESCRIÇÃO:**
  O framework exige que projetos governados possuam contratos arquiteturais de camada (`contracts.json`), lista de requisitos verificada e avaliações periódicas documentadas. No entanto, o próprio repositório não define um `contracts.json` para seus módulos em `tools/`, não fornece um `requirements.txt` (usando apenas `pyproject.toml`), quebra ao inspecionar diffs fora de um repositório git ativo e não possui evidência arquivada de sua própria autoavaliação em AL2.
- **CENÁRIO:**
  Um mantenedor sênior de open source clona o repositório e executa `auracode arch .` para verificar se os autores aplicam as próprias regras. A ferramenta aborta com erro fatal por falta de contrato no próprio repositório.
- **IMPACTO:**
  Perda severa de autoridade técnica e credibilidade. O framework aparenta ser um exercício teórico não adotado nem pelos seus criadores.
- **CAUSA RAIZ:**
  Desenvolvimento dos validadores com foco exclusivo nos cenários sintéticos de teste em `validation/`, sem institucionalizar rotinas de teste contínuo sobre o próprio código-fonte.
- **CONTROLES AFETADOS:** `ARC-01`, `ARC-03`, `SUP-01`, `VER-01`, `GOV-01`, `GOV-08`.
- **RECOMENDAÇÃO:**
  1. Criar e versionar `contracts.json` definindo as camadas do próprio repositório (ex: `tools` não podem importar `validation/scenarios`).
  2. Fazer `verify_dependencies.py` suportar a leitura direta de `pyproject.toml` quando `requirements.txt` não existir.
  3. Gerar e versionar `assessment.json` do próprio framework documentando conformidade com AL2.
- **VALIDAÇÃO DA CORREÇÃO:**
  Um script de teste no CI executando `auracode arch .` e `auracode assess self-assessment.json` e retornando código 0.

---

## I. MEDIUM FINDINGS (DETALHADOS)

### `AUD-DES-001` — Desproporcionalidade estrutural nos níveis de garantia (AL4 monofatorial e não mandatório)
- **SEVERIDADE:** MEDIUM | **CONFIANÇA:** HIGH | **DOMÍNIO:** DES / ARC
- **LOCALIZAÇÃO:** `controls/catalog.json:VER-09`, `profiles/al4.json`
- **EVIDÊNCIA:**
  - AL1: 14 controles.
  - AL2: 61 controles (+47).
  - AL3: 74 controles (+13).
  - AL4: 75 controles (+1).
  O único controle exclusivo do AL4 é `VER-09`:
  *"Critical invariant verification: For AL4 invariants whose failure could cause catastrophic or irreversible harm, stronger assurance techniques such as model checking, formal specification, independent implementation, or equivalent evidence SHOULD be evaluated and used when practical."*
- **DESCRIÇÃO:**
  O AL4 é definido em `ASSURANCE-LEVELS.md` como o patamar para *"Critical / life-critical / national infrastructure"*. No entanto, a passagem de AL3 para AL4 adiciona um único controle cuja redação usa `"SHOULD"` (deveria), sem impor obrigações adicionais de segurança de runtime, isolamento físico de hardware, auditoria independente externa obrigatória ou salvaguardas humanas intransponíveis.
- **IMPACTO:** O perfil AL4 não oferece salto de garantia substancial em relação ao AL3, funcionando como uma classificação puramente decorativa.

---

### `AUD-DES-002` — Deslocamento do controle de testes protegidos (`VER-07`) para AL3 e contradição com `AGT-05` no AL2
- **SEVERIDADE:** MEDIUM | **CONFIANÇA:** HIGH | **DOMÍNIO:** AGT / VER / DES
- **LOCALIZAÇÃO:** `controls/catalog.json:AGT-05`, `controls/catalog.json:VER-07`, `profiles/al2.json`
- **EVIDÊNCIA:**
  `AGT-05` (exigido no AL2): *"Agents under evaluation MUST NOT be able to silently weaken, replace or bypass the mechanism used to judge their work."*
  `VER-07` (exigido apenas no AL3): *"Held-out or protected tests: High-assurance agent-generated changes MUST include evaluation cases unavailable for modification by the implementing agent..."*
- **DESCRIÇÃO:**
  Não é possível satisfazer plenamente a premissa de `AGT-05` (impedir que o agente enfraqueça o oráculo) se os testes não forem mantidos protegidos/fora do alcance do agente, como preconizado em `VER-07`. Ao colocar `VER-07` exclusivamente no AL3, o framework permite que no AL2 (padrão comercial) agentes modifiquem suas próprias suítes de teste públicas sem infringir os controles do perfil.
- **IMPACTO:** Criação de inconsistência normativa e brecha para *reward hacking* no nível padrão de produção (AL2).

---

### `AUD-SCH-001` — Schemas JSON operam como documentação morta sem enforcement no código
- **SEVERIDADE:** MEDIUM | **CONFIANÇA:** HIGH | **DOMÍNIO:** SCH / VER
- **LOCALIZAÇÃO:** `schemas/*.schema.json`, `tests/test_v2_governance.py:286-289`
- **EVIDÊNCIA:**
  A busca por `jsonschema` em todo o repositório retorna zero ocorrências.
  No arquivo de testes de governança:
  ```python
  def test_schema_json_syntax(self):
      schema = json.loads((ROOT / "schemas/contracts.schema.json").read_text(encoding="utf-8"))
      self.assertEqual(schema["title"], "Architecture Contract Specification")
  ```
  O teste apenas valida que o arquivo é um JSON parseável e que o título coincide.
- **DESCRIÇÃO:**
  O repositório possui quatro schemas JSON bem elaborados (`contracts.schema.json`, `assessment.schema.json`, `control.schema.json`, `profile.schema.json`). No entanto, nenhum validador de código do framework os aplica aos arquivos reais. Se um contrato de arquitetura contiver campos com tipos inválidos ou chaves incorretas, os linters processam com valores default sem acusar erro de schema.
- **IMPACTO:** Falta de enforcement formal; schemas cumprem apenas papel ilustrativo.

---

### `AUD-SUP-002` — Workflow CI utiliza tag fictícia `# v7.0.1` e validador aceita SHA arbitrário
- **SEVERIDADE:** MEDIUM | **CONFIANÇA:** HIGH | **DOMÍNIO:** SUP / CI
- **LOCALIZAÇÃO:** `.github/workflows/validate.yml:14`, `tools/validate_framework.py:105-120`
- **EVIDÊNCIA:**
  Em `.github/workflows/validate.yml`:
  `- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`
  No ecossistema GitHub Actions oficial, `actions/checkout` está na versão `v4`. A versão `v7.0.1` não existe.
  Em `tools/validate_framework.py`:
  ```python
  sha_re = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
  ...
  if not sha_re.fullmatch(version):
      errors.append(...)
  ```
  O validador apenas checa se a string possui 40 dígitos hexadecimais. Qualquer hash inventado é aceito como prova de conformidade com o controle `SUP-06`.
- **IMPACTO:** Evidência fictícia de conformidade e risco de quebra caso o hash não resolva em ambiente real de runner do GitHub.

---

### `AUD-LNT-001` — Linter AST de arquitetura vulnerável a bypass por importações dinâmicas
- **SEVERIDADE:** MEDIUM | **CONFIANÇA:** HIGH | **DOMÍNIO:** ARC / SEC
- **LOCALIZAÇÃO:** `tools/check_architecture.py`: linhas 18–53
- **EVIDÊNCIA:**
  A classe `ImportVisitor` intercepta apenas nós `ast.Import` e `ast.ImportFrom`.
  Linhas de código como:
  `pkg = __import__("infrastructure.database")` ou  
  `db = importlib.import_module("infrastructure.database")`
  são nós de chamada de função (`ast.Call`), completamente invisíveis para o visitante AST atual.
- **IMPACTO:** Um agente com incentivo para passar testes pode recorrer a importações dinâmicas para acessar camadas proibidas sem que o linter acuse violação de contrato de arquitetura.

---

## J. LOW / INFO FINDINGS

### `AUD-DOC-001` — Relatório de validação estático desatualizado em relação à suíte real de testes
- **SEVERIDADE:** LOW | **CONFIANÇA:** HIGH | **DOMÍNIO:** DOC
- **LOCALIZAÇÃO:** `VALIDATION-REPORT.md`: linhas 74–90
- **EVIDÊNCIA:** O arquivo relata a execução de 10 testes unitários (`Ran 10 tests in 0.003s OK`), enquanto o framework atual conta com 57 testes em 5 suítes. O relatório congelado em 09/09/2026 está desatualizado.

### `AUD-CWK-001` — Standards crosswalk mapeia normas inteiras para domínios sem granularidade de requisitos
- **SEVERIDADE:** LOW | **CONFIANÇA:** HIGH | **DOMÍNIO:** GOV / NORMATIVE
- **LOCALIZAÇÃO:** `controls/standards-crosswalk.json`
- **EVIDÊNCIA:** O crosswalk relaciona, por exemplo, `NIST-SSDF-1.1` diretamente a `["INT", "ARC", "SEC", "VER", "SUP", "RLS", "OPS", "GOV"]`. Não há vinculação de subpráticas do NIST (ex: `PW.1.1`, `PO.2.1`) aos controles individuais (`INT-01`, `SEC-04`). Funciona apenas como um mapeamento temático preliminar.

### `AUD-RES-001` — Poluição de 97 arquivos residuais de cache de ferramenta externa (`graphify-out/`)
- **SEVERIDADE:** INFO | **CONFIANÇA:** HIGH | **DOMÍNIO:** CLEANLINESS
- **LOCALIZAÇÃO:** Raiz do repositório, `.gitignore`
- **EVIDÊNCIA:** 97 arquivos residuais de cache de AST e análise de grafos totalizando 3,88 MB encontram-se acumulados no diretório `graphify-out/` sem inclusão no `.gitignore`.

---

## K. CODE QUALITY & ENGENHARIA DE SOFTWARE

1. **Modularidade e Coesão:** O código é dividido em utilitários funcionais focados (`check_architecture.py`, `verify_dependencies.py`, `check_surgical_diff.py`). As ferramentas possuem boa legibilidade e seguem a diretriz de zero dependências externas (recorrendo apenas à biblioteca padrão).
2. **Tratamento de Exceções:** Há instâncias de captura ampla de exceções (`except Exception as e:`) em `assess.py`, `assurance_mcp.py` e `check_architecture.py`. Em vários pontos, erros de I/O são convertidos silenciosamente em mensagens genéricas sem preservar rastros de depuração (`traceback`).
3. **Gerenciamento de Estado e Processos:** O script unificado `tools/assurance.py` manipula a variável global `sys.argv` antes de despachar chamadas para os módulos filhos (`sys.argv = ["check_architecture.py", ...]`). Essa prática cria acoplamento temporal e efeitos colaterais caso seja importado como biblioteca em outros processos.
4. **Portabilidade de Paths:** Boa parte do código utiliza `Path.resolve()` e normalização via `.replace("\\", "/")`, garantindo compatibilidade cruzada entre Windows e sistemas POSIX. No entanto, chamadas de processo como `taskkill /F /T` em `runner.py` são específicas para Windows, dependendo de `os.name == "nt"`.

---

## L. SECURITY & THREAT AUDIT

1. **Execução de Subprocessos e Git Security:** A introdução de `SAFE_GIT_ARGS` (`core.fsmonitor=`, `core.hooksPath=`, `diff.external=`, `diff.textconv=false`) em `check_surgical_diff.py` foi uma medida de hardening bem-sucedida, neutralizando a execução de githooks maliciosos durante a análise de diffs.
2. **Sanitização de Ambiente no Harness:** O método `sanitize_environment()` em `runner.py` filtra adequadamente variáveis contendo fragmentos como `TOKEN`, `KEY`, `SECRET`, `AUTH`, `PASS`. Os testes unitários em `test_harness_isolation.py` validam com sucesso esse comportamento.
3. **Resiliência do Servidor MCP:** O servidor implementa drenagem de buffers em caso de frames JSON-RPC que excedam `max_message_bytes`, prevenindo ataques de negação de serviço por esgotamento de memória. A principal lacuna remanescente de segurança reside na autoridade de caminhos absolutos (`AUD-SEC-002`).

---

## M. AGENTIC SECURITY & GOVERNANÇA DE AGENTES

1. **Instruções e Regras para Agentes (`adapters/antigravity`):** Os arquivos em `adapters/antigravity/.agents/rules/` são diretos e focados:
   - `00-human-authority.md`: proíbe inferir requisitos não especificados.
   - `01-ai-zero-trust.md`: exige evidência verificável e proíbe assumir que testes passando equivalem a segurança total.
   - `02-engineering.md`: impõe simplicidade e proíbe complexidade especulativa.
   - `03-execution-gates.md`: estabelece portões de validação.
2. **Subagentes Customizados:** O framework fornece agentes especializados (`architecture-reviewer`, `correctness-reviewer`, `security-reviewer`). No entanto, o papel deles é opinativo; nenhum deles tem autoridade de bloqueio criptográfico em código sem as ferramentas ativas de enforcement.
3. **Resistência a Reward Hacking:** O cenário `VER-TAMPER-001` testa a tentativa do agente de alterar o oráculo de testes. O oráculo reside fora do workspace e a função `integrity_ok()` em `harness.py` detecta e bloqueia modificações em arquivos rastreados.

---

## N. SUPPLY CHAIN AUDIT

1. **Dependências do Pacote Python:** O arquivo `pyproject.toml` declara `dependencies = []` (zero dependências externas para execução das ferramentas). Esse é um ponto altamente favorável da postura de supply chain, minimizando a superfície de ataques de confusão de dependência (*dependency confusion*) ou comprometimento de pacotes de terceiros.
2. **Verificador PyPI:** A ferramenta `tools/verify_dependencies.py` consulta diretamente a API JSON oficial do PyPI (`https://pypi.org/pypi/{pkg}/json`) e detecta pacotes alucinados, versões inexistentes e colisão com módulos nativos da biblioteca padrão do Python.
3. **Integridade de Workflows:** Como detalhado em `AUD-SUP-002`, o workflow de CI peca ao utilizar comentários com versões fictícias (`# v7.0.1`), necessitando de validação estrita dos commits de ações externas.

---

## O. TESTING & TEST SUITE AUDIT

1. **Cobertura da Suíte:** A suíte conta atualmente com 57 testes unitários distribuídos em 5 arquivos (`test_framework.py`, `test_validation_suite.py`, `test_v2_governance.py`, `test_security_boundaries.py`, `test_harness_isolation.py`). Todos os 57 passam em menos de 2 segundos.
2. **Profundidade das Asserções:**
   - **Fortes:** Os testes de contenção de boundaries em `test_security_boundaries.py` e isolamento em `test_harness_isolation.py` são rigorosos, verificando falha em arquivos gigantes, estouro de frames e filtragem de credenciais.
   - **Fracos:** Os testes em `TestContractsSchemaAndTemplate` (linhas 276–289 de `test_v2_governance.py`) limitam-se a validar se os arquivos são JSONs parseáveis e se títulos estáticos coincidem, sem validar instâncias contra o schema.

---

## P. BENCHMARK & VALIDADE CIENTÍFICA

A metodologia empírica A0/A1/A2 avaliada através do protocolo P1 foi inspecionada segundo critérios formais de metodologia de pesquisa:

1. **Validade de Construto:** Os 10 cenários automatizados cobrem tópicos legítimos de segurança e robustez de software (injeção SQL, controle de acesso, idempotência, atomicidade de transação).
2. **Validade Interna:** Há um sério risco de variável de confusão: a suíte foi executada no Antigravity IDE onde regras comportamentais globais do usuário (`RULE[user_global]`) operam no sistema. Se o agente A0 recebeu instruções comportamentais residuais no contexto, ele não atuou como um "agente cru", explicando em parte a performance perfeita de 100%.
3. **Validade Ecológica:** O benchmark testa funções isoladas em arquivos pequenos (menos de 100 linhas de código). Não há representatividade de sistemas legados de grande porte, múltiplos microsserviços ou desafios de escala com milhares de arquivos.
4. **Conclusão Metodológica:** O benchmark é valioso como teste de regressão e fumaça funcional, mas atualmente carece de poder estatístico para fundamentar alegações acadêmicas de superioridade frente a LLMs contemporâneos.

---

## Q. CI/CD AUDIT

1. **Arquivo de Workflow:** `.github/workflows/validate.yml` é conciso e seguro do ponto de vista de permissões (`permissions: contents: read`).
2. **Lacunas de CI:**
   - O pipeline roda exclusivamente em `ubuntu-latest`. Não há testes em Windows ou macOS.
   - O pipeline não invoca linters estáticos (flake8, ruff, mypy).
   - O pipeline não testa o CLI unificado `auracode` nem o servidor MCP `tools/assurance_mcp.py`.
   - O pipeline não valida a integridade do `MANIFEST.json`.

---

## R. OPEN SOURCE READINESS & GOVERNANÇA

1. **Arquivos Comunitários:**
   - `LICENSE`: MIT License padronizada.
   - `SECURITY.md`: Política de reporte de vulnerabilidades bem estruturada (embora aponte para um email genérico `security@auracode.org` que deve estar ativo no lançamento).
   - `CONTRIBUTING.md` e `CODE_OF_CONDUCT.md`: Diretrizes claras e alinhadas às convenções de projetos de código aberto.
   - `GOVERNANCE.md`: Modelo de governança por consenso e liderança técnica.
2. **Gargalos para Publicação:** O repositório não possui branches protegidas configuradas (pois não está hospedado no GitHub no momento da auditoria) e não possui automação para geração de SBOM e assinatura de releases (Cosign / SLSA).

---

## S. LICENSING AUDIT

1. **Compatibilidade MIT:** O código do framework é original e licenciado sob MIT.
2. **Código de Terceiros e Benchmarks:** Os cenários em `validation/scenarios/` utilizam estruturas sintéticas originais criadas para o projeto, sem incorporação indevida de código proprietário de benchmarks externos.
3. **Citações e Metadados:** Fontes externas em `source-registry.json` limitam-se a metadados bibliográficos e URLs, não violando direitos de propriedade intelectual.

---

## T. DOCUMENTATION AUDIT

1. **Coerência Geral:** A documentação é densa, bem escrita e articulada tecnicamente.
2. **Divergências Fatuais:**
   - `README.md` e `docs/FRAMEWORK.md` afirmam que os contratos são validados por esquemas de máquina, quando na prática não há validador de schema implementado.
   - `VALIDATION-REPORT.md` relata 10 testes quando o repositório possui 57.
   - Referências de comandos que assumem repositório Git ativo falham se o framework for distribuído como arquivo ZIP/tarball.

---

## U. STANDARDS CROSSWALK AUDIT

1. **Análise de Risco de *Citation Laundering*:** O mapeamento em `controls/standards-crosswalk.json` correlaciona padrões como NIST SSDF 1.1, OWASP ASVS e CISA Secure-by-Design aos domínios do catálogo.
2. **Veredito:** O mapeamento é honesto em sua ressalva (`"disclaimer": "High-level objective/domain crosswalk only; not clause-by-clause compliance"`). Não há alegações falsas de certificação oficial. Contudo, para ter utilidade em auditorias de conformidade corporativa, o crosswalk deverá ser aprofundado para vincular requisitos de nível de controle a seções específicas das normas.

---

## V. CLAIM AUDIT

| Alegação Pública do Projeto | Evidência Encontrada | Veredito |
| :--- | :--- | :---: |
| *"Machine-validated controls"* | `validate_framework.py` valida integridade interna, monotonicidade e formatos de ID. | **SUPPORTED** |
| *"Zero external dependencies"* | `pyproject.toml` declara lista vazia de dependências; ferramentas rodam apenas com stdlib. | **SUPPORTED** |
| *"Protected evaluator prevents reward hacking"* | `harness.py` e `integrity_ok()` impedem adulteração de testes em `evaluate`. | **SUPPORTED** |
| *"Isolated candidate execution"* | `runner.py` oferece container Docker e subprocesso sanitizado de segredos. | **PARTIALLY SUPPORTED** (Comandos `baseline` e `gold` sofrem bypass) |
| *"Evidence over confidence"* | `tools/assess.py` aceita status PASS sem nenhuma evidência atrelada. | **MISLEADING** |
| *"Enforced by JSON Schema"* | Schemas existem na pasta `schemas/`, mas não há execução de `jsonschema` no código. | **MISLEADING** |
| *"Proven superior to bare agents"* | Benchmark P1 apresentou A0 = 1.000 e A2 = 1.000 (diferença nula). | **UNSUPPORTED** |

---

## W. REPRODUCIBILITY AUDIT

1. **Condições Testadas:**
   - Ambiente local: Windows 11, Python 3.13.10, Git 2.52.0.
   - Comandos executados diretamente:
     - `python tools/validate_framework.py`: APROVADO (< 0,1 s).
     - `python validation/tools/validate_suite.py`: APROVADO (2,85 s).
     - `python -m unittest discover -s tests -v`: APROVADO (1,70 s).
     - `python validation/tools/analyze_results.py`: APROVADO (< 0,1 s).
2. **Reprodutibilidade Externa:** Alta. Qualquer desenvolvedor com Python 3.9+ instalado consegue reproduzir integralmente as checagens básicas sem instalar dependências via pip.

---

## X. PORTABILITY AUDIT

1. **Separadores de Caminho:** O código trata consistentemente separadores usando `pathlib.Path` e normalização para `/`, permitindo execução estável no Windows.
2. **Subprocess Termination:** Em `runner.py`, o encerramento forçado de árvores de processo utiliza `taskkill /F /T` no Windows e `os.killpg` no Unix, demonstrando cuidado com as particularidades de cada SO.
3. **Limitação em Arquivos Sem Git:** Ferramentas baseadas em Git (`check_surgical_diff.py`) quebram caso o diretório raiz não seja um repositório git inicializado.

---

## Y. DOGFOODING ASSESSMENT (AVALIAÇÃO DO PRÓPRIO FRAMEWORK)

Ao submeter o repositório do framework à avaliação do nível **AL2 Production**:
- **INT (Intent):** Aprovado (especificações claras e documentadas).
- **ARC (Architecture):** **REPROVADO**. Não há `contracts.json` definindo as camadas das próprias ferramentas do framework; `auracode arch .` aborta com erro.
- **AGT (Agentic):** Aprovado (regras e adaptadores definidos).
- **SEC (Security):** **REPROVADO**. A ferramenta CLI com `--json` retorna exit code 0 em falhas, e o servidor MCP não restringe diretório por padrão.
- **VER (Verification):** **REPROVADO**. `assess.py` não valida evidências e não há um `assessment.json` gerado para o próprio projeto.
- **SUP (Supply Chain):** **REPROVADO**. `MANIFEST.json` está desatualizado em 317 arquivos e com hashes quebrados; não há `requirements.txt`.
- **Resultado do Dogfooding:** **FAIL (Reprovado em AL2)**. O framework não atende aos seus próprios requisitos de produção.

---

## Z. REMEDIATION ROADMAP

### P0 — Bloqueadores Mandatórios para Publicação (Prazo Imediato)
1. **Corrigir retorno de exit code das ferramentas CLI (`AUD-SEC-001`):** Garantir que `check_architecture.py`, `verify_dependencies.py` e `check_surgical_diff.py` finalizem com `sys.exit(1)` em caso de violação quando executados com a flag `--json`.
   - *Esforço:* Baixo (0,5 dia). *Risco:* Baixo.
2. **Regenerar e automatizar o `MANIFEST.json` (`AUD-SUP-001`):** Criar script de sincronização de hashes e integrar validação do manifesto ao `validate_framework.py`.
   - *Esforço:* Médio (1 dia). *Risco:* Baixo.
3. **Hardening de caminhos no MCP (`AUD-SEC-002`):** Configurar `--allowed-root` padrão para o diretório de execução atual (`Path.cwd()`), bloqueando navegação não autorizada no filesystem.
   - *Esforço:* Baixo (0,5 dia). *Risco:* Baixo.
4. **Isolar execução em `baseline` e `gold` (`AUD-AGT-001`):** Passar `runner` instanciado nas rotinas de validação de suíte em `harness.py`.
   - *Esforço:* Baixo (0,5 dia). *Risco:* Baixo.
5. **Limpar artefatos residuais e atualizar `.gitignore` (`AUD-RES-001`):** Remover a pasta `graphify-out/` e atualizar o `.gitignore` para ignorar diretórios de ferramentas analíticas externas.
   - *Esforço:* Mínimo (1 hora). *Risco:* Nulo.

### P1 — Antes da Primeira Release Pública Estável (v0.2.0)
1. **Enforcement de Evidência e Schemas em `assess.py` (`AUD-VER-001`, `AUD-SCH-001`):** Integrar validação formal via `jsonschema` (ou validador leve stdlib) e exigir array de evidência para status `PASS`.
   - *Esforço:* Médio (2 dias). *Risco:* Médio.
2. **Implementar Dogfooding no Repositório (`AUD-DOG-001`):** Criar `contracts.json` para o AuraCode, suportar `pyproject.toml` em `verify_dependencies.py` e arquivar o `self-assessment.json`.
   - *Esforço:* Médio (2 dias). *Risco:* Baixo.
3. **Corrigir alinhamento entre `AGT-05` e `VER-07` (`AUD-DES-002`):** Ajustar os catálogos e perfis para que o requisito de testes protegidos seja mandatado ou claramente harmonizado no AL2.
   - *Esforço:* Baixo (1 dia). *Risco:* Baixo.
4. **Atualizar pinagem de GitHub Actions e `VALIDATION-REPORT.md` (`AUD-SUP-002`, `AUD-DOC-001`):** Corrigir a referência em `validate.yml` e regenerar os relatórios estáticos.
   - *Esforço:* Baixo (0,5 dia). *Risco:* Nulo.

### P2 — Antes da Versão 1.0.0
1. **Revisão Estrutural do Nível AL4 (`AUD-DES-001`):** Redesenhar o perfil AL4, incorporando controles adicionais de isolamento de execução, restrições criptográficas de deploy e separação de oráculos para sistemas críticos.
   - *Esforço:* Médio (3 dias). *Risco:* Médio.
2. **Expansão do Benchmark para Combater o Efeito Teto (`AUD-SCI-001`):** Criar a suíte empírica P2 com cenários de alta complexidade que desafiem modelos de raciocínio avançado.
   - *Esforço:* Alto (1 a 2 semanas). *Risco:* Médio.
3. **Defesa contra Importações Dinâmicas no Linter AST (`AUD-LNT-001`):** Adicionar inspeção de nós `ast.Call` para interceptar `__import__` e `importlib`.
   - *Esforço:* Médio (1 dia). *Risco:* Baixo.

### P3 — Melhorias Futuras
1. **Aprofundamento do Standards Crosswalk (`AUD-CWK-001`):** Criar matriz granular de rastreabilidade cláusula a cláusula para NIST SSDF e OWASP ASVS.
2. **Automação de Assinatura Criptográfica:** Adicionar suporte a atestados SLSA e assinatura de releases via Sigstore/Cosign.

---

## CONCLUSÃO DO AUDITOR

O *AI Software Assurance Framework for Agentic Development* é um projeto conceitualmente robusto, com ideias fundamentais para a maturidade da engenharia de software na era dos agentes autônomos. Suas defesas contra reward hacking, linting arquitetural estático e auditoria de dependências são contribuições práticas valiosas.

No entanto, a auditoria revelou que o projeto encontra-se atualmente em um estágio de maturidade intermediário (Draft/Beta), com falhas severas na camada de ferramentas ativas (exit codes com flag JSON), manifesto de release quebrado, motor de avaliação que aceita afirmações sem evidências e ausência de dogfooding.

A execução rigorosa do plano de remediação P0 transformará este repositório de um protótipo promissor em uma ferramenta verdadeiramente confiável e pronta para governar software em escala no ecossistema open source global.
