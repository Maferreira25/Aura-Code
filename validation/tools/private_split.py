#!/usr/bin/env python3
"""Create and verify privacy-preserving SHA-256 commitments for private/fresh P2 splits."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


def _files(root: Path, max_files: int = 10000) -> List[Path]:
    if not root.is_dir():
        raise ValueError(f"private split directory does not exist: {root}")
    output: List[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlink is not allowed in committed private split: {path}")
        if path.is_file():
            output.append(path)
            if len(output) > max_files:
                raise ValueError(f"private split exceeds max_files={max_files}")
    if not output:
        raise ValueError("private split contains no files")
    return output


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def build_commitment(root: Path, max_files: int = 10000) -> Dict[str, Any]:
    base = root.resolve()
    paths = _files(base, max_files=max_files)
    canonical: List[Tuple[str, str, int]] = []
    total_bytes = 0
    for path in paths:
        rel = path.relative_to(base).as_posix()
        size = path.stat().st_size
        total_bytes += size
        canonical.append((rel, _file_sha256(path), size))

    aggregate = hashlib.sha256()
    for rel, digest, size in canonical:
        aggregate.update(rel.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(digest.encode("ascii"))
        aggregate.update(b"\0")
        aggregate.update(str(size).encode("ascii"))
        aggregate.update(b"\n")

    return {
        "scheme": "AURACODE-PRIVATE-SPLIT-SHA256-V1",
        "sha256": aggregate.hexdigest(),
        "file_count": len(canonical),
        "total_bytes": total_bytes,
        "paths_disclosed": False,
        "claim_boundary": (
            "This commitment can detect later split changes when the same private directory is available. "
            "It does not prove scenario quality, freshness, independence, or absence of model contamination."
        ),
    }


def verify_commitment(root: Path, expected: Dict[str, Any], max_files: int = 10000) -> Dict[str, Any]:
    actual = build_commitment(root, max_files=max_files)
    expected_digest = str(expected.get("sha256", "")).strip().lower()
    expected_scheme = str(expected.get("scheme", "")).strip()
    matched = (
        expected_scheme == actual["scheme"]
        and len(expected_digest) == 64
        and expected_digest == actual["sha256"]
        and expected.get("file_count") == actual["file_count"]
        and expected.get("total_bytes") == actual["total_bytes"]
    )
    return {
        "status": "PASS" if matched else "FAIL",
        "matched": matched,
        "expected_sha256": expected_digest,
        "actual_sha256": actual["sha256"],
        "expected_file_count": expected.get("file_count"),
        "actual_file_count": actual["file_count"],
        "expected_total_bytes": expected.get("total_bytes"),
        "actual_total_bytes": actual["total_bytes"],
    }


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to read commitment: {exc}")
    if not isinstance(data, dict):
        raise ValueError("commitment JSON root must be an object")
    return data


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AuraCode private/fresh split commitment")
    sub = parser.add_subparsers(dest="action", required=True)

    commit = sub.add_parser("commit")
    commit.add_argument("directory")
    commit.add_argument("--output", required=True)
    commit.add_argument("--max-files", type=int, default=10000)
    commit.add_argument("--json", action="store_true")

    verify = sub.add_parser("verify")
    verify.add_argument("directory")
    verify.add_argument("commitment")
    verify.add_argument("--max-files", type=int, default=10000)
    verify.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.action == "commit":
            result = build_commitment(Path(args.directory), max_files=args.max_files)
            output = Path(args.output).resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            code = 0
        else:
            result = verify_commitment(
                Path(args.directory),
                _load_json(Path(args.commitment)),
                max_files=args.max_files,
            )
            code = 0 if result["matched"] else 1
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if args.action == "commit":
            print(f"Private split commitment: {result['sha256']}")
            print(f"Files: {result['file_count']}; bytes: {result['total_bytes']}")
        else:
            print(f"Private split verification: {result['status']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
