#!/usr/bin/env python3
"""AuraCode Comprehensive System Health Audit Engine.

Executes a holistic software assurance audit on an existing or new project:
- AI Slop & Swallowed Exceptions (check_slop_code / multilang_ast)
- Unclosed Resource Leaks (check_resource_leaks / multilang_ast)
- Strict Type Annotations (check_strict_types)
- Security Injection Vectors (check_injection_vectors / multilang_ast)
- Test Suite Integrity & Assertions (check_test_integrity)
- Architectural Boundaries & Contracts (check_architecture)
- Requirement Ambiguity (check_requirements_ambiguity)

Reports each guarantee independently as PASS, FAIL, NOT_RUN,
NOT_APPLICABLE, or ERROR. It intentionally does not calculate a composite
score because missing evidence must never look like approval.
Zero external runtime dependencies (Pure Python Standard Library).
"""

import os
import sys
import json
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.multilang_ast import MultiLangASTAnalyzer, SUPPORTED_EXTENSIONS, HAS_TREE_SITTER
from tools import check_strict_types
from tools import check_test_integrity
from tools import check_architecture
from tools import check_requirements_ambiguity
from tools import traceability_engine
from tools.assurance_result import build_result, normalize_legacy_status


GUARANTEE_KEYS = (
    "security",
    "resource_leaks",
    "slop",
    "strict_types",
    "test_integrity",
    "architecture",
    "requirements",
)


_CANONICAL_CHECKS = {
    "security": ("injection-vectors", "check_injection_vectors"),
    "resource_leaks": ("resource-leaks", "check_resource_leaks"),
    "slop": ("slop", "check_slop_code"),
    "strict_types": ("strict-types", "check_strict_types"),
    "test_integrity": ("test-integrity", "check_test_integrity"),
    "architecture": ("architecture", "check_architecture"),
    "requirements": ("requirements-ambiguity", "check_requirements_ambiguity"),
}

_FINDING_KEYS = {
    "strict_types": "types",
    "test_integrity": "tests",
}


def _canonicalize_guarantees(
    workspace_dir: Path,
    guarantees: Dict[str, Dict[str, Any]],
    findings: Dict[str, List[Dict[str, Any]]],
    languages_detected: Dict[str, int],
) -> List[Dict[str, Any]]:
    """Normalize legacy audit guarantees into canonical shadow-mode results."""
    results: List[Dict[str, Any]] = []
    languages = sorted(languages_detected)
    for key in GUARANTEE_KEYS:
        guarantee = guarantees[key]
        check_id, producer_tool = _CANONICAL_CHECKS[key]
        legacy_status = guarantee.get("status")
        canonical_status = normalize_legacy_status(legacy_status).value
        finding_key = _FINDING_KEYS.get(key, key)
        result_findings = findings.get(finding_key, [])
        if not isinstance(result_findings, list):
            result_findings = []

        results.append(
            build_result(
                check_id=check_id,
                status=canonical_status,
                producer_tool=producer_tool,
                producer_method=str(guarantee.get("method", "unknown")),
                workspace=str(workspace_dir),
                reason=str(guarantee.get("reason") or "Legacy audit guarantee normalized in shadow mode."),
                scope={
                    "files_scanned": int(guarantee.get("files_scanned", 0) or 0),
                    "languages": languages,
                },
                findings=result_findings,
                legacy={
                    "source": "tools/audit.py",
                    "source_status": legacy_status,
                    "guarantee_key": key,
                },
            )
        )
    return results


def _guarantee(
    status: str,
    method: str,
    files_scanned: int = 0,
    findings: int = 0,
    reason: str = "",
) -> Dict[str, Any]:
    """Build one explicit, evidence-oriented guarantee result."""
    return {
        "status": status,
        "method": method,
        "files_scanned": files_scanned,
        "findings": findings,
        "reason": reason,
    }


def _unperformed_guarantees(reason: str) -> Dict[str, Dict[str, Any]]:
    """Return a complete matrix that cannot be mistaken for approval."""
    return {
        key: _guarantee("NOT_RUN", "not_executed", reason=reason)
        for key in GUARANTEE_KEYS
    }


def _overall_status(guarantees: Dict[str, Dict[str, Any]]) -> str:
    """Aggregate by severity without averaging guarantees into a score."""
    statuses = {item["status"] for item in guarantees.values()}
    if "ERROR" in statuses:
        return "ERROR"
    if "FAIL" in statuses:
        return "FAIL"
    if "NOT_RUN" in statuses:
        return "NOT_RUN"
    return "PASS"


def _empty_result(workspace_dir: Path, target_status: str, overall_status: str, reason: str) -> Dict[str, Any]:
    """Return a stable result for invalid or uninspectable targets."""
    guarantees = _unperformed_guarantees(reason)
    empty_findings = {key: [] for key in GUARANTEE_KEYS}
    return {
        "status": overall_status,
        "workspace": str(workspace_dir),
        "target": {"status": target_status, "reason": reason},
        "total_files_scanned": 0,
        "languages_detected": {},
        "guarantees": guarantees,
        "canonical_results": _canonicalize_guarantees(workspace_dir, guarantees, empty_findings, {}),
        "violations_summary": {
            "total_violations": 0,
            "security": 0,
            "resource_leaks": 0,
            "slop_and_swallowed_errors": 0,
            "type_annotations": 0,
            "test_integrity": 0,
            "architecture_violations": None,
            "ambiguity_status": None,
        },
        "findings": {key: [] for key in GUARANTEE_KEYS},
    }


def discover_source_files(workspace_dir: Path, include_benchmarks: bool = False) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    """Discover application files and test files separately in workspace."""
    app_files = []
    test_files = []
    workspace_dir = workspace_dir.resolve()
    ignored_parts = {
        ".git", "node_modules", "dist", "build", "vendor", "out",
        "__pycache__", "venv", ".venv", ".agents", ".auracode", ".next", "_next", ".turbo"
    }
    if not include_benchmarks:
        ignored_parts.update({"validation", "scenarios", "reference"})

    for ext, lang in SUPPORTED_EXTENSIONS.items():
        pattern = str(workspace_dir / "**" / f"*{ext}")
        for f in glob.glob(pattern, recursive=True):
            rel = os.path.relpath(f, str(workspace_dir))
            parts = Path(rel).parts
            if any(
                p in ignored_parts
                or (p.startswith("_auracode_") and p != "_auracode_forward")
                or p.startswith("wheel-")
                or p.endswith(".dist-info")
                or p.startswith("_reversa_")
                for p in parts
            ) or ("auracode" in parts and "studio" in parts and "assets" in parts):
                continue

            fname = Path(f).name.lower()
            is_test = (
                "tests" in parts
                or "__tests__" in parts
                or fname.startswith("test_")
                or fname.endswith("_test.py")
                or fname.endswith(".test.ts")
                or fname.endswith(".spec.ts")
                or fname.endswith(".test.js")
                or fname.endswith(".spec.js")
                or fname.endswith(".test.tsx")
                or fname.endswith(".spec.tsx")
                or fname.endswith("_test.go")
            )
            if is_test:
                test_files.append((f, lang))
            else:
                app_files.append((f, lang))

    return sorted(list(set(app_files))), sorted(list(set(test_files)))


def audit_workspace(workspace_dir: Path, contracts_path: Optional[Path] = None) -> Dict[str, Any]:
    """Execute complete holistic software assurance audit on target workspace."""
    workspace_dir = workspace_dir.resolve()

    if not workspace_dir.exists():
        return _empty_result(workspace_dir, "MISSING", "ERROR", "Target path does not exist.")
    if not workspace_dir.is_dir():
        return _empty_result(workspace_dir, "NOT_DIRECTORY", "ERROR", "Target must be a directory.")

    app_files, test_files = discover_source_files(workspace_dir)
    if not app_files and not test_files:
        return _empty_result(
            workspace_dir,
            "NO_SUPPORTED_FILES",
            "NOT_RUN",
            "No supported application or test files were discovered.",
        )

    analyzer = MultiLangASTAnalyzer(str(workspace_dir))

    slop_violations: List[Dict[str, Any]] = []
    leaks_violations: List[Dict[str, Any]] = []
    sec_violations: List[Dict[str, Any]] = []
    type_violations: List[Dict[str, Any]] = []
    test_violations: List[Dict[str, Any]] = []

    languages_detected: Dict[str, int] = {}
    python_app_files = 0
    non_python_app_files = 0
    python_test_files = 0

    for fpath, lang in app_files:
        languages_detected[lang] = languages_detected.get(lang, 0) + 1
        if lang == "python":
            python_app_files += 1
        else:
            non_python_app_files += 1

        # 1. Slop & Swallowed Exceptions
        s_v = analyzer.analyze_slop(fpath)
        slop_violations.extend(s_v)

        # 2. Resource Leaks
        l_v = analyzer.analyze_leaks(fpath)
        leaks_violations.extend(l_v)

        # 3. Security Vectors
        sec_v = analyzer.analyze_security(fpath)
        sec_violations.extend(sec_v)

        # 4. Strict Types (Python source files - flag missing annotations)
        if lang == "python":
            t_v = check_strict_types.check_file(fpath, str(workspace_dir))
            missing_ann = [v for v in t_v if v.get("type") in ("missing_param_annotation", "missing_return_annotation")]
            type_violations.extend(missing_ann)

    # 5. Test Integrity (Test files)
    for fpath, lang in test_files:
        languages_detected[lang] = languages_detected.get(lang, 0) + 1
        if lang == "python":
            python_test_files += 1
            ti_v = check_test_integrity.check_test_file(fpath)
            test_violations.extend(ti_v)

    # 6. Architecture Layer Contracts
    arch_result: Optional[Dict[str, Any]] = None
    c_candidates = [
        contracts_path if contracts_path else None,
        workspace_dir / ".auracode" / "contracts.json",
        workspace_dir / ".reversa" / "contracts.json",
        workspace_dir / "contracts.json",
        workspace_dir / "architecture.json",
    ]
    resolved_contracts = None
    for c in c_candidates:
        if c and Path(c).is_file():
            resolved_contracts = Path(c)
            break

    if resolved_contracts:
        arch_result = check_architecture.check_architecture(
            workspace_dir, contracts_path=resolved_contracts
        )

    # 7. Requirements Ambiguity
    sdd_dir = workspace_dir / "_auracode_sdd"
    if not sdd_dir.is_dir() and (workspace_dir / "_reversa_sdd").is_dir():
        sdd_dir = workspace_dir / "_reversa_sdd"
    ambiguity_result: Optional[Dict[str, Any]] = None
    if sdd_dir.is_dir() and any(sdd_dir.glob("*.md")):
        ambiguity_result = check_requirements_ambiguity.analyze_workspace(str(sdd_dir))

    traceability_manifest = sdd_dir / "traceability.json"
    if not traceability_manifest.is_file():
        traceability_manifest = workspace_dir / ".auracode" / "traceability.json"
    if traceability_manifest.is_file():
        traceability_result = traceability_engine.evaluate_traceability_file(
            traceability_manifest,
            workspace_dir,
            verify_evidence=True,
        )
    else:
        traceability_result = {
            "status": "NOT_TESTED",
            "progression": {
                "state": "BLOCKED",
                "blocked_by": [
                    {
                        "check_id": "traceability",
                        "status": "NOT_TESTED",
                        "reason": "No traceability manifest was found.",
                    }
                ],
            },
            "canonical_results": [
                build_result(
                    check_id="traceability",
                    control_id="INT-02",
                    status="NOT_TESTED",
                    producer_tool="traceability_engine",
                    producer_method="traceability_graph",
                    workspace=str(workspace_dir),
                    reason="No traceability manifest was found.",
                )
            ],
            "requirements": [],
            "invariants": [],
        }

    if non_python_app_files:
        if HAS_TREE_SITTER:
            source_method = "python_ast_plus_treesitter_cst"
            clean_source_status = "PASS"
            clean_source_reason = (
                "Structural Python AST and Tree-sitter Concrete Syntax Tree (CST) checks completed."
            )
        else:
            source_method = "python_ast_missing_multilang_cst"
            clean_source_status = "NOT_RUN"
            clean_source_reason = (
                "Tree-sitter parser is not installed for non-Python files. "
                "Install with 'pip install auracode[multilang]' to enable multi-language AST/CST guarantees."
            )
    else:
        source_method = "python_ast"
        clean_source_status = "PASS"
        clean_source_reason = "Structural Python AST checks completed."

    def source_guarantee(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        if any(f.get("type") == "parser_unavailable" for f in findings):
            status = "NOT_RUN"
            reason = "Tree-sitter parser unavailable for one or more discovered file types."
        elif findings:
            status = "FAIL"
            reason = clean_source_reason
        else:
            status = clean_source_status
            reason = clean_source_reason
        return _guarantee(
            status,
            source_method,
            files_scanned=len(app_files),
            findings=len(findings),
            reason=reason,
        )

    guarantees: Dict[str, Dict[str, Any]] = {
        "security": source_guarantee(sec_violations),
        "resource_leaks": source_guarantee(leaks_violations),
        "slop": source_guarantee(slop_violations),
    }

    if python_app_files:
        guarantees["strict_types"] = _guarantee(
            "FAIL" if type_violations else "PASS",
            "python_ast",
            files_scanned=python_app_files,
            findings=len(type_violations),
            reason="Strict type signatures checked for Python application files.",
        )
    else:
        guarantees["strict_types"] = _guarantee(
            "NOT_APPLICABLE",
            "python_ast",
            reason="No Python application files were discovered.",
        )

    if python_test_files:
        guarantees["test_integrity"] = _guarantee(
            "FAIL" if test_violations else "PASS",
            "python_ast",
            files_scanned=python_test_files,
            findings=len(test_violations),
            reason="Python test assertions were inspected structurally.",
        )
    else:
        guarantees["test_integrity"] = _guarantee(
            "NOT_RUN",
            "python_ast",
            reason="No structurally supported test files were discovered.",
        )

    if arch_result is None:
        guarantees["architecture"] = _guarantee(
            "NOT_RUN",
            "architecture_contract",
            reason="No architecture contract was found or supplied.",
        )
    else:
        raw_count = arch_result.get("violations_count", 0)
        arch_findings = int(raw_count) if isinstance(raw_count, (int, str)) else 0
        guarantees["architecture"] = _guarantee(
            "PASS" if arch_result.get("success", False) else "FAIL",
            "architecture_contract",
            files_scanned=len(app_files),
            findings=arch_findings,
            reason=f"Contract: {resolved_contracts}",
        )

    if ambiguity_result is None:
        guarantees["requirements"] = _guarantee(
            "NOT_RUN",
            "requirements_supported_marker_scan",
            reason="No non-empty _auracode_sdd or _reversa_sdd directory was found.",
        )
    else:
        requirements_status = "PASS" if ambiguity_result.get("status") == "PASS" else "FAIL"
        ambiguity_findings = len(ambiguity_result.get("unclear_requirements", []))
        guarantees["requirements"] = _guarantee(
            requirements_status,
            "requirements_supported_marker_scan",
            files_scanned=len(list(sdd_dir.glob("*.md"))),
            findings=ambiguity_findings,
            reason=(
                f"Supported ambiguity-marker scan returned {ambiguity_result.get('status')}. "
                "This does not prove requirements completeness or human clarity."
            ),
        )

    total_violations = (
        len(slop_violations)
        + len(leaks_violations)
        + len(sec_violations)
        + len(type_violations)
        + len(test_violations)
    )

    architecture_violations = arch_result.get("violations_count", 0) if arch_result else None
    status = _overall_status(guarantees)

    return {
        "status": status,
        "workspace": str(workspace_dir),
        "target": {"status": "VALID", "reason": "Target exists and supported files were discovered."},
        "total_files_scanned": len(app_files) + len(test_files),
        "languages_detected": languages_detected,
        "guarantees": guarantees,
        "violations_summary": {
            "total_violations": total_violations,
            "security": len(sec_violations),
            "resource_leaks": len(leaks_violations),
            "slop_and_swallowed_errors": len(slop_violations),
            "type_annotations": len(type_violations),
            "test_integrity": len(test_violations),
            "architecture_violations": architecture_violations,
            "ambiguity_status": ambiguity_result.get("status") if ambiguity_result else None,
        },
        "findings": {
            "security": sec_violations,
            "resource_leaks": leaks_violations,
            "slop": slop_violations,
            "types": type_violations,
            "tests": test_violations,
            "architecture": arch_result.get("violations", []) if arch_result else [],
            "requirements": ambiguity_result.get("unclear_requirements", []) if ambiguity_result else [],
        },
        "traceability": traceability_result,
        "canonical_results": (
            _canonicalize_guarantees(
                workspace_dir,
                guarantees,
                {
                    "security": sec_violations,
                    "resource_leaks": leaks_violations,
                    "slop": slop_violations,
                    "types": type_violations,
                    "tests": test_violations,
                    "architecture": arch_result.get("violations", []) if arch_result else [],
                    "requirements": ambiguity_result.get("unclear_requirements", []) if ambiguity_result else [],
                },
                languages_detected,
            )
            + traceability_result.get("canonical_results", [])
        ),
    }


def format_executive_report(audit_data: Dict[str, Any]) -> str:
    """Format an accessible report without grades or false equivalence claims."""
    lines = [
        "=" * 80,
        "   AURA CODE -- LAUDO MESTRE DE AUDITORIA E SAUDE DO SOFTWARE",
        "=" * 80,
        f">> Diretorio Auditado: {audit_data['workspace']}",
        f">> Estado do Alvo: {audit_data['target']['status']}",
        f">> Arquivos Analisados: {audit_data['total_files_scanned']} arquivos",
    ]
    langs = [f"{lang} ({count})" for lang, count in audit_data["languages_detected"].items()]
    lines.append(f">> Linguagens Detectadas: {', '.join(langs) if langs else 'Nenhuma'}")
    lines.extend(["", f"RESULTADO GERAL: {audit_data['status']}", "", "GARANTIAS VERIFICADAS:"])

    labels = {
        "security": "Portaria e fechaduras (seguranca)",
        "resource_leaks": "Instalacao hidraulica (recursos)",
        "slop": "Alvenaria e limpeza (codigo incompleto)",
        "strict_types": "Sinalizacao (tipos)",
        "test_integrity": "Testes de resistencia",
        "architecture": "Estrutura mestra (arquitetura)",
        "requirements": "Planta da casa (requisitos)",
    }
    for key in GUARANTEE_KEYS:
        guarantee = audit_data["guarantees"][key]
        lines.append(
            f" [{guarantee['status']}] {labels[key]}: "
            f"{guarantee['findings']} achado(s), {guarantee['files_scanned']} arquivo(s)"
        )
        if guarantee["reason"]:
            lines.append(f"    Metodo: {guarantee['method']} — {guarantee['reason']}")

    lines.append("")
    if audit_data["status"] == "PASS":
        lines.append("[AUDITORIA CONCLUIDA] Todas as garantias obrigatorias aplicaveis foram executadas e aprovadas.")
    else:
        lines.append("[NAO APROVADO] Falhas ou verificacoes ausentes precisam ser resolvidas antes da publicacao.")
    lines.append("=" * 80 + "\n")
    return "\n".join(lines)


def main() -> None:
    """CLI entrypoint for auracode audit."""
    args = sys.argv[1:]
    target = "."
    is_json = False
    output_file: Optional[Path] = None
    contracts_file: Optional[Path] = None

    strict_mode = False

    i = 0
    while i < len(args):
        a = args[i]
        if a == "--json":
            is_json = True
        elif a == "--strict":
            strict_mode = True
        elif a in ("--output", "-o") and i + 1 < len(args):
            i += 1
            output_file = Path(args[i])
        elif a.startswith("--output="):
            output_file = Path(a.split("=", 1)[1])
        elif a in ("--contracts", "-c") and i + 1 < len(args):
            i += 1
            contracts_file = Path(args[i])
        elif not a.startswith("-"):
            target = a
        i += 1

    res = audit_workspace(Path(target), contracts_path=contracts_file)

    report_str = json.dumps(res, indent=2, ensure_ascii=False) if is_json else format_executive_report(res)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(report_str, encoding="utf-8")
        if not is_json:
            print(f"[AURA AUDIT] Relatorio salvo com sucesso em: {output_file}")

    print(report_str)
    status = res.get("status")
    if status == "PASS":
        sys.exit(0)
    if status == "FAIL":
        sys.exit(1)
    sys.exit(2)


if __name__ == "__main__":
    main()
