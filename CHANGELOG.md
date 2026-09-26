# Changelog

## 0.3.0 — 2026-09-26

Strategic Enhancement Release — Graduated SDD profiles, AST mutation testing, non-technical TUI briefing wizard, polyglot static scanning, and adversarial agentic debate:

### Added
- **Graduated SDD Profiles (`templates/sdd/` & `auracode init --profile <name>`):**
  - Introduced 4 graduated specification profiles tailored to project scale and assurance level:
    - `micro` (AL1): Single-document task spec (`01_task_spec.md`) for quick scripts and surgical fixes.
    - `lite` (AL2): 3 core blueprints (Vision & Rules, Architecture & Data, Tests & Acceptance) for MVPs and idea validation.
    - `standard` / `basic` (AL3): 7 core architectural blueprints for production web and backend systems.
    - `enterprise` (AL4): 15 comprehensive blueprints for mission-critical, regulated, and high-scale systems.
  - Supported via `auracode init --profile {micro,lite,standard,basic,enterprise}`.
- **AST Mutation Engine (`tools/mutation_engine.py` & `auracode tests --mutate`):**
  - Lightweight syntax mutation testing to detect vitiated test oracles and tautological assertions (`assert True`).
  - AST mutators invert relational comparisons (`==` to `!=`, `<` to `>=`), arithmetic operators (`+` to `-`), boolean constants (`True` to `False`), and nullify return statements (`return expr` to `return None`).
  - Safe in-place file mutation with guaranteed `try/finally` restoration and timeout handling.
- **Interactive Terminal Briefing Wizard (`tools/wizard.py` & `auracode wizard` / `interview`):**
  - Non-technical, zero-jargon interactive TUI guiding lay users through 5 structured briefing stages.
  - Translates technical decisions into physical world analogies (smart filing cabinets, storefronts, ID badges).
  - Automatically initializes appropriate SDD blueprints and computes the Gate G1 requirement clarity score directly from the terminal.
- **Polyglot Multi-Language Scanner (`tools/multilang_runner.py` & `auracode multilang`):**
  - Unified syntax inspection for Python, TypeScript, JavaScript, Go, Java, and C# codebases.
  - Catches empty exception handling / swallowed errors, unclosed stream/file leaks, and unsafe code execution across all supported languages without requiring language-specific compilation dependencies.
  - Ingests and outputs findings in standard SARIF v2.1.0 and JSON formats.
- **Adversarial Agentic Debate with Containment (`tools/adversarial_debate.py`, `auracode debate`, `.agents/skills/auracode-debate`, `.agents/skills/auracode-adversary`):**
  - Safe 3-phase structured debate protocol preventing LLM sycophancy without context explosion.
  - Phase 1 (Builder / Proponent) proposes architecture $\rightarrow$ Phase 2 (Adversary Red-Team) challenges security/scale risks $\rightarrow$ Phase 3 (Lay-User Clarifier) translates findings into everyday physical analogies and structured choices for human decision.
- **CLI and Test Suite Growth:**
  - Expanded CLI to 20 native commands.
  - Expanded unit test suite from 124 to 144 passing tests (100% pass rate).
  - 15 active agent skills registered in `.agents/skills/`.

## 0.2.0 — 2026-09-26

V2.0 Modernization Release — Comprehensive agentic containment, physical isolation, enterprise specifications, hermetic DevContainers, and Ralph Architecture autonomous execution based on the engineering manual *Engenharia de Software com Agentes Inteligentes*:

### Added
- **Aura Guard (`auracode guard` / `tools/pre_tool_guard.py` & `.agents/hooks.json`):**
  - Active real-time pre-tool and post-tool execution hooks.
  - Fail-closed security rules blocking destructive OS commands (`rm -rf /`, `rmdir /s /q`, disk wipes, destructive git resets).
  - Data exfiltration barrier blocking commands targeting environment variables, private keys (`id_rsa`), and credentials sent via `curl`, `wget`, or netcat.
  - CLI commands `auracode guard check` and `auracode guard install`.
- **Aura Worktree (`auracode worktree` / `tools/manage_worktree.py`):**
  - Physical Git worktree directory isolation (`.auracode/worktrees/<task>`).
  - Ensures autonomous agent sessions never dirty or corrupt the developer's working directory or active branch.
  - Lifecycle management: `create`, `list`, `merge`, and `clean`.
- **SDD Enterprise Profile (`templates/sdd/enterprise/` & `auracode init --profile enterprise`):**
  - Expanded specification suite from 7 basic blueprints to 15 modular enterprise blueprints.
  - New cadernos: Observability & Telemetry, Compliance & Privacy (LGPD/GDPR), Disaster Recovery & Resilience, STRIDE Threat Modeling, Horizontal Scalability & Caching, External Partner Integrations, Database Migration Strategy, and Blue/Green Rollout.
  - Baseline 7 blueprints preserved in `templates/sdd/basic/` under `--profile basic`.
- **Aura Cage (`auracode cage` / `tools/manage_cage.py` & `templates/cage/`):**
  - Hermetic DevContainer sandbox with strict **Default-Deny** network firewall via `iptables`.
  - Blocks all unauthorized outbound connections to neutralize indirect prompt injection data exfiltration attacks in autonomous/YOLO agent modes.
  - Whitelist mechanism via `allowed-domains.txt` with automated container config generation and verification.
- **Aura Loop (`auracode loop` / `tools/loop_runner.py`):**
  - Stateless autonomous runner implementing Geoffrey Huntley's Ralph Architecture.
  - Anti-Dumb-Zone: fresh execution contexts prevent degradation in long context windows (>100k tokens).
  - Anti-Reward-Hacking: enforces 5 deterministic assurance verification levels per turn (Compilation, AST Linters, Unit Tests, Semantic Asserts, Security Checks).
  - Circuit Breaker: automatic emergency halt upon 3 consecutive failures.
- **Unified CLI Expansion:**
  - Expanded `auracode` CLI from 12 to 17 unified commands: `init`, `arch`, `deps`, `diff`, `ambiguity`, `slop`, `leaks`, `types`, `tests`, `sec`, `sarif`, `assess`, `mcp`, `guard`, `worktree`, `cage`, `loop`.
- **Comprehensive Test Suite Expansion:**
  - Expanded from 92 to 124 passing unit tests covering all new components.
  - Zero AST violations across all 7 syntax linters.
- **Book Synthesis Reference:**
  - Published comprehensive 113 KB treatise: `RESUMO_ENGENHARIA_SOFTWARE_AGENTES_INTELIGENTES.md`.
- **Master Certification Report:**
  - Published `framework_audit/audit_8_v2_modernization_certification_report.md`.

## 0.1.1-draft — 2026-09-09

Antigravity-current compatibility correction:
- removed operational dependence on historical `Planning Mode/Fast Mode` labels in the IDE adapter;
- added explicit model + reasoning/thinking variant controls;
- separated IDE and CLI execution surfaces;
- added Antigravity documentation-drift record;
- expanded preregistration/result schema/harness metadata for model effort and IDE settings;
- added current Portuguese P1 step-by-step guide;
- added validator checks preventing obsolete IDE-mode terminology from re-entering operational Antigravity files.

## 0.1.0-draft — 2026-09-09

Initial public-draft structure:
- assurance-case control model;
- AL1–AL4 profiles;
- lifecycle gates;
- AI/agent-specific controls;
- empirical failure-mode mapping;
- standards crosswalk;
- validator and assessment CLI;
- Antigravity adapter;
- open-source governance templates.
