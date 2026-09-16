# Normative Principles

The following principles are normative for the framework.

1. **Human semantic authority.** Material product/risk decisions remain human-owned unless explicitly delegated.
2. **Repository as system of record.** Requirements, architecture, invariants, decisions and exceptions persist outside transient model context.
3. **AI zero-trust.** AI-generated output is an untrusted assertion until corroborated.
4. **Evidence over confidence.** A model's statement is never the sole proof of a material property.
5. **Independent verification.** Higher-risk changes require increasing independence between generation, oracle, review and release authority.
6. **Evaluator integrity.** An implementer cannot silently weaken the mechanism used to judge its work.
7. **Risk-proportionate assurance.** Controls scale with consequence and exposure.
8. **Least agency + least privilege.** Agents get the minimum action capability and privilege needed.
9. **Secure by design/default.** Security requirements and threat modeling precede security-sensitive code.
10. **Architecture continuity.** Long-lived systems preserve explicit boundaries, invariants and decisions across iterative agent work.
11. **Demonstrated recoverability.** Rollback, restore and disaster recovery are evidence-bearing capabilities.
12. **Continuous assurance.** Production signals feed requirements, tests and risk decisions.

## Normative language

- **MUST / MUST NOT**: mandatory when the control is applicable at the selected assurance level.
- **SHOULD / SHOULD NOT**: strong recommendation; deviation requires rationale when material.
- **MAY**: optional.

A control may be marked `NA` only when its applicability condition is genuinely absent and the rationale is recorded. `NA` is not a mechanism to avoid cost.
