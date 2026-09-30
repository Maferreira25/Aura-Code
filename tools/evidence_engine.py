#!/usr/bin/env python3
"""Aura Code Evidence Engine v2.

Creates and verifies evidence records bound to the evaluated repository state.
The engine is fail-closed: missing, tampered, unverifiable or stale evidence
must never be treated as positive assurance.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence
from uuid import uuid4

from tools.assurance_result import validate_status


EVIDENCE_SCHEMA_VERSION = "2.0.0"

_EXCLUDED_PARTS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "_auracode_evidence",
}

_EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log"}


def _canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON deterministically for hashing."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_paths(root: Path, paths: Optional[Sequence[Path]]) -> Optional[str]:
    """Hash an ordered set of declared files/directories relative to root."""
    if not paths:
        return None

    root = root.resolve()
    h = hashlib.sha256()
    resolved: List[Path] = []
    for item in paths:
        p = item if item.is_absolute() else (root / item)
        p = p.resolve()
        try:
            p.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"Bound evidence path escapes workspace: {p}") from exc
        if not p.exists():
            raise FileNotFoundError(f"Bound evidence path does not exist: {p}")
        resolved.append(p)

    files: List[Path] = []
    for p in resolved:
        if p.is_file():
            files.append(p)
        else:
            files.extend(sorted(x for x in p.rglob("*") if x.is_file()))

    for file_path in sorted(set(files), key=lambda x: x.as_posix()):
        rel = file_path.relative_to(root).as_posix()
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(file_path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def workspace_hash(root: Path) -> str:
    """Hash the actual inspectable workspace, including uncommitted source changes."""
    root = root.resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Workspace does not exist: {root}")

    h = hashlib.sha256()
    files: List[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part in _EXCLUDED_PARTS for part in rel.parts):
            continue
        if rel.suffix.lower() in _EXCLUDED_SUFFIXES:
            continue
        files.append(p)

    for file_path in sorted(files, key=lambda x: x.relative_to(root).as_posix()):
        rel = file_path.relative_to(root).as_posix()
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(file_path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def _git_value(root: Path, args: Sequence[str]) -> Optional[str]:
    """Read a git identity value without turning git absence into PASS."""
    try:
        cp = subprocess.run(
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if cp.returncode != 0:
        return None
    value = cp.stdout.strip()
    return value or None


def source_commit(root: Path) -> Optional[str]:
    return _git_value(root, ["rev-parse", "HEAD"])


def source_tree_hash(root: Path) -> Optional[str]:
    return _git_value(root, ["rev-parse", "HEAD^{tree}"])


def file_sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _record_digest(record: Mapping[str, Any]) -> str:
    clone = json.loads(json.dumps(record))
    clone.setdefault("integrity", {})["record_sha256"] = None
    return _sha256_bytes(_canonical_json_bytes(clone))


def create_evidence(
    result: Mapping[str, Any],
    workspace: Path,
    *,
    location: str,
    evidence_type: str = "canonical-assurance-result",
    description: Optional[str] = None,
    independence: str = "deterministic-tool",
    artifact: Optional[Path] = None,
    config_paths: Optional[Sequence[Path]] = None,
    ruleset_paths: Optional[Sequence[Path]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create evidence bound to the exact current target state."""
    workspace = workspace.resolve()
    if not isinstance(result, Mapping):
        raise ValueError("Canonical assurance result must be a mapping.")
    status = result.get("status")
    validate_status(status)
    check_id = result.get("check_id")
    if not isinstance(check_id, str) or not check_id:
        raise ValueError("Canonical result check_id is required.")
    if not location:
        raise ValueError("Evidence location is required.")

    producer = result.get("producer")
    if not isinstance(producer, Mapping):
        raise ValueError("Canonical result producer metadata is required.")

    artifact_digest = None
    if artifact is not None:
        artifact_path = artifact if artifact.is_absolute() else (workspace / artifact)
        artifact_path = artifact_path.resolve()
        try:
            artifact_path.relative_to(workspace)
        except ValueError as exc:
            raise ValueError("Artifact path escapes workspace.") from exc
        if not artifact_path.is_file():
            raise FileNotFoundError(f"Artifact not found: {artifact_path}")
        artifact_digest = file_sha256(artifact_path)

    result_copy = json.loads(json.dumps(result))
    result_digest = _sha256_bytes(_canonical_json_bytes(result_copy))

    record: Dict[str, Any] = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "evidence_id": f"EV-{uuid4()}",
        "control_id": result.get("control_id"),
        "check_id": check_id,
        "type": evidence_type,
        "description": description or str(result.get("reason") or "Canonical assurance evidence."),
        "producer": {
            "tool": str(producer.get("tool") or "unknown"),
            "tool_version": producer.get("tool_version"),
            "method": str(producer.get("method") or "unknown"),
            "independence": independence,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "location": location,
        "subject": {
            "source_commit": source_commit(workspace),
            "source_tree_hash": source_tree_hash(workspace),
            "workspace_hash": workspace_hash(workspace),
            "artifact_digest": artifact_digest,
            "config_hash": _hash_paths(workspace, config_paths),
            "ruleset_hash": _hash_paths(workspace, ruleset_paths),
        },
        "integrity": {
            "result_sha256": result_digest,
            "record_sha256": None,
        },
        "freshness": "VALID",
        "result": result_copy,
        "metadata": metadata or {},
    }
    record["integrity"]["record_sha256"] = _record_digest(record)
    return record


def verify_evidence(
    record: Mapping[str, Any],
    workspace: Path,
    *,
    artifact: Optional[Path] = None,
    config_paths: Optional[Sequence[Path]] = None,
    ruleset_paths: Optional[Sequence[Path]] = None,
) -> Dict[str, Any]:
    """Verify evidence integrity and freshness against the current workspace."""
    workspace = workspace.resolve()
    if not isinstance(record, Mapping):
        return {"status": "INVALID", "reason": "Evidence record is not an object."}

    required = {
        "schema_version",
        "evidence_id",
        "check_id",
        "producer",
        "subject",
        "integrity",
        "result",
    }
    missing = sorted(required - set(record))
    if missing:
        return {"status": "INVALID", "reason": f"Missing evidence fields: {', '.join(missing)}"}

    if record.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        return {"status": "INVALID", "reason": "Unsupported evidence schema version."}

    integrity = record.get("integrity")
    subject = record.get("subject")
    result = record.get("result")
    if not isinstance(integrity, Mapping) or not isinstance(subject, Mapping) or not isinstance(result, Mapping):
        return {"status": "INVALID", "reason": "Malformed evidence subject, integrity, or result."}

    try:
        validate_status(result.get("status"))
    except ValueError as exc:
        return {"status": "INVALID", "reason": f"Invalid canonical result in evidence: {exc}"}

    expected_result_hash = _sha256_bytes(_canonical_json_bytes(result))
    if integrity.get("result_sha256") != expected_result_hash:
        return {"status": "INVALID", "reason": "Canonical result digest mismatch."}

    expected_record_hash = _record_digest(record)
    if integrity.get("record_sha256") != expected_record_hash:
        return {"status": "INVALID", "reason": "Evidence record digest mismatch."}

    try:
        current_workspace_hash = workspace_hash(workspace)
        current_config_hash = _hash_paths(workspace, config_paths)
        current_ruleset_hash = _hash_paths(workspace, ruleset_paths)
    except (OSError, ValueError) as exc:
        return {"status": "INVALID", "reason": f"Unable to verify bound workspace inputs: {exc}"}

    current_artifact_digest = None
    if artifact is not None:
        artifact_path = artifact if artifact.is_absolute() else (workspace / artifact)
        artifact_path = artifact_path.resolve()
        if not artifact_path.is_file():
            return {"status": "MISSING", "reason": f"Bound artifact is missing: {artifact_path}"}
        current_artifact_digest = file_sha256(artifact_path)

    comparisons = {
        "source_commit": source_commit(workspace),
        "source_tree_hash": source_tree_hash(workspace),
        "workspace_hash": current_workspace_hash,
        "artifact_digest": current_artifact_digest,
        "config_hash": current_config_hash,
        "ruleset_hash": current_ruleset_hash,
    }

    stale_fields = [
        key for key, current in comparisons.items()
        if subject.get(key) != current
    ]
    if stale_fields:
        return {
            "status": "STALE",
            "reason": "Evidence no longer matches current target state.",
            "stale_fields": stale_fields,
        }

    return {"status": "VALID", "reason": "Evidence integrity and target bindings are current."}


def write_evidence(record: Mapping[str, Any], path: Path) -> Path:
    """Persist one evidence record atomically enough for local tooling."""
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def verify_evidence_file(
    path: Path,
    workspace: Path,
    *,
    artifact: Optional[Path] = None,
    config_paths: Optional[Sequence[Path]] = None,
    ruleset_paths: Optional[Sequence[Path]] = None,
) -> Dict[str, Any]:
    """Load and verify a persisted evidence record."""
    path = path.resolve()
    if not path.is_file():
        return {"status": "MISSING", "reason": f"Evidence file not found: {path}"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "INVALID", "reason": f"Evidence file cannot be parsed: {exc}"}
    return verify_evidence(
        data,
        workspace,
        artifact=artifact,
        config_paths=config_paths,
        ruleset_paths=ruleset_paths,
    )
