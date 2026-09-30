# AuraCode Architecture Specification

## 1. System Overview and Scope

AuraCode is an open-source software assurance framework designed to enforce governance, architectural boundaries, active agent containment, physical workspace isolation, and empirical evaluation for AI-generated codebases.

## 2. Architectural Layers and Boundaries

As specified normatively in `contracts.json`, AuraCode maintains strict separation between runtime governance tools, containment engines, and evaluation harnesses:

1. **Governance & Containment Tools Layer (`tools/`)**:
   - Contains active linters, assessment engines, dependency verifiers, MCP servers, and active agent containment tools:
     - `pre_tool_guard.py` (`auracode guard`): Fail-closed Pre/PostToolUse hooks intercepting OS and shell actions.
     - `manage_worktree.py` (`auracode worktree`): Physical Git worktree directory isolation.
     - `manage_cage.py` (`auracode cage`): DevContainer sandboxing with Default-Deny iptables firewall.
     - `loop_runner.py` (`auracode loop`): Ralph Architecture autonomous loop runner with 5-level AST verification gates.
   - **Boundary Invariant**: Pure Python standard library only (zero external runtime dependencies).
   - **Forbidden Imports**: `requests`, `httpx`, web frameworks, or internal validation scenarios.

2. **Validation and Evaluation Harness Layer (`validation/tools/`)**:
   - Contains test runners (`DockerRunner`, `SubprocessSanitizedRunner`), scenario orchestrators, and baseline comparison harnesses.
   - **Boundary Invariant**: Isolated execution environments for untrusted candidate code. Candidate test oracles must be tamper-resistant against in-memory monkeypatching.

3. **Normative Catalogs and Schemas (`controls/`, `profiles/`, `schemas/`)**:
   - Contains declarative controls (`catalog.json`), assurance profiles (AL1–AL4), JSON schemas, and standards crosswalk mappings.

4. **Specification Templates Layer (`templates/`)**:
   - `templates/sdd/basic/`: 7 foundational SDD blueprints for lightweight and MVP systems.
   - `templates/sdd/enterprise/`: 15 modular enterprise SDD blueprints covering observability, DR, compliance, STRIDE threat models, caching, and migrations.
   - `templates/cage/`: DevContainer Dockerfile, allowed domains, and firewall bootstrap scripts.

5. **Integration Adapters (`adapters/` & `.agents/`)**:
   - Contains IDE and CLI integration assets (e.g. Google Antigravity IDE rules, skills, hooks in `.agents/hooks.json`, and subagents).

## 3. System Invariants

- **INV-01 (Zero External Runtime Dependencies)**: Core tools (`tools/`) must run on any Python 3.9+ environment without requiring `pip install` of third-party libraries.
- **INV-02 (Fail-Closed Assurance)**: In the presence of missing evidence, network unavailability, or unverified claims, tools must fail closed rather than approving unverified states.
- **INV-03 (Tamper-Resistant Oracles)**: Execution runners must detect and reject any runtime alteration of test assertion machinery by evaluated candidate code.
- **INV-04 (Evidence Existence Verification)**: Self-assessments claiming `PASS` must reference verifiable, physically existing artifacts on disk.
- **INV-05 (Fail-Closed Tool Guardrail)**: Tool execution hooks must block destructive shell commands (`rm -rf /`, format, destructive git wipes) and token/credential exfiltration patterns before system dispatch.
- **INV-06 (Worktree Directory Isolation)**: Agent file operations must reside inside designated physical git worktrees (`.auracode/worktrees/<task>`), never dirtying the primary user branch.
- **INV-07 (Default-Deny Container Network Isolation)**: Autonomous execution environments (Aura Cage) must block all outbound traffic by default, whitelisting only verified repositories and registries.
- **INV-08 (Stateless Loop Context)**: Multi-turn autonomous runners must reset conversational context each turn to eliminate cognitive degradation (>100k token Dumb Zone).

## 4. Architecture Decision Records (ADR Index)

- **ADR-001: Pure Standard Library for Runtime Tools**: Chosen to prevent supply chain attack vectors and ensure instant deployment across air-gapped CI/CD environments.
- **ADR-002: Dual Execution Runners (Docker + Sanitized Host Subprocess)**: Containers are preferred for strong isolation; host subprocess execution provides a fallback with secret stripping and process-tree termination.
- **ADR-003: Model Context Protocol (MCP) Integration**: AuraCode exposes assurance tools via stdio-based MCP servers (`tools/assurance_mcp.py`) to interface seamlessly with AI agents and IDEs.
- **ADR-004: PreTool/PostTool Execution Hooks (Aura Guard)**: Intercepts tools via `.agents/hooks.json` to enforce fail-closed containment before the host operating system executes shell actions.
- **ADR-005: Physical Git Worktree Directory Isolation (Aura Worktree)**: Uses `git worktree` to provide separate physical workspaces per agent task, preventing active-branch corruption.
- **ADR-006: Hermetic DevContainers with Default-Deny Firewall (Aura Cage)**: Deploys Linux DevContainers with iptables blocking all outbound traffic except explicitly listed domains, neutralizing prompt injection data exfiltration.
- **ADR-007: Ralph Architecture Autonomous Loop Runner (Aura Loop)**: Implements stateless single-turn iterations with 5-level AST verification gates, anti-reward-hacking controls, and circuit breakers.

## 5. Scale Assumptions and Limits

- AST architectural linter operates efficiently on repositories with up to 100,000 lines of code within standard CI timeouts (< 10 seconds).
- Diff linter limits maximum single-turn churn to configurable thresholds (default 500 lines) to prevent unreviewable large-scale hallucinated modifications.


## 6. Assurance State and Decision Engine

AuraCode now includes a persistent fail-closed assurance state and decision layer.

The normative control catalog and AL1-AL4 profiles remain the source of applicable requirements. The Decision Engine consumes those controls through controls/gates.json and determines whether a lifecycle transition may advance.

Core components:
- tools/assurance_state.py — state and decision core;
- tools/assurance_state_cli.py — CLI adapter;
- schemas/assurance-state.schema.json — persisted-state contract;
- tools/continuous_assurance.py — cross-revision drift/regression detection;
- tools/dogfood_assurance.py — framework dogfooding;
- docs/ASSURANCE-STATE.md — full design specification.

The engine uses PASS, FAIL, UNKNOWN, NOT_APPLICABLE and WAIVED as explicit control states. UNKNOWN is not treated as success.

Independent verification is enforced through actor provenance. Where required by the assurance profile, implementer and verifier/auditor cannot be the same actor or prohibited same session. For AL3/AL4 AI-to-AI verification, the current policy also requires distinct model identities.

Remediation and revalidation are deliberately separated. A remediation can reach IMPLEMENTED, but only an independent revalidator can move the finding to RESOLVED.

The stable-1.0 maturity gate is separate from lifecycle assurance. It governs whether AuraCode itself has enough empirical/governance evidence to make a stable-release maturity claim; it does not replace the lifecycle Decision Engine.
