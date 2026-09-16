# External Benchmark Strategy

The framework should not reinvent every benchmark.

## Security generation

**BaxBench** is useful because it evaluates backend functionality and actual exploitability rather than equating functional tests with security.

**SecureAgentBench** and **SecRepoBench** add repository-level secure-change pressure.

## Fresh issue resolution

**SWE-bench-Live** and **SWE-rebench** are preferred over relying exclusively on old static SWE-bench tasks when studying contemporary agents, because freshness and contamination are explicit concerns.

## Vulnerability detection calibration

**OWASP Benchmark** and **NIST SARD** can help calibrate SAST/DAST/repair tooling. They are not substitutes for production threat models.

## Evaluation-integrity research

**METR MALT** and reward-hacking reports inform transcript monitoring and scorer hardening.

## Supply-chain/repository posture

**OpenSSF Scorecard** is an external signal, not a replacement for the framework's control assessment.

## Licensing

Do not copy third-party datasets into this repository merely because the benchmark is open source. Check:
- code license;
- task/data license;
- original repository licenses;
- redistribution conditions;
- exploit/test-data conditions.

The registry intentionally uses `VERIFY UPSTREAM` when current terms have not been confirmed.
