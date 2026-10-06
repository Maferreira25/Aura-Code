# Preflight: required verification coverage

The full preflight plan is mandatory. A missing `MANIFEST.json`, benchmark
validator (`validation/tools/validate_suite.py`), or `tests/` directory blocks
the plan immediately. Missing files are not an applicability decision.

The report keeps the top-level `FAIL` status and nonzero CLI exit code for
compatibility. The missing gate has `failed_step.status = NOT_ASSESSED` and
`returncode = null`, because no verifier ran. `steps_executed` counts actual
executions only; no subsequent gate executes after the missing prerequisite.
An empty gate plan also fails.

## Compatibility and scope

Previously, projects missing these inputs could obtain PASS after the remaining
checks succeeded. These projects must now provide the full preflight inputs.
Do not create placeholder files to satisfy the existence check: the actual
validators still execute and must succeed. A future application-specific plan
must define applicability explicitly through a validated policy; file absence
must never silently authorize skipping a gate.

This change closes the missing-input bypass. It does not establish evidence
signatures, freshness, provenance, assurance graph completeness, or prove that
an existing test directory contains meaningful tests. Those remain separate
requirements in the assurance evolution program.

## Threat and regression checks

Deleting verification inputs could previously remove gates from the plan.
Regression tests remove each required input in turn, assert NOT_ASSESSED,
confirm no later command runs, check a nonzero CLI exit code, and reject an
empty gate plan. Existing success, failure, and hook-installation tests remain.
