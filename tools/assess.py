#!/usr/bin/env python3
"""Assess an assessment JSON against the framework profile."""
from pathlib import Path
from typing import Dict, Any, Optional, List
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
VALID_LEVELS = {"AL1", "AL2", "AL3", "AL4"}


def assess_data(
    a: Dict[str, Any],
    root: Optional[Path] = None,
    project_root: Optional[Path] = None,
    verify_evidence_paths: bool = True,
) -> Dict[str, Any]:
    """Assess in-memory assessment data against catalog and profile."""
    base_root = root or ROOT
    level = str(a.get("assurance_level", "")).upper()
    if level not in VALID_LEVELS:
        return {
            "success": False,
            "error": f"Invalid or missing assurance_level: '{level}'. Expected one of {sorted(VALID_LEVELS)}.",
            "project": a.get("project", "unknown"),
            "level": level,
        }

    profile_path = (base_root / "profiles" / f"{level.lower()}.json").resolve()
    # Path traversal safeguard
    profiles_dir = (base_root / "profiles").resolve()
    if not profile_path.is_relative_to(profiles_dir) or not profile_path.exists():
        return {
            "success": False,
            "error": f"Profile file not found for level '{level}'",
            "project": a.get("project", "unknown"),
            "level": level,
        }

    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to load profile '{level}': {e}",
            "project": a.get("project", "unknown"),
            "level": level,
        }

    results = a.get("controls", {})
    if not isinstance(results, dict):
        results = {}

    fail = []
    not_assessed = []
    bad_na = []
    bad_pass = []
    missing_evidence = {}
    passed = []
    na = []

    for cid in profile.get("included_controls", []):
        r = results.get(cid, {"status": "NOT_ASSESSED"})
        status = r.get("status", "NOT_ASSESSED") if isinstance(r, dict) else "NOT_ASSESSED"
        if status == "PASS":
            evidence = r.get("evidence") if isinstance(r, dict) else None
            ev_list = []
            if isinstance(evidence, list):
                ev_list = [str(e).strip() for e in evidence if str(e).strip()]
            elif isinstance(evidence, str) and evidence.strip():
                ev_list = [evidence.strip()]

            if not ev_list:
                bad_pass.append(cid)
            else:
                missing_files = []
                if verify_evidence_paths and project_root is not None:
                    for item in ev_list:
                        if item.lower().startswith(("http://", "https://", "urn:", "ftp://")):
                            continue
                        p = (project_root / item).resolve()
                        if not p.exists():
                            missing_files.append(item)

                if missing_files:
                    bad_pass.append(cid)
                    missing_evidence[cid] = missing_files
                else:
                    passed.append(cid)
        elif status == "FAIL":
            fail.append(cid)
        elif status == "NA":
            if not isinstance(r, dict) or not r.get("rationale", "").strip():
                bad_na.append(cid)
            else:
                na.append(cid)
        else:
            not_assessed.append(cid)

    satisfied = (len(fail) == 0 and len(bad_na) == 0 and len(bad_pass) == 0 and len(not_assessed) == 0)
    return {
        "success": satisfied,
        "project": a.get("project", "unnamed"),
        "level": level,
        "passed": passed,
        "invalid_pass": bad_pass,
        "missing_evidence": missing_evidence,
        "fail": fail,
        "na": na,
        "invalid_na": bad_na,
        "not_assessed": not_assessed,
        "total_required": len(profile.get("included_controls", [])),
    }


def assess_file(
    filepath: Path,
    max_file_bytes: int = 1_000_000,
    verify_evidence_paths: bool = True,
) -> Dict[str, Any]:
    """Load and assess a file path against the framework profile."""
    p = Path(filepath).resolve()
    if not p.exists() or not p.is_file():
        return {"success": False, "error": f"Assessment file not found: {p}"}

    try:
        size = p.stat().st_size
        if size > max_file_bytes:
            return {"success": False, "error": f"Assessment file size ({size} bytes) exceeds limit ({max_file_bytes} bytes)"}
        content = p.read_text(encoding="utf-8")
        data = json.loads(content)
    except Exception as e:
        return {"success": False, "error": f"Failed to read/parse assessment JSON: {e}"}

    if not isinstance(data, dict):
        return {"success": False, "error": "Invalid assessment JSON: root must be an object"}

    return assess_data(
        data,
        project_root=p.parent,
        verify_evidence_paths=verify_evidence_paths,
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Assess an assessment JSON against the framework profile.")
    parser.add_argument("assessment_file", help="Path to assessment.json file")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args(argv)

    res = assess_file(Path(args.assessment_file))
    if args.json:
        print(json.dumps(res, indent=2))
        return 0 if res.get("success") else 1

    if res.get("error"):
        print(f"ERROR: {res['error']}")
        return 2

    print(f"Project: {res.get('project')}")
    print(f"Profile: {res.get('level')}")
    print(
        f"PASS={len(res['passed'])} NA={len(res['na'])} FAIL={len(res['fail'])} "
        f"NOT_ASSESSED={len(res['not_assessed'])} INVALID_NA={len(res['invalid_na'])} "
        f"INVALID_PASS={len(res.get('invalid_pass', []))}"
    )

    if res["fail"]:
        print("FAIL:", ", ".join(res["fail"]))
    if res.get("invalid_pass"):
        print("PASS without valid evidence:", ", ".join(res["invalid_pass"]))
        if res.get("missing_evidence"):
            for cid, mfiles in res["missing_evidence"].items():
                print(f"  - {cid}: non-existent evidence file(s): {', '.join(mfiles)}")
    if res["invalid_na"]:
        print("NA without rationale:", ", ".join(res["invalid_na"]))
    if res["not_assessed"]:
        print("NOT_ASSESSED:", ", ".join(res["not_assessed"]))

    if not res["success"]:
        print("\nPROFILE NOT SATISFIED")
        return 1

    print("\nPROFILE SATISFIED (self-assessment; not certification)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
