# Assurance Case Model

The framework uses a lightweight assurance-case structure.

For each material property:

1. **Claim** — what must be true.
2. **Context/applicability** — when the claim matters.
3. **Evidence** — artifact that supports the claim.
4. **Verification** — how the evidence is checked.
5. **Decision rule** — what blocks release.
6. **Exception** — who can accept residual risk, for how long, and with what compensation.

Example:

**Claim:** retrying a payment request cannot create a second charge.  
**Evidence:** idempotency design + integration test with duplicate delivery.  
**Verification:** run the same operation twice with the same idempotency key and inspect persisted charge count.  
**Decision rule:** release blocks if more than one charge is created.  
**Exception:** normally not waivable at high assurance because the invariant is core to financial integrity.

The machine-readable form is in `controls/catalog.json` and `schemas/evidence.schema.json`.
