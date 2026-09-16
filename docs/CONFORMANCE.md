# Conformance and Assessment Language

## Purpose

Version 0.1 defines profile assessment, not certification.

An assessment is always scoped to:
- framework version;
- assurance level;
- project/repository;
- commit, release or artifact;
- environment when relevant;
- assessment date;
- assessor identity/role.

## Profile satisfaction

A profile is satisfied only when every included control is one of:

- `PASS` with sufficient evidence; or
- `NA` with a legitimate applicability rationale.

Any `FAIL`, `NOT_ASSESSED` or `NA` without rationale prevents a profile-satisfied result.

Run:

```bash
python tools/assess.py <assessment.json>
```

## Allowed statements

Preferred:

> Assessed against AI Software Assurance Framework for Agentic Development 0.1.1-draft, AL2, scope commit `<sha>`. All applicable included controls were recorded as PASS or justified NA. This is a self-assessment and not a certification.

Or:

> Independently assessed against ... for the stated scope.

## Disallowed/unsupported statements in v0.1

Do not state:

- "certified by the framework";
- "NIST compliant";
- "ISO compliant/certified";
- "OWASP certified";
- "guaranteed secure";
- "equivalent to senior human engineering";
- "vulnerability free".

External standards have their own conformity, accreditation and interpretation regimes.

## Independence disclosure

An assessment should state whether it was:
- implementer self-assessment;
- separate agent review;
- deterministic-tool based;
- independent human/team assessment;
- external assessment.

A separate AI agent is useful evidence, but is not automatically equivalent to organizationally independent review.

## Waivers

A valid waiver does not turn a failed control into `PASS`. The assessment must disclose the residual risk and waiver separately. Projects may define release policies that permit specific waivers, except where their own AL4/critical policy prohibits them.
