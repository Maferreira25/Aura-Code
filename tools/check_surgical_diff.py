#!/usr/bin/env python3
"""Surgical Change & Anti-Reward-Hacking Diff Engine.

Analyzes proposed diffs or repository changes to ensure changes are strictly
surgical: within allowed scope, preserving existing tests (preventing reward hacking),
and avoiding unrelated edits to adjacent files.
"""

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


SAFE_GIT_ARGS = [
    "-c", "core.fsmonitor=",
    "-c", "core.hooksPath=",
    "-c", "diff.external=",
    "-c", "diff.textconv=false",
]


def get_git_status(repo_dir: Path, timeout: int = 15) -> Tuple[List[Dict[str, str]], Optional[str]]:
    """Get list of changed files and their status from git repository securely."""
    try:
        res = subprocess.run(
            ["git"] + SAFE_GIT_ARGS + ["status", "--porcelain"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
    except Exception as e:
        return [], f"Git status error in {repo_dir}: {e}"

    changes = []
    for line in res.stdout.splitlines():
        if not line.strip():
            continue
        status = line[:2].strip()
        file_path = line[3:].strip()
        # Handle renames e.g. "R  old -> new"
        if "->" in file_path:
            file_path = file_path.split("->")[-1].strip()
        changes.append({
            "status": status,
            "file": file_path.replace("\\", "/")
        })
    return changes, None


def get_git_diff_stats(
    repo_dir: Path,
    changes: Optional[List[Dict[str, str]]] = None,
    timeout: int = 15,
    max_file_bytes: int = 1_000_000,
) -> Dict[str, object]:
    """Calculate diff statistics (added, removed lines) per file covering unstaged, staged, and untracked."""
    stats = {}
    complete = True

    try:
        # Unstaged diff
        res_unstaged = subprocess.run(
            ["git"] + SAFE_GIT_ARGS + ["diff", "--numstat"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
        for line in res_unstaged.stdout.splitlines():
            parts = line.strip().split("\t")
            if len(parts) >= 3:
                added = int(parts[0]) if parts[0].isdigit() else 0
                deleted = int(parts[1]) if parts[1].isdigit() else 0
                path = parts[2].replace("\\", "/")
                stats[path] = {"added": added, "deleted": deleted}

        # Staged diff
        res_staged = subprocess.run(
            ["git"] + SAFE_GIT_ARGS + ["diff", "--cached", "--numstat"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
        for line in res_staged.stdout.splitlines():
            parts = line.strip().split("\t")
            if len(parts) >= 3:
                added = int(parts[0]) if parts[0].isdigit() else 0
                deleted = int(parts[1]) if parts[1].isdigit() else 0
                path = parts[2].replace("\\", "/")
                if path in stats:
                    stats[path]["added"] += added
                    stats[path]["deleted"] += deleted
                else:
                    stats[path] = {"added": added, "deleted": deleted}
    except Exception:
        return {"complete": False, "files": {}, "total_added": 0, "total_deleted": 0}

    # If changes provided or discoverable, count untracked text files
    if changes is not None:
        for c in changes:
            if c.get("status") == "??":
                fpath = repo_dir / c["file"]
                if fpath.is_file():
                    try:
                        sz = fpath.stat().st_size
                        if sz > max_file_bytes:
                            complete = False
                        else:
                            content = fpath.read_text(encoding="utf-8", errors="replace")
                            line_count = len(content.splitlines())
                            rel_key = c["file"].replace("\\", "/")
                            if rel_key in stats:
                                stats[rel_key]["added"] += line_count
                            else:
                                stats[rel_key] = {"added": line_count, "deleted": 0}
                    except Exception:
                        complete = False

    total_added = sum(s["added"] for s in stats.values())
    total_deleted = sum(s["deleted"] for s in stats.values())

    return {
        "complete": complete,
        "files": stats,
        "total_added": total_added,
        "total_deleted": total_deleted,
    }


def is_path_in_scope(file_path: str, allowed_patterns: List[str]) -> bool:
    """Check if file matches any of the allowed glob patterns."""
    if not allowed_patterns:
        return True
    norm_path = file_path.replace("\\", "/")
    for pat in allowed_patterns:
        pat = pat.replace("\\", "/")
        if fnmatch.fnmatch(norm_path, pat):
            return True
        if "/" not in pat and fnmatch.fnmatch(Path(norm_path).name, pat):
            return True
        if pat.endswith("/") and norm_path.startswith(pat):
            return True
    return False


PROTECTED_CONFIG_FILES = {
    "scenario.json", "contracts.json", "evaluation.md", ".assurance-run.json",
    "tox.ini", "pytest.ini", "conftest.py"
}


def is_test_file(file_path: str) -> bool:
    """Determine if a file is an automated test, benchmark, or evaluation file."""
    norm = file_path.replace("\\", "/").lower()
    parts = norm.split("/")
    filename = parts[-1]
    if "tests" in parts or "test" in parts or ".github" in parts:
        return True
    if parts and parts[0] == "validation":
        return True
    if filename.startswith("test_") or filename.endswith("_test.py") or filename.endswith("_spec.py"):
        return True
    if filename in PROTECTED_CONFIG_FILES:
        return True
    return False


def check_surgical_diff(
    repo_dir: Path,
    allowed_scope: Optional[List[str]] = None,
    allow_test_modifications: bool = False,
    max_modified_lines: int = 500,
    direct_changes: Optional[List[Dict[str, str]]] = None,
    direct_stats: Optional[Dict[str, object]] = None,
    block_on_excessive_churn: bool = False,
) -> Dict[str, object]:
    """Audit repository diff against surgical change and evaluation integrity rules."""
    repo_dir = Path(repo_dir).resolve()
    
    if direct_changes is not None:
        changes = direct_changes
        err = None
    else:
        changes, err = get_git_status(repo_dir)

    if err:
        return {
            "success": False,
            "error": err,
            "repo_dir": str(repo_dir),
            "total_files_changed": 0,
            "total_lines_added": 0,
            "total_lines_deleted": 0,
            "violations_count": 0,
            "violations": [],
            "files_changed": [],
            "stats": {}
        }

    stats = direct_stats if direct_stats is not None else get_git_diff_stats(repo_dir, changes=changes)
    violations: List[Dict[str, object]] = []

    if not stats.get("complete", True):
        violations.append({
            "file": "*",
            "rule": "incomplete_diff_stats",
            "severity": "error",
            "message": "Diff statistics could not be completely calculated (e.g. oversized file or git failure)."
        })

    for item in changes:
        fpath = item["file"]
        status = item["status"]

        # Check 1: Anti-Reward-Hacking (Unauthorized Test Modifications)
        if is_test_file(fpath) and not allow_test_modifications:
            violations.append({
                "file": fpath,
                "rule": "unauthorized_test_tampering",
                "severity": "critical",
                "status": status,
                "message": f"Test/evaluator file '{fpath}' was modified or created without explicit authorization. Violates evaluation integrity (potential reward-hacking)."
            })

        # Check 2: Scope Boundaries
        if allowed_scope and not is_path_in_scope(fpath, allowed_scope):
            violations.append({
                "file": fpath,
                "rule": "out_of_scope_change",
                "severity": "error",
                "status": status,
                "message": f"File '{fpath}' is outside the authorized scope for this task: {allowed_scope}"
            })

    # Check 3: Diff Volume / Excessive Modification
    tot_added = stats.get("total_added", 0)
    tot_del = stats.get("total_deleted", 0)
    total_churn = tot_added + tot_del
    if max_modified_lines and total_churn > max_modified_lines:
        violations.append({
            "file": "*",
            "rule": "excessive_diff_churn",
            "severity": "error" if block_on_excessive_churn else "warning",
            "message": f"Total change volume ({total_churn} lines: +{tot_added}/-{tot_del}) exceeds recommended surgical threshold of {max_modified_lines} lines."
        })

    passed = len([v for v in violations if v["severity"] in ("critical", "error")]) == 0
    return {
        "success": passed,
        "repo_dir": str(repo_dir),
        "total_files_changed": len(changes),
        "total_lines_added": tot_added,
        "total_lines_deleted": tot_del,
        "violations_count": len(violations),
        "violations": violations,
        "files_changed": changes
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify that repository changes are surgical, bounded, and do not tamper with tests."
    )
    parser.add_argument(
        "target", nargs="?", default=".", help="Repository directory (default: current dir)"
    )
    parser.add_argument(
        "--scope", "-s", type=str, help="Comma-separated glob patterns of allowed files (e.g. 'src/*.py,TASK.md')"
    )
    parser.add_argument(
        "--allow-tests", action="store_true", help="Allow modifications to test files (disabled by default for integrity)"
    )
    parser.add_argument(
        "--max-lines", type=int, default=500, help="Maximum allowed churn before warning (default: 500)"
    )
    parser.add_argument(
        "--block-on-churn", action="store_true", help="Fail verification if change volume exceeds max-lines limit"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results in machine-readable JSON format"
    )
    args = parser.parse_args()

    repo_dir = Path(args.target).resolve()
    scope = [s.strip() for s in args.scope.split(",") if s.strip()] if args.scope else None

    result = check_surgical_diff(
        repo_dir=repo_dir,
        allowed_scope=scope,
        allow_test_modifications=args.allow_tests,
        max_modified_lines=args.max_lines,
        block_on_excessive_churn=args.block_on_churn,
    )

    if args.json:
        print(json.dumps(result, indent=2))
        if result.get("error"):
            sys.exit(2)
        sys.exit(0 if result.get("success") else 1)
    else:
        if result.get("error"):
            print(f"ERROR: {result['error']}")
            sys.exit(2)

        print(f"Surgical Diff Inspection: {result['repo_dir']}")
        print(f"Files changed: {result['total_files_changed']}")
        print(f"Lines added/deleted: +{result['total_lines_added']} / -{result['total_lines_deleted']}")
        print(f"Integrity violations: {result['violations_count']}")
        print("-" * 60)

        for v in result["violations"]:
            print(f"[{v['SEVERITY'].upper() if 'SEVERITY' in v else v['severity'].upper()}] {v['file']}: {v['message']}")

        if result["success"]:
            print("\nSURGICAL CHANGE INTEGRITY PRESERVED")
            sys.exit(0)
        else:
            print("\nSURGICAL CHANGE POLICY VIOLATED")
            sys.exit(1)


if __name__ == "__main__":
    main()
