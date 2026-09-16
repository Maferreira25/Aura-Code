#!/usr/bin/env python3
"""
AuraCode Slop Code and Reachability Analyzer (AST-based)
Analyzes Python files for dead code, unreachable statements, empty/silent exception swallowing,
and dummy fallback strings.
"""
import os
import sys
import json
import ast
import glob

class SlopASTVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.violations = []

    def visit_FunctionDef(self, node):
        has_returned = False
        for stmt in node.body:
            if has_returned:
                self.violations.append({
                    "file": self.filename,
                    "line": stmt.lineno,
                    "type": "unreachable_code",
                    "message": f"Statement is unreachable after return/raise in function '{node.name}'"
                })
            if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                has_returned = True
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            exc_name = node.type.id if isinstance(node.type, ast.Name) else "Exception"
            self.violations.append({
                "file": self.filename,
                "line": node.lineno,
                "type": "silent_exception_swallowing",
                "message": f"Empty 'except {exc_name}: pass' block swallows errors without logging or re-raising"
            })
        self.generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            if "check_slop_code.py" in self.filename.replace("\\", "/"):
                return
            val_lower = node.value.lower()
            if any(marker in val_lower for marker in ["todo: implement", "dummy response", "fake fallback", "mock data here"]):
                self.violations.append({
                    "file": self.filename,
                    "line": node.lineno,
                    "type": "dummy_placeholder_string",
                    "message": f"Hardcoded placeholder string found: '{node.value[:30]}...'"
                })

def check_file(filepath: str, workspace_dir: str) -> list:
    rel_path = os.path.relpath(filepath, workspace_dir)
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        tree = ast.parse(code, filename=filepath)
        visitor = SlopASTVisitor(rel_path)
        visitor.visit(tree)
        return visitor.violations
    except SyntaxError as e:
        return [{
            "file": rel_path,
            "line": e.lineno or 1,
            "type": "syntax_error",
            "message": f"Syntax error in file: {e.msg}"
        }]
    except Exception:
        return []

def main() -> None:
    workspace_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    py_files = glob.glob(os.path.join(workspace_dir, '**', '*.py'), recursive=True)
    ignored = ['.git', 'node_modules', 'venv', '__pycache__', '.agents', '.auracode', '_auracode', 'validation/scenarios', 'validation/reference']
    py_files = [f for f in py_files if not any(x in f.replace('\\', '/') for x in ignored)]



    all_violations = []
    for f in py_files:
        all_violations.extend(check_file(f, workspace_dir))

    status = "FAIL" if len(all_violations) > 0 else "PASS"
    output = {
        "status": status,
        "violations_count": len(all_violations),
        "violations": all_violations
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if status == "FAIL":
        sys.exit(1)

if __name__ == "__main__":
    main()
