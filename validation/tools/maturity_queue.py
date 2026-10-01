#!/usr/bin/env python3
"""Deterministic execution queues for frozen P2, P3 and P4 maturity studies."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from validation.tools.maturity_studies import (
    ARMS,
    validate_p2_plan,
    validate_p3_plan,
    validate_p4_plan,
)


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to read {path}: {exc}")
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", value.strip()).strip("-").lower()
    return text or "item"


def _pairing_key(item: Mapping[str, Any]) -> Tuple[str, str, str]:
    return (
        str(item.get("model_display_name", "")).strip(),
        str(item.get("agent", "")).strip(),
        str(item.get("reasoning_effort", "")).strip(),
    )


def build_p2_queue(plan: Mapping[str, Any], result: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    checked = validate_p2_plan(plan)
    if checked["status"] != "VALID":
        raise ValueError("invalid P2 plan: " + "; ".join(checked["errors"]))

    study_id = str(plan["study_id"])
    repetitions = int(plan["repetitions_per_arm"])
    scenarios = [str(item["id"]) for item in plan["scenarios"]]
    pairings = [item for item in plan["model_agent_pairings"] if isinstance(item, dict)]

    completed_ids: Set[str] = set()
    if isinstance(result, Mapping):
        runs = result.get("runs", [])
        if isinstance(runs, list):
            completed_ids = {
                str(row.get("run_id"))
                for row in runs
                if isinstance(row, dict) and str(row.get("run_id", "")).strip()
            }

    entries: List[Dict[str, Any]] = []
    for scenario in scenarios:
        for pair_index, pairing in enumerate(pairings, start=1):
            model, agent, reasoning = _pairing_key(pairing)
            pair_id = f"{_slug(study_id)}-{_slug(scenario)}-p{pair_index}"
            for repetition in range(1, repetitions + 1):
                for arm in ARMS:
                    run_id = (
                        f"{_slug(study_id)}-{_slug(scenario)}-p{pair_index}-"
                        f"{arm.lower()}-r{repetition}"
                    )
                    entries.append({
                        "study": "P2",
                        "study_id": study_id,
                        "scenario_id": scenario,
                        "arm": arm,
                        "repetition": repetition,
                        "pair_index": pair_index,
                        "pair_id": pair_id,
                        "run_id": run_id,
                        "model_display_name": model,
                        "agent": agent,
                        "reasoning_effort": reasoning,
                        "status": "COMPLETE" if run_id in completed_ids else "MISSING",
                    })

    missing = [item for item in entries if item["status"] == "MISSING"]
    return {
        "study": "P2",
        "study_id": study_id,
        "expected": len(entries),
        "complete": len(entries) - len(missing),
        "missing": len(missing),
        "entries": entries,
        "claim_boundary": "Queue completion is execution coverage only; it does not imply Qualified Success or MAT-02 PASS.",
    }


def build_p3_queue(
    plan: Mapping[str, Any],
    benchmark_registry: Mapping[str, Any],
    result: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    checked = validate_p3_plan(plan, benchmark_registry)
    if checked["status"] != "VALID":
        raise ValueError("invalid P3 plan: " + "; ".join(checked["errors"]))

    study_id = str(plan["study_id"])
    pairing = plan["model_agent_pairing"]
    model, agent, reasoning = _pairing_key(pairing)
    completed_attempts: Dict[Tuple[str, str], int] = {}

    if isinstance(result, Mapping):
        benchmarks = result.get("benchmarks", [])
        if isinstance(benchmarks, list):
            for item in benchmarks:
                if not isinstance(item, dict):
                    continue
                bid = str(item.get("id", "")).strip()
                arms = item.get("arms", {})
                if not isinstance(arms, dict):
                    continue
                for arm in ARMS:
                    arm_result = arms.get(arm)
                    if isinstance(arm_result, dict) and isinstance(arm_result.get("attempts"), int):
                        completed_attempts[(bid, arm)] = max(0, int(arm_result["attempts"]))

    entries: List[Dict[str, Any]] = []
    for benchmark in plan["benchmarks"]:
        bid = str(benchmark["id"])
        attempts = int(benchmark["attempts_per_arm"])
        for arm in ARMS:
            observed = completed_attempts.get((bid, arm), 0)
            for attempt in range(1, attempts + 1):
                run_id = f"{_slug(study_id)}-{_slug(bid)}-{arm.lower()}-r{attempt}"
                entries.append({
                    "study": "P3",
                    "study_id": study_id,
                    "benchmark_id": bid,
                    "arm": arm,
                    "attempt": attempt,
                    "run_id": run_id,
                    "model_display_name": model,
                    "agent": agent,
                    "reasoning_effort": reasoning,
                    "upstream_revision": benchmark["upstream_revision"],
                    "task_subset_commitment_sha256": benchmark["task_subset_commitment_sha256"],
                    "status": "COMPLETE" if attempt <= observed else "MISSING",
                })

    missing = [item for item in entries if item["status"] == "MISSING"]
    return {
        "study": "P3",
        "study_id": study_id,
        "expected": len(entries),
        "complete": len(entries) - len(missing),
        "missing": len(missing),
        "entries": entries,
        "claim_boundary": "Queue completion records attempt coverage; benchmark interpretation remains separate and benchmark-specific.",
    }


def build_p4_queue(plan: Mapping[str, Any], result: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    checked = validate_p4_plan(plan)
    if checked["status"] != "VALID":
        raise ValueError("invalid P4 plan: " + "; ".join(checked["errors"]))

    dimensions = ("load", "soak", "rollback", "recovery", "observability")
    entries: List[Dict[str, Any]] = []
    result_map = result if isinstance(result, Mapping) else {}

    for dimension in dimensions:
        criteria = plan["acceptance_criteria"][dimension]
        observed = result_map.get(dimension)
        complete = (
            isinstance(observed, dict)
            and str(observed.get("status", "")).upper() in {"PASS", "FAIL"}
            and isinstance(observed.get("evidence"), list)
            and any(str(x).strip() for x in observed["evidence"])
        )
        item = {
            "study": "P4",
            "study_id": plan["study_id"],
            "dimension": dimension,
            "service_id": plan["service_id"],
            "revision": plan["revision"],
            "environment": plan["environment"],
            "success_criteria": criteria["success_criteria"],
            "status": "COMPLETE" if complete else "MISSING",
        }
        if "target_rps" in criteria:
            item["target_rps"] = criteria["target_rps"]
        if "duration_minutes" in criteria:
            item["duration_minutes"] = criteria["duration_minutes"]
        entries.append(item)

    missing = [item for item in entries if item["status"] == "MISSING"]
    return {
        "study": "P4",
        "study_id": plan["study_id"],
        "expected": len(entries),
        "complete": len(entries) - len(missing),
        "missing": len(missing),
        "entries": entries,
        "claim_boundary": "Operational checklist completion does not imply the dimensions passed; PASS/FAIL remains in the frozen result package.",
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate frozen AuraCode maturity-study execution queues")
    sub = parser.add_subparsers(dest="study", required=True)

    p2 = sub.add_parser("p2")
    p2.add_argument("plan")
    p2.add_argument("--result")
    p2.add_argument("--missing-only", action="store_true")
    p2.add_argument("--json", action="store_true")

    p3 = sub.add_parser("p3")
    p3.add_argument("plan")
    p3.add_argument("--registry", default="validation/benchmark-registry.json")
    p3.add_argument("--result")
    p3.add_argument("--missing-only", action="store_true")
    p3.add_argument("--json", action="store_true")

    p4 = sub.add_parser("p4")
    p4.add_argument("plan")
    p4.add_argument("--result")
    p4.add_argument("--missing-only", action="store_true")
    p4.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    try:
        plan = _read_json(Path(args.plan))
        result = _read_json(Path(args.result)) if args.result else None
        if args.study == "p2":
            queue = build_p2_queue(plan, result)
        elif args.study == "p3":
            queue = build_p3_queue(plan, _read_json(Path(args.registry)), result)
        else:
            queue = build_p4_queue(plan, result)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    entries = [
        item for item in queue["entries"]
        if not args.missing_only or item["status"] == "MISSING"
    ]
    output = dict(queue)
    output["entries"] = entries

    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(
            f"{queue['study']} queue: complete={queue['complete']} "
            f"missing={queue['missing']} expected={queue['expected']}"
        )
        for item in entries:
            identity = item.get("run_id") or item.get("dimension")
            print(f"{item['status']:8} {identity}")
        print(queue["claim_boundary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
