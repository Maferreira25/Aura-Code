# Assurance State and Decision Architecture

## Purpose

AuraCode uses a persistent, fail-closed assurance state to prevent a software change from advancing when required evidence is missing, failed, malformed, or produced without the required independence.

The state engine does not replace the normative control catalog. "controls/catalog.json" and the AL1-AL4 profiles remain the source of applicable requirements. The state engine consumes those requirements and decides whether a lifecycle transition is allowed.

## Components

- tools/assurance_state.py — state model, evidence/control ingestion, findings, remediation/revalidation, independence checks, and lifecycle decision logic.
- tools/assurance_state_cli.py — command-line adapter for the state engine.
- controls/gates.json — machine-readable lifecycle gate policy.
- schemas/assurance-state.schema.json — persisted-state contract.
- tools/continuous_assurance.py — deterministic posture snapshots and drift/regression detection.
- tools/dogfood_assurance.py — applies AuraCode's own assessment/audit pipeline to a repository without fabricating missing provenance.
- tools/maturity_gate.py — separate release-maturity boundary used only for promotion of AuraCode itself to stable 1.0.

## State model

The principal lifecycle states are:

~~~
INTAKE
  -> RISK_CLASSIFIED
  -> REQUIREMENTS_VERIFIED
  -> ARCHITECTURE_VERIFIED
  -> IMPLEMENTATION
  -> VERIFICATION
  -> SECURITY_VERIFIED
  -> RELEASE_READY
  -> RELEASE_APPROVED
  -> DEPLOYED
  -> PRODUCTION_VERIFIED
  -> CONTINUOUS_ASSURANCE
~~~

Transitions are sequential. A stage cannot be skipped merely because later evidence exists.

The persisted state also records:
- assurance level;
- assurance status;
- control results and evidence;
- actor provenance;
- findings and their lifecycle;
- material decisions;
- audit history;
- transition history.

## Control result semantics

Supported control states are:
- PASS — requirement is satisfied and evidence is present.
- FAIL — requirement is not satisfied.
- UNKNOWN — evidence is absent or insufficient.
- NOT_APPLICABLE — requirement does not apply and has a rationale.
- WAIVED — temporary exception with valid owner, rationale, and expiry where the gate permits waiver.

For mandatory evidence, UNKNOWN is blocking. Absence of information is never converted to PASS.

A declared PASS without evidence is also blocking.

## Actor separation

AuraCode separates these roles:
- implementer;
- verifier;
- auditor;
- remediator;
- revalidator;
- approver.

For assurance levels where independence is required, the implementing actor cannot be the sole verifier or approver of its own work.

Current policy:
- AL2: implementer and verifier/auditor must be distinct actors and distinct sessions.
- AL3/AL4: when both roles are performed by AI, the current gate policy also requires distinct model identities.
- Remediation never self-closes a finding. A remediator may reach IMPLEMENTED, but RESOLVED requires independent revalidation.
- Human approval remains required where the applicable control/profile demands it.

Deterministic tools and protected evaluators remain independent evidence sources; a second AI opinion does not override a failing deterministic gate.

## Finding lifecycle

A confirmed finding follows a controlled lifecycle:

~~~
CONFIRMED
  -> IN_REMEDIATION
  -> IMPLEMENTED
  -> independent revalidation
       -> RESOLVED
       -> REVALIDATION_FAILED
~~~

IMPLEMENTED means a correction exists. It does not mean the problem is resolved.

## Continuous Assurance

Continuous Assurance compares evidence-bearing snapshots across revisions.

A blocking regression can include:
- a control changing from PASS to FAIL or UNKNOWN;
- a deterministic guarantee changing from PASS to a non-pass state;
- a new open Critical/High finding;
- increased architecture or test-integrity violations.

When such a regression is applied to persistent state, AuraCode creates a governed finding and marks assurance as reopened. The production lifecycle history is not falsified or rewound; instead, future progression is blocked until remediation and independent revalidation restore an active assurance posture.

## Assessment and audit ingestion

Existing AuraCode assessment and audit engines remain authoritative for what they actually verify.

The state engine does not translate a clean audit into blanket control approval.

When importing an assessment:
- evidence paths are verified;
- invalid PASS or invalid NA claims are downgraded to UNKNOWN;
- only applicable profile controls are imported.

When importing an audit:
- a clean audit is stored as audit evidence;
- a failed/non-run audit creates a blocking finding;
- no unrelated control is silently upgraded to PASS.

## Dogfooding

"auracode dogfood" applies the framework to a repository using its assessment and deterministic audit evidence.

It deliberately does not fabricate implementer/verifier identity. Therefore a repository with valid engineering evidence can still stop at the independent-verification boundary until real provenance is supplied.

A blocked dogfood result is a valid outcome.

## Stable 1.0 maturity gate

The lifecycle Decision Engine and the stable-release Maturity Gate have different responsibilities.

The lifecycle Decision Engine answers:

> May this project/change advance to the next assurance stage?

The Maturity Gate answers:

> Does the AuraCode framework itself have the preregistered empirical, operational, governance, and independent-review evidence required for a stable 1.0 claim?

The Maturity Gate is therefore not a second lifecycle engine. It is a project-level claim/release boundary for AuraCode itself.

Unknown maturity evidence remains blocking. The gate must not be weakened merely to produce a stable version number.

## Architectural invariant

The central invariant is:

> A later stage must never be used as evidence that an earlier failed, unknown, or unverified requirement was valid.

This prevents error propagation through the development lifecycle and implements the framework principle: evidence over confidence.
