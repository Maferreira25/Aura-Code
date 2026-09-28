#!/usr/bin/env python3
"""Aura Worktree: Physical Directory Isolation for AI Agent Development.

Orchestrates Git Worktrees so autonomous agent tasks operate in isolated
physical folders, completely preventing unstaged or corrupted code from
polluting the human developer's active workspace.

Zero external dependencies (uses standard library 'subprocess', 're', 'pathlib', 'argparse', 'json').
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _run_git(args: List[str], cwd: Path) -> Tuple[int, str, str]:
    """Executes a git command and returns (exit_code, stdout, stderr)."""
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except FileNotFoundError:
        return 127, "", "Git binary not found in system PATH."
    except Exception as e:
        return 1, "", str(e)


def slugify_task(task_name: str) -> str:
    """Converts a human task description into a safe URL/folder slug."""
    slug = re.sub(r"[^a-zA-Z0-9_\-]", "-", task_name.strip()).lower()
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "unnamed-task"


def get_current_branch(repo_root: Path) -> str:
    """Returns the name of the currently checked out branch."""
    code, out, _ = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_root)
    return out if code == 0 else "main"


def list_worktrees(repo_root: Path) -> List[Dict[str, Any]]:
    """Parses and lists all active git worktrees in the repository."""
    code, out, err = _run_git(["worktree", "list", "--porcelain"], repo_root)
    if code != 0:
        return []

    worktrees = []
    current: Dict[str, Any] = {}

    for line in out.splitlines():
        line = line.strip()
        if not line:
            if current:
                worktrees.append(current)
                current = {}
            continue

        if line.startswith("worktree "):
            current["path"] = line[len("worktree "):].strip()
        elif line.startswith("HEAD "):
            current["head"] = line[len("HEAD "):].strip()
        elif line.startswith("branch "):
            current["branch"] = line[len("branch "):].strip().replace("refs/heads/", "")
        elif line == "bare":
            current["bare"] = True
        elif line == "detached":
            current["detached"] = True

    if current:
        worktrees.append(current)

    return worktrees


def create_worktree(
    repo_root: Path,
    task_name: str,
    base_branch: Optional[str] = None,
    target_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Creates a dedicated isolated Git worktree for an autonomous agent task."""
    slug = slugify_task(task_name)
    branch_name = f"feat/agent-{slug}"

    if not base_branch:
        base_branch = get_current_branch(repo_root)

    if target_dir is None:
        target_dir = repo_root / ".auracode" / "worktrees" / slug

    target_dir = Path(target_dir).resolve()

    # Check if worktree directory already exists
    existing_worktrees = list_worktrees(repo_root)
    for wt in existing_worktrees:
        wt_path = Path(wt.get("path", "")).resolve()
        if wt_path == target_dir:
            return {
                "success": True,
                "created": False,
                "message": f"Worktree already active at {target_dir}",
                "task": task_name,
                "slug": slug,
                "branch": wt.get("branch", branch_name),
                "path": str(target_dir),
                "base_branch": base_branch,
            }

    # Ensure parent directory exists
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    # Check if branch exists already
    code_br, _, _ = _run_git(["rev-parse", "--verify", branch_name], repo_root)
    branch_exists = (code_br == 0)

    if branch_exists:
        # Attach existing branch
        cmd = ["worktree", "add", str(target_dir), branch_name]
    else:
        # Create branch from base_branch
        cmd = ["worktree", "add", "-b", branch_name, str(target_dir), base_branch]

    code, out, err = _run_git(cmd, repo_root)
    if code != 0:
        return {
            "success": False,
            "error": f"Failed to create git worktree: {err or out}",
            "task": task_name,
            "slug": slug,
            "branch": branch_name,
            "path": str(target_dir),
        }

    # Sync theoretical specifications and contracts if available in parent
    sdd_source = repo_root / "_auracode_sdd"
    if sdd_source.exists() and sdd_source.is_dir():
        sdd_dest = target_dir / "_auracode_sdd"
        if not sdd_dest.exists():
            shutil.copytree(sdd_source, sdd_dest, dirs_exist_ok=True)

    contracts_source = repo_root / "contracts.json"
    if contracts_source.exists():
        contracts_dest = target_dir / "contracts.json"
        if not contracts_dest.exists():
            shutil.copy2(contracts_source, contracts_dest)

    return {
        "success": True,
        "created": True,
        "message": f"Isolated agent worktree created successfully at {target_dir}",
        "task": task_name,
        "slug": slug,
        "branch": branch_name,
        "path": str(target_dir),
        "base_branch": base_branch,
    }


def clean_worktree(
    repo_root: Path,
    task_name: str,
    delete_branch: bool = False,
) -> Dict[str, Any]:
    """Removes an agent worktree directory and prunes git records."""
    slug = slugify_task(task_name)
    branch_name = f"feat/agent-{slug}"

    # Locate worktree path
    existing_worktrees = list_worktrees(repo_root)
    found_path: Optional[Path] = None

    for wt in existing_worktrees:
        b = wt.get("branch", "")
        p = Path(wt.get("path", "")).resolve()
        if b == branch_name or p.name == slug or slug in p.name:
            found_path = p
            break

    if not found_path:
        default_p = (repo_root / ".auracode" / "worktrees" / slug).resolve()
        if default_p.exists():
            found_path = default_p

    if not found_path or not found_path.exists():
        # Run prune just in case
        _run_git(["worktree", "prune"], repo_root)
        return {
            "success": True,
            "message": f"No active worktree found for task '{task_name}'. Cleaned up records.",
            "task": task_name,
        }

    # Remove worktree via git
    code, out, err = _run_git(["worktree", "remove", "--force", str(found_path)], repo_root)
    if code != 0:
        # Fallback: manual rmtree if git remove reports error
        if found_path.exists():
            shutil.rmtree(found_path, ignore_errors=True)
        _run_git(["worktree", "prune"], repo_root)

    # Prune git internal worktree tracking
    _run_git(["worktree", "prune"], repo_root)

    # Optionally delete branch
    if delete_branch:
        _run_git(["branch", "-D", branch_name], repo_root)

    return {
        "success": True,
        "message": f"Agent worktree '{task_name}' removed cleanly.",
        "path": str(found_path),
        "branch_deleted": delete_branch,
    }


def merge_worktree(
    repo_root: Path,
    task_name: str,
    target_branch: Optional[str] = None,
    auto_clean: bool = True,
    delete_branch: bool = True,
) -> Dict[str, Any]:
    """Merges an approved agent worktree branch into the target branch and cleans up."""
    slug = slugify_task(task_name)
    branch_name = f"feat/agent-{slug}"

    if not target_branch:
        target_branch = get_current_branch(repo_root)

    # Ensure target branch is checked out in repo_root
    code_co, _, err_co = _run_git(["checkout", target_branch], repo_root)
    if code_co != 0:
        return {
            "success": False,
            "error": f"Failed to checkout target branch '{target_branch}': {err_co}",
        }

    # Perform merge
    merge_msg = f"feat(agent): merge completed task '{task_name}' [AuraCode Assurance Verified]"
    code_m, out_m, err_m = _run_git(["merge", "--no-ff", branch_name, "-m", merge_msg], repo_root)
    if code_m != 0:
        return {
            "success": False,
            "error": f"Merge conflict or failure merging branch '{branch_name}' into '{target_branch}': {err_m or out_m}",
        }

    cleanup_info = None
    if auto_clean:
        cleanup_info = clean_worktree(repo_root, task_name, delete_branch=delete_branch)

    return {
        "success": True,
        "message": f"Successfully merged '{branch_name}' into '{target_branch}'",
        "target_branch": target_branch,
        "source_branch": branch_name,
        "cleaned": auto_clean,
        "cleanup_details": cleanup_info,
    }


def main(argv: Optional[List[str]] = None) -> int:
    """CLI Entrypoint for Aura Worktree management."""
    parser = argparse.ArgumentParser(
        prog="auracode worktree",
        description="Aura Worktree: Physical Directory Isolation for AI Agent Development"
    )
    subparsers = parser.add_subparsers(dest="worktree_action", help="Worktree action to perform")

    # create
    create_p = subparsers.add_parser("create", help="Create an isolated worktree for an agent task")
    create_p.add_argument("task_name", nargs="?", default=None, help="Task name or identifier")
    create_p.add_argument("--task", type=str, default=None, help="Task name or identifier (flag alias)")
    create_p.add_argument("--base-branch", "-b", type=str, default=None, help="Base branch to fork from")
    create_p.add_argument("--dir", "-d", type=str, default=None, help="Custom target directory for the worktree")
    create_p.add_argument("--json", action="store_true", help="Output result in JSON format")

    # list
    list_p = subparsers.add_parser("list", help="List all active worktrees")
    list_p.add_argument("--json", action="store_true", help="Output list in JSON format")

    # clean
    clean_p = subparsers.add_parser("clean", help="Remove an agent worktree and prune tracking")
    clean_p.add_argument("task_name", nargs="?", default=None, help="Task name or identifier to clean")
    clean_p.add_argument("--task", type=str, default=None, help="Task name or identifier to clean (flag alias)")
    clean_p.add_argument("--delete-branch", action="store_true", help="Delete the agent branch as well")
    clean_p.add_argument("--json", action="store_true", help="Output result in JSON format")

    # merge
    merge_p = subparsers.add_parser("merge", help="Merge an approved agent worktree branch and clean up")
    merge_p.add_argument("task_name", nargs="?", default=None, help="Task name or identifier to merge")
    merge_p.add_argument("--task", type=str, default=None, help="Task name or identifier to merge (flag alias)")
    merge_p.add_argument("--target-branch", "-t", type=str, default=None, help="Target branch (default: current)")
    merge_p.add_argument("--keep-branch", action="store_true", help="Do not delete the agent branch after merge")
    merge_p.add_argument("--no-clean", action="store_true", help="Do not remove the worktree folder after merge")
    merge_p.add_argument("--json", action="store_true", help="Output result in JSON format")

    args = parser.parse_args(argv)

    if not args.worktree_action:
        parser.print_help()
        return 0

    repo_root = Path.cwd().resolve()

    effective_task = getattr(args, "task", None) or getattr(args, "task_name", None)

    if args.worktree_action in ("create", "clean", "merge") and not effective_task:
        sys.stderr.write(f"Error: task name is required for worktree {args.worktree_action}.\n")
        return 1

    if args.worktree_action == "create":
        target_dir = Path(args.dir).resolve() if args.dir else None
        res = create_worktree(repo_root, effective_task, base_branch=args.base_branch, target_dir=target_dir)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            if res["success"]:
                print(f"[AURA WORKTREE CREATED]\nPath: {res['path']}\nBranch: {res['branch']}\nBase: {res['base_branch']}")
            else:
                sys.stderr.write(f"[AURA WORKTREE ERROR] {res['error']}\n")
        return 0 if res["success"] else 1

    elif args.worktree_action == "list":
        wts = list_worktrees(repo_root)
        if args.json:
            print(json.dumps(wts, indent=2, ensure_ascii=False))
        else:
            print(f"Active Git Worktrees ({len(wts)}):")
            for wt in wts:
                branch = wt.get("branch", "(detached)")
                path = wt.get("path", "")
                head = wt.get("head", "")[:8]
                print(f" - [{branch}] {path} ({head})")
        return 0

    elif args.worktree_action == "clean":
        res = clean_worktree(repo_root, effective_task, delete_branch=args.delete_branch)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(f"[AURA WORKTREE CLEAN] {res['message']}")
        return 0

    elif args.worktree_action == "merge":
        res = merge_worktree(
            repo_root,
            effective_task,
            target_branch=args.target_branch,
            auto_clean=not args.no_clean,
            delete_branch=not args.keep_branch,
        )
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            if res["success"]:
                print(f"[AURA WORKTREE MERGED] {res['message']}")
            else:
                sys.stderr.write(f"[AURA WORKTREE ERROR] {res['error']}\n")
        return 0 if res["success"] else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
