#!/usr/bin/env python3
"""Canonical assurance result model for Aura Code.

This module is intentionally dependency-free and fail-closed. Evaluator-specific
states must be normalized here before they can influence an assurance decision.

Assurance Continuity Principle:
No dependent stage may proceed on failed, absent, inconclusive, erroneous,
stale, unverifiable, or unvalidated assurance.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional
from uuid import uuid4


class AssuranceStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_TESTED = "NOT_TESTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    WAIVED = "WAIVED"
    ERROR = "ERROR"
    STALE = "STALE"


class StageState(str, Enum):
    READY = "READY"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"


_BLOCKING_STATUSES = frozenset(
    {
        AssuranceStatus.FAIL,
        AssuranceStatus.INCONCLUSIVE,
        AssuranceStatus.NOT_TESTED,
        AssuranceStatus.ERROR,
        AssuranceStatus.STALE,
    }
)

# Conservative aggregation order. This is a migration aid, not the future
# policy engine. Lower index means higher precedence.
_STATUS_PRECEDENCE = (
    AssuranceStatus.ERROR,
    AssuranceStatus.FAIL,
    AssuranceStatus.STALE,
    AssuranceStatus.INCONCLUSIVE,
    AssuranceStatus.NOT_TESTED,
    AssuranceStatus.WAIVED,
    AssuranceStatus.PASS,
    AssuranceStatus.NOT_APPLICABLE,
)

_LEGACY_DIRECT_MAP = {
    "PASS": AssuranceStatus.PASS,
    "FAIL": AssuranceStatus.FAIL,
    "ERROR": AssuranceStatus.ERROR,
    "NOT_RUN": AssuranceStatus.NOT_TESTED,
    "NOT_ASSESSED": AssuranceStatus.NOT_TESTED,
    "NOT_APPLICABLE": AssuranceStatus.NOT_APPLICABLE,
    "NA": AssuranceStatus.NOT_APPLICABLE,
}


@dataclass(frozen=True)
class Producer:
    tool: str
    method: str
    tool_version: Optional[str] = None


@dataclass(frozen=True)
class Target:
    workspace: str
    source_commit: Optional[str] = None
    tree_hash: Optional[str] = None
    artifact_digest: Optional[str] = None


@dataclass(frozen=True)
class Execution:
    started_at: str
    finished_at: str
    exit_code: Optional[int] = None
    duration_ms: Optional[int] = None


@dataclass(frozen=True)
class CanonicalAssuranceResult:
    schema_version: str
    result_id: str
    check_id: str
    status: str
    producer: Producer
    target: Target
    execution: Execution
    reason: str
    control_id: Optional[str] = None
    severity: str = "MEDIUM"
    scope: Dict[str, Any] = field(default_factory=dict)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    waiver: Optional[Dict[str, Any]] = None
    legacy: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_legacy_status(status: Any) -> AssuranceStatus:
    """Normalize a legacy status without permissive coercion.

    Generic WARN is deliberately rejected because its meaning depends on the
    evaluator. Adapters such as mutation or SARIF must interpret WARN using
    their domain-specific facts.
    """
    if not isinstance(status, str):
        raise ValueError("Assurance status must be an exact string value.")
    if status in AssuranceStatus._value2member_map_:
        return AssuranceStatus(status)
    if status in _LEGACY_DIRECT_MAP:
        return _LEGACY_DIRECT_MAP[status]
    if status == "WARN":
        raise ValueError("WARN requires an evaluator-specific adapter; generic normalization is forbidden.")
    raise ValueError(f"Unknown assurance status: {status!r}")


def validate_status(status: Any) -> AssuranceStatus:
    """Validate canonical status exactly; lowercase/whitespace aliases are rejected."""
    if not isinstance(status, str) or status not in AssuranceStatus._value2member_map_:
        raise ValueError(f"Invalid canonical assurance status: {status!r}")
    return AssuranceStatus(status)


def is_progression_blocked(status: Any, *, waiver_authorized: bool = False) -> bool:
    """Return whether a dependent stage MUST be blocked.

    PASS can advance. NOT_APPLICABLE can advance only after applicability was
    already justified by the caller/policy layer. WAIVED advances only when an
    authorized policy decision explicitly permits it.
    """
    canonical = validate_status(status.value if isinstance(status, AssuranceStatus) else status)
    if canonical in _BLOCKING_STATUSES:
        return True
    if canonical is AssuranceStatus.WAIVED:
        return not waiver_authorized
    return False


def progression_state(
    required_results: Iterable[Mapping[str, Any]],
    *,
    waiver_authorized: bool = False,
) -> Dict[str, Any]:
    """Evaluate a stage boundary using the Assurance Continuity Principle."""
    blockers: List[Dict[str, Any]] = []
    seen = 0
    for item in required_results:
        seen += 1
        raw_status = item.get("status")
        try:
            status = validate_status(raw_status)
        except ValueError as exc:
            blockers.append(
                {
                    "check_id": item.get("check_id"),
                    "status": "ERROR",
                    "reason": f"Invalid predecessor result: {exc}",
                }
            )
            continue
        if is_progression_blocked(status, waiver_authorized=waiver_authorized):
            blockers.append(
                {
                    "check_id": item.get("check_id"),
                    "status": status.value,
                    "reason": item.get("reason", ""),
                }
            )

    if seen == 0:
        blockers.append(
            {
                "check_id": None,
                "status": AssuranceStatus.NOT_TESTED.value,
                "reason": "No predecessor assurance results were supplied.",
            }
        )

    return {
        "state": StageState.BLOCKED.value if blockers else StageState.READY.value,
        "blocked_by": blockers,
    }


def aggregate_status(statuses: Iterable[Any]) -> AssuranceStatus:
    """Aggregate canonically and fail closed on empty input or invalid states."""
    normalized: List[AssuranceStatus] = []
    for status in statuses:
        if isinstance(status, AssuranceStatus):
            normalized.append(status)
        else:
            normalized.append(validate_status(status))

    if not normalized:
        return AssuranceStatus.NOT_TESTED

    present = set(normalized)
    for candidate in _STATUS_PRECEDENCE:
        if candidate in present:
            return candidate
    return AssuranceStatus.ERROR


def build_result(
    *,
    check_id: str,
    status: Any,
    producer_tool: str,
    producer_method: str,
    workspace: str,
    reason: str,
    control_id: Optional[str] = None,
    severity: str = "MEDIUM",
    tool_version: Optional[str] = None,
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
    exit_code: Optional[int] = None,
    duration_ms: Optional[int] = None,
    source_commit: Optional[str] = None,
    tree_hash: Optional[str] = None,
    artifact_digest: Optional[str] = None,
    scope: Optional[Dict[str, Any]] = None,
    findings: Optional[List[Dict[str, Any]]] = None,
    evidence: Optional[List[str]] = None,
    waiver: Optional[Dict[str, Any]] = None,
    legacy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a validated canonical result dictionary."""
    canonical = validate_status(status.value if isinstance(status, AssuranceStatus) else status)

    if not check_id or not isinstance(check_id, str):
        raise ValueError("check_id is required.")
    if not producer_tool or not producer_method:
        raise ValueError("producer tool and method are required.")
    if not workspace:
        raise ValueError("workspace is required.")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("reason is required; empty assurance claims are forbidden.")
    if canonical is AssuranceStatus.WAIVED and not waiver:
        raise ValueError("WAIVED requires explicit waiver metadata.")

    start = started_at or utc_now_iso()
    finish = finished_at or start

    result = CanonicalAssuranceResult(
        schema_version="1.0.0",
        result_id=f"AR-{uuid4()}",
        check_id=check_id,
        status=canonical.value,
        producer=Producer(tool=producer_tool, method=producer_method, tool_version=tool_version),
        target=Target(
            workspace=str(Path(workspace)),
            source_commit=source_commit,
            tree_hash=tree_hash,
            artifact_digest=artifact_digest,
        ),
        execution=Execution(
            started_at=start,
            finished_at=finish,
            exit_code=exit_code,
            duration_ms=duration_ms,
        ),
        reason=reason.strip(),
        control_id=control_id,
        severity=severity,
        scope=scope or {},
        findings=findings or [],
        evidence=evidence or [],
        waiver=waiver,
        legacy=legacy,
    )
    return result.to_dict()


def compare_legacy_and_canonical(legacy_status: Any, canonical_status: Any) -> Dict[str, str]:
    """Compare legacy and canonical status conservatively for shadow-mode migration."""
    canonical = validate_status(
        canonical_status.value if isinstance(canonical_status, AssuranceStatus) else canonical_status
    )
    try:
        legacy = normalize_legacy_status(legacy_status)
    except ValueError:
        return {
            "status": "SHADOW_MISMATCH",
            "legacy_status": str(legacy_status),
            "canonical_status": canonical.value,
        }

    return {
        "status": "MATCH" if legacy is canonical else "SHADOW_MISMATCH",
        "legacy_status": legacy.value,
        "canonical_status": canonical.value,
    }
