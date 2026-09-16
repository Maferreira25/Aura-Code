# AuraCode Architecture Specification

## 1. System Overview and Scope

AuraCode is an open-source software assurance framework designed to enforce governance, architectural boundaries, dependency provenance, and empirical evaluation for AI-generated codebases.

## 2. Architectural Layers and Boundaries

As specified normatively in `contracts.json`, AuraCode maintains strict separation between runtime governance tools and evaluation harnesses:

1. **Governance Tools Layer (`tools/`)**:
   - Contains active linters, assessment engines, dependency verifiers, and MCP servers.
   - **Boundary Invariant**: Pure Python standard library only (zero external runtime dependencies).
   - **Forbidden Imports**: `requests`, `httpx`, web frameworks, or internal validation scenarios.

2. **Validation and Evaluation Harness Layer (`validation/tools/`)**:
   - Contains test runners (`DockerRunner`, `SubprocessSanitizedRunner`), scenario orchestrators, and baseline comparison harnesses.
   - **Boundary Invariant**: Isolated execution environments for untrusted candidate code. Candidate test oracles must be tamper-resistant against in-memory monkeypatching.

3. **Normative Catalogs and Schemas (`controls/`, `profiles/`, `schemas/`)**:
   - Contains declarative controls (`catalog.json`), assurance profiles (AL1–AL4), JSON schemas, and standards crosswalk mappings.

4. **Integration Adapters (`adapters/`)**:
   - Contains IDE and CLI integration assets (e.g. Google Antigravity IDE rules, skills, and subagents).

## 3. System Invariants

- **INV-01 (Zero External Runtime Dependencies)**: Core tools (`tools/`) must run on any Python 3.9+ environment without requiring `pip install` of third-party libraries.
- **INV-02 (Fail-Closed Assurance)**: In the presence of missing evidence, network unavailability, or unverified claims, tools must fail closed rather than approving unverified states.
- **INV-03 (Tamper-Resistant Oracles)**: Execution runners must detect and reject any runtime alteration of test assertion machinery by evaluated candidate code.
- **INV-04 (Evidence Existence Verification)**: Self-assessments claiming `PASS` must reference verifiable, physically existing artifacts on disk.

## 4. Architecture Decision Records (ADR Index)

- **ADR-001: Pure Standard Library for Runtime Tools**: Chosen to prevent supply chain attack vectors and ensure instant deployment across air-gapped CI/CD environments.
- **ADR-002: Dual Execution Runners (Docker + Sanitized Host Subprocess)**: Containers are preferred for strong isolation; host subprocess execution provides a fallback with secret stripping and process-tree termination.
- **ADR-003: Model Context Protocol (MCP) Integration**: AuraCode exposes assurance tools via stdio-based MCP servers (`tools/assurance_mcp.py`) to interface seamlessly with AI agents and IDEs.

## 5. Scale Assumptions and Limits

- AST architectural linter operates efficiently on repositories with up to 100,000 lines of code within standard CI timeouts (< 10 seconds).
- Diff linter limits maximum single-turn churn to configurable thresholds (default 300 lines) to prevent unreviewable large-scale halluncinated modifications.
