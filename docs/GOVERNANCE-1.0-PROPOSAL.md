# Governance 1.0 Proposal — NOT ADOPTED

Status: **DRAFT / HUMAN DECISION REQUIRED**

This document prepares the governance decisions required by MAT-10. It does not adopt them.

AuraCode's current governance remains maintainer-led. Stable 1.0 requires explicit human adoption of roles and decision rules.

## Decisions that must be made by project governance

### 1. Maintainer body

Decide:
- named maintainers;
- admission/removal rule;
- quorum;
- conflict-of-interest handling;
- inactivity policy.

No agent may invent or appoint maintainers.

## 2. Normative control changes

Decide the approval rule for changes to:
- controls/catalog.json;
- assurance levels/profiles;
- gate semantics;
- schemas that affect conformance;
- claim boundaries.

Candidate models include consensus, supermajority, or maintainer approval plus independent review. The project must choose and document one.

## 3. Release authority

Define:
- who may approve a release;
- who may create/sign release artifacts;
- minimum review/CI/maturity evidence;
- emergency release path;
- separation between implementer and release approver.

## 4. Security response

Define:
- security response team;
- private reporting channel;
- triage SLA or target;
- embargo/coordinated disclosure process;
- authority for emergency fixes;
- post-incident review requirement.

## 5. Appeals

Define a route for:
- rejected normative proposals;
- disputed conformance decisions;
- waiver disputes;
- maintainer conflicts.

## 6. Research/evidence governance

Define:
- who may alter preregistered protocols;
- when a protocol change creates a new study version;
- who approves claim language;
- how negative/null results are preserved;
- conflict-of-interest disclosure for evaluations.

## 7. Stable 1.0 adoption record

After human adoption, create one canonical JSON evidence package matching the MAT-10 validator with:
- status=ADOPTED;
- actual role identities;
- normative change rule;
- release authority rule;
- security response rule;
- appeal rule;
- evidence paths to adopted governance records.

Until then, validation/maturity-evidence.json must keep MAT-10 as UNKNOWN.

## Non-delegation rule

AI may draft alternatives, explain trade-offs, and verify internal consistency. AI must not decide:
- who has project authority;
- voting/quorum rules;
- release authority;
- appeals authority;
- security disclosure authority.

Those are governance decisions reserved to humans.
