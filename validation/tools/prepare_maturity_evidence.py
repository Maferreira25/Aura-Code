#!/usr/bin/env python3
"""Prepare a validated maturity-ledger PASS entry without mutating the ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

ROOT = Path(__file__).resolve().parents[2]


def prepare_entry(
    criterion_id: str,
    package_path: Path,
    reviewed_by: str,
    reviewed_at: str,
    rationale: str,
    root: Path = ROOT,
) -> Dict[str, Any]:
    criterion = criterion_id.strip().upper()
    if criterion not in {f"MAT-{i:02d}" for i in range(2, 11)}:
        raise ValueError("criterion must be MAT-02 through MAT-10")
    reviewer = reviewed_by.strip()
    if not reviewer:
        raise ValueError("reviewed_by is required")
    timestamp = reviewed_at.strip()
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("reviewed_at must be ISO-8601") from exc

    root_resolved = root.resolve()
    package = package_path.resolve()
    try:
        relative = package.relative_to(root_resolved).as_posix()
    except ValueError as exc:
        raise ValueError("maturity package must be inside repository root") from exc
    if not package.is_file():
        raise ValueError("maturity package does not exist")
    if package.suffix.lower() != ".json":
        raise ValueError("maturity package must be JSON")

    from tools.maturity_gate import _semantic_validate_evidence

    semantic = _semantic_validate_evidence(root_resolved, criterion, [relative])
    if not semantic.get("valid"):
        raise ValueError(str(semantic.get("reason", "semantic validation failed")))

    digest = hashlib.sha256(package.read_bytes()).hexdigest()
    return {
        "criterion": criterion,
        "ledger_entry": {
            "status": "PASS",
            "evidence": [relative],
            "rationale": rationale.strip() or "Evidence package validated and independently reviewed.",
            "reviewed_by": reviewer,
            "reviewed_at": timestamp,
            "evidence_sha256": digest,
        },
        "semantic_report": semantic.get("report"),
        "claim_boundary": (
            "This command prepares a ledger entry only. It does not authenticate the reviewer identity, "
            "alter validation/maturity-evidence.json, approve a release, or make the maturity claim true by itself."
        ),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare a reviewed AuraCode maturity-evidence ledger entry")
    parser.add_argument("criterion")
    parser.add_argument("package")
    parser.add_argument("--reviewed-by", required=True)
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument("--rationale", default="")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = prepare_entry(
            args.criterion,
            Path(args.package),
            args.reviewed_by,
            args.reviewed_at,
            args.rationale,
            Path(args.root),
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    if args.output:
        out = Path(args.output).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['criterion']}: validated proposal prepared")
        print(json.dumps(result["ledger_entry"], ensure_ascii=False, indent=2))
        print(result["claim_boundary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
