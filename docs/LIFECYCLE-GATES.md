# Lifecycle Gates

A gate is a decision boundary. Passing requires evidence, not a narrative statement.

## G0 — Intake & Risk

Required:
- purpose and accountable owner;
- risk/assurance level;
- initial data/exposure/privilege classification.

Block when material risk is unknown.

## G1 — Requirements & Acceptance

Required:
- traceable requirements;
- resolved material ambiguity;
- observable acceptance criteria;
- relevant NFRs.

Block when the agent would need to invent material behavior.

## G2 — Threat & Architecture

Required proportionately:
- architecture/boundaries;
- threat model;
- invariants;
- ADR for material long-lived decision;
- scale/recovery assumptions.

Block when a high-risk trust boundary or destructive data decision is unresolved.

## G3 — Implementation

Required:
- least-agency execution;
- verified dependencies;
- controlled scope;
- coding/security rules;
- agent provenance for significant work.

Block on secret exposure, unverified package introduction, unauthorized evaluator modification or prohibited architecture dependency.

## G4 — Verification

Required proportionately:
- acceptance tests;
- regression/integration/E2E;
- independent oracle;
- security tests/scans;
- test-strength evidence at higher assurance;
- protected evaluator/test integrity.

Block on mandatory failing gate, critical unwaived finding, or missing evidence.

## G5 — Release

Required:
- evidence package;
- artifact identity;
- supply-chain evidence;
- recovery/rollback;
- approval separation at higher assurance.

Block when release cannot be traced/recovered or blocking control is unresolved.

## G6 — Production & Continuous Assurance

Required:
- monitoring/SLIs/SLOs;
- alerts/runbooks;
- incident feedback;
- recovery exercises;
- technical-debt/architecture trend.

A production incident reopens the assurance loop; it is not merely an operations event.


## Fail-closed state semantics

Lifecycle gates are machine-enforced through controls/gates.json and the persistent Assurance State engine.

For required evidence:
- FAIL blocks;
- UNKNOWN blocks;
- missing evidence blocks;
- PASS without evidence blocks;
- NOT_APPLICABLE requires rationale;
- WAIVED is accepted only where the gate permits it and the waiver is valid.

A later successful stage never repairs an earlier failed or unknown requirement by implication.

## Independent verification boundary

At G4 and later gates where independence applies:
- the implementing actor cannot be the sole verifier/auditor;
- actor provenance must be recorded;
- prohibited same-session verification blocks advancement;
- AL3/AL4 AI-to-AI verification additionally follows the current model-diversity policy;
- protected/deterministic evidence is not overridden by agent confidence.

A remediator cannot self-declare a finding resolved. Resolution requires independent revalidation.

See docs/ASSURANCE-STATE.md for the complete state model and finding lifecycle.

## Stable-release maturity boundary

The AuraCode stable-1.0 maturity gate is intentionally separate from G0-G6. G0-G6 govern project/change lifecycle assurance. The maturity gate governs whether AuraCode itself has the preregistered evidence needed for a stable 1.0 maturity claim.

UNKNOWN maturity evidence blocks stable release.
