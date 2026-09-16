# Benchmark Contamination and Freshness

Public static coding benchmarks can become training data or be memorized. A framework-effect study must separate engineering ability from benchmark recall.

## Splits

### Public calibration split

Open scenarios in this repository.

Purpose:
- develop adapters;
- debug harnesses;
- demonstrate methodology.

Do not use them alone for headline model capability claims.

### Private evaluation split

Task statement and candidate repository are provided to the agent; protected evaluator and reference information remain outside agent access.

### Fresh/live split

Periodically collect or create new tasks after benchmark design freeze, following licensing and ethical rules.

## Freshness metadata

Every scenario/result should record:
- creation/collection date;
- source repository and issue date if external;
- whether task/solution was publicly available before evaluation;
- contamination risk: low / medium / high / unknown.

## Dynamic variants

Where semantically valid, randomize:
- identifiers;
- input data;
- tenant/user IDs;
- file names;
- boundary values;
- ordering;
- generated fixtures.

Dynamic variants are not a substitute for genuinely new tasks, but make lookup-table overfitting harder.

## Hidden-test security

Do not rely on obscurity alone.

A capable agent may try to inspect the scorer. Prefer:
- separate scoring container;
- no reference program in candidate namespace;
- no write access to evaluator;
- minimal scorer feedback;
- clean scoring environment;
- protected artifacts copied only after candidate execution.

## External fresh benchmarks

Adapters may use projects such as SWE-bench-Live/SWE-rebench where licensing and evaluation methodology permit. External tasks are not vendored by this project.
