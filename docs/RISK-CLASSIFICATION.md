# Risk Classification

Classify the project/change before selecting assurance.

Score is intentionally qualitative in v0.1. Consider:

- **Impact:** harm if incorrect, unavailable or compromised.
- **Exposure:** internet/public input, adversarial access, supply-chain reach.
- **Data:** sensitivity, regulatory significance, cross-tenant risk.
- **Privilege:** credentials, admin/IAM, execution, production access.
- **Irreversibility:** deletion, financial transfer, destructive migration.
- **Scale:** users, geographic reach, dependency blast radius.
- **Autonomy:** whether an agent can take consequential actions without per-action approval.
- **Novelty/uncertainty:** unfamiliar stack, external service, unstable API.

### Default recommendation

- Low across dimensions → AL1 may be reasonable.
- Commercial production → at least AL2.
- Any high material dimension → consider/promote to AL3.
- Catastrophic/critical dimension → AL4.

Record the rationale. Risk classification is itself reviewable evidence.
