#!/usr/bin/env python3
"""Aggregate AuraCode stable-1.0 maturity blockers into a deterministic work queue."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

ROOT = Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to read {path}: {exc}")
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return data


def validate_workplan(workplan: Mapping[str, Any], criterion_ids: Sequence[str]) -> List[str]:
    errors: List[str] = []
    if str(workplan.get("target", "")) != "stable-1.0":
        errors.append("workplan target must be stable-1.0")
    raw = workplan.get("criteria")
    if not isinstance(raw, list):
        return errors + ["workplan criteria must be an array"]

    entries: Dict[str, Mapping[str, Any]] = {}
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            errors.append(f"criteria[{index}] must be object")
            continue
        cid = str(item.get("id", "")).strip().upper()
        if not cid:
            errors.append(f"criteria[{index}] missing id")
            continue
        if cid in entries:
            errors.append(f"duplicate workplan criterion {cid}")
        entries[cid] = item
        for field in (
            "owner_role",
            "validator",
            "evidence_package",
            "completion_condition",
            "next_action",
        ):
            if not str(item.get(field, "")).strip():
                errors.append(f"{cid}: missing {field}")
        if not isinstance(item.get("human_required"), bool):
            errors.append(f"{cid}: human_required must be boolean")
        if not isinstance(item.get("independence_required"), bool):
            errors.append(f"{cid}: independence_required must be boolean")
        prereqs = item.get("prerequisites")
        if not isinstance(prereqs, list) or not any(str(x).strip() for x in prereqs):
            errors.append(f"{cid}: prerequisites must be non-empty array")

    expected = {str(cid).strip().upper() for cid in criterion_ids}
    actual = set(entries)
    if actual != expected:
        errors.append(
            "workplan criteria differ from maturity criteria: "
            f"missing={sorted(expected-actual)} extra={sorted(actual-expected)}"
        )
    return errors


def build_readiness(root: Path = ROOT) -> Dict[str, Any]:
    root = root.resolve()
    from tools.maturity_gate import evaluate_maturity
    from validation.tools.p1_matrix import build_matrix
    from validation.tools.validate_experiment_evidence import load_results

    criteria_data = _load_json(root / "validation" / "maturity-criteria.json")
    workplan = _load_json(root / "validation" / "maturity-workplan.json")
    criterion_ids = [
        str(item.get("id", "")).strip().upper()
        for item in criteria_data.get("criteria", [])
        if isinstance(item, dict) and str(item.get("id", "")).strip()
    ]
    errors = validate_workplan(workplan, criterion_ids)
    if errors:
        raise ValueError("; ".join(errors))

    maturity = evaluate_maturity(root)
    status_by_id = {
        str(item.get("id", "")).strip().upper(): item
        for item in maturity.get("criteria", [])
        if isinstance(item, dict)
    }
    plan_by_id = {
        str(item.get("id", "")).strip().upper(): item
        for item in workplan["criteria"]
        if isinstance(item, dict)
    }

    rows, load_errors = load_results(root / "validation" / "results")
    matrix = build_matrix(rows)
    p1_detail = {
        "total_expected": matrix.get("total_expected"),
        "total_complete": matrix.get("total_complete"),
        "total_missing": matrix.get("total_missing"),
        "missing_by_category": matrix.get("missing_by_category"),
        "load_errors": load_errors,
    }

    remaining: List[Dict[str, Any]] = []
    completed: List[str] = []
    for cid in criterion_ids:
        result = status_by_id.get(cid, {"status": "UNKNOWN", "reason": "not evaluated"})
        status = str(result.get("status", "UNKNOWN")).upper()
        plan = plan_by_id[cid]
        if status == "PASS":
            completed.append(cid)
            continue
        item: Dict[str, Any] = {
            "id": cid,
            "status": status,
            "reason": result.get("reason"),
            "owner_role": plan["owner_role"],
            "human_required": plan["human_required"],
            "independence_required": plan["independence_required"],
            "prerequisites": plan["prerequisites"],
            "validator": plan["validator"],
            "evidence_package": plan["evidence_package"],
            "completion_condition": plan["completion_condition"],
            "next_action": plan["next_action"],
        }
        if cid == "MAT-01":
            item["p1"] = p1_detail
        remaining.append(item)

    return {
        "target": "stable-1.0",
        "decision": maturity.get("decision", "BLOCK"),
        "ready": bool(maturity.get("ready")),
        "completed_criteria": completed,
        "remaining_count": len(remaining),
        "remaining": remaining,
        "p1": p1_detail,
        "claim_boundary": (
            "This report schedules evidence work only. It does not execute external studies, "
            "authenticate reviewers, adopt governance, or promote any MAT criterion."
        ),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AuraCode stable maturity readiness queue")
    parser.add_argument("target", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args(argv)

    try:
        report = build_readiness(Path(args.target))
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Stable maturity: {report['decision']}")
        print(f"Remaining criteria: {report['remaining_count']}")
        for item in report["remaining"]:
            print(f"- {item['id']} {item['status']}: {item['next_action']}")
        print(report["claim_boundary"])

    if args.report_only:
        return 0
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
