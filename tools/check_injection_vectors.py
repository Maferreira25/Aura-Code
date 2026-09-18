#!/usr/bin/env python3
"""
AuraCode Security Risk and Injection Vector AST Analyzer
Scans Python code for unsafe code evaluation (`eval`, `exec`), dangerous subprocess calls (`shell=True`),
and unescaped SQL/command string interpolations.
"""
import os
import sys
import json
import ast
import glob

class SecurityASTVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.findings = []

    def visit_Call(self, node):
        func_name = ""
        is_bare_name = isinstance(node.func, ast.Name)
        if is_bare_name:
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        # Dynamic execution check: only bare function calls for 'compile' (re.compile is safe)
        if (is_bare_name and func_name in ["eval", "exec", "compile"]) or (not is_bare_name and func_name in ["eval", "exec"]):
            self.findings.append({
                "file": self.filename,
                "line": node.lineno,
                "severity": "CRITICAL",
                "type": "unsafe_eval_exec",
                "message": f"Dynamic execution using '{func_name}()' exposes codebase to arbitrary code execution"
            })

        if func_name in ["run", "Popen", "call", "check_output"]:
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.findings.append({
                        "file": self.filename,
                        "line": node.lineno,
                        "severity": "HIGH",
                        "type": "command_injection_shell_true",
                        "message": f"Subprocess invocation '{func_name}' with 'shell=True' vulnerable to command injection"
                    })

        self.generic_visit(node)

    def visit_JoinedStr(self, node):
        full_text = ""
        for val in node.values:
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                full_text += val.value
        if any(sql_kw in full_text.upper() for sql_kw in ["SELECT ", "INSERT INTO ", "UPDATE ", "DELETE FROM "]):
            self.findings.append({
                "file": self.filename,
                "line": node.lineno,
                "severity": "HIGH",
                "type": "potential_sql_injection",
                "message": "F-string formatting detected inside SQL statement. Use parameterized queries instead."
            })
        self.generic_visit(node)

def check_file(filepath: str, workspace_dir: str) -> list:
    from tools.multilang_ast import MultiLangASTAnalyzer
    analyzer = MultiLangASTAnalyzer(workspace_dir)
    return analyzer.analyze_security(filepath)

def main() -> None:
    workspace_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    extensions = ['*.py', '*.js', '*.jsx', '*.ts', '*.tsx', '*.go']
    target_files = []
    for ext in extensions:
        target_files.extend(glob.glob(os.path.join(workspace_dir, '**', ext), recursive=True))

    ignored = ['.git', 'node_modules', 'venv', '__pycache__', '.agents', '.auracode', '_auracode', 'validation/scenarios', 'validation/reference']
    target_files = [f for f in target_files if not any(x in f.replace('\\', '/') for x in ignored)]

    all_findings = []
    for f in target_files:
        all_findings.extend(check_file(f, workspace_dir))

    status = "FAIL" if len(all_findings) > 0 else "PASS"
    output = {
        "status": status,
        "findings_count": len(all_findings),
        "findings": all_findings
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if status == "FAIL":
        sys.exit(1)

if __name__ == "__main__":
    main()
