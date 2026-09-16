# Antigravity Adapter

This adapter translates the tool-neutral framework into **current Antigravity IDE** workspace instructions.

## Current IDE execution model

For experiment reproducibility, treat the Antigravity IDE as selecting:

- an exact **model**; and
- the model's displayed **reasoning/thinking variant**, when available (for example Low, Medium or High).

Do **not** use `Planning Mode` or `Fast Mode` as IDE experimental variables. Those labels remain in some older/lagging documentation pages, but the current IDE model selector and recent documentation/changelog expose model variants/reasoning levels instead.

The Antigravity CLI is a separate execution surface and may expose additional command-line controls such as `--effort low|medium|high`. CLI settings MUST NOT be inferred to exist in the IDE.

## Recommended experimental controls

Across A0/A1/A2, freeze the same:

- Antigravity IDE version/build;
- model display name;
- reasoning/thinking variant;
- Artifact Review policy;
- Terminal Auto Execution policy;
- Strict Mode state;
- non-workspace file access;
- network/browser policy;
- plugins/MCP configuration;
- machine/resources.

For the initial P1 protocol, the documented default is **Gemini 3.8 Flash — Medium**, unless the preregistration deliberately chooses another currently available model/variant.

## Installation

Copy `.agents/` from this directory into the candidate project root **only for A2**.

Recommended:
- user authority / zero-trust / engineering / execution-gate rules: Always On;
- Artifact Review: Request Review for all arms when available;
- Strict Mode and workspace isolation: same state for all arms;
- use specialized skills by task;
- use read-only independent reviewers for significant/security-sensitive changes.

The framework catalog remains authoritative. If an adapter conflicts with `controls/catalog.json`, the catalog wins.

See `DOCUMENTATION-SOURCES.md` for the current Antigravity documentation basis and known documentation inconsistency.
