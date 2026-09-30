#!/usr/bin/env python3
"""Protected Assurance Plane policy engine.

Classifies repository paths by trust boundary and evaluates proposed changes.
The developer/implementing agent is never allowed to modify the mechanisms that
judge its own work. Held-out assets are additionally marked unreadable by policy.
Evidence stores are append-only for the developer plane.
"""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


DEFAULT_POLICY = Path(__file__).resolve().parents[1] / "policies" / "protected-assurance-plane.json"

PLANE_PROTECTED = "PROTECTED"
PLANE_HELD_OUT = "HELD_OUT"
PLANE_APPEND_ONLY = "APPEND_ONLY"
PLANE_PUBLIC_TEST = "PUBLIC_TEST"
PLANE_DEVELOPER = "DEVELOPER"


def _normalize(path: str) -> str:
    value = path.replace("\\", "/").strip()
    while value.startswith("./"):
        value = value[2:]
    return value.lstrip("/")


def _matches(path: str, pattern: str) -> bool:
    path = _normalize(path)
    pattern = _normalize(pattern)
    if fnmatch.fnmatch(path, pattern):
        return True
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return path == prefix or path.startswith(prefix + "/")
    return False


def load_policy(path: Optional[Path] = None) -> Dict[str, Any]:
    target = (path or DEFAULT_POLICY).resolve()
    if not target.is_file():
        raise FileNotFoundError(f"Protected Assurance Plane policy not found: {target}")
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Protected Assurance Plane policy cannot be parsed: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported or malformed Protected Assurance Plane policy.")
    for key in ("protected", "held_out", "append_only", "public_tests"):
        if not isinstance(data.get(key), list):
            raise ValueError(f"Policy field {key!r} must be an array.")
    return data


def classify_path(path: str, policy: Mapping[str, Any]) -> str:
    """Classify one repository-relative path using strongest-boundary precedence."""
    norm = _normalize(path)
    for pattern in policy.get("held_out", []):
        if _matches(norm, str(pattern)):
            return PLANE_HELD_OUT
    for pattern in policy.get("append_only", []):
        if _matches(norm, str(pattern)):
            return PLANE_APPEND_ONLY
    for pattern in policy.get("protected", []):
        if _matches(norm, str(pattern)):
            return PLANE_PROTECTED
    for pattern in policy.get("public_tests", []):
        if _matches(norm, str(pattern)):
            return PLANE_PUBLIC_TEST
    return PLANE_DEVELOPER


def can_read(path: str, policy: Mapping[str, Any], *, actor: str = "developer") -> bool:
    plane = classify_path(path, policy)
    if actor == "developer" and plane == PLANE_HELD_OUT:
        return False
    return True


def can_write(
    path: str,
    policy: Mapping[str, Any],
    *,
    status: str = "M",
    actor: str = "developer",
) -> bool:
    """Return whether an actor may write a path.

    The implementing developer/agent cannot write protected, held-out, or public
    test planes. Append-only locations permit only additions/untracked creation.
    """
    plane = classify_path(path, policy)
    if actor != "developer":
        return True
    if plane in {PLANE_PROTECTED, PLANE_HELD_OUT, PLANE_PUBLIC_TEST}:
        return False
    if plane == PLANE_APPEND_ONLY:
        normalized_status = status.strip().upper()
        return normalized_status in {"A", "??"}
    return True


def evaluate_changes(
    changes: Iterable[Mapping[str, Any]],
    policy: Mapping[str, Any],
    *,
    actor: str = "developer",
) -> Dict[str, Any]:
    """Evaluate repository changes against the protected-plane policy."""
    violations: List[Dict[str, Any]] = []
    classified: List[Dict[str, Any]] = []

    for item in changes:
        path = _normalize(str(item.get("file") or ""))
        status = str(item.get("status") or "")
        if not path:
            violations.append({
                "file": "",
                "status": status,
                "plane": "UNKNOWN",
                "rule": "invalid_change_path",
                "severity": "critical",
                "message": "Change has no repository-relative path.",
            })
            continue

        plane = classify_path(path, policy)
        allowed = can_write(path, policy, status=status, actor=actor)
        classified.append({"file": path, "status": status, "plane": plane, "allowed": allowed})

        if not allowed:
            if plane == PLANE_APPEND_ONLY:
                message = (
                    f"Evidence plane is append-only for developer actors; existing evidence cannot be "
                    f"modified, renamed, or deleted: {path}"
                )
                rule = "evidence_not_append_only"
            elif plane == PLANE_HELD_OUT:
                message = f"Held-out evaluator asset cannot be modified by developer actors: {path}"
                rule = "held_out_tampering"
            elif plane == PLANE_PUBLIC_TEST:
                message = f"Public test/evaluator modification requires an independent authorized workflow: {path}"
                rule = "public_test_tampering"
            else:
                message = f"Protected assurance asset cannot be modified by the implementing developer/agent: {path}"
                rule = "protected_assurance_tampering"

            violations.append({
                "file": path,
                "status": status,
                "plane": plane,
                "rule": rule,
                "severity": "critical",
                "message": message,
            })

    return {
        "status": "PASS" if not violations else "BLOCKED",
        "success": not violations,
        "actor": actor,
        "violations_count": len(violations),
        "violations": violations,
        "classified_changes": classified,
    }


def check_path_access(
    path: str,
    policy: Mapping[str, Any],
    *,
    operation: str,
    status: str = "M",
    actor: str = "developer",
) -> Dict[str, Any]:
    """Check one read/write request for pre-tool integrations."""
    op = operation.lower().strip()
    if op not in {"read", "write"}:
        return {
            "allowed": False,
            "status": "ERROR",
            "reason": f"Unsupported protected-plane operation: {operation!r}",
        }

    plane = classify_path(path, policy)
    allowed = can_read(path, policy, actor=actor) if op == "read" else can_write(
        path, policy, status=status, actor=actor
    )
    return {
        "allowed": allowed,
        "status": "PASS" if allowed else "BLOCKED",
        "plane": plane,
        "path": _normalize(path),
        "operation": op,
        "actor": actor,
        "reason": (
            "Access permitted by Protected Assurance Plane policy."
            if allowed
            else f"{op.upper()} access denied for {plane} asset."
        ),
    }
