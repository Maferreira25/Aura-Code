# Independent Security and Supply-Chain Review — MAT-09

## Purpose

MAT-09 requires an independent review of the AuraCode threat model and software supply chain with no unresolved Critical or High blockers.

This guide defines the evidence package expected from an assessor who did not implement the change under review.

## Frozen review target

Before review, record:
- immutable Git commit SHA;
- AuraCode version;
- assessor identity/organization;
- review start/end dates;
- tools and versions used;
- scope limitations;
- conflicts of interest;
- whether the assessor had any implementation role in the reviewed changes.

The review must not target a moving branch.

## Required review areas

### Threat model

The assessor should independently evaluate:
- assets and security objectives;
- trust boundaries;
- attacker capabilities;
- prompt/context injection;
- evaluator tampering and reward hacking;
- agent tool misuse and privilege escalation;
- secret exposure;
- supply-chain compromise;
- unsafe code execution;
- workspace/container escape assumptions;
- CI/CD compromise;
- failure cascades and recovery;
- production/continuous assurance;
- threats introduced by AuraCode itself.

The existing docs/THREAT-MODEL.md is input, not the answer.

### Software supply chain

Review at minimum:
- dependency existence and provenance;
- Python packaging metadata;
- optional dependency groups;
- lock/resolution strategy where applicable;
- GitHub Actions pinning;
- action permissions;
- credential persistence;
- untrusted PR behavior;
- release provenance/attestation;
- SBOM generation;
- vulnerability review;
- license policy;
- private vulnerability reporting;
- branch/repository protection settings where observable.

## Evidence requirements

The canonical MAT-09 JSON package must contain:
- assessor_id;
- independence_attestation=true;
- immutable revision;
- scope;
- threat_model.status;
- threat_model.evidence;
- supply_chain.status;
- supply_chain.evidence;
- open_findings.critical;
- open_findings.high.

The supporting evidence referenced by the JSON should be committed or otherwise frozen in a review artifact package.

## Finding discipline

Every finding should include:
- stable ID;
- severity;
- confidence;
- affected path/control;
- evidence;
- exploitation/failure scenario;
- impact;
- recommendation;
- validation method.

Critical/High findings are blocking until independently revalidated.

## Independence

The implementing agent or maintainer may answer factual questions, but must not be the sole assessor.

A second model/session is better than self-review, but MAT-09 is intended to provide genuinely independent security/supply-chain assurance. Human or organizational independence should be preferred for the stable-1.0 claim.

## Claim boundary

A passing MAT-09 package means the configured independent review completed without open Critical/High blockers in its defined scope.

It does not mean:
- defect-free;
- vulnerability-free;
- certified by NIST/ISO/OWASP;
- permanently secure after later changes.
