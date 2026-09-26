#!/usr/bin/env python3
"""Unified CLI Entrypoint for AI Software Assurance Framework (AuraCode) V2.

Provides a consolidated interface for architectural linting, dependency verification,
surgical diff analysis, requirement ambiguity evaluation, AST slop analysis,
resource leak detection, strict type checking, test integrity, and injection vector scanning.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools import check_architecture
from tools import verify_dependencies
from tools import check_surgical_diff
from tools import check_requirements_ambiguity
from tools import check_slop_code
from tools import check_resource_leaks
from tools import check_strict_types
from tools import check_test_integrity
from tools import check_injection_vectors
from tools import sarif_aggregator
from tools import assurance_mcp
from tools import assess
from tools import pre_tool_guard
from tools import manage_worktree
from tools import manage_cage
from tools import loop_runner


def setup_auracode_environment(profile: str = "basic", copy_templates: bool = True, target_dir: Optional[Path] = None) -> None:
    root = target_dir if target_dir else Path.cwd()
    dirs = ['.auracode', '_auracode_sdd', '_auracode_forward', '_auracode_bugs', '_auracode_refactor', '_auracode_docs']
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)

    if copy_templates:
        import shutil
        templates_dir = ROOT_DIR / "templates" / "sdd" / profile
        if not templates_dir.exists():
            templates_dir = ROOT_DIR / "templates" / "sdd" / "basic"

        target_sdd = root / "_auracode_sdd"
        if templates_dir.exists():
            for tpl in sorted(templates_dir.glob("*.md")):
                dest = target_sdd / tpl.name
                if not dest.exists():
                    shutil.copy2(tpl, dest)

def _dispatch_with_argv(argv: list, fn: object) -> None:
    """Invoke a module's main() with a temporary sys.argv, then restore the original."""
    original = sys.argv
    try:
        sys.argv = argv
        fn()
    finally:
        sys.argv = original


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="auracode",
        description="AuraCode - Agentic Unified Reliability & Assurance for AI Software Engineering"
    )
    subparsers = parser.add_subparsers(dest="command", help="Assurance command to execute")

    # Subcommand: init
    init_p = subparsers.add_parser("init", help="Initialize workspace assurance environment directories")
    init_p.add_argument("--profile", "-p", choices=["basic", "enterprise"], default="basic", help="SDD specification template profile (basic: 7 specs, enterprise: 15 specs)")
    init_p.add_argument("--no-templates", action="store_true", help="Do not copy SDD template files into _auracode_sdd")


    # Subcommand: arch
    arch_p = subparsers.add_parser("arch", help="Verify Clean Architecture boundaries using AST")
    arch_p.add_argument("target", nargs="?", default=".", help="Project directory to inspect")
    arch_p.add_argument("--contracts", "-c", type=str, help="Path to contracts.json specification")
    arch_p.add_argument("--max-files", type=int, default=1000, help="Maximum number of files to inspect (default: 1000)")
    arch_p.add_argument("--max-file-bytes", type=int, default=1000000, help="Maximum bytes per file (default: 1000000)")
    arch_p.add_argument("--json", action="store_true", help="Output results in JSON format")

    # Subcommand: deps
    deps_p = subparsers.add_parser("deps", help="Verify dependencies against PyPI to prevent hallucinations")
    deps_p.add_argument("target", nargs="?", default=None, help="Path to requirements.txt, pyproject.toml or package name")
    deps_p.add_argument("--package", "-p", type=str, help="Single package name to check")
    deps_p.add_argument("--version", "-v", type=str, help="Target package version to verify")
    deps_p.add_argument("--offline", action="store_true", help="Run in offline mode (stdlib collision check only)")
    deps_p.add_argument("--allow-unverified-network", action="store_true", help="Do not fail verification when network is unreachable")
    deps_p.add_argument("--max-file-bytes", type=int, default=100000, help="Maximum requirements file bytes (default: 100000)")
    deps_p.add_argument("--max-packages", type=int, default=100, help="Maximum packages to verify (default: 100)")
    deps_p.add_argument("--total-timeout", type=float, default=30.0, help="Total execution timeout in seconds (default: 30.0)")
    deps_p.add_argument("--json", action="store_true", help="Output results in JSON format")

    # Subcommand: diff
    diff_p = subparsers.add_parser("diff", help="Verify that repository changes are surgical and bounded")
    diff_p.add_argument("target", nargs="?", default=".", help="Repository directory")
    diff_p.add_argument("--scope", "-s", type=str, help="Comma-separated glob patterns of allowed files")
    diff_p.add_argument("--allow-tests", action="store_true", help="Permit modifications to test/evaluator files")
    diff_p.add_argument("--max-lines", type=int, default=500, help="Maximum allowed churn (default: 500)")
    diff_p.add_argument("--block-on-churn", action="store_true", help="Fail verification if change volume exceeds max-lines limit")
    diff_p.add_argument("--json", action="store_true", help="Output results in JSON format")

    # Subcommand: ambiguity (Gate G1)
    amb_p = subparsers.add_parser("ambiguity", help="Evaluate requirement ambiguity & non-technical questions (Gate G1)")
    amb_p.add_argument("target", nargs="?", default=".", help="Target workspace directory")
    amb_p.add_argument("--include-json", action="store_true", help="Include JSON files in ambiguity scanning")

    # Subcommand: slop
    slop_p = subparsers.add_parser("slop", help="Scan Python AST for dead code, unreachable code, and swallowed errors")
    slop_p.add_argument("target", nargs="?", default=".", help="Target workspace directory")

    # Subcommand: leaks
    leaks_p = subparsers.add_parser("leaks", help="Scan Python AST for unclosed resource leaks (file handles, sockets, DBs)")
    leaks_p.add_argument("target", nargs="?", default=".", help="Target workspace directory")

    # Subcommand: types
    types_p = subparsers.add_parser("types", help="Scan Python AST for strict type hints and Any usage")
    types_p.add_argument("target", nargs="?", default=".", help="Target workspace directory")

    # Subcommand: tests
    tests_p = subparsers.add_parser("tests", help="Scan test suite integrity and detect vacuous tests without assertions")
    tests_p.add_argument("target", nargs="?", default=".", help="Target workspace directory")
    tests_p.add_argument("--allow-zero-tests", action="store_true", help="Permit zero test files without failing")

    # Subcommand: sec
    sec_p = subparsers.add_parser("sec", help="Scan Python AST for injection vectors, eval/exec, and shell=True risks")
    sec_p.add_argument("target", nargs="?", default=".", help="Target workspace directory")

    # Subcommand: sarif
    sarif_p = subparsers.add_parser("sarif", help="Ingest SARIF 2.1.0 or JSON external linter report")
    sarif_p.add_argument("target", help="Path to SARIF/JSON report file")

    # Subcommand: assess
    assess_p = subparsers.add_parser("assess", help="Assess project against an Assurance Level (AL1-AL4)")
    assess_p.add_argument("assessment_file", help="Path to assessment.json file")
    assess_p.add_argument("--json", action="store_true", help="Output results in JSON format")

    # Subcommand: mcp
    mcp_p = subparsers.add_parser("mcp", help="Start the stdio Model Context Protocol (MCP) server")
    mcp_p.add_argument("--allowed-root", type=str, default=None, help="Root directory for allowed tool operations")
    mcp_p.add_argument("--max-message-bytes", type=int, default=1000000, help="Maximum incoming JSON-RPC frame size")

    # Subcommand: guard
    guard_p = subparsers.add_parser("guard", help="Real-time Pre-Tool Execution Safety Guardrail (Aura Guard)")
    guard_sub = guard_p.add_subparsers(dest="guard_action", help="Guard action to execute")
    guard_check_p = guard_sub.add_parser("check", help="Check command safety before execution")
    guard_check_p.add_argument("command_str", nargs="?", default="", help="Command line string to evaluate")
    guard_check_p.add_argument("--json", action="store_true", help="Output result in JSON format")
    guard_install_p = guard_sub.add_parser("install", help="Install .agents/hooks.json in target workspace")
    guard_install_p.add_argument("target", nargs="?", default=".", help="Workspace root directory")

    # Subcommand: worktree
    wt_p = subparsers.add_parser("worktree", help="Physical Directory Isolation for AI Agents (Git Worktrees)")
    wt_sub = wt_p.add_subparsers(dest="worktree_action", help="Worktree action to perform")
    
    wt_create_p = wt_sub.add_parser("create", help="Create an isolated worktree for an agent task")
    wt_create_p.add_argument("task_name", help="Task name or identifier")
    wt_create_p.add_argument("--base-branch", "-b", type=str, default=None, help="Base branch to fork from")
    wt_create_p.add_argument("--dir", "-d", type=str, default=None, help="Custom target directory for the worktree")
    wt_create_p.add_argument("--json", action="store_true", help="Output result in JSON format")

    wt_list_p = wt_sub.add_parser("list", help="List all active worktrees")
    wt_list_p.add_argument("--json", action="store_true", help="Output list in JSON format")

    wt_clean_p = wt_sub.add_parser("clean", help="Remove an agent worktree and prune tracking")
    wt_clean_p.add_argument("task_name", help="Task name or identifier to clean")
    wt_clean_p.add_argument("--delete-branch", action="store_true", help="Delete the agent branch as well")
    wt_clean_p.add_argument("--json", action="store_true", help="Output result in JSON format")

    wt_merge_p = wt_sub.add_parser("merge", help="Merge an approved agent worktree branch and clean up")
    wt_merge_p.add_argument("task_name", help="Task name or identifier to merge")
    wt_merge_p.add_argument("--target-branch", "-t", type=str, default=None, help="Target branch (default: current)")
    wt_merge_p.add_argument("--keep-branch", action="store_true", help="Do not delete the agent branch after merge")
    wt_merge_p.add_argument("--no-clean", action="store_true", help="Do not remove the worktree folder after merge")
    wt_merge_p.add_argument("--json", action="store_true", help="Output result in JSON format")

    # Subcommand: cage
    cage_p = subparsers.add_parser("cage", help="DevContainer Sandbox & Default-Deny Firewall Manager (Aura Cage)")
    cage_sub = cage_p.add_subparsers(dest="cage_action", help="Cage action to perform")

    cage_init_p = cage_sub.add_parser("init", help="Initialize .devcontainer with Default-Deny firewall in workspace")
    cage_init_p.add_argument("target", nargs="?", default=".", help="Target workspace directory")
    cage_init_p.add_argument("--force", "-f", action="store_true", help="Overwrite existing cage files")
    cage_init_p.add_argument("--json", action="store_true", help="Output result in JSON format")

    cage_verify_p = cage_sub.add_parser("verify", help="Check whether the current environment is sandboxed")
    cage_verify_p.add_argument("--json", action="store_true", help="Output result in JSON format")

    # Subcommand: loop
    loop_p = subparsers.add_parser("loop", help="Autonomous Loop Runner based on Ralph Architecture (Aura Loop)")
    loop_sub = loop_p.add_subparsers(dest="loop_action", help="Loop action to perform")

    loop_run_p = loop_sub.add_parser("run", help="Start or resume autonomous loop runner")
    loop_run_p.add_argument("--max-iterations", "-n", type=int, default=10, help="Maximum iterations before pausing (default: 10)")
    loop_run_p.add_argument("--tasks-file", "-t", type=str, default=None, help="Path to custom tasks JSON backlog")
    loop_run_p.add_argument("--dry-run", action="store_true", help="Simulate loop execution without running full suites")
    loop_run_p.add_argument("--continue-on-fail", action="store_true", help="Do not stop loop on verification failure")
    loop_run_p.add_argument("--json", action="store_true", help="Output summary in JSON format")

    loop_status_p = loop_sub.add_parser("status", help="Display telemetry and current progress of the loop")
    loop_status_p.add_argument("--json", action="store_true", help="Output status in JSON format")

    loop_reset_p = loop_sub.add_parser("reset", help="Reset loop state and failure counters")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "init":
        profile = getattr(args, "profile", "basic")
        copy_tpl = not getattr(args, "no_templates", False)
        setup_auracode_environment(profile=profile, copy_templates=copy_tpl)
        print(f"Initialized AuraCode workspace directories (.auracode, _auracode_* [profile: {profile}]).")
        sys.exit(0)

    elif args.command == "arch":
        target_path = Path(args.target).resolve()
        cpath = Path(args.contracts).resolve() if args.contracts else None
        result = check_architecture.check_architecture(
            target_path,
            cpath,
            max_files=args.max_files,
            max_file_bytes=args.max_file_bytes,
        )
        code = check_architecture.print_architecture_result(
            result, target_path, is_json=args.json
        )
        sys.exit(code)

    elif args.command == "deps":
        argv = ["verify_dependencies.py"]
        if args.package:
            argv.extend(["--package", args.package])
        elif args.target:
            argv.append(args.target)
        if args.version:
            argv.extend(["--version", args.version])
        if args.offline:
            argv.append("--offline")
        if args.allow_unverified_network:
            argv.append("--allow-unverified-network")
        if args.max_file_bytes:
            argv.extend(["--max-file-bytes", str(args.max_file_bytes)])
        if args.max_packages:
            argv.extend(["--max-packages", str(args.max_packages)])
        if args.total_timeout:
            argv.extend(["--total-timeout", str(args.total_timeout)])
        if args.json:
            argv.append("--json")
        _dispatch_with_argv(argv, verify_dependencies.main)

    elif args.command == "diff":
        argv = ["check_surgical_diff.py", args.target]
        if args.scope:
            argv.extend(["--scope", args.scope])
        if args.allow_tests:
            argv.append("--allow-tests")
        if args.max_lines:
            argv.extend(["--max-lines", str(args.max_lines)])
        if args.block_on_churn:
            argv.append("--block-on-churn")
        if args.json:
            argv.append("--json")
        _dispatch_with_argv(argv, check_surgical_diff.main)

    elif args.command == "ambiguity":
        argv = ["check_requirements_ambiguity.py", args.target]
        if args.include_json:
            argv.append("--include-json")
        _dispatch_with_argv(argv, check_requirements_ambiguity.main)

    elif args.command == "slop":
        _dispatch_with_argv(["check_slop_code.py", args.target], check_slop_code.main)

    elif args.command == "leaks":
        _dispatch_with_argv(["check_resource_leaks.py", args.target], check_resource_leaks.main)

    elif args.command == "types":
        _dispatch_with_argv(["check_strict_types.py", args.target], check_strict_types.main)

    elif args.command == "tests":
        argv = ["check_test_integrity.py", args.target]
        if args.allow_zero_tests:
            argv.append("--allow-zero-tests")
        _dispatch_with_argv(argv, check_test_integrity.main)

    elif args.command == "sec":
        _dispatch_with_argv(["check_injection_vectors.py", args.target], check_injection_vectors.main)

    elif args.command == "sarif":
        _dispatch_with_argv(["sarif_aggregator.py", args.target], sarif_aggregator.main)

    elif args.command == "assess":
        assess_argv = [args.assessment_file]
        if args.json:
            assess_argv.append("--json")
        sys.exit(assess.main(assess_argv))

    elif args.command == "mcp":
        if getattr(args, "unrestricted_root", False) or args.allowed_root == "*":
            root_p = None
            unrestricted = True
        elif args.allowed_root:
            root_p = Path(args.allowed_root).resolve()
            unrestricted = False
        else:
            root_p = Path.cwd().resolve()
            unrestricted = False
        assurance_mcp.run_stdio_server(max_message_bytes=args.max_message_bytes, allowed_root=root_p, permit_unrestricted=unrestricted)
 
    elif args.command == "guard":
        guard_argv = []
        if getattr(args, "guard_action", None):
            guard_argv.append(args.guard_action)
        if getattr(args, "json", False):
            guard_argv.append("--json")
        if getattr(args, "command_str", ""):
            guard_argv.append(args.command_str)
        if getattr(args, "target", "") and args.guard_action == "install":
            guard_argv.append(args.target)
        sys.exit(pre_tool_guard.main(guard_argv))

    elif args.command == "worktree":
        wt_argv = []
        if getattr(args, "worktree_action", None):
            wt_argv.append(args.worktree_action)
        if getattr(args, "task_name", None):
            wt_argv.append(args.task_name)
        if getattr(args, "base_branch", None):
            wt_argv.extend(["--base-branch", args.base_branch])
        if getattr(args, "dir", None):
            wt_argv.extend(["--dir", args.dir])
        if getattr(args, "target_branch", None):
            wt_argv.extend(["--target-branch", args.target_branch])
        if getattr(args, "delete_branch", False):
            wt_argv.append("--delete-branch")
        if getattr(args, "keep_branch", False):
            wt_argv.append("--keep-branch")
        if getattr(args, "no_clean", False):
            wt_argv.append("--no-clean")
        if getattr(args, "json", False):
            wt_argv.append("--json")
        sys.exit(manage_worktree.main(wt_argv))

    elif args.command == "cage":
        cage_argv = []
        if getattr(args, "cage_action", None):
            cage_argv.append(args.cage_action)
        if getattr(args, "target", None) and args.cage_action == "init":
            cage_argv.append(args.target)
        if getattr(args, "force", False):
            cage_argv.append("--force")
        if getattr(args, "json", False):
            cage_argv.append("--json")
        sys.exit(manage_cage.main(cage_argv))

    elif args.command == "loop":
        loop_argv = []
        if getattr(args, "loop_action", None):
            loop_argv.append(args.loop_action)
        if getattr(args, "max_iterations", None) and args.loop_action == "run":
            loop_argv.extend(["--max-iterations", str(args.max_iterations)])
        if getattr(args, "tasks_file", None):
            loop_argv.extend(["--tasks-file", args.tasks_file])
        if getattr(args, "dry_run", False):
            loop_argv.append("--dry-run")
        if getattr(args, "continue_on_fail", False):
            loop_argv.append("--continue-on-fail")
        if getattr(args, "json", False):
            loop_argv.append("--json")
        sys.exit(loop_runner.main(loop_argv))


if __name__ == "__main__":
    main()
