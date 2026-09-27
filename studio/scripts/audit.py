#!/usr/bin/env python3
"""Audit dependencies and structural invariants of compiled Aura Studio assets."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


def _dependency_audit(studio: Path, environment: Dict[str, str]) -> int:
    npm = "npm.cmd" if os.name == "nt" else "npm"
    try:
        completed = subprocess.run(
            [npm, "audit", "--package-lock-only", "--audit-level=high", "--json"],
            cwd=studio,
            env=environment,
            capture_output=True,
            text=True,
            shell=False,
            check=False,
        )
    except OSError as exc:
        print(json.dumps({"status": "ERROR", "reason": str(exc)}))
        return 127
    if completed.returncode != 0:
        print(completed.stdout or completed.stderr)
    return completed.returncode


def _asset_findings(output: Path) -> List[str]:
    findings: List[str] = []
    if not (output / "index.html").is_file():
        findings.append("compiled entrypoint index.html is missing")
    files = sorted(path for path in output.rglob("*") if path.is_file()) if output.is_dir() else []
    if not any(path.suffix == ".js" for path in files):
        findings.append("compiled JavaScript assets are missing")
    if not any(path.suffix == ".css" for path in files):
        findings.append("compiled CSS assets are missing")
    if output.is_symlink() or any(path.is_symlink() for path in output.rglob("*")):
        findings.append("symbolic links are not allowed in compiled assets")
    searchable = b"".join(path.read_bytes() for path in files if path.suffix in {".html", ".js"})
    for marker in (b"pt-BR", b"English", b"NOT_RUN"):
        if marker not in searchable:
            findings.append(f"compiled locale/status marker is missing: {marker.decode()}")
    return findings


def main() -> int:
    studio = Path(__file__).resolve().parents[1]
    environment = dict(os.environ)
    environment["NEXT_TELEMETRY_DISABLED"] = "1"
    audit_code = _dependency_audit(studio, environment)
    findings = _asset_findings(studio / "out")
    result = {"status": "PASS" if audit_code == 0 and not findings else "FAIL", "findings": findings}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
