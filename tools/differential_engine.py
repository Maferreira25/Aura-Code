#!/usr/bin/env python3
"""Aura Code Differential Testing Engine.

Executes a reference and candidate command with identical JSON inputs over stdin.
Outputs must be valid JSON and are compared canonically. A divergence is
INCONCLUSIVE because differential testing alone cannot determine which side is
correct. Execution failures are ERROR.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from tools.assurance_result import build_result, progression_state
from validation.tools.runner import sanitize_environment


def load_differential_suite(path: Path) -> Dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Differential suite manifest not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Differential suite manifest cannot be parsed: {exc}") from exc
    required = {
        "schema_version",
        "suite_id",
        "requirements",
        "reference_command",
        "candidate_command",
        "cases",
        "timeout_seconds",
    }
    if not isinstance(data, dict) or not required.issubset(data):
        raise ValueError("Differential suite manifest is incomplete.")
    if data.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported differential suite schema version.")
    return data


def _run_json_command(
    command: Sequence[str],
    case: Any,
    workspace: Path,
    timeout: int,
) -> Tuple[str, Any, str]:
    """Return state, parsed output, digest/reason without using a shell."""
    if not command or not all(isinstance(item, str) and item for item in command):
        return "ERROR", None, "Invalid empty/non-string command."

    env = sanitize_environment()
    env["PYTHONPATH"] = str(workspace)
    input_text = json.dumps(case, sort_keys=True, ensure_ascii=False)
    try:
        cp = subprocess.run(
            list(command),
            cwd=str(workspace),
            env=env,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "ERROR", None, "Command timed out."
    except (OSError, subprocess.SubprocessError) as exc:
        return "ERROR", None, f"Command failed to execute: {exc}"

    raw = (cp.stdout or "").strip()
    digest = hashlib.sha256(
        ((cp.stdout or "") + "\n" + (cp.stderr or "")).encode("utf-8", errors="replace")
    ).hexdigest()

    if cp.returncode != 0:
        return "ERROR", None, f"Command exited with code {cp.returncode}; output_digest={digest}."
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return "ERROR", None, f"Command did not emit valid JSON; output_digest={digest}."
    return "OK", parsed, digest


def evaluate_differential_suite(workspace: Path, manifest: Mapping[str, Any]) -> Dict[str, Any]:
    workspace = workspace.resolve()
    if not workspace.is_dir():
        result = build_result(
            check_id="differential",
            status="ERROR",
            producer_tool="differential_engine",
            producer_method="json_stdin_comparison",
            workspace=str(workspace),
            reason="Candidate workspace does not exist or is not a directory.",
        )
        return {"status": "ERROR", "canonical_result": result, "progression": progression_state([result])}

    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        result = build_result(
            check_id=f"differential:{str(manifest.get('suite_id', 'unknown')).lower()}",
            status="NOT_TESTED",
            producer_tool="differential_engine",
            producer_method="json_stdin_comparison",
            workspace=str(workspace),
            reason="No differential input cases were supplied.",
        )
        return {
            "status": "NOT_TESTED",
            "cases_total": 0,
            "canonical_result": result,
            "progression": progression_state([result]),
        }

    reference = manifest.get("reference_command")
    candidate = manifest.get("candidate_command")
    if not isinstance(reference, list) or not isinstance(candidate, list):
        result = build_result(
            check_id="differential",
            status="ERROR",
            producer_tool="differential_engine",
            producer_method="json_stdin_comparison",
            workspace=str(workspace),
            reason="Differential commands must be argument arrays.",
        )
        return {"status": "ERROR", "canonical_result": result, "progression": progression_state([result])}

    timeout = int(manifest.get("timeout_seconds", 30))
    divergences: List[Dict[str, Any]] = []
    case_digests: List[str] = []

    for index, case in enumerate(cases):
        case_digest = hashlib.sha256(
            json.dumps(case, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        case_digests.append(case_digest)

        ref_state, ref_output, ref_meta = _run_json_command(reference, case, workspace, timeout)
        if ref_state != "OK":
            result = build_result(
                check_id=f"differential:{str(manifest.get('suite_id', 'unknown')).lower()}",
                status="ERROR",
                producer_tool="differential_engine",
                producer_method="json_stdin_comparison",
                workspace=str(workspace),
                reason=f"Reference implementation could not be evaluated for case {index}: {ref_meta}",
            )
            return {
                "status": "ERROR",
                "cases_total": len(cases),
                "case_index": index,
                "side": "reference",
                "canonical_result": result,
                "progression": progression_state([result]),
            }

        cand_state, cand_output, cand_meta = _run_json_command(candidate, case, workspace, timeout)
        if cand_state != "OK":
            result = build_result(
                check_id=f"differential:{str(manifest.get('suite_id', 'unknown')).lower()}",
                status="ERROR",
                producer_tool="differential_engine",
                producer_method="json_stdin_comparison",
                workspace=str(workspace),
                reason=f"Candidate implementation could not be evaluated for case {index}: {cand_meta}",
            )
            return {
                "status": "ERROR",
                "cases_total": len(cases),
                "case_index": index,
                "side": "candidate",
                "canonical_result": result,
                "progression": progression_state([result]),
            }

        if ref_output != cand_output:
            divergences.append({
                "case_index": index,
                "case_digest": case_digest,
                "reference_output_digest": hashlib.sha256(
                    json.dumps(ref_output, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                ).hexdigest(),
                "candidate_output_digest": hashlib.sha256(
                    json.dumps(cand_output, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                ).hexdigest(),
            })

    if divergences:
        canonical_status = "INCONCLUSIVE"
        reason = (
            f"{len(divergences)} of {len(cases)} differential case(s) diverged. "
            "Differential testing does not establish which implementation is correct."
        )
    else:
        canonical_status = "PASS"
        reason = f"Reference and candidate outputs matched for all {len(cases)} differential case(s)."

    result = build_result(
        check_id=f"differential:{str(manifest.get('suite_id', 'unknown')).lower()}",
        status=canonical_status,
        producer_tool="differential_engine",
        producer_method="json_stdin_comparison",
        workspace=str(workspace),
        reason=reason,
        findings=divergences,
        legacy={
            "suite_id": manifest.get("suite_id"),
            "requirements": list(manifest.get("requirements", [])),
            "cases_total": len(cases),
            "case_digests": case_digests,
        },
    )
    return {
        "status": canonical_status,
        "suite_id": manifest.get("suite_id"),
        "requirements": list(manifest.get("requirements", [])),
        "cases_total": len(cases),
        "divergences_count": len(divergences),
        "divergences": divergences,
        "canonical_result": result,
        "progression": progression_state([result]),
    }


def evaluate_differential_suite_file(workspace: Path, manifest_path: Path) -> Dict[str, Any]:
    try:
        manifest = load_differential_suite(manifest_path)
    except (OSError, ValueError) as exc:
        result = build_result(
            check_id="differential",
            status="ERROR",
            producer_tool="differential_engine",
            producer_method="json_stdin_comparison",
            workspace=str(workspace.resolve()),
            reason=f"Differential suite configuration error: {exc}",
        )
        return {"status": "ERROR", "canonical_result": result, "progression": progression_state([result])}
    return evaluate_differential_suite(workspace, manifest)
