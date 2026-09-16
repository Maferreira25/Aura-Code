# Antigravity Documentation Basis — 2026-09-09

This adapter is maintained against the **current Antigravity IDE interface**, not historical UI assumptions.

## Official sources checked

- Models: https://antigravity.google/docs/models
- IDE Settings: https://antigravity.google/docs/ide/settings/
- Agent Settings: https://www.antigravity.google/docs/agent-settings
- CLI Headless: https://antigravity.google/docs/cli/headless/
- Artifact Review: https://www.antigravity.google/docs/artifact-review/

## Operational interpretation

The current IDE model selector exposes model choices and displayed reasoning/thinking variants. For example, official current documentation lists Gemini 3.8 Flash Medium and other model variants.

The current CLI documentation separately exposes `--model` and `--effort low|medium|high`. This CLI capability is not treated as proof that the same control is exposed in the graphical IDE.

The Artifact Review documentation still contains references to `Planning Mode` and `Fast Mode`. Because those labels are not present in the current IDE interface used by the experiment, this adapter does **not** use them as IDE controls. Artifact Review itself remains a current setting, including `Request Review`.

## Maintenance rule

Before a formal experiment:

1. record the installed Antigravity version/build;
2. record the exact model label shown in the UI;
3. record the exact reasoning/thinking variant shown in the UI;
4. capture/record the relevant settings;
5. re-check current official documentation if the UI differs from this adapter.

When product documentation conflicts with the installed interface, record the discrepancy rather than silently mapping an old concept onto a new UI.

## Source registry IDs

- `ANTIGRAVITY-MODELS-2026`
- `ANTIGRAVITY-IDE-SETTINGS-2026`
- `ANTIGRAVITY-CLI-HEADLESS-2026`
