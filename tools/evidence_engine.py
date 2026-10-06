"""Execution evidence v1: explicit scope, byte integrity, and fail-closed checks.

Digests detect changes against a retained record; they do not authenticate a producer.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from tools.version import FRAMEWORK_VERSION


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    """Project-specific deterministic JSON encoding, not a JCS implementation."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def current_commit(root: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                            capture_output=True, text=True, timeout=10, check=True)
    commit = result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
        raise ValueError("Invalid repository commit")
    return commit


def scope_hashes(root: Path, paths: List[str]) -> Dict[str, str]:
    """Hash explicit relative files; reject traversal and alternate path spellings."""
    root = root.resolve()
    if not paths or len(set(paths)) != len(paths):
        raise ValueError("Scope must contain distinct files")
    hashes: Dict[str, str] = {}
    for name in paths:
        relative = Path(name)
        if (relative.is_absolute() or ".." in relative.parts or
                relative.as_posix() != name or "\\" in name):
            raise ValueError("Scope paths must be canonical relative paths")
        target = (root / relative).resolve(strict=True)
        target.relative_to(root)
        if not target.is_file():
            raise ValueError("Scope entries must be files")
        hashes[name] = digest_bytes(target.read_bytes())
    return hashes


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def execute(root: Path, control: str, verification: str, paths: List[str],
            command: List[str], timeout: int = 60) -> Dict[str, Any]:
    """Run an explicitly authorized verifier command without shell expansion."""
    if not control.strip() or not verification.strip() or not command or timeout <= 0:
        raise ValueError("Control, verification, command, and positive timeout required")
    commit = current_commit(root)
    before = scope_hashes(root, paths)
    started = now()
    try:
        result = subprocess.run(command, cwd=root, capture_output=True,
                                timeout=timeout, check=False)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
        status = "PASS" if code == 0 else "FAIL"
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr = None, exc.stdout or b"", exc.stderr or b""
        status = "ERROR"
    except OSError as exc:
        code, stdout, stderr = None, b"", str(exc).encode("utf-8")
        status = "ERROR"
    finished = now()
    try:
        if scope_hashes(root, paths) != before or current_commit(root) != commit:
            status = "STALE"
    except (OSError, ValueError, subprocess.SubprocessError):
        status = "STALE"
    record: Dict[str, Any] = {
        "schema_version": "1", "evidence_id": "EVD-" + uuid.uuid4().hex,
        "run_id": "RUN-" + uuid.uuid4().hex,
        "control_id": control, "verification_id": verification,
        "commit": commit, "scope": before,
        "tool": "auracode-evidence", "tool_version": FRAMEWORK_VERSION,
        "command": command, "started_at": started, "finished_at": finished,
        "status": status, "returncode": code,
        "stdout_hex": stdout.hex(), "stderr_hex": stderr.hex(),
        "stdout_sha256": digest_bytes(stdout), "stderr_sha256": digest_bytes(stderr),
    }
    record["digest"] = digest_bytes(canonical_bytes(record))
    return record


def verify(record: Dict[str, Any], root: Path) -> Dict[str, str]:
    """Reject incomplete, changed, stale, and unsuccessful evidence."""
    required = {"schema_version", "evidence_id", "run_id", "control_id",
                "verification_id", "commit", "scope", "tool", "tool_version",
                "command", "started_at", "finished_at", "status", "returncode",
                "stdout_hex", "stderr_hex", "stdout_sha256", "stderr_sha256", "digest"}
    if not isinstance(record, dict) or set(record) != required:
        return {"status": "INCOMPLETE", "reason": "Unexpected or missing fields"}
    try:
        if (record["schema_version"] != "1" or record["tool"] != "auracode-evidence" or
                not isinstance(record["scope"], dict) or
                not isinstance(record["command"], list) or not record["command"] or
                any(not isinstance(item, str) or not item for item in record["command"])):
            raise ValueError("Invalid record shape")
        for field in required - {"scope", "command", "returncode"}:
            if not isinstance(record[field], str) or (not record[field] and field not in {"stdout_hex", "stderr_hex"}):
                raise ValueError("Invalid text field")
        if record["returncode"] is not None and type(record["returncode"]) is not int:
            raise ValueError("Invalid returncode")
        if (record["status"] not in {"PASS", "FAIL", "ERROR", "STALE"} or
                not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", record["commit"])):
            raise ValueError("Invalid execution status or commit")
        for value in [record["digest"], record["stdout_sha256"], record["stderr_sha256"], *record["scope"].values()]:
            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
                raise ValueError("Invalid SHA-256 field")
        start = datetime.fromisoformat(record["started_at"])
        finish = datetime.fromisoformat(record["finished_at"])
        if start.tzinfo is None or finish.tzinfo is None or finish < start:
            raise ValueError("Invalid execution timestamps")
        unsigned = {key: value for key, value in record.items() if key != "digest"}
        if digest_bytes(canonical_bytes(unsigned)) != record["digest"]:
            return {"status": "TAMPERED", "reason": "Record digest mismatch"}
        for stream in ("stdout", "stderr"):
            if digest_bytes(bytes.fromhex(record[stream + "_hex"])) != record[stream + "_sha256"]:
                return {"status": "TAMPERED", "reason": "Output digest mismatch"}
        if (current_commit(root) != record["commit"] or
                scope_hashes(root, list(record["scope"])) != record["scope"] or
                record["tool_version"] != FRAMEWORK_VERSION):
            return {"status": "STALE", "reason": "Commit, scope, or tool changed"}
        if record["status"] != "PASS" or record["returncode"] != 0:
            return {"status": "FAIL", "reason": "Execution did not pass"}
        return {"status": "PASS", "reason": "Recorded execution and explicit scope match"}
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        return {"status": "INVALID", "reason": "Malformed evidence or unavailable scope"}


def reject_duplicates(pairs: List[Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(prog="auracode evidence")
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("run")
    run.add_argument("--root", default=".")
    run.add_argument("--control", required=True)
    run.add_argument("--verification", required=True)
    run.add_argument("--scope", action="append", required=True)
    run.add_argument("--output", required=True)
    run.add_argument("--timeout", type=int, default=60)
    run.add_argument("command", nargs=argparse.REMAINDER)
    check = sub.add_parser("verify")
    check.add_argument("record")
    check.add_argument("--root", default=".")
    gate = sub.add_parser("gate")
    gate.add_argument("--policy", required=True)
    gate.add_argument("--bundle", required=True, help="JSON array of execution records")
    gate.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    try:
        if args.action == "run":
            command = args.command[1:] if args.command[:1] == ["--"] else args.command
            record = execute(Path(args.root), args.control, args.verification,
                             args.scope, command, args.timeout)
            with Path(args.output).open("x", encoding="utf-8") as file:
                json.dump(record, file, indent=2)
            result = verify(record, Path(args.root))
        elif args.action == "gate":
            from tools.evidence_policy import read_json, decide
            result = decide(read_json(Path(args.policy)), read_json(Path(args.bundle)), Path(args.root))
        else:
            record = json.loads(Path(args.record).read_text(encoding="utf-8"),
                                object_pairs_hook=reject_duplicates)
            result = verify(record, Path(args.root))
    except (OSError, ValueError, subprocess.SubprocessError):
        result = {"status": "INVALID", "reason": "Cannot create or read evidence"}
    print(json.dumps(result))
    return 0 if result["status"] == "PASS" else 1
