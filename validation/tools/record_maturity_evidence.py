#!/usr/bin/env python3
"""Atomically record a reviewed maturity PASS after revalidating the evidence package."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from validation.tools.prepare_maturity_evidence import prepare_entry


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to read {path}: {exc}")
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def record_entry(
    criterion_id: str,
    package_path: Path,
    reviewed_by: str,
    reviewed_at: str,
    rationale: str,
    root: Path,
    confirm_reviewed: bool,
) -> Dict[str, Any]:
    if not confirm_reviewed:
        raise ValueError(
            "recording PASS requires explicit --confirm-reviewed acknowledgement"
        )

    root_resolved = root.resolve()
    ledger_path = root_resolved / "validation" / "maturity-evidence.json"
    if not ledger_path.is_file():
        raise ValueError("validation/maturity-evidence.json does not exist")

    prepared = prepare_entry(
        criterion_id,
        package_path,
        reviewed_by,
        reviewed_at,
        rationale,
        root_resolved,
    )
    criterion = prepared["criterion"]
    entry = prepared["ledger_entry"]

    ledger = _read_json(ledger_path)
    if str(ledger.get("target", "")) != "stable-1.0":
        raise ValueError("maturity ledger target must be stable-1.0")
    criteria = ledger.get("criteria")
    if not isinstance(criteria, dict):
        raise ValueError("maturity ledger criteria must be an object")
    if criterion not in criteria:
        raise ValueError(f"{criterion} is not present in maturity ledger")

    current_raw = criteria.get(criterion)
    current = current_raw if isinstance(current_raw, dict) else {}
    current_status = str(current.get("status", "UNKNOWN")).upper()
    current_hash = str(current.get("evidence_sha256", "")).lower().strip()

    if current_status == "PASS":
        if current_hash == entry["evidence_sha256"]:
            return {
                "status": "UNCHANGED",
                "criterion": criterion,
                "ledger_entry": current,
                "ledger_path": str(ledger_path),
                "claim_boundary": (
                    "The same PASS evidence was already recorded. No file was changed."
                ),
            }
        raise ValueError(
            f"{criterion} already has PASS evidence with a different hash; "
            "do not overwrite historical approval silently"
        )

    criteria[criterion] = entry
    ledger["updated_at"] = reviewed_at

    # Validate the candidate ledger in a temporary repository-local file first.
    candidate_path = ledger_path.with_name("maturity-evidence.candidate.json")
    try:
        candidate_path.write_text(
            json.dumps(ledger, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        # Re-evaluate the entry through the same gate primitives before replacing
        # the canonical ledger. The full maturity gate may remain BLOCK because
        # other MAT criteria are incomplete; this is expected.
        from tools.maturity_gate import _semantic_validate_evidence, _verify_pass_metadata

        metadata = _verify_pass_metadata(root_resolved, entry, entry["evidence"])
        if not metadata.get("valid"):
            raise ValueError(str(metadata.get("reason", "PASS metadata invalid")))
        semantic = _semantic_validate_evidence(
            root_resolved,
            criterion,
            entry["evidence"],
        )
        if not semantic.get("valid"):
            raise ValueError(str(semantic.get("reason", "semantic evidence invalid")))
    finally:
        try:
            candidate_path.unlink()
        except OSError:
            pass

    _atomic_write_json(ledger_path, ledger)

    return {
        "status": "RECORDED",
        "criterion": criterion,
        "ledger_entry": entry,
        "ledger_path": str(ledger_path),
        "claim_boundary": (
            "Recording one validated MAT criterion does not approve stable 1.0. "
            "The full maturity gate remains authoritative and all required criteria must PASS."
        ),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Record a reviewed AuraCode stable-maturity evidence package"
    )
    parser.add_argument("criterion")
    parser.add_argument("package")
    parser.add_argument("--reviewed-by", required=True)
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument("--rationale", default="")
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--confirm-reviewed",
        action="store_true",
        help="Explicitly confirm that the evidence package was actually reviewed",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = record_entry(
            args.criterion,
            Path(args.package),
            args.reviewed_by,
            args.reviewed_at,
            args.rationale,
            Path(args.root),
            args.confirm_reviewed,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['criterion']}: {result['status']}")
        print(f"Ledger: {result['ledger_path']}")
        print(result["claim_boundary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
