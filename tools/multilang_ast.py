#!/usr/bin/env python3
"""
AuraCode Multi-Language AST Analysis Engine.
Provides unified static analysis for Python (.py), Node.js / TypeScript (.js, .jsx, .ts, .tsx), and Go (.go).
Detects AI slop, swallowed exceptions, unclosed resource leaks, and injection vectors across language boundaries.
"""

import os
import re
import ast
import json
from typing import List, Dict, Any, Optional, Tuple

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go"
}

# Try importing tree_sitter if grammars are available
HAS_TREE_SITTER = False
try:
    import tree_sitter
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False


class MultiLangASTAnalyzer:
    """Unified analyzer for Python, JavaScript, TypeScript, and Go files."""

    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_dir = workspace_dir or os.getcwd()

    def get_language(self, filepath: str) -> Optional[str]:
        ext = os.path.splitext(filepath)[1].lower()
        return SUPPORTED_EXTENSIONS.get(ext)

    def analyze_slop(self, filepath: str) -> List[Dict[str, Any]]:
        """Scans Python, JS/TS, or Go files for dead code, swallowed exceptions, and placeholders."""
        lang = self.get_language(filepath)
        if not lang:
            return []

        rel_path = os.path.relpath(filepath, self.workspace_dir)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return []

        violations = []

        if lang == "python":
            violations.extend(self._analyze_slop_python(filepath, rel_path, content))
        elif lang in ("javascript", "typescript"):
            violations.extend(self._analyze_slop_jsts(filepath, rel_path, content))
        elif lang == "go":
            violations.extend(self._analyze_slop_go(filepath, rel_path, content))

        return violations

    def analyze_leaks(self, filepath: str) -> List[Dict[str, Any]]:
        """Scans Python, JS/TS, or Go files for unclosed resource leaks."""
        lang = self.get_language(filepath)
        if not lang:
            return []

        rel_path = os.path.relpath(filepath, self.workspace_dir)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return []

        violations = []
        if lang == "python":
            violations.extend(self._analyze_leaks_python(filepath, rel_path, content))
        elif lang in ("javascript", "typescript"):
            violations.extend(self._analyze_leaks_jsts(filepath, rel_path, content))
        elif lang == "go":
            violations.extend(self._analyze_leaks_go(filepath, rel_path, content))

        return violations

    def analyze_security(self, filepath: str) -> List[Dict[str, Any]]:
        """Scans Python, JS/TS, or Go files for injection vectors and security hazards."""
        lang = self.get_language(filepath)
        if not lang:
            return []

        rel_path = os.path.relpath(filepath, self.workspace_dir)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return []

        violations = []
        if lang == "python":
            violations.extend(self._analyze_security_python(filepath, rel_path, content))
        elif lang in ("javascript", "typescript"):
            violations.extend(self._analyze_security_jsts(filepath, rel_path, content))
        elif lang == "go":
            violations.extend(self._analyze_security_go(filepath, rel_path, content))

        return violations

    # --- Python Analyzers ---
    def _analyze_slop_python(self, filepath: str, rel_path: str, content: str) -> List[Dict[str, Any]]:
        from tools.check_slop_code import SlopASTVisitor
        try:
            tree = ast.parse(content, filename=filepath)
            visitor = SlopASTVisitor(rel_path)
            visitor.visit(tree)
            return visitor.violations
        except SyntaxError as e:
            return [{
                "file": rel_path,
                "line": e.lineno or 1,
                "type": "syntax_error",
                "message": f"Python syntax error: {str(e)}"
            }]
        except Exception:
            return []

    def _analyze_leaks_python(self, filepath: str, rel_path: str, content: str) -> List[Dict[str, Any]]:
        from tools.check_resource_leaks import ResourceLeakVisitor
        try:
            tree = ast.parse(content, filename=filepath)
            visitor = ResourceLeakVisitor(rel_path)
            visitor.visit(tree)
            return visitor.leaks
        except Exception:
            return []

    def _analyze_security_python(self, filepath: str, rel_path: str, content: str) -> List[Dict[str, Any]]:
        from tools.check_injection_vectors import SecurityASTVisitor
        try:
            tree = ast.parse(content, filename=filepath)
            visitor = SecurityASTVisitor(rel_path)
            visitor.visit(tree)
            return visitor.findings
        except Exception:
            return []


    # --- JS/TS Analyzers ---
    def _analyze_slop_jsts(self, filepath: str, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        lines = content.splitlines()

        # Check for empty catch blocks: catch (e) {} or catch {}
        empty_catch_regex = re.compile(r"catch\s*\([^)]*\)\s*\{\s*\}|catch\s*\{\s*\}")
        # Check for placeholders
        placeholder_terms = ["todo: implement", "dummy response", "fake fallback", "mock data here"]

        for idx, line in enumerate(lines, 1):
            if empty_catch_regex.search(line):
                violations.append({
                    "file": rel_path,
                    "line": idx,
                    "type": "silent_exception_swallowing",
                    "message": "Empty 'catch {}' block swallows errors without logging or re-raising"
                })

            line_lower = line.lower()
            for term in placeholder_terms:
                if term in line_lower and ("//" in line or "/*" in line or "'" in line or '"' in line or "`" in line):
                    violations.append({
                        "file": rel_path,
                        "line": idx,
                        "type": "dummy_placeholder_string",
                        "message": f"Hardcoded placeholder string found: '{term}'"
                    })
                    break

        return violations

    def _analyze_leaks_jsts(self, filepath: str, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        lines = content.splitlines()

        # Check unclosed fs.openSync or fs.open without close
        open_regex = re.compile(r"\b(fs\.openSync|fs\.open|net\.connect|tls\.connect)\b")
        close_regex = re.compile(r"\b(fs\.closeSync|fs\.close|\.close\(\)|\.destroy\(\))\b")

        has_open = False
        open_line = 1
        for idx, line in enumerate(lines, 1):
            if open_regex.search(line):
                has_open = True
                open_line = idx

        if has_open and not close_regex.search(content):
            violations.append({
                "file": rel_path,
                "line": open_line,
                "type": "unclosed_resource_leak",
                "message": "Resource opened via fs.open/net.connect without corresponding close() call"
            })

        return violations

    def _analyze_security_jsts(self, filepath: str, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        lines = content.splitlines()

        eval_regex = re.compile(r"\beval\s*\(")
        exec_regex = re.compile(r"\b(child_process|cp)\.(exec|execSync)\s*\(")
        sql_concat_regex = re.compile(r"SELECT\s+.*\s+FROM\s+.*\s*\+\s*|INSERT\s+INTO\s+.*\s*\+\s*|UPDATE\s+.*\s+SET\s+.*\s*\+\s*|DELETE\s+FROM\s+.*\s*\+\s*", re.IGNORECASE)

        for idx, line in enumerate(lines, 1):
            if eval_regex.search(line):
                violations.append({
                    "file": rel_path,
                    "line": idx,
                    "type": "eval_execution",
                    "message": "Dynamic code execution via eval() detected"
                })
            if exec_regex.search(line):
                violations.append({
                    "file": rel_path,
                    "line": idx,
                    "type": "shell_command_injection",
                    "message": "Unchecked shell command execution via child_process.exec() detected"
                })
            if sql_concat_regex.search(line):
                violations.append({
                    "file": rel_path,
                    "line": idx,
                    "type": "sql_injection_vector",
                    "message": "Potential SQL injection vector via string concatenation detected"
                })

        return violations

    # --- Go Analyzers ---
    def _analyze_slop_go(self, filepath: str, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        lines = content.splitlines()

        # Swallowed err: _ = err or empty if err != nil {}
        ignored_err_regex = re.compile(r"_\s*=\s*err\b")
        empty_err_if_regex = re.compile(r"if\s+err\s*!=\s*nil\s*\{\s*\}")
        placeholder_terms = ["todo: implement", "dummy response", "fake fallback", "mock data here"]

        for idx, line in enumerate(lines, 1):
            if ignored_err_regex.search(line):
                violations.append({
                    "file": rel_path,
                    "line": idx,
                    "type": "silent_exception_swallowing",
                    "message": "Ignored error assignment '_ = err' swallows Go error without handling"
                })
            if empty_err_if_regex.search(line):
                violations.append({
                    "file": rel_path,
                    "line": idx,
                    "type": "silent_exception_swallowing",
                    "message": "Empty 'if err != nil {}' block swallows error silently"
                })

            line_lower = line.lower()
            for term in placeholder_terms:
                if term in line_lower:
                    violations.append({
                        "file": rel_path,
                        "line": idx,
                        "type": "dummy_placeholder_string",
                        "message": f"Hardcoded placeholder string found: '{term}'"
                    })
                    break

        return violations

    def _analyze_leaks_go(self, filepath: str, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        lines = content.splitlines()

        # Check http.Get / os.Open / os.OpenFile without defer Body.Close() / defer f.Close()
        open_http_regex = re.compile(r"http\.(Get|Post|Head|Do)\s*\(")
        open_file_regex = re.compile(r"os\.(Open|OpenFile|Create)\s*\(")
        defer_close_regex = re.compile(r"defer\s+.*\.(Close\(\)|Body\.Close\(\))")

        has_http_open = False
        has_file_open = False
        open_line = 1

        for idx, line in enumerate(lines, 1):
            if open_http_regex.search(line):
                has_http_open = True
                open_line = idx
            if open_file_regex.search(line):
                has_file_open = True
                open_line = idx

        if (has_http_open or has_file_open) and not defer_close_regex.search(content):
            violations.append({
                "file": rel_path,
                "line": open_line,
                "type": "unclosed_resource_leak",
                "message": "Resource opened via http/os without corresponding 'defer Close()' call"
            })

        return violations

    def _analyze_security_go(self, filepath: str, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        lines = content.splitlines()

        exec_cmd_regex = re.compile(r"exec\.Command\s*\(\s*\"(sh|bash|cmd|powershell)\"")
        sql_concat_regex = re.compile(r"SELECT\s+.*\s+FROM\s+.*\s*\+\s*|INSERT\s+INTO\s+.*\s*\+\s*|fmt\.Sprintf\s*\(\s*\"SELECT", re.IGNORECASE)

        for idx, line in enumerate(lines, 1):
            if exec_cmd_regex.search(line):
                violations.append({
                    "file": rel_path,
                    "line": idx,
                    "type": "shell_command_injection",
                    "message": "Unchecked shell command invocation via exec.Command(sh/bash) detected"
                })
            if sql_concat_regex.search(line):
                violations.append({
                    "file": rel_path,
                    "line": idx,
                    "type": "sql_injection_vector",
                    "message": "Potential SQL injection vector via fmt.Sprintf/string concatenation detected"
                })

        return violations
