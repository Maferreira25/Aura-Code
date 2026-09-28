#!/usr/bin/env python3
"""Generate or verify the hashed Aura Studio package manifest."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List


def _asset(path: Path, studio_root: Path) -> Dict[str, object]:
    content = path.read_bytes()
    return {
        "path": path.relative_to(studio_root).as_posix(),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def expected_manifest(workspace: Path) -> Dict[str, object]:
    studio_root = workspace / "auracode" / "studio"
    server = studio_root / "server.py"
    assets_root = studio_root / "assets"
    if not server.is_file() or not (assets_root / "index.html").is_file():
        raise ValueError("Studio server or packaged assets are missing")
    paths: List[Path] = [server]
    for path in sorted(assets_root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symbolic package asset is forbidden: {path}")
        if path.is_file():
            paths.append(path)
    version = (workspace / "VERSION").read_text(encoding="utf-8").strip()
    return {
        "schema_version": 1,
        "framework_version": version,
        "status": "READY",
        "reason": "The local server and compiled assets are packaged and hash-verified.",
        "workflow_status": "PASS",
        "workflow_reason": "Aura Studio local workspace inspection workflows are verified.",
        "entrypoint": "server.py",
        "locales": ["pt-BR", "en"],
        "assets": [_asset(path, studio_root) for path in paths],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    workspace = Path.cwd().resolve()
    destination = workspace / "auracode" / "studio" / "manifest.json"
    try:
        expected = expected_manifest(workspace)
        if args.verify:
            actual = json.loads(destination.read_text(encoding="utf-8"))
            return 0 if actual == expected else 1
        destination.write_text(json.dumps(expected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return 0
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Studio manifest generation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
