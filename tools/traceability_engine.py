#!/usr/bin/env python3
"""Aura Code Traceability Engine.

Builds and evaluates the chain Requirement -> Invariant -> Implementation ->
Test -> Evidence. The engine is fail-closed: missing mandatory links never
become PASS and critical gaps block progression.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set

from tools.assurance_result import build_result, progression_state
from tools.evidence_engine import verify_evidence_file


CRITICALITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def _nonempty_strings(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if isinstance(item, str) and item.strip()]


def _index_unique(items: Iterable[Mapping[str, Any]], key: str) -> Dict[str, Mapping[str, Any]]:
    index: Dict[str, Mapping[str, Any]] = {}
    duplicates: Set[str] = set()
    for item in items:
        identifier = item.get(key)
        if not isinstance(identifier, str) or not identifier:
            continue
        if identifier in index:
            duplicates.add(identifier)
        else:
            index[identifier] = item
    if duplicates:
        raise ValueError(f"Duplicate {key} values: {', '.join(sorted(duplicates))}")
    return index


def load_traceability_manifest(path: Path) -> Dict[str, Any]:
    """Load a traceability manifest without accepting malformed roots."""
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Traceability manifest not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Traceability manifest cannot be parsed: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Traceability manifest root must be an object.")
    if data.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported traceability schema version.")
    if not isinstance(data.get("requirements"), list) or not isinstance(data.get("invariants"), list):
        raise ValueError("Traceability manifest requires requirements and invariants arrays.")
    return data


def evaluate_traceability(
    manifest: Mapping[str, Any],
    workspace: Path,
    *,
    verify_evidence: bool = True,
) -> Dict[str, Any]:
    """Evaluate requirement/invariant traceability and produce canonical results."""
    workspace = workspace.resolve()
    requirements = manifest.get("requirements")
    invariants = manifest.get("invariants")

    if not isinstance(requirements, list) or not isinstance(invariants, list):
        return {
            "status": "ERROR",
            "progression": {"state": "BLOCKED", "blocked_by": [{"status": "ERROR", "reason": "Malformed traceability manifest."}]},
            "requirements": [],
            "invariants": [],
        }

    try:
        req_index = _index_unique(
            [item for item in requirements if isinstance(item, Mapping)],
            "requirement_id",
        )
        inv_index = _index_unique(
            [item for item in invariants if isinstance(item, Mapping)],
            "invariant_id",
        )
    except ValueError as exc:
        return {
            "status": "ERROR",
            "progression": {"state": "BLOCKED", "blocked_by": [{"status": "ERROR", "reason": str(exc)}]},
            "requirements": [],
            "invariants": [],
        }

    canonical_results: List[Dict[str, Any]] = []
    requirement_reports: List[Dict[str, Any]] = []
    invariant_reports: List[Dict[str, Any]] = []

    # Evaluate invariants first so requirement links can depend on their outcome.
    invariant_status: Dict[str, str] = {}
    for inv_id, inv in inv_index.items():
        criticality = str(inv.get("criticality", "")).upper()
        tests = _nonempty_strings(inv.get("tests"))
        checks = _nonempty_strings(inv.get("checks"))
        evidence_paths = _nonempty_strings(inv.get("evidence"))
        human_required = bool(inv.get("human_assurance_required", False))
        gaps: List[str] = []

        if criticality not in CRITICALITIES:
            gaps.append("invalid criticality")
        if not tests and not checks and not human_required:
            gaps.append("no verification mechanism")
        if human_required and not evidence_paths:
            gaps.append("human assurance required but no evidence recorded")
        if (tests or checks) and not evidence_paths:
            gaps.append("verification declared but no evidence linked")

        evidence_states: List[Dict[str, Any]] = []
        if verify_evidence:
            for item in evidence_paths:
                evidence_path = (workspace / item).resolve()
                try:
                    evidence_path.relative_to(workspace)
                except ValueError:
                    evidence_states.append({"path": item, "status": "INVALID", "reason": "Evidence path escapes workspace."})
                    continue
                verification = verify_evidence_file(evidence_path, workspace)
                evidence_states.append({"path": item, **verification})

        if any(item.get("status") in {"INVALID", "MISSING"} for item in evidence_states):
            status = "ERROR"
        elif any(item.get("status") == "STALE" for item in evidence_states):
            status = "STALE"
        elif gaps:
            status = "NOT_TESTED"
        elif evidence_paths and verify_evidence and any(item.get("status") != "VALID" for item in evidence_states):
            status = "INCONCLUSIVE"
        elif evidence_paths:
            status = "PASS"
        else:
            status = "NOT_TESTED"

        reason = (
            "Invariant is fully linked to current verification evidence."
            if status == "PASS"
            else "; ".join(gaps) or "Invariant evidence is missing, stale, invalid, or inconclusive."
        )

        result = build_result(
            check_id=f"invariant:{inv_id.lower()}",
            control_id="ARC-04",
            status=status,
            producer_tool="traceability_engine",
            producer_method="traceability_graph",
            workspace=str(workspace),
            reason=reason,
            severity="CRITICAL" if criticality == "CRITICAL" else "HIGH" if criticality == "HIGH" else "MEDIUM",
            evidence=evidence_paths,
            legacy=None,
        )
        canonical_results.append(result)
        invariant_status[inv_id] = status
        invariant_reports.append(
            {
                "invariant_id": inv_id,
                "criticality": criticality,
                "status": status,
                "gaps": gaps,
                "evidence_states": evidence_states,
            }
        )

    for req_id, req in req_index.items():
        criticality = str(req.get("criticality", "")).upper()
        source = req.get("source")
        criteria = _nonempty_strings(req.get("acceptance_criteria"))
        linked_invariants = _nonempty_strings(req.get("invariants"))
        implementation = _nonempty_strings(req.get("implementation"))
        tests = _nonempty_strings(req.get("tests"))
        evidence_paths = _nonempty_strings(req.get("evidence"))
        gaps: List[str] = []

        if criticality not in CRITICALITIES:
            gaps.append("invalid criticality")
        if not isinstance(source, Mapping) or not source.get("document") or not source.get("locator"):
            gaps.append("missing requirement source")
        elif source.get("approved") is False:
            gaps.append("requirement source not approved")
        if not criteria:
            gaps.append("no acceptance criteria")
        if not implementation:
            gaps.append("no implementation link")
        if not tests:
            gaps.append("no test link")
        if not evidence_paths:
            gaps.append("no evidence link")

        unknown_invariants = sorted(set(linked_invariants) - set(inv_index))
        if unknown_invariants:
            gaps.append("unknown invariant links: " + ", ".join(unknown_invariants))

        bad_invariants = [
            inv_id for inv_id in linked_invariants
            if invariant_status.get(inv_id) not in {None, "PASS"}
        ]

        evidence_states: List[Dict[str, Any]] = []
        if verify_evidence:
            for item in evidence_paths:
                evidence_path = (workspace / item).resolve()
                try:
                    evidence_path.relative_to(workspace)
                except ValueError:
                    evidence_states.append({"path": item, "status": "INVALID", "reason": "Evidence path escapes workspace."})
                    continue
                verification = verify_evidence_file(evidence_path, workspace)
                evidence_states.append({"path": item, **verification})

        if any(item.get("status") in {"INVALID", "MISSING"} for item in evidence_states):
            status = "ERROR"
        elif any(item.get("status") == "STALE" for item in evidence_states):
            status = "STALE"
        elif bad_invariants:
            status = "INCONCLUSIVE"
        elif gaps:
            status = "NOT_TESTED"
        elif evidence_paths and verify_evidence and any(item.get("status") != "VALID" for item in evidence_states):
            status = "INCONCLUSIVE"
        else:
            status = "PASS"

        reason = (
            "Requirement is traceable through implementation, tests and current evidence."
            if status == "PASS"
            else "; ".join(gaps)
            or ("linked invariant not in PASS state: " + ", ".join(bad_invariants))
            or "Requirement evidence is stale or inconclusive."
        )

        result = build_result(
            check_id=f"requirement:{req_id.lower()}",
            control_id="INT-02",
            status=status,
            producer_tool="traceability_engine",
            producer_method="traceability_graph",
            workspace=str(workspace),
            reason=reason,
            severity="CRITICAL" if criticality == "CRITICAL" else "HIGH" if criticality == "HIGH" else "MEDIUM",
            evidence=evidence_paths,
        )
        canonical_results.append(result)
        requirement_reports.append(
            {
                "requirement_id": req_id,
                "criticality": criticality,
                "status": status,
                "gaps": gaps,
                "blocked_by_invariants": bad_invariants,
                "evidence_states": evidence_states,
            }
        )

    progression = progression_state(canonical_results)
    status = "PASS" if progression["state"] == "READY" else "BLOCKED"

    return {
        "status": status,
        "progression": progression,
        "requirements": requirement_reports,
        "invariants": invariant_reports,
        "canonical_results": canonical_results,
        "summary": {
            "requirements_total": len(requirement_reports),
            "requirements_pass": sum(1 for item in requirement_reports if item["status"] == "PASS"),
            "invariants_total": len(invariant_reports),
            "invariants_pass": sum(1 for item in invariant_reports if item["status"] == "PASS"),
        },
    }


def evaluate_traceability_file(
    manifest_path: Path,
    workspace: Path,
    *,
    verify_evidence: bool = True,
) -> Dict[str, Any]:
    """Load and evaluate a traceability manifest."""
    try:
        manifest = load_traceability_manifest(manifest_path)
    except (OSError, ValueError) as exc:
        return {
            "status": "ERROR",
            "progression": {"state": "BLOCKED", "blocked_by": [{"status": "ERROR", "reason": str(exc)}]},
            "requirements": [],
            "invariants": [],
            "canonical_results": [],
        }
    return evaluate_traceability(manifest, workspace, verify_evidence=verify_evidence)
