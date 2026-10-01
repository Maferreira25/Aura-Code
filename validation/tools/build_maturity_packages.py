#!/usr/bin/env python3
"""Build canonical MAT-02/MAT-03/MAT-07 evidence packages from frozen raw inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from validation.tools.maturity_queue import build_p2_queue
from validation.tools.maturity_studies import (
    validate_burden_error_result,
    validate_p2_plan,
    validate_p2_result,
    validate_replication_result,
)


ARMS = ("A0", "A1", "A2")


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to read {path}: {exc}")
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(root: Path, path: Path) -> str:
    resolved_root = root.resolve()
    resolved = path.resolve()
    try:
        return resolved.relative_to(resolved_root).as_posix()
    except ValueError as exc:
        raise ValueError(f"path must be inside repository root: {resolved}") from exc


def _load_result_files(directory: Path) -> List[Dict[str, Any]]:
    root = directory.resolve()
    if not root.is_dir():
        raise ValueError(f"results directory does not exist: {root}")
    rows: List[Dict[str, Any]] = []
    for path in sorted(root.rglob("*.json")):
        data = _read_json(path)
        if str(data.get("run_id", "")).strip():
            row = dict(data)
            row["_source_path"] = str(path)
            rows.append(row)
    return rows


def build_p2_package(
    root: Path,
    plan_path: Path,
    results_dir: Path,
) -> Dict[str, Any]:
    repo = root.resolve()
    plan_file = plan_path.resolve()
    plan = _read_json(plan_file)
    plan_check = validate_p2_plan(plan)
    if plan_check["status"] != "VALID":
        raise ValueError("invalid P2 preregistration: " + "; ".join(plan_check["errors"]))

    queue = build_p2_queue(plan)
    expected = {str(item["run_id"]): item for item in queue["entries"]}
    raw_rows = _load_result_files(results_dir)

    selected: Dict[str, Dict[str, Any]] = {}
    duplicates: List[str] = []
    for row in raw_rows:
        run_id = str(row.get("run_id", "")).strip()
        if run_id not in expected:
            continue
        if run_id in selected:
            duplicates.append(run_id)
            continue
        clean = {key: value for key, value in row.items() if key != "_source_path"}
        selected[run_id] = clean

    if duplicates:
        raise ValueError("duplicate P2 run ids: " + ", ".join(sorted(set(duplicates))))

    ordered_runs = [
        selected[str(item["run_id"])]
        for item in queue["entries"]
        if str(item["run_id"]) in selected
    ]
    missing = [
        str(item["run_id"])
        for item in queue["entries"]
        if str(item["run_id"]) not in selected
    ]

    package: Dict[str, Any] = {
        "study": "P2",
        "study_id": str(plan["study_id"]),
        "preregistered": True,
        "private_or_fresh_split": True,
        "preregistration_path": _relative(repo, plan_file),
        "preregistration_sha256": _sha256(plan_file),
        "private_split_commitment_sha256": str(plan["private_split_commitment_sha256"]).lower(),
        "repetitions_per_arm": int(plan["repetitions_per_arm"]),
        "model_agent_pairings": plan["model_agent_pairings"],
        "scenarios": plan["scenarios"],
        "expected_attempts": int(queue["expected"]),
        "completed": not missing,
        "runs": ordered_runs,
        "builder": {
            "expected": int(queue["expected"]),
            "observed": len(ordered_runs),
            "missing": len(missing),
            "missing_run_ids": missing,
        },
    }

    validation = validate_p2_result(package, root=repo)
    package["validation"] = validation
    return package


def _pairing(row: Mapping[str, Any]) -> Tuple[str, str, str]:
    return (
        str(row.get("model_display_name", "")).strip(),
        str(row.get("agent", "")).strip(),
        str(row.get("reasoning_effort", "")).strip(),
    )


def _qs_rate(rows: Iterable[Mapping[str, Any]], arm: str) -> Optional[float]:
    selected = [
        bool(row.get("qualified_success"))
        for row in rows
        if str(row.get("arm", "")).strip() == arm and isinstance(row.get("qualified_success"), bool)
    ]
    if not selected:
        return None
    return sum(1 for value in selected if value) / len(selected)


def build_replication_package(
    root: Path,
    p2_packages: Sequence[Path],
) -> Dict[str, Any]:
    repo = root.resolve()
    entries: List[Dict[str, Any]] = []
    source_packages: List[str] = []

    for path in p2_packages:
        package_path = path.resolve()
        package = _read_json(package_path)
        validation = validate_p2_result(package, root=repo)
        if validation["status"] != "VALID":
            raise ValueError(
                f"invalid completed P2 package {package_path}: "
                + "; ".join(validation["errors"])
            )
        source_packages.append(_relative(repo, package_path))
        rows = [
            row for row in package.get("runs", [])
            if isinstance(row, dict)
        ]
        by_pairing: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}
        for row in rows:
            key = _pairing(row)
            if not all(key):
                raise ValueError(f"incomplete pairing provenance in {package_path}")
            by_pairing.setdefault(key, []).append(row)

        for (model, agent, reasoning), paired_rows in sorted(by_pairing.items()):
            a0 = _qs_rate(paired_rows, "A0")
            a2 = _qs_rate(paired_rows, "A2")
            if a0 is None or a2 is None:
                raise ValueError(f"missing A0/A2 runs for pairing {model}/{agent}/{reasoning}")
            entries.append({
                "model_display_name": model,
                "agent": agent,
                "reasoning_effort": reasoning,
                "study_id": str(package.get("study_id", "")).strip(),
                "a0_qs_rate": a0,
                "a2_qs_rate": a2,
                "completed": True,
                "source_package": _relative(repo, package_path),
            })

    result: Dict[str, Any] = {
        "pairings": entries,
        "source_packages": source_packages,
    }
    validation = validate_replication_result(result)
    result["validation"] = validation
    return result


def build_burden_package(
    results_dir: Path,
    calibration_path: Path,
) -> Dict[str, Any]:
    rows = _load_result_files(results_dir)
    calibration = _read_json(calibration_path)

    result_rows: List[Dict[str, Any]] = []
    fields = (
        "run_id",
        "scenario_id",
        "arm",
        "model_display_name",
        "agent",
        "reasoning_effort",
        "elapsed_seconds",
        "input_tokens",
        "output_tokens",
        "tool_calls",
        "human_interventions",
        "cost_usd",
    )
    for row in rows:
        if str(row.get("arm", "")) not in ARMS:
            continue
        result_rows.append({key: row.get(key) for key in fields if key in row})

    package: Dict[str, Any] = {
        "results": result_rows,
        "error_calibration": calibration,
    }
    validation = validate_burden_error_result(package)
    package["validation"] = validation
    return package


def _write(path: Path, data: Mapping[str, Any]) -> None:
    output = path.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build canonical AuraCode maturity evidence packages")
    sub = parser.add_subparsers(dest="command", required=True)

    p2 = sub.add_parser("p2")
    p2.add_argument("--root", default=".")
    p2.add_argument("--plan", required=True)
    p2.add_argument("--results-dir", required=True)
    p2.add_argument("--output", required=True)
    p2.add_argument("--allow-incomplete", action="store_true")

    rep = sub.add_parser("replication")
    rep.add_argument("--root", default=".")
    rep.add_argument("--p2-package", action="append", required=True)
    rep.add_argument("--output", required=True)

    burden = sub.add_parser("burden")
    burden.add_argument("--results-dir", required=True)
    burden.add_argument("--calibration", required=True)
    burden.add_argument("--output", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "p2":
            package = build_p2_package(
                Path(args.root),
                Path(args.plan),
                Path(args.results_dir),
            )
            _write(Path(args.output), package)
            valid = package["validation"]["status"] == "VALID"
            if not valid and not args.allow_incomplete:
                print(
                    "ERROR: P2 package is incomplete/invalid: "
                    + "; ".join(package["validation"]["errors"])
                )
                return 1
        elif args.command == "replication":
            package = build_replication_package(
                Path(args.root),
                [Path(item) for item in args.p2_package],
            )
            _write(Path(args.output), package)
            valid = package["validation"]["status"] == "VALID"
            if not valid:
                print(
                    "ERROR: replication package invalid: "
                    + "; ".join(package["validation"]["errors"])
                )
                return 1
        else:
            package = build_burden_package(
                Path(args.results_dir),
                Path(args.calibration),
            )
            _write(Path(args.output), package)
            valid = package["validation"]["status"] == "VALID"
            if not valid:
                print(
                    "ERROR: burden package invalid: "
                    + "; ".join(package["validation"]["errors"])
                )
                return 1
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    print(f"{args.command}: package written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
