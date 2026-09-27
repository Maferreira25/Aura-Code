#!/usr/bin/env python3
"""Temporal evidence for scope-bound AuraCode build iterations."""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional

from tools.check_surgical_diff import is_path_in_scope, is_test_file
from tools.generated_artifact import describe_path
from tools.version import FRAMEWORK_VERSION


IGNORED_PARTS = {".git", ".auracode", ".pytest_cache", "__pycache__", "node_modules"}
IGNORED_PREFIXES = ("_auracode_forward/", "graphify-out/")
IGNORED_TRANSIENT_ROOTS = {"build", "dist"}
MAX_TEXT_BYTES = 1_000_000
ITERATION_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _ignored(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/")
    parts = normalized.split("/")
    transient_root = parts[0] in IGNORED_TRANSIENT_ROOTS or parts[0].endswith(".egg-info")
    return (
        transient_root
        or any(part in IGNORED_PARTS for part in parts)
        or normalized.startswith(IGNORED_PREFIXES)
    )


def _inventory(root: Path) -> Dict[str, Dict[str, object]]:
    inventory: Dict[str, Dict[str, object]] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if _ignored(relative):
            continue
        content = path.read_bytes()
        inventory[relative] = {
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
        }
    return inventory


def _without_ignored(inventory: Dict[str, Dict[str, object]]) -> Dict[str, Dict[str, object]]:
    """Filter legacy inventories with the same rules used for new captures."""
    return {path: metadata for path, metadata in inventory.items() if not _ignored(path)}


def _line_hashes(path: Path) -> Optional[List[str]]:
    if not path.is_file() or path.stat().st_size > MAX_TEXT_BYTES:
        return None
    content = path.read_bytes()
    if b"\x00" in content:
        return None
    text = content.decode("utf-8", errors="strict")
    return [hashlib.sha256(line.encode("utf-8")).hexdigest() for line in text.splitlines()]


def _record_path(root: Path, iteration_id: str) -> Path:
    return root / ".auracode" / "iterations" / f"{iteration_id}.json"


def _load_record(root: Path, iteration_id: str) -> Dict[str, object]:
    source = _record_path(root, iteration_id)
    if not source.is_file():
        raise ValueError(f"iteration does not exist: {iteration_id}")
    record = json.loads(source.read_text(encoding="utf-8"))
    recorded_seal = record.pop("manifest_sha256", None)
    if recorded_seal != _json_hash(record):
        raise ValueError("iteration manifest integrity check failed")
    return record


def _load_iteration_evidence(root: Path, relative_path: str) -> Dict[str, object]:
    evidence_root = (root / ".auracode" / "evidence" / "iterations").resolve()
    source = (root / relative_path).resolve()
    try:
        source.relative_to(evidence_root)
    except ValueError as exc:
        raise ValueError("sealed iteration evidence is outside the evidence directory") from exc
    if not source.is_file():
        raise ValueError("sealed iteration evidence is missing")
    evidence = json.loads(source.read_text(encoding="utf-8"))
    recorded_seal = evidence.get("evidence_sha256")
    seal_body = {
        key: value for key, value in evidence.items() if key not in {"evidence_sha256", "evidence_path"}
    }
    if recorded_seal != _json_hash(seal_body):
        raise ValueError("sealed iteration evidence integrity check failed")
    return evidence


def _sealed_result(root: Path, record: Dict[str, object]) -> Dict[str, object]:
    relative_path = str(record.get("sealed_evidence_path", ""))
    evidence = _load_iteration_evidence(root, relative_path)
    if (
        evidence.get("iteration_id") != record.get("iteration_id")
        or evidence.get("status") != "PASS"
        or evidence.get("evidence_sha256") != record.get("sealed_evidence_sha256")
    ):
        raise ValueError("sealed iteration evidence does not match the iteration record")
    return {
        "success": True,
        "status": "PASS",
        "iteration_status": "SEALED",
        "iteration_id": record["iteration_id"],
        "requirement": record["requirement"],
        "verification_mode": "sealed_historical_evidence",
        "current_workspace_evaluated": False,
        "sealed_at": record["sealed_at"],
        "sealed_evidence_sha256": record["sealed_evidence_sha256"],
        "sealed_evidence_path": str((root / relative_path).resolve()),
        "sealed_verified_at": evidence["verified_at"],
    }


def begin_iteration(
    root: Path,
    iteration_id: str,
    requirement: str,
    scope: List[str],
    allow_tests: bool = False,
    max_lines: int = 500,
    generated_artifacts: Optional[List[str]] = None,
) -> Dict[str, object]:
    """Capture a hash-only baseline before an authorized iteration starts."""
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError("workspace root must be an existing directory")
    if not ITERATION_ID.fullmatch(iteration_id):
        raise ValueError("iteration id must use lowercase letters, numbers, dots, dashes, or underscores")
    if not requirement.strip():
        raise ValueError("requirement is required")
    normalized_scope = [item.strip().replace("\\", "/") for item in scope if item.strip()]
    if not normalized_scope:
        raise ValueError("at least one scope pattern is required")
    if max_lines < 1 or max_lines > 500:
        raise ValueError("max_lines must be between 1 and the invariant limit of 500")
    normalized_generated = sorted(
        {item.strip().replace("\\", "/") for item in (generated_artifacts or []) if item.strip()}
    )
    for relative in normalized_generated:
        if not (
            is_path_in_scope(relative, normalized_scope)
            or is_path_in_scope(f"{relative}/__artifact__", normalized_scope)
        ):
            raise ValueError(f"generated artifact is outside iteration scope: {relative}")

    destination = _record_path(root, iteration_id)
    if destination.exists():
        raise ValueError(f"iteration already exists: {iteration_id}")

    inventory = _inventory(root)
    scoped_lines: Dict[str, Optional[List[str]]] = {}
    for relative in inventory:
        if is_path_in_scope(relative, normalized_scope):
            scoped_lines[relative] = _line_hashes(root / relative)

    record: Dict[str, object] = {
        "schema_version": 1,
        "framework_version": FRAMEWORK_VERSION,
        "iteration_id": iteration_id,
        "requirement": requirement.strip(),
        "scope": normalized_scope,
        "allow_tests": allow_tests,
        "max_lines": max_lines,
        "generated_artifacts": normalized_generated,
        "status": "OPEN",
        "created_at": _utc_now(),
        "baseline_inventory": inventory,
        "scoped_line_hashes": scoped_lines,
        "baseline_sha256": _json_hash(inventory),
    }
    record["manifest_sha256"] = _json_hash(record)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(destination)
    return {
        "status": "OPEN",
        "iteration_id": iteration_id,
        "requirement": requirement.strip(),
        "scope": normalized_scope,
        "generated_artifacts": normalized_generated,
        "baseline_sha256": record["baseline_sha256"],
        "record": str(destination),
    }


def _valid_artifact_evidence(root: Path, artifact_path: str) -> Optional[Dict[str, str]]:
    artifact = (root / artifact_path).resolve()
    try:
        artifact.relative_to(root)
        description = describe_path(artifact)
    except ValueError:
        return None
    evidence_dir = root / ".auracode" / "evidence" / "artifacts"
    for evidence_path in sorted(evidence_dir.glob("*.json"), reverse=True):
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            sealed = evidence.get("evidence_sha256")
            seal_body = {key: value for key, value in evidence.items() if key not in {"evidence_sha256", "evidence_path"}}
            if sealed != _json_hash(seal_body):
                continue
            if (
                evidence.get("status") != "PASS"
                or evidence.get("artifact_path") != artifact_path
                or evidence.get("manual_edit_allowed") is not False
                or evidence.get("artifact_kind", "file") != description["kind"]
                or evidence.get("bytes") != description["bytes"]
                or evidence.get("first_sha256") != description["sha256"]
                or evidence.get("reproduction_sha256") != description["sha256"]
                or (description["kind"] == "directory" and evidence.get("files") != description["files"])
            ):
                continue
            inputs_valid = True
            for item in evidence.get("inputs", []):
                input_path = (root / item["path"]).resolve()
                try:
                    input_path.relative_to(root)
                    input_description = describe_path(input_path)
                except ValueError:
                    inputs_valid = False
                    break
                expected_kind = item.get("kind", "file")
                if (
                    expected_kind != input_description["kind"]
                    or item.get("bytes") != input_description["bytes"]
                    or item.get("sha256") != input_description["sha256"]
                    or (expected_kind == "directory" and item.get("files") != input_description["files"])
                ):
                    inputs_valid = False
                    break
            if inputs_valid and evidence.get("inputs"):
                return {"evidence_path": str(evidence_path), "evidence_sha256": str(sealed)}
        except (KeyError, OSError, UnicodeError, json.JSONDecodeError, TypeError):
            continue
    return None


def _generated_owner(path: str, generated: set[str]) -> Optional[str]:
    matches = [root for root in generated if path == root or path.startswith(f"{root}/")]
    return max(matches, key=len) if matches else None


def verify_iteration(root: Path, iteration_id: str) -> Dict[str, object]:
    """Compare the workspace with the sealed baseline and enforce iteration invariants."""
    root = Path(root).resolve()
    record = _load_record(root, iteration_id)
    if record.get("status") == "SEALED":
        return _sealed_result(root, record)
    if record.get("status") != "OPEN":
        raise ValueError("iteration status must be OPEN or SEALED")

    baseline = _without_ignored(record["baseline_inventory"])
    current = _inventory(root)
    changed = sorted(
        path for path in set(baseline) | set(current) if baseline.get(path) != current.get(path)
    )
    scope = record["scope"]
    out_of_scope = [path for path in changed if not is_path_in_scope(path, scope)]
    selected = [path for path in changed if is_path_in_scope(path, scope)]
    violations: List[Dict[str, str]] = []
    generated = set(record.get("generated_artifacts", []))
    generated_evidence: Dict[str, Dict[str, str]] = {}
    checked_generated: set[str] = set()
    added = 0
    deleted = 0

    for path in out_of_scope:
        violations.append({"rule": "out_of_scope_change", "file": path})
    for path in selected:
        if is_test_file(path) and not record["allow_tests"]:
            violations.append({"rule": "unauthorized_test_tampering", "file": path})
        generated_root = _generated_owner(path, generated)
        if generated_root:
            if generated_root not in checked_generated:
                checked_generated.add(generated_root)
                evidence = _valid_artifact_evidence(root, generated_root)
                if evidence is None:
                    violations.append({"rule": "generated_artifact_evidence_missing", "file": generated_root})
                else:
                    generated_evidence[generated_root] = evidence
            continue
        old_lines = record["scoped_line_hashes"].get(path, [])
        new_lines = _line_hashes(root / path) if (root / path).is_file() else []
        if old_lines is None or new_lines is None:
            violations.append({"rule": "unmeasurable_file_change", "file": path})
            continue
        for tag, old_start, old_end, new_start, new_end in SequenceMatcher(
            None, old_lines, new_lines, autojunk=False
        ).get_opcodes():
            if tag in {"replace", "delete"}:
                deleted += old_end - old_start
            if tag in {"replace", "insert"}:
                added += new_end - new_start

    if not changed and not record.get("integrations"):
        violations.append({"rule": "no_iteration_changes", "file": "*"})
    if added + deleted > record["max_lines"]:
        violations.append({"rule": "excessive_diff_churn", "file": "*"})

    result: Dict[str, object] = {
        "success": not violations,
        "status": "PASS" if not violations else "FAIL",
        "iteration_id": iteration_id,
        "requirement": record["requirement"],
        "scope": scope,
        "baseline_sha256": record["baseline_sha256"],
        "changed_files": selected,
        "out_of_scope_files": out_of_scope,
        "total_lines_added": added,
        "total_lines_deleted": deleted,
        "max_lines": record["max_lines"],
        "generated_artifact_evidence": generated_evidence,
        "integrations": record.get("integrations", []),
        "violations": violations,
        "verified_at": _utc_now(),
    }
    result["evidence_sha256"] = _json_hash(result)
    evidence_dir = root / ".auracode" / "evidence" / "iterations"
    evidence_path = evidence_dir / f"{iteration_id}-{result['evidence_sha256']}.json"
    result["evidence_path"] = str(evidence_path)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    temporary = evidence_path.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(evidence_path)
    return result


def seal_iteration(root: Path, iteration_id: str) -> Dict[str, object]:
    """Close an iteration around an immutable historical PASS evidence."""
    root = Path(root).resolve()
    record = _load_record(root, iteration_id)
    if record.get("status") != "OPEN":
        raise ValueError("only an open iteration can be sealed")

    evidence_dir = root / ".auracode" / "evidence" / "iterations"
    candidates: List[Dict[str, object]] = []
    for source in evidence_dir.glob(f"{iteration_id}-*.json"):
        relative = source.relative_to(root).as_posix()
        try:
            evidence = _load_iteration_evidence(root, relative)
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
            continue
        if evidence.get("iteration_id") == iteration_id and evidence.get("status") == "PASS":
            evidence["_relative_path"] = relative
            candidates.append(evidence)
    if not candidates:
        raise ValueError("iteration has no valid PASS evidence to seal")

    selected = max(candidates, key=lambda item: str(item.get("verified_at", "")))
    record["status"] = "SEALED"
    record["sealed_at"] = _utc_now()
    record["sealed_evidence_sha256"] = selected["evidence_sha256"]
    record["sealed_evidence_path"] = selected["_relative_path"]
    record["manifest_sha256"] = _json_hash(record)
    destination = _record_path(root, iteration_id)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(destination)
    return {
        "success": True,
        "status": "SEALED",
        "iteration_id": iteration_id,
        "sealed_at": record["sealed_at"],
        "sealed_evidence_sha256": record["sealed_evidence_sha256"],
        "sealed_evidence_path": str((root / str(record["sealed_evidence_path"])).resolve()),
        "current_workspace_evaluated": False,
    }


def integrate_iteration(root: Path, parent_id: str, child_id: str) -> Dict[str, object]:
    """Revalidate a corrective child and incorporate only its certified paths into a parent baseline."""
    root = Path(root).resolve()
    if parent_id == child_id:
        raise ValueError("parent and child iterations must differ")
    parent = _load_record(root, parent_id)
    child = _load_record(root, child_id)
    if parent.get("status") != "OPEN" or child.get("status") != "OPEN":
        raise ValueError("only open iterations can be integrated")
    if str(child.get("created_at", "")) < str(parent.get("created_at", "")):
        raise ValueError("child iteration must have been opened after its parent")
    if any(item.get("child_iteration") == child_id for item in parent.get("integrations", [])):
        raise ValueError(f"child iteration is already integrated: {child_id}")

    current = _inventory(root)
    baseline = _without_ignored(child["baseline_inventory"])
    changed = sorted(path for path in set(baseline) | set(current) if baseline.get(path) != current.get(path))
    out_of_scope = [path for path in changed if not is_path_in_scope(path, child["scope"])]
    selected = [path for path in changed if is_path_in_scope(path, child["scope"])]
    violations: List[Dict[str, str]] = []
    generated = set(child.get("generated_artifacts", []))
    checked_generated: set[str] = set()
    generated_evidence: Dict[str, Dict[str, str]] = {}
    added = 0
    deleted = 0
    for path in out_of_scope:
        violations.append({"rule": "out_of_scope_change", "file": path})
    for path in selected:
        if is_test_file(path) and not child["allow_tests"]:
            violations.append({"rule": "unauthorized_test_tampering", "file": path})
        generated_root = _generated_owner(path, generated)
        if generated_root:
            if generated_root not in checked_generated:
                checked_generated.add(generated_root)
                evidence = _valid_artifact_evidence(root, generated_root)
                if evidence is None:
                    violations.append({"rule": "generated_artifact_evidence_missing", "file": generated_root})
                else:
                    generated_evidence[generated_root] = evidence
            continue
        old_lines = child["scoped_line_hashes"].get(path, [])
        new_lines = _line_hashes(root / path) if (root / path).is_file() else []
        if old_lines is None or new_lines is None:
            violations.append({"rule": "unmeasurable_file_change", "file": path})
            continue
        for tag, old_start, old_end, new_start, new_end in SequenceMatcher(
            None, old_lines, new_lines, autojunk=False
        ).get_opcodes():
            if tag in {"replace", "delete"}:
                deleted += old_end - old_start
            if tag in {"replace", "insert"}:
                added += new_end - new_start
    if not selected:
        violations.append({"rule": "no_iteration_changes", "file": "*"})
    if added + deleted > child["max_lines"]:
        violations.append({"rule": "excessive_diff_churn", "file": "*"})
    if violations:
        raise ValueError(f"child iteration cannot be integrated: {json.dumps(violations)}")

    previous_baseline = str(parent["baseline_sha256"])
    for path in selected:
        if path in current:
            parent["baseline_inventory"][path] = current[path]
        else:
            parent["baseline_inventory"].pop(path, None)
        parent["scoped_line_hashes"][path] = _line_hashes(root / path) if (root / path).is_file() else []
    parent["baseline_inventory"] = _without_ignored(parent["baseline_inventory"])
    parent["scoped_line_hashes"] = {
        path: hashes for path, hashes in parent["scoped_line_hashes"].items() if not _ignored(path)
    }
    parent.setdefault("initial_baseline_sha256", previous_baseline)
    parent["baseline_sha256"] = _json_hash(parent["baseline_inventory"])
    integration: Dict[str, object] = {
        "status": "PASS",
        "parent_iteration": parent_id,
        "child_iteration": child_id,
        "child_requirement": child["requirement"],
        "changed_files": selected,
        "changed_file_inventory": {path: current.get(path) for path in selected},
        "total_lines_added": added,
        "total_lines_deleted": deleted,
        "generated_artifact_evidence": generated_evidence,
        "previous_parent_baseline_sha256": previous_baseline,
        "updated_parent_baseline_sha256": parent["baseline_sha256"],
        "integrated_at": _utc_now(),
    }
    integration["evidence_sha256"] = _json_hash(integration)
    evidence_dir = root / ".auracode" / "evidence" / "integrations"
    evidence_path = evidence_dir / f"{parent_id}--{child_id}-{integration['evidence_sha256']}.json"
    integration["evidence_path"] = str(evidence_path)
    parent.setdefault("integrations", []).append(
        {
            "child_iteration": child_id,
            "evidence_sha256": integration["evidence_sha256"],
            "evidence_path": str(evidence_path),
        }
    )
    parent["manifest_sha256"] = _json_hash(parent)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(integration, indent=2, ensure_ascii=False), encoding="utf-8")
    destination = _record_path(root, parent_id)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(parent, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(destination)
    return integration


def main() -> None:
    parser = argparse.ArgumentParser(description="Open or verify a hash-baselined AuraCode iteration.")
    actions = parser.add_subparsers(dest="action", required=True)
    begin = actions.add_parser("begin")
    begin.add_argument("target", nargs="?", default=".")
    begin.add_argument("--id", required=True)
    begin.add_argument("--requirement", required=True)
    begin.add_argument("--scope", required=True)
    begin.add_argument("--allow-tests", action="store_true")
    begin.add_argument("--max-lines", type=int, default=500)
    begin.add_argument("--generated-artifact", action="append", default=[])
    begin.add_argument("--json", action="store_true")
    verify = actions.add_parser("verify")
    verify.add_argument("target", nargs="?", default=".")
    verify.add_argument("--id", required=True)
    verify.add_argument("--json", action="store_true")
    integrate = actions.add_parser("integrate")
    integrate.add_argument("target", nargs="?", default=".")
    integrate.add_argument("--id", required=True)
    integrate.add_argument("--child", required=True)
    integrate.add_argument("--json", action="store_true")
    seal = actions.add_parser("seal")
    seal.add_argument("target", nargs="?", default=".")
    seal.add_argument("--id", required=True)
    seal.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "begin":
            result = begin_iteration(
                Path(args.target), args.id, args.requirement,
                [item.strip() for item in args.scope.split(",") if item.strip()],
                args.allow_tests, args.max_lines,
                args.generated_artifact,
            )
        elif args.action == "verify":
            result = verify_iteration(Path(args.target), args.id)
        elif args.action == "integrate":
            result = integrate_iteration(Path(args.target), args.id, args.child)
        else:
            result = seal_iteration(Path(args.target), args.id)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False))
        sys.exit(2)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("status") in {"OPEN", "PASS", "SEALED"} else 1)


if __name__ == "__main__":
    main()
