#!/usr/bin/env python3
"""Utility to synchronize and regenerate MANIFEST.json cryptographic manifest."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    "graphify-out",
    "dist",
    "build",
    ".venv",
    ".pytest_cache",
    "auracode.egg-info",
    ".auracode",
    "_auracode_sdd",
    "_auracode_forward",
    "_auracode_bugs",
    "_auracode_refactor",
    "_auracode_docs",
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
}

EXCLUDE_FILES = {
    "MANIFEST.json",
}


def compute_file_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    h.update(filepath.read_bytes())
    return h.hexdigest()


def generate_manifest() -> dict:
    files_map = {}
    all_files = sorted(list(ROOT.rglob("*")))

    for f in all_files:
        if not f.is_file():
            continue
        rel = f.relative_to(ROOT)
        rel_str = str(rel).replace("\\", "/")

        # Check directory exclusions
        parts = rel.parts
        if any(part in EXCLUDE_DIRS or part.startswith("_auracode_") for part in parts):
            continue
        if parts and parts[0] == ".agents":
            continue

        # Check extension exclusions
        if f.suffix.lower() in EXCLUDE_EXTENSIONS:
            continue

        # Check filename exclusions
        if f.name in EXCLUDE_FILES:
            continue

        sha = compute_file_sha256(f)
        size = f.stat().st_size
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

    manifest_path = ROOT / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"MANIFEST.json updated: {len(files_map)} files cataloged.")
    return manifest


if __name__ == "__main__":
    generate_manifest()
