# Experiment Runbook

## Before experiment

- Freeze framework commit.
- Freeze validation suite commit.
- Freeze model/agent/scaffold version.
- Register experimental arms.
- Predeclare scenarios, repetitions and primary endpoint.
- Prepare isolated candidate/scoring environments.
- Verify baseline seeded defects.
- Verify scorer passes on a reference/gold solution if one exists.
- Confirm protected files are not candidate-readable/writable.

## For each run

1. Create clean workspace with `harness.py prepare`.
2. Record run metadata before agent starts.
3. Start a fresh agent context.
4. Supply only the arm-authorized instructions.
5. Apply identical time/token/tool limits.
6. Record transcript/tool actions when permitted.
7. Stop according to common budget/termination rule.
8. Snapshot/hash submitted workspace.
9. Evaluate outside the candidate environment.
10. Review evaluator-integrity signals.
11. Store result JSON immutably.

## After runs

- blind subjective reviewers;
- reconcile disagreements;
- run analysis;
- inspect all successful runs for cheating/evaluator manipulation in high-assurance experiments;
- report failures and infrastructure exclusions;
- archive protocol, prompts, versions and hashes.
