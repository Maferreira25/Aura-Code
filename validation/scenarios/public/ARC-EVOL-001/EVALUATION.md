# Longitudinal Evaluation

Run each stage in a fresh continuation of the same repository/workstream.

After every stage record:
- tests;
- file/module count;
- LOC;
- duplicated logic indicators;
- imports/dependency direction;
- domain/service boundary violations;
- public API regressions;
- reviewer findings.

Minimum architecture fitness rules:
1. `domain.py` MUST NOT import infrastructure/storage/network modules.
2. `service.py` MUST NOT import `json`, `sqlite3`, `smtplib`, `requests` or a concrete infrastructure adapter.
3. External I/O is injected through collaborators.
4. Existing tests remain green.
5. New stage behavior has tests.

For formal longitudinal studies, add stack-appropriate static dependency/complexity tooling and freeze thresholds before the experiment.
