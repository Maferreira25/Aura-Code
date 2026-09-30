#!/usr/bin/env python3
"""Aura Code detector diversity engine.

Compares normalized findings from independent analyzers. A finding detected by
only one detector is not discarded; it becomes ASSURANCE_GAP and is a candidate
for a native rule/regression fixture.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Set


def _key(finding: Mapping[str, Any]) -> str:
    fingerprint = finding.get("fingerprint")
    if isinstance(fingerprint, str) and fingerprint:
        return fingerprint
    return "|".join([
        str(finding.get("file") or ""),
        str(finding.get("line") or ""),
        str(finding.get("rule_id") or ""),
        str(finding.get("sink") or ""),
    ])


def compare_detectors(reports: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    reports = list(reports)
    if len(reports) < 2:
        return {
            "status": "NOT_TESTED",
            "assurance_gaps": [],
            "reason": "Detector diversity requires at least two independent reports.",
        }

    detector_sets: Dict[str, Set[str]] = {}
    finding_by_key: Dict[str, Dict[str, Any]] = {}
    for report in reports:
        analyzer_id = str(report.get("analyzer_id") or "")
        if not analyzer_id:
            return {"status": "ERROR", "assurance_gaps": [], "reason": "Analyzer report missing analyzer_id."}
        if analyzer_id in detector_sets:
            return {"status": "ERROR", "assurance_gaps": [], "reason": f"Duplicate analyzer_id: {analyzer_id}"}
        findings = report.get("findings", [])
        if not isinstance(findings, list):
            return {"status": "ERROR", "assurance_gaps": [], "reason": f"Malformed findings for {analyzer_id}."}
        keys: Set[str] = set()
        for finding in findings:
            if not isinstance(finding, Mapping):
                continue
            k = _key(finding)
            keys.add(k)
            finding_by_key.setdefault(k, dict(finding))
        detector_sets[analyzer_id] = keys

    all_keys = set().union(*detector_sets.values()) if detector_sets else set()
    gaps: List[Dict[str, Any]] = []
    for k in sorted(all_keys):
        detected_by = sorted(name for name, keys in detector_sets.items() if k in keys)
        if len(detected_by) != len(detector_sets):
            missed_by = sorted(set(detector_sets) - set(detected_by))
            gaps.append({
                "type": "ASSURANCE_GAP",
                "finding": finding_by_key[k],
                "detected_by": detected_by,
                "missed_by": missed_by,
                "recommended_action": "Create or improve native/external rule and add a regression fixture.",
            })

    return {
        "status": "INCONCLUSIVE" if gaps else "PASS",
        "assurance_gaps": gaps,
        "detectors": sorted(detector_sets),
        "reason": (
            f"{len(gaps)} detector-diversity gap(s) require investigation."
            if gaps else "All normalized findings were consistently represented across detectors."
        ),
    }
