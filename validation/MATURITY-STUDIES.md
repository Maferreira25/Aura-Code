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


## Frozen-evidence mechanics

The maturity tooling now treats preregistration and result packages as separate artifacts.

For P2:
- create the private/fresh scenario split outside the public candidate workspace;
- commit the split cryptographically with validation/tools/private_split.py;
- freeze the preregistration file and record its SHA-256;
- execute the exact scenario × arm × pairing × repetition matrix;
- the result package must reference the preregistration path/hash and the same private-split commitment;
- the validator rejects missing cells, added/removed scenarios, changed pairings, altered repetition counts, or a shrunken expected_attempts value.

For P3:
- freeze benchmark IDs, upstream revisions, license verification, task-subset commitments, attempts per arm, and model/agent pairing before execution;
- completed results must match that preregistration exactly;
- at least two benchmark families are required for stable-maturity evidence;
- each benchmark reports A0/A1/A2 separately; heterogeneous scores are not collapsed into a single opaque score.

For P4:
- freeze service/revision/environment and success criteria before execution;
- load and soak targets/durations are preregistered;
- stable-maturity evidence requires PASS for load, soak, rollback, recovery, and observability;
- changing the test target or thresholds after observing outcomes invalidates the package.

## Private/fresh split commitment

Create a privacy-preserving commitment without publishing the split contents:

~~~text
python validation/tools/private_split.py commit /private/p2-split \
  --output validation/private/P2-PRIVATE-001-commitment.json --json
~~~

Later verify the same split:

~~~text
python validation/tools/private_split.py verify /private/p2-split \
  validation/private/P2-PRIVATE-001-commitment.json --json
~~~

The commitment detects changed files/content. It does not prove scenario quality, freshness, independence, or absence of contamination.

## Multi-language qualification

The public corpus at validation/multilang-qualification/corpus.json is only a development baseline.

Run:

~~~text
python validation/tools/qualify_multilang.py \
  --revision <immutable-commit> --json
~~~

A public-corpus result is deliberately marked maturity_eligible=false.

MAT-08 stable evidence requires a private/fresh independently labeled corpus, a corpus commitment, preregistered thresholds, Python and TypeScript confusion matrices, and passing recall/false-positive-rate thresholds.

## Stable maturity ledger integrity

A declared PASS for MAT-02 through MAT-10 requires:
- exactly one canonical JSON evidence package;
- semantic validation for the specific MAT criterion;
- all nested evidence references to be repository-relative files that actually exist;
- reviewed_by;
- reviewed_at in ISO-8601;
- evidence_sha256 matching the canonical package.

Use the proposal helper:

~~~text
python validation/tools/prepare_maturity_evidence.py MAT-XX <package.json> \
  --reviewed-by "<independent reviewer>" \
  --reviewed-at "YYYY-MM-DDTHH:MM:SSZ" --json
~~~

The command validates and hashes the package but does **not** modify validation/maturity-evidence.json and does not authenticate reviewer identity. Human/project governance still decides whether the reviewed package is accepted into the ledger.

## MAT-09 and MAT-10

MAT-09 uses docs/audit/INDEPENDENT-SECURITY-REVIEW-GUIDE.md. The assessor must attest independence and must not have had an implementation role in the reviewed change. Threat-model and supply-chain review evidence are both required, with zero open Critical/High blockers.

MAT-10 is intentionally not self-completable by an agent. docs/GOVERNANCE-1.0-PROPOSAL.md is a draft decision package only. A PASS requires explicit human adoption, identified human authority, adopted roles, and frozen governance evidence.


## Execution queues and global readiness

AuraCode now separates two kinds of queue.

### Study execution queues

validation/tools/maturity_queue.py materializes the frozen execution design for P2, P3 and P4.

Examples:

~~~text
python validation/tools/maturity_queue.py p2 <p2-plan.json> --missing-only --json
python validation/tools/maturity_queue.py p3 <p3-plan.json> \
  --registry validation/benchmark-registry.json --missing-only --json
python validation/tools/maturity_queue.py p4 <p4-plan.json> --json
~~~

A queue entry marked COMPLETE means only that the planned execution/evidence slot exists. It does not mean Qualified Success, PASS, or maturity approval.

### Stable-maturity readiness queue

validation/tools/maturity_readiness.py combines:
- the authoritative maturity gate;
- the MAT-01 through MAT-10 workplan;
- current P1 completion/missing-run counts.

Run:

~~~text
python validation/tools/maturity_readiness.py . --json
~~~

The workplan at validation/maturity-workplan.json defines owner-role type, prerequisites, validator command, evidence package and next action for every MAT criterion.

The workplan is explicitly **not** a status source. PASS/FAIL/UNKNOWN continues to come only from the maturity gate and validated evidence ledger.

This distinction prevents an operational checklist from silently becoming evidence.


## Unified AuraCode maturity CLI

The internal Python tools remain directly executable for research automation, but the supported operator entrypoint is the unified AuraCode CLI.

Existing gate syntax remains valid:

~~~text
auracode maturity . --json
~~~

Equivalent explicit form:

~~~text
auracode maturity gate . --json
~~~

Current readiness/work queue:

~~~text
auracode maturity readiness . --json
~~~

Validate study plans or result packages:

~~~text
auracode maturity study p2 <p2-plan.json> --json
auracode maturity study p2-result <p2-result.json> --root . --json
auracode maturity study p3 <p3-plan.json> --registry validation/benchmark-registry.json --json
auracode maturity study p3-result <p3-result.json> --registry validation/benchmark-registry.json --root . --json
auracode maturity study p4-plan <p4-plan.json> --json
auracode maturity study p4 <p4-result.json> --root . --json
auracode maturity study inter-rater <package.json> --root . --json
auracode maturity study burden-errors <package.json> --json
auracode maturity study multilang-qualification <package.json> --json
auracode maturity study security-audit <package.json> --json
auracode maturity study governance <package.json> --json
~~~

Generate deterministic execution queues:

~~~text
auracode maturity queue p2 <p2-plan.json> --missing-only --json
auracode maturity queue p3 <p3-plan.json> --registry validation/benchmark-registry.json --missing-only --json
auracode maturity queue p4 <p4-plan.json> --missing-only --json
~~~

Prepare, but do not automatically adopt, a reviewed ledger entry:

~~~text
auracode maturity prepare MAT-XX <package.json> \
  --reviewed-by "<reviewer>" \
  --reviewed-at "YYYY-MM-DDTHH:MM:SSZ" --json
~~~

Validate that MAT-01 through MAT-10 still have complete implementation scaffolding:

~~~text
auracode maturity infrastructure . --json
~~~

The unified CLI does not change the evidence model: plans are not results, completed runs are not automatically successful, and a prepared ledger entry is not automatically accepted into project governance.


## External review handoff

Before an independent maturity/security/governance review, export a frozen handoff package:

~~~text
auracode maturity handoff . \
  --revision <immutable-commit-sha> \
  --output-dir <review-package-directory> --json
~~~

The export contains the frozen revision, current maturity blockers, P1 progress, selected review-file hashes, and the MANIFEST hash. It intentionally excludes private/fresh scenario contents and hidden evaluator material.

The handoff is not an approval and does not alter validation/maturity-evidence.json.
