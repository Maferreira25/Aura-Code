#!/usr/bin/env python3
"""CLI adapter for AuraCode's persistent assurance-state engine."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from tools.assurance_state import (
    LEGACY_STATUS_MAP,
    STAGES,
    VALID_ACTOR_KINDS,
    VALID_FINDING_SEVERITIES,
    VALID_FINDING_STATUSES,
    VALID_LEVELS,
    VALID_ROLES,
    VALID_STATUSES,
    _read_json,
    advance_state,
    evaluate_gate,
    import_assessment,
    import_audit_result,
    load_state,
    mark_remediation_implemented,
    new_state,
    record_actor,
    record_control,
    register_finding,
    revalidate_finding,
    save_state,
    start_remediation,
)

def default_state_path(target: Path) -> Path:
    return target.resolve() / ".auracode" / "assurance-state.json"


def _state_path(target: str, state_path: Optional[str]) -> Path:
    return Path(state_path).resolve() if state_path else default_state_path(Path(target))


def build_parser() -> "argparse.ArgumentParser":
    import argparse
    parser = argparse.ArgumentParser(description="AuraCode persistent assurance-state decision engine")
    sub = parser.add_subparsers(dest="action", required=True)

    init_p = sub.add_parser("init", help="Create a new assurance state")
    init_p.add_argument("target", nargs="?", default=".")
    init_p.add_argument("--project", required=True)
    init_p.add_argument("--level", required=True, choices=VALID_LEVELS)
    init_p.add_argument("--framework-version", default="unknown")
    init_p.add_argument("--state")
    init_p.add_argument("--json", action="store_true")

    audit_import_p = sub.add_parser("import-audit", help="Import a deterministic audit report into assurance state")
    audit_import_p.add_argument("target", nargs="?", default=".")
    audit_import_p.add_argument("--audit", required=True)
    audit_import_p.add_argument("--evidence", action="append", default=[])
    audit_import_p.add_argument("--state")
    audit_import_p.add_argument("--json", action="store_true")

    import_p = sub.add_parser("import-assessment", help="Import a validated assessment into assurance state")
    import_p.add_argument("target", nargs="?", default=".")
    import_p.add_argument("--assessment", required=True)
    import_p.add_argument("--state")
    import_p.add_argument("--json", action="store_true")

    actor_p = sub.add_parser("actor", help="Record actor provenance")
    actor_p.add_argument("target", nargs="?", default=".")
    actor_p.add_argument("--role", required=True, choices=sorted(VALID_ROLES))
    actor_p.add_argument("--actor-id", required=True)
    actor_p.add_argument("--kind", required=True, choices=sorted(VALID_ACTOR_KINDS))
    actor_p.add_argument("--session-id")
    actor_p.add_argument("--model-id")
    actor_p.add_argument("--state")
    actor_p.add_argument("--json", action="store_true")

    control_p = sub.add_parser("control", help="Record one control result")
    control_p.add_argument("target", nargs="?", default=".")
    control_p.add_argument("--id", required=True)
    control_p.add_argument("--status", required=True, choices=sorted(VALID_STATUSES | set(LEGACY_STATUS_MAP)))
    control_p.add_argument("--evidence", action="append", default=[])
    control_p.add_argument("--rationale", default="")
    control_p.add_argument("--state")
    control_p.add_argument("--json", action="store_true")

    finding_p = sub.add_parser("finding", help="Manage finding remediation and independent revalidation")
    finding_sub = finding_p.add_subparsers(dest="finding_action", required=True)

    finding_add = finding_sub.add_parser("add", help="Register an audit/review finding")
    finding_add.add_argument("target", nargs="?", default=".")
    finding_add.add_argument("--id", required=True)
    finding_add.add_argument("--severity", required=True, choices=sorted(VALID_FINDING_SEVERITIES))
    finding_add.add_argument("--title", required=True)
    finding_add.add_argument("--status", default="OPEN", choices=sorted(VALID_FINDING_STATUSES))
    finding_add.add_argument("--evidence", action="append", default=[])
    finding_add.add_argument("--state")
    finding_add.add_argument("--json", action="store_true")

    finding_start = finding_sub.add_parser("start", help="Start remediation for a confirmed finding")
    finding_start.add_argument("target", nargs="?", default=".")
    finding_start.add_argument("--id", required=True)
    finding_start.add_argument("--evidence", action="append", default=[])
    finding_start.add_argument("--state")
    finding_start.add_argument("--json", action="store_true")

    finding_impl = finding_sub.add_parser("implemented", help="Record remediation implementation evidence")
    finding_impl.add_argument("target", nargs="?", default=".")
    finding_impl.add_argument("--id", required=True)
    finding_impl.add_argument("--evidence", action="append", required=True)
    finding_impl.add_argument("--state")
    finding_impl.add_argument("--json", action="store_true")

    finding_reval = finding_sub.add_parser("revalidate", help="Record independent revalidation result")
    finding_reval.add_argument("target", nargs="?", default=".")
    finding_reval.add_argument("--id", required=True)
    finding_reval.add_argument("--result", required=True, choices=["PASS", "FAIL"])
    finding_reval.add_argument("--evidence", action="append", required=True)
    finding_reval.add_argument("--state")
    finding_reval.add_argument("--json", action="store_true")

    gate_p = sub.add_parser("gate", help="Evaluate or advance one sequential assurance gate")
    gate_p.add_argument("target", nargs="?", default=".")
    gate_p.add_argument("--to", required=True, choices=STAGES)
    gate_p.add_argument("--advance", action="store_true")
    gate_p.add_argument("--state")
    gate_p.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    state_path = _state_path(args.target, getattr(args, "state", None))

    if args.action == "init":
        if state_path.exists():
            print(f"ERROR: assurance state already exists: {state_path}")
            return 2
        state = new_state(args.project, args.level, args.framework_version)
        save_state(state_path, state)
        payload = {"status": "PASS", "state_file": str(state_path), "state": state}
    else:
        try:
            state = load_state(state_path)
        except ValueError as exc:
            print(f"ERROR: {exc}")
            return 2

        if args.action == "import-audit":
            try:
                audit_path = Path(args.audit).resolve()
                audit_result = _read_json(audit_path)
                imported = import_audit_result(
                    state,
                    audit_result,
                    args.evidence or [str(audit_path)],
                )
            except ValueError as exc:
                print(f"ERROR: {exc}")
                return 2
            save_state(state_path, state)
            payload = {
                "status": "PASS",
                "state_file": str(state_path),
                "audit": imported,
            }
        elif args.action == "import-assessment":
            try:
                assessment_path = Path(args.assessment).resolve()
                assessment = _read_json(assessment_path)
                imported = import_assessment(
                    state,
                    assessment,
                    project_root=Path(args.target).resolve(),
                )
            except ValueError as exc:
                print(f"ERROR: {exc}")
                return 2
            save_state(state_path, state)
            payload = {
                "status": "PASS",
                "state_file": str(state_path),
                "assessment": imported,
            }
        elif args.action == "finding":
            try:
                if args.finding_action == "add":
                    finding = register_finding(
                        state, args.id, args.severity, args.title, args.status, args.evidence
                    )
                elif args.finding_action == "start":
                    finding = start_remediation(state, args.id, args.evidence)
                elif args.finding_action == "implemented":
                    finding = mark_remediation_implemented(state, args.id, args.evidence)
                else:
                    finding = revalidate_finding(state, args.id, args.result, args.evidence)
            except ValueError as exc:
                print(f"ERROR: {exc}")
                return 2
            save_state(state_path, state)
            payload = {
                "status": "PASS",
                "state_file": str(state_path),
                "finding": finding,
            }
        elif args.action == "actor":
            record_actor(state, args.role, args.actor_id, args.kind, args.session_id, args.model_id)
            save_state(state_path, state)
            payload = {"status": "PASS", "state_file": str(state_path), "actor": args.role}
        elif args.action == "control":
            record_control(state, args.id, args.status, args.evidence, args.rationale)
            save_state(state_path, state)
            payload = {"status": "PASS", "state_file": str(state_path), "control": args.id.upper()}
        else:
            try:
                payload = advance_state(state, args.to) if args.advance else evaluate_gate(state, args.to)
            except ValueError as exc:
                print(f"ERROR: {exc}")
                return 2
            if args.advance:
                save_state(state_path, state)

    if getattr(args, "json", False):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.action == "gate":
        print(f"{payload['decision']}: {payload['from_stage']} -> {payload['target_stage']}")
        for reason in payload.get("reasons", []):
            print(f"- {reason}")
    else:
        print(f"{payload['status']}: {payload.get('state_file')}")
    return 0 if payload.get("decision", payload.get("status")) in {"ALLOW", "PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
