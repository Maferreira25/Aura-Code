#!/usr/bin/env python3
"""Generate, audit, reproduce, and evidence deterministic artifacts."""

import hashlib
import json
import os
import secrets
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tools.version import FRAMEWORK_VERSION


def _hash_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical_hash(value: object) -> str:
    content = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _hash_bytes(content)


def _inside(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes workspace: {relative}") from exc
    return candidate


def _safe_environment(run_root: Path) -> Dict[str, str]:
    allowed = ("PATH", "PATHEXT", "SystemRoot", "WINDIR", "COMSPEC")
    environment = {key: os.environ[key] for key in allowed if key in os.environ}
    temporary = run_root / ".runtime"
    cache = temporary / "npm-cache"
    temporary.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    environment.update(
        {
            "HOME": str(temporary),
            "USERPROFILE": str(temporary),
            "APPDATA": str(temporary),
            "LOCALAPPDATA": str(temporary),
            "TEMP": str(temporary),
            "TMP": str(temporary),
            "NPM_CONFIG_CACHE": str(cache),
            "NPM_CONFIG_USERCONFIG": str(temporary / "empty-npmrc"),
            "PYTHONIOENCODING": "utf-8",
        }
    )
    return environment


def _run(command: List[str], cwd: Path, environment: Dict[str, str], timeout: int) -> Tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            shell=False,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, str(exc)
    diagnostic = (completed.stderr or completed.stdout or "").strip()[:1000]
    return completed.returncode, diagnostic


def _prepare_run(workspace: Path, run_root: Path, inputs: List[str]) -> None:
    for relative in inputs:
        source = _inside(workspace, relative)
        describe_path(source)
        destination = _inside(run_root, relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)


def describe_path(path: Path) -> Dict[str, object]:
    """Return a canonical, symlink-free description of a file or directory tree."""
    path = Path(path)
    if path.is_symlink() or not path.exists():
        raise ValueError(f"artifact path is missing or symbolic: {path}")
    if path.is_file():
        content = path.read_bytes()
        return {"kind": "file", "bytes": len(content), "sha256": _hash_bytes(content)}
    if not path.is_dir():
        raise ValueError(f"artifact path is not a file or directory: {path}")
    files: List[Dict[str, object]] = []
    for candidate in sorted(path.rglob("*")):
        if candidate.is_symlink():
            raise ValueError(f"symbolic links are not allowed in artifacts: {candidate}")
        if candidate.is_file():
            content = candidate.read_bytes()
            files.append(
                {
                    "path": candidate.relative_to(path).as_posix(),
                    "bytes": len(content),
                    "sha256": _hash_bytes(content),
                }
            )
    return {
        "kind": "directory",
        "bytes": sum(int(item["bytes"]) for item in files),
        "sha256": _canonical_hash(files),
        "files": files,
    }


def _copy_artifact(source: Path, destination: Path, kind: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if kind == "file":
        shutil.copy2(source, destination)
        return
    if destination.is_symlink():
        raise ValueError(f"artifact destination cannot be symbolic: {destination}")
    token = secrets.token_hex(16)
    staged = destination.parent / f".{destination.name}.{token}.new"
    backup = destination.parent / f".{destination.name}.{token}.previous"
    try:
        shutil.copytree(source, staged)
        if destination.exists():
            destination.replace(backup)
        try:
            staged.replace(destination)
        except OSError:
            if backup.exists() and not destination.exists():
                backup.replace(destination)
            raise
    finally:
        if staged.exists():
            shutil.rmtree(staged, ignore_errors=True)
        if backup.exists():
            shutil.rmtree(backup, ignore_errors=True)


def _persist(workspace: Path, result: Dict[str, object], artifact_path: str) -> Dict[str, object]:
    result["evidence_sha256"] = _canonical_hash(result)
    safe_name = artifact_path.replace("\\", "/").replace("/", "_").replace(".", "_")
    evidence = workspace / ".auracode" / "evidence" / "artifacts" / f"{safe_name}-{result['evidence_sha256']}.json"
    result["evidence_path"] = str(evidence)
    evidence.parent.mkdir(parents=True, exist_ok=True)
    temporary = evidence.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(evidence)
    return result


def reproduce_artifact(
    workspace: Path,
    artifact_path: str,
    input_paths: List[str],
    command: List[str],
    audit_command: List[str],
    generator: str,
    working_directory: str = ".",
    timeout: int = 120,
) -> Dict[str, object]:
    """Run a generator twice in clean directories and copy only audited identical output."""
    workspace = Path(workspace).resolve()
    if not workspace.is_dir():
        raise ValueError("workspace must be an existing directory")
    if not artifact_path.strip() or not input_paths or not command or not audit_command or not generator.strip():
        raise ValueError("artifact, inputs, generator command, audit command, and generator are required")
    _inside(workspace, artifact_path)
    _inside(workspace, working_directory)
    normalized_inputs = [path.replace("\\", "/") for path in input_paths]
    input_evidence = []
    for relative in normalized_inputs:
        source = _inside(workspace, relative)
        input_evidence.append({"path": relative, **describe_path(source)})

    base: Dict[str, object] = {
        "schema_version": 1,
        "framework_version": FRAMEWORK_VERSION,
        "artifact_path": artifact_path.replace("\\", "/"),
        "generator": generator,
        "command": command,
        "audit_command": audit_command,
        "working_directory": working_directory.replace("\\", "/"),
        "inputs": input_evidence,
        "manual_edit_allowed": False,
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }

    generated: List[Tuple[Dict[str, object], Path]] = []
    audit_codes: List[int] = []
    with tempfile.TemporaryDirectory(prefix="auracode-artifact-") as temporary_root:
        temporary = Path(temporary_root)
        for run_number in (1, 2):
            run_root = temporary / f"run-{run_number}"
            run_root.mkdir()
            _prepare_run(workspace, run_root, normalized_inputs)
            cwd = _inside(run_root, working_directory)
            cwd.mkdir(parents=True, exist_ok=True)
            environment = _safe_environment(run_root)
            code, diagnostic = _run(command, cwd, environment, timeout)
            if code != 0:
                result = dict(base, status="FAIL", reason=f"generator command failed on run {run_number}: {diagnostic}")
                return _persist(workspace, result, artifact_path)
            output = _inside(run_root, artifact_path)
            if not output.exists():
                result = dict(base, status="FAIL", reason=f"generator did not create artifact on run {run_number}")
                return _persist(workspace, result, artifact_path)
            audit_code, audit_diagnostic = _run(audit_command, cwd, environment, timeout)
            audit_codes.append(audit_code)
            if audit_code != 0:
                result = dict(base, status="FAIL", reason=f"audit command failed on run {run_number}: {audit_diagnostic}")
                return _persist(workspace, result, artifact_path)
            generated.append((describe_path(output), output))

        first_description, first_path = generated[0]
        second_description, _ = generated[1]
        first_hash = str(first_description["sha256"])
        second_hash = str(second_description["sha256"])
        if first_description != second_description:
            result = dict(
                base,
                status="FAIL",
                reason="generated artifact is not reproducible across two clean runs",
                first_sha256=first_hash,
                reproduction_sha256=second_hash,
            )
            return _persist(workspace, result, artifact_path)

        destination = _inside(workspace, artifact_path)
        _copy_artifact(first_path, destination, str(first_description["kind"]))
        result = dict(
            base,
            status="PASS",
            reason="artifact was audited and reproduced identically in two clean runs",
            artifact_kind=first_description["kind"],
            bytes=first_description["bytes"],
            first_sha256=first_hash,
            reproduction_sha256=second_hash,
            audit_exit_codes=audit_codes,
        )
        if first_description["kind"] == "directory":
            result["files"] = first_description["files"]
        return _persist(workspace, result, artifact_path)


def reproduce_from_recipe(workspace: Path, recipe_path: str) -> Dict[str, object]:
    """Load a workspace-contained recipe and execute its reproduction contract."""
    workspace = Path(workspace).resolve()
    recipe_file = _inside(workspace, recipe_path)
    if not recipe_file.is_file():
        raise ValueError(f"artifact recipe is not a file: {recipe_path}")
    recipe = json.loads(recipe_file.read_text(encoding="utf-8"))
    if not isinstance(recipe, dict) or recipe.get("schema_version") != 1:
        raise ValueError("artifact recipe must be an object with schema_version 1")

    required_strings = ("artifact_path", "generator")
    for field in required_strings:
        if not isinstance(recipe.get(field), str) or not recipe[field].strip():
            raise ValueError(f"artifact recipe field must be a non-empty string: {field}")
    required_lists = ("input_paths", "command", "audit_command")
    for field in required_lists:
        value = recipe.get(field)
        if not isinstance(value, list) or not value or not all(
            isinstance(item, str) and item for item in value
        ):
            raise ValueError(f"artifact recipe field must be a non-empty string list: {field}")
    working_directory = recipe.get("working_directory", ".")
    timeout = recipe.get("timeout", 120)
    if not isinstance(working_directory, str) or not working_directory.strip():
        raise ValueError("artifact recipe working_directory must be a non-empty string")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
        raise ValueError("artifact recipe timeout must be a positive integer")

    return reproduce_artifact(
        workspace=workspace,
        artifact_path=recipe["artifact_path"],
        input_paths=recipe["input_paths"],
        command=recipe["command"],
        audit_command=recipe["audit_command"],
        generator=recipe["generator"],
        working_directory=working_directory,
        timeout=timeout,
    )
