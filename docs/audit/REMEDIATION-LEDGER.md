# REMEDIATION LEDGER — AI SOFTWARE ASSURANCE FRAMEWORK

**Document ID:** `LEDGER-MASTER-2026-09-12`  
**Repository Version:** `0.1.1-draft`  
**Initial Clean Tree SHA-256:** `044be35157a2066e82c06afbd073881fd50df55540946dd08832d0e015fc6e04`  
**Framework Baseline:** `tools/validate_framework.py` (PASS), `validate_suite.py` (PASS), `unittest` (57 tests PASS), `analyze_results.py` (PASS).

---

## Reconciliation & Normalization Table

| REM-ID | Source Findings | Title | Status | Final Severity | Confidence | Priority |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **REM-001** | `AUD-SEC-001` | Exit code 0 com flag `--json` em falhas nas ferramentas CLI | CONFIRMED | **CRITICAL** | High | **P0** |
| **REM-002** | `AUD-SUP-001` | `MANIFEST.json` desatualizado e colisão de hashes | CONFIRMED | **CRITICAL** | High | **P0** |
| **REM-003** | `AUD-VER-001` | Motor `assess.py` aprova status PASS sem checagem de evidência | CONFIRMED | **HIGH** | High | **P0** |
| **REM-004** | `AUD-AGT-001` / `REM-001` | Bypass do runner isolado em `cmd_baseline` e `cmd_gold` do harness | CONFIRMED | **HIGH** | High | **P0** |
| **REM-005** | `AUD-SEC-002` / `NR-2` | Servidor MCP sem contenção padrão de diretório (`--allowed-root` default None) | CONFIRMED | **HIGH** | High | **P0** |
| **REM-006** | `META-FN-1` | 11 de 12 cenários de benchmark com `integrity_files: []` (sem proteção contra adulteração) | CONFIRMED | **HIGH** | High | **P0** |
| **REM-007** | `AUD-LNT-001` / `META-FN-2` | Linter AST vulnerável a bypass por imports relativos (`from .. import x`) e chamadas dinâmicas | CONFIRMED | **MEDIUM** | High | **P1** |
| **REM-008** | `META-FN-3` | `verify_dependencies.py` ignora dependências com extras PEP 508 | CONFIRMED | **MEDIUM** | High | **P1** |
| **REM-009** | `META-FN-4` | `check_surgical_diff.py` bloqueia indevidamente edição de `pyproject.toml` como teste | CONFIRMED | **MEDIUM** | High | **P1** |
| **REM-010** | `AUD-DOG-001` | Falha no dogfooding do próprio framework (`contracts.json`, `pyproject.toml`, self-assessment) | CONFIRMED | **HIGH** | High | **P1** |
| **REM-011** | `AUD-SCH-001` | Schemas JSON sem validação estrutural no validador do framework | CONFIRMED | **MEDIUM** | High | **P1** |
| **REM-012** | `AUD-SUP-002` | Workflow CI com tag fictícia `# v7.0.1` | CONFIRMED | **MEDIUM** | High | **P1** |
| **REM-013** | `AUD-RES-001` | 97 arquivos residuais de cache em `graphify-out/` e `.gitignore` incompleto | CONFIRMED | **INFO** | High | **P1** |
| **REM-014** | `AUD-DOC-001` | `VALIDATION-REPORT.md` relata contagem desatualizada de testes | CONFIRMED | **LOW** | High | **P2** |
| **REM-015** | `AUD-CWK-001` | Standards crosswalk mapeia normas inteiras em nível alto | CONFIRMED | **LOW** | High | **P3** |
| **REM-016** | `AUD-DES-002` | Aparente contradição entre `AGT-05` (AL2) e `VER-07` (AL3) | **FALSE POSITIVE** | **INFO** | High | **N/A** |
| **REM-017** | `AUD-DES-001` | Desproporcionalidade AL4 com 1 controle não mandatório | PARTIALLY CONFIRMED | **LOW** | Medium | **USER DECISION** |
| **REM-018** | `AUD-SCI-001` / `META-FN-6` | Efeito teto e amostra N=36 no benchmark empírico P1 | CONFIRMED | **MEDIUM** | High | **P2** |
| **REM-019** | `FN-01` | Falha de empacotamento: omissão de package-data e ausência de `__init__.py` | CONFIRMED | **CRITICAL** | High | **P0** |
| **REM-020** | `AUD-SEC-001` | Falha aberta em indisponibilidade de rede no `verify_dependencies.py` | CONFIRMED | **CRITICAL** | High | **P0** |
| **REM-021** | `FN-02` | Ponto cego bidirecional no validador do `MANIFEST.json` (Disk -> Manifest) | CONFIRMED | **HIGH** | High | **P0** |
| **REM-022** | `AUD-SEC-002` | Subversão de oráculo por monkeypatching em memória no `SubprocessSanitizedRunner` | CONFIRMED | **HIGH** | High | **P0** |
| **REM-023** | `AUD-VER-001` | Validação superficial de evidências em `tools/assess.py` | CONFIRMED | **HIGH** | High | **P0** |
| **REM-024** | `FN-04` | Sobreprivilégio de subagentes revisores (`run_command` indevido) | CONFIRMED | **HIGH** | High | **P1** |
| **REM-025** | `FN-03` | Arquivos Python não contratados não reportados pelo linter de arquitetura | CONFIRMED | **MEDIUM** | High | **P1** |
| **REM-026** | `FN-05` | Falso positivo no linter de diff contra pacotes de negócio `validation/` | CONFIRMED | **MEDIUM** | High | **P1** |
| **REM-027** | `AUD-SUP-001` | Omissão da pasta `.agents` no script `update_manifest.py` | CONFIRMED | **MEDIUM** | High | **P1** |
| **REM-028** | `AUD-DOC-001` | Argumentos de diff desatualizados no `README.md` (`--allowed-scope`, `--max-churn`) | CONFIRMED | **MEDIUM** | High | **P1** |
| **REM-029** | `AUD-DOG-002` | Falha de dogfooding: `auracode deps` sem alvo falhava por buscar `requirements.txt` | CONFIRMED | **MEDIUM** | High | **P1** |
| **REM-030** | `FN-06` | Divergência descritiva do AL4 em `docs/ASSURANCE-LEVELS.md` | CONFIRMED | **MEDIUM** | High | **P2** |

---

## Detailed Ledger Entries

### REM-001
- **Source Findings:** `AUD-SEC-001`
- **Status:** CONFIRMED / REPRODUCED
- **Severity:** CRITICAL | **Confidence:** HIGH
- **Root Cause:** Os scripts `check_architecture.py`, `verify_dependencies.py` e `check_surgical_diff.py` executavam `print(json.dumps(result))` no bloco `if args.json:` e retornavam normalmente sem chamar `sys.exit(1 if not result.get('success') else 0)`.
- **Files Affected:** `tools/check_architecture.py`, `tools/verify_dependencies.py`, `tools/check_surgical_diff.py`
- **Controls Affected:** `ARC-01`, `SUP-01`, `VER-01`, `RLS-01`
- **Remediation Strategy:** Garantir que o exit code reflita o campo booleano de sucesso (`result['success']`) independentemente do formato de saída (`--json`).
- **Regression Test Required:** Sim (`tests/test_v2_governance.py`).
- **Validation Method:** Subprocessos executados com `--json` em condições de erro devem retornar código de saída 1 ou 2.

### REM-002
- **Source Findings:** `AUD-SUP-001`
- **Status:** CONFIRMED / REPRODUCED
- **Severity:** CRITICAL | **Confidence:** HIGH
- **Root Cause:** O `MANIFEST.json` foi gerado manualmente na v1 (183 arquivos) e nunca atualizado durante o desenvolvimento da v2.
- **Files Affected:** `MANIFEST.json`, `tools/validate_framework.py`, `tools/update_manifest.py` (novo)
- **Controls Affected:** `SUP-01`, `SUP-05`, `SUP-06`, `RLS-01`
- **Remediation Strategy:** Criar utilitário `update_manifest.py` e adicionar checagem de integridade em `validate_framework.py`.
- **Regression Test Required:** Sim (`test_framework.py`).
- **Validation Method:** `python tools/validate_framework.py` deve atestar 100% de conformidade com todos os arquivos rastreados.

### REM-003
- **Source Findings:** `AUD-VER-001`
- **Status:** CONFIRMED / REPRODUCED
- **Severity:** HIGH | **Confidence:** HIGH
- **Root Cause:** `tools/assess.py` aceitava `status: PASS` sem checar se havia array `"evidence"` não vazio e justificativa.
- **Files Affected:** `tools/assess.py`
- **Controls Affected:** `VER-01`, `VER-08`, `GOV-01`
- **Remediation Strategy:** Exigir que cada controle marcado como `PASS` forneça uma lista não vazia de evidências (`evidence: [...]`), rejeitando autoasserções cegas.
- **Regression Test Required:** Sim (`tests/test_v2_governance.py`).
- **Validation Method:** Teste unitário com controle PASS sem evidência deve falhar a avaliação.

### REM-004
- **Source Findings:** `AUD-AGT-001` / `REM-001`
- **Status:** CONFIRMED / REPRODUCED
- **Severity:** HIGH | **Confidence:** HIGH
- **Root Cause:** `cmd_baseline` e `cmd_gold` em `harness.py` chamavam `public_tests` e `protected_tests` sem passar a instância do `runner`.
- **Files Affected:** `validation/tools/harness.py`
- **Controls Affected:** `AGT-04`, `AGT-05`, `VER-07`, `SEC-04`
- **Remediation Strategy:** Instanciar `runner = get_runner(mode="auto")` e repassá-lo em `cmd_baseline` e `cmd_gold`.
- **Regression Test Required:** Sim (`tests/test_harness_isolation.py`).
- **Validation Method:** `validate_suite.py` executa sob runner isolado sem herdar variáveis de ambiente secretas.

### REM-005
- **Source Findings:** `AUD-SEC-002` / `NR-2`
- **Status:** CONFIRMED / REPRODUCED
- **Severity:** HIGH | **Confidence:** HIGH
- **Root Cause:** `--allowed-root` tinha valor default `None`, permitindo autoridade irrestrita no filesystem.
- **Files Affected:** `tools/assurance_mcp.py`
- **Controls Affected:** `AGT-03`, `AGT-04`, `SEC-04`
- **Remediation Strategy:** Alterar o default de `allowed_root` para `Path.cwd().resolve()`.
- **Regression Test Required:** Sim (`tests/test_security_boundaries.py`).
- **Validation Method:** Chamadas MCP sem `--allowed-root` para fora do diretório de execução atual devem retornar `PermissionError`.

### REM-006
- **Source Findings:** `META-FN-1`
- **Status:** CONFIRMED / REPRODUCED
- **Severity:** HIGH | **Confidence:** HIGH
- **Root Cause:** 11 cenários de teste em `validation/scenarios/public/` possuíam `"integrity_files": []` em seus metadados `scenario.json`, permitindo adulteração de testes públicos sem detecção por `integrity_ok()`.
- **Files Affected:** `validation/scenarios/public/*/scenario.json`
- **Controls Affected:** `AGT-05`, `VER-07`, `VER-08`
- **Remediation Strategy:** Registrar todos os arquivos em `tests/` no array `integrity_files` de cada cenário.
- **Regression Test Required:** Sim (`validation/tools/validate_suite.py`).
- **Validation Method:** Alterar um teste público em qualquer cenário e verificar que `integrity_ok()` detecta a modificação e rejeita o run.

### REM-007
- **Source Findings:** `AUD-LNT-001` / `META-FN-2`
- **Status:** CONFIRMED / REPRODUCED
- **Severity:** MEDIUM | **Confidence:** HIGH
- **Root Cause:** `ImportVisitor` em `check_architecture.py` não inspecionava `alias.name` quando `node.module` era `None` em imports relativos (`from .. import forbidden`), e não checava nós `ast.Call` para `__import__` / `importlib.import_module`.
- **Files Affected:** `tools/check_architecture.py`
- **Controls Affected:** `ARC-01`, `ARC-02`, `SEC-04`
- **Remediation Strategy:** Interceptar nós de chamadas dinâmicas e tratar nós `ImportFrom` relativos atribuindo `alias.name` ao módulo verificado.
- **Regression Test Required:** Sim (`tests/test_v2_governance.py`).
- **Validation Method:** Teste unitário com `from .. import db` e `__import__("db")` deve ser interceptado e registrar violação.

### REM-008
- **Source Findings:** `META-FN-3`
- **Status:** CONFIRMED / REPRODUCED
- **Severity:** MEDIUM | **Confidence:** HIGH
- **Root Cause:** O regex de `parse_requirements` em `verify_dependencies.py` não aceitava colchetes de extras (`[extra]`), descartando silenciosamente linhas como `fastapi[all]>=0.100.0`.
- **Files Affected:** `tools/verify_dependencies.py`
- **Controls Affected:** `SUP-01`, `SUP-06`
- **Remediation Strategy:** Atualizar regex para `r"^([A-Za-z0-9_.\-]+)(?:\[[^\]]+\])?(?:([=><~!^]+)(.*))?$"` e usar `sys.stdlib_module_names` no Python 3.10+.
- **Regression Test Required:** Sim (`tests/test_v2_governance.py`).
- **Validation Method:** Teste com `fastapi[all]>=0.100.0` extrai `name: "fastapi"` com sucesso.

### REM-009
- **Source Findings:** `META-FN-4`
- **Status:** CONFIRMED / REPRODUCED
- **Severity:** MEDIUM | **Confidence:** HIGH
- **Root Cause:** `pyproject.toml` estava na lista `PROTECTED_CONFIG_FILES` em `check_surgical_diff.py`, sendo incorretamente tratado como arquivo de teste oracular em `is_test_file()`.
- **Files Affected:** `tools/check_surgical_diff.py`
- **Controls Affected:** `VER-08`, `RLS-01`
- **Remediation Strategy:** Remover `pyproject.toml` de `PROTECTED_CONFIG_FILES`, permitindo alterações ordinárias de dependências e metadados.
- **Regression Test Required:** Sim (`tests/test_v2_governance.py`).
- **Validation Method:** Modificação em `pyproject.toml` não acusa `unauthorized_test_tampering`.

### REM-010
- **Source Findings:** `AUD-DOG-001`
- **Status:** CONFIRMED / REPRODUCED
- **Severity:** HIGH | **Confidence:** HIGH
- **Root Cause:** O repositório não possuía `contracts.json`, `verify_dependencies.py` não suportava inspecionar `pyproject.toml`, e não havia um `self-assessment.json`.
- **Files Affected:** `contracts.json` (novo), `tools/verify_dependencies.py`, `templates/assessment.json`
- **Controls Affected:** `ARC-01`, `SUP-01`, `GOV-01`, `GOV-08`
- **Remediation Strategy:** Criar `contracts.json` do AuraCode, adicionar suporte à leitura de dependências em `pyproject.toml`, e criar script de autoavaliação.
- **Regression Test Required:** Sim.
- **Validation Method:** Executar `auracode arch .` e `auracode deps` com sucesso sobre o repositório.

### REM-011
- **Source Findings:** `AUD-SCH-001`
- **Status:** CONFIRMED / REPRODUCED
- **Severity:** MEDIUM | **Confidence:** HIGH
- **Root Cause:** Os schemas JSON em `schemas/` não eram validados em tempo de execução nem integrados aos validadores.
- **Files Affected:** `tools/validate_framework.py`, `schemas/*.schema.json`
- **Controls Affected:** `VER-01`, `GOV-08`
- **Remediation Strategy:** Integrar validação estrutural dos schemas JSON e de conformidade dos templates ao validador do framework (usando stdlib com fallback).
- **Regression Test Required:** Sim.
- **Validation Method:** `validate_framework.py` valida formalmente os schemas JSON.

### REM-012
- **Source Findings:** `AUD-SUP-002`
- **Status:** CONFIRMED / REPRODUCED
- **Severity:** MEDIUM | **Confidence:** HIGH
- **Root Cause:** `.github/workflows/validate.yml` usava o comentário `# v7.0.1` para `actions/checkout`.
- **Files Affected:** `.github/workflows/validate.yml`
- **Controls Affected:** `SUP-06`, `RLS-01`
- **Remediation Strategy:** Atualizar a referência de checkout para o SHA imutável oficial de `actions/checkout@v4` com comentário verídico `# v4.2.2`.
- **Regression Test Required:** Sim (`tools/validate_framework.py`).
- **Validation Method:** `validate_framework.py` valida SHA do GitHub Actions com sucesso.

### REM-013
- **Source Findings:** `AUD-RES-001`
- **Status:** CONFIRMED / REPRODUCED
- **Severity:** INFO | **Confidence:** HIGH
- **Root Cause:** O diretório `graphify-out/` continha 97 arquivos temporários de AST externa que não foram ignorados no `.gitignore`.
- **Files Affected:** `.gitignore`, remoção de `graphify-out/`
- **Controls Affected:** `RLS-01`
- **Remediation Strategy:** Adicionar `graphify-out/` ao `.gitignore` e limpar os arquivos residuais.
- **Regression Test Required:** Sim.
- **Validation Method:** `git status` limpo.

### REM-019
- **Source Findings:** `FN-01`
- **Status:** RESOLVED
- **Severity:** CRITICAL | **Confidence:** HIGH
- **Root Cause:** `pyproject.toml` omitia `[tool.setuptools.package-data]` e pastas `controls/`, `profiles/`, `schemas/`, `templates/` não tinham `__init__.py`, impedindo distribuição correta via `pip install`.
- **Files Affected:** `pyproject.toml`, `controls/__init__.py`, `profiles/__init__.py`, `schemas/__init__.py`, `templates/__init__.py`
- **Controls Affected:** `SUP-01`, `RLS-01`
- **Remediation Strategy:** Adicionar `__init__.py` aos pacotes de dados e configurar `package-data` no `pyproject.toml`.
- **Regression Test Required:** Sim (`python -c "import setuptools; print(setuptools.find_packages())"`).
- **Validation Method:** `setuptools.find_packages()` descobre todos os pacotes.

### REM-020
- **Source Findings:** `AUD-SEC-001`
- **Status:** RESOLVED
- **Severity:** CRITICAL | **Confidence:** HIGH
- **Root Cause:** `verify_dependencies.py` aprovava dependências não verificadas em caso de falha de conexão (fail-open silencioso).
- **Files Affected:** `tools/verify_dependencies.py`, `tools/assurance.py`
- **Controls Affected:** `SUP-01`, `SUP-04`, `SEC-06`
- **Remediation Strategy:** Enforçar fail-closed estrito (`success = False`, exit code 1) em caso de erro de rede, salvo flag explícita `--allow-unverified-network` ou `--offline`.
- **Regression Test Required:** Sim (`tests/test_v2_governance.py`).
- **Validation Method:** Pacote não verificado por erro de rede gera código 1 e `success: False`.

### REM-021
- **Source Findings:** `FN-02`
- **Status:** RESOLVED
- **Severity:** HIGH | **Confidence:** HIGH
- **Root Cause:** `validate_framework.py` verificava apenas `MANIFEST.json` -> Disco, ignorando Disco -> `MANIFEST.json` (ponto cego reverso).
- **Files Affected:** `tools/validate_framework.py`
- **Controls Affected:** `SUP-01`, `SUP-05`, `RLS-01`
- **Remediation Strategy:** Implementar verificação bidirecional completa, detectando arquivos untracked no disco.
- **Regression Test Required:** Sim (`python tools/validate_framework.py`).
- **Validation Method:** Presença de arquivo untracked causa falha imediata na validação.

### REM-022
- **Source Findings:** `AUD-SEC-002`
- **Status:** RESOLVED
- **Severity:** HIGH | **Confidence:** HIGH
- **Root Cause:** No modo `SubprocessSanitizedRunner`, código avaliado podia sobrescrever asserções do `unittest.TestCase` em memória.
- **Files Affected:** `validation/tools/runner.py`, `tests/test_harness_isolation.py`
- **Controls Affected:** `AGT-05`, `VER-07`, `SEC-04`
- **Remediation Strategy:** Adicionar runner de teste à prova de adulteração (`RUNNER_ORACLE_WRAPPER_CODE`) checando oráculos antes e depois de cada teste e ao final da suíte (exit code 101).
- **Regression Test Required:** Sim (`tests/test_harness_isolation.py`).
- **Validation Method:** Teste malicioso com monkeypatching de `assertEqual` é abortado com código 101.

### REM-023
- **Source Findings:** `AUD-VER-001`
- **Status:** RESOLVED
- **Severity:** HIGH | **Confidence:** HIGH
- **Root Cause:** `tools/assess.py` aceitava strings com nomes fictícios de arquivos como evidência de conformidade.
- **Files Affected:** `tools/assess.py`, `docs/ARCHITECTURE.md`, `tests/test_v2_governance.py`
- **Controls Affected:** `VER-01`, `VER-08`, `GOV-01`
- **Remediation Strategy:** Verificar a existência física de arquivos citados como evidência em relação ao root do projeto avaliado; criar `docs/ARCHITECTURE.md`.
- **Regression Test Required:** Sim (`tests/test_v2_governance.py`).
- **Validation Method:** Arquivo inexistente em evidência é marcado como `invalid_pass` e reprova a avaliação.

### REM-024
- **Source Findings:** `FN-04`
- **Status:** RESOLVED
- **Severity:** HIGH | **Confidence:** HIGH
- **Root Cause:** Subagentes revisores (read-only) em `adapters/antigravity/.agents/agents/*.md` possuíam permissão `run_command`.
- **Files Affected:** `adapters/antigravity/.agents/agents/*-reviewer/agent.md`
- **Controls Affected:** `AGT-03`, `SEC-04`
- **Remediation Strategy:** Remover `run_command` e `commandExecutionPolicy` dos manifestos dos revisores.
- **Regression Test Required:** Inspeção de YAML.
- **Validation Method:** Agentes contêm apenas ferramentas read-only (`view_file`, `grep_search`).

### REM-025
- **Source Findings:** `FN-03`
- **Status:** RESOLVED
- **Severity:** MEDIUM | **Confidence:** HIGH
- **Root Cause:** `check_architecture.py` não reportava arquivos Python não mapeados em nenhuma camada (`uncontracted files`).
- **Files Affected:** `tools/check_architecture.py`, `tests/test_v2_governance.py`
- **Controls Affected:** `ARC-01`, `ARC-02`
- **Remediation Strategy:** Rastrear e listar arquivos Python não mapeados no resultado JSON e CLI.
- **Regression Test Required:** Sim (`tests/test_v2_governance.py`).
- **Validation Method:** Arquivos Python sem contrato são listados no output.

### REM-026
- **Source Findings:** `FN-05`
- **Status:** RESOLVED
- **Severity:** MEDIUM | **Confidence:** HIGH
- **Root Cause:** `is_test_file` em `check_surgical_diff.py` tratava qualquer caminho contendo `"validation"` como teste protegido.
- **Files Affected:** `tools/check_surgical_diff.py`, `tests/test_v2_governance.py`
- **Controls Affected:** `VER-07`, `RLS-01`
- **Remediation Strategy:** Restringir verificação de `validation` apenas à raiz do repositório (`parts[0] == 'validation'`).
- **Regression Test Required:** Sim (`tests/test_v2_governance.py`).
- **Validation Method:** `is_test_file("src/validation/rules.py")` retorna `False`.

### REM-027
- **Source Findings:** `AUD-SUP-001`
- **Status:** RESOLVED
- **Severity:** MEDIUM | **Confidence:** HIGH
- **Root Cause:** `update_manifest.py` excluía incondicionalmente a pasta `.agents`, ignorando `adapters/antigravity/.agents/`.
- **Files Affected:** `tools/update_manifest.py`
- **Controls Affected:** `SUP-01`, `SUP-06`, `RLS-01`
- **Remediation Strategy:** Excluir `.agents` apenas quando na raiz do repositório.
- **Regression Test Required:** Sim (`update_manifest.py`).
- **Validation Method:** Todos os 15 arquivos de `adapters/` incluídos no `MANIFEST.json`.

### REM-028
- **Source Findings:** `AUD-DOC-001`
- **Status:** RESOLVED
- **Severity:** MEDIUM | **Confidence:** HIGH
- **Root Cause:** `README.md` referenciava argumentos obsoletos de diff (`--allowed-scope`, `--max-churn`).
- **Files Affected:** `README.md`
- **Controls Affected:** `INT-01`, `RLS-01`
- **Remediation Strategy:** Atualizar `README.md` para `--scope` e `--max-lines`.
- **Regression Test Required:** Manual CLI.
- **Validation Method:** Comando documentado roda sem erros.

### REM-029
- **Source Findings:** `AUD-DOG-002`
- **Status:** RESOLVED
- **Severity:** MEDIUM | **Confidence:** HIGH
- **Root Cause:** `auracode deps` sem alvo tentava ler `requirements.txt` obrigatoriamente, quebrando dogfooding em projetos com `pyproject.toml`.
- **Files Affected:** `tools/assurance.py`, `tools/verify_dependencies.py`
- **Controls Affected:** `SUP-01`, `RLS-01`
- **Remediation Strategy:** Autodetectar `requirements.txt`, `pyproject.toml` ou `setup.cfg` quando alvo não for passado.
- **Regression Test Required:** Sim.
- **Validation Method:** `auracode deps` executa com sucesso no repositório AuraCode.

### REM-030
- **Source Findings:** `FN-06`
- **Status:** RESOLVED
- **Severity:** MEDIUM | **Confidence:** HIGH
- **Root Cause:** `docs/ASSURANCE-LEVELS.md` listava no AL4 controles que pertencem na realidade ao AL2 e AL3.
- **Files Affected:** `docs/ASSURANCE-LEVELS.md`
- **Controls Affected:** `INT-03`, `VER-09`
- **Remediation Strategy:** Alinhar o texto do AL4 com a definição formal de `controls/catalog.json` (`VER-09` e verificação de invariantes críticos).
- **Regression Test Required:** Manual review.
- **Validation Method:** Texto alinhado com `controls/catalog.json` e `profiles/al4.json`.
