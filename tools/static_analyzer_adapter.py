#!/usr/bin/env python3
"""Independent static-analysis adapters and detector-diversity analysis.

External analyzers execute without a shell and must produce valid SARIF.
Tool absence, timeout, rejected exit codes, missing output, and parse failures
are ERROR. Findings visible only to independent detectors are surfaced as
ASSURANCE_GAP candidates, not automatically as confirmed vulnerabilities.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from tools.assurance_result import aggregate_status, build_result, progression_state
from tools.sarif_aggregator import SarifAggregator
from validation.tools.runner import sanitize_environment


@dataclass(frozen=True)
class AnalyzerSpec:
    analyzer_id: str
    kind: str
    command: List[str]
    sarif_output: str
    accepted_exit_codes: List[int]
    timeout_seconds: int
    required: bool


def load_static_suite(path: Path) -> Dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Static analyzer suite not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Static analyzer suite cannot be parsed: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported or malformed static analyzer suite.")
    if not isinstance(data.get("analyzers"), list) or not data["analyzers"]:
        raise ValueError("Static analyzer suite requires at least one analyzer.")
    return data


def _spec(item: Mapping[str, Any]) -> AnalyzerSpec:
    return AnalyzerSpec(
        analyzer_id=str(item["analyzer_id"]),
        kind=str(item["kind"]),
        command=[str(x) for x in item["command"]],
        sarif_output=str(item["sarif_output"]),
        accepted_exit_codes=[int(x) for x in item["accepted_exit_codes"]],
        timeout_seconds=int(item["timeout_seconds"]),
        required=bool(item["required"]),
    )


def _command_identity_ok(spec: AnalyzerSpec) -> bool:
    """Prevent accidental/misleading analyzer labels for named adapters."""
    if not spec.command:
        return False
    executable = Path(spec.command[0]).name.lower()
    if spec.kind == "semgrep":
        return executable.startswith("semgrep")
    if spec.kind == "codeql":
        return executable.startswith("codeql")
    return True


def _resolve_output(workspace: Path, rel: str) -> Optional[Path]:
    path = (workspace / rel).resolve()
    try:
        path.relative_to(workspace)
    except ValueError:
        return None
    return path


def run_analyzer(workspace: Path, spec: AnalyzerSpec) -> Dict[str, Any]:
    """Run one independent analyzer and normalize its SARIF output."""
    workspace = workspace.resolve()
    if not _command_identity_ok(spec):
        result = build_result(
            check_id=f"static:{spec.analyzer_id}",
            status="ERROR",
            producer_tool="static_analyzer_adapter",
            producer_method=spec.kind,
            workspace=str(workspace),
            reason=f"Analyzer command identity does not match declared kind {spec.kind!r}.",
        )
        return {"status": "ERROR", "analyzer_id": spec.analyzer_id, "canonical_result": result, "findings": []}

    output_path = _resolve_output(workspace, spec.sarif_output)
    if output_path is None:
        result = build_result(
            check_id=f"static:{spec.analyzer_id}",
            status="ERROR",
            producer_tool="static_analyzer_adapter",
            producer_method=spec.kind,
            workspace=str(workspace),
            reason="SARIF output path escapes the candidate workspace.",
        )
        return {"status": "ERROR", "analyzer_id": spec.analyzer_id, "canonical_result": result, "findings": []}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    executable = spec.command[0]
    if os.path.sep not in executable and shutil.which(executable) is None:
        status = "ERROR" if spec.required else "NOT_TESTED"
        result = build_result(
            check_id=f"static:{spec.analyzer_id}",
            status=status,
            producer_tool="static_analyzer_adapter",
            producer_method=spec.kind,
            workspace=str(workspace),
            reason=f"Analyzer executable is unavailable: {executable}",
        )
        return {"status": status, "analyzer_id": spec.analyzer_id, "canonical_result": result, "findings": []}

    env = sanitize_environment()
    env["PYTHONPATH"] = str(workspace)
    try:
        cp = subprocess.run(
            spec.command,
            cwd=str(workspace),
            env=env,
            capture_output=True,
            text=True,
            timeout=spec.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        status = "ERROR"
        reason = f"Analyzer {spec.analyzer_id} timed out."
        cp = None
    except (OSError, subprocess.SubprocessError) as exc:
        status = "ERROR"
        reason = f"Analyzer {spec.analyzer_id} failed to execute: {exc}"
        cp = None
    else:
        if cp.returncode not in spec.accepted_exit_codes:
            status = "ERROR"
            reason = (
                f"Analyzer {spec.analyzer_id} exited with unexpected code {cp.returncode}; "
                f"accepted={spec.accepted_exit_codes}."
            )
        elif not output_path.is_file():
            status = "ERROR"
            reason = f"Analyzer {spec.analyzer_id} did not produce declared SARIF output."
        else:
            parsed = SarifAggregator(str(workspace)).parse_sarif_file(str(output_path))
            legacy = parsed.get("status")
            if legacy == "ERROR":
                status = "ERROR"
            elif legacy == "FAIL":
                status = "FAIL"
            elif legacy == "WARN":
                status = "INCONCLUSIVE"
            elif legacy == "PASS":
                status = "PASS"
            else:
                status = "ERROR"
            reason = (
                f"Analyzer {spec.analyzer_id} produced {len(parsed.get('findings', []))} "
                f"normalized finding(s) from SARIF."
            )

    findings: List[Dict[str, Any]] = []
    if output_path.is_file():
        parsed = SarifAggregator(str(workspace)).parse_sarif_file(str(output_path))
        if isinstance(parsed.get("findings"), list):
            findings = [
                {**item, "analyzer_id": spec.analyzer_id, "analyzer_kind": spec.kind}
                for item in parsed["findings"]
            ]

    output_digest = None
    if output_path.is_file():
        output_digest = hashlib.sha256(output_path.read_bytes()).hexdigest()

    result = build_result(
        check_id=f"static:{spec.analyzer_id}",
        status=status,
        producer_tool="static_analyzer_adapter",
        producer_method=spec.kind,
        workspace=str(workspace),
        reason=reason,
        findings=findings,
        legacy={
            "analyzer_id": spec.analyzer_id,
            "kind": spec.kind,
            "sarif_digest": output_digest,
            "required": spec.required,
        },
    )
    return {
        "status": status,
        "analyzer_id": spec.analyzer_id,
        "kind": spec.kind,
        "findings": findings,
        "sarif_digest": output_digest,
        "canonical_result": result,
    }


def _normalize_native_locations(native_findings: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for item in native_findings:
        file = item.get("file") or item.get("path")
        line = item.get("line")
        if isinstance(file, str) and isinstance(line, int):
            out.append({"file": file.replace("\\", "/").lstrip("/"), "line": line})
    return out


def detector_diversity_gaps(
    native_findings: Sequence[Mapping[str, Any]],
    external_results: Sequence[Mapping[str, Any]],
    *,
    line_tolerance: int = 2,
) -> List[Dict[str, Any]]:
    """Identify external-only locations as candidates for native detector improvement."""
    native = _normalize_native_locations(native_findings)
    gaps: List[Dict[str, Any]] = []

    for result in external_results:
        for finding in result.get("findings", []):
            if not isinstance(finding, Mapping):
                continue
            file = str(finding.get("file") or "").replace("\\", "/").lstrip("/")
            line = finding.get("line")
            if not file or not isinstance(line, int):
                continue
            matched = any(
                item["file"] == file and abs(item["line"] - line) <= line_tolerance
                for item in native
            )
            if not matched:
                gaps.append({
                    "type": "ASSURANCE_GAP",
                    "analyzer_id": finding.get("analyzer_id"),
                    "rule_id": finding.get("rule_id"),
                    "file": file,
                    "line": line,
                    "severity": finding.get("severity"),
                    "message": (
                        "Independent detector reported a finding not matched by a native "
                        "finding at the same location. Candidate for native rule/fixture review."
                    ),
                })
    return gaps


def evaluate_static_suite(
    workspace: Path,
    manifest: Mapping[str, Any],
    *,
    native_findings: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    workspace = workspace.resolve()
    analyzers = manifest.get("analyzers")
    if not isinstance(analyzers, list) or not analyzers:
        result = build_result(
            check_id="independent-static-analysis",
            status="NOT_TESTED",
            producer_tool="static_analyzer_adapter",
            producer_method="sarif_adapters",
            workspace=str(workspace),
            reason="No independent static analyzers were declared.",
        )
        return {"status": "NOT_TESTED", "canonical_result": result, "progression": progression_state([result])}

    results: List[Dict[str, Any]] = []
    for item in analyzers:
        if not isinstance(item, Mapping):
            result = build_result(
                check_id="static:invalid",
                status="ERROR",
                producer_tool="static_analyzer_adapter",
                producer_method="sarif_adapters",
                workspace=str(workspace),
                reason="Malformed static analyzer declaration.",
            )
            results.append({"status": "ERROR", "canonical_result": result, "findings": []})
            continue
        try:
            spec = _spec(item)
        except (KeyError, TypeError, ValueError) as exc:
            result = build_result(
                check_id="static:invalid",
                status="ERROR",
                producer_tool="static_analyzer_adapter",
                producer_method="sarif_adapters",
                workspace=str(workspace),
                reason=f"Invalid static analyzer declaration: {exc}",
            )
            results.append({"status": "ERROR", "canonical_result": result, "findings": []})
            continue
        results.append(run_analyzer(workspace, spec))

    overall = aggregate_status(
        item["canonical_result"]["status"] for item in results
    ).value

    diversity_cfg = manifest.get("diversity") if isinstance(manifest.get("diversity"), Mapping) else {}
    gaps: List[Dict[str, Any]] = []
    if diversity_cfg.get("enabled") and native_findings is not None:
        gaps = detector_diversity_gaps(
            native_findings,
            results,
            line_tolerance=int(diversity_cfg.get("line_tolerance", 2)),
        )

    canonical_results = [item["canonical_result"] for item in results]
    progression = progression_state(canonical_results)

    return {
        "status": overall,
        "suite_id": manifest.get("suite_id"),
        "analyzers": results,
        "assurance_gaps": gaps,
        "assurance_gaps_count": len(gaps),
        "canonical_results": canonical_results,
        "progression": progression,
    }
