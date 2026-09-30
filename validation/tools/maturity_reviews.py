#!/usr/bin/env python3
"""Independent-review, replication, burden and maturity qualification validators."""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

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
