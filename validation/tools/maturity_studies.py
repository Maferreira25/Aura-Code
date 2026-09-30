#!/usr/bin/env python3
"""Validation primitives for AuraCode maturity studies P2/P3/P4 and reviewer agreement."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from validation.tools.maturity_claims import (
    validate_governance_1_0,
    validate_independent_security_audit,
    validate_multilang_qualification,
)

ARMS = ("A0", "A1", "A2")
RATING_VALUES = ("PASS", "FAIL", "NOT_APPLICABLE")


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to read {path}: {exc}")
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def _nonempty_list(value: object) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def validate_p2_plan(data: Mapping[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    study_id = str(data.get("study_id", "")).strip()
    if not study_id:
        errors.append("study_id is required")
    if not bool(data.get("preregistered")):
        errors.append("preregistered must be true before formal P2 execution")
    if not bool(data.get("private_or_fresh_split")):
        errors.append("private_or_fresh_split must be true")

    arms = tuple(str(x) for x in _nonempty_list(data.get("arms")))
    if arms != ARMS:
        errors.append("arms must be exactly A0, A1, A2 in canonical order")

    scenarios = _nonempty_list(data.get("scenarios"))
    if len(scenarios) < 30:
        errors.append(f"P2 requires at least 30 scenarios; found {len(scenarios)}")
    scenario_ids = [str(x.get("id", "")).strip() for x in scenarios if isinstance(x, dict)]
    if len(scenario_ids) != len(scenarios) or any(not x for x in scenario_ids):
        errors.append("every P2 scenario requires a non-empty id")
    if len(set(scenario_ids)) != len(scenario_ids):
        errors.append("P2 scenario ids must be unique")

    families = {
        str(x.get("family", "")).strip()
        for x in scenarios
        if isinstance(x, dict) and str(x.get("family", "")).strip()
    }
    required_families = {
        "security",
        "data-integrity",
        "supply-chain",
        "evaluator-integrity",
        "architecture",
        "reliability",
    }
    missing_families = sorted(required_families - families)
    if missing_families:
        errors.append("missing required P2 scenario families: " + ", ".join(missing_families))

    repetitions = data.get("repetitions_per_arm")
    if not isinstance(repetitions, int) or repetitions < 5:
        errors.append("repetitions_per_arm must be an integer >= 5")

    commitment = str(data.get("private_split_commitment_sha256", "")).strip().lower()
    if len(commitment) != 64 or any(c not in "0123456789abcdef" for c in commitment):
        errors.append("private_split_commitment_sha256 must be a 64-character SHA-256 hex digest")

    pairings = _nonempty_list(data.get("model_agent_pairings"))
    if not pairings:
        errors.append("at least one model_agent_pairing is required")
    for index, pairing in enumerate(pairings):
        if not isinstance(pairing, dict):
            errors.append(f"model_agent_pairings[{index}] must be an object")
            continue
        for field in ("model_family", "model_display_name", "agent", "reasoning_effort"):
            if not str(pairing.get(field, "")).strip():
                errors.append(f"model_agent_pairings[{index}].{field} is required")

    if "results" in data or "outcomes" in data:
        warnings.append("preregistration contains result-like fields; verify it was frozen before outcome collection")

    expected_attempts = (
        len(scenarios) * len(ARMS) * repetitions * len(pairings)
        if isinstance(repetitions, int) and repetitions > 0
        else 0
    )
    return {
        "study": "P2",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "warnings": warnings,
        "scenario_count": len(scenarios),
        "pairing_count": len(pairings),
        "expected_attempts": expected_attempts,
    }



def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pairing_key(item: Mapping[str, Any]) -> Tuple[str, str, str]:
    return (
        str(item.get("model_display_name", "")).strip(),
        str(item.get("agent", "")).strip(),
        str(item.get("reasoning_effort", "")).strip(),
    )


def validate_p2_result(data: Mapping[str, Any], root: Optional[Path] = None) -> Dict[str, Any]:
    """Validate a completed P2 package against its frozen preregistration."""
    errors: List[str] = []
    warnings: List[str] = []
    if str(data.get("study", "")).upper() != "P2":
        errors.append("study must be P2")
    if not bool(data.get("preregistered")):
        errors.append("preregistered must be true")
    if not bool(data.get("private_or_fresh_split")):
        errors.append("private_or_fresh_split must be true")

    preregistration_path = str(data.get("preregistration_path", "")).strip()
    preregistration_sha = str(data.get("preregistration_sha256", "")).lower().strip()
    if not preregistration_path:
        errors.append("preregistration_path is required")
    if len(preregistration_sha) != 64 or any(ch not in "0123456789abcdef" for ch in preregistration_sha):
        errors.append("preregistration_sha256 must be a 64-character SHA-256 hex digest")

    split_commitment = str(data.get("private_split_commitment_sha256", "")).lower().strip()
    if len(split_commitment) != 64 or any(ch not in "0123456789abcdef" for ch in split_commitment):
        errors.append("private_split_commitment_sha256 must be a 64-character SHA-256 hex digest")

    plan: Optional[Dict[str, Any]] = None
    if root is not None and preregistration_path:
        root_resolved = root.resolve()
        raw_path = Path(preregistration_path)
        if raw_path.is_absolute():
            errors.append("preregistration_path must be repository-relative")
        else:
            plan_path = (root_resolved / raw_path).resolve()
            try:
                plan_path.relative_to(root_resolved)
            except ValueError:
                errors.append("preregistration_path escapes repository root")
            else:
                if not plan_path.is_file():
                    errors.append("preregistration file does not exist")
                else:
                    actual_sha = _sha256_file(plan_path)
                    if actual_sha != preregistration_sha:
                        errors.append(
                            f"preregistration hash mismatch: expected {preregistration_sha}, got {actual_sha}"
                        )
                    try:
                        plan = _read_json(plan_path)
                    except ValueError as exc:
                        errors.append(str(exc))
                    if plan is not None:
                        plan_check = validate_p2_plan(plan)
                        if plan_check["status"] != "VALID":
                            errors.append("referenced P2 preregistration is invalid: " + "; ".join(plan_check["errors"]))
                        if str(plan.get("private_split_commitment_sha256", "")).lower() != split_commitment:
                            errors.append("private split commitment does not match preregistration")

    runs = _nonempty_list(data.get("runs"))
    if not runs:
        errors.append("P2 result requires runs")
    ids: List[str] = []
    by_arm: Dict[str, int] = {arm: 0 for arm in ARMS}
    observed_scenarios = set()
    observed_pairings = set()
    coverage: Counter[Tuple[str, Tuple[str, str, str], str]] = Counter()
    invalid_qs: List[str] = []

    for index, row in enumerate(runs):
        if not isinstance(row, dict):
            errors.append(f"runs[{index}] must be an object")
            continue
        run_id = str(row.get("run_id", "")).strip()
        arm = str(row.get("arm", "")).strip()
        scenario_id = str(row.get("scenario_id", "")).strip()
        pairing = _pairing_key(row)
        if not run_id or arm not in ARMS or not scenario_id or not all(pairing):
            errors.append(f"runs[{index}] missing required provenance")
            continue
        ids.append(run_id)
        by_arm[arm] += 1
        observed_scenarios.add(scenario_id)
        observed_pairings.add(pairing)
        coverage[(scenario_id, pairing, arm)] += 1

        required = ("public_tests_passed", "protected_tests_passed", "evaluator_integrity")
        if all(isinstance(row.get(key), bool) for key in required):
            expected_qs = all(bool(row.get(key)) for key in required)
            if bool(row.get("qualified_success")) != expected_qs:
                invalid_qs.append(run_id)
        elif not isinstance(row.get("qualified_success"), bool):
            errors.append(f"{run_id}: qualified_success must be boolean")

    if len(ids) != len(set(ids)):
        errors.append("P2 run_id values must be unique")
    if invalid_qs:
        errors.append("Qualified Success formula mismatch: " + ", ".join(sorted(invalid_qs)))
    if len(observed_scenarios) < 30:
        errors.append(f"P2 result requires >=30 scenarios; found {len(observed_scenarios)}")
    for arm in ARMS:
        if by_arm[arm] == 0:
            errors.append(f"P2 result has no runs for arm {arm}")

    declared_repetitions = data.get("repetitions_per_arm")
    if not isinstance(declared_repetitions, int) or declared_repetitions < 5:
        errors.append("repetitions_per_arm must be an integer >= 5")
    declared_pairings_raw = _nonempty_list(data.get("model_agent_pairings"))
    declared_pairings = {
        _pairing_key(item)
        for item in declared_pairings_raw
        if isinstance(item, dict) and all(_pairing_key(item))
    }
    if not declared_pairings:
        errors.append("model_agent_pairings must contain at least one complete pairing")

    declared_scenarios = {
        str(item.get("id", "")).strip()
        for item in _nonempty_list(data.get("scenarios"))
        if isinstance(item, dict) and str(item.get("id", "")).strip()
    }
    if len(declared_scenarios) < 30:
        errors.append("result scenarios must contain at least 30 scenario ids")

    if plan is not None:
        plan_scenarios = {
            str(item.get("id", "")).strip()
            for item in _nonempty_list(plan.get("scenarios"))
            if isinstance(item, dict) and str(item.get("id", "")).strip()
        }
        plan_pairings = {
            _pairing_key(item)
            for item in _nonempty_list(plan.get("model_agent_pairings"))
            if isinstance(item, dict) and all(_pairing_key(item))
        }
        plan_repetitions = plan.get("repetitions_per_arm")
        if declared_scenarios != plan_scenarios:
            errors.append("result scenario set differs from preregistration")
        if declared_pairings != plan_pairings:
            errors.append("result model/agent pairings differ from preregistration")
        if declared_repetitions != plan_repetitions:
            errors.append("result repetition count differs from preregistration")

    expected_attempts = 0
    if isinstance(declared_repetitions, int) and declared_repetitions > 0:
        expected_attempts = (
            len(declared_scenarios)
            * len(ARMS)
            * declared_repetitions
            * len(declared_pairings)
        )
    declared_expected = data.get("expected_attempts")
    if declared_expected != expected_attempts or expected_attempts <= 0:
        errors.append(
            f"expected_attempts must equal frozen design size {expected_attempts}; got {declared_expected}"
        )
    if expected_attempts and len(runs) != expected_attempts:
        errors.append(f"P2 incomplete: observed {len(runs)}/{expected_attempts} attempts")

    if expected_attempts:
        for scenario_id in sorted(declared_scenarios):
            for pairing in sorted(declared_pairings):
                for arm in ARMS:
                    observed = coverage[(scenario_id, pairing, arm)]
                    if observed != declared_repetitions:
                        errors.append(
                            f"incomplete cell {scenario_id}/{pairing[0]}/{pairing[1]}/{pairing[2]}/{arm}: "
                            f"{observed}/{declared_repetitions}"
                        )

    unexpected_scenarios = observed_scenarios - declared_scenarios
    if unexpected_scenarios:
        errors.append("runs contain undeclared scenarios: " + ", ".join(sorted(unexpected_scenarios)))
    unexpected_pairings = observed_pairings - declared_pairings
    if unexpected_pairings:
        errors.append("runs contain undeclared model/agent pairings")

    completed = bool(data.get("completed"))
    if not completed:
        errors.append("completed must be true for a formal P2 result")

    return {
        "study": "P2_RESULT",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "warnings": warnings,
        "completed": completed and not errors,
        "run_count": len(runs),
        "scenario_count": len(observed_scenarios),
        "pairing_count": len(observed_pairings),
        "expected_attempts": expected_attempts,
        "by_arm": by_arm,
    }


def validate_p3_plan(data: Mapping[str, Any], benchmark_registry: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate a frozen external/ecological P3 plan before outcome collection."""
    errors: List[str] = []
    warnings: List[str] = []
    if not str(data.get("study_id", "")).strip():
        errors.append("study_id is required")
    if not bool(data.get("preregistered")):
        errors.append("preregistered must be true before P3 execution")
    arms = tuple(str(x) for x in _nonempty_list(data.get("arms")))
    if arms != ARMS:
        errors.append("arms must be exactly A0, A1, A2 in canonical order")

    known = {
        str(item.get("id", "")): item
        for item in _nonempty_list(benchmark_registry.get("benchmarks"))
        if isinstance(item, dict) and str(item.get("id", "")).strip()
    }
    selections = _nonempty_list(data.get("benchmarks"))
    if not selections:
        errors.append("at least one external benchmark must be selected")

    seen = set()
    for index, selected in enumerate(selections):
        if not isinstance(selected, dict):
            errors.append(f"benchmarks[{index}] must be an object")
            continue
        benchmark_id = str(selected.get("id", "")).strip()
        if benchmark_id not in known:
            errors.append(f"unknown benchmark id: {benchmark_id or '<empty>'}")
            continue
        if benchmark_id in seen:
            errors.append(f"duplicate benchmark id: {benchmark_id}")
        seen.add(benchmark_id)
        if not bool(selected.get("license_verified")):
            errors.append(f"{benchmark_id}: license_verified must be true for formal execution")
        if not str(selected.get("upstream_revision", "")).strip():
            errors.append(f"{benchmark_id}: upstream_revision is required")
        commitment = str(selected.get("task_subset_commitment_sha256", "")).strip().lower()
        if len(commitment) != 64 or any(ch not in "0123456789abcdef" for ch in commitment):
            errors.append(f"{benchmark_id}: task_subset_commitment_sha256 must be 64 hex characters")
        attempts = selected.get("attempts_per_arm")
        if not isinstance(attempts, int) or attempts <= 0:
            errors.append(f"{benchmark_id}: attempts_per_arm must be a positive integer")

    pairing = data.get("model_agent_pairing")
    if not isinstance(pairing, dict) or not all(_pairing_key(pairing)):
        errors.append("model_agent_pairing with model_display_name, agent, reasoning_effort is required")

    if data.get("combine_heterogeneous_scores") is True:
        errors.append("heterogeneous benchmark scores must not be collapsed into one composite score")
    if len(selections) == 1:
        warnings.append("single benchmark family limits ecological validity")

    return {
        "study": "P3",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "warnings": warnings,
        "benchmark_count": len(selections),
    }


def validate_p3_result(
    data: Mapping[str, Any],
    benchmark_registry: Mapping[str, Any],
    root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Validate completed ecological evidence against a frozen P3 preregistration."""
    errors: List[str] = []
    known = {
        str(item.get("id", "")): item
        for item in _nonempty_list(benchmark_registry.get("benchmarks"))
        if isinstance(item, dict) and str(item.get("id", "")).strip()
    }
    if str(data.get("study", "")).upper() != "P3":
        errors.append("study must be P3")
    if not bool(data.get("preregistered")):
        errors.append("preregistered must be true")

    prereg_path = str(data.get("preregistration_path", "")).strip()
    prereg_sha = str(data.get("preregistration_sha256", "")).strip().lower()
    if not prereg_path:
        errors.append("preregistration_path is required")
    if len(prereg_sha) != 64 or any(ch not in "0123456789abcdef" for ch in prereg_sha):
        errors.append("preregistration_sha256 must be 64 hex characters")

    plan: Optional[Dict[str, Any]] = None
    if root is not None and prereg_path:
        root_resolved = root.resolve()
        raw = Path(prereg_path)
        if raw.is_absolute():
            errors.append("preregistration_path must be repository-relative")
        else:
            plan_path = (root_resolved / raw).resolve()
            try:
                plan_path.relative_to(root_resolved)
            except ValueError:
                errors.append("preregistration_path escapes repository root")
            else:
                if not plan_path.is_file():
                    errors.append("P3 preregistration file does not exist")
                else:
                    actual = _sha256_file(plan_path)
                    if actual != prereg_sha:
                        errors.append(f"preregistration hash mismatch: expected {prereg_sha}, got {actual}")
                    try:
                        plan = _read_json(plan_path)
                    except ValueError as exc:
                        errors.append(str(exc))
                    if plan is not None:
                        plan_check = validate_p3_plan(plan, benchmark_registry)
                        if plan_check["status"] != "VALID":
                            errors.append("referenced P3 preregistration is invalid: " + "; ".join(plan_check["errors"]))

    results = _nonempty_list(data.get("benchmarks"))
    if not results:
        errors.append("P3 result requires benchmark results")

    seen = set()
    result_map: Dict[str, Mapping[str, Any]] = {}
    for index, item in enumerate(results):
        if not isinstance(item, dict):
            errors.append(f"benchmarks[{index}] must be an object")
            continue
        bid = str(item.get("id", "")).strip()
        if bid not in known:
            errors.append(f"unknown benchmark id: {bid or '<empty>'}")
            continue
        if bid in seen:
            errors.append(f"duplicate benchmark result: {bid}")
        seen.add(bid)
        result_map[bid] = item

        if not bool(item.get("license_verified")):
            errors.append(f"{bid}: license_verified must be true")
        if not str(item.get("upstream_revision", "")).strip():
            errors.append(f"{bid}: upstream_revision is required")
        commitment = str(item.get("task_subset_commitment_sha256", "")).strip().lower()
        if len(commitment) != 64 or any(ch not in "0123456789abcdef" for ch in commitment):
            errors.append(f"{bid}: task_subset_commitment_sha256 must be 64 hex characters")
        if not bool(item.get("completed")):
            errors.append(f"{bid}: completed must be true")

        arms = item.get("arms")
        if not isinstance(arms, dict):
            errors.append(f"{bid}: results must report A0/A1/A2 separately")
        else:
            for arm in ARMS:
                arm_result = arms.get(arm)
                if not isinstance(arm_result, dict):
                    errors.append(f"{bid}: missing {arm} result")
                    continue
                attempts = arm_result.get("attempts")
                successes = arm_result.get("qualified_successes")
                if not isinstance(attempts, int) or attempts <= 0:
                    errors.append(f"{bid}/{arm}: attempts must be positive integer")
                if not isinstance(successes, int) or successes < 0:
                    errors.append(f"{bid}/{arm}: qualified_successes must be non-negative integer")
                elif isinstance(attempts, int) and successes > attempts:
                    errors.append(f"{bid}/{arm}: qualified_successes cannot exceed attempts")

    if data.get("combined_score") is not None:
        errors.append("P3 must not collapse heterogeneous benchmarks into one combined_score")
    if len(seen) < 2:
        errors.append("P3 maturity evidence requires at least two distinct benchmark families")

    result_pairing = data.get("model_agent_pairing")
    if not isinstance(result_pairing, dict) or not all(_pairing_key(result_pairing)):
        errors.append("model_agent_pairing provenance is required")

    if plan is not None:
        plan_items = {
            str(item.get("id", "")).strip(): item
            for item in _nonempty_list(plan.get("benchmarks"))
            if isinstance(item, dict) and str(item.get("id", "")).strip()
        }
        if set(result_map) != set(plan_items):
            errors.append("P3 result benchmark set differs from preregistration")
        if _pairing_key(result_pairing if isinstance(result_pairing, dict) else {}) != _pairing_key(
            plan.get("model_agent_pairing") if isinstance(plan.get("model_agent_pairing"), dict) else {}
        ):
            errors.append("P3 result model/agent pairing differs from preregistration")

        for bid, planned in plan_items.items():
            actual = result_map.get(bid)
            if not isinstance(actual, dict):
                continue
            for field in ("upstream_revision", "task_subset_commitment_sha256"):
                if str(actual.get(field, "")).strip() != str(planned.get(field, "")).strip():
                    errors.append(f"{bid}: {field} differs from preregistration")
            if bool(actual.get("license_verified")) != bool(planned.get("license_verified")):
                errors.append(f"{bid}: license verification differs from preregistration")
            required_attempts = planned.get("attempts_per_arm")
            arms = actual.get("arms")
            if isinstance(arms, dict) and isinstance(required_attempts, int):
                for arm in ARMS:
                    arm_result = arms.get(arm)
                    if isinstance(arm_result, dict) and arm_result.get("attempts") != required_attempts:
                        errors.append(
                            f"{bid}/{arm}: attempts {arm_result.get('attempts')} != preregistered {required_attempts}"
                        )

    return {
        "study": "P3_RESULT",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "completed": not errors,
        "benchmark_count": len(seen),
    }


def _validate_success_criteria(name: str, value: object, errors: List[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{name} acceptance criteria must be an object")
        return
    text = str(value.get("success_criteria", "")).strip()
    if not text:
        errors.append(f"{name}.success_criteria is required")


def validate_p4_plan(data: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate a frozen operational-validation plan before execution."""
    errors: List[str] = []
    if not str(data.get("study_id", "")).strip():
        errors.append("study_id is required")
    if not bool(data.get("preregistered")):
        errors.append("preregistered must be true")
    if not str(data.get("service_id", "")).strip():
        errors.append("service_id is required")
    if not str(data.get("revision", "")).strip():
        errors.append("revision is required")
    if not str(data.get("environment", "")).strip():
        errors.append("environment is required")

    criteria = data.get("acceptance_criteria")
    if not isinstance(criteria, dict):
        errors.append("acceptance_criteria object is required")
        criteria = {}
    for field in ("load", "soak", "rollback", "recovery", "observability"):
        _validate_success_criteria(field, criteria.get(field), errors)

    load = criteria.get("load")
    if isinstance(load, dict):
        target = load.get("target_rps")
        duration = load.get("duration_minutes")
        if not isinstance(target, (int, float)) or isinstance(target, bool) or target <= 0:
            errors.append("load.target_rps must be > 0")
        if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration <= 0:
            errors.append("load.duration_minutes must be > 0")

    soak = criteria.get("soak")
    if isinstance(soak, dict):
        duration = soak.get("duration_minutes")
        if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration <= 0:
            errors.append("soak.duration_minutes must be > 0")

    return {
        "study": "P4_PLAN",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
    }


def _check_operational_dimension(name: str, value: object, errors: List[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return
    status = str(value.get("status", "")).upper()
    if status != "PASS":
        errors.append(f"{name}.status must be PASS for stable-maturity evidence")
    evidence = _nonempty_list(value.get("evidence"))
    if not any(str(item).strip() for item in evidence):
        errors.append(f"{name}.evidence requires at least one artifact")


def validate_p4_result(data: Mapping[str, Any], root: Optional[Path] = None) -> Dict[str, Any]:
    """Validate successful P4 evidence against its frozen operational plan."""
    errors: List[str] = []
    if str(data.get("study", "")).upper() != "P4":
        errors.append("study must be P4")
    if not bool(data.get("preregistered")):
        errors.append("preregistered must be true")

    prereg_path = str(data.get("preregistration_path", "")).strip()
    prereg_sha = str(data.get("preregistration_sha256", "")).strip().lower()
    if not prereg_path:
        errors.append("preregistration_path is required")
    if len(prereg_sha) != 64 or any(ch not in "0123456789abcdef" for ch in prereg_sha):
        errors.append("preregistration_sha256 must be 64 hex characters")

    plan: Optional[Dict[str, Any]] = None
    if root is not None and prereg_path:
        root_resolved = root.resolve()
        raw = Path(prereg_path)
        if raw.is_absolute():
            errors.append("preregistration_path must be repository-relative")
        else:
            plan_path = (root_resolved / raw).resolve()
            try:
                plan_path.relative_to(root_resolved)
            except ValueError:
                errors.append("preregistration_path escapes repository root")
            else:
                if not plan_path.is_file():
                    errors.append("P4 preregistration file does not exist")
                else:
                    actual_sha = _sha256_file(plan_path)
                    if actual_sha != prereg_sha:
                        errors.append(f"preregistration hash mismatch: expected {prereg_sha}, got {actual_sha}")
                    try:
                        plan = _read_json(plan_path)
                    except ValueError as exc:
                        errors.append(str(exc))
                    if plan is not None:
                        plan_check = validate_p4_plan(plan)
                        if plan_check["status"] != "VALID":
                            errors.append("referenced P4 plan is invalid: " + "; ".join(plan_check["errors"]))

    if not str(data.get("service_id", "")).strip():
        errors.append("service_id is required")
    if not str(data.get("revision", "")).strip():
        errors.append("revision is required")
    if not str(data.get("environment", "")).strip():
        errors.append("environment is required")

    for field in ("load", "soak", "rollback", "recovery", "observability"):
        _check_operational_dimension(field, data.get(field), errors)

    if plan is not None:
        for field in ("service_id", "revision", "environment"):
            if str(data.get(field, "")).strip() != str(plan.get(field, "")).strip():
                errors.append(f"{field} differs from preregistration")
        criteria = plan.get("acceptance_criteria")
        if isinstance(criteria, dict):
            planned_load = criteria.get("load")
            result_load = data.get("load")
            if isinstance(planned_load, dict) and isinstance(result_load, dict):
                if result_load.get("target_rps") != planned_load.get("target_rps"):
                    errors.append("load.target_rps differs from preregistration")
                if result_load.get("duration_minutes") != planned_load.get("duration_minutes"):
                    errors.append("load.duration_minutes differs from preregistration")
            planned_soak = criteria.get("soak")
            result_soak = data.get("soak")
            if isinstance(planned_soak, dict) and isinstance(result_soak, dict):
                if result_soak.get("duration_minutes") != planned_soak.get("duration_minutes"):
                    errors.append("soak.duration_minutes differs from preregistration")

    return {
        "study": "P4_RESULT",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "operational_complete": not errors,
    }


def cohen_kappa(left: Sequence[str], right: Sequence[str]) -> float:
    if len(left) != len(right):
        raise ValueError("rating vectors must have the same length")
    if not left:
        raise ValueError("at least one paired rating is required")
    for rating in list(left) + list(right):
        if rating not in RATING_VALUES:
            raise ValueError(f"unsupported rating '{rating}'")
    observed = sum(a == b for a, b in zip(left, right)) / len(left)
    left_counts = Counter(left)
    right_counts = Counter(right)
    expected = sum(
        (left_counts[value] / len(left)) * (right_counts[value] / len(right))
        for value in RATING_VALUES
    )
    if math.isclose(expected, 1.0):
        return 1.0 if math.isclose(observed, 1.0) else 0.0
    return (observed - expected) / (1.0 - expected)


def analyze_inter_rater(data: Mapping[str, Any], root: Optional[Path] = None) -> Dict[str, Any]:
    """Analyze assessor agreement and enforce declared reviewer independence/coverage."""
    errors: List[str] = []
    assessors = _nonempty_list(data.get("assessors"))
    if len(assessors) < 2:
        errors.append("at least two independent assessors are required")
    ids: List[str] = []
    for index, assessor in enumerate(assessors):
        if not isinstance(assessor, dict):
            errors.append(f"assessors[{index}] must be an object")
            continue
        assessor_id = str(assessor.get("id", "")).strip()
        if not assessor_id:
            errors.append(f"assessors[{index}].id is required")
            continue
        ids.append(assessor_id)
        if not bool(assessor.get("independence_attestation")):
            errors.append(f"{assessor_id}: independence_attestation must be true")
        if bool(assessor.get("implementation_role")):
            errors.append(f"{assessor_id}: assessor must not have implementation_role in reviewed change")
    if len(set(ids)) != len(ids):
        errors.append("assessor ids must be unique")

    assurance_level = str(data.get("assurance_level", "")).upper()
    expected_controls_raw = _nonempty_list(data.get("control_ids"))
    expected_controls = {str(x).strip().upper() for x in expected_controls_raw if str(x).strip()}
    if not expected_controls:
        errors.append("control_ids must declare the independently rated control set")

    if root is not None and assurance_level:
        profile_path = root.resolve() / "profiles" / f"{assurance_level.lower()}.json"
        if not profile_path.is_file():
            errors.append(f"unknown assurance_level/profile: {assurance_level}")
        else:
            profile = _read_json(profile_path)
            profile_controls = {
                str(x).strip().upper()
                for x in _nonempty_list(profile.get("included_controls"))
                if str(x).strip()
            }
            if expected_controls != profile_controls:
                errors.append("control_ids must exactly match the selected assurance profile")
    elif assurance_level not in {"AL1", "AL2", "AL3", "AL4"}:
        errors.append("assurance_level must be AL1, AL2, AL3, or AL4")

    ratings = _nonempty_list(data.get("ratings"))
    paired: Dict[str, Dict[str, str]] = defaultdict(dict)
    for item in ratings:
        if not isinstance(item, dict):
            errors.append("each rating must be an object")
            continue
        control_id = str(item.get("control_id", "")).strip().upper()
        assessor_id = str(item.get("assessor_id", "")).strip()
        rating = str(item.get("rating", "")).upper()
        if not control_id or assessor_id not in ids or rating not in RATING_VALUES:
            errors.append(f"invalid rating record: {item}")
            continue
        key = (control_id, assessor_id)
        if assessor_id in paired[control_id]:
            errors.append(f"duplicate rating for {control_id}/{assessor_id}")
        paired[control_id][assessor_id] = rating

    for control_id in sorted(expected_controls):
        for assessor_id in ids:
            if assessor_id not in paired.get(control_id, {}):
                errors.append(f"missing rating for {control_id}/{assessor_id}")
    unexpected = set(paired) - expected_controls
    if unexpected:
        errors.append("ratings contain controls outside declared scope: " + ", ".join(sorted(unexpected)))

    kappa = None
    agreement = None
    paired_count = 0
    if len(ids) >= 2 and not errors:
        left_id, right_id = ids[0], ids[1]
        common = sorted(expected_controls)
        paired_count = len(common)
        left = [paired[cid][left_id] for cid in common]
        right = [paired[cid][right_id] for cid in common]
        agreement = sum(a == b for a, b in zip(left, right)) / paired_count
        kappa = cohen_kappa(left, right)

    return {
        "study": "INTER_RATER",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "assurance_level": assurance_level,
        "paired_controls": paired_count,
        "percent_agreement": agreement,
        "cohen_kappa": kappa,
        "claim_boundary": "Agreement metrics describe assessor consistency; they do not prove control correctness.",
    }


def validate_replication_result(data: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate MAT-03 replication evidence without asserting an effect size threshold."""
    errors: List[str] = []
    pairings = _nonempty_list(data.get("pairings"))
    if len(pairings) < 2:
        errors.append("replication requires at least two distinct model/agent pairings")
    identities = set()
    for index, item in enumerate(pairings):
        if not isinstance(item, dict):
            errors.append(f"pairings[{index}] must be an object")
            continue
        model = str(item.get("model_display_name", "")).strip()
        agent = str(item.get("agent", "")).strip()
        study_id = str(item.get("study_id", "")).strip()
        if not model or not agent or not study_id:
            errors.append(f"pairings[{index}] requires model_display_name, agent, and study_id")
            continue
        identities.add((model, agent))
        if not isinstance(item.get("a0_qs_rate"), (int, float)):
            errors.append(f"pairings[{index}].a0_qs_rate is required")
        if not isinstance(item.get("a2_qs_rate"), (int, float)):
            errors.append(f"pairings[{index}].a2_qs_rate is required")
        if not bool(item.get("completed")):
            errors.append(f"pairings[{index}].completed must be true")
    if len(identities) < 2:
        errors.append("replication requires at least two distinct model/agent identities")
    return {
        "study": "REPLICATION",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "pairing_count": len(identities),
        "claim_boundary": "This validator proves replication coverage, not that the replicated effect is positive or statistically significant.",
    }


def validate_burden_error_result(data: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate that burden plus false-positive/false-negative evidence was actually measured."""
    errors: List[str] = []
    rows = _nonempty_list(data.get("results"))
    burden = analyze_burden(rows)
    for arm in ARMS:
        if burden["by_arm"][arm]["runs"] == 0:
            errors.append(f"no burden runs for arm {arm}")
    for metric in ("elapsed_seconds", "human_interventions"):
        for arm in ARMS:
            observed = burden["by_arm"][arm]["metrics"][metric]["observed"]
            if observed == 0:
                errors.append(f"{metric} has no observations for arm {arm}")

    calibration = data.get("error_calibration")
    if not isinstance(calibration, dict):
        errors.append("error_calibration object is required")
    else:
        for field in ("true_positive", "true_negative", "false_positive", "false_negative"):
            value = calibration.get(field)
            if not isinstance(value, int) or value < 0:
                errors.append(f"error_calibration.{field} must be a non-negative integer")
        if not errors:
            total = sum(int(calibration[k]) for k in ("true_positive", "true_negative", "false_positive", "false_negative"))
            if total == 0:
                errors.append("error_calibration must contain at least one classified case")

    return {
        "study": "BURDEN_ERRORS",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "burden": burden,
        "claim_boundary": "Measurement completeness does not decide whether the observed burden or error rate is acceptable; acceptance thresholds must be preregistered.",
    }



def _number(row: Mapping[str, Any], name: str) -> Optional[float]:
    value = row.get(name)
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def analyze_burden(rows: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    metrics = ("elapsed_seconds", "input_tokens", "output_tokens", "tool_calls", "human_interventions", "cost_usd")
    materialized = [row for row in rows if str(row.get("arm", "")) in ARMS]
    by_arm: Dict[str, Dict[str, Any]] = {}
    for arm in ARMS:
        selected = [row for row in materialized if row.get("arm") == arm]
        arm_metrics: Dict[str, Any] = {}
        for metric in metrics:
            values = [value for row in selected if (value := _number(row, metric)) is not None]
            arm_metrics[metric] = {
                "observed": len(values),
                "missing": len(selected) - len(values),
                "mean": mean(values) if values else None,
                "median": median(values) if values else None,
            }
        by_arm[arm] = {"runs": len(selected), "metrics": arm_metrics}
    return {
        "study": "BURDEN",
        "status": "VALID",
        "total_runs": len(materialized),
        "by_arm": by_arm,
        "claim_boundary": "Missing burden fields remain missing; the analyzer never silently converts them to zero.",
    }



def validate_evidence_for_criterion(
    criterion_id: str,
    data: Mapping[str, Any],
    benchmark_registry: Optional[Mapping[str, Any]] = None,
    root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Dispatch maturity evidence to the semantic validator for its criterion."""
    cid = criterion_id.strip().upper()
    if cid == "MAT-02":
        return validate_p2_result(data, root=root)
    if cid == "MAT-03":
        return validate_replication_result(data)
    if cid == "MAT-04":
        if benchmark_registry is None:
            raise ValueError("MAT-04 validation requires benchmark registry")
        return validate_p3_result(data, benchmark_registry, root=root)
    if cid == "MAT-05":
        return validate_p4_result(data, root=root)
    if cid == "MAT-06":
        return analyze_inter_rater(data, root=root)
    if cid == "MAT-07":
        return validate_burden_error_result(data)
    if cid == "MAT-08":
        return validate_multilang_qualification(data)
    if cid == "MAT-09":
        return validate_independent_security_audit(data)
    if cid == "MAT-10":
        return validate_governance_1_0(data)
    raise ValueError(f"No semantic maturity validator for {cid}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AuraCode maturity-study validation toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("p2", "p2-result", "p4-plan", "p4", "inter-rater", "burden", "replication", "burden-errors", "multilang-qualification", "security-audit", "governance"):
        p = sub.add_parser(name)
        p.add_argument("input")
        p.add_argument("--root", default=".")
        p.add_argument("--json", action="store_true")

    p3r = sub.add_parser("p3-result")
    p3r.add_argument("input")
    p3r.add_argument("--registry", default="validation/benchmark-registry.json")
    p3r.add_argument("--root", default=".")
    p3r.add_argument("--json", action="store_true")

    p3 = sub.add_parser("p3")
    p3.add_argument("input")
    p3.add_argument("--registry", default="validation/benchmark-registry.json")
    p3.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    data = _read_json(Path(args.input))
    if args.command == "p2":
        result = validate_p2_plan(data)
    elif args.command == "p2-result":
        result = validate_p2_result(data, root=Path(args.root))
    elif args.command == "p3":
        result = validate_p3_plan(data, _read_json(Path(args.registry)))
    elif args.command == "p3-result":
        result = validate_p3_result(data, _read_json(Path(args.registry)), root=Path(args.root))
    elif args.command == "p4-plan":
        result = validate_p4_plan(data)
    elif args.command == "p4":
        result = validate_p4_result(data, root=Path(args.root))
    elif args.command == "replication":
        result = validate_replication_result(data)
    elif args.command == "burden-errors":
        result = validate_burden_error_result(data)
    elif args.command == "inter-rater":
        result = analyze_inter_rater(data, root=Path(args.root))
    elif args.command == "multilang-qualification":
        result = validate_multilang_qualification(data)
    elif args.command == "security-audit":
        result = validate_independent_security_audit(data)
    elif args.command == "governance":
        result = validate_governance_1_0(data)
    else:
        rows = data.get("results", [])
        if not isinstance(rows, list):
            print("ERROR: burden input must contain a results array")
            return 2
        result = analyze_burden(rows)

    if getattr(args, "json", False):
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['study']}: {result['status']}")
        for error in result.get("errors", []):
            print(f"ERROR: {error}")
        for warning in result.get("warnings", []):
            print(f"WARN: {warning}")
    return 0 if result["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
