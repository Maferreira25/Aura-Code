#!/usr/bin/env python3
"""Dogfood AuraCode's assurance pipeline against a repository, fail closed."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from tools.assurance_state import (
    STAGES,
    advance_state,
    import_assessment,
    import_audit_result,
    new_state,
)
from tools.audit import audit_workspace


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to read {path}: {exc}")
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def dogfood_repository(
    workspace: Path,
    assessment_path: Path,
    framework_root: Path,
) -> Dict[str, Any]:
    root = workspace.resolve()
    assessment_file = assessment_path.resolve()
    framework = framework_root.resolve()
    assessment = _load_json(assessment_file)

    project = str(assessment.get("project", "")).strip() or root.name
    level = str(assessment.get("assurance_level", "")).upper()
    framework_version = str(assessment.get("framework_version", "unknown"))

    state = new_state(project, level, framework_version)
    assessment_result = import_assessment(
        state,
        assessment,
        project_root=root,
        root=framework,
    )

    audit_result = audit_workspace(root)
    audit_import = import_audit_result(
        state,
        audit_result,
        [str(assessment_file), "dogfood:audit_workspace"],
    )

    transitions: List[Dict[str, Any]] = []
    blocked_at: Optional[str] = None
    for target in STAGES[1:]:
        result = advance_state(state, target, root=framework)
        transitions.append(result)
        if not result["allowed"]:
            blocked_at = target
            break

    return {
        "status": "PASS" if blocked_at is None else "BLOCKED",
        "project": project,
        "assurance_level": level,
        "assessment": assessment_result,
        "audit": {
            "status": audit_result.get("status"),
            "import": audit_import,
        },
        "current_stage": state.get("current_stage"),
        "assurance_status": state.get("assurance_status"),
        "blocked_at": blocked_at,
        "transitions": transitions,
        "state": state,
        "interpretation": (
            "BLOCKED is a valid fail-closed result. The tool never fabricates actor "
            "provenance or upgrades missing evidence into PASS."
        ),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Dogfood AuraCode assurance against a repository")
    parser.add_argument("target", nargs="?", default=".")
    parser.add_argument("--assessment", default="self-assessment.json")
    parser.add_argument("--framework-root", default=None)
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Always exit 0 after producing the dogfood report",
    )
    args = parser.parse_args(argv)

    workspace = Path(args.target).resolve()
    assessment = Path(args.assessment)
    if not assessment.is_absolute():
        assessment = workspace / assessment
    framework_root = Path(args.framework_root).resolve() if args.framework_root else Path(__file__).resolve().parents[1]

    try:
        report = dogfood_repository(workspace, assessment, framework_root)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Dogfood status: {report['status']}")
        print(f"Project: {report['project']} ({report['assurance_level']})")
        print(f"Audit: {report['audit']['status']}")
        print(f"Current stage: {report['current_stage']}")
        if report["blocked_at"]:
            print(f"Blocked at: {report['blocked_at']}")
            last = report["transitions"][-1]
            for reason in last.get("reasons", []):
                print(f"- {reason}")
        print(report["interpretation"])

    if args.report_only:
        return 0
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
