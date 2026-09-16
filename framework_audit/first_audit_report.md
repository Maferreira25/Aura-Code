# Security Review: C:/ai-software-assurance-framework

## Scope

Repository-wide static audit of the directory snapshot.

- Scan mode: repository
- Target kind: directory_snapshot
- Target ID: ai-software-assurance-framework
- Snapshot digest: codex-security-snapshot/v1:sha256:d1422a09b898a72b168619030a61509dc05afad2b3517644da3a40ac74a92459
- Inventory strategy: directory
- Included paths: .
- Excluded paths: .git/\*\*
- Runtime or test status: not recorded

Limitations and exclusions:
- The provided directory is not a Git worktree, so revision and history controls were not independently verified.
- Candidate code was not executed outside the repository's existing test suite.
- Excluded .git/\*\*: The supplied directory has no usable Git worktree or history.

### Scan Summary

| Field | Value |
| --- | --- |
| Scan outcome | completed |
| Reportable findings | 2 |
| Severity mix | high: 1, medium: 1 |
| Confidence mix | high: 2 |
| Coverage | complete |
| Validation mode | not recorded |

Canonical artifacts: `scan-manifest.json`, `findings.json`, and `coverage.json`. This report is a deterministic projection of those files.

## Threat Model

The evaluator and active governance tools process untrusted repositories and agent-produced workspaces. Candidate code, contracts, paths, results, workflows, and adapters form trust boundaries.

### Assets

- evaluator host
- protected tests
- validation results
- framework integrity

### Trust Boundaries

- candidate workspace to evaluator
- MCP client to local scanner
- repository to CI

### Attacker Capabilities

- modify candidate workspace
- supply an architecture contract and scan target
- run an MCP client with the launching user's authority

### Security Objectives

- isolate hostile candidate execution
- bound untrusted scanning
- preserve evaluator integrity

## Findings

| Finding | Severity | Confidence | Detailed write-up |
| --- | --- | --- | --- |
| [Validation harness executes hostile candidate code with evaluator privileges](#finding-1) | high | high | inline below |
| [Architecture scanner has no resource limits for an untrusted target](#finding-2) | medium | high | inline below |

### Confidence Scale

| Label | Meaning |
| --- | --- |
| high | Direct evidence supports the finding with no material unresolved blocker. |
| medium | Evidence supports a plausible issue, but material runtime or reachability proof remains. |
| low | Evidence is incomplete and the item is retained only for explicit follow-up. |

<a id="finding-1"></a>

### [1] Validation harness executes hostile candidate code with evaluator privileges

| Field | Value |
| --- | --- |
| Severity | high |
| Confidence | high |
| Confidence rationale | Direct static dataflow from an arbitrary workspace argument to Python test discovery and candidate imports. |
| Category | sandbox-escape |
| CWE | CWE-94 |
| Affected lines | validation/tools/harness.py:33-35, validation/tools/harness.py:43-54, validation/tools/harness.py:98-103 |

#### Summary

The evaluator imports candidate modules and tests in unsandboxed subprocesses that retain the evaluator account and environment.

#### Root Cause

The harness treats code submitted for assessment as ordinary tests rather than hostile code requiring an execution boundary.

**Candidate test execution** — `validation/tools/harness.py:43-47`

Candidate-controlled tests and modules execute from the supplied workspace.

```python
r=run([sys.executable,"-m","unittest","discover","-s","tests","-v"],workspace)
```

**Candidate import in protected test run** — `validation/tools/harness.py:52-54`

The protected evaluation retains the full environment and executes with the candidate workspace as cwd; protected tests insert it into sys.path before importing candidate modules.

```python
env=os.environ.copy(); env["TARGET_WORKSPACE"]=str(Path(workspace).resolve()); r=run([...],workspace,env)
```

#### Validation

Argument-list subprocess invocation prevents shell injection but does not sandbox code intentionally imported by Python.

Validation method: Static source review

Counterevidence and remaining uncertainty:
- The harness applies a 15-second timeout.

#### Dataflow

attacker-controlled workspace -\> unittest discovery/protected import -\> Python execution as evaluator user

- **Source:** evaluate workspace argument

- **Sink:** subprocess.run

- **Outcome:** host-level arbitrary code execution

#### Reachability

The evaluate CLI accepts any existing workspace path for an automated scenario.

- **Attacker:** malicious coding agent or workspace supplier

- **Entry point:** validation/tools/harness.py evaluate

- **Outcome:** candidate receives evaluator process privileges

Preconditions:
- An operator evaluates an untrusted or compromised candidate workspace.

#### Severity

**High** — A malicious candidate can execute arbitrary Python on the evaluator host and tamper with scoring or access evaluator resources.

Additional runtime or deployment evidence could raise or lower this severity.

#### Remediation

Run every candidate in a disposable container or VM with a read-only evaluator image, non-root identity, empty/minimal environment, no host credentials, network disabled by default, resource quotas, process-group cleanup, and only a submitted artifact crossing into scoring.

Tests:
- Use a malicious candidate fixture that attempts to read evaluator environment, modify the protected directory, and spawn a child process; all attempts must fail and scoring must remain intact.

Preventive controls:
- Separate candidate execution and scorer contexts.
- Treat candidate code and tests as hostile.

<a id="finding-2"></a>

### [2] Architecture scanner has no resource limits for an untrusted target

| Field | Value |
| --- | --- |
| Severity | medium |
| Confidence | high |
| Confidence rationale | The unbounded traversal, read, and AST parse operations are present on the MCP-controlled path. |
| Category | resource-exhaustion |
| CWE | CWE-400 |
| Affected lines | tools/assurance_mcp.py:148-151, tools/check_architecture.py:62-74, tools/check_architecture.py:87-111 |

#### Summary

The MCP-exposed scanner eagerly traverses matching files, reads them fully, and parses them without file, byte, depth, or time limits.

#### Root Cause

The scanner assumes targets and contracts are small and benign despite accepting them through the MCP interface.

**Eager recursive enumeration** — `tools/check_architecture.py:62-65`

All matching files are materialized without a resource limit.

```python
matched = list(root_dir.rglob(pattern))
```

**Unbounded file read and parse** — `tools/check_architecture.py:87-111`

Each selected file is read and parsed in full without a size or timeout guard.

```python
content = file_path.read_text(encoding="utf-8"); tree = ast.parse(content, filename=str(file_path))
```

#### Validation

Target source is not executed, but enumeration, reads, and parsing remain unbounded.

Validation method: Static source review

Counterevidence and remaining uncertainty:
- AST parsing avoids direct target-code execution.

#### Dataflow

MCP target directory/contract -\> recursive glob -\> full source reads -\> AST parsing

- **Source:** MCP check_architecture arguments

- **Sink:** rglob/read_text/ast.parse

- **Outcome:** CPU, memory, or disk resource exhaustion

#### Reachability

The stdio MCP server forwards client-selected resolved paths to the scanner.

- **Attacker:** MCP client inducing a scan of a hostile repository

- **Entry point:** check_architecture MCP tool

- **Outcome:** IDE or client degradation

#### Severity

**Medium** — An untrusted project or contract can exhaust the client process through traversal or oversized sources.

Additional runtime or deployment evidence could raise or lower this severity.

#### Remediation

Set conservative configurable maximums for traversal depth, matched files, cumulative bytes, and per-file bytes; enumerate lazily; skip oversized files with an incomplete result; and enforce an overall deadline/cancellation path.

Tests:
- A fixture with excessive depth, file count, and one oversized Python file must terminate within the documented limit and report incomplete coverage.

Preventive controls:
- Resource budgets for all untrusted scans.

## Reviewed Surfaces

| Surface | Risk Area | Outcome | Notes |
| --- | --- | --- | --- |
| Candidate validation harness | evaluator isolation | Reported | No additional canonical notes were recorded. |
| Architecture scanner and MCP | untrusted-input resource limits | Reported | No additional canonical notes were recorded. |
| CI workflow supply chain | workflow permissions and action pinning | No issue found | Workflow has read-only contents permission, disabled persisted credentials, and a full-SHA checkout action. |
| Public seeded scenario fixtures | intentionally vulnerable test fixtures | Not applicable | Seeded defects are scenario inputs, not product vulnerabilities. |
