#!/usr/bin/env python3
"""Aura Code Metamorphic Testing Engine.

Each declared metamorphic relation must map to an explicit test target containing
an AURA_MR:<relation_id> marker. Missing relation coverage is NOT_TESTED, test
failures are FAIL, and evaluator/infrastructure failures are ERROR.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping

from tools.assurance_result import build_result, progression_state
from validation.tools.runner import sanitize_environment


def load_metamorphic_suite(path: Path) -> Dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Metamorphic suite manifest not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Metamorphic suite manifest cannot be parsed: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported or malformed metamorphic suite.")
    if not isinstance(data.get("relations"), list) or not data["relations"]:
        raise ValueError("Metamorphic suite requires at least one relation.")
    return data


def _relation_marker(relation_id: str) -> str:
    return f"AURA_MR:{relation_id}"


def evaluate_metamorphic_suite(workspace: Path, manifest: Mapping[str, Any]) -> Dict[str, Any]:
    workspace = workspace.resolve()
    if not workspace.is_dir():
        result = build_result(
            check_id="metamorphic",
            status="ERROR",
            producer_tool="metamorphic_engine",
            producer_method="declared_relation_tests",
            workspace=str(workspace),
            reason="Candidate workspace does not exist or is not a directory.",
        )
        return {"status": "ERROR", "canonical_result": result, "progression": progression_state([result])}

    relations = manifest.get("relations")
    if not isinstance(relations, list) or not relations:
        result = build_result(
            check_id="metamorphic",
            status="NOT_TESTED",
            producer_tool="metamorphic_engine",
            producer_method="declared_relation_tests",
            workspace=str(workspace),
            reason="No metamorphic relations were declared.",
        )
        return {"status": "NOT_TESTED", "canonical_result": result, "progression": progression_state([result])}

    relation_reports: List[Dict[str, Any]] = []
    targets: List[Path] = []
    missing = False

    for relation in relations:
        if not isinstance(relation, Mapping):
            relation_reports.append({"relation_id": None, "status": "ERROR", "reason": "Malformed relation record."})
            missing = True
            continue
        relation_id = str(relation.get("relation_id") or "")
        target_rel = str(relation.get("test_target") or "")
        try:
            target = (workspace / target_rel).resolve()
            target.relative_to(workspace)
        except ValueError:
            relation_reports.append({
                "relation_id": relation_id,
                "requirement_id": relation.get("requirement_id"),
                "status": "ERROR",
                "reason": "Metamorphic test target escapes workspace.",
            })
            missing = True
            continue

        if not target.is_file():
            relation_reports.append({
                "relation_id": relation_id,
                "requirement_id": relation.get("requirement_id"),
                "status": "NOT_TESTED",
                "reason": "Declared metamorphic test target is missing.",
            })
            missing = True
            continue

        try:
            body = target.read_text(encoding="utf-8")
        except OSError as exc:
            relation_reports.append({
                "relation_id": relation_id,
                "requirement_id": relation.get("requirement_id"),
                "status": "ERROR",
                "reason": f"Metamorphic test target cannot be read: {exc}",
            })
            missing = True
            continue

        marker = _relation_marker(relation_id)
        if marker not in body:
            relation_reports.append({
                "relation_id": relation_id,
                "requirement_id": relation.get("requirement_id"),
                "status": "NOT_TESTED",
                "reason": f"Declared relation marker {marker!r} was not found in its test target.",
            })
            missing = True
            continue

        targets.append(target)
        relation_reports.append({
            "relation_id": relation_id,
            "requirement_id": relation.get("requirement_id"),
            "status": "DECLARED",
            "test_target": target_rel,
        })

    hard_error = any(item["status"] == "ERROR" for item in relation_reports)
    if hard_error:
        canonical_status = "ERROR"
        reason = "One or more metamorphic relation declarations are invalid or unreadable."
        exit_code = None
        output_digest = None
    elif missing:
        canonical_status = "NOT_TESTED"
        reason = "One or more declared metamorphic relations lack an identifiable executable test."
        exit_code = None
        output_digest = None
    else:
        unique_targets = sorted({str(path) for path in targets})
        timeout = int(manifest.get("timeout_seconds", 60))
        env = sanitize_environment()
        env["PYTHONPATH"] = str(workspace)
        command = [sys.executable, "-m", "pytest", *unique_targets, "-q", "--tb=no"]
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
            reason = "Metamorphic test execution timed out."
            exit_code = None
            output = b"timeout"
        except (OSError, subprocess.SubprocessError) as exc:
            canonical_status = "ERROR"
            reason = f"Metamorphic test runner failed: {exc}"
            exit_code = None
            output = str(exc).encode("utf-8", errors="replace")
        else:
            exit_code = cp.returncode
            output = (cp.stdout + "\n" + cp.stderr).encode("utf-8", errors="replace")
            if cp.returncode == 0:
                canonical_status = "PASS"
                reason = f"All {len(relations)} declared metamorphic relation(s) passed."
                for item in relation_reports:
                    item["status"] = "PASS"
            elif cp.returncode == 1:
                canonical_status = "FAIL"
                reason = "At least one declared metamorphic relation was violated."
                for item in relation_reports:
                    item["status"] = "FAIL"
            else:
                canonical_status = "ERROR"
                reason = f"Metamorphic test runner exited with infrastructure/error code {cp.returncode}."
        output_digest = hashlib.sha256(output).hexdigest()

    result = build_result(
        check_id=f"metamorphic:{str(manifest.get('suite_id', 'unknown')).lower()}",
        status=canonical_status,
        producer_tool="metamorphic_engine",
        producer_method="declared_relation_tests",
        workspace=str(workspace),
        reason=reason,
        exit_code=exit_code,
        legacy={
            "suite_id": manifest.get("suite_id"),
            "relations_count": len(relations),
            "output_digest": output_digest,
        },
    )
    return {
        "status": canonical_status,
        "suite_id": manifest.get("suite_id"),
        "relations_count": len(relations),
        "relations": relation_reports,
        "output_digest": output_digest,
        "canonical_result": result,
        "progression": progression_state([result]),
    }


def evaluate_metamorphic_suite_file(workspace: Path, manifest_path: Path) -> Dict[str, Any]:
    try:
        manifest = load_metamorphic_suite(manifest_path)
    except (OSError, ValueError) as exc:
        result = build_result(
            check_id="metamorphic",
            status="ERROR",
            producer_tool="metamorphic_engine",
            producer_method="declared_relation_tests",
            workspace=str(workspace.resolve()),
            reason=f"Metamorphic suite configuration error: {exc}",
        )
        return {"status": "ERROR", "canonical_result": result, "progression": progression_state([result])}
    return evaluate_metamorphic_suite(workspace, manifest)
