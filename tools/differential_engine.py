#!/usr/bin/env python3
"""Aura Code Differential Testing Engine.

Compares a candidate implementation with an independently declared reference.
A divergence is INCONCLUSIVE rather than FAIL because differential testing
establishes disagreement, not which side is correct.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple

from tools.assurance_result import build_result, progression_state


_CALLABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*$")


def load_differential_suite(path: Path) -> Dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Differential suite manifest not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Differential suite manifest cannot be parsed: {exc}") from exc

    required = {
        "schema_version", "suite_id", "title", "requirements", "adapter",
        "candidate", "reference", "cases", "timeout_seconds",
    }
    if not isinstance(data, dict) or not required.issubset(data):
        raise ValueError("Differential suite manifest is incomplete.")
    if data.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported differential suite schema version.")
    if data.get("adapter") != "python-callable":
        raise ValueError("Unsupported differential adapter.")
    if not isinstance(data.get("requirements"), list) or not data["requirements"]:
        raise ValueError("Differential suite must reference at least one requirement.")
    if not isinstance(data.get("cases"), list) or not data["cases"]:
        raise ValueError("Differential suite requires at least one input case.")
    for field in ("candidate", "reference"):
        if not isinstance(data.get(field), str) or not _CALLABLE_RE.fullmatch(data[field]):
            raise ValueError(f"Invalid Python callable declaration for {field}.")
    if data["candidate"] == data["reference"]:
        raise ValueError("Candidate and reference must be distinct callables.")
    return data


def _runner_code() -> str:
    return (
        "import importlib,json,sys\n"
        "spec=sys.argv[1]\n"
        "payload=json.loads(sys.stdin.read())\n"
        "module_name,func_name=spec.split(':',1)\n"
        "module=importlib.import_module(module_name)\n"
        "func=getattr(module,func_name)\n"
        "if isinstance(payload,dict) and '__args__' in payload:\n"
        "    args=payload.get('__args__',[])\n"
        "    kwargs=payload.get('__kwargs__',{})\n"
        "    result=func(*args,**kwargs)\n"
        "else:\n"
        "    result=func(payload)\n"
        "print(json.dumps(result,sort_keys=True,separators=(',',':'),ensure_ascii=False))\n"
    )


def _invoke_callable(
    spec: str,
    case: Any,
    workspace: Path,
    timeout: int,
) -> Tuple[str, Any, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(workspace) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        run = subprocess.run(
            [sys.executable, "-c", _runner_code(), spec],
            cwd=str(workspace),
            env=env,
            input=json.dumps(case, ensure_ascii=False),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "ERROR", None, "TIMEOUT"
    except (OSError, subprocess.SubprocessError):
        return "ERROR", None, "RUNNER_ERROR"

    if run.returncode != 0:
        digest = hashlib.sha256((run.stdout + "\n" + run.stderr).encode("utf-8", errors="replace")).hexdigest()
        return "ERROR", None, f"CALLABLE_ERROR:{digest}"

    try:
        value = json.loads(run.stdout.strip())
    except json.JSONDecodeError:
        return "ERROR", None, "INVALID_JSON_RESULT"
    return "PASS", value, ""


def evaluate_differential_suite(workspace: Path, manifest_path: Path) -> Dict[str, Any]:
    workspace = workspace.resolve()
    if not workspace.is_dir():
        result = build_result(
            check_id="differential-testing", status="ERROR",
            producer_tool="differential_engine", producer_method="python_callable_reference",
            workspace=str(workspace), reason="Candidate workspace does not exist or is not a directory."
        )
        return {"status": "ERROR", "canonical_result": result, "progression": progression_state([result])}

    try:
        manifest = load_differential_suite(manifest_path)
    except (OSError, ValueError) as exc:
        result = build_result(
            check_id="differential-testing", status="ERROR",
            producer_tool="differential_engine", producer_method="python_callable_reference",
            workspace=str(workspace), reason=f"Differential suite configuration error: {exc}"
        )
        return {"status": "ERROR", "canonical_result": result, "progression": progression_state([result])}

    timeout = int(manifest["timeout_seconds"])
    case_reports: List[Dict[str, Any]] = []
    divergences: List[Dict[str, Any]] = []

    for index, case in enumerate(manifest["cases"]):
        c_status, candidate_value, c_error = _invoke_callable(
            str(manifest["candidate"]), case, workspace, timeout
        )
        r_status, reference_value, r_error = _invoke_callable(
            str(manifest["reference"]), case, workspace, timeout
        )

        if c_status == "ERROR" or r_status == "ERROR":
            result = build_result(
                check_id=f"differential:{str(manifest['suite_id']).lower()}",
                status="ERROR",
                producer_tool="differential_engine",
                producer_method="python_callable_reference",
                workspace=str(workspace),
                reason=f"Differential execution failed for case {index}.",
                legacy={
                    "case_index": index,
                    "candidate_error": c_error,
                    "reference_error": r_error,
                },
            )
            return {
                "status": "ERROR",
                "suite_id": manifest["suite_id"],
                "case_index": index,
                "failure_category": "EXECUTION_ERROR",
                "canonical_result": result,
                "progression": progression_state([result]),
            }

        matched = candidate_value == reference_value
        report = {
            "case_index": index,
            "match": matched,
            "input_digest": hashlib.sha256(
                json.dumps(case, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            ).hexdigest(),
        }
        case_reports.append(report)
        if not matched:
            divergences.append({
                "case_index": index,
                "candidate_digest": hashlib.sha256(
                    json.dumps(candidate_value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                ).hexdigest(),
                "reference_digest": hashlib.sha256(
                    json.dumps(reference_value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                ).hexdigest(),
            })

    if divergences:
        status = "INCONCLUSIVE"
        reason = (
            f"{len(divergences)} differential case(s) diverged. "
            "Differential testing does not determine which implementation is correct."
        )
    else:
        status = "PASS"
        reason = "Candidate and reference matched for every declared differential case."

    result = build_result(
        check_id=f"differential:{str(manifest['suite_id']).lower()}",
        status=status,
        producer_tool="differential_engine",
        producer_method="python_callable_reference",
        workspace=str(workspace),
        reason=reason,
        severity="HIGH",
        legacy={
            "suite_id": manifest["suite_id"],
            "requirements": list(manifest["requirements"]),
            "candidate": manifest["candidate"],
            "reference": manifest["reference"],
            "cases": len(case_reports),
            "divergences": len(divergences),
        },
    )

    return {
        "status": status,
        "suite_id": manifest["suite_id"],
        "requirements": list(manifest["requirements"]),
        "cases_total": len(case_reports),
        "matches": sum(1 for item in case_reports if item["match"]),
        "divergences": divergences,
        "cases": case_reports,
        "canonical_result": result,
        "progression": progression_state([result]),
    }
