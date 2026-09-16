# Audit Guide

## 1. Establish scope

Record project, commit/release, environment and assurance level.

## 2. Validate risk classification

Do not begin by accepting the project's chosen AL. Review exposure, data, privilege, autonomy, scale and irreversibility.

## 3. Evaluate controls

For each control in the profile:
- PASS with evidence;
- FAIL with finding;
- NA with rationale;
- NOT_ASSESSED.

Do not accept "the agent says it did this" as sufficient evidence for material controls.

## 4. Evidence quality

Prefer evidence in this rough order:
1. independently reproducible/deterministic artifact;
2. protected/held-out test;
3. independent human/team review;
4. independent agent plus corroboration;
5. implementer-produced evidence.

Quality depends on the claim; this order is not absolute.

## 5. Findings

Record:
- control;
- observed condition;
- evidence;
- consequence;
- remediation;
- severity;
- owner.

## 6. Conformance statement

Use:
> "Assessed against AI Software Assurance Framework 0.1.1-draft, profile ALx, for scope <commit/release>. This is not a certification."

Do not call an assessment "certified" unless a future governance program explicitly creates and controls certification.
