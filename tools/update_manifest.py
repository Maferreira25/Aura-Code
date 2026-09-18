#!/usr/bin/env python3
"""Utility to synchronize and regenerate MANIFEST.json cryptographic manifest."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validate_framework import (
    MANIFEST_EXCLUDE_DIRS,
    MANIFEST_EXCLUDE_EXTS,
    MANIFEST_EXCLUDE_FILES,
    MANIFEST_EXCLUDE_ROOT_FILES,
    load_normalized_bytes,
)


def compute_file_metrics(filepath: Path) -> tuple[str, int]:
    content = load_normalized_bytes(filepath)
    return hashlib.sha256(content).hexdigest(), len(content)


def generate_manifest(root_dir: Path = ROOT) -> dict:
    files_map = {}
    all_files = sorted(list(root_dir.rglob("*")))

    for f in all_files:
        if not f.is_file():
            continue
        rel = f.relative_to(root_dir)
        rel_str = str(rel).replace("\\", "/")

        # Check directory exclusions
        parts = rel.parts
        if any(part in MANIFEST_EXCLUDE_DIRS or part.startswith("_auracode_") or part.startswith("_reversa_") for part in parts):
            continue
        if parts and parts[0] in {".agents", ".reversa"}:
            continue

        # Check extension and filename exclusions
        if f.suffix.lower() in MANIFEST_EXCLUDE_EXTS or f.name in MANIFEST_EXCLUDE_FILES or rel_str in MANIFEST_EXCLUDE_ROOT_FILES:
            continue

        sha, size = compute_file_metrics(f)
        files_map[rel_str] = {
            "sha256": sha,
            "bytes": size
        }

    manifest = {
        "framework_version": "0.1.1-draft",
        "validation_suite": "0.1.1-alpha",
        "file_count": len(files_map),
        "files": files_map
    }

    manifest_path = root_dir / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"MANIFEST.json updated: {len(files_map)} files cataloged.")
    return manifest


if __name__ == "__main__":
    generate_manifest()
