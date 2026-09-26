#!/usr/bin/env python3
"""AuraCode Multi-Language Assurance Runner.

Discovers source files across multiple programming languages (Python, TypeScript,
JavaScript, Go, Java, C#), executes deterministic multi-language AST inspection,
and optionally bridges external linter findings into normalized SARIF assurance reports.
Zero external runtime dependencies (Pure Python Standard Library).
"""

import os
import sys
import json
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.multilang_ast import MultiLangASTAnalyzer, SUPPORTED_EXTENSIONS
from tools.sarif_aggregator import SarifAggregator


def scan_multilang_workspace(workspace_dir: Path, target_lang: Optional[str] = None, include_tests: bool = False) -> Dict[str, Any]:
    """Scan workspace across all supported languages and aggregate AST findings."""
    workspace_dir = workspace_dir.resolve()
    analyzer = MultiLangASTAnalyzer(str(workspace_dir))

    ignored_parts = {
        "node_modules", "dist", "build", "vendor", "__pycache__",
        "venv", ".venv", ".agents", ".auracode", "validation", "scenarios", "reference"
    }
    if not include_tests:
        ignored_parts.add("tests")

    all_files = []
    for ext, lang in SUPPORTED_EXTENSIONS.items():
        if target_lang and lang != target_lang.lower():
            continue
        pattern = str(workspace_dir / "**" / f"*{ext}")
        matched = glob.glob(pattern, recursive=True)
        for f in matched:
            rel = os.path.relpath(f, str(workspace_dir))
            parts = Path(rel).parts
            if any(p.startswith(".") or p in ignored_parts for p in parts):
                continue
            all_files.append((f, lang))

    all_files = sorted(list(set(all_files)))

    files_by_lang: Dict[str, int] = {}
    slop_findings: List[Dict[str, Any]] = []
    leaks_findings: List[Dict[str, Any]] = []
    security_findings: List[Dict[str, Any]] = []

    for filepath, lang in all_files:
        files_by_lang[lang] = files_by_lang.get(lang, 0) + 1
        # Run analyzers
        s_violations = analyzer.analyze_slop(filepath)
        l_violations = analyzer.analyze_leaks(filepath)
        sec_violations = analyzer.analyze_security(filepath)

        slop_findings.extend(s_violations)
        leaks_findings.extend(l_violations)
        security_findings.extend(sec_violations)

    total_violations = len(slop_findings) + len(leaks_findings) + len(security_findings)
    status = "PASS" if total_violations == 0 else "FAIL"

    return {
        "status": status,
        "workspace": str(workspace_dir),
        "total_files_scanned": len(all_files),
        "languages_detected": files_by_lang,
        "violations_count": total_violations,
        "slop_violations_count": len(slop_findings),
        "leaks_violations_count": len(leaks_findings),
        "security_violations_count": len(security_findings),
        "findings": {
            "slop": slop_findings,
            "leaks": leaks_findings,
            "security": security_findings,
        }
    }


def main() -> None:
    args = sys.argv[1:]
    target = "."
    target_lang = None
    is_json = False
    include_tests = False

    i = 0
    while i < len(args):
        a = args[i]
        if a == "--json":
            is_json = True
        elif a in ("--include-tests", "--allow-tests"):
            include_tests = True
        elif a.startswith("--lang="):
            target_lang = a.split("=", 1)[1]
        elif a in ("--lang", "-l") and i + 1 < len(args):
            i += 1
            target_lang = args[i]
        elif not a.startswith("-"):
            target = a
        i += 1

    res = scan_multilang_workspace(Path(target), target_lang=target_lang, include_tests=include_tests)
    if is_json:
        print(json.dumps(res, indent=2))
    else:
        print(f"AuraCode Multi-Language Assurance Scan: {res['status']}")
        print(f"Files scanned: {res['total_files_scanned']} across {len(res['languages_detected'])} languages")
        for lang, count in res["languages_detected"].items():
            print(f" - {lang}: {count} files")
        print(f"Total violations: {res['violations_count']}")
        if res["violations_count"] > 0:
            print(f" - Slop / Swallowed Errors: {res['slop_violations_count']}")
            print(f" - Unclosed Resource Leaks: {res['leaks_violations_count']}")
            print(f" - Injection / Security Hazards: {res['security_violations_count']}")

    sys.exit(0 if res["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
