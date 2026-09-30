#!/usr/bin/env python3
"""Fail-closed maturity gate for the first stable AuraCode 1.0 release."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to load {path}: {exc}")
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def _verify_local_evidence(root: Path, values: object) -> Dict[str, Any]:
    if not isinstance(values, list):
        return {"valid": False, "missing": [], "reason": "evidence must be an array"}
    normalized = [str(item).strip() for item in values if str(item).strip()]
    if not normalized:
        return {"valid": False, "missing": [], "reason": "PASS requires at least one evidence file"}

    missing: List[str] = []
    rejected: List[str] = []
    root_resolved = root.resolve()
    for item in normalized:
        if item.lower().startswith(("http://", "https://", "ftp://", "urn:")):
            rejected.append(item)
            continue
        candidate = (root_resolved / item).resolve()
        try:
            candidate.relative_to(root_resolved)
        except ValueError:
            rejected.append(item)
            continue
        if not candidate.is_file():
            missing.append(item)

    if rejected:
        return {
            "valid": False,
            "missing": missing,
            "rejected": rejected,
            "reason": "maturity evidence must be a local repository file, not an external/unbounded reference",
        }
    if missing:
        return {
            "valid": False,
            "missing": missing,
            "reason": "one or more evidence files do not exist",
        }
    return {"valid": True, "missing": [], "reason": ""}


def evaluate_maturity(root: Path = ROOT) -> Dict[str, Any]:
    root = root.resolve()
    criteria_data = _load_json(root / "validation" / "maturity-criteria.json")
    evidence_data = _load_json(root / "validation" / "maturity-evidence.json")
    criteria_raw = criteria_data.get("criteria", [])
    if not isinstance(criteria_raw, list):
        raise ValueError("maturity-criteria.json criteria must be an array")
    evidence_map_raw = evidence_data.get("criteria", {})
    evidence_map = evidence_map_raw if isinstance(evidence_map_raw, dict) else {}

    try:
        from validation.tools.validate_experiment_evidence import evaluate_p1, load_results
        rows, result_load_errors = load_results(root / "validation" / "results")
        p1 = evaluate_p1(rows)
        if result_load_errors:
            p1["errors"] = list(p1.get("errors", [])) + result_load_errors
            p1["formal_p1_complete"] = False
            p1["comparative_signal_interpretable"] = False
    except ImportError as exc:
        p1 = {
            "formal_p1_complete": False,
            "comparative_signal_interpretable": False,
            "ceiling_effect": False,
            "automated_runs": 0,
            "automated_expected": 90,
            "errors": [f"P1 evaluator unavailable: {exc}"],
        }

    results: List[Dict[str, Any]] = []
    blockers: List[str] = []

    for criterion in criteria_raw:
        if not isinstance(criterion, dict):
            blockers.append("invalid maturity criterion entry")
            continue
        criterion_id = str(criterion.get("id", "")).strip()
        title = str(criterion.get("title", "")).strip()
        mode = str(criterion.get("mode", "")).strip()
        required = bool(criterion.get("required", True))
        if not criterion_id:
            blockers.append("maturity criterion missing id")
            continue

        if mode == "auto_p1":
            passed = bool(p1.get("formal_p1_complete")) and bool(
                p1.get("comparative_signal_interpretable")
            )
            status = "PASS" if passed else "UNKNOWN"
            reason = (
                "Frozen P1 is complete and comparative signal is interpretable."
                if passed
                else "Frozen P1 is incomplete or non-discriminative."
            )
            evidence = ["validation/results", "validation/PREREGISTRATION-P1.md"]
        elif mode == "evidence":
            raw = evidence_map.get(criterion_id, {})
            entry = raw if isinstance(raw, dict) else {}
            declared = str(entry.get("status", "UNKNOWN")).upper()
            evidence = entry.get("evidence", [])
            verification = _verify_local_evidence(root, evidence)
            if declared == "PASS" and verification["valid"]:
                status = "PASS"
                reason = str(entry.get("rationale", "")).strip() or "Evidence verified."
            elif declared == "PASS":
                status = "INVALID_PASS"
                reason = str(verification["reason"])
            elif declared == "FAIL":
                status = "FAIL"
                reason = str(entry.get("rationale", "")).strip() or "Criterion failed."
            else:
                status = "UNKNOWN"
                reason = str(entry.get("rationale", "")).strip() or "Criterion not yet evidenced."
        else:
            status = "INVALID"
            evidence = []
            reason = f"Unsupported criterion mode '{mode}'"

        item = {
            "id": criterion_id,
            "title": title,
            "required": required,
            "status": status,
            "evidence": evidence,
            "reason": reason,
        }
        results.append(item)
        if required and status != "PASS":
            blockers.append(f"{criterion_id}: {status} - {reason}")

    ready = not blockers
    return {
        "target": criteria_data.get("target", "stable-1.0"),
        "decision": "ALLOW" if ready else "BLOCK",
        "ready": ready,
        "criteria": results,
        "blockers": blockers,
        "p1": {
            "formal_p1_complete": p1.get("formal_p1_complete"),
            "comparative_signal_interpretable": p1.get("comparative_signal_interpretable"),
            "ceiling_effect": p1.get("ceiling_effect"),
            "automated_runs": p1.get("automated_runs"),
            "automated_expected": p1.get("automated_expected"),
        },
        "claim_boundary": (
            "ALLOW means the repository contains the configured evidence package for a stable-1.0 candidate. "
            "It is not third-party certification or a guarantee of defect-free software."
        ),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AuraCode stable-release maturity gate")
    parser.add_argument("target", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report-only", action="store_true", help="Always exit 0 after producing the report")
    args = parser.parse_args(argv)

    try:
        report = evaluate_maturity(Path(args.target))
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Maturity target: {report['target']}")
        print(f"Decision: {report['decision']}")
        for item in report["criteria"]:
            print(f"- {item['id']} {item['status']}: {item['title']}")
            if item["status"] != "PASS":
                print(f"  {item['reason']}")
        print(report["claim_boundary"])

    if args.report_only:
        return 0
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
