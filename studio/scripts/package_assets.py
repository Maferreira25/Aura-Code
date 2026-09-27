#!/usr/bin/env python3
"""Copy or verify compiled Studio assets for Python package inclusion."""

import argparse
import hashlib
import shutil
from pathlib import Path
from typing import Dict


def _inventory(root: Path) -> Dict[str, str]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"asset directory is missing or symbolic: {root}")
    inventory: Dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symbolic asset is forbidden: {path}")
        if path.is_file():
            inventory[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if "index.html" not in inventory:
        raise ValueError("compiled Studio index.html is missing")
    return inventory


def verify_assets(workspace: Path) -> bool:
    source = workspace / "studio" / "out"
    destination = workspace / "auracode" / "studio" / "assets"
    return _inventory(source) == _inventory(destination)


def package_assets(workspace: Path) -> None:
    source = workspace / "studio" / "out"
    destination = workspace / "auracode" / "studio" / "assets"
    _inventory(source)
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    workspace = Path.cwd().resolve()
    try:
        if args.verify:
            return 0 if verify_assets(workspace) else 1
        package_assets(workspace)
        return 0
    except (OSError, ValueError) as exc:
        print(f"Studio asset packaging failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
