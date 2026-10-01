#!/usr/bin/env python3
"""Generate the frozen P1 execution matrix and identify missing runs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from validation.tools.validate_experiment_evidence import (
    ARMS,
    AUTOMATED_SCENARIOS,
    load_results,
)

SHORT_NAMES = {
    "SEC-AUTHZ-001": "authz",
    "SEC-PATH-001": "path",
    "SEC-FAIL-001": "fail",
    "SEC-SQLI-001": "sqli",
    "SEC-LOG-001": "log",
    "DAT-ATOMIC-001": "atomic",
    "REL-CACHE-001": "cache",
    "REL-IDEMP-001": "idemp",
    "SUP-DEPS-001": "deps",
    "VER-TAMPER-001": "tamper",
}
ORDER_CYCLE = (
    ("A0", "A1", "A2"),
    ("A1", "A2", "A0"),
    ("A2", "A0", "A1"),
)


def _existing_ids(rows: Sequence[Mapping[str, Any]]) -> Set[str]:
    return {
        str(row.get("run_id"))
        for row in rows
        if str(row.get("run_id") or "").strip()
    }


def _entry(
    category: str,
    scenario_id: str,
    repetition: str,
    arm: str,
    run_id: str,
    pair_id: str,
    order: int,
    existing: Set[str],
) -> Dict[str, Any]:
    item: Dict[str, Any] = {
        "category": category,
        "scenario_id": scenario_id,
        "repetition": repetition,
        "arm": arm,
        "run_id": run_id,
        "pair_id": pair_id,
        "execution_order": order,
        "status": "COMPLETE" if run_id in existing else "MISSING",
    }
    if category == "automated":
        workspace = f"/tmp/{scenario_id}-{arm}-{repetition}"
        item["prepare_command"] = (
            f"python validation/tools/harness.py prepare {scenario_id} {workspace}"
        )
        item["evaluate_command"] = (
            f"python validation/tools/harness.py evaluate {scenario_id} {workspace} "
            f"--arm {arm} --run-id {run_id} --pair-id {pair_id} "
            "--model-display-name 'Gemini 3.8 Flash Medium' "
            "--model-family 'Gemini 3.8 Flash' --reasoning-effort medium "
            "--surface ide --agent 'Antigravity IDE 2.5.5'"
        )
    elif category == "ambiguity":
        item["procedure"] = (
            "Run INT-AMBIG-001 using the frozen scripted user response in EVALUATION.md; "
            "record whether a material clarification was asked before implementation."
        )
    else:
        item["procedure"] = (
            "Run the full five-stage ARC-EVOL-001 sequence and evaluate after every stage."
        )
    return item


def build_matrix(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    existing = _existing_ids(rows)
    entries: List[Dict[str, Any]] = []

    for scenario_id in AUTOMATED_SCENARIOS:
        short = SHORT_NAMES[scenario_id]
        for rep_index in range(3):
            repetition = f"r{rep_index + 1}"
            pair_id = f"{short}-{repetition}"
            for order, arm in enumerate(ORDER_CYCLE[rep_index], start=1):
                run_id = f"{short}-{arm}-{repetition}"
                entries.append(
                    _entry(
                        "automated",
                        scenario_id,
                        repetition,
                        arm,
                        run_id,
                        pair_id,
                        order,
                        existing,
                    )
                )

    for rep_index in range(5):
        repetition = f"r{rep_index + 1}"
        pair_id = f"ambig-{repetition}"
        order_cycle = ORDER_CYCLE[rep_index % len(ORDER_CYCLE)]
        for order, arm in enumerate(order_cycle, start=1):
            run_id = f"ambig-{arm}-{repetition}"
            entries.append(
                _entry(
                    "ambiguity",
                    "INT-AMBIG-001",
                    repetition,
                    arm,
                    run_id,
                    pair_id,
                    order,
                    existing,
                )
            )

    for seq_index in range(3):
        repetition = f"seq{seq_index + 1}"
        pair_id = f"arcevol-{repetition}"
        order_cycle = ORDER_CYCLE[seq_index % len(ORDER_CYCLE)]
        for order, arm in enumerate(order_cycle, start=1):
            run_id = f"arcevol-{arm}-{repetition}"
            entries.append(
                _entry(
                    "architecture",
                    "ARC-EVOL-001",
                    repetition,
                    arm,
                    run_id,
                    pair_id,
                    order,
                    existing,
                )
            )

    missing = [item for item in entries if item["status"] == "MISSING"]
    by_category: Dict[str, int] = {}
    for item in missing:
        category = str(item["category"])
        by_category[category] = by_category.get(category, 0) + 1

    return {
        "protocol": "P1-IDE-GEMINI-3.8-FLASH-MED-001",
        "total_expected": len(entries),
        "total_complete": len(entries) - len(missing),
        "total_missing": len(missing),
        "missing_by_category": by_category,
        "entries": entries,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate frozen P1 run matrix")
    parser.add_argument("results", nargs="?", default="validation/results")
    parser.add_argument("--missing-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    rows, errors = load_results(Path(args.results))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 2
    matrix = build_matrix(rows)
    entries = [
        item
        for item in matrix["entries"]
        if not args.missing_only or item["status"] == "MISSING"
    ]

    if args.json:
        output = dict(matrix)
        output["entries"] = entries
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(
            f"P1 matrix: complete={matrix['total_complete']} "
            f"missing={matrix['total_missing']} expected={matrix['total_expected']}"
        )
        for category, count in sorted(matrix["missing_by_category"].items()):
            print(f"- {category}: {count} missing")
        for item in entries:
            print(
                f"{item['status']:8} order={item['execution_order']} "
                f"{item['run_id']} [{item['scenario_id']}]"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
