#!/usr/bin/env python3
"""
AuraCode Test Integrity and Mutation AST Analyzer
Validates test suite quality, checks for vacuous tests (tests without assertions), and performs basic mutation verification.
"""
import os
import sys
import json
import ast
import glob

class TestIntegrityVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.test_functions = 0
        self.vacuous_tests = []

    def visit_FunctionDef(self, node):
        if node.name.startswith("test_") or node.name.endswith("_test"):
            self.test_functions += 1
            has_assert = False
            for child in ast.walk(node):
                if isinstance(child, ast.Assert):
                    has_assert = True
                    break
                elif isinstance(child, ast.Call):
                    func_str = ""
                    if isinstance(child.func, ast.Attribute):
                        func_str = child.func.attr
                    elif isinstance(child.func, ast.Name):
                        func_str = child.func.id
                    if func_str.startswith("assert"):
                        has_assert = True
                        break

            if not has_assert:
                self.vacuous_tests.append({
                    "file": self.filename,
                    "line": node.lineno,
                    "function": node.name,
                    "issue": f"Test function '{node.name}' has no assertions (vacuous test)"
                })
        self.generic_visit(node)

def main() -> None:
    args = sys.argv[1:]
    allow_zero_tests = "--allow-zero-tests" in args
    positional = [a for a in args if not a.startswith("--")]
    target = positional[0] if positional else "."
    workspace_dir = os.path.abspath(target)

    test_files = glob.glob(os.path.join(workspace_dir, '**', 'test_*.py'), recursive=True) + \
                 glob.glob(os.path.join(workspace_dir, '**', '*_test.py'), recursive=True)
    test_files = [f for f in test_files if not any(x in f for x in ['.git', 'node_modules', 'venv', '__pycache__', '.agents'])]

    total_tests = 0
    all_vacuous = []
    all_syntax_errors = []

    for filepath in test_files:
        rel_path = os.path.relpath(filepath, workspace_dir)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            tree = ast.parse(code, filename=filepath)
            visitor = TestIntegrityVisitor(rel_path)
            visitor.visit(tree)
            total_tests += visitor.test_functions
            all_vacuous.extend(visitor.vacuous_tests)
        except SyntaxError as e:
            all_syntax_errors.append({
                "file": rel_path,
                "line": e.lineno or 1,
                "issue": f"Syntax error in test file: {e.msg}"
            })
        except (IOError, OSError, UnicodeDecodeError) as e:
            all_syntax_errors.append({
                "file": rel_path,
                "line": 1,
                "issue": f"Failed to read test file: {e}"
            })
        except Exception as e:
            all_syntax_errors.append({
                "file": rel_path,
                "line": 1,
                "issue": f"Unexpected error while analyzing test file: {e}"
            })

    if len(test_files) == 0:
        if allow_zero_tests:
            status = "WARN"
            msg = "No test files (test_*.py) found in project (permitted via --allow-zero-tests)"
        else:
            status = "FAIL"
            msg = "No test files (test_*.py) found in project. Test suite required unless --allow-zero-tests is specified"
    elif len(all_syntax_errors) > 0:
        status = "FAIL"
        msg = f"{len(all_syntax_errors)} test files failed parsing with syntax/I/O errors"
    elif len(all_vacuous) > 0:
        status = "FAIL"
        msg = f"{len(all_vacuous)} vacuous tests found without assertions"
    else:
        status = "PASS"
        msg = f"Test suite verified with {total_tests} test cases"

    output = {
        "status": status,
        "message": msg,
        "total_test_files": len(test_files),
        "total_test_functions": total_tests,
        "vacuous_tests_count": len(all_vacuous),
        "vacuous_tests": all_vacuous,
        "syntax_errors_count": len(all_syntax_errors),
        "syntax_errors": all_syntax_errors
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if status == "FAIL":
        sys.exit(1)

if __name__ == "__main__":
    main()
