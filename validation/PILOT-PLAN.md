# Empirical Pilot Plan

## Purpose

The pilot validates the **experiment**, not yet the framework's universal effectiveness.

It asks whether the A0/A1/A2 methodology can be run reproducibly, whether the scorers discriminate seeded defects, whether agent behavior can be captured without evaluator leakage, and whether the framework shows a signal large enough to justify a larger confirmatory study.

## Phase P0 — Harness qualification — COMPLETE IN THIS DRAFT

Public automated smoke scenarios: 10.

Acceptance:
- every seeded baseline passes public tests;
- every seeded baseline fails protected tests;
- every reference solution passes public + protected tests;
- evaluator-integrity file checks work;
- scenario/control references validate;
- framework unit tests remain green.

The generated validation report records P0 status.

## Phase P1 — Single-agent methodology pilot

Use one fixed contemporary model + one fixed coding-agent/scaffold version.

For the current Antigravity IDE pilot, freeze both **model** and **reasoning/thinking variant**. The default P1 configuration is `Gemini 3.8 Flash Medium` unless the preregistration chooses another current model/variant before results are observed. Do not use historical `Planning Mode/Fast Mode` labels as IDE factors.

### Automated scenarios

10 public smoke scenarios × 3 arms × 3 independent repetitions = **90 runs**.

Purpose:
- validate session isolation;
- validate result capture;
- measure run-to-run variance;
- detect harness weaknesses;
- measure overhead;
- test whether A1 is a meaningful active comparator.

These public scenarios MUST NOT be used for headline capability claims because contamination risk is high after publication.

### Manual ambiguity scenario

`INT-AMBIG-001`: 3 arms × 5 repetitions = 15 runs.

Use the exact scripted user response in `EVALUATION.md`.

Measure:
- whether a material question is asked;
- whether it is asked before implementation;
- question relevance and plain-language quality;
- final duplicate-data behavior.

### Longitudinal architecture scenario

`ARC-EVOL-001`: run the five-stage sequence at least 3 times per arm.

Measure after every stage, not merely at the end.

## Phase P2 — Private/fresh confirmatory suite

Before collecting results, create and freeze a private/fresh split of at least **30 scenarios**, covering at minimum:

1. authorization/input security;
2. data integrity/idempotency/concurrency;
3. dependency/supply chain;
4. evaluator integrity/agentic security;
5. architecture evolution;
6. reliability/operability.

Recommended confirmatory design:

30 scenarios × 3 arms × 5 repetitions × at least 3 distinct model/agent pairings = **1,350 attempts**.

This number is a design target, not a statistical power claim. Final sample size MUST be informed by P1 variance/effect size and preregistered before P2.

## Phase P3 — External ecological validation

Repeat the framework comparison on selected upstream benchmark families rather than only synthetic tasks.

Priority candidates:
- BaxBench;
- SecureAgentBench or SecRepoBench after license verification;
- SWE-bench-Live and/or SWE-rebench for fresh real-world issue resolution;
- OWASP Benchmark / NIST SARD for security-tool calibration.

Do not combine scores from heterogeneous benchmarks into one opaque number.

## Phase P4 — Operational validation

Select at least one representative service and test:
- load/capacity;
- sustained/soak workload;
- dependency failure;
- rollback;
- backup/restore where persistent data exists;
- observability and SLO evidence.

## Promotion criteria toward framework 1.0

Before the first formal P2 result, project governance must freeze practical success criteria.

At minimum, 1.0 should require evidence that:
- A2 improves Qualified Success relative to A0 across multiple task families;
- the improvement is replicated across more than one model/agent pairing;
- A2 does not create a material regression relative to A1 on ordinary engineering outcomes;
- evaluator-integrity and critical-security failures are reduced;
- overhead is measured and judged acceptable for the target assurance level;
- independent reviewers can apply the control model with reasonable agreement.

No threshold should be invented after seeing whether the framework passed it.
