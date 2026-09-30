#!/usr/bin/env python3
"""Fail-closed maturity gate for the first stable AuraCode 1.0 release."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
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





def _verify_pass_metadata(root: Path, entry: Mapping[str, Any], evidence: object) -> Dict[str, Any]:
    """Require reviewer provenance and a pinned hash for any declared maturity PASS."""
    reviewer = str(entry.get("reviewed_by", "")).strip()
    reviewed_at = str(entry.get("reviewed_at", "")).strip()
    expected_hash = str(entry.get("evidence_sha256", "")).strip().lower()
    if not reviewer:
        return {"valid": False, "reason": "PASS requires reviewed_by"}
    if not reviewed_at:
        return {"valid": False, "reason": "PASS requires reviewed_at"}
    try:
        datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    except ValueError:
        return {"valid": False, "reason": "reviewed_at must be ISO-8601"}
    if len(expected_hash) != 64 or any(ch not in "0123456789abcdef" for ch in expected_hash):
        return {"valid": False, "reason": "PASS requires a 64-character evidence_sha256"}

    values = evidence if isinstance(evidence, list) else []
    normalized = [str(item).strip() for item in values if str(item).strip()]
    if len(normalized) != 1:
        return {"valid": False, "reason": "PASS requires exactly one canonical evidence file"}
    candidate = Path(normalized[0])
    if candidate.is_absolute():
        return {"valid": False, "reason": "canonical evidence path must be repository-relative"}
    path = (root.resolve() / candidate).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return {"valid": False, "reason": "canonical evidence path escapes repository root"}
    if not path.is_file():
        return {"valid": False, "reason": "canonical evidence file does not exist"}
    actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        return {
            "valid": False,
            "reason": f"canonical evidence hash mismatch: expected {expected_hash}, got {actual_hash}",
        }
    return {"valid": True, "reason": "", "actual_sha256": actual_hash}


def _collect_nested_evidence(value: object) -> List[str]:
    """Collect nested fields explicitly named 'evidence' from a canonical package."""
    refs: List[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "evidence" and isinstance(item, list):
                refs.extend(str(ref).strip() for ref in item if str(ref).strip())
            else:
                refs.extend(_collect_nested_evidence(item))
    elif isinstance(value, list):
        for item in value:
            refs.extend(_collect_nested_evidence(item))
    return refs


def _verify_nested_evidence(root: Path, data: Mapping[str, Any]) -> Dict[str, Any]:
    refs = _collect_nested_evidence(data)
    missing: List[str] = []
    rejected: List[str] = []
    root_resolved = root.resolve()
    for ref in refs:
        if ref.lower().startswith(("http://", "https://", "ftp://", "urn:")):
            rejected.append(ref)
            continue
        candidate = (root_resolved / ref).resolve()
        try:
            candidate.relative_to(root_resolved)
        except ValueError:
            rejected.append(ref)
            continue
        if not candidate.is_file():
            missing.append(ref)
    if rejected:
        return {
            "valid": False,
            "reason": "nested evidence must be local repository files",
            "rejected": sorted(set(rejected)),
            "missing": sorted(set(missing)),
        }
    if missing:
        return {
            "valid": False,
            "reason": "one or more nested evidence files do not exist",
            "rejected": [],
            "missing": sorted(set(missing)),
        }
    return {"valid": True, "reason": "", "rejected": [], "missing": []}


def _semantic_validate_evidence(root: Path, criterion_id: str, evidence: object) -> Dict[str, Any]:
    """Validate maturity evidence content, not just path existence."""
    values = evidence if isinstance(evidence, list) else []
    normalized = [str(item).strip() for item in values if str(item).strip()]
    if len(normalized) != 1:
        return {
            "valid": False,
            "reason": "maturity criterion PASS requires exactly one canonical JSON evidence package",
        }
    path = (root / normalized[0]).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return {"valid": False, "reason": "maturity evidence must remain inside repository root"}
    if path.suffix.lower() != ".json":
        return {"valid": False, "reason": "semantic maturity evidence must be a JSON file"}
    try:
        data = _load_json(path)
    except ValueError as exc:
        return {"valid": False, "reason": str(exc)}

    root_str = str(root)
    added_root_path = root_str not in sys.path
    if added_root_path:
        sys.path.insert(0, root_str)
    try:
        from validation.tools.maturity_studies import validate_evidence_for_criterion
        registry = None
        if criterion_id == "MAT-04":
            registry = _load_json(root / "validation" / "benchmark-registry.json")
        result = validate_evidence_for_criterion(criterion_id, data, registry)
    except (ImportError, ValueError) as exc:
        return {"valid": False, "reason": f"semantic validator unavailable/invalid: {exc}"}
    finally:
        if added_root_path and root_str in sys.path:
            sys.path.remove(root_str)

    if str(result.get("status", "")).upper() != "VALID":
        errors = result.get("errors", [])
        detail = "; ".join(str(item) for item in errors) if isinstance(errors, list) else "invalid evidence"
        return {"valid": False, "reason": detail or "semantic evidence validation failed"}

    nested = _verify_nested_evidence(root, data)
    if not nested["valid"]:
        detail = str(nested["reason"])
        if nested.get("missing"):
            detail += ": " + ", ".join(nested["missing"])
        if nested.get("rejected"):
            detail += ": " + ", ".join(nested["rejected"])
        return {"valid": False, "reason": detail}
    return {"valid": True, "reason": "", "report": result}


def evaluate_maturity(root: Path = ROOT) -> Dict[str, Any]:
    root = root.resolve()
    criteria_data = _load_json(root / "validation" / "maturity-criteria.json")
    evidence_data = _load_json(root / "validation" / "maturity-evidence.json")
    criteria_raw = criteria_data.get("criteria", [])
    if not isinstance(criteria_raw, list):
        raise ValueError("maturity-criteria.json criteria must be an array")
    evidence_map_raw = evidence_data.get("criteria", {})
    evidence_map = evidence_map_raw if isinstance(evidence_map_raw, dict) else {}

    root_str = str(root)
    added_root_path = root_str not in sys.path
    if added_root_path:
        sys.path.insert(0, root_str)
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
    finally:
        if added_root_path and root_str in sys.path:
            sys.path.remove(root_str)

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
                metadata = _verify_pass_metadata(root, entry, evidence)
                if not metadata["valid"]:
                    status = "INVALID_PASS"
                    reason = str(metadata["reason"])
                else:
                    semantic = _semantic_validate_evidence(root, criterion_id, evidence)
                    if semantic["valid"]:
                        status = "PASS"
                        reason = str(entry.get("rationale", "")).strip() or "Evidence verified."
                    else:
                        status = "INVALID_PASS"
                        reason = str(semantic["reason"])
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
