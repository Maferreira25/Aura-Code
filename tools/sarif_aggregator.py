#!/usr/bin/env python3
"""
AuraCode SARIF and External Linter Report Aggregator (Phase 3).
Ingests OASIS SARIF 2.1.0 and custom JSON reports from external static analysis tools
(e.g., ESLint, SpotBugs, GolangCI-Lint, Bandit, Semgrep, PMD, SonarQube)
and normalizes findings into AuraCode assurance evidence format for Gate G2/G3 evaluation.
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional

from tools.assurance_result import build_result


def _attach_canonical_result(result: Dict[str, Any], workspace_dir: str) -> Dict[str, Any]:
    """Attach canonical semantics to a legacy SARIF aggregation result."""
    legacy_status = result.get("status")
    if legacy_status == "ERROR":
        canonical_status = "ERROR"
        reason = str(result.get("error") or "SARIF ingestion failed.")
    elif legacy_status == "FAIL":
        canonical_status = "FAIL"
        reason = "One or more high-severity external findings were reported."
    elif legacy_status == "WARN":
        canonical_status = "INCONCLUSIVE"
        reason = "External findings exist but no policy has yet authorized treating them as PASS."
    elif legacy_status == "PASS":
        canonical_status = "PASS"
        reason = "SARIF report was parsed and contained no findings."
    else:
        canonical_status = "ERROR"
        reason = f"Unknown legacy SARIF status: {legacy_status!r}"

    enriched = dict(result)
    enriched["canonical_result"] = build_result(
        check_id="external-static-analysis",
        status=canonical_status,
        producer_tool="sarif_aggregator",
        producer_method="sarif_2.1.0_ingestion",
        workspace=workspace_dir,
        reason=reason,
        findings=result.get("findings", []) if isinstance(result.get("findings"), list) else [],
        legacy={
            "source": "tools/sarif_aggregator.py",
            "source_status": legacy_status,
        },
    )
    return enriched


class SarifAggregator:
    """Ingests and normalizes SARIF v2.1.0 & JSON linter reports."""

    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_dir = workspace_dir or os.getcwd()

    def parse_sarif_file(self, filepath: str) -> Dict[str, Any]:
        """Parses a SARIF v2.1.0 file and extracts normalized violations."""
        rel_path = os.path.relpath(filepath, self.workspace_dir)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
        except Exception as e:
            return _attach_canonical_result({
                "status": "ERROR",
                "error": f"Failed to parse SARIF JSON file '{rel_path}': {str(e)}",
                "findings": []
            }, self.workspace_dir)

        findings = []
        runs = data.get("runs", [])
        for run in runs:
            tool_name = run.get("tool", {}).get("driver", {}).get("name", "ExternalLinter")
            results = run.get("results", [])

            for res in results:
                rule_id = res.get("ruleId") or res.get("rule", {}).get("id", "LINTER_RULE")
                message = res.get("message", {}).get("text", "Linter finding")
                level = res.get("level", "warning")

                # Map level to AuraCode severity
                severity = "MEDIUM"
                if level in ("error", "high"):
                    severity = "HIGH"
                elif level in ("note", "low", "info"):
                    severity = "LOW"

                locations = res.get("locations", [])
                file_path = rel_path
                line_no = 1

                if locations:
                    phys = locations[0].get("physicalLocation", {})
                    artifact = phys.get("artifactLocation", {}).get("uri", rel_path)
                    file_path = artifact.replace("file://", "").lstrip("/")
                    line_no = phys.get("region", {}).get("startLine", 1)

                findings.append({
                    "tool": tool_name,
                    "rule_id": rule_id,
                    "file": file_path,
                    "line": line_no,
                    "severity": severity,
                    "message": f"[{tool_name}:{rule_id}] {message}"
                })

        status = "FAIL" if any(f["severity"] == "HIGH" for f in findings) else ("WARN" if findings else "PASS")

        return _attach_canonical_result({
            "status": status,
            "sarif_file": rel_path,
            "findings_count": len(findings),
            "findings": findings
        }, self.workspace_dir)


def check_sarif_file(filepath: str, workspace_dir: str) -> Dict[str, Any]:
    aggregator = SarifAggregator(workspace_dir)
    return aggregator.parse_sarif_file(filepath)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: auracode sarif <path-to-report.sarif>")
        sys.exit(1)

    target_file = sys.argv[1]
    workspace_dir = os.getcwd()
    result = check_sarif_file(target_file, workspace_dir)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result.get("status") in ("FAIL", "ERROR"):
        sys.exit(1)


if __name__ == "__main__":
    main()
