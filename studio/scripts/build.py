#!/usr/bin/env python3
"""Build Aura Studio from a clean dependency installation."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


def _run(command: List[str], cwd: Path, environment: Dict[str, str]) -> int:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            shell=False,
            check=False,
        )
    except OSError as exc:
        print(f"could not execute {command[0]}: {exc}", file=sys.stderr)
        return 127
    if completed.returncode != 0:
        diagnostic = (completed.stderr or completed.stdout or "no diagnostic")[-4000:]
        print(diagnostic, file=sys.stderr)
    return completed.returncode


def main() -> int:
    studio = Path(__file__).resolve().parents[1]
    environment = dict(os.environ)
    environment.update({"CI": "1", "NEXT_TELEMETRY_DISABLED": "1"})
    npm = "npm.cmd" if os.name == "nt" else "npm"
    commands = [
        [npm, "ci", "--include=dev", "--ignore-scripts", "--no-audit"],
        [npm, "run", "typecheck"],
        [npm, "run", "build"],
    ]
    for command in commands:
        code = _run(command, studio, environment)
        if code != 0:
            return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
