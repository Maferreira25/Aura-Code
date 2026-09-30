#!/usr/bin/env python3
"""Generalized held-out evaluator for Aura Code.

Held-out tests are kept outside the candidate workspace, executed through the
existing isolation runner, and never returned verbatim to the implementing
agent. Missing, malformed, timed-out, tampered, or side-effecting evaluations
fail closed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from tools.assurance_result import build_result, progression_state
from tools.evidence_engine import workspace_hash
from validation.tools.runner import DEFAULT_CONTAINER_IMAGE, get_runner


def _tree_hash(root: Path) -> str:
    """Hash stable evaluator inputs, excluding interpreter-generated caches."""
    root = root.resolve()
    h = hashlib.sha256()
    files: List[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if "__pycache__" in rel.parts:
            continue
        if rel.suffix.lower() in {".pyc", ".pyo"}:
            continue
        files.append(path)

    for path in sorted(files, key=lambda p: p.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def load_suite_manifest(suite_dir: Path) -> Dict[str, Any]:
    manifest_path = suite_dir.resolve() / "suite.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Held-out suite manifest not found: {manifest_path}")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Held-out suite manifest cannot be parsed: {exc}") from exc

    required = {
        "schema_version",
        "suite_id",
        "title",
        "category",
        "requirements",
        "test_glob",
        "disclosure",
    }
    if not isinstance(data, dict) or not required.issubset(data):
        raise ValueError("Held-out suite manifest is incomplete.")
    if data.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported held-out suite schema version.")
    if not isinstance(data.get("requirements"), list) or not data["requirements"]:
        raise ValueError("Held-out suite must reference at least one requirement.")
    return data


def _public_reason(manifest: Mapping[str, Any], status: str) -> str:
    disclosure = manifest.get("disclosure")
    category = manifest.get("category", "OTHER")
    requirements = manifest.get("requirements", [])
    if status == "PASS":
        if disclosure == "REQUIREMENT_ONLY":
            return f"Held-out evaluation passed for requirement(s): {', '.join(map(str, requirements))}."
        return f"Held-out {category} evaluation passed."
    if disclosure == "REQUIREMENT_ONLY":
        return f"Held-out evaluation did not pass for requirement(s): {', '.join(map(str, requirements))}."
    return f"Held-out {category} evaluation did not pass."


def evaluate_held_out(
    workspace: Path,
    suite_dir: Path,
    *,
    isolation: str = "auto",
    strict_mode: bool = False,
    image: str = DEFAULT_CONTAINER_IMAGE,
) -> Dict[str, Any]:
    """Run a protected suite without exposing test source or raw test output."""
    workspace = workspace.resolve()
    suite_dir = suite_dir.resolve()

    if not workspace.is_dir():
        result = build_result(
            check_id="held-out",
            status="ERROR",
            producer_tool="heldout_runner",
            producer_method="protected_test_execution",
            workspace=str(workspace),
            reason="Candidate workspace does not exist or is not a directory.",
        )
        return {
            "status": "ERROR",
            "progression": progression_state([result]),
            "canonical_result": result,
            "disclosure": {"message": "Held-out evaluation unavailable."},
        }

    if not suite_dir.exists():
        result = build_result(
            check_id="held-out",
            status="NOT_TESTED",
            producer_tool="heldout_runner",
            producer_method="protected_test_execution",
            workspace=str(workspace),
            reason="No held-out suite was available for this target.",
        )
        return {
            "status": "NOT_TESTED",
            "progression": progression_state([result]),
            "canonical_result": result,
            "disclosure": {"message": "Held-out evaluation was not performed."},
        }

    if not suite_dir.is_dir():
        result = build_result(
            check_id="held-out",
            status="ERROR",
            producer_tool="heldout_runner",
            producer_method="protected_test_execution",
            workspace=str(workspace),
            reason="Held-out suite path is not a directory.",
        )
        return {
            "status": "ERROR",
            "progression": progression_state([result]),
            "canonical_result": result,
            "disclosure": {"message": "Held-out evaluator configuration is invalid."},
        }

    if _is_within(suite_dir, workspace):
        result = build_result(
            check_id="held-out",
            status="ERROR",
            producer_tool="heldout_runner",
            producer_method="protected_test_execution",
            workspace=str(workspace),
            reason="Held-out suite is inside the candidate workspace and therefore not independent.",
        )
        return {
            "status": "ERROR",
            "progression": progression_state([result]),
            "canonical_result": result,
            "disclosure": {"message": "Held-out evaluator independence requirement was not satisfied."},
        }

    try:
        manifest = load_suite_manifest(suite_dir)
    except (OSError, ValueError) as exc:
        result = build_result(
            check_id="held-out",
            status="ERROR",
            producer_tool="heldout_runner",
            producer_method="protected_test_execution",
            workspace=str(workspace),
            reason=f"Held-out suite configuration error: {exc}",
        )
        return {
            "status": "ERROR",
            "progression": progression_state([result]),
            "canonical_result": result,
            "disclosure": {"message": "Held-out evaluator configuration is invalid."},
        }

    test_glob = str(manifest["test_glob"])
    test_files = sorted(p for p in suite_dir.glob(test_glob) if p.is_file())
    if not test_files:
        result = build_result(
            check_id=f"held-out:{str(manifest['suite_id']).lower()}",
            status="NOT_TESTED",
            producer_tool="heldout_runner",
            producer_method="protected_test_execution",
            workspace=str(workspace),
            reason="Held-out suite contained no executable tests matching its declared pattern.",
        )
        return {
            "status": "NOT_TESTED",
            "suite_id": manifest["suite_id"],
            "category": manifest["category"],
            "requirements": list(manifest["requirements"]),
            "progression": progression_state([result]),
            "canonical_result": result,
            "disclosure": {"message": _public_reason(manifest, "NOT_TESTED")},
        }

    suite_hash_before = _tree_hash(suite_dir)
    workspace_hash_before = workspace_hash(workspace)

    timeout = int(manifest.get("timeout_seconds", 30))
    try:
        execution_runner = get_runner(
            mode=isolation,
            strict_mode=strict_mode,
            image=image,
        )
        raw = execution_runner.run_tests(
            workspace,
            suite_dir,
            env_vars=None,
            timeout=timeout,
            protected_dir=suite_dir,
        )
    except Exception as exc:
        result = build_result(
            check_id=f"held-out:{str(manifest['suite_id']).lower()}",
            status="ERROR",
            producer_tool="heldout_runner",
            producer_method="protected_test_execution",
            workspace=str(workspace),
            reason=f"Held-out evaluator could not execute: {exc}",
        )
        return {
            "status": "ERROR",
            "suite_id": manifest["suite_id"],
            "category": manifest["category"],
            "requirements": list(manifest["requirements"]),
            "progression": progression_state([result]),
            "canonical_result": result,
            "disclosure": {"message": "Held-out evaluator could not complete."},
        }

    suite_hash_after = _tree_hash(suite_dir)
    workspace_hash_after = workspace_hash(workspace)

    timed_out = bool(raw.get("timed_out", False))
    oracle_tampering = bool(raw.get("oracle_tampering_detected", False))
    returncode = raw.get("returncode")
    suite_changed = suite_hash_before != suite_hash_after
    workspace_changed = workspace_hash_before != workspace_hash_after

    if suite_changed:
        canonical_status = "ERROR"
        internal_reason = "Held-out evaluator files changed during evaluation."
        failure_category = "EVALUATOR_INTEGRITY"
    elif workspace_changed:
        canonical_status = "ERROR"
        internal_reason = "Candidate workspace changed during held-out evaluation."
        failure_category = "EVALUATION_SIDE_EFFECT"
    elif timed_out:
        canonical_status = "ERROR"
        internal_reason = "Held-out evaluation timed out."
        failure_category = "TIMEOUT"
    elif oracle_tampering:
        canonical_status = "FAIL"
        internal_reason = "Oracle tampering was detected during held-out evaluation."
        failure_category = "ORACLE_TAMPERING"
    elif returncode == 0:
        canonical_status = "PASS"
        internal_reason = _public_reason(manifest, "PASS")
        failure_category = None
    else:
        canonical_status = "FAIL"
        internal_reason = _public_reason(manifest, "FAIL")
        failure_category = "HELD_OUT_TEST_FAILURE"

    output_material = (
        str(raw.get("stdout", "")) + "\n" + str(raw.get("stderr", ""))
    ).encode("utf-8", errors="replace")
    output_digest = hashlib.sha256(output_material).hexdigest()

    result = build_result(
        check_id=f"held-out:{str(manifest['suite_id']).lower()}",
        status=canonical_status,
        producer_tool="heldout_runner",
        producer_method="protected_test_execution",
        workspace=str(workspace),
        reason=internal_reason,
        severity="CRITICAL" if manifest.get("category") in {"SECURITY", "PRIVACY", "DATA_INTEGRITY"} else "HIGH",
        artifact_digest=suite_hash_before,
        legacy={
            "suite_id": manifest["suite_id"],
            "category": manifest["category"],
            "requirements": list(manifest["requirements"]),
            "runner_backend": raw.get("backend"),
            "strong_isolation": bool(getattr(execution_runner, "is_strong_isolation", False)),
            "output_digest": output_digest,
            "failure_category": failure_category,
        },
    )

    return {
        "status": canonical_status,
        "suite_id": manifest["suite_id"],
        "category": manifest["category"],
        "requirements": list(manifest["requirements"]),
        "tests_present": len(test_files),
        "suite_digest": suite_hash_before,
        "runner_backend": raw.get("backend"),
        "strong_isolation": bool(getattr(execution_runner, "is_strong_isolation", False)),
        "output_digest": output_digest,
        "failure_category": failure_category,
        "progression": progression_state([result]),
        "canonical_result": result,
        "disclosure": {
            "mode": manifest["disclosure"],
            "message": _public_reason(manifest, canonical_status),
        },
    }
