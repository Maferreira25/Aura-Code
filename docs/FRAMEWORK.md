# Framework Specification — 0.1.1-draft

## Scope

This framework governs software whose source, tests, architecture or operational configuration is produced or materially modified by LLMs/coding agents.

It is tool-neutral. Antigravity, Claude Code, Codex, Copilot, Cursor, custom agents and human-only teams can use the same assurance model.

## Non-goals

The framework is not:
- a guarantee of defect-free software;
- a replacement for domain regulation;
- a certification body;
- a claim that AI code is intrinsically inferior to human code;
- a requirement to use every security tool on every project.

## Control model

There are **75 controls** across **11 domains**.

Each control has:
- identifier;
- minimum assurance level;
- normative requirement;
- applicability;
- rationale;
- required evidence;
- verification method;
- blocking condition;
- source references.

The catalog is normative: `controls/catalog.json`.

## Control evaluation

Status:
- `PASS`: requirement satisfied with sufficient evidence.
- `FAIL`: applicable requirement not satisfied.
- `NA`: genuinely inapplicable, with rationale.
- `NOT_ASSESSED`: no conclusion yet.

A project cannot claim profile completion with `FAIL` or `NOT_ASSESSED` among included controls. `NA` without rationale is invalid.

## Risk and exceptions

Use `GOV-01` and `docs/RISK-CLASSIFICATION.md`.

Waivers:
- are explicit;
- have a human risk owner;
- expire or have a review date;
- identify compensating controls;
- do not rewrite history;
- may be prohibited for project-specific critical invariants.

## Independence model

Independence is a gradient, not a binary label:

1. implementer self-check;
2. separate agent context;
3. deterministic/static/dynamic tooling;
4. protected tests/held-out oracle;
5. independent human/team;
6. external assessor.

Higher assurance increases the expected diversity and independence of evidence.

A second LLM using the same model/context can add value but is not automatically independent enough for critical claims.

## Architecture continuity

Agentic development is iterative. Therefore architecture is controlled through:
- architecture system-of-record;
- ADRs;
- invariants;
- dependency/boundary rules;
- fitness/trend checks.

## Continuous assurance

Release is not the end. Operational evidence can falsify assumptions. Incidents, SLO failures, newly discovered vulnerabilities and architecture-debt trends must feed the next engineering cycle.
