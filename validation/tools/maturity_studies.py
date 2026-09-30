#!/usr/bin/env python3
"""Validation primitives for AuraCode maturity studies P2/P3/P4 and reviewer agreement."""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

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



def validate_p2_result(data: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate a completed P2 result package; plans alone can never satisfy this."""
    errors: List[str] = []
    warnings: List[str] = []
    if str(data.get("study", "")).upper() != "P2":
        errors.append("study must be P2")
    if not bool(data.get("preregistered")):
        errors.append("preregistered must be true")
    if not bool(data.get("private_or_fresh_split")):
        errors.append("private_or_fresh_split must be true")
    prereg = str(data.get("preregistration_sha256", "")).lower().strip()
    if len(prereg) != 64 or any(ch not in "0123456789abcdef" for ch in prereg):
        errors.append("preregistration_sha256 must be a 64-character SHA-256 hex digest")

    runs = _nonempty_list(data.get("runs"))
    if not runs:
        errors.append("P2 result requires runs")
    ids: List[str] = []
    by_arm: Dict[str, int] = {arm: 0 for arm in ARMS}
    scenario_ids = set()
    pairings = set()
    invalid_qs: List[str] = []
    for index, row in enumerate(runs):
        if not isinstance(row, dict):
            errors.append(f"runs[{index}] must be an object")
            continue
        run_id = str(row.get("run_id", "")).strip()
        arm = str(row.get("arm", "")).strip()
        scenario_id = str(row.get("scenario_id", "")).strip()
        model = str(row.get("model_display_name", "")).strip()
        agent = str(row.get("agent", "")).strip()
        if not run_id or arm not in ARMS or not scenario_id or not model or not agent:
            errors.append(f"runs[{index}] missing required provenance")
            continue
        ids.append(run_id)
        by_arm[arm] += 1
        scenario_ids.add(scenario_id)
        pairings.add((model, agent))
        required = ("public_tests_passed", "protected_tests_passed", "evaluator_integrity")
        if all(isinstance(row.get(key), bool) for key in required):
            expected = all(bool(row.get(key)) for key in required)
            if bool(row.get("qualified_success")) != expected:
                invalid_qs.append(run_id)
        elif not isinstance(row.get("qualified_success"), bool):
            errors.append(f"{run_id}: qualified_success must be boolean")

    if len(ids) != len(set(ids)):
        errors.append("P2 run_id values must be unique")
    if invalid_qs:
        errors.append("Qualified Success formula mismatch: " + ", ".join(sorted(invalid_qs)))
    if len(scenario_ids) < 30:
        errors.append(f"P2 result requires >=30 scenarios; found {len(scenario_ids)}")
    for arm in ARMS:
        if by_arm[arm] == 0:
            errors.append(f"P2 result has no runs for arm {arm}")

    declared_expected = data.get("expected_attempts")
    if not isinstance(declared_expected, int) or declared_expected <= 0:
        errors.append("expected_attempts must be a positive integer")
    elif len(runs) != declared_expected:
        errors.append(f"P2 incomplete: observed {len(runs)}/{declared_expected} attempts")

    completed = bool(data.get("completed"))
    if not completed:
        errors.append("completed must be true for a formal P2 result")

    if len(pairings) < 1:
        errors.append("P2 result requires at least one model/agent pairing")

    return {
        "study": "P2_RESULT",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "warnings": warnings,
        "completed": completed and not errors,
        "run_count": len(runs),
        "scenario_count": len(scenario_ids),
        "pairing_count": len(pairings),
        "by_arm": by_arm,
    }



def validate_p3_plan(data: Mapping[str, Any], benchmark_registry: Mapping[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    if not bool(data.get("preregistered")):
        errors.append("preregistered must be true before P3 execution")

    known = {
        str(item.get("id", "")): item
        for item in _nonempty_list(benchmark_registry.get("benchmarks"))
        if isinstance(item, dict) and str(item.get("id", "")).strip()
    }
    selections = _nonempty_list(data.get("benchmarks"))
    if not selections:
        errors.append("at least one external benchmark must be selected")

    for index, selected in enumerate(selections):
        if not isinstance(selected, dict):
            errors.append(f"benchmarks[{index}] must be an object")
            continue
        benchmark_id = str(selected.get("id", "")).strip()
        if benchmark_id not in known:
            errors.append(f"unknown benchmark id: {benchmark_id or '<empty>'}")
            continue
        if not bool(selected.get("license_verified")):
            errors.append(f"{benchmark_id}: license_verified must be true for formal execution")
        if not str(selected.get("upstream_revision", "")).strip():
            errors.append(f"{benchmark_id}: upstream_revision is required")
        if not str(selected.get("task_subset_commitment_sha256", "")).strip():
            errors.append(f"{benchmark_id}: task_subset_commitment_sha256 is required")

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



def validate_p3_result(data: Mapping[str, Any], benchmark_registry: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate completed ecological/external benchmark evidence."""
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
    results = _nonempty_list(data.get("benchmarks"))
    if not results:
        errors.append("P3 result requires benchmark results")
    seen = set()
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
        if not bool(item.get("license_verified")):
            errors.append(f"{bid}: license_verified must be true")
        if not str(item.get("upstream_revision", "")).strip():
            errors.append(f"{bid}: upstream_revision is required")
        if not str(item.get("task_subset_commitment_sha256", "")).strip():
            errors.append(f"{bid}: task_subset_commitment_sha256 is required")
        if not isinstance(item.get("attempts"), int) or int(item.get("attempts", 0)) <= 0:
            errors.append(f"{bid}: attempts must be a positive integer")
        if not isinstance(item.get("completed"), bool) or not item.get("completed"):
            errors.append(f"{bid}: completed must be true")
        arms = item.get("arms")
        if not isinstance(arms, dict) or any(arm not in arms for arm in ARMS):
            errors.append(f"{bid}: results must report A0/A1/A2 separately")

    if data.get("combined_score") is not None:
        errors.append("P3 must not collapse heterogeneous benchmarks into one combined_score")
    if len(seen) < 2:
        errors.append("P3 maturity evidence requires at least two distinct benchmark families")

    return {
        "study": "P3_RESULT",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "completed": not errors,
        "benchmark_count": len(seen),
    }



def _check_operational_dimension(name: str, value: object, errors: List[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return
    status = str(value.get("status", "")).upper()
    if status not in {"PASS", "FAIL"}:
        errors.append(f"{name}.status must be PASS or FAIL")
    evidence = _nonempty_list(value.get("evidence"))
    if not any(str(item).strip() for item in evidence):
        errors.append(f"{name}.evidence requires at least one artifact")


def validate_p4_result(data: Mapping[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    if not str(data.get("service_id", "")).strip():
        errors.append("service_id is required")
    if not str(data.get("revision", "")).strip():
        errors.append("revision is required")
    for field in ("load", "soak", "rollback", "recovery", "observability"):
        _check_operational_dimension(field, data.get(field), errors)

    soak = data.get("soak")
    if isinstance(soak, dict):
        duration = soak.get("duration_minutes")
        if not isinstance(duration, (int, float)) or duration <= 0:
            errors.append("soak.duration_minutes must be > 0")

    load = data.get("load")
    if isinstance(load, dict):
        target = load.get("target_rps")
        if not isinstance(target, (int, float)) or target <= 0:
            errors.append("load.target_rps must be > 0")

    return {
        "study": "P4",
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


def analyze_inter_rater(data: Mapping[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    assessors = _nonempty_list(data.get("assessors"))
    if len(assessors) < 2:
        errors.append("at least two independent assessors are required")
    ids = [str(a.get("id", "")).strip() for a in assessors if isinstance(a, dict)]
    if len(ids) != len(assessors) or any(not item for item in ids):
        errors.append("every assessor requires a non-empty id")
    if len(set(ids)) != len(ids):
        errors.append("assessor ids must be unique")

    ratings = _nonempty_list(data.get("ratings"))
    paired: Dict[str, Dict[str, str]] = defaultdict(dict)
    for item in ratings:
        if not isinstance(item, dict):
            errors.append("each rating must be an object")
            continue
        control_id = str(item.get("control_id", "")).strip()
        assessor_id = str(item.get("assessor_id", "")).strip()
        rating = str(item.get("rating", "")).upper()
        if not control_id or assessor_id not in ids or rating not in RATING_VALUES:
            errors.append(f"invalid rating record: {item}")
            continue
        paired[control_id][assessor_id] = rating

    kappa = None
    agreement = None
    paired_count = 0
    if len(ids) >= 2 and not errors:
        left_id, right_id = ids[0], ids[1]
        common = sorted(cid for cid, values in paired.items() if left_id in values and right_id in values)
        paired_count = len(common)
        if paired_count == 0:
            errors.append("no controls have paired ratings from the first two assessors")
        else:
            left = [paired[cid][left_id] for cid in common]
            right = [paired[cid][right_id] for cid in common]
            agreement = sum(a == b for a, b in zip(left, right)) / paired_count
            kappa = cohen_kappa(left, right)

    return {
        "study": "INTER_RATER",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
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



def validate_multilang_qualification(data: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate evidence for MAT-08 without inventing acceptance thresholds."""
    errors: List[str] = []
    if not bool(data.get("preregistered")):
        errors.append("multilang qualification must be preregistered")
    revision = str(data.get("revision", "")).strip()
    if not revision:
        errors.append("revision is required")
    thresholds = data.get("acceptance_thresholds")
    if not isinstance(thresholds, dict):
        errors.append("acceptance_thresholds object is required")
        thresholds = {}
    languages = data.get("languages")
    if not isinstance(languages, dict):
        errors.append("languages object is required")
        languages = {}

    required_languages = ("python", "typescript")
    results: Dict[str, Any] = {}
    for language in required_languages:
        entry = languages.get(language)
        if not isinstance(entry, dict):
            errors.append(f"{language}: qualification result is required")
            continue
        cases = entry.get("cases")
        tp = entry.get("true_positive")
        tn = entry.get("true_negative")
        fp = entry.get("false_positive")
        fn = entry.get("false_negative")
        for name, value in (("cases", cases), ("true_positive", tp), ("true_negative", tn), ("false_positive", fp), ("false_negative", fn)):
            if not isinstance(value, int) or value < 0:
                errors.append(f"{language}.{name} must be a non-negative integer")
        if not bool(entry.get("parser_available")):
            errors.append(f"{language}: parser_available must be true")
        if not str(entry.get("engine", "")).strip():
            errors.append(f"{language}: engine is required")
        evidence = _nonempty_list(entry.get("evidence"))
        if not any(str(item).strip() for item in evidence):
            errors.append(f"{language}: evidence is required")
        if all(isinstance(v, int) and v >= 0 for v in (tp, tn, fp, fn)):
            total = int(tp) + int(tn) + int(fp) + int(fn)
            if isinstance(cases, int) and cases != total:
                errors.append(f"{language}: cases must equal TP+TN+FP+FN")
            precision = (tp / (tp + fp)) if (tp + fp) else None
            recall = (tp / (tp + fn)) if (tp + fn) else None
            fpr = (fp / (fp + tn)) if (fp + tn) else None
            results[language] = {"precision": precision, "recall": recall, "false_positive_rate": fpr, "cases": total}

    for metric in ("min_recall", "max_false_positive_rate"):
        value = thresholds.get(metric)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= float(value) <= 1:
            errors.append(f"acceptance_thresholds.{metric} must be between 0 and 1")

    if not errors:
        min_recall = float(thresholds["min_recall"])
        max_fpr = float(thresholds["max_false_positive_rate"])
        for language, metrics in results.items():
            recall = metrics["recall"]
            fpr = metrics["false_positive_rate"]
            if recall is None or recall < min_recall:
                errors.append(f"{language}: recall does not meet preregistered threshold")
            if fpr is None or fpr > max_fpr:
                errors.append(f"{language}: false-positive rate exceeds preregistered threshold")

    return {
        "study": "MULTILANG_QUALIFICATION",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "results": results,
        "claim_boundary": "Qualification is limited to the frozen corpus, rules and thresholds in this evidence package.",
    }


def validate_independent_security_audit(data: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate MAT-09 evidence package structure and blocking finding status."""
    errors: List[str] = []
    if not bool(data.get("independence_attestation")):
        errors.append("independence_attestation must be true")
    for field in ("assessor_id", "revision", "scope"):
        if not str(data.get(field, "")).strip():
            errors.append(f"{field} is required")
    for section in ("threat_model", "supply_chain"):
        item = data.get(section)
        if not isinstance(item, dict):
            errors.append(f"{section} assessment is required")
            continue
        if str(item.get("status", "")).upper() != "PASS":
            errors.append(f"{section}.status must be PASS")
        evidence = _nonempty_list(item.get("evidence"))
        if not any(str(x).strip() for x in evidence):
            errors.append(f"{section}.evidence is required")
    open_findings = data.get("open_findings")
    if not isinstance(open_findings, dict):
        errors.append("open_findings object is required")
    else:
        for severity in ("critical", "high"):
            value = open_findings.get(severity)
            if not isinstance(value, int) or value < 0:
                errors.append(f"open_findings.{severity} must be a non-negative integer")
            elif value != 0:
                errors.append(f"open {severity} findings must be zero for MAT-09")
    return {
        "study": "INDEPENDENT_SECURITY_AUDIT",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
    }


def validate_governance_1_0(data: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate that stable-1.0 governance roles and decision rules are explicitly established."""
    errors: List[str] = []
    if str(data.get("status", "")).upper() != "ADOPTED":
        errors.append("governance status must be ADOPTED")
    roles = data.get("roles")
    if not isinstance(roles, dict):
        errors.append("roles object is required")
        roles = {}
    for role in ("maintainers", "release_manager", "security_response"):
        value = roles.get(role)
        if isinstance(value, list):
            if not any(str(x).strip() for x in value):
                errors.append(f"roles.{role} must contain at least one identity")
        elif not str(value or "").strip():
            errors.append(f"roles.{role} is required")
    for field in ("normative_change_rule", "release_authority_rule", "security_response_rule", "appeal_rule"):
        if not str(data.get(field, "")).strip():
            errors.append(f"{field} is required")
    evidence = _nonempty_list(data.get("evidence"))
    if not any(str(x).strip() for x in evidence):
        errors.append("governance evidence is required")
    return {
        "study": "GOVERNANCE_1_0",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
    }


def validate_evidence_for_criterion(
    criterion_id: str,
    data: Mapping[str, Any],
    benchmark_registry: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Dispatch maturity evidence to the semantic validator for its criterion."""
    cid = criterion_id.strip().upper()
    if cid == "MAT-02":
        return validate_p2_result(data)
    if cid == "MAT-03":
        return validate_replication_result(data)
    if cid == "MAT-04":
        if benchmark_registry is None:
            raise ValueError("MAT-04 validation requires benchmark registry")
        return validate_p3_result(data, benchmark_registry)
    if cid == "MAT-05":
        return validate_p4_result(data)
    if cid == "MAT-06":
        return analyze_inter_rater(data)
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

    for name in ("p2", "p2-result", "p4", "inter-rater", "burden", "replication", "burden-errors", "multilang-qualification", "security-audit", "governance"):
        p = sub.add_parser(name)
        p.add_argument("input")
        p.add_argument("--json", action="store_true")

    p3r = sub.add_parser("p3-result")
    p3r.add_argument("input")
    p3r.add_argument("--registry", default="validation/benchmark-registry.json")
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
        result = validate_p2_result(data)
    elif args.command == "p3":
        result = validate_p3_plan(data, _read_json(Path(args.registry)))
    elif args.command == "p3-result":
        result = validate_p3_result(data, _read_json(Path(args.registry)))
    elif args.command == "p4":
        result = validate_p4_result(data)
    elif args.command == "replication":
        result = validate_replication_result(data)
    elif args.command == "burden-errors":
        result = validate_burden_error_result(data)
    elif args.command == "inter-rater":
        result = analyze_inter_rater(data)
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
