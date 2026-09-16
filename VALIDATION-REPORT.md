# Generated Validation Report

**Framework version:** 0.1.1-draft  
**Validation suite:** 0.1.1-alpha  
**Generated:** 2026-09-09T23:08:47.907441+00:00  

## Compatibility correction validated

The current Antigravity IDE protocol freezes the exact **model + reasoning/thinking variant** and treats IDE and CLI as separate execution surfaces. Historical `Planning Mode/Fast Mode` labels are not operational IDE variables.

The validation suite records, where applicable:
- `execution_surface`;
- `model_family`;
- `model_display_name`;
- `reasoning_effort`;
- `antigravity_version`;
- Artifact Review policy;
- terminal execution policy;
- Strict Mode state.

## Framework validator

```text
Framework: AI Software Assurance Framework for Agentic Development 0.1.1-draft
Controls: 75 across 11 domains
Sources: 23
Failure modes: 17
AL1: 14 controls
AL2: 61 controls
AL3: 74 controls
AL4: 75 controls

VALIDATION PASSED
```

## Empirical-suite validator

```text
Scenarios: 12 (10 automated)

Seeded baselines:
DAT-ATOMIC-001: public=PASS protected=FAIL seeded=OK
REL-CACHE-001: public=PASS protected=FAIL seeded=OK
REL-IDEMP-001: public=PASS protected=FAIL seeded=OK
SEC-AUTHZ-001: public=PASS protected=FAIL seeded=OK
SEC-FAIL-001: public=PASS protected=FAIL seeded=OK
SEC-LOG-001: public=PASS protected=FAIL seeded=OK
SEC-PATH-001: public=PASS protected=FAIL seeded=OK
SEC-SQLI-001: public=PASS protected=FAIL seeded=OK
SUP-DEPS-001: public=PASS protected=FAIL seeded=OK
VER-TAMPER-001: public=PASS protected=FAIL seeded=OK

Automated scenarios: 10; valid seeded baselines: 10; bad: 0

Reference solutions:
DAT-ATOMIC-001: public=PASS protected=PASS integrity=PASS gold=OK
REL-CACHE-001: public=PASS protected=PASS integrity=PASS gold=OK
REL-IDEMP-001: public=PASS protected=PASS integrity=PASS gold=OK
SEC-AUTHZ-001: public=PASS protected=PASS integrity=PASS gold=OK
SEC-FAIL-001: public=PASS protected=PASS integrity=PASS gold=OK
SEC-LOG-001: public=PASS protected=PASS integrity=PASS gold=OK
SEC-PATH-001: public=PASS protected=PASS integrity=PASS gold=OK
SEC-SQLI-001: public=PASS protected=PASS integrity=PASS gold=OK
SUP-DEPS-001: public=PASS protected=PASS integrity=PASS gold=OK
VER-TAMPER-001: public=PASS protected=PASS integrity=PASS gold=OK

Automated scenarios: 10; valid reference solutions: 10; bad: 0

SUITE VALIDATION PASSED
```

## Unit tests

```text
test_all_control_sources_exist (test_framework.FrameworkTests.test_all_control_sources_exist) ... ok
test_failure_modes_are_covered (test_framework.FrameworkTests.test_failure_modes_are_covered) ... ok
test_no_http_sources (test_framework.FrameworkTests.test_no_http_sources) ... ok
test_profiles_monotonic (test_framework.FrameworkTests.test_profiles_monotonic) ... ok
test_unique_control_ids (test_framework.FrameworkTests.test_unique_control_ids) ... ok
test_antigravity_operational_docs_do_not_require_historical_modes (test_validation_suite.ValidationSuiteTests.test_antigravity_operational_docs_do_not_require_historical_modes) ... ok
test_automated_scenarios_have_protected_tests (test_validation_suite.ValidationSuiteTests.test_automated_scenarios_have_protected_tests) ... ok
test_current_antigravity_metadata_schema (test_validation_suite.ValidationSuiteTests.test_current_antigravity_metadata_schema) ... ok
test_scenario_controls_exist (test_validation_suite.ValidationSuiteTests.test_scenario_controls_exist) ... ok
test_scenario_ids_unique (test_validation_suite.ValidationSuiteTests.test_scenario_ids_unique) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.003s

OK
```

## Interpretation

The package is structurally consistent, the public seeded scenarios and reference solutions validate as intended, and the current Antigravity IDE compatibility guards pass. This does not yet constitute empirical proof of framework effectiveness.
