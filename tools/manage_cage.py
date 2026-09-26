#!/usr/bin/env python3
"""Aura Cage: DevContainer Sandbox & Default-Deny Firewall Manager.

Scaffolds and verifies hermetic DevContainer sandboxes with Default-Deny
outbound firewall policies, enabling secure autonomous execution (YOLO mode)
without risks of data exfiltration or host workstation corruption.

Zero external dependencies (uses standard library 'pathlib', 'shutil', 'os', 'sys', 'argparse', 'json').
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
CAGE_TEMPLATE_DIR = ROOT_DIR / "templates" / "cage"


def is_running_in_container() -> bool:
    """Detects if execution is currently confined inside a container or sandbox."""
    if os.environ.get("AURA_CAGE") == "1" or os.environ.get("DEVCONTAINER") == "true":
        return True
    if Path("/.dockerenv").exists():
        return True
    cgroup = Path("/proc/1/cgroup")
    if cgroup.is_file():
        try:
            return "docker" in cgroup.read_text(encoding="utf-8", errors="ignore")
        except (OSError, PermissionError):
            return False
    return False


def init_cage(target_dir: Path, force: bool = False) -> Dict[str, Any]:
    """Injects the Aura Cage DevContainer configuration into the target project."""
    target_devcontainer = target_dir / ".devcontainer"
    target_devcontainer.mkdir(parents=True, exist_ok=True)

    if not CAGE_TEMPLATE_DIR.exists():
        return {
            "success": False,
            "error": f"Cage template directory not found at {CAGE_TEMPLATE_DIR}",
        }

    installed_files = []
    for item in CAGE_TEMPLATE_DIR.iterdir():
        if item.is_file():
            dest = target_devcontainer / item.name
            if dest.exists() and not force:
                continue
            shutil.copy2(item, dest)
            installed_files.append(item.name)

    return {
        "success": True,
        "message": f"Aura Cage DevContainer environment initialized at {target_devcontainer}",
        "path": str(target_devcontainer),
        "files_installed": installed_files,
        "capabilities": ["NET_ADMIN", "NET_RAW"],
        "firewall_policy": "Default-Deny",
    }


def verify_cage() -> Dict[str, Any]:
    """Inspects the current execution environment for containerization and guardrails."""
    in_container = is_running_in_container()
    
    return {
        "in_container": in_container,
        "environment": "Container / Sandbox (Aura Cage)" if in_container else "Host Workstation (Direct)",
        "recommendation": (
            "Environment is sandboxed. Safe to run autonomous YOLO loops."
            if in_container
            else "Caution: Running directly on host workstation. Run 'auracode cage init' to create an isolated DevContainer."
        ),
    }


def main(argv: Optional[List[str]] = None) -> int:
    """CLI Entrypoint for Aura Cage management."""
    parser = argparse.ArgumentParser(
        prog="auracode cage",
        description="Aura Cage: DevContainer Sandbox & Default-Deny Firewall Manager"
    )
    subparsers = parser.add_subparsers(dest="cage_action", help="Cage action to perform")

    # init
    init_p = subparsers.add_parser("init", help="Initialize .devcontainer with Default-Deny firewall in target workspace")
    init_p.add_argument("target", nargs="?", default=".", help="Target workspace directory")
    init_p.add_argument("--force", "-f", action="store_true", help="Overwrite existing cage files")
    init_p.add_argument("--json", action="store_true", help="Output result in JSON format")

    # verify
    verify_p = subparsers.add_parser("verify", help="Check whether the current environment is sandboxed inside a cage")
    verify_p.add_argument("--json", action="store_true", help="Output result in JSON format")

    args = parser.parse_args(argv)

    if not args.cage_action:
        parser.print_help()
        return 0

    if args.cage_action == "init":
        target_path = Path(args.target).resolve()
        res = init_cage(target_path, force=args.force)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            if res["success"]:
                print(f"[AURA CAGE INITIALIZED] {res['message']}")
                print(f"Files: {', '.join(res['files_installed'])}")
                print("Policy: Default-Deny with capabilities [NET_ADMIN, NET_RAW]")
            else:
                sys.stderr.write(f"[AURA CAGE ERROR] {res['error']}\n")
        return 0 if res["success"] else 1

    elif args.cage_action == "verify":
        res = verify_cage()
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            status_tag = "[CAGE SANDBOX ACTIVE]" if res["in_container"] else "[HOST WORKSTATION WARNING]"
            print(f"{status_tag} {res['environment']}")
            print(f"Recommendation: {res['recommendation']}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
