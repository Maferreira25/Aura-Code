#!/usr/bin/env python3
"""Aura Code Property-Based Testing Engine.

First adapter: Hypothesis for Python. Property testing is treated as distinct
assurance evidence, not as ordinary example-based unit-test coverage.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from tools.assurance_result import build_result, progression_state


def load_property_suite(path: Path) -> Dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Property suite manifest not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Property suite manifest cannot be parsed: {exc}") from exc

    required = {
        "schema_version",
        "suite_id",
        "title",
        "framework",
        "requirements",
        "test_target",
        "seed",
        "timeout_seconds",
    }
    if not isinstance(data, dict) or not required.issubset(data):
        raise ValueError("Property suite manifest is incomplete.")
    if data.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported property suite schema version.")
    if data.get("framework") != "hypothesis":
        raise ValueError("Unsupported property-testing framework.")
    if not isinstance(data.get("requirements"), list) or not data["requirements"]:
        raise ValueError("Property suite must reference at least one requirement.")
    return data


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _has_hypothesis_property(path: Path) -> bool:
    """Detect an actual @given decorator structurally, without claiming execution."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return False

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            target = decorator.func if isinstance(decorator, ast.Call) else decorator
            if isinstance(target, ast.Name) and target.id == "given":
                return True
            if isinstance(target, ast.Attribute) and target.attr == "given":
                return True
    return False


def _property_files(target: Path) -> List[Path]:
    if target.is_file():
        return [target] if target.suffix == ".py" else []
    if target.is_dir():
        return sorted(p for p in target.rglob("*.py") if p.is_file())
    return []


def evaluate_property_suite(
    workspace: Path,
    manifest_path: Path,
) -> Dict[str, Any]:
    """Execute a declared property suite using a reproducible seed."""
    workspace = workspace.resolve()

    if not workspace.is_dir():
        result = build_result(
            check_id="property-testing",
            status="ERROR",
            producer_tool="property_engine",
            producer_method="hypothesis_pytest",
            workspace=str(workspace),
            reason="Candidate workspace does not exist or is not a directory.",
        )
        return {"status": "ERROR", "canonical_result": result, "progression": progression_state([result])}

    try:
        manifest = load_property_suite(manifest_path)
    except (OSError, ValueError) as exc:
        result = build_result(
            check_id="property-testing",
            status="ERROR",
            producer_tool="property_engine",
            producer_method="hypothesis_pytest",
            workspace=str(workspace),
            reason=f"Property suite configuration error: {exc}",
        )
        return {"status": "ERROR", "canonical_result": result, "progression": progression_state([result])}

    target = (workspace / str(manifest["test_target"])).resolve()
    if not _inside(target, workspace):
        result = build_result(
            check_id=f"property:{str(manifest['suite_id']).lower()}",
            status="ERROR",
            producer_tool="property_engine",
            producer_method="hypothesis_pytest",
            workspace=str(workspace),
            reason="Property test target escapes the candidate workspace.",
        )
        return {"status": "ERROR", "canonical_result": result, "progression": progression_state([result])}

    files = _property_files(target)
    property_files = [p for p in files if _has_hypothesis_property(p)]
    if not property_files:
        result = build_result(
            check_id=f"property:{str(manifest['suite_id']).lower()}",
            status="NOT_TESTED",
            producer_tool="property_engine",
            producer_method="hypothesis_pytest",
            workspace=str(workspace),
            reason="No structurally declared Hypothesis @given property was found in the target.",
        )
        return {
            "status": "NOT_TESTED",
            "suite_id": manifest["suite_id"],
            "requirements": list(manifest["requirements"]),
            "property_files": 0,
            "canonical_result": result,
            "progression": progression_state([result]),
        }

    if importlib.util.find_spec("hypothesis") is None:
        result = build_result(
            check_id=f"property:{str(manifest['suite_id']).lower()}",
            status="NOT_TESTED",
            producer_tool="property_engine",
            producer_method="hypothesis_pytest",
            workspace=str(workspace),
            reason="Hypothesis adapter is not installed; property suite was not executed.",
        )
        return {
            "status": "NOT_TESTED",
            "suite_id": manifest["suite_id"],
            "requirements": list(manifest["requirements"]),
            "property_files": len(property_files),
            "canonical_result": result,
            "progression": progression_state([result]),
        }

    seed = int(manifest["seed"])
    timeout = int(manifest["timeout_seconds"])
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        str(target),
        f"--hypothesis-seed={seed}",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(workspace) + os.pathsep + env.get("PYTHONPATH", "")

    try:
        run = subprocess.run(
            cmd,
            cwd=str(workspace),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        result = build_result(
            check_id=f"property:{str(manifest['suite_id']).lower()}",
            status="ERROR",
            producer_tool="property_engine",
            producer_method="hypothesis_pytest",
            workspace=str(workspace),
            reason="Property-based test execution timed out.",
            legacy={"seed": seed},
        )
        return {
            "status": "ERROR",
            "suite_id": manifest["suite_id"],
            "seed": seed,
            "canonical_result": result,
            "progression": progression_state([result]),
        }
    except (OSError, subprocess.SubprocessError) as exc:
        result = build_result(
            check_id=f"property:{str(manifest['suite_id']).lower()}",
            status="ERROR",
            producer_tool="property_engine",
            producer_method="hypothesis_pytest",
            workspace=str(workspace),
            reason=f"Property-based test evaluator failed: {exc}",
            legacy={"seed": seed},
        )
        return {
            "status": "ERROR",
            "suite_id": manifest["suite_id"],
            "seed": seed,
            "canonical_result": result,
            "progression": progression_state([result]),
        }

    if run.returncode == 0:
        status = "PASS"
        reason = "Declared Hypothesis properties passed for the recorded deterministic seed."
        failure_category = None
    elif run.returncode == 1:
        status = "FAIL"
        reason = "At least one declared property was falsified."
        failure_category = "PROPERTY_FALSIFIED"
    else:
        status = "ERROR"
        reason = "Property-test runner did not complete with a recognized test outcome."
        failure_category = "RUNNER_ERROR"

    result = build_result(
        check_id=f"property:{str(manifest['suite_id']).lower()}",
        status=status,
        producer_tool="property_engine",
        producer_method="hypothesis_pytest",
        workspace=str(workspace),
        reason=reason,
        severity="HIGH",
        legacy={
            "suite_id": manifest["suite_id"],
            "requirements": list(manifest["requirements"]),
            "seed": seed,
            "returncode": run.returncode,
            "failure_category": failure_category,
        },
    )

    return {
        "status": status,
        "suite_id": manifest["suite_id"],
        "requirements": list(manifest["requirements"]),
        "seed": seed,
        "property_files": len(property_files),
        "failure_category": failure_category,
        "output_digest": __import__("hashlib").sha256(
            (run.stdout + "\n" + run.stderr).encode("utf-8", errors="replace")
        ).hexdigest(),
        "canonical_result": result,
        "progression": progression_state([result]),
    }
