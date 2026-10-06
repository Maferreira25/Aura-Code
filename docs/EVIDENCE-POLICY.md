# Evidence policy gate v1

`auracode evidence gate --policy policy.json --bundle bundle.json --root .`
evaluates a JSON array of execution records against an externally trusted policy.
Every requirement must have exactly one record with the required control and
verification identity, an exact command match, and the exact declared file scope.
Each record must also pass execution-evidence integrity and freshness checks.
Missing, duplicate, unrelated, failed, malformed, or stale evidence blocks the
overall decision and returns a nonzero CLI exit code. A PASS for one requirement
cannot compensate for another requirement without proof. Empty policies fail.

Policy structure:

```json
{
  "schema_version": "1",
  "policy_id": "POL-tests",
  "requirements": [{
    "requirement_id": "REQ-tests",
    "control_id": "VER-01",
    "verification_id": "python-tests",
    "command": ["python", "-m", "unittest", "tests.test_example"],
    "scope": ["src/example.py", "tests/test_example.py"]
  }]
}
```

The report includes the policy digest and successful requirement/control/verifier/
evidence links, each pinned to its record digest. This is initial traceability,
not the full assurance graph, signed release manifest, or independent certification.

The caller must retain and protect the policy and records. Commands are compared
exactly, including executable names/paths. The gate cannot authenticate unsigned
records, determine if the policy covers all necessary controls, or establish the
quality of its verifier. It evaluates evidence; it never runs bundle commands.
Invocation is explicit and is not yet mandatory in every release workflow.

## Preflight enforcement

```sh
auracode preflight . --evidence-policy policy.json --evidence-bundle bundle.json
```

When either evidence parameter is supplied, both files are mandatory. The evidence
gate executes before the existing preflight checks, and any failure halts the plan.
Missing inputs produce NOT_ASSESSED without running subsequent checks. CI/release
owners must protect this invocation and its policy; omitting both flags retains the
legacy ten-gate plan. This is an explicit enforcement option, not a claim that every
release workflow already requires it.
