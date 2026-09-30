#!/usr/bin/env python3
"""Aura Code Metamorphic Testing Engine.

Metamorphic testing verifies declared relations between executions when a
simple expected output oracle is unavailable. Every declared relation must map
to an executable, uniquely named test selector. Missing or unexecutable
relations fail closed.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping

from tools.assurance_result import build_result, progression_state


def load_metamorphic_suite(path: Path) -> Dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Metamorphic suite manifest not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Metamorphic suite manifest cannot be parsed: {exc}") from exc

    required = {
        "schema_version", "suite_id", "title", "requirements",
        "test_target", "relations", "timeout_seconds",
    }
    if not isinstance(data, dict) or not required.issubset(data):
        raise ValueError("Metamorphic suite manifest is incomplete.")
    if data.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported metamorphic suite schema version.")
    if not isinstance(data.get("requirements"), list) or not data["requirements"]:
        raise ValueError("Metamorphic suite must reference at least one requirement.")
    if not isinstance(data.get("relations"), list) or not data["relations"]:
        raise ValueError("Metamorphic suite must declare at least one relation.")

    seen = set()
    for relation in data["relations"]:
        if not isinstance(relation, dict):
            raise ValueError("Each metamorphic relation must be an object.")
        selector = relation.get("test_selector")
        relation_id = relation.get("relation_id")
        if not isinstance(selector, str) or not selector.startswith("test_mr_"):
            raise ValueError("Metamorphic test selectors must start with 'test_mr_'.")
        if relation_id in seen:
            raise ValueError(f"Duplicate metamorphic relation id: {relation_id}")
        seen.add(relation_id)
    return data


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _test_function_names(target: Path) -> List[str]:
    files = [target] if target.is_file() else sorted(target.rglob("*.py")) if target.is_dir() else []
    names: List[str] = []
    for path in files:
        if path.suffix != ".py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.append(node.name)
    return names


def evaluate_metamorphic_suite(workspace: Path, manifest_path: Path) -> Dict[str, Any]:
    workspace = workspace.resolve()
    if not workspace.is_dir():
        result = build_result(
            check_id="metamorphic-testing", status="ERROR",
            producer_tool="metamorphic_engine", producer_method="declared_relation_pytest",
            workspace=str(workspace), reason="Candidate workspace does not exist or is not a directory."
        )
        return {"status": "ERROR", "canonical_result": result, "progression": progression_state([result])}

    try:
        manifest = load_metamorphic_suite(manifest_path)
    except (OSError, ValueError) as exc:
        result = build_result(
            check_id="metamorphic-testing", status="ERROR",
            producer_tool="metamorphic_engine", producer_method="declared_relation_pytest",
            workspace=str(workspace), reason=f"Metamorphic suite configuration error: {exc}"
        )
        return {"status": "ERROR", "canonical_result": result, "progression": progression_state([result])}

    target = (workspace / str(manifest["test_target"])).resolve()
    if not _inside(target, workspace):
        result = build_result(
            check_id=f"metamorphic:{str(manifest['suite_id']).lower()}", status="ERROR",
            producer_tool="metamorphic_engine", producer_method="declared_relation_pytest",
            workspace=str(workspace), reason="Metamorphic test target escapes the candidate workspace."
        )
        return {"status": "ERROR", "canonical_result": result, "progression": progression_state([result])}

    discovered = set(_test_function_names(target))
    missing = [
        relation["test_selector"] for relation in manifest["relations"]
        if relation["test_selector"] not in discovered
    ]
    if missing:
        result = build_result(
            check_id=f"metamorphic:{str(manifest['suite_id']).lower()}", status="NOT_TESTED",
            producer_tool="metamorphic_engine", producer_method="declared_relation_pytest",
            workspace=str(workspace),
            reason="Declared metamorphic relation(s) lack executable test selectors: " + ", ".join(sorted(missing))
        )
        return {
            "status": "NOT_TESTED",
            "suite_id": manifest["suite_id"],
            "missing_selectors": sorted(missing),
            "canonical_result": result,
            "progression": progression_state([result]),
        }

    timeout = int(manifest["timeout_seconds"])
    env = os.environ.copy()
    env["PYTHONPATH"] = str(workspace) + os.pathsep + env.get("PYTHONPATH", "")
    relation_reports: List[Dict[str, Any]] = []
    canonical_results: List[Dict[str, Any]] = []

    for relation in manifest["relations"]:
        selector = str(relation["test_selector"])
        cmd = [sys.executable, "-m", "pytest", "-q", str(target), "-k", selector]
        try:
            run = subprocess.run(
                cmd, cwd=str(workspace), env=env, capture_output=True,
                text=True, timeout=timeout, check=False
            )
        except subprocess.TimeoutExpired:
            status = "ERROR"
            category = "TIMEOUT"
            reason = f"Metamorphic relation {relation['relation_id']} timed out."
            output = ""
        except (OSError, subprocess.SubprocessError) as exc:
            status = "ERROR"
            category = "RUNNER_ERROR"
            reason = f"Metamorphic evaluator failed for {relation['relation_id']}: {exc}"
            output = ""
        else:
            output = run.stdout + "\n" + run.stderr
            if run.returncode == 0:
                status = "PASS"
                category = None
                reason = f"Metamorphic relation {relation['relation_id']} held."
            elif run.returncode == 1:
                status = "FAIL"
                category = "RELATION_VIOLATED"
                reason = f"Metamorphic relation {relation['relation_id']} was violated."
            else:
                status = "ERROR"
                category = "RUNNER_ERROR"
                reason = f"Metamorphic relation {relation['relation_id']} did not complete with a recognized test outcome."

        result = build_result(
            check_id=f"metamorphic:{str(relation['relation_id']).lower()}",
            status=status,
            producer_tool="metamorphic_engine",
            producer_method="declared_relation_pytest",
            workspace=str(workspace),
            reason=reason,
            severity="HIGH",
            legacy={
                "suite_id": manifest["suite_id"],
                "relation_id": relation["relation_id"],
                "requirements": list(manifest["requirements"]),
                "transformation": relation["transformation"],
                "expected_relation": relation["expected_relation"],
                "failure_category": category,
            },
        )
        canonical_results.append(result)
        relation_reports.append({
            "relation_id": relation["relation_id"],
            "test_selector": selector,
            "status": status,
            "failure_category": category,
            "output_digest": hashlib.sha256(output.encode("utf-8", errors="replace")).hexdigest(),
        })

    progression = progression_state(canonical_results)
    if any(item["status"] == "ERROR" for item in relation_reports):
        overall = "ERROR"
    elif any(item["status"] == "FAIL" for item in relation_reports):
        overall = "FAIL"
    elif progression["state"] == "READY":
        overall = "PASS"
    else:
        overall = "INCONCLUSIVE"

    return {
        "status": overall,
        "suite_id": manifest["suite_id"],
        "requirements": list(manifest["requirements"]),
        "relations_total": len(relation_reports),
        "relations_pass": sum(1 for item in relation_reports if item["status"] == "PASS"),
        "relations": relation_reports,
        "canonical_results": canonical_results,
        "progression": progression,
    }
