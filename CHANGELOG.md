# Changelog

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
