"""Fail-closed evidence decisions against an externally trusted policy."""
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from tools.evidence_engine import canonical_bytes, digest_bytes, reject_duplicates, verify


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)


def text_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(x, str) and bool(x.strip()) for x in value)


def validate_policy(policy: Any) -> None:
    if (not isinstance(policy, dict) or set(policy) != {"schema_version", "policy_id", "requirements"}
            or policy["schema_version"] != "1" or not isinstance(policy["policy_id"], str)
            or not policy["policy_id"].strip() or not isinstance(policy["requirements"], list)
            or not policy["requirements"]):
        raise ValueError("Invalid or empty evidence policy")
    identities = set()
    for requirement in policy["requirements"]:
        fields = {"requirement_id", "control_id", "verification_id", "command", "scope"}
        if not isinstance(requirement, dict) or set(requirement) != fields:
            raise ValueError("Incomplete policy requirement")
        for name in ("requirement_id", "control_id", "verification_id"):
            if not isinstance(requirement[name], str) or not requirement[name].strip():
                raise ValueError("Invalid policy identity")
        identity = requirement["requirement_id"]
        if identity in identities or not text_list(requirement["command"]) or not text_list(requirement["scope"]):
            raise ValueError("Duplicate identity or empty command/scope")
        identities.add(identity)
        if len(set(requirement["scope"])) != len(requirement["scope"]):
            raise ValueError("Duplicate scope path")
        for name in requirement["scope"]:
            path = Path(name)
            if path.is_absolute() or ".." in path.parts or path.as_posix() != name or "\\" in name:
                raise ValueError("Invalid policy scope path")


def decide(policy: Any, records: List[Any], root: Path) -> Dict[str, Any]:
    """Every requirement needs exactly one matching, valid execution record."""
    report: Dict[str, Any] = {"status": "FAIL", "decisions": [], "links": []}
    try:
        validate_policy(policy)
        if not isinstance(records, list) or any(not isinstance(record, dict) for record in records):
            raise ValueError("Invalid evidence bundle")
        ids = [record.get("evidence_id") for record in records]
        if any(not isinstance(identity, str) for identity in ids) or len(set(ids)) != len(ids):
            raise ValueError("Missing or duplicate evidence identity")
        report["policy_id"] = policy["policy_id"]
        report["policy_digest"] = digest_bytes(canonical_bytes(policy))
        used = set()
        for requirement in policy["requirements"]:
            matches = [record for record in records
                       if record.get("control_id") == requirement["control_id"]
                       and record.get("verification_id") == requirement["verification_id"]]
            decision = {"requirement_id": requirement["requirement_id"], "status": "NOT_ASSESSED"}
            if len(matches) != 1:
                decision["reason"] = "Exactly one matching evidence record is required"
            else:
                record = matches[0]
                used.add(record["evidence_id"])
                decision["evidence_id"] = record["evidence_id"]
                decision.update(verify(record, root))
                if decision["status"] == "PASS":
                    if (record["command"] != requirement["command"] or
                            set(record["scope"]) != set(requirement["scope"])):
                        decision.update(status="INVALID", reason="Command or scope differs from policy")
                    else:
                        report["links"].append({
                            "requirement_id": requirement["requirement_id"],
                            "control_id": requirement["control_id"],
                            "verification_id": requirement["verification_id"],
                            "evidence_id": record["evidence_id"], "evidence_digest": record["digest"],
                        })
            report["decisions"].append(decision)
        if used != set(ids):
            report["reason"] = "Bundle contains evidence outside the policy"
        elif all(decision["status"] == "PASS" for decision in report["decisions"]):
            report["status"] = "PASS"
        return report
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        report["reason"] = "Invalid policy or evidence bundle"
        return report
