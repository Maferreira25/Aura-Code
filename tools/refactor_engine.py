#!/usr/bin/env python3
"""
AuraCode Refactoring Engine (auracode-refactor).
Analyzes application codebase for refactoring opportunities (dead code/slop removal,
strict type signature completion, resource cleanup, Clean Architecture boundary compliance)
while preserving exact business behavior under test.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.audit import audit_workspace, discover_source_files
from tools.check_strict_types import check_file as check_types_file
from tools.check_slop_code import SlopASTVisitor
import ast


class RefactorEngine:
    """Surgical refactoring planning and verification engine."""

    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = (workspace_dir or Path.cwd()).resolve()

    def analyze_opportunities(self) -> Dict[str, Any]:
        """Scan codebase for high-ROI refactoring opportunities."""
        app_files, _ = discover_source_files(self.workspace_dir)

        type_opportunities = []
        slop_opportunities = []

        for fpath, lang in app_files:
            rel = os.path.relpath(fpath, str(self.workspace_dir))
            if lang == "python":
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Type annotations
                    t_violations = check_types_file(fpath, str(self.workspace_dir))
                    for tv in t_violations:
                        type_opportunities.append({
                            "file": rel,
                            "line": tv.get("line", 1),
                            "action": "ADD_TYPE_ANNOTATION",
                            "message": tv.get("message", "Missing type annotation")
                        })

                    # Slop / swallowed exceptions
                    tree = ast.parse(content, filename=fpath)
                    visitor = SlopASTVisitor(rel)
                    visitor.visit(tree)
                    for sv in visitor.violations:
                        slop_opportunities.append({
                            "file": rel,
                            "line": sv.get("line", 1),
                            "action": "REMOVE_SLOP_OR_HANDLE_ERROR",
                            "message": sv.get("message", "Slop or swallowed error detected")
                        })
                except (OSError, SyntaxError, UnicodeDecodeError):
                    continue

        total_opps = len(type_opportunities) + len(slop_opportunities)
        return {
            "status": "OPPORTUNITIES_IDENTIFIED" if total_opps > 0 else "CLEAN",
            "total_opportunities": total_opps,
            "type_annotations_missing": len(type_opportunities),
            "slop_and_errors_to_clean": len(slop_opportunities),
            "opportunities": {
                "strict_types": type_opportunities[:20],
                "slop": slop_opportunities[:20]
            }
        }

    def generate_plan(self, output_path: Optional[Path] = None) -> Path:
        """Create structured refactoring plan in _auracode_refactor/plan.md."""
        analysis = self.analyze_opportunities()
        ref_dir = self.workspace_dir / "_auracode_refactor"
        ref_dir.mkdir(parents=True, exist_ok=True)
        dest = output_path or (ref_dir / "plan.md")

        md_lines = [
            f"# Aura Code — Plano de Refatoração Cirúrgica (`auracode-refactor`)",
            f"",
            f"> **Status:** {analysis['status']}",
            f"> **Total de Oportunidades:** {analysis['total_opportunities']}",
            f"",
            f"---",
            f"",
            f"## 🎯 Princípios do Refactor",
            f"1. **Zero alteração de comportamento:** Todas as regras de negócio devem ser preservadas.",
            f"2. **Limite Cirúrgico:** Máximo de 500 linhas de alteração por ciclo.",
            f"3. **Garantia AST:** Nenhuma violação nova deve ser introduzida.",
            f"",
            f"---",
            f"",
            f"## 📋 Ações Prioritárias de Alto ROI",
            f"",
            f"### 1. Tipagem Estrita (Total: {analysis['type_annotations_missing']})",
        ]

        if analysis["opportunities"]["strict_types"]:
            for item in analysis["opportunities"]["strict_types"]:
                md_lines.append(f"- [ ] `{item['file']}:{item['line']}` — {item['message']}")
        else:
            md_lines.append("- *(Nenhuma pendência crítica de tipagem encontrada)*")

        md_lines.append(f"\n### 2. Limpeza de Slop e Tratamento de Erros (Total: {analysis['slop_and_errors_to_clean']})")
        if analysis["opportunities"]["slop"]:
            for item in analysis["opportunities"]["slop"]:
                md_lines.append(f"- [ ] `{item['file']}:{item['line']}` — {item['message']}")
        else:
            md_lines.append("- *(Nenhum código morto ou exceção engolida encontrada)*")

        md_lines.extend([
            f"",
            f"---",
            f"",
            f"## 🔍 Verificação Pós-Refatoração",
            f"Após aplicar cada ajuste, execute:",
            f"```bash",
            f"auracode audit .",
            f"pytest",
            f"```",
            f""
        ])

        dest.write_text("\n".join(md_lines), encoding="utf-8")
        return dest


def main() -> None:
    args = sys.argv[1:]
    is_json = "--json" in args
    save_plan = "--save" in args or "--plan" in args

    clean_positionals = [a for a in args if not a.startswith("-")]
    target_dir = Path(clean_positionals[0]).resolve() if clean_positionals else Path.cwd()

    engine = RefactorEngine(workspace_dir=target_dir)
    analysis = engine.analyze_opportunities()

    if save_plan:
        plan_file = engine.generate_plan()
        analysis["plan_file"] = str(plan_file)

    if is_json:
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
    else:
        print(f"\n=======================================================")
        print(f"   AURA CODE — ANÁLISE DE REFATORAÇÃO E MELHORIA")
        print(f"=======================================================")
        print(f"Status: {analysis['status']}")
        print(f"Total de Oportunidades: {analysis['total_opportunities']}")
        print(f" - Tipagem ausente: {analysis['type_annotations_missing']}")
        print(f" - Slop / Erros silenciosos: {analysis['slop_and_errors_to_clean']}")
        if save_plan:
            print(f"\nPlano de refatoração gravado em: {analysis.get('plan_file')}")


if __name__ == "__main__":
    main()
