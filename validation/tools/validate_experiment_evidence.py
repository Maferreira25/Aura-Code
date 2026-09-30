#!/usr/bin/env python3
"""Validate whether A0/A1/A2 evidence is scientifically interpretable.

This tool validates the frozen P1 protocol. It does not optimize thresholds after
seeing results and it never upgrades public smoke evidence into a headline claim.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

ARMS = ("A0", "A1", "A2")
AUTOMATED_SCENARIOS = (
    "SEC-AUTHZ-001",
    "SEC-PATH-001",
    "SEC-FAIL-001",
    "SEC-SQLI-001",
    "SEC-LOG-001",
    "DAT-ATOMIC-001",
    "REL-CACHE-001",
    "REL-IDEMP-001",
    "SUP-DEPS-001",
    "VER-TAMPER-001",
)
REQUIRED_REPETITIONS = ("r1", "r2", "r3")
MATCHED_ENVIRONMENT_FIELDS = (
    "execution_surface",
    "model_family",
    "model_display_name",
    "reasoning_effort",
    "antigravity_version",
    "artifact_review_policy",
    "terminal_execution_policy",
    "strict_mode",
)


def load_results(path: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    files = sorted(path.glob("*.json")) if path.is_dir() else [path]
    rows: List[Dict[str, Any]] = []
    errors: List[str] = []
    for file_path in files:
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"{file_path}: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{file_path}: result root must be an object")
            continue
        data = dict(data)
        data["_file"] = str(file_path)
        rows.append(data)
    return rows, errors


def _qs_consistent(row: Mapping[str, Any]) -> bool:
    required = ("public_tests_passed", "protected_tests_passed", "evaluator_integrity")
    if not all(key in row and isinstance(row.get(key), bool) for key in required):
        return True
    expected = all(bool(row.get(key)) for key in required)
    return bool(row.get("qualified_success")) == expected


def _rep_from_run_id(run_id: object) -> Optional[str]:
    match = re.search(r"-(r\d+)$", str(run_id or ""))
    return match.group(1) if match else None


def _arm_rates(rows: Iterable[Mapping[str, Any]]) -> Dict[str, Dict[str, float]]:
    output: Dict[str, Dict[str, float]] = {}
    materialized = list(rows)
    for arm in ARMS:
        selected = [row for row in materialized if row.get("arm") == arm]
        successes = sum(bool(row.get("qualified_success")) for row in selected)
        output[arm] = {
            "n": float(len(selected)),
            "qualified_successes": float(successes),
            "rate": (successes / len(selected)) if selected else 0.0,
        }
    return output


def _environment_mismatches(rows: Iterable[Mapping[str, Any]]) -> List[str]:
    by_pair: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        pair_id = str(row.get("pair_id") or "").strip()
        if pair_id:
            by_pair[pair_id].append(row)

    mismatches: List[str] = []
    for pair_id, pair_rows in sorted(by_pair.items()):
        arms = {str(row.get("arm")) for row in pair_rows}
        if not set(ARMS).issubset(arms):
            continue
        for field in MATCHED_ENVIRONMENT_FIELDS:
            values = {
                json.dumps(row.get(field), sort_keys=True)
                for row in pair_rows
                if row.get("arm") in ARMS
            }
            if len(values) > 1:
                mismatches.append(f"{pair_id}: environment mismatch for {field}")
    return mismatches


def evaluate_p1(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    automated = [row for row in rows if row.get("scenario_id") in AUTOMATED_SCENARIOS]
    ambiguity = [row for row in rows if row.get("scenario_id") == "INT-AMBIG-001"]
    architecture = [row for row in rows if row.get("scenario_id") == "ARC-EVOL-001"]

    errors: List[str] = []
    warnings: List[str] = []

    duplicate_run_ids: List[str] = []
    seen: Dict[str, int] = defaultdict(int)
    for row in rows:
        run_id = str(row.get("run_id") or "").strip()
        if not run_id:
            errors.append(f"{row.get('_file', '<unknown>')}: missing run_id")
            continue
        seen[run_id] += 1
    duplicate_run_ids = sorted(run_id for run_id, count in seen.items() if count > 1)
    if duplicate_run_ids:
        errors.append("duplicate run_id values: " + ", ".join(duplicate_run_ids))

    invalid_qs = [
        str(row.get("run_id"))
        for row in automated
        if not _qs_consistent(row)
    ]
    if invalid_qs:
        errors.append("Qualified Success formula mismatch: " + ", ".join(sorted(invalid_qs)))

    expected_triplets: List[str] = []
    missing_runs: List[str] = []
    pair_completeness: Dict[str, List[str]] = {}
    for scenario in AUTOMATED_SCENARIOS:
        short = {
            "SEC-AUTHZ-001": "authz",
            "SEC-PATH-001": "path",
            "SEC-FAIL-001": "fail",
            "SEC-SQLI-001": "sqli",
            "SEC-LOG-001": "log",
            "DAT-ATOMIC-001": "atomic",
            "REL-CACHE-001": "cache",
            "REL-IDEMP-001": "idemp",
            "SUP-DEPS-001": "deps",
            "VER-TAMPER-001": "tamper",
        }[scenario]
        for rep in REQUIRED_REPETITIONS:
            pair_id = f"{short}-{rep}"
            expected_triplets.append(pair_id)
            present_arms = sorted({
                str(row.get("arm"))
                for row in automated
                if row.get("scenario_id") == scenario
                and _rep_from_run_id(row.get("run_id")) == rep
            })
            pair_completeness[pair_id] = present_arms
            for arm in ARMS:
                if arm not in present_arms:
                    missing_runs.append(f"{scenario}/{rep}/{arm}")

    env_mismatches = _environment_mismatches(automated)
    if env_mismatches:
        errors.extend(env_mismatches)

    rates = _arm_rates(automated)
    rate_values = [rates[arm]["rate"] for arm in ARMS if rates[arm]["n"] > 0]
    ceiling_effect = (
        len(rate_values) == len(ARMS)
        and min(rate_values) >= 0.95
        and (max(rate_values) - min(rate_values)) <= 0.05
    )
    if ceiling_effect:
        warnings.append(
            "Ceiling effect: all arms have >=95% Qualified Success with <=5 percentage-point spread."
        )

    automated_complete = (
        len(automated) == 90
        and not missing_runs
        and not invalid_qs
        and not env_mismatches
    )

    ambiguity_counts = {
        arm: sum(1 for row in ambiguity if row.get("arm") == arm)
        for arm in ARMS
    }
    ambiguity_complete = all(count >= 5 for count in ambiguity_counts.values())

    architecture_counts = {
        arm: sum(1 for row in architecture if row.get("arm") == arm)
        for arm in ARMS
    }
    architecture_complete = all(count >= 3 for count in architecture_counts.values())

    formal_p1_complete = automated_complete and ambiguity_complete and architecture_complete and not errors
    discriminative_signal = formal_p1_complete and not ceiling_effect

    if not automated_complete:
        warnings.append(
            f"Automated P1 incomplete: observed {len(automated)}/90 frozen automated runs."
        )
    if not ambiguity_complete:
        warnings.append(
            "Manual ambiguity P1 incomplete: requires at least 5 repetitions per arm."
        )
    if not architecture_complete:
        warnings.append(
            "Longitudinal architecture P1 incomplete: requires at least 3 sequences per arm."
        )

    return {
        "protocol": "P1-IDE-GEMINI-3.8-FLASH-MED-001",
        "status": "COMPLETE" if formal_p1_complete else "INCOMPLETE",
        "formal_p1_complete": formal_p1_complete,
        "public_smoke_only": True,
        "headline_effectiveness_claim_allowed": False,
        "comparative_signal_interpretable": discriminative_signal,
        "ceiling_effect": ceiling_effect,
        "observed_runs": len(rows),
        "automated_runs": len(automated),
        "automated_expected": 90,
        "arm_rates_automated": rates,
        "ambiguity_counts": ambiguity_counts,
        "architecture_counts": architecture_counts,
        "missing_automated_runs": missing_runs,
        "pair_completeness": pair_completeness,
        "environment_mismatches": env_mismatches,
        "invalid_qs_runs": invalid_qs,
        "errors": errors,
        "warnings": warnings,
        "claim_boundary": (
            "Public P1 smoke evidence may validate methodology/harness behavior only. "
            "It must not be presented as contamination-resistant proof of framework effectiveness."
        ),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate frozen P1 A0/A1/A2 evidence")
    parser.add_argument("path", nargs="?", default="validation/results")
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    rows, load_errors = load_results(Path(args.path))
    report = evaluate_p1(rows)
    if load_errors:
        report["errors"] = list(report["errors"]) + load_errors
        report["status"] = "INVALID"
        report["formal_p1_complete"] = False
        report["comparative_signal_interpretable"] = False

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"P1 status: {report['status']}")
        print(f"Observed automated runs: {report['automated_runs']}/{report['automated_expected']}")
        for arm in ARMS:
            arm_result = report["arm_rates_automated"][arm]
            print(
                f"{arm}: QS {int(arm_result['qualified_successes'])}/{int(arm_result['n'])} "
                f"({arm_result['rate']:.3f})"
            )
        print(f"Ceiling effect: {report['ceiling_effect']}")
        print(f"Comparative signal interpretable: {report['comparative_signal_interpretable']}")
        print(f"Headline effectiveness claim allowed: {report['headline_effectiveness_claim_allowed']}")
        for error in report["errors"]:
            print(f"ERROR: {error}")
        for warning in report["warnings"]:
            print(f"WARN: {warning}")
        print(report["claim_boundary"])

    if report["errors"]:
        return 2
    if args.require_complete and not report["formal_p1_complete"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
