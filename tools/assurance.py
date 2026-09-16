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
from tools import assurance_mcp
from tools import assess


def setup_auracode_environment() -> None:
    dirs = ['.auracode', '_auracode_sdd', '_auracode_forward', '_auracode_bugs', '_auracode_refactor', '_auracode_docs']
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="auracode",
        description="AuraCode - Agentic Unified Reliability & Assurance for AI Software Engineering"
    )
    subparsers = parser.add_subparsers(dest="command", help="Assurance command to execute")

    # Subcommand: init
    init_p = subparsers.add_parser("init", help="Initialize workspace assurance environment directories")


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

    # Subcommand: sec
    sec_p = subparsers.add_parser("sec", help="Scan Python AST for injection vectors, eval/exec, and shell=True risks")
    sec_p.add_argument("target", nargs="?", default=".", help="Target workspace directory")

    # Subcommand: assess
    assess_p = subparsers.add_parser("assess", help="Assess project against an Assurance Level (AL1-AL4)")
    assess_p.add_argument("assessment_file", help="Path to assessment.json file")
    assess_p.add_argument("--json", action="store_true", help="Output results in JSON format")

    # Subcommand: mcp
    mcp_p = subparsers.add_parser("mcp", help="Start the stdio Model Context Protocol (MCP) server")
    mcp_p.add_argument("--allowed-root", type=str, default=None, help="Root directory for allowed tool operations")
    mcp_p.add_argument("--max-message-bytes", type=int, default=1000000, help="Maximum incoming JSON-RPC frame size")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "init":
        setup_auracode_environment()
        print("Initialized AuraCode workspace directories (.auracode, _auracode_*).")
        sys.exit(0)

    elif args.command == "arch":
        sys.argv = ["check_architecture.py", args.target]
        if args.contracts:
            sys.argv.extend(["--contracts", args.contracts])
        if args.max_files:
            sys.argv.extend(["--max-files", str(args.max_files)])
        if args.max_file_bytes:
            sys.argv.extend(["--max-file-bytes", str(args.max_file_bytes)])
        if args.json:
            sys.argv.append("--json")
        check_architecture.main()

    elif args.command == "deps":
        sys.argv = ["verify_dependencies.py"]
        if args.package:
            sys.argv.extend(["--package", args.package])
        elif args.target:
            sys.argv.append(args.target)
        if args.version:
            sys.argv.extend(["--version", args.version])
        if args.offline:
            sys.argv.append("--offline")
        if args.allow_unverified_network:
            sys.argv.append("--allow-unverified-network")
        if args.max_file_bytes:
            sys.argv.extend(["--max-file-bytes", str(args.max_file_bytes)])
        if args.max_packages:
            sys.argv.extend(["--max-packages", str(args.max_packages)])
        if args.total_timeout:
            sys.argv.extend(["--total-timeout", str(args.total_timeout)])
        if args.json:
            sys.argv.append("--json")
        verify_dependencies.main()

    elif args.command == "diff":
        sys.argv = ["check_surgical_diff.py", args.target]
        if args.scope:
            sys.argv.extend(["--scope", args.scope])
        if args.allow_tests:
            sys.argv.append("--allow-tests")
        if args.max_lines:
            sys.argv.extend(["--max-lines", str(args.max_lines)])
        if args.block_on_churn:
            sys.argv.append("--block-on-churn")
        if args.json:
            sys.argv.append("--json")
        check_surgical_diff.main()

    elif args.command == "ambiguity":
        sys.argv = ["check_requirements_ambiguity.py", args.target]
        check_requirements_ambiguity.main()

    elif args.command == "slop":
        sys.argv = ["check_slop_code.py", args.target]
        check_slop_code.main()

    elif args.command == "leaks":
        sys.argv = ["check_resource_leaks.py", args.target]
        check_resource_leaks.main()

    elif args.command == "types":
        sys.argv = ["check_strict_types.py", args.target]
        check_strict_types.main()

    elif args.command == "tests":
        sys.argv = ["check_test_integrity.py", args.target]
        check_test_integrity.main()

    elif args.command == "sec":
        sys.argv = ["check_injection_vectors.py", args.target]
        check_injection_vectors.main()

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


if __name__ == "__main__":
    main()
