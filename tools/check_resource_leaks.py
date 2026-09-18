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

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call):
            call_func = ""
            if isinstance(node.value.func, ast.Name):
                call_func = node.value.func.id
            elif isinstance(node.value.func, ast.Attribute):
                if isinstance(node.value.func.value, ast.Name):
                    call_func = f"{node.value.func.value.id}.{node.value.func.attr}"
                else:
                    call_func = node.value.func.attr

            if call_func in ["open", "sqlite3.connect", "connect"]:
                self.leaks.append({
                    "file": self.filename,
                    "line": node.lineno,
                    "type": "potential_unclosed_resource",
                    "resource": call_func,
                    "message": f"Resource allocation '{call_func}' assigned to variable without explicit 'with' context manager"
                })
        self.generic_visit(node)

def check_file(filepath: str, workspace_dir: str) -> list:
    from tools.multilang_ast import MultiLangASTAnalyzer
    analyzer = MultiLangASTAnalyzer(workspace_dir)
    return analyzer.analyze_leaks(filepath)

def main() -> None:
    workspace_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    extensions = ['*.py', '*.js', '*.jsx', '*.ts', '*.tsx', '*.go']
    target_files = []
    for ext in extensions:
        target_files.extend(glob.glob(os.path.join(workspace_dir, '**', ext), recursive=True))

    ignored = ['.git', 'node_modules', 'venv', '__pycache__', '.agents', '.auracode', '_auracode', 'validation/scenarios', 'validation/reference']
    target_files = [f for f in target_files if not any(x in f.replace('\\', '/') for x in ignored)]

    all_leaks = []
    for f in target_files:
        all_leaks.extend(check_file(f, workspace_dir))

    status = "FAIL" if len(all_leaks) > 0 else "PASS"
    output = {
        "status": status,
        "leaks_count": len(all_leaks),
        "leaks": all_leaks
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if status == "FAIL":
        sys.exit(1)

if __name__ == "__main__":
    main()
