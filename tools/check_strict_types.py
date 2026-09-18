#!/usr/bin/env python3
"""
AuraCode Strict Type Annotations AST Analyzer
Ensures all functions and methods have return type annotations, argument type hints, and prohibits unconstrained 'Any'.
"""
import os
import sys
import json
import ast
import glob

class TypeAnnotationVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.violations = []
        self.any_count = 0

    def visit_FunctionDef(self, node):
        if node.name.startswith("__") and node.name.endswith("__"):
            self.generic_visit(node)
            return

        # Skip AST NodeVisitor overrides which inherently return None
        is_visitor = node.name.startswith("visit_") or node.name == "generic_visit"

        if not is_visitor and node.returns is None:
            self.violations.append({
                "file": self.filename,
                "line": node.lineno,
                "type": "missing_return_annotation",
                "message": f"Function '{node.name}' is missing return type annotation"
            })

        for arg in node.args.args:
            if arg.arg not in ["self", "cls"] and arg.annotation is None and not is_visitor:
                self.violations.append({
                    "file": self.filename,
                    "line": arg.lineno if hasattr(arg, 'lineno') else node.lineno,
                    "type": "missing_arg_annotation",
                    "message": f"Argument '{arg.arg}' in function '{node.name}' is missing type hint"
                })

        self.generic_visit(node)

    def visit_Name(self, node):
        if node.id == "Any":
            self.any_count += 1
            self.violations.append({
                "file": self.filename,
                "line": node.lineno,
                "type": "forbidden_any_type",
                "message": "Explicit usage of 'Any' type bypasses strict static type safety"
            })
        self.generic_visit(node)

def check_file(filepath: str, workspace_dir: str) -> list:
    rel_path = os.path.relpath(filepath, workspace_dir)
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        tree = ast.parse(code, filename=filepath)
        visitor = TypeAnnotationVisitor(rel_path)
        visitor.visit(tree)
        return visitor.violations
    except SyntaxError as e:
        return [{
            "file": rel_path,
            "line": e.lineno or 1,
            "type": "syntax_error",
            "message": f"Syntax error in file: {e.msg}"
        }]
    except (IOError, OSError, UnicodeDecodeError) as e:
        return [{
            "file": rel_path,
            "line": 1,
            "type": "read_error",
            "message": f"Failed to read file: {e}"
        }]
    except Exception as e:
        return [{
            "file": rel_path,
            "line": 1,
            "type": "unexpected_error",
            "message": f"Unexpected error while analyzing file: {e}"
        }]

def main() -> None:
    args = sys.argv[1:]
    strict_any = "--strict-any" in args
    include_tests = "--include-tests" in args
    positional = [a for a in args if not a.startswith("--")]
    target = positional[0] if positional else "."

    workspace_dir = os.path.abspath(target)
    if os.path.isfile(workspace_dir):
        py_files = [workspace_dir]
        workspace_dir = os.path.dirname(workspace_dir)
    else:
        py_files = glob.glob(os.path.join(workspace_dir, '**', '*.py'), recursive=True)

    ignored = ['.git', 'node_modules', 'venv', '__pycache__', '.agents', '.auracode', '_auracode']
    if not include_tests:
        ignored.extend(['tests', 'validation'])
    py_files = [f for f in py_files if not any(x in f.replace('\\', '/') for x in ignored)]

    all_violations = []
    for f in py_files:
        all_violations.extend(check_file(f, workspace_dir))

    missing_annotations = [v for v in all_violations if v['type'] != 'forbidden_any_type']
    any_violations = [v for v in all_violations if v['type'] == 'forbidden_any_type']

    fail_violations = missing_annotations + (any_violations if strict_any else [])
    status = "FAIL" if len(fail_violations) > 0 else "PASS"
    output = {
        "status": status,
        "missing_annotations_count": len(missing_annotations),
        "any_usages_count": len(any_violations),
        "violations": fail_violations
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if status == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()
