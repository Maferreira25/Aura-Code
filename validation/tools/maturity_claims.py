#!/usr/bin/env python3
"""Semantic validators for MAT-08, MAT-09 and MAT-10 evidence packages."""
from __future__ import annotations

from typing import Any, Dict, List, Mapping


def _nonempty_list(value: object) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def validate_multilang_qualification(
    data: Mapping[str, Any],
    allow_public_baseline: bool = False,
) -> Dict[str, Any]:
    """Validate MAT-08 qualification; public baseline may be validated but is not maturity-eligible."""
    errors: List[str] = []
    if not bool(data.get("preregistered")):
        errors.append("multilang qualification must be preregistered")
    public_corpus = bool(data.get("public_corpus"))
    if public_corpus and not allow_public_baseline:
        errors.append("public development corpus is not sufficient for stable MAT-08 evidence")
    if not public_corpus:
        commitment = str(data.get("corpus_commitment_sha256", "")).strip().lower()
        if len(commitment) != 64 or any(ch not in "0123456789abcdef" for ch in commitment):
            errors.append("private/fresh MAT-08 evidence requires corpus_commitment_sha256")
        if not bool(data.get("independent_labels")):
            errors.append("private/fresh MAT-08 evidence requires independent_labels=true")
    revision = str(data.get("revision", "")).strip()
    if not revision:
        errors.append("revision is required")
    thresholds = data.get("acceptance_thresholds")
    if not isinstance(thresholds, dict):
        errors.append("acceptance_thresholds object is required")
        thresholds = {}
    languages = data.get("languages")
    if not isinstance(languages, dict):
        errors.append("languages object is required")
        languages = {}

    required_languages = ("python", "typescript")
    results: Dict[str, Any] = {}
    for language in required_languages:
        entry = languages.get(language)
        if not isinstance(entry, dict):
            errors.append(f"{language}: qualification result is required")
            continue
        cases = entry.get("cases")
        tp = entry.get("true_positive")
        tn = entry.get("true_negative")
        fp = entry.get("false_positive")
        fn = entry.get("false_negative")
        for name, value in (("cases", cases), ("true_positive", tp), ("true_negative", tn), ("false_positive", fp), ("false_negative", fn)):
            if not isinstance(value, int) or value < 0:
                errors.append(f"{language}.{name} must be a non-negative integer")
        if not bool(entry.get("parser_available")):
            errors.append(f"{language}: parser_available must be true")
        if not str(entry.get("engine", "")).strip():
            errors.append(f"{language}: engine is required")
        evidence = _nonempty_list(entry.get("evidence"))
        if not any(str(item).strip() for item in evidence):
            errors.append(f"{language}: evidence is required")
        if all(isinstance(v, int) and v >= 0 for v in (tp, tn, fp, fn)):
            total = int(tp) + int(tn) + int(fp) + int(fn)
            if isinstance(cases, int) and cases != total:
                errors.append(f"{language}: cases must equal TP+TN+FP+FN")
            precision = (tp / (tp + fp)) if (tp + fp) else None
            recall = (tp / (tp + fn)) if (tp + fn) else None
            fpr = (fp / (fp + tn)) if (fp + tn) else None
            results[language] = {"precision": precision, "recall": recall, "false_positive_rate": fpr, "cases": total}

    for metric in ("min_recall", "max_false_positive_rate"):
        value = thresholds.get(metric)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= float(value) <= 1:
            errors.append(f"acceptance_thresholds.{metric} must be between 0 and 1")

    if not errors:
        min_recall = float(thresholds["min_recall"])
        max_fpr = float(thresholds["max_false_positive_rate"])
        for language, metrics in results.items():
            recall = metrics["recall"]
            fpr = metrics["false_positive_rate"]
            if recall is None or recall < min_recall:
                errors.append(f"{language}: recall does not meet preregistered threshold")
            if fpr is None or fpr > max_fpr:
                errors.append(f"{language}: false-positive rate exceeds preregistered threshold")

    return {
        "study": "MULTILANG_QUALIFICATION",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "results": results,
        "maturity_eligible": (not public_corpus) and not errors,
        "claim_boundary": "Qualification is limited to the frozen corpus, rules and thresholds in this evidence package.",
    }


def validate_independent_security_audit(data: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate MAT-09 evidence package structure and blocking finding status."""
    errors: List[str] = []
    if not bool(data.get("independence_attestation")):
        errors.append("independence_attestation must be true")
    if data.get("implementation_role") is not False:
        errors.append("implementation_role must be false for the independent assessor")
    for field in ("assessor_id", "revision", "scope"):
        if not str(data.get(field, "")).strip():
            errors.append(f"{field} is required")
    for section in ("threat_model", "supply_chain"):
        item = data.get(section)
        if not isinstance(item, dict):
            errors.append(f"{section} assessment is required")
            continue
        if str(item.get("status", "")).upper() != "PASS":
            errors.append(f"{section}.status must be PASS")
        evidence = _nonempty_list(item.get("evidence"))
        if not any(str(x).strip() for x in evidence):
            errors.append(f"{section}.evidence is required")
    open_findings = data.get("open_findings")
    if not isinstance(open_findings, dict):
        errors.append("open_findings object is required")
    else:
        for severity in ("critical", "high"):
            value = open_findings.get(severity)
            if not isinstance(value, int) or value < 0:
                errors.append(f"open_findings.{severity} must be a non-negative integer")
            elif value != 0:
                errors.append(f"open {severity} findings must be zero for MAT-09")
    return {
        "study": "INDEPENDENT_SECURITY_AUDIT",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
    }


def validate_governance_1_0(data: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate that stable-1.0 governance roles and decision rules are explicitly established."""
    errors: List[str] = []
    if str(data.get("status", "")).upper() != "ADOPTED":
        errors.append("governance status must be ADOPTED")
    if not bool(data.get("human_adoption_attestation")):
        errors.append("human_adoption_attestation must be true")
    adopted_at = str(data.get("adopted_at", "")).strip()
    if not adopted_at:
        errors.append("adopted_at is required")
    adopted_by = _nonempty_list(data.get("adopted_by"))
    if not any(str(item).strip() for item in adopted_by):
        errors.append("adopted_by must identify at least one human authority")
    roles = data.get("roles")
    if not isinstance(roles, dict):
        errors.append("roles object is required")
        roles = {}
    for role in ("maintainers", "release_manager", "security_response"):
        value = roles.get(role)
        if isinstance(value, list):
            if not any(str(x).strip() for x in value):
                errors.append(f"roles.{role} must contain at least one identity")
        elif not str(value or "").strip():
            errors.append(f"roles.{role} is required")
    for field in ("normative_change_rule", "release_authority_rule", "security_response_rule", "appeal_rule"):
        if not str(data.get(field, "")).strip():
            errors.append(f"{field} is required")
    evidence = _nonempty_list(data.get("evidence"))
    if not any(str(x).strip() for x in evidence):
        errors.append("governance evidence is required")
    return {
        "study": "GOVERNANCE_1_0",
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
    }
