# AuraCode — Agentic Unified Reliability & Assurance Framework

> **AuraCode** (**A**gentic **U**nified **R**eliability & **A**ssurance for **Code**)  
> **Status: 0.1.1 (Beta / Community Preview) — AST Verification Engine, Lay-User AI Pair Programming & Governance Framework**  
> **Language Support:** Architectural principles and governance controls are language-agnostic. The automated AST inspection engine (`auracode`) currently targets **Python (3.9+)**.

[![Português](https://img.shields.io/badge/Language-Portugu%C3%AAs-blue.svg)](README.pt-BR.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A vendor-neutral, evidence-gated framework and active governance toolkit for building, auditing, and operating professional software developed with substantial assistance from large language models (LLMs) and autonomous coding agents—specifically designed to guide **lay/non-technical users** through building software from scratch or improving existing systems using academic software engineering best practices.

---

## 📖 Manifesto: AI Software Assurance & Lay-User Pair Programming

Artificial intelligence has fundamentally transformed software engineering. Large Language Models (LLMs) and autonomous coding agents can now interpret requirements, refactor systems, invoke tools, and generate thousands of lines of code in seconds. However, this velocity introduces critical risks when non-technical users interact with AI: hallucinated dependencies, silent assumptions, architectural erosion, superficial test suites (*vitiated oracles*), and *"AI slop"* (bloated code, forgotten stubs, and unnecessary abstractions).

AuraCode bridges this gap through **Zero-Trust AI Pair Programming for Non-Technical Users**:

> **AI Zero Trust & Zero Presumption:** Do not trust AI simply because the output looks plausible. AI must never silently guess requirements, interfaces, or technical trade-offs. Demand empirical evidence and explicit human authorization for every decision.

### Core Principles of AuraCode

1. **Zero-Presumption Directive (Tolerância Zero a Presunções):** The AI agent is strictly forbidden from inferring or deciding business rules, screen behaviors, data models, or error cases on its own. Every ambiguity—no matter how small—triggers a plain-language question to the user.
2. **House Blueprint First Paradigm (`_auracode_sdd/`):** Just like constructing a house, no application code, directories, or scripts are generated before the complete theoretical architecture (frontend, backend, database, security, APIs, design system, assurance level AL1-AL4) is fully specified and reviewed in 7 markdown blueprints under `_auracode_sdd/`.
3. **Plain-Language Dialogue & Analogies:** Complex technical trade-offs are translated into real-world analogies (e.g., Database $\rightarrow$ *"Smart Filing Cabinet"*, Backend $\rightarrow$ *"Restaurant Kitchen"*, API $\rightarrow$ *"Waiter taking orders"*, Frontend $\rightarrow$ *"Storefront counter"*, Authentication $\rightarrow$ *"ID Badge"*). Structured choice menus with simple pros and cons are provided whenever technical options arise.
4. **Native AST Static Analysis (`auracode <command>`):** Deterministic syntax analyzers inspect code for LLM anti-patterns without relying on LLMs to judge LLMs: hunts dead code and stubs (`auracode slop`), prevents resource leaks (`auracode leaks`), catches injection vectors (`auracode sec`), enforces strict type hints, and restricts diffs to under 500 lines to block uncontrolled rewrites.
5. **Progressive Assurance Levels (AL1 to AL4):** From low-risk local utilities (AL1) to mission-critical financial infrastructure (AL4), verification rigor scales proportionally with the impact of failure.

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

## 🤖 AuraCode Active Skills & Persona Swarms (`.agents/skills/`)

AuraCode defines 9 primary IDE skills enforcing non-technical dialogue protocols and strict evidence scales:

1. **`auracode`**: Main framework entry point and command navigator.
2. **`auracode-new`**: Greenfield project workflow conducting plain-language interviews and generating the 7-part House Blueprint in `_auracode_sdd/`.
3. **`auracode-clarify`**: Non-technical requirement dialogue generator with zero presumptions and analogy menus.
4. **`auracode-brainstorm`**: Ideation and scope framing agent translating raw user concepts into plain-language feature menus.
5. **`auracode-forward`**: Spec-driven execution agent implementing Clean Architecture code (`domain/`, `usecases/`, `adapters/`, `infrastructure/`, `tests/`) strictly from approved blueprints.
6. **`auracode-audit`**: Autonomous QA runner executing the full 12-part `auracode` static analysis suite.
7. **`auracode-debugger`**: Bug investigator reproducing failures via failing unit tests first before applying minimal surgical fixes.
8. **`auracode-refactor`**: Quality specialist eliminating slop, unclosed resources, and missing type hints without altering public APIs.
9. **`auracode-agents-help`**: Explanatory catalog detailing the specialized agent personas using plain-language analogies.

---

## 📜 License & Governance
Licensed under the MIT License.

