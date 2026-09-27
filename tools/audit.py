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

Calculates a unified Health Score (0-100) and formats an executive report
in plain language with physical-world analogies for lay users.
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

from tools.multilang_ast import MultiLangASTAnalyzer, SUPPORTED_EXTENSIONS
from tools import check_strict_types
from tools import check_test_integrity
from tools import check_architecture
from tools import check_requirements_ambiguity


def discover_source_files(workspace_dir: Path, include_benchmarks: bool = False) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    """Discover application files and test files separately in workspace."""
    app_files = []
    test_files = []
    workspace_dir = workspace_dir.resolve()
    ignored_parts = {
        ".git", "node_modules", "dist", "build", "vendor",
        "__pycache__", "venv", ".venv", ".agents", ".auracode"
    }
    if not include_benchmarks:
        ignored_parts.update({"validation", "scenarios", "reference"})

    for ext, lang in SUPPORTED_EXTENSIONS.items():
        pattern = str(workspace_dir / "**" / f"*{ext}")
        for f in glob.glob(pattern, recursive=True):
            rel = os.path.relpath(f, str(workspace_dir))
            parts = Path(rel).parts
            if any(p in ignored_parts for p in parts):
                continue

            fname = Path(f).name.lower()
            if "tests" in parts or fname.startswith("test_") or fname.endswith("_test.py"):
                test_files.append((f, lang))
            else:
                app_files.append((f, lang))

    return sorted(list(set(app_files))), sorted(list(set(test_files)))


def audit_workspace(workspace_dir: Path, contracts_path: Optional[Path] = None) -> Dict[str, Any]:
    """Execute complete holistic software assurance audit on target workspace."""
    workspace_dir = workspace_dir.resolve()
    app_files, test_files = discover_source_files(workspace_dir)

    analyzer = MultiLangASTAnalyzer(str(workspace_dir))

    slop_violations: List[Dict[str, Any]] = []
    leaks_violations: List[Dict[str, Any]] = []
    sec_violations: List[Dict[str, Any]] = []
    type_violations: List[Dict[str, Any]] = []
    test_violations: List[Dict[str, Any]] = []

    languages_detected: Dict[str, int] = {}

    for fpath, lang in app_files:
        languages_detected[lang] = languages_detected.get(lang, 0) + 1

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
    if sdd_dir.is_dir():
        ambiguity_result = check_requirements_ambiguity.analyze_workspace(str(sdd_dir))

    # Calculate Deductions & Health Score (0-100)
    deductions = 0
    deductions += len(sec_violations) * 10
    deductions += len(leaks_violations) * 5
    deductions += len(slop_violations) * 5
    deductions += len(type_violations) * 2
    deductions += len(test_violations) * 5

    if arch_result and not arch_result.get("success", False):
        deductions += int(arch_result.get("violations_count", 0)) * 5

    if ambiguity_result and ambiguity_result.get("status") == "FAIL":
        deductions += 15
    elif ambiguity_result and ambiguity_result.get("status") == "WARN":
        deductions += 5

    health_score = max(0, min(100, 100 - deductions))

    if health_score >= 90:
        grade = "A"
        grade_desc = "Excelente (Conforme com Engenharia Senior)"
    elif health_score >= 75:
        grade = "B"
        grade_desc = "Bom (Pequenos ajustes recomendados)"
    elif health_score >= 50:
        grade = "C"
        grade_desc = "Regular (Debitos tecnicos e atencao necessaria)"
    else:
        grade = "F"
        grade_desc = "Critico (Riscos operacionais ou vulnerabilidades detectadas)"

    total_violations = (
        len(slop_violations)
        + len(leaks_violations)
        + len(sec_violations)
        + len(type_violations)
        + len(test_violations)
    )

    if total_violations == 0:
        status = "PASS"
    elif health_score >= 75 and len(sec_violations) == 0:
        status = "WARN"
    else:
        status = "FAIL"

    return {
        "status": status,
        "health_score": health_score,
        "grade": grade,
        "grade_description": grade_desc,
        "workspace": str(workspace_dir),
        "total_files_scanned": len(app_files) + len(test_files),
        "languages_detected": languages_detected,
        "violations_summary": {
            "total_violations": total_violations,
            "security": len(sec_violations),
            "resource_leaks": len(leaks_violations),
            "slop_and_swallowed_errors": len(slop_violations),
            "type_annotations": len(type_violations),
            "test_integrity": len(test_violations),
            "architecture_violations": arch_result.get("violations_count", 0) if arch_result else None,
            "ambiguity_status": ambiguity_result.get("status") if ambiguity_result else None,
        },
        "findings": {
            "security": sec_violations,
            "resource_leaks": leaks_violations,
            "slop": slop_violations,
            "types": type_violations,
            "tests": test_violations,
            "architecture": arch_result.get("violations", []) if arch_result else [],
            "ambiguity": ambiguity_result.get("unclear_requirements", []) if ambiguity_result else [],
        }
    }


def format_executive_report(audit_data: Dict[str, Any]) -> str:
    """Format an accessible, ASCII-safe executive report with physical analogies."""
    lines = []
    lines.append("=" * 80)
    lines.append("   AURA CODE -- LAUDO MESTRE DE AUDITORIA E SAUDE DO SOFTWARE")
    lines.append("=" * 80)
    lines.append(f">> Diretorio Auditado: {audit_data['workspace']}")
    lines.append(f">> Arquivos Analisados: {audit_data['total_files_scanned']} arquivos")
    
    langs = [f"{lang} ({count})" for lang, count in audit_data["languages_detected"].items()]
    lines.append(f">> Linguagens Detectadas: {', '.join(langs) if langs else 'Nenhuma'}")
    lines.append("")
    lines.append("--------------------------------------------------------------------------------")
    lines.append(f"  PONTUACAO DE SAUDE: {audit_data['health_score']} / 100  [Nota: {audit_data['grade']}]")
    lines.append(f"  Classificacao: {audit_data['grade_description']}")
    lines.append("--------------------------------------------------------------------------------")
    lines.append("")
    lines.append("AVALIACAO POR ANALOGIAS DO MUNDO FISICO:")
    
    v = audit_data["violations_summary"]
    
    # 1. Portaria e Seguranca
    sec_icon = "[OK]" if v["security"] == 0 else "[X]"
    lines.append(f" 1. Portaria e Fechaduras (Seguranca e Injecoes) .............. {sec_icon} {v['security']} falha(s)")
    if v["security"] > 0:
        lines.append("    -> Risco: Portas destrancadas ou entradas sem verificacao (eval, exec, SQL injection).")

    # 2. Instalacao Hidraulica
    leak_icon = "[OK]" if v["resource_leaks"] == 0 else "[X]"
    lines.append(f" 2. Instalacao Hidraulica (Vazamento de Recursos e Conexoes) ... {leak_icon} {v['resource_leaks']} falha(s)")
    if v["resource_leaks"] > 0:
        lines.append("    -> Risco: Torneiras abertas sem fechar ('with' ausente em arquivos e conexoes de banco).")

    # 3. Alvenaria e Acabamento
    slop_icon = "[OK]" if v["slop_and_swallowed_errors"] == 0 else "[X]"
    lines.append(f" 3. Alvenaria e Limpeza (Erros Silenciados e Codigo Morto) ..... {slop_icon} {v['slop_and_swallowed_errors']} falha(s)")
    if v["slop_and_swallowed_errors"] > 0:
        lines.append("    -> Risco: Entulho na obra (funcoes esquecidas ou erros escondidos com 'except: pass').")

    # 4. Sinalizacao e Especificacao
    type_icon = "[OK]" if v["type_annotations"] == 0 else "[X]"
    lines.append(f" 4. Sinalizacao das Portas (Tipagem Estrita e Assinaturas) ..... {type_icon} {v['type_annotations']} falha(s)")
    if v["type_annotations"] > 0:
        lines.append("    -> Risco: Caixas sem etiqueta clara (funcoes sem definicao do que entra e do que sai).")

    # 5. Testes de Carga
    test_icon = "[OK]" if v["test_integrity"] == 0 else "[X]"
    lines.append(f" 5. Testes de Resistencia (Integridade das Assercoes) ......... {test_icon} {v['test_integrity']} falha(s)")
    if v["test_integrity"] > 0:
        lines.append("    -> Risco: Alarmes de teste sem pilha ou sem assercoes reais.")

    # 6. Estrutura do Edificio
    if v["architecture_violations"] is not None:
        arch_icon = "[OK]" if v["architecture_violations"] == 0 else "[X]"
        lines.append(f" 6. Estrutura Mestra (Fronteiras Clean Architecture) .......... {arch_icon} {v['architecture_violations']} falha(s)")
    else:
        lines.append(" 6. Estrutura Mestra (Fronteiras Clean Architecture) .......... [-] Sem contratos definidos")

    # 7. Planta da Casa
    if v["ambiguity_status"] is not None:
        amb_icon = "[OK]" if v["ambiguity_status"] == "PASS" else "[X]"
        lines.append(f" 7. Planta da Casa (Clareza das Especificacoes _auracode_sdd) . {amb_icon} Status: {v['ambiguity_status']}")

    lines.append("")
    lines.append("=" * 80)
    
    if audit_data["health_score"] >= 90:
        lines.append("[SISTEMA APROVADO] Parabens! O codigo atende os mais altos padroes de confiabilidade.")
    else:
        lines.append("[ACOES RECOMENDADAS PARA CORRECAO]:")
        step_num = 1
        if v["security"] > 0:
            lines.append(f"   {step_num}. Execute `auracode sec .` para ver a lista de vulnerabilidades de seguranca.")
            step_num += 1
        if v["resource_leaks"] > 0:
            lines.append(f"   {step_num}. Execute `auracode leaks .` para envolver arquivos e conexoes em blocos `with`.")
            step_num += 1
        if v["slop_and_swallowed_errors"] > 0:
            lines.append(f"   {step_num}. Execute `auracode slop .` para remover 'except: pass' e substituir por tratamento real.")
            step_num += 1
        if v["type_annotations"] > 0:
            lines.append(f"   {step_num}. Execute `auracode types .` para adicionar tipagem estrita nas assinaturas.")
            step_num += 1
        if v["test_integrity"] > 0:
            lines.append(f"   {step_num}. Execute `auracode tests --mutate` para detectar testes fracos ou oraculos viciados.")
            step_num += 1
        lines.append(f"   {step_num}. Apos corrigir, rode `auracode audit .` novamente para verificar o novo Score.")

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
    if strict_mode:
        sys.exit(0 if res.get("status") == "PASS" else 1)
    else:
        sys.exit(0 if res.get("status") in ("PASS", "WARN") else 1)


if __name__ == "__main__":
    main()
