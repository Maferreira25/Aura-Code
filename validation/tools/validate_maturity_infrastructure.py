#!/usr/bin/env python3
"""Verify that every stable-maturity criterion has complete implementation scaffolding."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_CRITERIA = tuple(f"MAT-{i:02d}" for i in range(1, 11))

ARTIFACTS = {
    "MAT-01": [
        "validation/tools/validate_experiment_evidence.py",
        "validation/tools/p1_matrix.py",
        "validation/PREREGISTRATION-P1.md",
    ],
    "MAT-02": [
        "validation/config/p2-preregistration.example.json",
        "validation/config/p2-result.example.json",
        "validation/tools/private_split.py",
        "validation/tools/maturity_queue.py",
    ],
    "MAT-03": [
        "validation/config/replication-result.example.json",
    ],
    "MAT-04": [
        "validation/config/p3-plan.example.json",
        "validation/config/p3-result.example.json",
        "validation/benchmark-registry.json",
        "validation/tools/maturity_queue.py",
    ],
    "MAT-05": [
        "validation/config/p4-plan.example.json",
        "validation/config/p4-result.example.json",
        "validation/tools/maturity_queue.py",
    ],
    "MAT-06": [
        "validation/config/inter-rater.example.json",
    ],
    "MAT-07": [
        "validation/config/burden-errors.example.json",
        "validation/schemas/result.schema.json",
    ],
    "MAT-08": [
        "validation/config/multilang-stable.example.json",
        "validation/multilang-qualification/corpus.json",
        "validation/tools/qualify_multilang.py",
    ],
    "MAT-09": [
        "validation/config/security-audit.example.json",
        "docs/audit/INDEPENDENT-SECURITY-REVIEW-GUIDE.md",
    ],
    "MAT-10": [
        "validation/config/governance-1.0.example.json",
        "docs/GOVERNANCE-1.0-PROPOSAL.md",
    ],
}

COMMON_ARTIFACTS = [
    "validation/MATURITY-STUDIES.md",
    "validation/maturity-criteria.json",
    "validation/maturity-evidence.json",
    "validation/maturity-workplan.json",
    "validation/schemas/maturity-workplan.schema.json",
    "validation/tools/maturity_readiness.py",
    "validation/schemas/maturity-evidence.schema.json",
    "validation/tools/maturity_studies.py",
    "validation/tools/maturity_reviews.py",
    "validation/tools/maturity_claims.py",
    "validation/tools/prepare_maturity_evidence.py",
    "tools/maturity_gate.py",
]


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to read {path}: {exc}")
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def validate_maturity_infrastructure(root: Path = ROOT) -> Dict[str, Any]:
    root = root.resolve()
    errors: List[str] = []
    warnings: List[str] = []

    criteria_path = root / "validation" / "maturity-criteria.json"
    ledger_path = root / "validation" / "maturity-evidence.json"
    if not criteria_path.is_file():
        return {"status": "INVALID", "errors": ["missing maturity-criteria.json"], "warnings": []}
    if not ledger_path.is_file():
        return {"status": "INVALID", "errors": ["missing maturity-evidence.json"], "warnings": []}

    criteria = _read_json(criteria_path)
    ledger = _read_json(ledger_path)

    raw_criteria = criteria.get("criteria")
    if not isinstance(raw_criteria, list):
        errors.append("maturity criteria must be an array")
        raw_criteria = []

    ids = [
        str(item.get("id", "")).strip()
        for item in raw_criteria
        if isinstance(item, dict)
    ]
    if tuple(ids) != EXPECTED_CRITERIA:
        errors.append(
            "maturity criteria must be exactly MAT-01 through MAT-10 in canonical order"
        )

    for item in raw_criteria:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("id", "")).strip()
        if not bool(item.get("required")):
            errors.append(f"{cid}: stable-1.0 criterion must remain required")
        expected_mode = "auto_p1" if cid == "MAT-01" else "evidence"
        if str(item.get("mode", "")).strip() != expected_mode:
            errors.append(f"{cid}: expected mode {expected_mode}")

    ledger_map = ledger.get("criteria")
    if not isinstance(ledger_map, dict):
        errors.append("maturity evidence criteria must be an object")
        ledger_map = {}

    for cid in EXPECTED_CRITERIA[1:]:
        if cid not in ledger_map:
            errors.append(f"{cid}: missing ledger entry")
        elif not isinstance(ledger_map[cid], dict):
            errors.append(f"{cid}: ledger entry must be an object")

    for rel in COMMON_ARTIFACTS:
        if not (root / rel).is_file():
            errors.append(f"missing common maturity artifact: {rel}")

    for cid, required in ARTIFACTS.items():
        for rel in required:
            if not (root / rel).is_file():
                errors.append(f"{cid}: missing maturity artifact {rel}")

    # The operational workplan must map exactly onto MAT-01..MAT-10 but never grant status.
    try:
        from validation.tools.maturity_readiness import validate_workplan
        workplan = _read_json(root / "validation" / "maturity-workplan.json")
        workplan_errors = validate_workplan(workplan, EXPECTED_CRITERIA)
        errors.extend(f"maturity workplan: {item}" for item in workplan_errors)
        for item in workplan.get("criteria", []):
            if isinstance(item, dict) and "status" in item:
                errors.append(f"{item.get('id', '<unknown>')}: workplan must not contain status")
    except (ImportError, ValueError) as exc:
        errors.append(f"maturity workplan validation failed: {exc}")

    # Prove that MAT-02..MAT-10 all resolve to a semantic validator.
    try:
        from validation.tools.maturity_studies import validate_evidence_for_criterion
        registry = _read_json(root / "validation" / "benchmark-registry.json")
        for cid in EXPECTED_CRITERIA[1:]:
            try:
                report = validate_evidence_for_criterion(
                    cid,
                    {},
                    registry if cid == "MAT-04" else None,
                    root=root,
                )
            except TypeError:
                # Backwards-compatible guard if the dispatch signature changes.
                try:
                    report = validate_evidence_for_criterion(
                        cid,
                        {},
                        registry if cid == "MAT-04" else None,
                    )
                except Exception as exc:
                    errors.append(f"{cid}: semantic validator unavailable: {exc}")
                    continue
            except Exception as exc:
                errors.append(f"{cid}: semantic validator unavailable: {exc}")
                continue
            if not isinstance(report, dict) or "status" not in report:
                errors.append(f"{cid}: semantic validator returned invalid report")
    except ImportError as exc:
        errors.append(f"semantic maturity validator import failed: {exc}")

    # Stable maturity policy must remain non-waivable in its own policy declaration.
    policy = str(criteria.get("policy", "")).lower()
    if "no maturity criterion may be waived" not in policy:
        errors.append("stable maturity policy must explicitly prohibit criterion waivers")

    # The public multilingual corpus must stay non-headline/non-maturity evidence.
    corpus = _read_json(root / "validation" / "multilang-qualification" / "corpus.json")
    if "not sufficient" not in str(corpus.get("purpose", "")).lower():
        warnings.append("public multilang corpus purpose should explicitly limit maturity claims")

    return {
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "warnings": warnings,
        "criteria_count": len(ids),
        "artifact_checks": sum(len(v) for v in ARTIFACTS.values()) + len(COMMON_ARTIFACTS),
        "claim_boundary": (
            "Infrastructure coverage proves that the evidence machinery exists. "
            "It does not prove that any MAT criterion has been satisfied."
        ),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate AuraCode stable-maturity infrastructure coverage")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        report = validate_maturity_infrastructure(Path(args.root))
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Maturity infrastructure: {report['status']}")
        for error in report["errors"]:
            print(f"ERROR: {error}")
        for warning in report["warnings"]:
            print(f"WARN: {warning}")
        print(report["claim_boundary"])
    return 0 if report["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
