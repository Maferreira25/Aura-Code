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
    load_gitignore_patterns,
    is_ignored_by_framework,
    load_normalized_bytes,
)
from tools.version import FRAMEWORK_VERSION


def compute_file_metrics(filepath: Path) -> tuple[str, int]:
    content = load_normalized_bytes(filepath)
    return hashlib.sha256(content).hexdigest(), len(content)


def generate_manifest(root_dir: Path = ROOT) -> dict:
    files_map = {}
    gitignore_patterns = load_gitignore_patterns(root_dir)
    all_files = sorted(list(root_dir.rglob("*")))

    for f in all_files:
        if not f.is_file():
            continue
        rel = f.relative_to(root_dir)
        if is_ignored_by_framework(rel, gitignore_patterns):
            continue
        rel_str = str(rel).replace("\\", "/")

        sha, size = compute_file_metrics(f)
        files_map[rel_str] = {
            "sha256": sha,
            "bytes": size
        }

    manifest = {
        "framework_version": FRAMEWORK_VERSION,
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
