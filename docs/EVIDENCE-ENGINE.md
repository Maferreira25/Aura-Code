# Execution evidence v1

This initial engine records physical execution of an explicitly supplied verifier.
It binds the result to a Git commit and SHA-256 digests of declared relative files.
Every verification must include all relevant source, tests, configuration, lockfiles,
and policy inputs in its scope. This engine does not infer complete scope.

```sh
auracode evidence run --control VER-01 --verification python-tests --scope tests/test_example.py --scope src/example.py --output evidence.json -- python -m unittest tests.test_example
auracode evidence verify evidence.json
```

The output path must not already exist. A failed or timed-out verifier still produces
a record, but the CLI returns nonzero. A scope or commit change during execution
produces STALE. Later changes, unavailable files, malformed records, duplicate JSON
keys, output digest mismatches, and non-PASS executions block verification.

## Integrity and trust boundary

Serialization is deterministic project-specific JSON (sorted keys, compact ASCII
encoding). It is not RFC 8785/JCS. Scope hashes cover actual bytes, without newline
normalization. The existing legacy evidence schema remains unchanged; the new
execution record uses a separate versioned schema.

Unsigned hashes detect changes against a trusted retained record. An attacker who
can rewrite both the record and its hashes can forge it. This engine does not prove
producer identity, reviewer independence, verifier quality, sandbox isolation,
complete scope, reproducible environment, or release authorization. A zero exit
code only proves the supplied process reported success. Commands execute with the
caller's permissions and must be authorized; no shell is introduced by the engine.

The evidence command is not yet a required release gate. Signing, policy binding,
environment attestation, assurance graph, and release integration remain pending.
