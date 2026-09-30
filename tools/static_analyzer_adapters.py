#!/usr/bin/env python3
"""Aura Code external static analyzer adapters.

Currently normalizes SARIF 2.1.0 reports from tools such as Semgrep or CodeQL
into a common report shape. The adapter does not infer security from an empty
report unless the report itself parsed successfully.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


def _fp(file: str, line: int, rule_id: str) -> str:
    return hashlib.sha256(f"{file}|{line}|{rule_id}".encode("utf-8")).hexdigest()


def normalize_sarif(path: Path, *, analyzer_id: str) -> Dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        return {
            "schema_version": "1.0.0",
            "analyzer_id": analyzer_id,
            "analyzer_type": "sarif-external",
            "status": "NOT_TESTED",
            "findings": [],
            "metadata": {"reason": "SARIF report file is missing."},
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema_version": "1.0.0",
            "analyzer_id": analyzer_id,
            "analyzer_type": "sarif-external",
            "status": "ERROR",
            "findings": [],
            "metadata": {"reason": f"SARIF parse failure: {exc}"},
        }

    if data.get("version") != "2.1.0" or not isinstance(data.get("runs"), list):
        return {
            "schema_version": "1.0.0",
            "analyzer_id": analyzer_id,
            "analyzer_type": "sarif-external",
            "status": "ERROR",
            "findings": [],
            "metadata": {"reason": "Unsupported or malformed SARIF document."},
        }

    findings: List[Dict[str, Any]] = []
    for run in data["runs"]:
        tool = run.get("tool", {}).get("driver", {}).get("name", analyzer_id)
        for item in run.get("results", []):
            rule_id = item.get("ruleId") or item.get("rule", {}).get("id") or "UNKNOWN_RULE"
            level = str(item.get("level") or "warning").lower()
            severity = "HIGH" if level == "error" else "LOW" if level in {"note", "info"} else "MEDIUM"
            locations = item.get("locations", [])
            file = "<unknown>"
            line = 1
            if locations:
                physical = locations[0].get("physicalLocation", {})
                file = str(physical.get("artifactLocation", {}).get("uri") or "<unknown>").replace("file://", "").lstrip("/")
                line = int(physical.get("region", {}).get("startLine", 1) or 1)
            message = str(item.get("message", {}).get("text") or "External analyzer finding.")
            findings.append({
                "fingerprint": _fp(file, line, str(rule_id)),
                "rule_id": str(rule_id),
                "severity": severity,
                "file": file,
                "line": line,
                "message": message,
                "source": None,
                "sink": None,
                "tool": str(tool),
            })

    return {
        "schema_version": "1.0.0",
        "analyzer_id": analyzer_id,
        "analyzer_type": "sarif-external",
        "status": "FAIL" if findings else "PASS",
        "findings": findings,
        "metadata": {"sarif_version": "2.1.0", "runs": len(data["runs"])},
    }
