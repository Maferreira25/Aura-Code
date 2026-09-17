# AuraCode — Agentic Unified Reliability & Assurance Framework

> **AuraCode** (**A**gentic **U**nified **R**eliability & **A**ssurance for **Code**)  
> **Status: 0.1.1 (Beta / Community Preview) — AST Verification Engine & Governance Framework**  
> **Language Support:** Architectural principles and governance controls are language-agnostic. The automated AST inspection engine (`auracode`) currently targets **Python (3.9+)**.

[![Português](https://img.shields.io/badge/Language-Portugu%C3%AAs-blue.svg)](README.pt-BR.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A vendor-neutral, evidence-gated framework and active governance toolkit for building, auditing, and operating professional software developed with substantial assistance from large language models (LLMs) and autonomous coding agents.

---

## 📖 Manifesto: AI Software Assurance for Agentic Development

Artificial intelligence has fundamentally transformed software engineering. Large Language Models (LLMs) and autonomous coding agents can now interpret requirements, refactor systems, invoke tools, and generate thousands of lines of code in seconds. However, this velocity introduces a new class of risks that traditional software engineering never had to face at such speed: hallucinated dependencies, progressive architectural erosion, superficial test suites that merely confirm the AI's own implementation (*vitiated oracles*), unintentional tool misuse, and *"AI slop"* (bloated code, forgotten stubs, and unnecessary abstractions).

Professional software is not just code that compiles and passes the happy path. A commercial system must resist malicious inputs, operate reliably under concurrency, recover from partial failures, safeguard data, and remain maintainable after hundreds of iterations.

The **AI Software Assurance Framework for Agentic Development** bridges this critical gap. Its objective is not to ask engineers to blindly trust AI, but to establish a new foundational premise:

> **AI Zero Trust:** Do not trust AI simply because the output looks plausible. Demand empirical evidence.

Instead of relying on fragile prompts like *"act as a senior software engineer"*, the framework translates established engineering principles (aligned with NIST SSDF, OWASP ASVS/Agentic Security, CISA Secure by Design, OpenSSF, and SLSA) into an **executable system of deterministic controls**, where every AI assertion must answer four fundamental questions:
1. *What must be true?*
2. *What evidence proves this is true?*
3. *How was this evidence independently verified?*
4. *What condition halts deployment if verification fails?*

### How AuraCode Operates in Practice

AuraCode is not a theoretical whitepaper; it is an **executable assurance engine**:

* **Human Authority & Ambiguity Resolution (Gate G1):** Humans retain decision authority over *what* the system does; AI decides *how* to implement it. Before coding begins, any ambiguity affecting behavior, security, or cost is presented to the user in plain language—translating technical trade-offs into functional decisions (e.g., instead of asking *"SQLite or PostgreSQL?"*, it asks *"Should data stay on this computer or be accessible across multiple devices?"*).
* **Native AST Static Analysis Engine (`auracode <command>`):** Deterministic syntax analyzers inspect code for LLM anti-patterns without relying on LLMs to judge LLMs: hunts dead code and stubs (`auracode slop`), prevents resource leaks (`auracode leaks`), catches injection vectors (`auracode sec`), enforces strict type hints, and restricts diffs to under 500 lines to block uncontrolled rewrites.
* **Real-Time IDE Integration via MCP (Model Context Protocol):** A native stdio MCP server (`auracode mcp`) connects AuraCode directly to AI agents and modern IDEs (Antigravity IDE, Cursor, Claude Desktop, VS Code), enforcing guardrails at generation time, not just in CI/CD pipelines.
* **Separation of Duties via Agent Swarms:** The agent that writes code cannot be the sole evaluator. The ecosystem organizes work into segregated personas (requirement scout, architect, feature writer, and independent reviewer).
* **Sandboxed Execution & Anti-Tampering:** Evaluations run inside isolated environments (non-root Docker, zero network, CPU/RAM quotas). The framework's own integrity is cryptographically sealed via SHA-256 hashes (`MANIFEST.json`), preventing autonomous agents from tampering with test oracles or disabling assurance controls.
* **Progressive Assurance Levels (AL1 to AL4):** From low-risk local utilities (AL1) to mission-critical financial infrastructure (AL4), verification rigor (adversarial testing, mutation testing, fuzzing, SBOM provenance) scales proportionally with the impact of failure.

### Empirical Verification

True to the principle that unverified claims are not evidence, AuraCode includes an **experimental benchmark suite** evaluating agents across real-world development scenarios with and without framework governance—empirically measuring functional correctness, vulnerability prevention, test integrity, and verification overhead.

The future of AI programming is not about hoping the model got it right. It is about building systems that **demonstrate with proof when it succeeded**—and rigorously prevent defects from reaching production when it failed.

---

## 🚀 Quick Start & Installation

### Option 1: Instant Execution via `uvx` (No installation needed, like `npx`)

Run any AuraCode command directly in an isolated environment without manual setup or cloning:

```bash
# Scan current project for AI slop and swallowed exceptions
uvx --from git+https://github.com/Maferreira25/Aura-Code.git auracode slop .

# Scan for injection vulnerabilities and shell risks
uvx --from git+https://github.com/Maferreira25/Aura-Code.git auracode sec .

# Start the stdio MCP server for Antigravity IDE / Cursor / Claude Desktop
uvx --from git+https://github.com/Maferreira25/Aura-Code.git auracode mcp
```

### Option 2: Local Installation via `pip`

Install AuraCode into your Python environment:

```bash
git clone https://github.com/Maferreira25/Aura-Code.git
cd Aura-Code
pip install -e .
```

Verify installation:
```bash
auracode --help
```

---

## 🛠️ Integrated AST Verification Suite (`auracode <command>`)

AuraCode provides 12 static AST and governance commands:

```bash
# 1. Initialize workspace directories (.auracode, _auracode_*)
auracode init

# 2. Evaluate requirement ambiguity & non-technical questions (Gate G1)
auracode ambiguity .

# 3. Scan Python AST for dead code, unreachable code, and swallowed errors
auracode slop .

# 4. Scan Python AST for unclosed resource leaks (file handles, sockets, DBs)
auracode leaks .

# 5. Scan Python AST for strict type hints and unconstrained 'Any' usage
auracode types .

# 6. Scan test suite integrity and detect vacuous tests lacking assertions
auracode tests .

# 7. Scan Python AST for injection vectors (eval/exec, shell=True, SQLi)
auracode sec .

# 8. Verify Clean Architecture layer boundaries using AST
auracode arch .

# 9. Verify dependencies against PyPI to prevent hallucinated packages
auracode deps .

# 10. Verify that repository changes are surgical and bounded (< 500 lines churn)
auracode diff .

# 11. Assess project against an Assurance Level (AL1-AL4)
auracode assess assessment.json

# 12. Start stdio Model Context Protocol (MCP) server for IDE integration
auracode mcp
```

---

## 🤖 AuraCode Specialized Agent Swarms (`adapters/antigravity/.agents/agents/`)

AuraCode defines 12 specialized agent profiles enforcing non-technical dialogue protocols and strict evidence scales:

1. **`auracode-scout`**: Fast workspace indexer & structural dependency mapper.
2. **`auracode-archaeologist`**: Historical commit log, contract lineage, and evolutionary debt analyzer.
3. **`auracode-architect`**: Clean Architecture Guardian enforcing layer isolation and Gate G1 interrogation.
4. **`auracode-writer`**: Production feature implementation agent enforcing zero slop and strict type safety.
5. **`auracode-reviewer`**: Autonomous QA runner executing the full 11-part `auracode` static analysis suite.
6. **`auracode-clarify`**: Non-technical requirement dialogue generator with mandatory doubt verification.
7. **`auracode-brainstorm`**: Pre-development planning agent translating user concepts into plain-language option menus.
8. **`auracode-new`**: Greenfield project scaffolding agent creating Clean Architecture folder structures (`domain/`, `usecases/`, `adapters/`, `infrastructure/`, `tests/`).
9. **`auracode-debugger-graph`**: Call graph topology mapper tracing execution paths.
10. **`auracode-debugger`**: Bug investigator reproducing failures via failing unit tests first.
11. **`auracode-debugger-fix`**: Surgical bug fixer applying minimal diffs to make reproducing tests pass.
12. **`auracode-refactor`**: Quality specialist eliminating slop, unclosed resources, and missing type hints without altering public APIs.

---

## 📜 License & Governance
Licensed under the MIT License.
