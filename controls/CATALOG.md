# Normative Control Catalog

Framework version: `0.1.1-draft`.

The machine-readable source of truth is `catalog.json`. This Markdown file is a human-readable projection.

A control is mandatory when its assurance level and applicability make it applicable. `NA` requires rationale.

## INT — Human Intent & Requirements

### INT-01 — Human authority over material requirements
**Minimum assurance:** `AL1`

**Requirement:** Material product, behavior, data, security, permission, compatibility, cost or irreversible decisions MUST be made or explicitly delegated by an accountable human.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Requirement/decision record identifying human decision or explicit delegation.

**Verification:**
- Review change against decision record.

**Blocking conditions:**
- A material requirement was invented or silently selected by the implementing agent.

**References:** `ISO-25010-2023`, `NIST-SSDF-1.1`

### INT-02 — Traceable requirements
**Minimum assurance:** `AL1`

**Requirement:** Each non-trivial change MUST trace from a stated requirement to implementation and verification evidence.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Requirement ID or issue; linked acceptance evidence.

**Verification:**
- Trace sample from requirement to code/test/evidence.

**Blocking conditions:**
- No identifiable requirement or no link to verification.

**References:** `NIST-SSDF-1.1`, `ISO-25010-2023`

### INT-03 — Ambiguity gate
**Minimum assurance:** `AL1`

**Requirement:** Unresolved ambiguities that can materially alter outcomes MUST be resolved before the affected implementation proceeds; discoverable facts SHOULD be investigated before questioning the user.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Clarification record for blocking ambiguity, or documented rationale that no material ambiguity remains.

**Verification:**
- Review implementation assumptions against requirements and repository facts.

**Blocking conditions:**
- Material ambiguity remains unresolved.

**References:** `NIST-SSDF-1.1`

### INT-04 — Observable acceptance criteria
**Minimum assurance:** `AL1`

**Requirement:** Non-trivial requirements MUST have observable, testable acceptance criteria before completion is claimed.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Acceptance criteria linked to tests or other evidence.

**Verification:**
- Check each criterion has a verification method and result.

**Blocking conditions:**
- A material criterion has no verification evidence.

**References:** `ISO-25010-2023`, `METR-MERGEABILITY`

### INT-05 — Non-functional requirements
**Minimum assurance:** `AL2`

**Requirement:** Relevant quality attributes such as security, reliability, performance, scalability, accessibility, privacy, maintainability and operability MUST be explicitly considered and material targets documented.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- NFR record or explicit N/A rationale per relevant attribute.

**Verification:**
- Review NFRs against product context and risk classification.

**Blocking conditions:**
- A material quality attribute is omitted without rationale.

**References:** `ISO-25010-2023`, `GOOGLE-SRE`

### INT-06 — Change-impact analysis
**Minimum assurance:** `AL2`

**Requirement:** Significant changes MUST identify affected contracts, data, dependencies, users, security boundaries, operations and rollback implications before implementation.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Change-impact record.

**Verification:**
- Review impact analysis against dependency graph/diff.

**Blocking conditions:**
- High-impact dependency or data effect is omitted.

**References:** `NIST-SSDF-1.1`, `SLOPCODEBENCH`

## ARC — Architecture & Evolution

### ARC-01 — Architecture as a maintained system-of-record
**Minimum assurance:** `AL1`

**Requirement:** The repository MUST contain a concise description of the architecture actually implemented, not only the intended architecture.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Architecture document with components, responsibilities and external boundaries.

**Verification:**
- Compare documented components to repository structure.

**Blocking conditions:**
- Architecture document is absent for a non-trivial system or materially stale.

**References:** `ISO-25010-2023`, `SLOPCODEBENCH`

### ARC-02 — Explicit boundaries and dependency direction
**Minimum assurance:** `AL2`

**Requirement:** Critical architectural boundaries and allowed dependency directions MUST be explicit and SHOULD be mechanically enforceable where practical.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Boundary/dependency rules; optional architecture tests.

**Verification:**
- Dependency analysis or architecture fitness test.

**Blocking conditions:**
- A change creates prohibited cross-boundary dependency.

**References:** `SLOPCODEBENCH`, `AI-TECH-DEBT`

### ARC-03 — Architecture Decision Records
**Minimum assurance:** `AL2`

**Requirement:** Material, long-lived architectural decisions and trade-offs MUST be recorded as ADRs or equivalent.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- ADR containing context, alternatives, decision and consequences.

**Verification:**
- Review significant architecture changes for ADR coverage.

**Blocking conditions:**
- Material architecture change lacks a decision record.

**References:** `ISO-25010-2023`, `SLOPCODEBENCH`

### ARC-04 — System invariants
**Minimum assurance:** `AL2`

**Requirement:** Critical properties that must remain true across future changes MUST be recorded as invariants and linked to verification where feasible.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Invariant records; linked tests/checks.

**Verification:**
- Verify changed components against touched invariants.

**Blocking conditions:**
- A touched critical invariant has no validation.

**References:** `SLOPCODEBENCH`, `BAXBENCH`

### ARC-05 — Architecture fitness and erosion checks
**Minimum assurance:** `AL3`

**Requirement:** Projects with sustained evolution MUST measure architecture erosion indicators appropriate to the stack, such as dependency violations, complexity concentration, duplication or cyclic coupling.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Fitness checks or trend report.

**Verification:**
- Compare current metrics to baseline/thresholds.

**Blocking conditions:**
- New critical boundary violation; unexplained material erosion beyond project threshold.

**References:** `SLOPCODEBENCH`, `AI-TECH-DEBT`

### ARC-06 — Scale assumptions and limits
**Minimum assurance:** `AL2`

**Requirement:** Architecture decisions that depend on load, data volume, geography or concurrency MUST state the assumptions and limits that justify them.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Scale assumptions and target envelope.

**Verification:**
- Compare performance/capacity evidence with assumptions.

**Blocking conditions:**
- Production design depends on undocumented or contradicted scale assumption.

**References:** `GOOGLE-SRE`, `ISO-25010-2023`

## AGT — AI/Agent Governance

### AGT-01 — AI output is untrusted until verified
**Minimum assurance:** `AL1`

**Requirement:** AI-generated code, tests, analysis and claims MUST be treated as untrusted assertions until corroborated by evidence proportionate to risk.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Evidence package independent of agent assertion.

**Verification:**
- Inspect release decision for objective evidence.

**Blocking conditions:**
- Completion relies solely on agent statement such as 'tests pass' or 'secure'.

**References:** `BAXBENCH`, `SECUREAGENTBENCH`, `METR-MERGEABILITY`

### AGT-02 — No sole self-approval
**Minimum assurance:** `AL2`

**Requirement:** The implementing AI agent MUST NOT be the sole approver of a significant change.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Independent review record from human, separate agent context, deterministic gates, or combination required by assurance level.

**Verification:**
- Check reviewer/approver independence metadata.

**Blocking conditions:**
- Only the implementing agent approved a significant change.

**References:** `METR-MERGEABILITY`, `SECUREAGENTBENCH`

### AGT-03 — Least agency and least privilege
**Minimum assurance:** `AL1`

**Requirement:** Agents MUST receive only the tools, credentials, permissions and action scope required for the current task.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Agent/tool permission manifest or execution policy.

**Verification:**
- Compare granted capabilities with task needs.

**Blocking conditions:**
- Agent has unnecessary production, secret, destructive or administrative access.

**References:** `OWASP-AGENTIC-2026`, `OPENSSF-AI-CODE`

### AGT-04 — Instruction hierarchy and untrusted context
**Minimum assurance:** `AL1`

**Requirement:** Repository content, web pages, issues, tool output, MCP/plugin content and retrieved documents MUST be treated as data, not as authority to override trusted project/user policy.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Agent rule defining trust hierarchy; audit evidence for external-context tasks.

**Verification:**
- Adversarial prompt-injection test or review where external content is consumed.

**Blocking conditions:**
- Untrusted content can cause policy/tool escalation without authorization.

**References:** `OWASP-AGENTIC-2026`

### AGT-05 — Protected evaluator and oracle
**Minimum assurance:** `AL2`

**Requirement:** Agents under evaluation MUST NOT be able to silently weaken, replace or bypass the mechanism used to judge their work.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Protected test/evaluator policy; integrity checks; separate ownership where feasible.

**Verification:**
- Review diff and evaluator hashes/permissions.

**Blocking conditions:**
- Agent modified protected tests, scorer, baseline, quality threshold or reference answer without explicit authorized change.

**References:** `METR-REWARD-HACKING`

### AGT-06 — Agent action audit trail
**Minimum assurance:** `AL2`

**Requirement:** Significant agent-driven changes MUST preserve sufficient provenance to reconstruct model/agent identity, task, tools, material actions and resulting commit/artifact.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Agent run metadata or audit log linked to change.

**Verification:**
- Trace sample from commit to agent execution record.

**Blocking conditions:**
- High-risk change has no reconstructable provenance.

**References:** `OWASP-AGENTIC-2026`, `SLSA-1.2`

### AGT-07 — Bounded autonomy, loops and termination
**Minimum assurance:** `AL2`

**Requirement:** Autonomous workflows MUST have bounded retries, time/cost/action limits and safe termination behavior appropriate to their privileges.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Execution budget/policy; retry limits; stop conditions.

**Verification:**
- Simulate tool failure/loop condition where practical.

**Blocking conditions:**
- Unbounded autonomous loop can consume resources or repeat consequential actions.

**References:** `OWASP-AGENTIC-2026`, `GOOGLE-SRE`

### AGT-08 — Secret isolation from model context
**Minimum assurance:** `AL2`

**Requirement:** Long-lived or high-value secrets MUST NOT be placed in prompts/model context when a scoped credential or brokered action can satisfy the task.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Secret-management design and scoped credential policy.

**Verification:**
- Secret scan and agent-context review.

**Blocking conditions:**
- Long-lived production secret is exposed unnecessarily to model context or logs.

**References:** `OWASP-AGENTIC-2026`, `OPENSSF-AI-CODE`

## SEC — Security Engineering

### SEC-01 — Threat modeling before high-risk implementation
**Minimum assurance:** `AL2`

**Requirement:** Security-sensitive or internet-exposed features MUST identify assets, actors, trust boundaries, abuse cases and mitigations before release.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Threat model linked to feature/system.

**Verification:**
- Review threat model against data flows and changed surfaces.

**Blocking conditions:**
- Material trust boundary or abuse case is unassessed.

**References:** `CISA-SBD`, `NIST-SSDF-1.1`, `OWASP-TOP10-2025`

### SEC-02 — Authentication and object/action authorization
**Minimum assurance:** `AL2`

**Requirement:** Protected operations MUST verify both identity and authorization for the requested action/object; authorization MUST default to deny when uncertain.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Authorization design; positive and negative access tests.

**Verification:**
- Test cross-user/cross-role access attempts.

**Blocking conditions:**
- Unauthorized actor can access or mutate protected resource.

**References:** `OWASP-ASVS-5`, `OWASP-TOP10-2025`

### SEC-03 — Validation at trust boundaries
**Minimum assurance:** `AL1`

**Requirement:** External input MUST be validated for expected type, format, range, size and semantics as appropriate; output encoding/sanitization MUST be context appropriate.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Validation code and negative tests.

**Verification:**
- Boundary tests and security scan.

**Blocking conditions:**
- Untrusted input reaches sensitive sink without appropriate validation/encoding.

**References:** `OWASP-ASVS-5`, `OWASP-TOP10-2025`

### SEC-04 — Safe interpreters, queries, commands and paths
**Minimum assurance:** `AL1`

**Requirement:** Code MUST use safe parameterization and constrained APIs for database queries, OS commands, templates and file paths; dynamic execution MUST be avoided or strongly isolated.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Implementation evidence; injection/path tests.

**Verification:**
- SAST plus targeted negative tests.

**Blocking conditions:**
- Known injection/path traversal class remains reachable.

**References:** `OWASP-ASVS-5`, `OWASP-TOP10-2025`, `OPENSSF-AI-CODE`

### SEC-05 — Secrets and cryptography
**Minimum assurance:** `AL2`

**Requirement:** Secrets MUST be externally managed and never hardcoded; cryptography MUST use maintained platform/library primitives rather than custom cryptographic constructions.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Secret scan; secret-store configuration; crypto design where relevant.

**Verification:**
- Secret scanning and dependency/API review.

**Blocking conditions:**
- Hardcoded credential/private key; custom/unapproved crypto protecting material assets.

**References:** `OWASP-TOP10-2025`, `OWASP-ASVS-5`, `OPENSSF-AI-CODE`

### SEC-06 — Safe failures and security logging
**Minimum assurance:** `AL2`

**Requirement:** Exceptional conditions MUST preserve secure state, avoid sensitive disclosure, produce actionable logs, and fail closed for security decisions unless explicitly justified.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Error-handling tests; logging specification.

**Verification:**
- Fault injection/negative tests; log review.

**Blocking conditions:**
- Exception bypasses authorization, corrupts state, leaks secret, or is silently swallowed in critical path.

**References:** `OWASP-TOP10-2025`, `OWASP-ASVS-5`

### SEC-07 — Adversarial and negative security tests
**Minimum assurance:** `AL2`

**Requirement:** Security controls MUST be tested for expected rejection/failure behavior, not only successful paths.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Negative/adversarial tests linked to threat model.

**Verification:**
- Execute representative abuse cases.

**Blocking conditions:**
- Critical security control has no negative verification.

**References:** `OWASP-ASVS-5`, `SECUREAGENTBENCH`, `BAXBENCH`

### SEC-08 — Security findings block by policy
**Minimum assurance:** `AL2`

**Requirement:** Known exploitable critical findings MUST block release; severity thresholds for other findings MUST be explicit, risk-based and waiver-controlled.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- SAST/SCA/DAST or equivalent reports as applicable; vulnerability policy.

**Verification:**
- Check finding status and waiver records.

**Blocking conditions:**
- Unwaived finding exceeds project blocking threshold.

**References:** `NIST-SSDF-1.1`, `OWASP-ASVS-5`

## VER — Verification & Test Integrity

### VER-01 — Tests derived from acceptance criteria
**Minimum assurance:** `AL1`

**Requirement:** Tests and other verification artifacts MUST trace to acceptance criteria rather than merely mirror the implementation.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Criteria-to-test mapping.

**Verification:**
- Sample tests for behavioral independence from code structure.

**Blocking conditions:**
- Material acceptance criterion has no verification.

**References:** `METR-MERGEABILITY`, `ISO-25010-2023`

### VER-02 — Independent oracle principle
**Minimum assurance:** `AL2`

**Requirement:** For significant changes, at least one material correctness oracle MUST be independent of the implementing agent's unsupported judgment.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Independent expected result, reference contract, human review, protected test, property, or deterministic analyzer.

**Verification:**
- Inspect evidence provenance.

**Blocking conditions:**
- All verification logic and expected results originate solely from the same implementation process with no independent oracle.

**References:** `BAXBENCH`, `METR-REWARD-HACKING`, `METR-MERGEABILITY`

### VER-03 — Layered test strategy
**Minimum assurance:** `AL2`

**Requirement:** Projects MUST apply unit, integration and end-to-end tests proportionately to the boundaries and risks actually changed.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Test plan and execution results.

**Verification:**
- Check changed boundaries have suitable test layer.

**Blocking conditions:**
- A changed critical integration boundary is covered only by isolated mocks.

**References:** `NIST-SSDF-1.1`, `BAXBENCH`

### VER-04 — Regression protection
**Minimum assurance:** `AL1`

**Requirement:** Bug fixes SHOULD include a regression test that demonstrates the prior failure and protects the corrected behavior when feasible.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Regression test or explicit infeasibility rationale.

**Verification:**
- Reproduce failure before fix when practical; run after fix.

**Blocking conditions:**
- High-impact recurring bug fixed without durable regression evidence and no rationale.

**References:** `NIST-SSDF-1.1`

### VER-05 — Mutation or equivalent test-strength evidence
**Minimum assurance:** `AL3`

**Requirement:** Critical business/security logic MUST use mutation testing or an equivalent method to demonstrate that tests detect meaningful behavioral faults.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Mutation report or documented equivalent fault-injection evidence.

**Verification:**
- Confirm threshold and surviving mutants disposition.

**Blocking conditions:**
- Critical logic test suite is demonstrably insensitive to material faults.

**References:** `METR-MERGEABILITY`

### VER-06 — Property, fuzz or generative boundary testing
**Minimum assurance:** `AL3`

**Requirement:** Parsers, protocol boundaries, validators and complex input spaces SHOULD use property-based, fuzz or equivalent generative testing proportional to attack surface.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Fuzz/property test config and results or N/A rationale.

**Verification:**
- Execute bounded campaign; triage crashes/invariants.

**Blocking conditions:**
- High-risk parser/input boundary lacks adversarial coverage without rationale.

**References:** `OWASP-ASVS-5`, `BAXBENCH`

### VER-07 — Held-out or protected tests
**Minimum assurance:** `AL3`

**Requirement:** High-assurance agent-generated changes MUST include evaluation cases unavailable for modification by the implementing agent when technically feasible.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Protected test location/ownership and results.

**Verification:**
- Verify implementer lacked write authority or test contents were held out.

**Blocking conditions:**
- High-risk autonomous change is judged only by tests the same agent could rewrite.

**References:** `METR-REWARD-HACKING`

### VER-08 — Test/evaluator tamper detection
**Minimum assurance:** `AL2`

**Requirement:** Changes to tests, golden files, snapshots, thresholds or evaluator logic MUST receive explicit review and MUST NOT be accepted merely because they make the implementation pass.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Diff review for evaluation artifacts; approval record.

**Verification:**
- Detect deleted/weakened assertions or threshold reductions.

**Blocking conditions:**
- Evaluation was weakened without documented requirement change.

**References:** `METR-REWARD-HACKING`

### VER-09 — Critical invariant verification
**Minimum assurance:** `AL4`

**Requirement:** For AL4 invariants whose failure could cause catastrophic or irreversible harm, stronger assurance techniques such as model checking, formal specification, independent implementation, or equivalent evidence SHOULD be evaluated and used when practical.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Critical-invariant assurance rationale and selected evidence.

**Verification:**
- Independent review of assurance method.

**Blocking conditions:**
- Critical invariant relies solely on ordinary happy-path tests without documented risk acceptance.

**References:** `ISO-25010-2023`

## SUP — Software Supply Chain

### SUP-01 — Dependency existence and source verification
**Minimum assurance:** `AL1`

**Requirement:** A newly introduced dependency MUST be verified to exist in the intended official ecosystem and to be the intended package before installation or merge.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Package registry/source verification record or lockfile provenance.

**Verification:**
- Verify package name, publisher/source and project linkage.

**Blocking conditions:**
- Dependency was installed solely from an AI suggestion without source verification.

**References:** `PACKAGE-HALLUCINATION-USENIX`, `OPENSSF-AI-CODE`

### SUP-02 — Reproducible dependency resolution
**Minimum assurance:** `AL2`

**Requirement:** Production dependencies MUST use lockfiles, exact immutable references, or an ecosystem-equivalent reproducible resolution mechanism.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Lockfile/immutable references.

**Verification:**
- Fresh resolution/build comparison.

**Blocking conditions:**
- Production build can silently resolve materially different dependency versions without policy.

**References:** `OPENSSF-AI-CODE`, `SLSA-1.2`

### SUP-03 — Dependency vulnerability and license review
**Minimum assurance:** `AL2`

**Requirement:** Direct and transitive dependencies MUST be scanned for known vulnerabilities and license/policy conflicts before release and continuously where practical.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- SCA report; license policy/result.

**Verification:**
- Check blocking findings and waivers.

**Blocking conditions:**
- Unwaived dependency finding exceeds blocking threshold.

**References:** `OWASP-TOP10-2025`, `NIST-SSDF-1.1`, `CYCLONEDX-1.7`

### SUP-04 — Software Bill of Materials
**Minimum assurance:** `AL2`

**Requirement:** Release artifacts SHOULD have a machine-readable SBOM; AL3+ release artifacts MUST have one unless technically inapplicable.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- CycloneDX/SPDX/equivalent SBOM linked to artifact.

**Verification:**
- Validate SBOM syntax and artifact/version linkage.

**Blocking conditions:**
- AL3+ release has no SBOM and no justified N/A.

**References:** `CYCLONEDX-1.7`, `SLSA-1.2`

### SUP-05 — Build provenance
**Minimum assurance:** `AL3`

**Requirement:** AL3+ release artifacts MUST have verifiable build provenance or an explicit migration plan toward an equivalent provenance guarantee.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- SLSA-compatible/equivalent provenance attestation.

**Verification:**
- Verify provenance authenticity and artifact digest where supported.

**Blocking conditions:**
- Release artifact cannot be traced to source/build inputs at required assurance level.

**References:** `SLSA-1.2`

### SUP-06 — CI/CD dependency and permission hardening
**Minimum assurance:** `AL2`

**Requirement:** CI/CD third-party actions/plugins MUST be version-controlled and SHOULD use immutable references for production-sensitive workflows; workflow permissions and secrets MUST follow least privilege.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Workflow configuration; action/plugin inventory.

**Verification:**
- Review references, permissions, secret exposure and pull-request trust boundaries.

**Blocking conditions:**
- Untrusted contribution can obtain write token/production secret; critical action reference is mutable without accepted rationale.

**References:** `OPENSSF-AI-CODE`, `SLSA-1.2`, `OWASP-TOP10-2025`

## DAT — Data & Persistence

### DAT-01 — Data classification and minimization
**Minimum assurance:** `AL2`

**Requirement:** Projects handling user, confidential or regulated data MUST classify material data, minimize collection/retention, and document access and lifecycle requirements.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Data inventory/classification; retention/access rules.

**Verification:**
- Review data flows and storage against classification.

**Blocking conditions:**
- Sensitive data has no ownership/access/retention rule.

**References:** `CISA-SBD`, `OWASP-ASVS-5`

### DAT-02 — Schema integrity and transactional correctness
**Minimum assurance:** `AL2`

**Requirement:** Persistent data models MUST enforce critical integrity constraints in the appropriate layer and use transactions/atomicity where partial updates would violate invariants.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Schema/constraint definitions; transactional tests.

**Verification:**
- Failure-injection test around multi-step writes.

**Blocking conditions:**
- Partial failure can leave critical data invariant violated.

**References:** `OWASP-ASVS-5`, `ISO-25010-2023`

### DAT-03 — Migration and rollback safety
**Minimum assurance:** `AL2`

**Requirement:** Schema/data migrations MUST be versioned, tested against representative existing data, and have rollback or forward-recovery strategy proportional to reversibility.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Migration scripts; migration test; recovery plan.

**Verification:**
- Dry-run/representative migration and compatibility checks.

**Blocking conditions:**
- Destructive migration has no approved recovery path.

**References:** `NIST-SSDF-1.1`, `GOOGLE-SRE`

### DAT-04 — Backup restore evidence
**Minimum assurance:** `AL3`

**Requirement:** Critical persistent data MUST have backups whose restoration is periodically tested; backup existence alone is not sufficient evidence of recoverability.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Backup policy; successful restore exercise record.

**Verification:**
- Restore to isolated environment and verify integrity.

**Blocking conditions:**
- Required restore test is stale/failed or recovery objectives cannot be met.

**References:** `GOOGLE-SRE`

### DAT-05 — Tenant isolation and retention enforcement
**Minimum assurance:** `AL3`

**Requirement:** Multi-tenant systems MUST verify tenant isolation at every data access boundary and enforce retention/deletion policy consistently.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Tenant-isolation tests; retention/deletion verification.

**Verification:**
- Cross-tenant adversarial tests.

**Blocking conditions:**
- Cross-tenant read/write is possible or retention rule is unenforced.

**References:** `OWASP-ASVS-5`, `OWASP-TOP10-2025`

## REL — Reliability & Scale

### REL-01 — SLIs, SLOs and error budgets
**Minimum assurance:** `AL2`

**Requirement:** Production services MUST define user-relevant reliability indicators and objectives; targets MUST be business/product decisions informed by engineering evidence.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- SLI/SLO document and measurement source.

**Verification:**
- Check metrics reflect user-visible success and error budget.

**Blocking conditions:**
- Production service has no measurable reliability target at AL2+.

**References:** `GOOGLE-SRE`

### REL-02 — Timeout, retry, backoff and idempotency
**Minimum assurance:** `AL2`

**Requirement:** Remote calls and repeatable operations MUST have explicit timeout/retry behavior; retries MUST be bounded and use backoff/jitter where appropriate; consequential repeated operations MUST be idempotent or deduplicated.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Client policies; idempotency design; fault tests.

**Verification:**
- Inject timeout/transient failure; verify bounded recovery and no duplicate effect.

**Blocking conditions:**
- Unbounded retry or duplicate consequential side effect is possible.

**References:** `GOOGLE-SRE`

### REL-03 — Concurrency correctness
**Minimum assurance:** `AL2`

**Requirement:** Shared mutable state and concurrent workflows MUST be analyzed for races, deadlocks, lost updates, TOCTOU and duplicate execution where applicable.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Concurrency analysis/tests; race detector when supported.

**Verification:**
- Stress/race test or deterministic concurrency test.

**Blocking conditions:**
- Known critical race/lost update remains unmitigated.

**References:** `ISO-25010-2023`, `GOOGLE-SRE`

### REL-04 — Load and capacity validation
**Minimum assurance:** `AL2`

**Requirement:** Systems with scale claims MUST validate expected and peak load against latency, error and saturation targets before relying on those claims.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Load-test report; capacity assumptions.

**Verification:**
- Run representative load test and compare p95/p99/error/saturation to targets.

**Blocking conditions:**
- Expected production load violates agreed target without accepted capacity plan.

**References:** `GOOGLE-SRE`, `ISO-25010-2023`

### REL-05 — Soak and software-aging tests
**Minimum assurance:** `AL3`

**Requirement:** Long-running services with material state/resource usage SHOULD undergo sustained-execution testing sufficient to detect leaks or progressive degradation.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Soak-test report with memory, latency, throughput/error trends.

**Verification:**
- Run sustained workload; analyze resource trends.

**Blocking conditions:**
- Material progressive degradation is observed without mitigation/acceptance.

**References:** `SOFTWARE-AGING-2026`, `GOOGLE-SRE`

### REL-06 — Resilience and cascading-failure controls
**Minimum assurance:** `AL3`

**Requirement:** Distributed/high-availability systems MUST test representative dependency failures, overload and degraded-mode behavior to limit cascading failures.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Resilience test/game-day evidence; circuit/backpressure/degraded-mode design as applicable.

**Verification:**
- Inject dependency latency/error/overload and observe system behavior.

**Blocking conditions:**
- Single dependency degradation predictably cascades beyond accepted blast radius.

**References:** `GOOGLE-SRE`, `OWASP-AGENTIC-2026`

## RLS — Release Engineering

### RLS-01 — Automated release quality gates
**Minimum assurance:** `AL2`

**Requirement:** Merge/release workflows MUST automatically enforce project-defined tests, security checks and framework validation appropriate to the assurance level.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- CI configuration and successful run.

**Verification:**
- Re-run pipeline on clean checkout.

**Blocking conditions:**
- Required gate is bypassed or non-blocking without waiver.

**References:** `NIST-SSDF-1.1`, `OPENSSF-AI-CODE`

### RLS-02 — Immutable, identifiable release artifacts
**Minimum assurance:** `AL2`

**Requirement:** Release artifacts MUST be uniquely versioned/content-addressable and SHOULD be signed or attestable at higher assurance levels.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Artifact digest/version; signature/attestation when required.

**Verification:**
- Verify digest and immutable release reference.

**Blocking conditions:**
- Deployed artifact cannot be uniquely identified.

**References:** `SLSA-1.2`

### RLS-03 — Staged rollout
**Minimum assurance:** `AL3`

**Requirement:** High-impact services SHOULD use staged rollout, canary, feature flags or equivalent blast-radius reduction where architecture permits.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Rollout plan/configuration.

**Verification:**
- Verify rollback/stop criteria and staged exposure.

**Blocking conditions:**
- High-risk release changes all production instances/users simultaneously without rationale.

**References:** `GOOGLE-SRE`

### RLS-04 — Tested rollback or forward recovery
**Minimum assurance:** `AL2`

**Requirement:** Significant releases MUST have a rollback or forward-recovery strategy that is tested proportionally to risk.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Rollback/recovery procedure and test evidence.

**Verification:**
- Exercise rollback in staging/representative environment.

**Blocking conditions:**
- Release creates irreversible failure mode without explicit AL-level approval.

**References:** `GOOGLE-SRE`, `NIST-SSDF-1.1`

### RLS-05 — Release approval separation
**Minimum assurance:** `AL3`

**Requirement:** AL3+ production release authorization MUST be separated from the implementing agent; AL4 MUST include accountable human approval.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Release approval record and identities.

**Verification:**
- Verify implementer/approver separation.

**Blocking conditions:**
- Implementing agent is sole authority for AL3+ release; AL4 lacks human approval.

**References:** `METR-REWARD-HACKING`, `OWASP-AGENTIC-2026`

## OPS — Production Operations

### OPS-01 — Golden-signal monitoring
**Minimum assurance:** `AL2`

**Requirement:** Production services MUST monitor latency, traffic/load, errors and saturation or domain-equivalent user-relevant signals.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Dashboards/metric definitions.

**Verification:**
- Verify metrics are emitted and queryable.

**Blocking conditions:**
- No visibility into material production failure/saturation.

**References:** `GOOGLE-SRE`

### OPS-02 — Structured logs, tracing and correlation
**Minimum assurance:** `AL2`

**Requirement:** Systems with distributed or asynchronous workflows SHOULD support correlation across material requests/jobs without logging sensitive secrets.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Logging/tracing design; sample trace/correlation ID.

**Verification:**
- Trace representative request across boundaries.

**Blocking conditions:**
- Material incident cannot be correlated across key components at AL3+ without rationale.

**References:** `GOOGLE-SRE`, `OWASP-TOP10-2025`

### OPS-03 — Actionable alerting and runbooks
**Minimum assurance:** `AL2`

**Requirement:** Alerts MUST correspond to actionable user-impact or impending capacity/security conditions and critical alerts MUST link to response guidance.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Alert rules; runbooks.

**Verification:**
- Test representative alert and escalation.

**Blocking conditions:**
- Critical known failure mode has no detectable/operable response path.

**References:** `GOOGLE-SRE`, `OWASP-TOP10-2025`

### OPS-04 — Incident learning and recurrence prevention
**Minimum assurance:** `AL2`

**Requirement:** Material incidents MUST produce a blameless technical record of impact, contributing causes, detection gaps and preventive actions.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Incident/postmortem record and tracked actions.

**Verification:**
- Verify actions have owners/status and feed requirements/tests.

**Blocking conditions:**
- Material recurring incident has no root-cause/recurrence action.

**References:** `NIST-SSDF-1.1`, `GOOGLE-SRE`

### OPS-05 — Disaster recovery objectives and exercises
**Minimum assurance:** `AL3`

**Requirement:** Critical services MUST define RPO/RTO or equivalent recovery objectives and periodically exercise recovery/failover against them.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- DR plan; RPO/RTO; exercise results.

**Verification:**
- Execute isolated recovery/failover exercise.

**Blocking conditions:**
- Recovery objectives are undefined or unverified for critical service.

**References:** `GOOGLE-SRE`

### OPS-06 — Production feedback closes the assurance loop
**Minimum assurance:** `AL2`

**Requirement:** Operational defects, near misses, security findings and SLO breaches MUST feed back into requirements, tests, controls or risk decisions.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Linked issue/control/test from production signal.

**Verification:**
- Trace sample incident/finding to corrective assurance artifact.

**Blocking conditions:**
- Repeated class of production failure has no feedback action.

**References:** `NIST-SSDF-1.1`, `AI-TECH-DEBT`

## GOV — Governance & Assurance

### GOV-01 — Risk and assurance-level classification
**Minimum assurance:** `AL1`

**Requirement:** Each project/release context MUST select an assurance level using documented risk triggers; risk may promote assurance requirements and MUST NOT be silently downgraded for convenience.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Risk classification and selected AL.

**Verification:**
- Review triggers against architecture/data/exposure.

**Blocking conditions:**
- Selected level contradicts mandatory promotion trigger without approved exception.

**References:** `NIST-SSDF-1.1`, `ISO-25010-2023`

### GOV-02 — Time-bounded waivers
**Minimum assurance:** `AL2`

**Requirement:** Exceptions to mandatory controls MUST identify reason, risk owner, scope, compensating controls, expiry/review date and remediation disposition.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Waiver record.

**Verification:**
- Check expiry, owner, compensating control and linked risk.

**Blocking conditions:**
- Blocking control is bypassed with no valid waiver; AL4 prohibited waivers ignored.

**References:** `NIST-SSDF-1.1`

### GOV-03 — Evidence package before release
**Minimum assurance:** `AL2`

**Requirement:** Release readiness MUST be based on an evidence package containing applicable control results, unresolved risks, waivers and approver decision.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Machine-readable assessment/evidence records and release summary.

**Verification:**
- Validate completeness and hashes/links.

**Blocking conditions:**
- Release decision has no auditable evidence package.

**References:** `NIST-SSDF-1.1`, `SLSA-1.2`

### GOV-04 — Model, agent, tool and environment provenance
**Minimum assurance:** `AL2`

**Requirement:** Significant AI-assisted changes SHOULD record model/agent/tool versions and material execution environment sufficiently to investigate failures and reproduce decisions where feasible.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Agent provenance metadata.

**Verification:**
- Trace representative change to recorded model/tool environment.

**Blocking conditions:**
- AL3+ high-impact AI change lacks model/tool provenance.

**References:** `OWASP-AGENTIC-2026`, `METR-REWARD-HACKING`

### GOV-05 — Technical-debt and architecture trend
**Minimum assurance:** `AL2`

**Requirement:** Projects with sustained AI-assisted development MUST monitor selected maintainability indicators and prevent unexplained long-term deterioration.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Trend metrics such as complexity, duplication, dependency violations, static findings, flaky tests or backlog aging.

**Verification:**
- Compare trend against baseline and investigate material regression.

**Blocking conditions:**
- Sustained material degradation is ignored without risk decision.

**References:** `SLOPCODEBENCH`, `AI-TECH-DEBT`

### GOV-06 — Standards and threat-model maintenance
**Minimum assurance:** `AL2`

**Requirement:** The framework/source registry and project threat model MUST be reviewed periodically for material changes in standards, dependencies, platforms and attack techniques.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Review date/owner and updates.

**Verification:**
- Check stale sources and material ecosystem changes.

**Blocking conditions:**
- High-assurance project relies on obsolete security baseline without review.

**References:** `NIST-SSDF-1.1`, `OWASP-TOP10-2025`, `OWASP-AGENTIC-2026`

### GOV-07 — Accountable human ownership
**Minimum assurance:** `AL2`

**Requirement:** Every production system MUST identify accountable human ownership for product risk, security/risk exceptions and incident escalation; AI agents cannot be the legal/organizational risk owner.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Ownership/approval matrix.

**Verification:**
- Verify named roles are reachable and authorized.

**Blocking conditions:**
- Production risk/exception has no accountable human owner.

**References:** `CISA-SBD`, `NIST-SSDF-1.1`

### GOV-08 — Independent assessment for higher assurance
**Minimum assurance:** `AL3`

**Requirement:** AL3 SHOULD receive periodic assessment by a person/team/process independent from implementation; AL4 MUST receive independent assessment before critical release and periodically thereafter.

**Applicability:** All software projects unless explicitly not applicable.

**Required evidence:**
- Independent assessment report and remediation status.

**Verification:**
- Verify assessor independence and evidence scope.

**Blocking conditions:**
- AL4 critical release lacks independent assessment.

**References:** `OWASP-ASVS-5`, `NIST-SSDF-1.1`

### GOV-09 — Authoritative repository access and branch protection
**Minimum assurance:** `AL2`

**Requirement:** The authoritative source repository MUST protect sensitive access with strong authentication where supported, grant collaborators least privilege, and prevent unreviewed or unauthorized changes to the primary branch and privileged CI/CD assets.

**Applicability:** Projects using a collaborative source-control platform; host-specific mechanisms may vary.

**Required evidence:**
- Repository/organization access policy and host settings showing applicable MFA/strong authentication, collaborator permissions, protected primary branch and required status/review controls.

**Verification:**
- Inspect authoritative repository settings and attempt/confirm that direct unauthorized primary-branch changes and untrusted privileged-CI access are prevented.

**Blocking conditions:**
- AL2+ production project has an unprotected authoritative branch or untrusted contributor path to privileged repository/CI credentials without approved compensating control.

**References:** `OPENSSF-OSPS-2026-08-28`, `OPENSSF-AI-CODE`, `NIST-SSDF-1.1`

### GOV-10 — Coordinated vulnerability reporting and response
**Minimum assurance:** `AL2`

**Requirement:** Released software MUST provide a documented vulnerability-reporting process with a private reporting path and accountable response ownership; public disclosure MUST not be the only route for reporting an unpatched vulnerability.

**Applicability:** Released software or public/open-source projects that can receive vulnerability reports.

**Required evidence:**
- Published security/vulnerability policy, private reporting mechanism, response ownership and expected handling process.

**Verification:**
- Verify the public documentation and that the private reporting route is operational and reaches an accountable owner.

**Blocking conditions:**
- Released AL2+ software has no documented private vulnerability reporting path or no accountable response owner.

**References:** `OPENSSF-OSPS-2026-08-28`, `NIST-SSDF-1.1`
