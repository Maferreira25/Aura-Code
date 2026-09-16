# Framework Threat Model

The framework itself assumes a capable coding agent may:
- make plausible but wrong implementation choices;
- optimize visible tests rather than user intent;
- alter tests/evaluators if permitted;
- trust malicious repository/web/tool content;
- install a hallucinated or malicious dependency;
- expose secrets via context/logs;
- accumulate architecture debt across iterations;
- overstate completion/quality;
- take excessive or repeated tool actions.

Threat actors also include:
- malicious package publishers;
- malicious contributors/issues/README content;
- compromised CI/actions/plugins/MCP servers;
- external attackers exploiting generated code;
- accidental human misconfiguration.

Trust boundaries:
- human/product authority;
- model context;
- repository;
- CI;
- package registries;
- secret stores;
- staging/production;
- external tools/MCP/plugins;
- evaluator/protected tests.

Framework defenses are primarily controls `AGT-*`, `VER-*`, `SUP-*`, `SEC-*`, `RLS-*` and `GOV-*`.

This threat model must itself evolve as agent capabilities change.
