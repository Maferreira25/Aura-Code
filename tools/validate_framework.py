#!/usr/bin/env python3
"""Validate framework internal integrity using Python stdlib only."""
from pathlib import Path
import json
import sys
import re
import hashlib
from typing import Dict, List, Tuple, Any

ROOT = Path(__file__).resolve().parents[1]

# Shared exclusion rules for manifest verification
MANIFEST_EXCLUDE_DIRS = {
    ".git", "__pycache__", "graphify-out", "dist", "build", ".venv", ".pytest_cache",
    "auracode.egg-info", ".auracode", ".reversa", "framework_audit"
}
MANIFEST_EXCLUDE_EXTS = {".pyc", ".pyo", ".pyd"}
MANIFEST_EXCLUDE_FILES = {"MANIFEST.json", ".cursorrules", "AGENTS.md"}


def validate_framework(root_dir: Path = ROOT) -> Dict[str, Any]:
    """Execute complete internal integrity and governance checks.

    Returns a dictionary with success status, errors, warnings, and summary.
    """
    errors: List[str] = []
    warnings: List[str] = []

    def load(rel: str) -> dict:
        with open(root_dir / rel, encoding="utf-8") as f:
            return json.load(f)

    catalog = load("controls/catalog.json")
    sources = load("controls/source-registry.json")["sources"]
    fm = load("controls/failure-modes.json")["failure_modes"]
    cross = load("controls/standards-crosswalk.json")["crosswalk"]

    levels = catalog["assurance_levels"]
    rank = {x: i for i, x in enumerate(levels)}
    domains = catalog["domains"]
    controls = catalog["controls"]
    ids = [c["id"] for c in controls]
    idset = set(ids)

    if len(ids) != len(idset):
        errors.append("Duplicate control IDs detected.")

    required = [
        "id", "title", "domain", "min_level", "requirement", "applicability",
        "required_evidence", "verification", "blocking_conditions", "references"
    ]
    for c in controls:
        for field in required:
            if field not in c:
                errors.append(f"{c.get('id', '<?>')}: missing {field}")
        if c.get("domain") not in domains:
            errors.append(f"{c.get('id')}: invalid domain {c.get('domain')}")
        if c.get("min_level") not in levels:
            errors.append(f"{c.get('id')}: invalid min_level {c.get('min_level')}")
        if not re.match(r"^[A-Z]{3}-[0-9]{2}$", c.get("id", "")):
            errors.append(f"{c.get('id')}: invalid ID format")
        for field in ["required_evidence", "verification", "blocking_conditions", "references"]:
            if not c.get(field):
                errors.append(f"{c.get('id')}: empty {field}")
        for ref in c.get("references", []):
            if ref not in sources:
                errors.append(f"{c.get('id')}: unknown source {ref}")

    for sid, s in sources.items():
        if not str(s.get("url", "")).startswith("https://"):
            errors.append(f"{sid}: source URL is not HTTPS")
        if not s.get("status") or not s.get("type"):
            errors.append(f"{sid}: source status/type missing")

    # Failure modes must resolve and have >=1 control and source
    for f in fm:
        if not f.get("controls"):
            errors.append(f"{f.get('id')}: failure mode has no controls")
        if not f.get("evidence"):
            errors.append(f"{f.get('id')}: failure mode has no evidence")
        for cid in f.get("controls", []):
            if cid not in idset:
                errors.append(f"{f.get('id')}: unknown control {cid}")
        for sid in f.get("evidence", []):
            if sid not in sources:
                errors.append(f"{f.get('id')}: unknown evidence source {sid}")

    # Crosswalk
    for sid, ds in cross.items():
        if sid not in sources:
            errors.append(f"Crosswalk unknown source: {sid}")
        for d in ds:
            if d not in domains:
                errors.append(f"Crosswalk {sid}: unknown domain {d}")

    # Profile exactness + monotonicity
    prev = set()
    for level in levels:
        p = load(f"profiles/{level.lower()}.json")
        actual = set(p["included_controls"])
        expected = {c["id"] for c in controls if rank[c["min_level"]] <= rank[level]}
        if actual != expected:
            errors.append(f"{level}: profile differs from catalog. missing={sorted(expected-actual)} extra={sorted(actual-expected)}")
        if not prev.issubset(actual):
            errors.append(f"{level}: profile is not monotonic")
        prev = actual

    # Template and key repository files
    for rel in [
        "README.md", "README.pt-BR.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md",
        "docs/FRAMEWORK.md", "docs/VALIDATION.md", "templates/assessment.json",
        "schemas/control.schema.json", "schemas/assessment.schema.json",
        "schemas/contracts.schema.json", "schemas/evidence.schema.json",
        "MANIFEST.json",
    ]:
        if not (root_dir / rel).exists():
            errors.append(f"Missing repository file: {rel}")

    # Manifest integrity verification (REM-002, REM-021, REM-027)
    manifest_path = root_dir / "MANIFEST.json"
    if manifest_path.exists():
        try:
            manifest_data = load("MANIFEST.json")
            m_files = manifest_data.get("files", {})
            if not m_files:
                errors.append("MANIFEST.json contains empty files mapping")

            # 1. Manifest -> Disk verification
            for rel_path, meta in m_files.items():
                f_path = root_dir / rel_path
                if not f_path.exists():
                    errors.append(f"Manifest entry not found on disk: {rel_path}")
                    continue
                content = f_path.read_bytes()
                if len(content) != meta.get("bytes"):
                    errors.append(f"Manifest byte count mismatch for {rel_path}: expected {meta.get('bytes')}, got {len(content)}")
                calc_hash = hashlib.sha256(content).hexdigest()
                if calc_hash != meta.get("sha256"):
                    errors.append(f"Manifest SHA-256 mismatch for {rel_path}: expected {meta.get('sha256')}, got {calc_hash}")

            # 2. Disk -> Manifest bidirectional verification (REM-021)
            for f in root_dir.rglob("*"):
                if not f.is_file():
                    continue
                rel = f.relative_to(root_dir)
                parts = rel.parts
                if any(p in MANIFEST_EXCLUDE_DIRS or p.startswith("_auracode_") or p.startswith("_reversa_") for p in parts) or (parts and parts[0] in {".agents", ".reversa"}):
                    continue
                if f.suffix.lower() in MANIFEST_EXCLUDE_EXTS or f.name in MANIFEST_EXCLUDE_FILES:
                    continue
                rel_str = str(rel).replace("\\", "/")
                if rel_str not in m_files:
                    errors.append(f"Untracked file on disk missing from MANIFEST.json: {rel_str}")
        except Exception as exc:
            errors.append(f"Failed to verify MANIFEST.json: {exc}")

    # Schema and contract structural verification (REM-011)
    for s_rel in [
        "schemas/control.schema.json", "schemas/assessment.schema.json",
        "schemas/contracts.schema.json", "schemas/evidence.schema.json",
        "validation/schemas/result.schema.json", "validation/schemas/scenario.schema.json"
    ]:
        sp = root_dir / s_rel
        if sp.exists():
            try:
                s_data = json.loads(sp.read_text(encoding="utf-8"))
                if not isinstance(s_data, dict) or "$schema" not in s_data:
                    errors.append(f"{s_rel}: invalid schema object or missing $schema")
            except Exception as e:
                errors.append(f"{s_rel}: failed to parse JSON schema: {e}")

    # Contracts schema conformity
    contracts_file = root_dir / "contracts.json"
    if contracts_file.exists():
        c_data = load("contracts.json")
        for req_k in ["project", "version", "layers"]:
            if req_k not in c_data:
                errors.append(f"contracts.json missing required property: {req_k}")
        if not isinstance(c_data.get("layers"), dict) or len(c_data.get("layers", {})) == 0:
            errors.append("contracts.json: layers must be a non-empty mapping")

    # Template assessment conformity
    tmpl_file = root_dir / "templates/assessment.json"
    if tmpl_file.exists():
        t_data = load("templates/assessment.json")
        for req_k in ["framework_version", "assurance_level", "project", "assessor", "controls"]:
            if req_k not in t_data:
                errors.append(f"templates/assessment.json missing required property: {req_k}")

    # Evidence-reference coverage signal
    referenced = {r for c in controls for r in c.get("references", [])}
    unreferenced = {
        sid for sid in (set(sources) - referenced)
        if sources[sid].get("status") not in {"draft"}
        and sources[sid].get("type") not in {"tool-documentation"}
    }
    if unreferenced:
        warnings.append("Sources not directly referenced by controls: " + ", ".join(sorted(unreferenced)))

    # Dogfood SUP-06: external GitHub Actions in workflows must use an immutable 40-hex SHA.
    workflow_dir = root_dir / ".github" / "workflows"
    action_re = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.MULTILINE)
    sha_re = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
    if workflow_dir.exists():
        for wf in list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml")):
            body = wf.read_text(encoding="utf-8")
            for ref in action_re.findall(body):
                if ref.startswith("./"):
                    continue
                if "@" not in ref:
                    errors.append(f"{wf.relative_to(root_dir)}: action without immutable ref: {ref}")
                    continue
                action, version = ref.rsplit("@", 1)
                if not sha_re.fullmatch(version):
                    errors.append(f"{wf.relative_to(root_dir)}: external action not pinned to full SHA: {ref}")

    # Antigravity IDE adapter drift guard: current operational docs must not rely on historical mode labels.
    for rel in [
        "adapters/antigravity/README.md",
        "validation/ANTIGRAVITY-EXPERIMENT.md",
        "validation/P1-ANTIGRAVITY-IDE-STEP-BY-STEP.pt-BR.md",
    ]:
        fp = root_dir / rel
        if fp.exists():
            body = fp.read_text(encoding="utf-8")
            bad_lines = []
            for i, line in enumerate(body.splitlines(), 1):
                if ("Planning Mode" in line or "Fast Mode" in line) and not any(k in line.lower() for k in ["do not", "não", "histor", "lagging", "not use"]):
                    bad_lines.append(i)
            if bad_lines:
                errors.append(f"{rel}: obsolete Antigravity IDE mode terminology used operationally at lines {bad_lines}")

    # Current experiment result schema must record model/reasoning/surface metadata.
    rs_path = root_dir / "validation/schemas/result.schema.json"
    rs = load("validation/schemas/result.schema.json") if rs_path.exists() else None
    if rs:
        rprops = rs.get("properties", {})
        for fld in ["execution_surface", "model_family", "model_display_name", "reasoning_effort", "antigravity_version"]:
            if fld not in rprops:
                errors.append(f"validation result schema missing Antigravity/current-agent metadata field: {fld}")

    return {
        "success": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "framework": f"{catalog.get('framework', '')} {catalog.get('version', '')}",
            "controls_count": len(controls),
            "domains_count": len(domains),
            "sources_count": len(sources),
            "failure_modes_count": len(fm),
            "profiles": {level: len(load(f'profiles/{level.lower()}.json')['included_controls']) for level in levels}
        }
    }


def main() -> None:
    res = validate_framework()
    s = res["summary"]
    print(f"Framework: {s['framework']}")
    print(f"Controls: {s['controls_count']} across {s['domains_count']} domains")
    print(f"Sources: {s['sources_count']}")
    print(f"Failure modes: {s['failure_modes_count']}")
    for level, count in s["profiles"].items():
        print(f"{level}: {count} controls")

    if res["warnings"]:
        print("\nWarnings:")
        for w in res["warnings"]:
            print(" -", w)

    if not res["success"]:
        print("\nVALIDATION FAILED")
        for e in res["errors"]:
            print(" -", e)
        sys.exit(1)

    print("\nVALIDATION PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
