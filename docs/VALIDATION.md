# Validation of the Framework

## Status

Version 0.1.1-draft is **conceptually and structurally validated**, not empirically certified.

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
