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
test_auto_mode_falls_back_to_sanitized_subprocess_in_permissive_mode (test_harness_isolation.HarnessIsolationTests.test_auto_mode_falls_back_to_sanitized_subprocess_in_permissive_mode) ... ok
test_docker_runner_selected_when_docker_is_available (test_harness_isolation.HarnessIsolationTests.test_docker_runner_selected_when_docker_is_available) ... ok
test_fail_closed_container_mode_when_docker_unavailable (test_harness_isolation.HarnessIsolationTests.test_fail_closed_container_mode_when_docker_unavailable) ... ok
test_harness_evaluate_records_isolation_metadata (test_harness_isolation.HarnessIsolationTests.test_harness_evaluate_records_isolation_metadata) ... ok
test_sanitize_environment_filters_secrets (test_harness_isolation.HarnessIsolationTests.test_sanitize_environment_filters_secrets) ... ok
test_sanitized_subprocess_does_not_leak_host_secrets_to_tests (test_harness_isolation.HarnessIsolationTests.test_sanitized_subprocess_does_not_leak_host_secrets_to_tests) ... ok
test_sanitized_subprocess_timeout_termination (test_harness_isolation.HarnessIsolationTests.test_sanitized_subprocess_timeout_termination) ... ok
test_strict_mode_fails_closed_when_docker_unavailable (test_harness_isolation.HarnessIsolationTests.test_strict_mode_fails_closed_when_docker_unavailable) ... ok
test_file_count_budget_fails_closed (test_security_boundaries.TestArchitectureBudget.test_file_count_budget_fails_closed) ... ok
test_oversized_source_fails_closed (test_security_boundaries.TestArchitectureBudget.test_oversized_source_fails_closed) ... ok
test_pattern_cannot_escape_target_root (test_security_boundaries.TestArchitectureBudget.test_pattern_cannot_escape_target_root) ... ok
test_repository_fsmonitor_is_not_executed (test_security_boundaries.TestGitExecutionBoundary.test_repository_fsmonitor_is_not_executed) ... ok
test_stats_include_staged_unstaged_and_untracked (test_security_boundaries.TestGitExecutionBoundary.test_stats_include_staged_unstaged_and_untracked) ... ok
test_direct_oversized_message_is_rejected (test_security_boundaries.TestMCPFraming.test_direct_oversized_message_is_rejected) ... ok
test_non_object_message_is_invalid_request (test_security_boundaries.TestMCPFraming.test_non_object_message_is_invalid_request) ... ok
test_non_object_params_is_invalid_request (test_security_boundaries.TestMCPFraming.test_non_object_params_is_invalid_request) ... ok
test_server_drains_oversized_frame_and_recovers (test_security_boundaries.TestMCPFraming.test_server_drains_oversized_frame_and_recovers) ... ok
test_oversized_requirements_file_fails_closed (test_security_boundaries.TestRequirementsBudget.test_oversized_requirements_file_fails_closed) ... ok
test_package_count_budget_fails_closed (test_security_boundaries.TestRequirementsBudget.test_package_count_budget_fails_closed) ... ok
test_total_deadline_fails_closed (test_security_boundaries.TestRequirementsBudget.test_total_deadline_fails_closed) ... ok
test_clean_domain_passes (test_v2_governance.TestArchitectureLinter.test_clean_domain_passes) ... ok
test_forbidden_import_detected (test_v2_governance.TestArchitectureLinter.test_forbidden_import_detected) ... ok
test_full_project_check_with_contract (test_v2_governance.TestArchitectureLinter.test_full_project_check_with_contract) ... ok
test_max_file_lines_rule (test_v2_governance.TestArchitectureLinter.test_max_file_lines_rule) ... ok
test_whitelist_not_allowed_import (test_v2_governance.TestArchitectureLinter.test_whitelist_not_allowed_import) ... ok
test_wildcard_import_forbidden (test_v2_governance.TestArchitectureLinter.test_wildcard_import_forbidden) ... ok
test_assess_invalid_profile_fails_gracefully (test_v2_governance.TestAssessEngine.test_assess_invalid_profile_fails_gracefully) ... ok
test_assess_nonexistent_file (test_v2_governance.TestAssessEngine.test_assess_nonexistent_file) ... ok
test_assess_pass_without_evidence_rejected (test_v2_governance.TestAssessEngine.test_assess_pass_without_evidence_rejected) ... ok
test_assess_valid_al2_data (test_v2_governance.TestAssessEngine.test_assess_valid_al2_data) ... ok
test_mcp_initialize (test_v2_governance.TestAssuranceMCPServer.test_mcp_initialize) ... ok
test_mcp_tools_call_verify_dependency_stdlib (test_v2_governance.TestAssuranceMCPServer.test_mcp_tools_call_verify_dependency_stdlib) ... ok
test_mcp_tools_list (test_v2_governance.TestAssuranceMCPServer.test_mcp_tools_list) ... ok
test_mcp_unknown_method_error (test_v2_governance.TestAssuranceMCPServer.test_mcp_unknown_method_error) ... ok
test_schema_json_syntax (test_v2_governance.TestContractsSchemaAndTemplate.test_schema_json_syntax) ... ok
test_template_json_syntax (test_v2_governance.TestContractsSchemaAndTemplate.test_template_json_syntax) ... ok
test_prepare_refuses_protected_repo_subdir (test_v2_governance.TestHarnessSafety.test_prepare_refuses_protected_repo_subdir) ... ok
test_prepare_refuses_repository_or_root_destination (test_v2_governance.TestHarnessSafety.test_prepare_refuses_repository_or_root_destination) ... ok
test_hallucinated_package_detected (test_v2_governance.TestSupplyChainVerification.test_hallucinated_package_detected) ... ok
test_nonexistent_version_detected (test_v2_governance.TestSupplyChainVerification.test_nonexistent_version_detected) ... ok
test_parse_requirements_file (test_v2_governance.TestSupplyChainVerification.test_parse_requirements_file) ... ok
test_stdlib_collision_detected (test_v2_governance.TestSupplyChainVerification.test_stdlib_collision_detected) ... ok
test_verified_package_success (test_v2_governance.TestSupplyChainVerification.test_verified_package_success) ... ok
test_excessive_churn_warning (test_v2_governance.TestSurgicalDiff.test_excessive_churn_warning) ... ok
test_is_test_file (test_v2_governance.TestSurgicalDiff.test_is_test_file) ... ok
test_out_of_scope_change_detected (test_v2_governance.TestSurgicalDiff.test_out_of_scope_change_detected) ... ok
test_scope_matching (test_v2_governance.TestSurgicalDiff.test_scope_matching) ... ok
test_unauthorized_test_modification_blocked (test_v2_governance.TestSurgicalDiff.test_unauthorized_test_modification_blocked) ... ok
test_antigravity_operational_docs_do_not_require_historical_modes (test_validation_suite.ValidationSuiteTests.test_antigravity_operational_docs_do_not_require_historical_modes) ... ok
test_automated_scenarios_have_protected_tests (test_validation_suite.ValidationSuiteTests.test_automated_scenarios_have_protected_tests) ... ok
test_current_antigravity_metadata_schema (test_validation_suite.ValidationSuiteTests.test_current_antigravity_metadata_schema) ... ok
test_scenario_controls_exist (test_validation_suite.ValidationSuiteTests.test_scenario_controls_exist) ... ok
test_scenario_ids_unique (test_validation_suite.ValidationSuiteTests.test_scenario_ids_unique) ... ok

----------------------------------------------------------------------
Ran 58 tests in 1.632s

OK
```

## Interpretation

The package is structurally consistent, the public seeded scenarios and reference solutions validate as intended, and the current Antigravity IDE compatibility guards pass. This does not yet constitute empirical proof of framework effectiveness.
