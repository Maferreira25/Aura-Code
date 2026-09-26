# Roadmap

## 0.1 — Research-backed draft (Completed)
- normative control catalog;
- assurance levels (AL1–AL4);
- failure-mode mapping;
- machine validator;
- Antigravity adapter;
- high-level standards crosswalk.

## 0.2 — Enterprise Modernization & Agentic Containment (Completed)
- Aura Guard: real-time pre/post-tool safety hooks (`.agents/hooks.json` & `pre_tool_guard.py`);
- Aura Worktree: physical Git directory isolation (`manage_worktree.py`);
- SDD Enterprise Profile: 15 modular specifications (`templates/sdd/enterprise/`);
- Aura Cage: DevContainers with Default-Deny outbound firewall (`manage_cage.py`);
- Aura Loop: Ralph Architecture autonomous runner with 5-level AST verification gates (`loop_runner.py`);
- 17 unified CLI commands (`auracode <command>`);
- 124 passing unit tests (100% pass rate).

## 0.3 — Tool & Language Profiles (In Progress)
- Python/web (FastAPI, Django, Flask);
- TypeScript/Node & Next.js AST linters;
- JVM (Java/Kotlin);
- Go/Rust assurance profiles;
- Cloud & Infrastructure-as-Code (Terraform, Pulumi, Kubernetes).

## 0.4 — Continuous Assurance Automation (Completed / Evolving)
- Evidence manifest synchronization (`tools/update_manifest.py`);
- GitHub Actions CI/CD workflows (`.github/workflows/`);
- OASIS SARIF v2.1.0 report ingestion and export;
- Anti-reward-hacking and non-vacuous assertion validation (`auracode tests`);
- Surgical diff bounds checking (`auracode diff`).

## 0.5 — Long-horizon Empirical Validation
- Repeated multi-agent feature-evolution benchmark;
- Architecture erosion and drift tracking;
- Autonomous soak testing with sustained loops;
- Red-teaming indirect prompt injection vectors inside DevContainers.

## 1.0 Enterprise Candidate
Requires:
- Completed empirical multi-repository validation protocol;
- Independent external assessor certification;
- Multi-language AST verification engines (Python + TypeScript);
- Zero open critical/high vulnerabilities;
- Formally audited threat model and supply chain hardening.
