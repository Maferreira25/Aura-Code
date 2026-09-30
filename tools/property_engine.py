#!/usr/bin/env python3
"""Aura Code Property-Based Testing Engine.

Discovers actual Hypothesis @given properties, executes them with a reproducible
seed, and emits canonical assurance results. Missing properties, unavailable
runners, timeouts, and malformed targets fail closed.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from tools.assurance_result import build_result, progression_state
from validation.tools.runner import sanitize_environment


def _decorator_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _decorator_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    return ""


def discover_property_tests(target: Path) -> Dict[str, Any]:
    """Discover Python test functions decorated with Hypothesis @given."""
    target = target.resolve()
    files: List[Path] = []
    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(target.rglob("test*.py"))
    else:
        return {
            "complete": False,
            "property_count": 0,
            "files_scanned": 0,
            "properties": [],
            "errors": [f"Target does not exist: {target}"],
        }

    properties: List[Dict[str, Any]] = []
    errors: List[str] = []
    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            errors.append(f"{path}: {exc}")
            continue

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            decorators = {_decorator_name(item) for item in node.decorator_list}
            if any(name == "given" or name.endswith(".given") for name in decorators):
                properties.append({
                    "file": str(path),
                    "name": node.name,
                    "line": getattr(node, "lineno", None),
                })

    return {
        "complete": len(errors) == 0,
        "property_count": len(properties),
        "files_scanned": len(files),
        "properties": properties,
        "errors": errors,
    }


def load_property_suite(path: Path) -> Dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Property suite manifest not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Property suite manifest cannot be parsed: {exc}") from exc
    required = {"schema_version", "suite_id", "requirements", "target", "seed", "timeout_seconds"}
    if not isinstance(data, dict) or not required.issubset(data):
        raise ValueError("Property suite manifest is incomplete.")
    if data.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported property suite schema version.")
    if not isinstance(data.get("requirements"), list) or not data["requirements"]:
        raise ValueError("Property suite must reference at least one requirement.")
    return data


def evaluate_property_suite(
    workspace: Path,
    manifest: Mapping[str, Any],
) -> Dict[str, Any]:
    """Evaluate one declared Hypothesis property suite."""
    workspace = workspace.resolve()
    if not workspace.is_dir():
        result = build_result(
            check_id="property-based",
            status="ERROR",
            producer_tool="property_engine",
            producer_method="hypothesis_pytest",
            workspace=str(workspace),
            reason="Candidate workspace does not exist or is not a directory.",
        )
        return {
            "status": "ERROR",
            "canonical_result": result,
            "progression": progression_state([result]),
        }

    try:
        target = (workspace / str(manifest["target"])).resolve()
        target.relative_to(workspace)
    except (KeyError, ValueError):
        result = build_result(
            check_id="property-based",
            status="ERROR",
            producer_tool="property_engine",
            producer_method="hypothesis_pytest",
            workspace=str(workspace),
            reason="Property suite target escapes the candidate workspace or is missing.",
        )
        return {
            "status": "ERROR",
            "canonical_result": result,
            "progression": progression_state([result]),
        }

    discovery = discover_property_tests(target)
    if not discovery["complete"]:
        result = build_result(
            check_id=f"property:{str(manifest.get('suite_id', 'unknown')).lower()}",
            status="ERROR",
            producer_tool="property_engine",
            producer_method="hypothesis_pytest",
            workspace=str(workspace),
            reason="Property discovery was incomplete: " + "; ".join(discovery["errors"]),
        )
        return {
            "status": "ERROR",
            "discovery": discovery,
            "canonical_result": result,
            "progression": progression_state([result]),
        }

    if discovery["property_count"] == 0:
        result = build_result(
            check_id=f"property:{str(manifest.get('suite_id', 'unknown')).lower()}",
            status="NOT_TESTED",
            producer_tool="property_engine",
            producer_method="hypothesis_pytest",
            workspace=str(workspace),
            reason="No Hypothesis @given property tests were discovered in the declared target.",
        )
        return {
            "status": "NOT_TESTED",
            "discovery": discovery,
            "canonical_result": result,
            "progression": progression_state([result]),
        }

    seed = int(manifest.get("seed", 0))
    timeout = int(manifest.get("timeout_seconds", 60))
    command = [
        sys.executable,
        "-m",
        "pytest",
        str(target),
        "-q",
        "--tb=no",
        f"--hypothesis-seed={seed}",
    ]

    env = sanitize_environment()
    env["PYTHONPATH"] = str(workspace)
    env["PYTHONHASHSEED"] = str(seed)

    try:
        cp = subprocess.run(
            command,
            cwd=str(workspace),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        canonical_status = "ERROR"
        reason = "Property-based test execution timed out."
        exit_code = None
        output = b"timeout"
    except (OSError, subprocess.SubprocessError) as exc:
        canonical_status = "ERROR"
        reason = f"Property-based test runner failed: {exc}"
        exit_code = None
        output = str(exc).encode("utf-8", errors="replace")
    else:
        exit_code = cp.returncode
        output = (cp.stdout + "\n" + cp.stderr).encode("utf-8", errors="replace")
        if cp.returncode == 0:
            canonical_status = "PASS"
            reason = (
                f"{discovery['property_count']} property test(s) passed with reproducible seed {seed}."
            )
        elif cp.returncode == 1:
            canonical_status = "FAIL"
            reason = (
                f"At least one property-based test produced a counterexample or test failure "
                f"with seed {seed}."
            )
        else:
            canonical_status = "ERROR"
            reason = f"Property test runner exited with infrastructure/error code {cp.returncode}."

    output_digest = hashlib.sha256(output).hexdigest()
    result = build_result(
        check_id=f"property:{str(manifest.get('suite_id', 'unknown')).lower()}",
        status=canonical_status,
        producer_tool="property_engine",
        producer_method="hypothesis_pytest",
        workspace=str(workspace),
        reason=reason,
        exit_code=exit_code,
        findings=[],
        legacy={
            "suite_id": manifest.get("suite_id"),
            "requirements": list(manifest.get("requirements", [])),
            "seed": seed,
            "property_count": discovery["property_count"],
            "output_digest": output_digest,
        },
    )

    return {
        "status": canonical_status,
        "suite_id": manifest.get("suite_id"),
        "requirements": list(manifest.get("requirements", [])),
        "seed": seed,
        "property_count": discovery["property_count"],
        "files_scanned": discovery["files_scanned"],
        "output_digest": output_digest,
        "canonical_result": result,
        "progression": progression_state([result]),
    }


def evaluate_property_suite_file(workspace: Path, manifest_path: Path) -> Dict[str, Any]:
    try:
        manifest = load_property_suite(manifest_path)
    except (OSError, ValueError) as exc:
        result = build_result(
            check_id="property-based",
            status="ERROR",
            producer_tool="property_engine",
            producer_method="hypothesis_pytest",
            workspace=str(workspace.resolve()),
            reason=f"Property suite configuration error: {exc}",
        )
        return {
            "status": "ERROR",
            "canonical_result": result,
            "progression": progression_state([result]),
        }
    return evaluate_property_suite(workspace, manifest)
