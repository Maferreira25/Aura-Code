#!/usr/bin/env python3
"""Continuous Assurance snapshots and deterministic regression detection."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from tools.assurance_state import load_state
from tools.audit import audit_workspace


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _git_revision(workspace: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "UNKNOWN"
    return proc.stdout.strip() if proc.returncode == 0 and proc.stdout.strip() else "UNKNOWN"


def _count_statuses(items: Mapping[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for raw in items.values():
        if not isinstance(raw, dict):
            continue
        status = str(raw.get("status", "UNKNOWN")).upper()
        counts[status] = counts.get(status, 0) + 1
    return counts


def _finding_counts(state: Mapping[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    findings = state.get("open_findings", [])
    if not isinstance(findings, list):
        return counts
    for item in findings:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "OPEN")).upper()
        if status in {"RESOLVED", "CLOSED", "FALSE_POSITIVE"}:
            continue
        severity = str(item.get("severity", "UNKNOWN")).upper()
        counts[severity] = counts.get(severity, 0) + 1
    return counts


def build_snapshot(workspace: Path, state_path: Optional[Path] = None) -> Dict[str, Any]:
    root = workspace.resolve()
    actual_state_path = state_path.resolve() if state_path else root / ".auracode" / "assurance-state.json"
    state = load_state(actual_state_path)
    audit = audit_workspace(root)

    controls = state.get("controls", {})
    control_map = controls if isinstance(controls, dict) else {}
    guarantees = audit.get("guarantees", {})
    guarantee_map = guarantees if isinstance(guarantees, dict) else {}
    violations = audit.get("violations_summary", {})
    violation_map = violations if isinstance(violations, dict) else {}

    return {
        "snapshot_version": "1.0",
        "captured_at": _now(),
        "project": state.get("project"),
        "assurance_level": state.get("assurance_level"),
        "stage": state.get("current_stage"),
        "source_revision": _git_revision(root),
        "control_statuses": {
            control_id: str(result.get("status", "UNKNOWN")).upper()
            for control_id, result in control_map.items()
            if isinstance(result, dict)
        },
        "control_counts": _count_statuses(control_map),
        "open_findings_by_severity": _finding_counts(state),
        "audit_status": audit.get("status"),
        "guarantees": {
            name: str(result.get("status", "NOT_RUN")).upper()
            for name, result in guarantee_map.items()
            if isinstance(result, dict)
        },
        "violations": violation_map,
    }


def compare_snapshots(previous: Mapping[str, Any], current: Mapping[str, Any]) -> Dict[str, Any]:
    blockers: List[str] = []
    warnings: List[str] = []

    prev_controls = previous.get("control_statuses", {})
    cur_controls = current.get("control_statuses", {})
    if isinstance(prev_controls, dict) and isinstance(cur_controls, dict):
        for control_id, old_status in prev_controls.items():
            if str(old_status).upper() != "PASS":
                continue
            new_status = str(cur_controls.get(control_id, "UNKNOWN")).upper()
            if new_status in {"FAIL", "UNKNOWN"}:
                blockers.append(f"control regression {control_id}: PASS -> {new_status}")
            elif new_status in {"WAIVED", "NOT_APPLICABLE"}:
                warnings.append(f"control assurance weakened {control_id}: PASS -> {new_status}")

    prev_guarantees = previous.get("guarantees", {})
    cur_guarantees = current.get("guarantees", {})
    if isinstance(prev_guarantees, dict) and isinstance(cur_guarantees, dict):
        for name, old_status in prev_guarantees.items():
            if str(old_status).upper() != "PASS":
                continue
            new_status = str(cur_guarantees.get(name, "NOT_RUN")).upper()
            if new_status != "PASS":
                blockers.append(f"deterministic guarantee regression {name}: PASS -> {new_status}")

    prev_findings = previous.get("open_findings_by_severity", {})
    cur_findings = current.get("open_findings_by_severity", {})
    if isinstance(prev_findings, dict) and isinstance(cur_findings, dict):
        for severity in ("CRITICAL", "HIGH"):
            before = int(prev_findings.get(severity, 0) or 0)
            after = int(cur_findings.get(severity, 0) or 0)
            if after > before:
                blockers.append(f"new open {severity} findings: {before} -> {after}")

    prev_violations = previous.get("violations", {})
    cur_violations = current.get("violations", {})
    if isinstance(prev_violations, dict) and isinstance(cur_violations, dict):
        for key in ("architecture_violations", "test_integrity"):
            before_raw = prev_violations.get(key)
            after_raw = cur_violations.get(key)
            if isinstance(before_raw, int) and isinstance(after_raw, int) and after_raw > before_raw:
                blockers.append(f"{key} increased: {before_raw} -> {after_raw}")

    decision = "BLOCK" if blockers else "ALLOW"
    return {
        "decision": decision,
        "regression_detected": bool(blockers or warnings),
        "blockers": blockers,
        "warnings": warnings,
        "previous_revision": previous.get("source_revision"),
        "current_revision": current.get("source_revision"),
        "evaluated_at": _now(),
    }


def save_snapshot(snapshot: Mapping[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(dict(snapshot), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def _default_output(workspace: Path, snapshot: Mapping[str, Any]) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    revision = str(snapshot.get("source_revision", "UNKNOWN"))[:12]
    return workspace.resolve() / ".auracode" / "assurance-history" / f"{stamp}-{revision}.json"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AuraCode Continuous Assurance")
    sub = parser.add_subparsers(dest="action", required=True)

    snap = sub.add_parser("snapshot", help="Capture current deterministic assurance posture")
    snap.add_argument("target", nargs="?", default=".")
    snap.add_argument("--state")
    snap.add_argument("--output")
    snap.add_argument("--json", action="store_true")

    comp = sub.add_parser("compare", help="Compare two assurance snapshots")
    comp.add_argument("previous")
    comp.add_argument("current")
    comp.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    if args.action == "snapshot":
        workspace = Path(args.target).resolve()
        state_path = Path(args.state).resolve() if args.state else None
        try:
            snapshot = build_snapshot(workspace, state_path)
        except (ValueError, OSError) as exc:
            print(f"ERROR: {exc}")
            return 2
        output = Path(args.output).resolve() if args.output else _default_output(workspace, snapshot)
        save_snapshot(snapshot, output)
        payload: Dict[str, Any] = {"status": "PASS", "output": str(output), "snapshot": snapshot}
        code = 0
    else:
        try:
            previous = json.loads(Path(args.previous).read_text(encoding="utf-8"))
            current = json.loads(Path(args.current).read_text(encoding="utf-8"))
            if not isinstance(previous, dict) or not isinstance(current, dict):
                raise ValueError("snapshot roots must be JSON objects")
            payload = compare_snapshots(previous, current)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            print(f"ERROR: {exc}")
            return 2
        code = 0 if payload["decision"] == "ALLOW" else 1

    if getattr(args, "json", False):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.action == "snapshot":
        print(f"PASS: snapshot saved to {payload['output']}")
    else:
        print(f"{payload['decision']}: continuous assurance comparison")
        for reason in payload.get("blockers", []):
            print(f"- BLOCK: {reason}")
        for warning in payload.get("warnings", []):
            print(f"- WARN: {warning}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
