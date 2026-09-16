# Control Domains

## INT — Human Intent & Requirements
6 controls.

- **INT-01** — Human authority over material requirements (minimum AL1)
- **INT-02** — Traceable requirements (minimum AL1)
- **INT-03** — Ambiguity gate (minimum AL1)
- **INT-04** — Observable acceptance criteria (minimum AL1)
- **INT-05** — Non-functional requirements (minimum AL2)
- **INT-06** — Change-impact analysis (minimum AL2)

## ARC — Architecture & Evolution
6 controls.

- **ARC-01** — Architecture as a maintained system-of-record (minimum AL1)
- **ARC-02** — Explicit boundaries and dependency direction (minimum AL2)
- **ARC-03** — Architecture Decision Records (minimum AL2)
- **ARC-04** — System invariants (minimum AL2)
- **ARC-05** — Architecture fitness and erosion checks (minimum AL3)
- **ARC-06** — Scale assumptions and limits (minimum AL2)

## AGT — AI/Agent Governance
8 controls.

- **AGT-01** — AI output is untrusted until verified (minimum AL1)
- **AGT-02** — No sole self-approval (minimum AL2)
- **AGT-03** — Least agency and least privilege (minimum AL1)
- **AGT-04** — Instruction hierarchy and untrusted context (minimum AL1)
- **AGT-05** — Protected evaluator and oracle (minimum AL2)
- **AGT-06** — Agent action audit trail (minimum AL2)
- **AGT-07** — Bounded autonomy, loops and termination (minimum AL2)
- **AGT-08** — Secret isolation from model context (minimum AL2)

## SEC — Security Engineering
8 controls.

- **SEC-01** — Threat modeling before high-risk implementation (minimum AL2)
- **SEC-02** — Authentication and object/action authorization (minimum AL2)
- **SEC-03** — Validation at trust boundaries (minimum AL1)
- **SEC-04** — Safe interpreters, queries, commands and paths (minimum AL1)
- **SEC-05** — Secrets and cryptography (minimum AL2)
- **SEC-06** — Safe failures and security logging (minimum AL2)
- **SEC-07** — Adversarial and negative security tests (minimum AL2)
- **SEC-08** — Security findings block by policy (minimum AL2)

## VER — Verification & Test Integrity
9 controls.

- **VER-01** — Tests derived from acceptance criteria (minimum AL1)
- **VER-02** — Independent oracle principle (minimum AL2)
- **VER-03** — Layered test strategy (minimum AL2)
- **VER-04** — Regression protection (minimum AL1)
- **VER-05** — Mutation or equivalent test-strength evidence (minimum AL3)
- **VER-06** — Property, fuzz or generative boundary testing (minimum AL3)
- **VER-07** — Held-out or protected tests (minimum AL3)
- **VER-08** — Test/evaluator tamper detection (minimum AL2)
- **VER-09** — Critical invariant verification (minimum AL4)

## SUP — Software Supply Chain
6 controls.

- **SUP-01** — Dependency existence and source verification (minimum AL1)
- **SUP-02** — Reproducible dependency resolution (minimum AL2)
- **SUP-03** — Dependency vulnerability and license review (minimum AL2)
- **SUP-04** — Software Bill of Materials (minimum AL2)
- **SUP-05** — Build provenance (minimum AL3)
- **SUP-06** — CI/CD dependency and permission hardening (minimum AL2)

## DAT — Data & Persistence
5 controls.

- **DAT-01** — Data classification and minimization (minimum AL2)
- **DAT-02** — Schema integrity and transactional correctness (minimum AL2)
- **DAT-03** — Migration and rollback safety (minimum AL2)
- **DAT-04** — Backup restore evidence (minimum AL3)
- **DAT-05** — Tenant isolation and retention enforcement (minimum AL3)

## REL — Reliability & Scale
6 controls.

- **REL-01** — SLIs, SLOs and error budgets (minimum AL2)
- **REL-02** — Timeout, retry, backoff and idempotency (minimum AL2)
- **REL-03** — Concurrency correctness (minimum AL2)
- **REL-04** — Load and capacity validation (minimum AL2)
- **REL-05** — Soak and software-aging tests (minimum AL3)
- **REL-06** — Resilience and cascading-failure controls (minimum AL3)

## RLS — Release Engineering
5 controls.

- **RLS-01** — Automated release quality gates (minimum AL2)
- **RLS-02** — Immutable, identifiable release artifacts (minimum AL2)
- **RLS-03** — Staged rollout (minimum AL3)
- **RLS-04** — Tested rollback or forward recovery (minimum AL2)
- **RLS-05** — Release approval separation (minimum AL3)

## OPS — Production Operations
6 controls.

- **OPS-01** — Golden-signal monitoring (minimum AL2)
- **OPS-02** — Structured logs, tracing and correlation (minimum AL2)
- **OPS-03** — Actionable alerting and runbooks (minimum AL2)
- **OPS-04** — Incident learning and recurrence prevention (minimum AL2)
- **OPS-05** — Disaster recovery objectives and exercises (minimum AL3)
- **OPS-06** — Production feedback closes the assurance loop (minimum AL2)

## GOV — Governance & Assurance
10 controls.

- **GOV-01** — Risk and assurance-level classification (minimum AL1)
- **GOV-02** — Time-bounded waivers (minimum AL2)
- **GOV-03** — Evidence package before release (minimum AL2)
- **GOV-04** — Model, agent, tool and environment provenance (minimum AL2)
- **GOV-05** — Technical-debt and architecture trend (minimum AL2)
- **GOV-06** — Standards and threat-model maintenance (minimum AL2)
- **GOV-07** — Accountable human ownership (minimum AL2)
- **GOV-08** — Independent assessment for higher assurance (minimum AL3)
- **GOV-09** — Authoritative repository access and branch protection (minimum AL2)
- **GOV-10** — Coordinated vulnerability reporting and response (minimum AL2)
