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
