# AuraCode — Agentic Unified Reliability & Assurance Framework

> **AuraCode** (**A**gentic **U**nified **R**eliability & **A**ssurance for **Code**)  
> **Status: 0.1.1 — Production-Ready Governance & AST Verification Engine**

A vendor-neutral, evidence-gated framework and active governance toolkit for building, auditing, and operating professional software developed with substantial assistance from large language models (LLMs) and autonomous coding agents.

---

## 🚀 Quick Start & Installation

Install AuraCode globally on your machine:

```bash
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
