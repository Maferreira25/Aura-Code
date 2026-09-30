#!/usr/bin/env python3
"""Aura Code native Python taint/data-flow engine.

This engine intentionally starts with a conservative, explainable Python data-flow
model. It tracks tainted function parameters and assignments into sensitive sinks.
Unknown parser/execution conditions fail closed rather than producing PASS.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from tools.assurance_result import build_result, progression_state


_SOURCE_NAMES = {
    "input",
    "request",
    "query",
    "params",
    "form",
    "body",
    "json",
    "headers",
    "cookies",
    "argv",
}

_SINK_NAMES = {
    "eval": "code-exec",
    "exec": "code-exec",
    "system": "command-exec",
    "popen": "command-exec",
    "run": "subprocess",
    "Popen": "subprocess",
    "execute": "sql-exec",
    "executemany": "sql-exec",
}

_SANITIZER_NAMES = {
    "escape",
    "quote",
    "quote_plus",
    "sanitize",
    "clean",
    "validate",
    "int",
    "float",
}


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def _name_of_expr(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Name):
        return node.id
    return None


def _contains_tainted_name(node: ast.AST, tainted: Set[str]) -> Optional[str]:
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id in tainted:
            return child.id
    return None


def _expr_is_sanitized(node: ast.AST) -> bool:
    if isinstance(node, ast.Call):
        name = _call_name(node)
        return name in _SANITIZER_NAMES
    return False


def _fingerprint(file: str, line: int, rule_id: str, source: Optional[str], sink: Optional[str]) -> str:
    raw = f"{file}|{line}|{rule_id}|{source}|{sink}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class _FunctionTaintVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.tainted: Set[str] = set()
        self.findings: List[Dict[str, Any]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        previous = set(self.tainted)
        self.tainted = {arg.arg for arg in node.args.args if arg.arg.lower() not in {"self", "cls"}}
        self.generic_visit(node)
        self.tainted = previous
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Assign(self, node: ast.Assign) -> Any:
        taint_source = _contains_tainted_name(node.value, self.tainted)
        if isinstance(node.value, ast.Call):
            call = _call_name(node.value)
            if call in _SOURCE_NAMES:
                taint_source = call
            if _expr_is_sanitized(node.value):
                taint_source = None
        for target in node.targets:
            name = _name_of_expr(target)
            if name:
                if taint_source:
                    self.tainted.add(name)
                elif name in self.tainted:
                    self.tainted.discard(name)
        self.generic_visit(node)
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
        if node.value is not None:
            taint_source = _contains_tainted_name(node.value, self.tainted)
            if isinstance(node.value, ast.Call) and _expr_is_sanitized(node.value):
                taint_source = None
            name = _name_of_expr(node.target)
            if name:
                if taint_source:
                    self.tainted.add(name)
                elif name in self.tainted:
                    self.tainted.discard(name)
        self.generic_visit(node)
        return node

    def visit_Call(self, node: ast.Call) -> Any:
        sink = _call_name(node)
        if sink in _SINK_NAMES:
            source_name = None
            for arg in list(node.args) + [kw.value for kw in node.keywords]:
                source_name = _contains_tainted_name(arg, self.tainted)
                if source_name:
                    break
            if source_name:
                rule_id = f"taint-{_SINK_NAMES[sink]}"
                severity = "CRITICAL" if _SINK_NAMES[sink] in {"code-exec", "command-exec"} else "HIGH"
                self.findings.append({
                    "fingerprint": _fingerprint(self.rel_path, node.lineno, rule_id, source_name, sink),
                    "rule_id": rule_id,
                    "severity": severity,
                    "file": self.rel_path,
                    "line": node.lineno,
                    "message": f"Tainted value '{source_name}' reaches sensitive sink '{sink}'.",
                    "source": source_name,
                    "sink": sink,
                    "tool": "native-taint",
                })
        self.generic_visit(node)
        return node


def analyze_python_file(path: Path, workspace: Path) -> Dict[str, Any]:
    path = path.resolve()
    workspace = workspace.resolve()
    try:
        rel = path.relative_to(workspace).as_posix()
    except ValueError:
        return {"status": "ERROR", "findings": [], "reason": "Target file escapes workspace."}
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError) as exc:
        return {"status": "ERROR", "findings": [], "reason": f"Unable to parse Python file: {exc}"}

    visitor = _FunctionTaintVisitor(rel)
    visitor.visit(tree)
    return {
        "status": "FAIL" if visitor.findings else "PASS",
        "findings": visitor.findings,
        "reason": "Taint findings detected." if visitor.findings else "No modeled taint flow reached a modeled sink.",
    }


def analyze_workspace(workspace: Path) -> Dict[str, Any]:
    workspace = workspace.resolve()
    if not workspace.is_dir():
        result = build_result(
            check_id="taint-analysis",
            status="ERROR",
            producer_tool="taint_engine",
            producer_method="python_ast_dataflow",
            workspace=str(workspace),
            reason="Workspace does not exist or is not a directory.",
        )
        return {"status": "ERROR", "canonical_result": result, "progression": progression_state([result])}

    targets = [
        p for p in workspace.rglob("*.py")
        if ".git" not in p.parts
        and "__pycache__" not in p.parts
        and "node_modules" not in p.parts
        and "tests" not in p.parts
        and "validation" not in p.parts
    ]
    if not targets:
        result = build_result(
            check_id="taint-analysis",
            status="NOT_TESTED",
            producer_tool="taint_engine",
            producer_method="python_ast_dataflow",
            workspace=str(workspace),
            reason="No supported Python production files were found for taint analysis.",
        )
        return {"status": "NOT_TESTED", "canonical_result": result, "progression": progression_state([result])}

    findings: List[Dict[str, Any]] = []
    parser_errors: List[str] = []
    for path in targets:
        res = analyze_python_file(path, workspace)
        if res["status"] == "ERROR":
            parser_errors.append(f"{path.relative_to(workspace).as_posix()}: {res['reason']}")
        findings.extend(res.get("findings", []))

    if parser_errors:
        status = "ERROR"
        reason = "One or more files could not be analyzed; absence of findings cannot be trusted."
    elif findings:
        status = "FAIL"
        reason = f"{len(findings)} tainted flow(s) reached modeled sensitive sinks."
    else:
        status = "PASS"
        reason = "All supported Python files were analyzed with no modeled taint flow to sensitive sinks."

    result = build_result(
        check_id="taint-analysis",
        status=status,
        control_id="SEC-04",
        producer_tool="taint_engine",
        producer_method="python_ast_dataflow",
        workspace=str(workspace),
        reason=reason,
        severity="CRITICAL" if findings else "HIGH",
        scope={"files_scanned": len(targets), "languages": ["python"]},
        findings=findings,
        legacy={"parser_errors": parser_errors},
    )
    return {
        "status": status,
        "files_scanned": len(targets),
        "findings": findings,
        "parser_errors": parser_errors,
        "canonical_result": result,
        "progression": progression_state([result]),
    }
