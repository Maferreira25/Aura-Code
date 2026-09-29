#!/usr/bin/env python3
"""
AuraCode Resource Leak AST Analyzer
Scans Python code for unclosed file handles, database connections, sockets, and unmanaged stream resources.
"""
import os
import sys
import json
import ast
import glob

class ResourceLeakVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.leaks = []
        self._with_depth = 0
        self._finally_closed_vars = set()

    def visit_With(self, node):
        self._with_depth += 1
        self.generic_visit(node)
        self._with_depth -= 1

    def visit_AsyncWith(self, node):
        self._with_depth += 1
        self.generic_visit(node)
        self._with_depth -= 1

    def visit_Try(self, node):
        for stmt in node.finalbody:
            for sub in ast.walk(stmt):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr == "close":
                    if isinstance(sub.func.value, ast.Name):
                        self._finally_closed_vars.add(sub.func.value.id)
        self.generic_visit(node)

    def _extract_call_name(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return f"{node.func.value.id}.{node.func.attr}"
            return node.func.attr
        return ""

    def visit_Assign(self, node):
        if self._with_depth == 0 and isinstance(node.value, ast.Call):
            call_func = self._extract_call_name(node.value)
            target_name = ""
            if node.targets and isinstance(node.targets[0], ast.Name):
                target_name = node.targets[0].id

            if target_name and target_name in self._finally_closed_vars:
                self.generic_visit(node)
                return

            monitored = ["open", "sqlite3.connect", "connect", "socket.socket", "requests.Session", "httpx.Client"]
            if call_func in monitored:
                self.leaks.append({
                    "file": self.filename,
                    "line": node.lineno,
                    "type": "potential_unclosed_resource",
                    "resource": call_func,
                    "message": f"Resource allocation '{call_func}' assigned to variable without explicit 'with' context manager or try...finally cleanup"
                })
        self.generic_visit(node)

    def visit_Call(self, node):
        if self._with_depth == 0 and isinstance(node.func, ast.Attribute):
            if node.func.attr in ("read", "readlines", "readline", "write", "writelines"):
                if isinstance(node.func.value, ast.Call):
                    inner_name = self._extract_call_name(node.func.value)
                    if inner_name == "open":
                        self.leaks.append({
                            "file": self.filename,
                            "line": node.lineno,
                            "type": "potential_unclosed_resource",
                            "resource": "open",
                            "message": "Chained 'open().read()' allocates unmanaged stream without explicit 'with' context manager"
                        })
        self.generic_visit(node)

def check_file(filepath: str, workspace_dir: str) -> list:
    from tools.multilang_ast import MultiLangASTAnalyzer
    analyzer = MultiLangASTAnalyzer(workspace_dir)
    return analyzer.analyze_leaks(filepath)

def main() -> None:
    workspace_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    extensions = ['*.py', '*.js', '*.jsx', '*.ts', '*.tsx', '*.go', '*.java', '*.cs']
    target_files = []
    for ext in extensions:
        target_files.extend(glob.glob(os.path.join(workspace_dir, '**', ext), recursive=True))

    ignored = [
        '.git', 'node_modules', 'venv', '.venv', '__pycache__', '.agents',
        '.auracode', 'validation/scenarios', 'validation/reference', 'dist',
        'build', 'out', 'auracode/studio/assets', '_reversa_', '.next', '_next', '.turbo',
        'wheel-', '.dist-info'
    ]
    target_files = [f for f in target_files if not any(x in f.replace('\\', '/') for x in ignored)]

    all_leaks = []
    for f in target_files:
        all_leaks.extend(check_file(f, workspace_dir))

    real_leaks = [l for l in all_leaks if l.get("type") != "parser_unavailable"]
    parser_warnings = [l for l in all_leaks if l.get("type") == "parser_unavailable"]

    status = "FAIL" if len(real_leaks) > 0 else "PASS"
    output = {
        "status": status,
        "leaks_count": len(real_leaks),
        "leaks": real_leaks
    }
    if parser_warnings:
        output["parser_warnings"] = parser_warnings
        output["parser_warnings_count"] = len(parser_warnings)
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if status == "FAIL":
        sys.exit(1)

if __name__ == "__main__":
    main()
