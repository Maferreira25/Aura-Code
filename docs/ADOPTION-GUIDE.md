# Adoption Guide

## Existing project

1. Run `tools/validate_framework.py`.
2. Select tentative assurance level.
3. Complete `templates/assessment.json`.
4. Map current architecture and critical invariants.
5. Do a gap assessment; do not refactor everything at once.
6. Fix Critical/High risks first.
7. Add CI evidence gates.
8. Add production/recovery evidence if the system is already live.
9. Reassess after material architecture/security changes.

## New project

Apply gates from G0. This is preferable because security, scale and invariants can influence architecture before code exists.

## AI coding agents

Use an adapter, but keep the normative catalog tool-neutral.

Recommended workflow:
- human intent;
- agent exploration;
- ambiguity gate;
- acceptance criteria;
- plan;
- controlled implementation;
- deterministic tests/scans;
- independent review;
- evidence package;
- release approval proportional to AL.

## Avoid checkbox compliance

The objective is not to maximize PASS counts. A small number of high-quality controls tied to real risks is better than ceremonial evidence.
