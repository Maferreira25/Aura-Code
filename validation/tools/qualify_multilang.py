#!/usr/bin/env python3
"""Run the public Python/TypeScript qualification corpus and emit confusion-matrix evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from tools.multilang_ast import HAS_TREE_SITTER, MultiLangASTAnalyzer


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to read {path}: {exc}")
    if not isinstance(data, dict):
        raise ValueError("qualification corpus root must be an object")
    return data


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_detector(analyzer: MultiLangASTAnalyzer, detector: str, path: Path) -> List[Dict[str, Any]]:
    if detector == "slop":
        return analyzer.analyze_slop(str(path))
    if detector == "leaks":
        return analyzer.analyze_leaks(str(path))
    if detector == "security":
        return analyzer.analyze_security(str(path))
    raise ValueError(f"unsupported detector '{detector}'")


def qualify(corpus_path: Path, revision: str) -> Dict[str, Any]:
    corpus_file = corpus_path.resolve()
    corpus = _read_json(corpus_file)
    thresholds = corpus.get("acceptance_thresholds")
    if not isinstance(thresholds, dict):
        raise ValueError("corpus acceptance_thresholds must be an object")
    cases = corpus.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("qualification corpus requires cases")
    if not revision.strip():
        raise ValueError("revision is required")

    by_language: Dict[str, Dict[str, Any]] = {}
    details: List[Dict[str, Any]] = []

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        analyzer = MultiLangASTAnalyzer(str(root))
        for raw in cases:
            if not isinstance(raw, dict):
                raise ValueError("every qualification case must be an object")
            case_id = str(raw.get("id", "")).strip()
            language = str(raw.get("language", "")).strip().lower()
            suffix = str(raw.get("suffix", "")).strip()
            detector = str(raw.get("detector", "")).strip().lower()
            source = str(raw.get("source", ""))
            expected = raw.get("expected_type")
            if not case_id or language not in {"python", "typescript"} or not suffix or not detector:
                raise ValueError(f"invalid qualification case metadata: {raw}")

            target = root / f"{case_id}{suffix}"
            target.write_text(source, encoding="utf-8")
            findings = _run_detector(analyzer, detector, target)
            observed = [
                str(item.get("type", ""))
                for item in findings
                if isinstance(item, dict) and str(item.get("type", ""))
            ]

            entry = by_language.setdefault(
                language,
                {
                    "cases": 0,
                    "true_positive": 0,
                    "true_negative": 0,
                    "false_positive": 0,
                    "false_negative": 0,
                    "parser_available": True if language == "python" else HAS_TREE_SITTER,
                    "engine": "python-ast" if language == "python" else "tree-sitter-typescript",
                    "evidence": [str(corpus_file)],
                },
            )
            entry["cases"] += 1

            expected_type = str(expected).strip() if expected is not None else ""
            if expected_type:
                outcome = "TP" if expected_type in observed else "FN"
                entry["true_positive" if outcome == "TP" else "false_negative"] += 1
            else:
                outcome = "TN" if not observed else "FP"
                entry["true_negative" if outcome == "TN" else "false_positive"] += 1

            details.append(
                {
                    "case_id": case_id,
                    "language": language,
                    "detector": detector,
                    "expected_type": expected_type or None,
                    "observed_types": observed,
                    "outcome": outcome,
                }
            )

    report: Dict[str, Any] = {
        "study": "MULTILANG_QUALIFICATION",
        "preregistered": bool(corpus.get("preregistered")),
        "revision": revision.strip(),
        "corpus_sha256": _sha256(corpus_file),
        "acceptance_thresholds": thresholds,
        "languages": by_language,
        "cases": details,
        "public_corpus": True,
        "claim_boundary": (
            "This public development corpus qualifies deterministic detector mechanics. "
            "It is not sufficient alone for stable MAT-08 evidence."
        ),
    }

    from validation.tools.maturity_studies import validate_multilang_qualification

    semantic = validate_multilang_qualification(report)
    report["qualification_status"] = semantic["status"]
    report["qualification_errors"] = semantic["errors"]
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AuraCode multi-language qualification harness")
    parser.add_argument(
        "--corpus",
        default="validation/multilang-qualification/corpus.json",
        help="Labeled qualification corpus",
    )
    parser.add_argument("--revision", required=True, help="Immutable source revision under qualification")
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Always exit zero after emitting the qualification report",
    )
    args = parser.parse_args(argv)

    try:
        report = qualify(Path(args.corpus), args.revision)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Multi-language qualification: {report['qualification_status']}")
        for language, values in report["languages"].items():
            print(
                f"- {language}: TP={values['true_positive']} TN={values['true_negative']} "
                f"FP={values['false_positive']} FN={values['false_negative']}"
            )
        for error in report["qualification_errors"]:
            print(f"ERROR: {error}")
        print(report["claim_boundary"])

    if args.report_only:
        return 0
    return 0 if report["qualification_status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
