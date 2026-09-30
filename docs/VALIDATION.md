# Validation of the Framework

## Status

Version 0.3.0.dev0 is a **development preview under structural and empirical validation**, not a certified release.

Validation is intentionally separated into four layers.

## V1 — Normative-source crosswalk

The control catalog was reviewed against high-level objectives from:

- NIST SSDF 1.1 (final baseline);
- NIST SSDF 1.2 initial public draft (informative only);
- OWASP ASVS 5.0;
- OWASP Top 10:2025;
- OWASP Top 10 for Agentic Applications 2026;
- OpenSSF security-focused AI code-assistant guidance;
- CISA Secure by Design;
- SLSA 1.2;
- CycloneDX;
- Google SRE guidance;
- ISO/IEC 25010:2023 high-level product quality model.

This is a **crosswalk of objectives**, not a claim of clause-by-clause compliance or certification. Proprietary ISO text is not reproduced.

## V2 — Empirical failure-mode coverage

`controls/failure-modes.json` maps observed AI/agent failure modes to one or more preventive/detective controls.

Examples include:
- correct-but-exploitable generated backends (BaxBench);
- correct-but-insecure/new vulnerabilities in realistic repository edits (SecureAgentBench);
- hallucinated software packages (USENIX Security 2025);
- evaluator/test manipulation and reward-hacking behavior (METR);
- benchmark pass not equivalent to maintainer merge readiness (METR);
- long-horizon architecture erosion (SlopCodeBench);
- persistent AI-attributed technical debt (2026 empirical preprint);
- sustained-runtime/software-aging risk (2026 empirical preprint).

Preprints and research notes are labeled as such in `controls/source-registry.json`; they inform risk controls but are not treated as normative standards.

## V3 — Machine structural validation

Run:

```bash
python tools/validate_framework.py
python -m unittest discover -s tests -v
```

The validator checks:
- unique control IDs;
- valid domains and assurance levels;
- mandatory control fields;
- non-empty evidence/verification/blocking rules;
- source references resolve;
- source URLs are HTTPS;
- failure-mode control/source references resolve;
- every documented failure mode maps to controls;
- assurance profiles match the catalog;
- profile monotonicity;
- schema/template basics;
- no control is orphaned from all evidence references.

## V4 — Empirical effectiveness validation (required before 1.0)

**Not yet completed.**

Before a stable 1.0 claim, the project should run at least:

1. **Pilot repositories:** diverse stacks and project sizes, including an internet-facing service.
2. **Seeded-defect benchmark:** known security, logic, architecture, dependency, test-integrity and reliability defects inserted under controlled conditions.
3. **Agent red-team:** prompt injection, malicious README/issue/tool output, evaluator tampering, package hallucination and privilege-abuse exercises.
4. **Long-horizon experiment:** repeated feature evolution with architecture/complexity trend measurement.
5. **Operational experiment:** load + soak + rollback/restore validation for a representative service.
6. **Inter-rater evaluation:** independent assessors apply the framework and measure agreement.
7. **Burden analysis:** time/cost and false-positive/false-negative estimates by assurance level.
8. **Baseline comparison:** compare ordinary AI-assisted workflow vs framework-governed workflow on matched tasks.

Suggested outcome metrics:
- escaped defects per change;
- exploitable findings per change;
- mutation score;
- architecture fitness violations;
- security scan findings;
- review rejection rate;
- mean verification effort;
- rollback/restore success;
- p95/p99 and error/SLO compliance;
- assessor agreement.

## Validation claim allowed for v0.1

Permitted:
> "Research-backed draft with machine-validated control integrity and traceable coverage of selected standards and empirical AI coding failure modes."

Not permitted:
> "Proven to make AI code as safe as senior human engineering."
> "Certified secure."
> "Compliant with NIST/ISO/OWASP."
> "Guarantees vulnerability-free software."

## Framework-repository dogfooding

The included GitHub Actions workflow pins `actions/checkout` to an immutable full commit SHA. The structural validator also checks external GitHub Action references for immutable SHA form, so the framework repository begins enforcing its own `SUP-06` rule rather than merely documenting it.


## Current P1 evidence status

**Snapshot: 2026-09-30.** At this snapshot, the repository contains 36 A0/A1/A2 result records from the public P1 smoke suite:

- 30 automated results: 10 scenarios x 3 arms x 1 repetition;
- 3 manual ambiguity results: 1 per arm;
- 3 longitudinal architecture results: 1 sequence per arm.

This is below the frozen P1 design of 90 automated runs (10 scenarios x 3 arms x 3 repetitions), 5 ambiguity repetitions per arm, and at least 3 architecture sequences per arm.

All three arms currently have 100% Qualified Success in the automated public-smoke results. This is a ceiling effect, so the current dataset does not discriminate A2 from A0/A1 and MUST NOT be described as evidence that the framework improves outcomes.

Run:

```bash
python validation/tools/validate_experiment_evidence.py validation/results
python validation/tools/validate_experiment_evidence.py validation/results --require-complete
```

The first command reports methodological status without failing solely because P1 is incomplete. The second is a blocking gate for any process that claims the frozen P1 has been completed.

Public smoke results remain methodology/harness evidence only; contamination-resistant effectiveness claims require the private/fresh P2 design described above.
