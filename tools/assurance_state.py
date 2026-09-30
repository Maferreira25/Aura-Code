#!/usr/bin/env python3
"""Persistent fail-closed assurance state and gate engine for AuraCode."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
VALID_LEVELS = ("AL1", "AL2", "AL3", "AL4")
VALID_STATUSES = {"PASS", "FAIL", "UNKNOWN", "NOT_APPLICABLE", "WAIVED"}
LEGACY_STATUS_MAP = {"NA": "NOT_APPLICABLE", "NOT_ASSESSED": "UNKNOWN"}
VALID_ACTOR_KINDS = {"AI_AGENT", "AI_MODEL", "HUMAN", "DETERMINISTIC_TOOL", "SERVICE"}
VALID_ROLES = {"implementer", "verifier", "auditor", "remediator", "revalidator", "approver"}
AI_KINDS = {"AI_AGENT", "AI_MODEL"}
VALID_FINDING_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
VALID_FINDING_STATUSES = {"OPEN", "CONFIRMED", "PARTIALLY_CONFIRMED", "FALSE_POSITIVE", "IN_REMEDIATION", "IMPLEMENTED", "REVALIDATION_FAILED", "RESOLVED", "BLOCKED", "ACCEPTED_RISK"}
STAGES = (
    "INTAKE",
    "RISK_CLASSIFIED",
    "REQUIREMENTS_VERIFIED",
    "ARCHITECTURE_VERIFIED",
    "IMPLEMENTATION",
    "VERIFICATION",
    "SECURITY_VERIFIED",
    "RELEASE_READY",
    "RELEASE_APPROVED",
    "DEPLOYED",
    "PRODUCTION_VERIFIED",
    "CONTINUOUS_ASSURANCE",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_status(value: object) -> str:
    raw = str(value or "UNKNOWN").strip().upper()
    return LEGACY_STATUS_MAP.get(raw, raw)


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"JSON file not found: {path}")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to read JSON '{path}': {exc}")
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def _atomic_write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def new_state(project: str, assurance_level: str, framework_version: str = "unknown") -> Dict[str, Any]:
    level = assurance_level.upper()
    if level not in VALID_LEVELS:
        raise ValueError(f"Invalid assurance level '{assurance_level}'")
    if not project.strip():
        raise ValueError("Project name must not be empty")
    now = utc_now()
    return {
        "schema_version": "1.0",
        "framework_version": framework_version,
        "project": project.strip(),
        "assurance_level": level,
        "current_stage": "INTAKE",
        "created_at": now,
        "updated_at": now,
        "actors": {},
        "controls": {},
        "open_findings": [],
        "material_decisions": [],
        "transition_history": [],
    }


def validate_state(state: Mapping[str, Any]) -> List[str]:
    errors: List[str] = []
    if str(state.get("assurance_level", "")).upper() not in VALID_LEVELS:
        errors.append("invalid assurance_level")
    if str(state.get("current_stage", "")) not in STAGES:
        errors.append("invalid current_stage")
    if not str(state.get("project", "")).strip():
        errors.append("project is required")

    actors = state.get("actors", {})
    if not isinstance(actors, dict):
        errors.append("actors must be an object")
    else:
        for role, actor in actors.items():
            if role not in VALID_ROLES:
                errors.append(f"unknown actor role: {role}")
            if not isinstance(actor, dict):
                errors.append(f"actor '{role}' must be an object")
                continue
            if not str(actor.get("actor_id", "")).strip():
                errors.append(f"actor '{role}' is missing actor_id")
            if str(actor.get("kind", "")).upper() not in VALID_ACTOR_KINDS:
                errors.append(f"actor '{role}' has invalid kind")

    controls = state.get("controls", {})
    if not isinstance(controls, dict):
        errors.append("controls must be an object")
    else:
        for control_id, result in controls.items():
            if not isinstance(result, dict):
                errors.append(f"control '{control_id}' must be an object")
            elif normalize_status(result.get("status")) not in VALID_STATUSES:
                errors.append(f"control '{control_id}' has invalid status")
    return errors


def load_state(path: Path) -> Dict[str, Any]:
    state = _read_json(path)
    errors = validate_state(state)
    if errors:
        raise ValueError("Invalid assurance state: " + "; ".join(errors))
    return state


def save_state(path: Path, state: Dict[str, Any]) -> None:
    errors = validate_state(state)
    if errors:
        raise ValueError("Invalid assurance state: " + "; ".join(errors))
    state["updated_at"] = utc_now()
    _atomic_write_json(path, state)


def record_actor(
    state: Dict[str, Any],
    role: str,
    actor_id: str,
    kind: str,
    session_id: Optional[str] = None,
    model_id: Optional[str] = None,
) -> None:
    role_norm = role.strip().lower()
    kind_norm = kind.strip().upper()
    if role_norm not in VALID_ROLES:
        raise ValueError(f"Invalid actor role '{role}'")
    if kind_norm not in VALID_ACTOR_KINDS:
        raise ValueError(f"Invalid actor kind '{kind}'")
    if not actor_id.strip():
        raise ValueError("actor_id must not be empty")
    state.setdefault("actors", {})[role_norm] = {
        "actor_id": actor_id.strip(),
        "kind": kind_norm,
        "session_id": (session_id or "").strip() or None,
        "model_id": (model_id or "").strip() or None,
        "recorded_at": utc_now(),
    }


def record_control(
    state: Dict[str, Any],
    control_id: str,
    status: str,
    evidence: Optional[Sequence[str]] = None,
    rationale: Optional[str] = None,
    waiver: Optional[Mapping[str, Any]] = None,
) -> None:
    control = control_id.strip().upper()
    normalized = normalize_status(status)
    if not control:
        raise ValueError("control_id must not be empty")
    if normalized not in VALID_STATUSES:
        raise ValueError(f"Invalid control status '{status}'")
    result: Dict[str, Any] = {
        "status": normalized,
        "evidence": [str(item).strip() for item in (evidence or []) if str(item).strip()],
        "rationale": (rationale or "").strip(),
        "updated_at": utc_now(),
    }
    if waiver is not None:
        result["waiver"] = dict(waiver)
    state.setdefault("controls", {})[control] = result



def import_assessment(
    state: Dict[str, Any],
    assessment: Mapping[str, Any],
    project_root: Path,
    root: Path = ROOT,
) -> Dict[str, Any]:
    """Import a legacy/current assessment only after evidence-path validation.

    Unsupported, missing, or invalid PASS/NA claims become UNKNOWN rather than
    silently authorizing a gate.
    """
    from tools.assess import assess_data

    level = str(assessment.get("assurance_level", "")).upper()
    if level != str(state.get("assurance_level", "")).upper():
        raise ValueError(
            f"Assessment level '{level}' does not match state level '{state.get('assurance_level')}'"
        )
    assessed = assess_data(
        dict(assessment),
        root=root,
        project_root=project_root.resolve(),
        verify_evidence_paths=True,
    )
    if assessed.get("error"):
        raise ValueError(str(assessed["error"]))

    raw_controls = assessment.get("controls", {})
    if not isinstance(raw_controls, dict):
        raw_controls = {}
    passed = set(assessed.get("passed", []))
    failed = set(assessed.get("fail", []))
    valid_na = set(assessed.get("na", []))
    invalid_pass = set(assessed.get("invalid_pass", []))
    invalid_na = set(assessed.get("invalid_na", []))
    required = load_profile_controls(level, root)

    imported: List[str] = []
    downgraded: List[str] = []
    for control_id in required:
        raw = raw_controls.get(control_id, {})
        raw = raw if isinstance(raw, dict) else {}
        evidence = raw.get("evidence", [])
        ev = evidence if isinstance(evidence, list) else []
        rationale = str(raw.get("rationale", "") or "")

        if control_id in passed:
            status = "PASS"
        elif control_id in failed:
            status = "FAIL"
        elif control_id in valid_na:
            status = "NOT_APPLICABLE"
        else:
            status = "UNKNOWN"
            if control_id in invalid_pass or control_id in invalid_na:
                downgraded.append(control_id)

        record_control(state, control_id, status, ev, rationale)
        imported.append(control_id)

    return {
        "status": "PASS",
        "assessment_success": bool(assessed.get("success")),
        "imported_controls": imported,
        "downgraded_to_unknown": downgraded,
        "not_assessed": list(assessed.get("not_assessed", [])),
    }


def load_profile_controls(level: str, root: Path = ROOT) -> List[str]:
    level_norm = level.upper()
    if level_norm not in VALID_LEVELS:
        raise ValueError(f"Invalid assurance level '{level}'")
    profile = _read_json(root / "profiles" / f"{level_norm.lower()}.json")
    controls = profile.get("included_controls", [])
    if not isinstance(controls, list):
        raise ValueError(f"Profile '{level_norm}' included_controls must be an array")
    return [str(item).strip().upper() for item in controls if str(item).strip()]


def load_gate_policy(root: Path = ROOT) -> Dict[str, Any]:
    return _read_json(root / "controls" / "gates.json")


def _gate_for_target(policy: Mapping[str, Any], target_stage: str) -> Dict[str, Any]:
    gates = policy.get("gates", [])
    if not isinstance(gates, list):
        raise ValueError("Gate policy must contain a gates array")
    for gate in gates:
        if isinstance(gate, dict) and gate.get("target_stage") == target_stage:
            return dict(gate)
    raise ValueError(f"No gate policy defined for target stage '{target_stage}'")


def _valid_waiver(result: Mapping[str, Any]) -> Tuple[bool, str]:
    waiver = result.get("waiver")
    if not isinstance(waiver, dict):
        return False, "WAIVED status requires waiver metadata"
    owner = str(waiver.get("owner", "")).strip()
    rationale = str(waiver.get("rationale", "")).strip()
    expires = str(waiver.get("expires", "")).strip()
    if not owner or not rationale or not expires:
        return False, "waiver requires owner, rationale, and expires"
    try:
        expiry = date.fromisoformat(expires)
    except ValueError:
        return False, "waiver expires must use YYYY-MM-DD"
    if expiry < date.today():
        return False, f"waiver expired on {expires}"
    return True, ""


def _control_decision(
    result: Optional[Mapping[str, Any]],
    allow_waiver: bool,
) -> Tuple[bool, str, str]:
    if result is None:
        return False, "UNKNOWN", "required control has no recorded result"
    status = normalize_status(result.get("status"))
    if status == "PASS":
        evidence = result.get("evidence", [])
        if not isinstance(evidence, list) or not any(str(item).strip() for item in evidence):
            return False, status, "PASS requires evidence"
        return True, status, ""
    if status == "NOT_APPLICABLE":
        if not str(result.get("rationale", "")).strip():
            return False, status, "NOT_APPLICABLE requires rationale"
        return True, status, ""
    if status == "WAIVED":
        if not allow_waiver:
            return False, status, "waiver is not permitted at this gate"
        valid, reason = _valid_waiver(result)
        return valid, status, reason
    if status == "FAIL":
        return False, status, "required control failed"
    if status == "UNKNOWN":
        return False, status, "required control is unknown/unverified"
    return False, status, f"unsupported status '{status}'"


def _actor(state: Mapping[str, Any], role: str) -> Optional[Mapping[str, Any]]:
    actors = state.get("actors", {})
    if not isinstance(actors, dict):
        return None
    actor = actors.get(role)
    return actor if isinstance(actor, dict) else None


def check_actor_independence(
    state: Mapping[str, Any],
    left_role: str,
    right_role: str,
    strong_model_independence: bool = False,
) -> List[str]:
    left = _actor(state, left_role)
    right = _actor(state, right_role)
    reasons: List[str] = []
    if left is None:
        reasons.append(f"missing actor provenance for '{left_role}'")
    if right is None:
        reasons.append(f"missing actor provenance for '{right_role}'")
    if reasons:
        return reasons

    left_id = str(left.get("actor_id", "")).strip()
    right_id = str(right.get("actor_id", "")).strip()
    if not left_id or not right_id:
        reasons.append("actor_id is required for independence verification")
    elif left_id == right_id:
        reasons.append(f"{left_role} and {right_role} must be different actors")

    left_session = str(left.get("session_id") or "").strip()
    right_session = str(right.get("session_id") or "").strip()
    if left_session and right_session and left_session == right_session:
        reasons.append(f"{left_role} and {right_role} must not share the same session")

    if strong_model_independence:
        left_kind = str(left.get("kind", "")).upper()
        right_kind = str(right.get("kind", "")).upper()
        left_model = str(left.get("model_id") or "").strip()
        right_model = str(right.get("model_id") or "").strip()
        if left_kind in AI_KINDS and right_kind in AI_KINDS:
            if not left_model or not right_model:
                reasons.append("strong independence requires model_id for both AI actors")
            elif left_model == right_model:
                reasons.append(
                    f"strong independence requires different model_id values for {left_role} and {right_role}"
                )
    return reasons



def _find_finding(state: Mapping[str, Any], finding_id: str) -> Optional[Dict[str, Any]]:
    findings = state.get("open_findings", [])
    if not isinstance(findings, list):
        return None
    target = finding_id.strip().upper()
    for item in findings:
        if isinstance(item, dict) and str(item.get("id", "")).upper() == target:
            return item
    return None


def register_finding(
    state: Dict[str, Any],
    finding_id: str,
    severity: str,
    title: str,
    status: str = "OPEN",
    evidence: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    fid = finding_id.strip().upper()
    sev = severity.strip().upper()
    finding_status = status.strip().upper()
    if not fid:
        raise ValueError("finding_id must not be empty")
    if sev not in VALID_FINDING_SEVERITIES:
        raise ValueError(f"Invalid finding severity '{severity}'")
    if finding_status not in VALID_FINDING_STATUSES:
        raise ValueError(f"Invalid finding status '{status}'")
    if _find_finding(state, fid) is not None:
        raise ValueError(f"Finding '{fid}' already exists")
    finding = {
        "id": fid,
        "title": title.strip() or fid,
        "severity": sev,
        "status": finding_status,
        "evidence": [str(item).strip() for item in (evidence or []) if str(item).strip()],
        "history": [{"status": finding_status, "at": utc_now()}],
    }
    state.setdefault("open_findings", []).append(finding)
    return finding


def start_remediation(
    state: Dict[str, Any],
    finding_id: str,
    evidence: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    finding = _find_finding(state, finding_id)
    if finding is None:
        raise ValueError(f"Finding '{finding_id}' not found")
    if str(finding.get("status", "")).upper() not in {"CONFIRMED", "PARTIALLY_CONFIRMED", "REVALIDATION_FAILED"}:
        raise ValueError("Finding must be confirmed before remediation")
    remediator = _actor(state, "remediator")
    if remediator is None:
        raise ValueError("remediator actor provenance is required")
    finding["status"] = "IN_REMEDIATION"
    finding["remediator"] = dict(remediator)
    finding["remediation_evidence"] = [str(item).strip() for item in (evidence or []) if str(item).strip()]
    finding.setdefault("history", []).append({"status": "IN_REMEDIATION", "at": utc_now()})
    return finding


def mark_remediation_implemented(
    state: Dict[str, Any],
    finding_id: str,
    evidence: Sequence[str],
) -> Dict[str, Any]:
    finding = _find_finding(state, finding_id)
    if finding is None:
        raise ValueError(f"Finding '{finding_id}' not found")
    if str(finding.get("status", "")).upper() != "IN_REMEDIATION":
        raise ValueError("Finding must be IN_REMEDIATION before implementation can be recorded")
    ev = [str(item).strip() for item in evidence if str(item).strip()]
    if not ev:
        raise ValueError("Implemented remediation requires evidence")
    finding["status"] = "IMPLEMENTED"
    finding["implementation_evidence"] = ev
    finding.setdefault("history", []).append({"status": "IMPLEMENTED", "at": utc_now()})
    return finding


def revalidate_finding(
    state: Dict[str, Any],
    finding_id: str,
    result: str,
    evidence: Sequence[str],
) -> Dict[str, Any]:
    finding = _find_finding(state, finding_id)
    if finding is None:
        raise ValueError(f"Finding '{finding_id}' not found")
    if str(finding.get("status", "")).upper() != "IMPLEMENTED":
        raise ValueError("Finding must be IMPLEMENTED before independent revalidation")
    ev = [str(item).strip() for item in evidence if str(item).strip()]
    if not ev:
        raise ValueError("Revalidation requires evidence")
    remediator = finding.get("remediator")
    revalidator = _actor(state, "revalidator")
    if not isinstance(remediator, dict):
        raise ValueError("Finding is missing remediator provenance")
    if revalidator is None:
        raise ValueError("revalidator actor provenance is required")

    level = str(state.get("assurance_level", "")).upper()
    shadow_state = {"actors": {"remediator": remediator, "revalidator": revalidator}}
    strong = level in {"AL3", "AL4"}
    independence_errors = check_actor_independence(
        shadow_state, "remediator", "revalidator", strong_model_independence=strong
    )
    if independence_errors:
        raise ValueError("Independent revalidation failed: " + "; ".join(independence_errors))

    normalized = result.strip().upper()
    if normalized not in {"PASS", "FAIL"}:
        raise ValueError("Revalidation result must be PASS or FAIL")
    finding["revalidation"] = {
        "result": normalized,
        "evidence": ev,
        "revalidator": dict(revalidator),
        "at": utc_now(),
    }
    new_status = "RESOLVED" if normalized == "PASS" else "REVALIDATION_FAILED"
    finding["status"] = new_status
    finding.setdefault("history", []).append({"status": new_status, "at": utc_now()})
    return finding


def _blocking_findings(state: Mapping[str, Any], severities: Iterable[str]) -> List[str]:
    blocked = {str(item).upper() for item in severities}
    findings = state.get("open_findings", [])
    if not isinstance(findings, list):
        return ["open_findings must be an array"]
    output: List[str] = []
    for item in findings:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "OPEN")).upper()
        severity = str(item.get("severity", "UNKNOWN")).upper()
        if status not in {"RESOLVED", "CLOSED", "FALSE_POSITIVE"} and severity in blocked:
            output.append(str(item.get("id", "UNNAMED")))
    return output


def _open_material_decisions(state: Mapping[str, Any]) -> List[str]:
    decisions = state.get("material_decisions", [])
    if not isinstance(decisions, list):
        return ["material_decisions must be an array"]
    return [
        str(item.get("id", "UNNAMED"))
        for item in decisions
        if isinstance(item, dict)
        and str(item.get("status", "OPEN")).upper() not in {"RESOLVED", "CLOSED"}
    ]


def evaluate_gate(state: Mapping[str, Any], target_stage: str, root: Path = ROOT) -> Dict[str, Any]:
    target = target_stage.strip().upper()
    current = str(state.get("current_stage", ""))
    if target not in STAGES:
        raise ValueError(f"Unknown target stage '{target_stage}'")
    if current not in STAGES:
        raise ValueError(f"Invalid current stage '{current}'")

    reasons: List[str] = []
    current_index = STAGES.index(current)
    expected = STAGES[current_index + 1] if current_index + 1 < len(STAGES) else None
    if STAGES.index(target) != current_index + 1:
        reasons.append(f"non-sequential transition blocked: {current} -> {target}; expected {expected}")

    gate = _gate_for_target(load_gate_policy(root), target)
    level = str(state.get("assurance_level", "")).upper()
    profile_controls = set(load_profile_controls(level, root))
    required = [
        str(control_id).upper()
        for control_id in gate.get("required_controls", [])
        if str(control_id).upper() in profile_controls
    ]
    raw_controls = state.get("controls", {})
    controls = raw_controls if isinstance(raw_controls, dict) else {}
    control_results: Dict[str, Dict[str, Any]] = {}
    blocking_controls: List[str] = []
    unknown_controls: List[str] = []
    allow_waiver = bool(gate.get("allow_waiver", True))

    for control_id in required:
        raw = controls.get(control_id)
        result = raw if isinstance(raw, dict) else None
        ok, status, reason = _control_decision(result, allow_waiver)
        control_results[control_id] = {"status": status, "satisfied": ok, "reason": reason}
        if not ok:
            blocking_controls.append(control_id)
            if status == "UNKNOWN":
                unknown_controls.append(control_id)
            reasons.append(f"{control_id}: {reason}")

    min_level = str(gate.get("independence_from_level", "")).upper()
    if min_level in VALID_LEVELS and VALID_LEVELS.index(level) >= VALID_LEVELS.index(min_level):
        strong_from = str(gate.get("strong_model_independence_from_level", "")).upper()
        strong = strong_from in VALID_LEVELS and VALID_LEVELS.index(level) >= VALID_LEVELS.index(strong_from)
        pairs = gate.get("independence_pairs", [])
        if isinstance(pairs, list):
            for pair in pairs:
                if isinstance(pair, list) and len(pair) == 2:
                    reasons.extend(check_actor_independence(state, str(pair[0]), str(pair[1]), strong))

    open_decisions: List[str] = []
    if bool(gate.get("block_on_open_material_decisions", False)):
        open_decisions = _open_material_decisions(state)
        if open_decisions:
            reasons.append("unresolved material decisions: " + ", ".join(open_decisions))

    blocking_findings = _blocking_findings(state, gate.get("blocking_finding_severities", []))
    if blocking_findings:
        reasons.append("blocking open findings: " + ", ".join(blocking_findings))

    decision = "ALLOW" if not reasons else "BLOCK"
    return {
        "decision": decision,
        "allowed": decision == "ALLOW",
        "gate_id": gate.get("id"),
        "from_stage": current,
        "target_stage": target,
        "assurance_level": level,
        "required_controls": required,
        "control_results": control_results,
        "blocking_controls": blocking_controls,
        "unknown_controls": unknown_controls,
        "blocking_findings": blocking_findings,
        "open_material_decisions": open_decisions,
        "reasons": reasons,
        "evaluated_at": utc_now(),
    }


def advance_state(state: Dict[str, Any], target_stage: str, root: Path = ROOT) -> Dict[str, Any]:
    result = evaluate_gate(state, target_stage, root=root)
    state.setdefault("transition_history", []).append({
        "from_stage": result["from_stage"],
        "target_stage": result["target_stage"],
        "decision": result["decision"],
        "reasons": list(result["reasons"]),
        "at": result["evaluated_at"],
    })
    if result["allowed"]:
        state["current_stage"] = result["target_stage"]
    return result


def default_state_path(target: Path) -> Path:
    return target.resolve() / ".auracode" / "assurance-state.json"


def _state_path(target: str, state_path: Optional[str]) -> Path:
    return Path(state_path).resolve() if state_path else default_state_path(Path(target))


def build_parser() -> "argparse.ArgumentParser":
    import argparse
    parser = argparse.ArgumentParser(description="AuraCode persistent assurance-state decision engine")
    sub = parser.add_subparsers(dest="action", required=True)

    init_p = sub.add_parser("init", help="Create a new assurance state")
    init_p.add_argument("target", nargs="?", default=".")
    init_p.add_argument("--project", required=True)
    init_p.add_argument("--level", required=True, choices=VALID_LEVELS)
    init_p.add_argument("--framework-version", default="unknown")
    init_p.add_argument("--state")
    init_p.add_argument("--json", action="store_true")

    import_p = sub.add_parser("import-assessment", help="Import a validated assessment into assurance state")
    import_p.add_argument("target", nargs="?", default=".")
    import_p.add_argument("--assessment", required=True)
    import_p.add_argument("--state")
    import_p.add_argument("--json", action="store_true")

    actor_p = sub.add_parser("actor", help="Record actor provenance")
    actor_p.add_argument("target", nargs="?", default=".")
    actor_p.add_argument("--role", required=True, choices=sorted(VALID_ROLES))
    actor_p.add_argument("--actor-id", required=True)
    actor_p.add_argument("--kind", required=True, choices=sorted(VALID_ACTOR_KINDS))
    actor_p.add_argument("--session-id")
    actor_p.add_argument("--model-id")
    actor_p.add_argument("--state")
    actor_p.add_argument("--json", action="store_true")

    control_p = sub.add_parser("control", help="Record one control result")
    control_p.add_argument("target", nargs="?", default=".")
    control_p.add_argument("--id", required=True)
    control_p.add_argument("--status", required=True, choices=sorted(VALID_STATUSES | set(LEGACY_STATUS_MAP)))
    control_p.add_argument("--evidence", action="append", default=[])
    control_p.add_argument("--rationale", default="")
    control_p.add_argument("--state")
    control_p.add_argument("--json", action="store_true")

    finding_p = sub.add_parser("finding", help="Manage finding remediation and independent revalidation")
    finding_sub = finding_p.add_subparsers(dest="finding_action", required=True)

    finding_add = finding_sub.add_parser("add", help="Register an audit/review finding")
    finding_add.add_argument("target", nargs="?", default=".")
    finding_add.add_argument("--id", required=True)
    finding_add.add_argument("--severity", required=True, choices=sorted(VALID_FINDING_SEVERITIES))
    finding_add.add_argument("--title", required=True)
    finding_add.add_argument("--status", default="OPEN", choices=sorted(VALID_FINDING_STATUSES))
    finding_add.add_argument("--evidence", action="append", default=[])
    finding_add.add_argument("--state")
    finding_add.add_argument("--json", action="store_true")

    finding_start = finding_sub.add_parser("start", help="Start remediation for a confirmed finding")
    finding_start.add_argument("target", nargs="?", default=".")
    finding_start.add_argument("--id", required=True)
    finding_start.add_argument("--evidence", action="append", default=[])
    finding_start.add_argument("--state")
    finding_start.add_argument("--json", action="store_true")

    finding_impl = finding_sub.add_parser("implemented", help="Record remediation implementation evidence")
    finding_impl.add_argument("target", nargs="?", default=".")
    finding_impl.add_argument("--id", required=True)
    finding_impl.add_argument("--evidence", action="append", required=True)
    finding_impl.add_argument("--state")
    finding_impl.add_argument("--json", action="store_true")

    finding_reval = finding_sub.add_parser("revalidate", help="Record independent revalidation result")
    finding_reval.add_argument("target", nargs="?", default=".")
    finding_reval.add_argument("--id", required=True)
    finding_reval.add_argument("--result", required=True, choices=["PASS", "FAIL"])
    finding_reval.add_argument("--evidence", action="append", required=True)
    finding_reval.add_argument("--state")
    finding_reval.add_argument("--json", action="store_true")

    gate_p = sub.add_parser("gate", help="Evaluate or advance one sequential assurance gate")
    gate_p.add_argument("target", nargs="?", default=".")
    gate_p.add_argument("--to", required=True, choices=STAGES)
    gate_p.add_argument("--advance", action="store_true")
    gate_p.add_argument("--state")
    gate_p.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    state_path = _state_path(args.target, getattr(args, "state", None))

    if args.action == "init":
        if state_path.exists():
            print(f"ERROR: assurance state already exists: {state_path}")
            return 2
        state = new_state(args.project, args.level, args.framework_version)
        save_state(state_path, state)
        payload = {"status": "PASS", "state_file": str(state_path), "state": state}
    else:
        try:
            state = load_state(state_path)
        except ValueError as exc:
            print(f"ERROR: {exc}")
            return 2

        if args.action == "import-assessment":
            try:
                assessment_path = Path(args.assessment).resolve()
                assessment = _read_json(assessment_path)
                imported = import_assessment(
                    state,
                    assessment,
                    project_root=Path(args.target).resolve(),
                )
            except ValueError as exc:
                print(f"ERROR: {exc}")
                return 2
            save_state(state_path, state)
            payload = {
                "status": "PASS",
                "state_file": str(state_path),
                "assessment": imported,
            }
        elif args.action == "finding":
            try:
                if args.finding_action == "add":
                    finding = register_finding(
                        state, args.id, args.severity, args.title, args.status, args.evidence
                    )
                elif args.finding_action == "start":
                    finding = start_remediation(state, args.id, args.evidence)
                elif args.finding_action == "implemented":
                    finding = mark_remediation_implemented(state, args.id, args.evidence)
                else:
                    finding = revalidate_finding(state, args.id, args.result, args.evidence)
            except ValueError as exc:
                print(f"ERROR: {exc}")
                return 2
            save_state(state_path, state)
            payload = {
                "status": "PASS",
                "state_file": str(state_path),
                "finding": finding,
            }
        elif args.action == "actor":
            record_actor(state, args.role, args.actor_id, args.kind, args.session_id, args.model_id)
            save_state(state_path, state)
            payload = {"status": "PASS", "state_file": str(state_path), "actor": args.role}
        elif args.action == "control":
            record_control(state, args.id, args.status, args.evidence, args.rationale)
            save_state(state_path, state)
            payload = {"status": "PASS", "state_file": str(state_path), "control": args.id.upper()}
        else:
            try:
                payload = advance_state(state, args.to) if args.advance else evaluate_gate(state, args.to)
            except ValueError as exc:
                print(f"ERROR: {exc}")
                return 2
            if args.advance:
                save_state(state_path, state)

    if getattr(args, "json", False):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.action == "gate":
        print(f"{payload['decision']}: {payload['from_stage']} -> {payload['target_stage']}")
        for reason in payload.get("reasons", []):
            print(f"- {reason}")
    else:
        print(f"{payload['status']}: {payload.get('state_file')}")
    return 0 if payload.get("decision", payload.get("status")) in {"ALLOW", "PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
