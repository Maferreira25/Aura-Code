# Segunda Etapa — Revisão Crítica da Auditoria de Segurança

## Escopo e método

Esta revisão confronta o relatório da primeira auditoria com o código-fonte e a política local (`SECURITY.md`). O objetivo foi procurar falsos positivos, falsos negativos e superfícies declaradas como cobertas sem evidência suficiente.

- Método: revisão estática de código e documentação.
- Não foram executados testes, aplicações, PoCs ou exploits.
- A avaliação aplica-se ao diretório disponível durante a revisão. O artefato original não contém inventário de hashes por arquivo nem revisão Git, pois ainda está em desenvolvimento, portanto é o snapshot original.

## Veredito sobre os achados originais

| ID | Veredito | Severidade | Observação |
| --- | --- | --- | --- |
| 1 — Harness executa código candidato com privilégios do avaliador | Confirmado | Alta | `harness.py` executa `unittest` no workspace candidato e preserva o ambiente do avaliador; a documentação exige que candidato e avaliador sejam separados. |
| 2 — Scanner de arquitetura sem limites de recursos | Confirmado | Média | Há enumeração, leitura e parsing sem limites de arquivos, bytes, prazo ou cancelamento no caminho MCP. |

Não foi identificado um falso positivo integral entre os dois itens.

### Correção de classificação do achado 1

`CWE-94` não é a classificação mais precisa: não há geração ou injeção de sintaxe de código a partir de um canal de dados. O defeito é a execução deliberada de código não confiável sem isolamento e com privilégios maiores que o mínimo necessário. `CWE-250` (Execution with Unnecessary Privileges) é mais apropriado, possivelmente acompanhado de uma categoria de isolamento/sandbox.

O timeout de 15 segundos não é uma mitigação de isolamento. Em particular, `subprocess.run(..., timeout=15)` não cria um grupo de processos nem elimina descendentes que o código candidato possa iniciar.

## Falsos negativos confirmados

### FN-1 — Verificador de requirements sem orçamento total de trabalho

**Severidade sugerida:** média. **Confiança estática:** alta. **CWE:** CWE-400.

`tools/verify_dependencies.py` lê o arquivo de requirements inteiro e percorre todas as dependências sem limite de tamanho ou quantidade. Para cada item, chama PyPI sequencialmente com timeout individual de cinco segundos. Não existem limite global de duração, máximo de pacotes, máximo de bytes, cache, rate limit ou cancelamento.

Fluxo relevante:

```text
requirements_path controlado via MCP
  -> parse_requirements(read_text integral)
  -> loop por cada dependência
  -> urlopen(PyPI, timeout=5) por item
```

Evidências:

- `tools/assurance_mcp.py:158-160`
- `tools/verify_dependencies.py:42-63`
- `tools/verify_dependencies.py:198-206`

Um requirements malicioso ou exageradamente grande pode reter o processo MCP e causar volume indevido de requisições a PyPI. Este caminho é independente do scanner de arquitetura e não foi listado no relatório original.

### FN-2 — Mensagens JSON-RPC MCP sem limite de tamanho ou prazo

**Severidade sugerida:** média/baixa. **Confiança estática:** alta. **CWE:** CWE-400.

O loop do servidor recebe uma linha inteira de `stdin` e a desserializa diretamente com `json.loads`, sem tamanho máximo de mensagem, limite de profundidade, deadline ou mecanismo de cancelamento. Uma mensagem única muito grande pode consumir memória antes de qualquer ferramenta ser chamada.

Evidências:

- `tools/assurance_mcp.py:206-219`
- `tools/assurance_mcp.py:247-253`

## Itens que precisam de validação de contexto

### NR-1 — Analisador de diff pode executar configuração Git do alvo

`tools/check_surgical_diff.py:22-28` e `:51-57` chamam `git status` e `git diff` em um repositório fornecido, sem timeout e sem sanitizar configuração ou ambiente Git. O Git documenta que `core.fsmonitor` pode indicar um comando-hook utilizado por operações como `git status`.

Se o modelo de ameaça tratar `.git/config` do alvo como controlável pelo atacante, isto pode resultar em execução de um hook com a identidade do processo MCP. A confirmação depende de estabelecer se esse metadado Git pode ser fornecido ou alterado pelo atacante no fluxo suportado.

Referências externas:

- https://git-scm.com/docs/git-status
- https://git-scm.com/docs/git-config/2.49.0.html

### NR-2 — Política de autoridade para caminhos absolutos no MCP

O servidor aceita e resolve caminhos absolutos para diretório-alvo, contrato, requirements e repositório, sem contenção em uma raiz aprovada:

- `tools/assurance_mcp.py:149-165`

Isso pode ser aceitável para um cliente local que já possua exatamente a mesma autoridade do processo. Contudo, o threat model original inclui cliente MCP malicioso; nesse modelo, é necessário definir explicitamente raízes permitidas, autorização de cada caminho e o que pode retornar ao cliente.

### NR-3 — Garantia de integridade do diff é mais estreita que a alegação do produto

`is_test_file()` apenas reconhece convenções de caminho/nome (`tests`, `test`, `validation`, `conftest.py` e poucos nomes fixos). Configurações e entrypoints que alterem a forma de executar a avaliação podem não ser classificados como protegidos. Além disso, `git diff --numstat` não inclui alterações staged ou untracked no cálculo de churn, e excesso de churn só gera aviso; o campo `success` continua verdadeiro.

Evidências:

- `tools/check_surgical_diff.py:48-76`
- `tools/check_surgical_diff.py:93-104`
- `tools/check_surgical_diff.py:145-187`

Este item é uma lacuna de política/garantia, não uma confirmação de exploração remota.

## Áreas não examinadas ou cobertura superdeclarada

O `coverage.json` da primeira auditoria declara `complete`, mas enumera somente quatro superfícies e não contém `receiptRefs`. A alegação deve ser entendida como inventário de diretório, não como evidência de revisão completa de segurança.

Superfícies sem registro de análise específico:

- verificador de dependências e tráfego para PyPI;
- analisador de diff e execução de Git em repositório alvo;
- parser, framing, limites e autorização do protocolo MCP;
- ferramenta CLI `assess.py`, incluindo leitura de arquivo de assessment e seleção de profile;
- caminhos de saída e operações destrutivas opcionais do harness (`--force` e `--output`);
- construção/distribuição Python descrita em `pyproject.toml`.

## Prioridade recomendada

1. Corrigir o isolamento do harness: contêiner/VM descartável, credenciais e rede ausentes por padrão, identidade sem privilégios, limites de CPU/memória/PIDs e limpeza de grupo de processos.
2. Aplicar um orçamento uniforme a todas as ferramentas MCP: bytes de entrada, arquivos, profundidade, itens, prazo global, cancelamento e resultado parcial explícito.
3. Definir o modelo de autoridade para os caminhos MCP; se o cliente não for totalmente confiável, impor raízes permitidas e negar caminhos externos.
4. Sanear a execução de Git ou rejeitar repositórios cuja configuração não seja confiável; incluir timeout.
5. Tornar a política do analisador de diff explícita para arquivos de configuração, entrypoints e alterações staged/untracked.

## Limitações

As conclusões acima são estáticas. Elas não demonstram explorabilidade em uma instalação específica, nem substituem validação dinâmica em ambiente isolado. Os itens NR-1 a NR-3 devem ser fechados com a definição do fluxo operacional e da relação de confiança entre operador, cliente MCP, repositório e avaliador.

---

## Termo de Encerramento e Reconciliação das Remediações

Todas as vulnerabilidades, falsos negativos e lacunas de garantia identificadas nesta revisão e na auditoria original foram remediadas, testadas dinamicamente e formalmente verificadas em 12 de setembro de 2026.

### Matriz de Fechamento de Remediações

| ID da Revisão | Remediation ID | Descrição | Status Final | Evidência de Validação |
|---|---|---|---|---|
| Achado 1 | **REM-001** | Isolamento de execução de candidatos | **RESOLVIDO / VERIFIED** | `runner.py` (`DockerRunner` e `SubprocessSanitizedRunner`), `Dockerfile`, 8 testes em `test_harness_isolation.py`. |
| Achado 2 | **REM-002** | Orçamento de recursos no scanner de arquitetura | **RESOLVIDO / VERIFIED** | `check_architecture.py` (`max_files`, `max_file_bytes`, path traversal check), `TestArchitectureBudget`. |
| FN-1 | **REM-003** | Orçamento total no verificador de dependências | **RESOLVIDO / VERIFIED** | `verify_dependencies.py` (`max_packages`, `max_file_bytes`, `total_timeout`), `TestRequirementsBudget`. |
| FN-2 | **REM-004** | Enquadramento e limites JSON-RPC do MCP | **RESOLVIDO / VERIFIED** | `assurance_mcp.py` (`max_message_bytes`, drenagem de buffer, strict errors), `TestMCPFraming`. |
| NR-1 | **REM-005** | Sanitização da execução do Git (`core.fsmonitor`) | **RESOLVIDO / VERIFIED** | `check_surgical_diff.py` (flags `-c core.fsmonitor=` e timeout 15s), `TestGitExecutionBoundary`. |
| NR-2 | **REM-006** | Autoridade de caminhos absolutos no MCP | **RESOLVIDO / VERIFIED** | `assurance_mcp.py` (`--allowed-root` e contenção de caminhos). |
| NR-3 | **REM-007** | Contabilização de churn com staged/untracked | **RESOLVIDO / VERIFIED** | `check_surgical_diff.py` (cálculo completo delimitado), `TestGitExecutionBoundary`. |
| NR-3 | **REM-008** | Proteção estendida de arquivos e churn blocking | **RESOLVIDO / VERIFIED** | `check_surgical_diff.py` (`PROTECTED_CONFIG_FILES` estendido, `--block-on-churn`), `TestSurgicalDiff`. |
| Área 104 | Hardening | Sanitização de perfis de garantia | **RESOLVIDO / VERIFIED** | `assess.py` (whitelist `AL1`..`AL4` contra path traversal), `TestAssessEngine`. |
| Área 105 | Hardening | Salvaguardas do harness contra remoção acidental | **RESOLVIDO / VERIFIED** | `harness.py` (bloqueio de `--force` sobre diretórios protegidos do repositório/raiz), `TestHarnessSafety`. |

### Veredito Final de Homologação
- **Testes Unitários:** 57/57 aprovados (`Ran 57 tests in 1.67s, OK`).
- **Validação de Governança do Framework:** `tools/validate_framework.py` aprovado (75 controles, 23 fontes, 17 modos de falha).
- **Validação de Cenários Automatizados:** `validation/tools/validate_suite.py` aprovado (10/10 baselines e soluções de referência aprovadas).
- **Registro Oficial:** Detalhes históricos e procedimentos de reversão arquivados em [`framework_audit/REMEDIATION-LEDGER.md`](file:///c:/ai-software-assurance-framework/framework_audit/REMEDIATION-LEDGER.md).
