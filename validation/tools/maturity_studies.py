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


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AuraCode maturity-study validation toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("p2", "p4", "inter-rater", "burden"):
        p = sub.add_parser(name)
        p.add_argument("input")
        p.add_argument("--json", action="store_true")

    p3 = sub.add_parser("p3")
    p3.add_argument("input")
    p3.add_argument("--registry", default="validation/benchmark-registry.json")
    p3.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    data = _read_json(Path(args.input))
    if args.command == "p2":
        result = validate_p2_plan(data)
    elif args.command == "p3":
        result = validate_p3_plan(data, _read_json(Path(args.registry)))
    elif args.command == "p4":
        result = validate_p4_result(data)
    elif args.command == "inter-rater":
        result = analyze_inter_rater(data)
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
