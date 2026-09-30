#!/usr/bin/env python3
"""CLI routing for advanced Assurance v2 engines.

Keeps tools/assurance.py as a bounded composition root while preserving one
public CLI surface.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from tools import differential_engine
from tools import dynamic_security_engine
from tools import fuzz_engine
from tools import heldout_runner
from tools import metamorphic_engine
from tools import property_engine
from tools import static_analyzer_adapters
from tools import taint_engine
from tools import traceability_engine


def register_commands(subparsers: Any) -> None:
    heldout_p = subparsers.add_parser("heldout", help="Execute protected held-out tests outside the candidate workspace")
    heldout_p.add_argument("target", nargs="?", default=".", help="Candidate workspace directory")
    heldout_p.add_argument("--suite", required=True, help="Protected held-out suite directory")
    heldout_p.add_argument("--isolation", choices=["auto", "container", "local"], default="auto")
    heldout_p.add_argument("--strict", action="store_true", help="Require strong container isolation when auto mode is used")
    heldout_p.add_argument("--json", action="store_true", help="Output redacted result in JSON format")

    for name, help_text in [
        ("property", "Execute declared property-based tests with reproducible seed"),
        ("metamorphic", "Execute declared metamorphic relations"),
        ("differential", "Compare candidate and independent reference behavior"),
        ("fuzz", "Execute deterministic corpus fuzzing against a declared target"),
        ("dast", "Execute local-only runtime security contract checks"),
    ]:
        p = subparsers.add_parser(name, help=help_text)
        p.add_argument("manifest", help=f"Path to {name} suite manifest")
        p.add_argument("--target", default=".", help="Target workspace directory")
        p.add_argument("--json", action="store_true", help="Output result in JSON format")

    taint_p = subparsers.add_parser("taint", help="Run native Python taint/data-flow analysis")
    taint_p.add_argument("target", nargs="?", default=".", help="Target workspace directory")
    taint_p.add_argument("--json", action="store_true", help="Output result in JSON format")

    analyzer_p = subparsers.add_parser("analyzer-report", help="Normalize an external SARIF static-analysis report")
    analyzer_p.add_argument("report", help="Path to SARIF report")
    analyzer_p.add_argument("--id", required=True, help="Stable analyzer identifier, e.g. semgrep or codeql")
    analyzer_p.add_argument("--json", action="store_true", help="Output normalized report in JSON format")

    trace_p = subparsers.add_parser("traceability", help="Verify Requirement -> Invariant -> Implementation -> Test -> Evidence chains")
    trace_p.add_argument("manifest", nargs="?", default="_auracode_sdd/traceability.json", help="Path to traceability manifest")
    trace_p.add_argument("--target", default=".", help="Target workspace directory")
    trace_p.add_argument("--no-evidence-verify", action="store_true", help="Do not verify linked evidence freshness")
    trace_p.add_argument("--json", action="store_true", help="Output result in JSON format")


def _manifest(workspace: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (workspace / path).resolve()


def _print_common(label: str, result: dict) -> None:
    print(f"AuraCode {label}: {result.get('status')}")
    if "progression" in result:
        print(f"Progression: {result.get('progression', {}).get('state', 'BLOCKED')}")


def dispatch(args: Any) -> Optional[int]:
    command = getattr(args, "command", None)
    if command == "heldout":
        result = heldout_runner.evaluate_held_out(
            Path(args.target).resolve(),
            Path(args.suite).resolve(),
            isolation=args.isolation,
            strict_mode=args.strict,
        )
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            _print_common("Held-Out Evaluation", result)
            disclosure = result.get("disclosure", {})
            if disclosure.get("message"):
                print(disclosure["message"])
            if result.get("failure_category"):
                print(f"Failure category: {result['failure_category']}")
        return 0 if result.get("status") == "PASS" else 1

    if command in {"property", "metamorphic", "differential", "fuzz", "dast"}:
        workspace = Path(args.target).resolve()
        manifest = _manifest(workspace, args.manifest)
        engines = {
            "property": (property_engine.evaluate_property_suite, "Property Testing"),
            "metamorphic": (metamorphic_engine.evaluate_metamorphic_suite, "Metamorphic Testing"),
            "differential": (differential_engine.evaluate_differential_suite, "Differential Testing"),
            "fuzz": (fuzz_engine.evaluate_fuzz_suite, "Fuzzing"),
            "dast": (dynamic_security_engine.evaluate_dast_suite, "DAST"),
        }
        engine, label = engines[command]
        result = engine(workspace, manifest)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            _print_common(label, result)
            if result.get("suite_id"):
                print(f"Suite: {result['suite_id']}")
        return 0 if result.get("status") == "PASS" else 1

    if command == "taint":
        result = taint_engine.analyze_workspace(Path(args.target).resolve())
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            _print_common("Taint Analysis", result)
            print(f"Findings: {len(result.get('findings', []))}")
        return 0 if result.get("status") == "PASS" else 1

    if command == "analyzer-report":
        result = static_analyzer_adapters.normalize_sarif(Path(args.report), analyzer_id=args.id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("status") in {"PASS", "FAIL"} else 1

    if command == "traceability":
        workspace = Path(args.target).resolve()
        result = traceability_engine.evaluate_traceability_file(
            _manifest(workspace, args.manifest),
            workspace,
            verify_evidence=not args.no_evidence_verify,
        )
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            _print_common("Traceability", result)
            summary = result.get("summary", {})
            if summary:
                print(
                    f"Requirements: {summary.get('requirements_pass', 0)}/{summary.get('requirements_total', 0)} PASS | "
                    f"Invariants: {summary.get('invariants_pass', 0)}/{summary.get('invariants_total', 0)} PASS"
                )
        return 0 if result.get("status") == "PASS" else 1

    return None
