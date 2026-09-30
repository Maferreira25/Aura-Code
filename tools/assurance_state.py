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
