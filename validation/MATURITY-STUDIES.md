# Maturity Studies — P2, P3, P4, Replication, Inter-Rater and Burden

This directory contains the evidence-producing studies required by the stable-1.0 maturity gate.

The key rule is:

> A valid study plan is not a completed study, and a completed study is not automatically a favorable result.

AuraCode separates three concepts:
1. preregistration/plan validity;
2. evidence-package completeness;
3. substantive interpretation of the observed effect.

The validators in validation/tools/maturity_studies.py check the first two. They deliberately do not invent a positive effect threshold after seeing results.

## P2 — Private/fresh confirmatory study

P2 is contamination-resistant confirmatory evidence.

A valid preregistration must freeze, before outcome collection:
- study id;
- A0/A1/A2 arms;
- at least 30 private/fresh scenarios;
- required scenario families;
- repetitions per arm;
- exact model/agent pairings;
- private split SHA-256 commitment.

Use:

~~~text
python validation/tools/maturity_studies.py p2 validation/config/p2-preregistration.example.json --json
~~~

A completed P2 evidence package is separately checked with:

~~~text
python validation/tools/maturity_studies.py p2-result <p2-result.json> --json
~~~

The result validator requires real runs, unique run IDs, scenario coverage, A0/A1/A2 coverage, consistent Qualified Success computation, expected attempt count, provenance and completed=true.

## Replication — MAT-03

Replication evidence must contain at least two distinct model/agent identities with completed studies.

Use:

~~~text
python validation/tools/maturity_studies.py replication <replication-result.json> --json
~~~

This verifies replication coverage only. It does not declare that an effect is favorable or statistically significant.

## P3 — External ecological validation

P3 uses external benchmark families without vendoring their datasets into AuraCode.

The preregistration must freeze:
- selected benchmark IDs from validation/benchmark-registry.json;
- verified license/terms;
- exact upstream revision;
- committed task subset hash;
- no opaque combined score across heterogeneous benchmarks.

Plan validation:

~~~text
python validation/tools/maturity_studies.py p3 <p3-plan.json> --json
~~~

Completed evidence validation:

~~~text
python validation/tools/maturity_studies.py p3-result <p3-result.json> --json
~~~

For stable-maturity evidence, at least two benchmark families must be completed and reported separately.

## P4 — Operational validation

P4 validates a representative service under:
- load;
- soak;
- rollback;
- recovery;
- observability.

Every dimension must carry evidence. Load must declare a positive target RPS and soak must declare a positive duration.

Use:

~~~text
python validation/tools/maturity_studies.py p4 <p4-result.json> --json
~~~

Production-destructive tests are not implied. Use a safe staging/sandbox environment and representative data unless an explicitly authorized production exercise exists.

## Independent assessor / inter-rater study — MAT-06

At least two independent assessors score the same controls using PASS / FAIL / NOT_APPLICABLE.

Use:

~~~text
python validation/tools/maturity_studies.py inter-rater <inter-rater.json> --json
~~~

The analyzer reports raw agreement and Cohen's kappa for the first two assessors. Agreement describes consistency; it is not proof that either assessor is correct.

## Burden and error calibration — MAT-07

Burden analysis preserves missing values as missing. It does not convert absent cost/token/tool-call measurements to zero.

For stable-maturity evidence, the package must also include false-positive/false-negative calibration counts.

Use:

~~~text
python validation/tools/maturity_studies.py burden-errors <burden-errors.json> --json
~~~

At minimum, elapsed time and human intervention burden must have observations in A0, A1 and A2.

## Evidence promotion rule

A MAT criterion remains UNKNOWN until:
- the required study is actually completed;
- the relevant validator returns VALID;
- the evidence artifact is committed/frozen;
- the criterion is reviewed under the applicable governance rule.

Creating a protocol, schema, template, or validator is implementation progress. It is not evidence that the corresponding study has passed.
