#!/usr/bin/env python3
"""Verify that Aura Studio server files and compiled assets are packaged intact."""

import hashlib
import json
from pathlib import Path
from typing import Dict, List

from tools.version import FRAMEWORK_VERSION


def _result(
    status: str,
    reason: str,
    findings: List[str],
    verified_assets: int = 0,
    workflow_status: str = "NOT_RUN",
    workflow_reason: str = "Aura Studio workflows have not been validated.",
) -> Dict[str, object]:
    return {
        "status": status,
        "complete": status == "PASS",
        "reason": reason,
        "verified_assets": verified_assets,
        "findings": findings,
        "workflow_status": workflow_status,
        "workflow_reason": workflow_reason,
    }


def verify_studio_package(package_root: Path) -> Dict[str, object]:
    """Validate the Studio manifest, language catalogs, paths, sizes, and hashes."""
    studio_root = (Path(package_root).resolve() / "auracode" / "studio").resolve()
    manifest_path = studio_root / "manifest.json"
    if not manifest_path.is_file():
        return _result("NOT_RUN", "Aura Studio manifest is not packaged.", [])

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return _result("ERROR", f"Aura Studio manifest cannot be read: {exc}", [str(exc)])
    if not isinstance(manifest, dict):
        return _result("FAIL", "Aura Studio manifest must be a JSON object.", ["invalid manifest root"])

    declared_status = manifest.get("status")
    workflow_status = str(manifest.get("workflow_status") or "NOT_RUN")
    workflow_reason = str(manifest.get("workflow_reason") or "Aura Studio workflows have not been validated.")
    if workflow_status not in {"PASS", "FAIL", "NOT_RUN", "NOT_APPLICABLE", "ERROR"}:
        workflow_status = "ERROR"
        workflow_reason = "Aura Studio manifest declares an invalid workflow status."
    if declared_status != "READY":
        reason = str(manifest.get("reason") or "Aura Studio declares that it is not ready.")
        return _result("NOT_RUN", reason, [], workflow_status=workflow_status, workflow_reason=workflow_reason)

    findings: List[str] = []
    if manifest.get("schema_version") != 1:
        findings.append("unsupported or missing schema_version")
    if manifest.get("framework_version") != FRAMEWORK_VERSION:
        findings.append("framework_version differs from the installed core")
    locales = manifest.get("locales")
    if not isinstance(locales, list) or not {"pt-BR", "en"}.issubset(set(locales)):
        findings.append("required locales pt-BR and en are not both declared")
    entrypoint = manifest.get("entrypoint")
    if not isinstance(entrypoint, str) or not entrypoint.strip():
        findings.append("entrypoint is missing")
        entrypoint = ""
    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets:
        findings.append("hashed asset inventory is empty")
        assets = []

    verified = 0
    declared_paths: List[str] = []
    for index, item in enumerate(assets):
        if not isinstance(item, dict):
            findings.append(f"asset {index} is not an object")
            continue
        relative = item.get("path")
        if not isinstance(relative, str) or not relative.strip():
            findings.append(f"asset {index} has no path")
            continue
        normalized = relative.replace("\\", "/")
        candidate = (studio_root / normalized).resolve()
        try:
            candidate.relative_to(studio_root)
        except ValueError:
            findings.append(f"asset path escapes the Studio directory: {relative}")
            continue
        declared_paths.append(normalized)
        if not candidate.is_file():
            findings.append(f"asset is missing: {normalized}")
            continue
        content = candidate.read_bytes()
        if item.get("bytes") != len(content):
            findings.append(f"asset byte count differs: {normalized}")
            continue
        if item.get("sha256") != hashlib.sha256(content).hexdigest():
            findings.append(f"asset hash differs: {normalized}")
            continue
        verified += 1
    if entrypoint and entrypoint.replace("\\", "/") not in declared_paths:
        findings.append("entrypoint is not present in the hashed asset inventory")
    if len(declared_paths) != len(set(declared_paths)):
        findings.append("asset inventory contains duplicate paths")

    if findings:
        return _result(
            "FAIL", "Aura Studio package is incomplete or inconsistent.", findings, verified,
            workflow_status, workflow_reason,
        )
    return _result(
        "PASS", "Aura Studio package manifest and assets are intact.", [], verified,
        workflow_status, workflow_reason,
    )
