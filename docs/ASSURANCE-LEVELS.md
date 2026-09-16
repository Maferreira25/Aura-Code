# Assurance Levels

Assurance level is selected from consequence, exposure and reversibility—not project prestige.

## AL1 — Foundation

Suitable for low-impact prototypes, local tools and governed early development.

Minimum intent: traceability, human authority over material requirements, basic secure coding, dependency verification and AI zero-trust.

## AL2 — Production

Default baseline for commercial production.

Adds threat modeling where relevant, layered tests, independent oracle, supply-chain scanning, CI gates, operational monitoring, SLOs, recovery planning and accountable ownership.

## AL3 — High Assurance

Promote to AL3 when one or more material triggers apply:
- public internet exposure with material attack surface;
- sensitive/confidential data;
- multi-tenant isolation;
- authentication/authorization boundary central to harm;
- payment/financial or other consequential actions;
- major irreversible data migration;
- global/high-availability service;
- agent with consequential autonomous tools;
- high-value supply-chain artifact.

Adds protected/held-out tests, stronger architecture fitness, SBOM/provenance expectations, mutation/fuzz/soak/resilience evidence, independent assessment and separation of release authority.

## AL4 — Critical

Use where failure may cause catastrophic safety, mission, critical-infrastructure, major regulatory or irreversible high-value harm.

Mandates comprehensive critical invariant verification (`VER-09`) via formal methods, exhaustive property-based proofs, or model checking, with zero-waiver policies for core safety invariants across all preceding AL1–AL3 controls.

## Promotion rule

Risk can promote controls above the nominal project level. A project MUST NOT lower its level solely to avoid a control.

## Applicability

The assurance level determines the minimum control set. Applicability still matters. For example, a desktop application with no distributed service may legitimately mark some SRE controls `NA`; rationale is required.
