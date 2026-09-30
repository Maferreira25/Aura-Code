#!/usr/bin/env python3
"""Aura Code local-only runtime security / DAST engine.

This foundation intentionally limits targets to loopback hosts. It verifies
declared runtime contracts (status codes, required security headers and bounded
responses) without providing arbitrary remote scanning capability.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

from tools.assurance_result import build_result, progression_state


_ALLOWED_HOSTS = {"localhost", "127.0.0.1", "::1"}


def load_dast_suite(path: Path) -> Dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"DAST suite manifest not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"DAST suite manifest cannot be parsed: {exc}") from exc

    required = {
        "schema_version", "suite_id", "title", "requirements", "base_url",
        "checks", "timeout_seconds", "max_response_bytes",
    }
    if not isinstance(data, dict) or not required.issubset(data):
        raise ValueError("DAST suite manifest is incomplete.")
    if data.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported DAST suite schema version.")
    if not isinstance(data.get("requirements"), list) or not data["requirements"]:
        raise ValueError("DAST suite must reference at least one requirement.")
    if not isinstance(data.get("checks"), list) or not data["checks"]:
        raise ValueError("DAST suite requires at least one declared check.")

    parsed = urllib.parse.urlparse(str(data["base_url"]))
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("DAST base_url must use http or https.")
    if parsed.hostname not in _ALLOWED_HOSTS:
        raise ValueError("DAST foundation is restricted to loopback targets only.")
    if parsed.username or parsed.password:
        raise ValueError("Credentials must not be embedded in DAST base_url.")
    return data


def _join_url(base_url: str, path: str) -> str:
    base = base_url.rstrip("/") + "/"
    return urllib.parse.urljoin(base, path.lstrip("/"))


def evaluate_dast_suite(workspace: Path, manifest_path: Path) -> Dict[str, Any]:
    workspace = workspace.resolve()
    try:
        manifest = load_dast_suite(manifest_path)
    except (OSError, ValueError) as exc:
        result = build_result(
            check_id="runtime-security",
            status="ERROR",
            producer_tool="dynamic_security_engine",
            producer_method="local_http_contract",
            workspace=str(workspace),
            reason=f"DAST suite configuration error: {exc}",
        )
        return {"status": "ERROR", "canonical_result": result, "progression": progression_state([result])}

    timeout = float(manifest["timeout_seconds"])
    max_bytes = int(manifest["max_response_bytes"])
    reports: List[Dict[str, Any]] = []
    canonical_results: List[Dict[str, Any]] = []

    for item in manifest["checks"]:
        url = _join_url(str(manifest["base_url"]), str(item["path"]))
        request = urllib.request.Request(url=url, method=str(item["method"]))
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status_code = int(response.getcode())
                headers = {k.lower(): v for k, v in response.headers.items()}
                body = response.read(max_bytes + 1)
        except urllib.error.HTTPError as exc:
            status_code = int(exc.code)
            headers = {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}
            body = exc.read(max_bytes + 1) if hasattr(exc, "read") else b""
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            result = build_result(
                check_id=f"dast:{str(item['check_id']).lower()}",
                status="ERROR",
                producer_tool="dynamic_security_engine",
                producer_method="local_http_contract",
                workspace=str(workspace),
                reason=f"Runtime target could not be evaluated: {type(exc).__name__}.",
                legacy={"url": url},
            )
            canonical_results.append(result)
            reports.append({
                "check_id": item["check_id"],
                "status": "ERROR",
                "reason": "Runtime target unavailable or evaluator connection failed.",
            })
            continue

        violations: List[str] = []
        if status_code != int(item["expected_status"]):
            violations.append(
                f"expected status {item['expected_status']}, got {status_code}"
            )
        for header in item["required_headers"]:
            if str(header).lower() not in headers:
                violations.append(f"missing required header: {header}")
        if len(body) > max_bytes:
            violations.append("response exceeds configured maximum size")

        status = "FAIL" if violations else "PASS"
        reason = (
            "; ".join(violations)
            if violations
            else "Runtime status, required headers and response bounds match the declared contract."
        )
        result = build_result(
            check_id=f"dast:{str(item['check_id']).lower()}",
            status=status,
            producer_tool="dynamic_security_engine",
            producer_method="local_http_contract",
            workspace=str(workspace),
            reason=reason,
            severity="HIGH",
            legacy={
                "url": url,
                "method": item["method"],
                "status_code": status_code,
            },
        )
        canonical_results.append(result)
        reports.append({
            "check_id": item["check_id"],
            "status": status,
            "status_code": status_code,
            "violations": violations,
        })

    progression = progression_state(canonical_results)
    if any(r["status"] == "ERROR" for r in reports):
        overall = "ERROR"
    elif any(r["status"] == "FAIL" for r in reports):
        overall = "FAIL"
    elif progression["state"] == "READY":
        overall = "PASS"
    else:
        overall = "INCONCLUSIVE"

    return {
        "status": overall,
        "suite_id": manifest["suite_id"],
        "requirements": list(manifest["requirements"]),
        "checks_total": len(reports),
        "checks_pass": sum(1 for r in reports if r["status"] == "PASS"),
        "checks": reports,
        "canonical_results": canonical_results,
        "progression": progression,
    }
