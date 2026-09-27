#!/usr/bin/env python3
"""Build, verify, and safely install the official AuraCode skill bundle."""

import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from tools.version import FRAMEWORK_VERSION


ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / "auracode" / "skill_bundle.json"
CONTRACTS_PATH = ROOT / "auracode" / "skill_contracts.json"
SKILL_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_MANIFEST_FIELDS: Set[str] = {
    "id",
    "version",
    "description",
    "core_compatibility",
    "inputs",
    "outputs",
    "permissions",
    "tools",
    "files",
    "guarantees",
    "failure_points",
    "origin",
}


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _read_json(path: Path) -> Dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return data


def _frontmatter(skill_text: str) -> Tuple[str, str]:
    lines = skill_text.splitlines()
    if len(lines) < 4 or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        closing = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("SKILL.md frontmatter is not closed") from exc
    fields: Dict[str, str] = {}
    for line in lines[1:closing]:
        if ":" not in line:
            raise ValueError(f"Invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    if set(fields) != {"name", "description"}:
        raise ValueError("SKILL.md frontmatter must contain only name and description")
    return fields["name"], fields["description"]


def _version_key(value: str) -> Tuple[int, int, int, int]:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:\.dev(\d+))?", value)
    if not match:
        raise ValueError(f"Unsupported version format: {value}")
    major, minor, patch, dev = match.groups()
    release_rank = int(dev) - 1_000_000 if dev is not None else 0
    return int(major), int(minor), int(patch), release_rank


def build_skill_bundle(
    source_skills_dir: Path,
    destination: Path = BUNDLE_PATH,
    contracts_path: Path = CONTRACTS_PATH,
) -> Dict[str, object]:
    """Create a deterministic bundle from checked-in SKILL.md files and contracts."""
    contracts = _read_json(contracts_path)
    framework_version = FRAMEWORK_VERSION
    skill_version = contracts.get("skill_version")
    compatibility = contracts.get("core_compatibility")
    skill_contracts = contracts.get("skills")
    if not isinstance(skill_version, str) or not isinstance(compatibility, dict):
        raise ValueError("Skill contract header is incomplete")
    if not isinstance(skill_contracts, list):
        raise ValueError("Skill contracts must be a list")

    bundled: List[Dict[str, object]] = []
    seen: Set[str] = set()
    for raw_contract in skill_contracts:
        if not isinstance(raw_contract, dict):
            raise ValueError("Each skill contract must be an object")
        skill_id = raw_contract.get("id")
        if not isinstance(skill_id, str) or not SKILL_ID_PATTERN.fullmatch(skill_id):
            raise ValueError(f"Invalid skill id: {skill_id}")
        if skill_id in seen:
            raise ValueError(f"Duplicate skill id: {skill_id}")
        seen.add(skill_id)
        skill_path = source_skills_dir / skill_id / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        declared_name, description_pt = _frontmatter(content)
        if declared_name != skill_id:
            raise ValueError(f"Skill folder/name mismatch: {skill_id} != {declared_name}")
        encoded = content.encode("utf-8")
        description_en = raw_contract.get("description_en")
        if not isinstance(description_en, str) or not description_en.strip():
            raise ValueError(f"Missing English description for {skill_id}")
        manifest: Dict[str, object] = {
            "id": skill_id,
            "version": skill_version,
            "description": {"pt": description_pt, "en": description_en},
            "core_compatibility": compatibility,
            "inputs": raw_contract.get("inputs", []),
            "outputs": raw_contract.get("outputs", []),
            "permissions": raw_contract.get("permissions", []),
            "tools": raw_contract.get("tools", []),
            "files": [{"path": "SKILL.md", "sha256": _sha256(encoded), "bytes": len(encoded)}],
            "guarantees": raw_contract.get("guarantees", []),
            "failure_points": raw_contract.get("failure_points", []),
            "origin": "official:auracode",
        }
        bundled.append({"manifest": manifest, "files": {"SKILL.md": content}})

    disk_ids = {path.name for path in source_skills_dir.iterdir() if path.is_dir()}
    if disk_ids != seen:
        raise ValueError(
            f"Skill catalog/source mismatch; missing contracts={sorted(disk_ids - seen)}, "
            f"missing sources={sorted(seen - disk_ids)}"
        )
    bundle: Dict[str, object] = {
        "schema_version": contracts.get("schema_version", 1),
        "framework_version": framework_version,
        "skills": sorted(bundled, key=lambda item: str(item["manifest"]["id"])),
    }
    destination.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return bundle


def load_skill_bundle(path: Path = BUNDLE_PATH) -> Dict[str, object]:
    """Load the bundle carried by the installed Python distribution."""
    return _read_json(path)


def verify_skill_bundle(
    bundle_path: Path = BUNDLE_PATH,
    source_skills_dir: Optional[Path] = None,
) -> Dict[str, object]:
    """Verify contract completeness, hashes, compatibility, and optional source parity."""
    findings: List[str] = []
    try:
        bundle = load_skill_bundle(bundle_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"status": "ERROR", "verified_skills": 0, "findings": [str(exc)]}

    framework_version = FRAMEWORK_VERSION
    if bundle.get("framework_version") != framework_version:
        findings.append("Bundle framework version does not match the installed core")
    skills = bundle.get("skills")
    if not isinstance(skills, list) or not skills:
        findings.append("Bundle has no skills")
        skills = []
    seen: Set[str] = set()
    verified = 0
    for item in skills:
        if not isinstance(item, dict):
            findings.append("Bundle skill entry is not an object")
            continue
        manifest = item.get("manifest")
        files = item.get("files")
        if not isinstance(manifest, dict) or not isinstance(files, dict):
            findings.append("Bundle skill entry lacks manifest or files")
            continue
        skill_id = manifest.get("id")
        if not isinstance(skill_id, str) or not SKILL_ID_PATTERN.fullmatch(skill_id):
            findings.append(f"Invalid skill id: {skill_id}")
            continue
        if skill_id in seen:
            findings.append(f"Duplicate skill id: {skill_id}")
            continue
        seen.add(skill_id)
        missing = REQUIRED_MANIFEST_FIELDS - set(manifest)
        if missing:
            findings.append(f"{skill_id}: missing manifest fields {sorted(missing)}")
            continue
        compatibility = manifest.get("core_compatibility")
        if not isinstance(compatibility, dict):
            findings.append(f"{skill_id}: invalid core compatibility")
            continue
        minimum = compatibility.get("minimum")
        maximum = compatibility.get("maximum_exclusive")
        try:
            compatible = (
                isinstance(minimum, str)
                and isinstance(maximum, str)
                and _version_key(minimum) <= _version_key(framework_version) < _version_key(maximum)
            )
        except ValueError as exc:
            findings.append(f"{skill_id}: {exc}")
            continue
        if not compatible:
            findings.append(f"{skill_id}: incompatible with core {framework_version}")
            continue
        file_contracts = manifest.get("files")
        content = files.get("SKILL.md")
        if not isinstance(file_contracts, list) or len(file_contracts) != 1:
            findings.append(f"{skill_id}: invalid file contract")
            continue
        file_contract = file_contracts[0]
        if not isinstance(file_contract, dict) or not isinstance(content, str):
            findings.append(f"{skill_id}: SKILL.md is missing")
            continue
        encoded = content.encode("utf-8")
        if file_contract.get("sha256") != _sha256(encoded) or file_contract.get("bytes") != len(encoded):
            findings.append(f"{skill_id}: SKILL.md hash or byte count differs")
            continue
        try:
            declared_name, _ = _frontmatter(content)
        except ValueError as exc:
            findings.append(f"{skill_id}: {exc}")
            continue
        if declared_name != skill_id:
            findings.append(f"{skill_id}: frontmatter name differs")
            continue
        if source_skills_dir is not None:
            source_path = source_skills_dir / skill_id / "SKILL.md"
            try:
                source_content = source_path.read_text(encoding="utf-8")
            except OSError:
                findings.append(f"{skill_id}: source SKILL.md is missing")
                continue
            if source_content != content:
                findings.append(f"{skill_id}: bundled content differs from source")
                continue
        verified += 1
    return {
        "status": "PASS" if not findings else "FAIL",
        "verified_skills": verified,
        "total_skills": len(skills),
        "findings": findings,
    }


def install_bundled_skills(target_root: Path) -> Dict[str, object]:
    """Materialize bundled skills without overwriting divergent user-owned files."""
    verification = verify_skill_bundle()
    if verification["status"] != "PASS":
        return {"status": "ERROR", "installed": [], "skipped": [], "conflicts": [], "verification": verification}
    bundle = load_skill_bundle()
    skills = bundle["skills"]
    if not isinstance(skills, list):
        return {"status": "ERROR", "installed": [], "skipped": [], "conflicts": [], "verification": verification}
    install_root = Path(target_root).resolve() / ".agents" / "skills"
    conflicts: List[str] = []
    planned: List[Tuple[Path, str, str]] = []
    skipped: List[str] = []
    for item in skills:
        manifest = item["manifest"]
        files = item["files"]
        skill_id = manifest["id"]
        content = files["SKILL.md"]
        destination = install_root / skill_id / "SKILL.md"
        relative = f"{skill_id}/SKILL.md"
        if destination.exists():
            if destination.read_text(encoding="utf-8") == content:
                skipped.append(relative)
            else:
                conflicts.append(relative)
        else:
            planned.append((destination, content, relative))
    if conflicts:
        return {"status": "FAIL", "installed": [], "skipped": skipped, "conflicts": conflicts}
    installed: List[str] = []
    for destination, content, relative in planned:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name("SKILL.md.auracode-tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(destination)
        installed.append(relative)
    return {"status": "PASS", "installed": installed, "skipped": skipped, "conflicts": []}


def main() -> None:
    """Regenerate the packaged bundle from the development skill sources."""
    bundle = build_skill_bundle(ROOT / ".agents" / "skills")
    skills = bundle.get("skills", [])
    print(f"AuraCode skill bundle updated: {len(skills)} skills")


if __name__ == "__main__":
    main()
