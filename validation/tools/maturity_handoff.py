#!/usr/bin/env python3
"""Generate a frozen, non-authoritative handoff package for external maturity review."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

ROOT = Path(__file__).resolve().parents[2]

DEFAULT_REVIEW_FILES = (
    "VERSION",
    "MANIFEST.json",
    "controls/catalog.json",
    "controls/gates.json",
    "profiles/al2.json",
    "docs/ASSURANCE-STATE.md",
    "docs/THREAT-MODEL.md",
    "docs/GOVERNANCE-1.0-PROPOSAL.md",
    "docs/audit/INDEPENDENT-SECURITY-REVIEW-GUIDE.md",
    "validation/PROTOCOL.md",
    "validation/PILOT-PLAN.md",
    "validation/PREREGISTRATION-P1.md",
    "validation/MATURITY-STUDIES.md",
    "validation/maturity-criteria.json",
    "validation/maturity-evidence.json",
    "validation/maturity-workplan.json",
    "validation/benchmark-registry.json",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def build_handoff(root: Path, revision: str) -> Dict[str, Any]:
    root = root.resolve()
    immutable_revision = revision.strip()
    if not immutable_revision:
        raise ValueError("revision is required and must identify the frozen review target")

    from validation.tools.maturity_readiness import build_readiness

    readiness = build_readiness(root)
    files: List[Dict[str, Any]] = []
    missing: List[str] = []
    for rel in DEFAULT_REVIEW_FILES:
        path = root / rel
        if not path.is_file():
            missing.append(rel)
            continue
        files.append({
            "path": rel,
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
        })

    if missing:
        raise ValueError("required handoff files are missing: " + ", ".join(missing))

    external_or_human = [
        item["id"]
        for item in readiness["remaining"]
        if item.get("human_required") or item.get("independence_required")
    ]

    return {
        "format": "AURACODE-MATURITY-HANDOFF-V1",
        "target": readiness["target"],
        "revision": immutable_revision,
        "decision_at_export": readiness["decision"],
        "ready_at_export": readiness["ready"],
        "remaining_count": readiness["remaining_count"],
        "remaining": readiness["remaining"],
        "p1": readiness["p1"],
        "external_or_human_criteria": external_or_human,
        "review_files": files,
        "manifest_sha256": next(
            item["sha256"] for item in files if item["path"] == "MANIFEST.json"
        ),
        "privacy_boundary": (
            "This handoff intentionally does not embed private/fresh scenario contents, "
            "credentials, hidden evaluators, or assessor secrets."
        ),
        "claim_boundary": (
            "The handoff freezes inputs for an independent reviewer. It is not an approval, "
            "does not authenticate reviewer identity, and does not change maturity status."
        ),
    }


def render_markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# AuraCode Stable-Maturity External Review Handoff",
        "",
        f"- Frozen revision: `{report['revision']}`",
        f"- Target: `{report['target']}`",
        f"- Decision at export: **{report['decision_at_export']}**",
        f"- Remaining criteria: **{report['remaining_count']}**",
        f"- MANIFEST SHA-256: `{report['manifest_sha256']}`",
        "",
        "## Remaining maturity work",
        "",
    ]
    for item in report["remaining"]:
        lines.extend([
            f"### {item['id']} — {item['status']}",
            "",
            f"Reason: {item.get('reason', '')}",
            "",
            f"Owner role: `{item['owner_role']}`",
            f"Human required: `{str(item['human_required']).lower()}`",
            f"Independence required: `{str(item['independence_required']).lower()}`",
            "",
            f"Next action: {item['next_action']}",
            "",
            f"Completion condition: {item['completion_condition']}",
            "",
        ])

    lines.extend([
        "## Frozen review files",
        "",
        "| Path | SHA-256 | Bytes |",
        "| --- | --- | ---: |",
    ])
    for item in report["review_files"]:
        lines.append(
            f"| `{item['path']}` | `{item['sha256']}` | {item['bytes']} |"
        )

    lines.extend([
        "",
        "## Boundaries",
        "",
        report["privacy_boundary"],
        "",
        report["claim_boundary"],
        "",
    ])
    return "\n".join(lines)


def write_handoff(root: Path, revision: str, output_dir: Path) -> Dict[str, Any]:
    report = build_handoff(root, revision)
    out = output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "maturity-handoff.json"
    md_path = out / "maturity-handoff.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {
        "report": report,
        "json": str(json_path),
        "markdown": str(md_path),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Export frozen AuraCode maturity-review handoff")
    parser.add_argument("target", nargs="?", default=".")
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = write_handoff(
            Path(args.target),
            args.revision,
            Path(args.output_dir),
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Maturity handoff generated")
        print(f"- JSON: {result['json']}")
        print(f"- Markdown: {result['markdown']}")
        print(result["report"]["claim_boundary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
