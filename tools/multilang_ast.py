#!/usr/bin/env python3
"""
AuraCode Multi-Language AST Analysis Engine.
Provides unified Concrete Syntax Tree (CST) and AST static analysis for:
- Python (.py) via Python standard `ast`
- Node.js / TypeScript (.js, .jsx, .ts, .tsx) via Tree-sitter CST
- Go (.go) via Tree-sitter CST
- Java (.java) via Tree-sitter CST
- C# / .NET (.cs) via Tree-sitter CST

Detects AI slop, swallowed exceptions, unclosed resource leaks, and injection vectors across language boundaries.
"""

import os
import ast
from typing import Any, Dict, Generator, List, Optional

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".go": "go",
    ".java": "java",
    ".cs": "csharp",
}

PLACEHOLDER_TERMS = [
    "todo: implement",
    "dummy response",
    "fake fallback",
    "mock data here",
]

SQL_KEYWORDS = ["SELECT ", "INSERT INTO ", "UPDATE ", "DELETE FROM ", "DROP TABLE ", "ALTER TABLE "]


def _is_sql_injection_vector(text: str) -> bool:
    """Check if a string appears to be a dynamic SQL query while ignoring HTML tags like <select>."""
    upper = text.upper()
    if any(kw in upper for kw in ["INSERT INTO ", "DELETE FROM ", "DROP TABLE ", "ALTER TABLE "]):
        return True
    if "UPDATE " in upper and " SET " in upper:
        return True
    if "SELECT " in upper and " FROM " in upper:
        return not ("<SELECT" in upper and upper.count("SELECT ") == upper.count("<SELECT "))
    return False

HAS_TREE_SITTER = False
_PARSERS: Dict[str, Any] = {}
_LANGUAGES: Dict[str, Any] = {}


def _init_tree_sitter() -> None:
    global HAS_TREE_SITTER, _PARSERS, _LANGUAGES
    try:
        import tree_sitter
        import tree_sitter_javascript
        import tree_sitter_typescript
        import tree_sitter_go
        import tree_sitter_java
        import tree_sitter_c_sharp

        langs = {
            "javascript": tree_sitter.Language(tree_sitter_javascript.language()),
            "typescript": tree_sitter.Language(tree_sitter_typescript.language_typescript()),
            "tsx": tree_sitter.Language(tree_sitter_typescript.language_tsx()),
            "go": tree_sitter.Language(tree_sitter_go.language()),
            "java": tree_sitter.Language(tree_sitter_java.language()),
            "csharp": tree_sitter.Language(tree_sitter_c_sharp.language()),
        }
        _LANGUAGES = langs
        _PARSERS = {k: tree_sitter.Parser(v) for k, v in langs.items()}
        HAS_TREE_SITTER = True
    except ImportError:
        HAS_TREE_SITTER = False


_init_tree_sitter()


def _walk_cst(root_node: Any) -> Generator[Any, None, None]:
    if root_node is None:
        return
    stack = [root_node]
    while stack:
        curr = stack.pop()
        yield curr
        if hasattr(curr, "children") and curr.children:
            stack.extend(reversed(curr.children))


class MultiLangASTAnalyzer:
    """Unified analyzer for Python, JavaScript, TypeScript, Go, Java, and C# files using AST & CST."""

    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_dir = workspace_dir or os.getcwd()

    def get_language(self, filepath: str) -> Optional[str]:
        ext = os.path.splitext(filepath)[1].lower()
        return SUPPORTED_EXTENSIONS.get(ext)

    def _parse_cst(self, content: str, lang: str) -> Optional[Any]:
        if not HAS_TREE_SITTER or lang not in _PARSERS:
            return None
        try:
            return _PARSERS[lang].parse(content.encode("utf-8", errors="ignore"))
        except Exception:
            return None

    def analyze_slop(self, filepath: str) -> List[Dict[str, Any]]:
        """Scans Python, JS/TS, Go, Java, or C# files for dead code, swallowed exceptions, and placeholders."""
        lang = self.get_language(filepath)
        if not lang:
            return []

        rel_path = os.path.relpath(filepath, self.workspace_dir)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except (IOError, OSError) as e:
            return [{
                "file": rel_path,
                "line": 1,
                "type": "file_read_error",
                "message": f"Failed to read file: {str(e)}"
            }]

        if lang == "python":
            return self._analyze_slop_python(filepath, rel_path, content)

        if not HAS_TREE_SITTER or lang not in _PARSERS:
            return [{
                "file": rel_path,
                "line": 1,
                "type": "parser_unavailable",
                "message": f"Tree-sitter parser for '{lang}' is not installed. Run 'pip install auracode[multilang]' to enable multi-language AST analysis."
            }]

        tree = self._parse_cst(content, lang)
        if tree is None:
            return []

        if lang in ("javascript", "typescript", "tsx"):
            return self._analyze_slop_jsts_cst(tree, rel_path, content)
        elif lang == "go":
            return self._analyze_slop_go_cst(tree, rel_path, content)
        elif lang == "java":
            return self._analyze_slop_java_cst(tree, rel_path, content)
        elif lang == "csharp":
            return self._analyze_slop_csharp_cst(tree, rel_path, content)

        return []

    def analyze_leaks(self, filepath: str) -> List[Dict[str, Any]]:
        """Scans Python, JS/TS, Go, Java, or C# files for unclosed resource leaks."""
        lang = self.get_language(filepath)
        if not lang:
            return []

        rel_path = os.path.relpath(filepath, self.workspace_dir)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except (IOError, OSError) as e:
            return [{
                "file": rel_path,
                "line": 1,
                "type": "file_read_error",
                "message": f"Failed to read file: {str(e)}"
            }]

        if lang == "python":
            return self._analyze_leaks_python(filepath, rel_path, content)

        if not HAS_TREE_SITTER or lang not in _PARSERS:
            return [{
                "file": rel_path,
                "line": 1,
                "type": "parser_unavailable",
                "message": f"Tree-sitter parser for '{lang}' is not installed. Run 'pip install auracode[multilang]' to enable multi-language AST analysis."
            }]

        tree = self._parse_cst(content, lang)
        if tree is None:
            return []

        if lang in ("javascript", "typescript", "tsx"):
            return self._analyze_leaks_jsts_cst(tree, rel_path, content)
        elif lang == "go":
            return self._analyze_leaks_go_cst(tree, rel_path, content)
        elif lang == "java":
            return self._analyze_leaks_java_cst(tree, rel_path, content)
        elif lang == "csharp":
            return self._analyze_leaks_csharp_cst(tree, rel_path, content)

        return []

    def analyze_security(self, filepath: str) -> List[Dict[str, Any]]:
        """Scans Python, JS/TS, Go, Java, or C# files for injection vectors and security hazards."""
        lang = self.get_language(filepath)
        if not lang:
            return []

        rel_path = os.path.relpath(filepath, self.workspace_dir)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except (IOError, OSError) as e:
            return [{
                "file": rel_path,
                "line": 1,
                "type": "file_read_error",
                "message": f"Failed to read file: {str(e)}"
            }]

        if lang == "python":
            return self._analyze_security_python(filepath, rel_path, content)

        if not HAS_TREE_SITTER or lang not in _PARSERS:
            return [{
                "file": rel_path,
                "line": 1,
                "type": "parser_unavailable",
                "message": f"Tree-sitter parser for '{lang}' is not installed. Run 'pip install auracode[multilang]' to enable multi-language AST analysis."
            }]

        tree = self._parse_cst(content, lang)
        if tree is None:
            return []

        if lang in ("javascript", "typescript", "tsx"):
            return self._analyze_security_jsts_cst(tree, rel_path, content)
        elif lang == "go":
            return self._analyze_security_go_cst(tree, rel_path, content)
        elif lang == "java":
            return self._analyze_security_java_cst(tree, rel_path, content)
        elif lang == "csharp":
            return self._analyze_security_csharp_cst(tree, rel_path, content)

        return []

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
        except Exception as e:
            return [{
                "file": rel_path,
                "line": 1,
                "type": "parse_error",
                "message": f"Failed to parse Python file: {str(e)}"
            }]

    def _analyze_leaks_python(self, filepath: str, rel_path: str, content: str) -> List[Dict[str, Any]]:
        from tools.check_resource_leaks import ResourceLeakVisitor
        try:
            tree = ast.parse(content, filename=filepath)
            visitor = ResourceLeakVisitor(rel_path)
            visitor.visit(tree)
            return visitor.leaks
        except SyntaxError as e:
            return [{
                "file": rel_path,
                "line": e.lineno or 1,
                "type": "syntax_error",
                "message": f"Python syntax error: {str(e)}"
            }]
        except Exception as e:
            return [{
                "file": rel_path,
                "line": 1,
                "type": "parse_error",
                "message": f"Failed to parse Python file: {str(e)}"
            }]

    def _analyze_security_python(self, filepath: str, rel_path: str, content: str) -> List[Dict[str, Any]]:
        from tools.check_injection_vectors import SecurityASTVisitor
        try:
            tree = ast.parse(content, filename=filepath)
            visitor = SecurityASTVisitor(rel_path)
            visitor.visit(tree)
            return visitor.findings
        except SyntaxError as e:
            return [{
                "file": rel_path,
                "line": e.lineno or 1,
                "type": "syntax_error",
                "message": f"Python syntax error: {str(e)}"
            }]
        except Exception as e:
            return [{
                "file": rel_path,
                "line": 1,
                "type": "parse_error",
                "message": f"Failed to parse Python file: {str(e)}"
            }]

    # --- JS/TS/TSX CST Analyzers ---
    def _analyze_slop_jsts_cst(self, tree: Any, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        content_bytes = content.encode("utf-8", errors="ignore")
        for node in _walk_cst(tree.root_node):
            if node.type == "catch_clause":
                body = node.child_by_field_name("body")
                if not body:
                    for c in node.named_children:
                        if c.type == "statement_block":
                            body = c
                            break
                if body:
                    non_comment = [c for c in body.named_children if c.type != "comment"]
                    if len(non_comment) == 0:
                        violations.append({
                            "file": rel_path,
                            "line": node.start_point[0] + 1,
                            "type": "silent_exception_swallowing",
                            "message": "Empty 'catch {}' block swallows errors without logging or re-raising"
                        })
            elif node.type in ("string", "template_string", "comment"):
                text = content_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore").lower()
                for term in PLACEHOLDER_TERMS:
                    if term in text:
                        violations.append({
                            "file": rel_path,
                            "line": node.start_point[0] + 1,
                            "type": "dummy_placeholder_string",
                            "message": f"Hardcoded placeholder string found: '{term}'"
                        })
                        break
        return violations

    def _analyze_leaks_jsts_cst(self, tree: Any, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        content_bytes = content.encode("utf-8", errors="ignore")
        open_nodes = []
        has_close = False
        for node in _walk_cst(tree.root_node):
            if node.type == "call_expression":
                fn = node.child_by_field_name("function")
                if fn:
                    fn_text = content_bytes[fn.start_byte:fn.end_byte].decode("utf-8", errors="ignore")
                    if fn_text in ("fs.openSync", "fs.open", "net.connect", "tls.connect"):
                        open_nodes.append(node)
                    elif fn_text in ("fs.closeSync", "fs.close") or fn_text.endswith(".close") or fn_text.endswith(".destroy"):
                        has_close = True

        if open_nodes and not has_close:
            for onode in open_nodes:
                violations.append({
                    "file": rel_path,
                    "line": onode.start_point[0] + 1,
                    "type": "unclosed_resource_leak",
                    "message": "Resource opened via fs.open/net.connect without corresponding close() call"
                })
        return violations

    def _analyze_security_jsts_cst(self, tree: Any, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        content_bytes = content.encode("utf-8", errors="ignore")
        for node in _walk_cst(tree.root_node):
            if node.type == "call_expression":
                fn = node.child_by_field_name("function")
                if fn:
                    fn_text = content_bytes[fn.start_byte:fn.end_byte].decode("utf-8", errors="ignore")
                    if fn_text == "eval":
                        violations.append({
                            "file": rel_path,
                            "line": node.start_point[0] + 1,
                            "type": "eval_execution",
                            "message": "Dynamic code execution via eval() detected"
                        })
                    elif fn_text in ("child_process.exec", "child_process.execSync", "cp.exec", "cp.execSync"):
                        violations.append({
                            "file": rel_path,
                            "line": node.start_point[0] + 1,
                            "type": "shell_command_injection",
                            "message": "Unchecked shell command execution via child_process.exec() detected"
                        })
            elif node.type == "binary_expression":
                left = node.child_by_field_name("left")
                right = node.child_by_field_name("right")
                if left and right:
                    left_text = content_bytes[left.start_byte:left.end_byte].decode("utf-8", errors="ignore")
                    right_text = content_bytes[right.start_byte:right.end_byte].decode("utf-8", errors="ignore")
                    combined = left_text + " " + right_text
                    if _is_sql_injection_vector(combined) and (left.type == "string" or right.type == "string") and not (left.type == "string" and right.type == "string"):
                        violations.append({
                            "file": rel_path,
                            "line": node.start_point[0] + 1,
                            "type": "sql_injection_vector",
                            "message": "Potential SQL injection vector via string concatenation detected"
                        })
            elif node.type == "template_string":
                text = content_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")
                has_sub = any(c.type == "template_substitution" for c in node.children)
                if has_sub and _is_sql_injection_vector(text):
                    violations.append({
                        "file": rel_path,
                        "line": node.start_point[0] + 1,
                        "type": "sql_injection_vector",
                        "message": "Potential SQL injection vector via string concatenation detected"
                    })
        return violations

    # --- Go CST Analyzers ---
    def _analyze_slop_go_cst(self, tree: Any, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        content_bytes = content.encode("utf-8", errors="ignore")
        for node in _walk_cst(tree.root_node):
            if node.type == "assignment_statement":
                left = node.child_by_field_name("left")
                right = node.child_by_field_name("right")
                if left and right:
                    l_text = content_bytes[left.start_byte:left.end_byte].decode("utf-8", errors="ignore").strip()
                    r_text = content_bytes[right.start_byte:right.end_byte].decode("utf-8", errors="ignore").strip()
                    if l_text == "_" and r_text == "err":
                        violations.append({
                            "file": rel_path,
                            "line": node.start_point[0] + 1,
                            "type": "silent_exception_swallowing",
                            "message": "Ignored error assignment '_ = err' swallows Go error without handling"
                        })
            elif node.type == "if_statement":
                cond = node.child_by_field_name("condition")
                consequence = node.child_by_field_name("consequence")
                if cond and consequence:
                    c_text = content_bytes[cond.start_byte:cond.end_byte].decode("utf-8", errors="ignore")
                    if "err" in c_text and "nil" in c_text:
                        non_comment = [c for c in consequence.named_children if c.type != "comment"]
                        if len(non_comment) == 0:
                            violations.append({
                                "file": rel_path,
                                "line": node.start_point[0] + 1,
                                "type": "silent_exception_swallowing",
                                "message": "Empty 'if err != nil {}' block swallows error silently"
                            })
            elif node.type in ("interpreted_string_literal", "raw_string_literal", "comment"):
                text = content_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore").lower()
                for term in PLACEHOLDER_TERMS:
                    if term in text:
                        violations.append({
                            "file": rel_path,
                            "line": node.start_point[0] + 1,
                            "type": "dummy_placeholder_string",
                            "message": f"Hardcoded placeholder string found: '{term}'"
                        })
                        break
        return violations

    def _analyze_leaks_go_cst(self, tree: Any, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        content_bytes = content.encode("utf-8", errors="ignore")
        open_nodes = []
        has_defer_close = False
        for node in _walk_cst(tree.root_node):
            if node.type == "call_expression":
                fn = node.child_by_field_name("function")
                if fn:
                    fn_text = content_bytes[fn.start_byte:fn.end_byte].decode("utf-8", errors="ignore")
                    if fn_text in ("http.Get", "http.Post", "http.Head", "http.Do", "os.Open", "os.OpenFile", "os.Create"):
                        open_nodes.append(node)
            elif node.type == "defer_statement":
                d_text = content_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")
                if "Close()" in d_text:
                    has_defer_close = True

        if open_nodes and not has_defer_close:
            for onode in open_nodes:
                violations.append({
                    "file": rel_path,
                    "line": onode.start_point[0] + 1,
                    "type": "unclosed_resource_leak",
                    "message": "Resource opened via http/os without corresponding 'defer Close()' call"
                })
        return violations

    def _analyze_security_go_cst(self, tree: Any, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        content_bytes = content.encode("utf-8", errors="ignore")
        for node in _walk_cst(tree.root_node):
            if node.type == "call_expression":
                fn = node.child_by_field_name("function")
                if fn:
                    fn_text = content_bytes[fn.start_byte:fn.end_byte].decode("utf-8", errors="ignore")
                    if fn_text == "exec.Command":
                        args = node.child_by_field_name("arguments")
                        if args:
                            args_text = content_bytes[args.start_byte:args.end_byte].decode("utf-8", errors="ignore")
                            if any(sh in args_text for sh in ('"sh"', '"bash"', '"cmd"', '"powershell"')):
                                violations.append({
                                    "file": rel_path,
                                    "line": node.start_point[0] + 1,
                                    "type": "shell_command_injection",
                                    "message": "Unchecked shell command invocation via exec.Command(sh/bash) detected"
                                })
                    elif fn_text == "fmt.Sprintf":
                        args = node.child_by_field_name("arguments")
                        if args:
                            args_text = content_bytes[args.start_byte:args.end_byte].decode("utf-8", errors="ignore")
                            if any(kw in args_text.upper() for kw in SQL_KEYWORDS) and len(args.named_children) > 1:
                                violations.append({
                                    "file": rel_path,
                                    "line": node.start_point[0] + 1,
                                    "type": "sql_injection_vector",
                                    "message": "Potential SQL injection vector via fmt.Sprintf/string concatenation detected"
                                })
            elif node.type == "binary_expression":
                left = node.child_by_field_name("left")
                right = node.child_by_field_name("right")
                if left and right:
                    left_text = content_bytes[left.start_byte:left.end_byte].decode("utf-8", errors="ignore")
                    right_text = content_bytes[right.start_byte:right.end_byte].decode("utf-8", errors="ignore")
                    has_sql = any(kw in left_text.upper() or kw in right_text.upper() for kw in SQL_KEYWORDS)
                    if has_sql and (left.type.endswith("string_literal") or right.type.endswith("string_literal")):
                        violations.append({
                            "file": rel_path,
                            "line": node.start_point[0] + 1,
                            "type": "sql_injection_vector",
                            "message": "Potential SQL injection vector via fmt.Sprintf/string concatenation detected"
                        })
        return violations

    # --- Java CST Analyzers ---
    def _analyze_slop_java_cst(self, tree: Any, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        content_bytes = content.encode("utf-8", errors="ignore")
        for node in _walk_cst(tree.root_node):
            if node.type == "catch_clause":
                body = node.child_by_field_name("body")
                if body:
                    non_comment = [c for c in body.named_children if "comment" not in c.type]
                    if len(non_comment) == 0:
                        violations.append({
                            "file": rel_path,
                            "line": node.start_point[0] + 1,
                            "type": "silent_exception_swallowing",
                            "message": "Empty catch block swallows Java exception without logging or re-raising"
                        })
            elif node.type in ("string_literal", "line_comment", "block_comment"):
                text = content_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore").lower()
                for term in PLACEHOLDER_TERMS:
                    if term in text:
                        violations.append({
                            "file": rel_path,
                            "line": node.start_point[0] + 1,
                            "type": "dummy_placeholder_string",
                            "message": f"Hardcoded placeholder string found: '{term}'"
                        })
                        break
        return violations

    def _analyze_leaks_java_cst(self, tree: Any, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        content_bytes = content.encode("utf-8", errors="ignore")
        for node in _walk_cst(tree.root_node):
            if node.type == "object_creation_expression":
                type_node = node.child_by_field_name("type")
                if type_node:
                    t_name = content_bytes[type_node.start_byte:type_node.end_byte].decode("utf-8", errors="ignore")
                    if t_name in ("FileInputStream", "FileOutputStream", "FileReader", "FileWriter", "Socket", "ServerSocket"):
                        curr = node.parent
                        inside_try_with_res = False
                        while curr:
                            if curr.type == "try_with_resources_statement":
                                inside_try_with_res = True
                                break
                            curr = curr.parent
                        if not inside_try_with_res and b".close()" not in content_bytes:
                            violations.append({
                                "file": rel_path,
                                "line": node.start_point[0] + 1,
                                "type": "unclosed_resource_leak",
                                "message": "Java resource initialized without try-with-resources / using / Dispose() call"
                            })
        return violations

    def _analyze_security_java_cst(self, tree: Any, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        content_bytes = content.encode("utf-8", errors="ignore")
        for node in _walk_cst(tree.root_node):
            if node.type == "method_invocation":
                m_text = content_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")
                if "Runtime.getRuntime().exec" in m_text:
                    violations.append({
                        "file": rel_path,
                        "line": node.start_point[0] + 1,
                        "type": "shell_command_injection",
                        "message": "Unchecked system command execution in Java detected"
                    })
            elif node.type == "object_creation_expression":
                type_node = node.child_by_field_name("type")
                if type_node:
                    t_name = content_bytes[type_node.start_byte:type_node.end_byte].decode("utf-8", errors="ignore")
                    if t_name == "ProcessBuilder":
                        violations.append({
                            "file": rel_path,
                            "line": node.start_point[0] + 1,
                            "type": "shell_command_injection",
                            "message": "Unchecked system command execution in Java detected"
                        })
            elif node.type == "binary_expression":
                left = node.child_by_field_name("left")
                right = node.child_by_field_name("right")
                if left and right:
                    left_text = content_bytes[left.start_byte:left.end_byte].decode("utf-8", errors="ignore")
                    right_text = content_bytes[right.start_byte:right.end_byte].decode("utf-8", errors="ignore")
                    has_sql = any(kw in left_text.upper() or kw in right_text.upper() for kw in SQL_KEYWORDS)
                    if has_sql and (left.type == "string_literal" or right.type == "string_literal") and not (left.type == "string_literal" and right.type == "string_literal"):
                        violations.append({
                            "file": rel_path,
                            "line": node.start_point[0] + 1,
                            "type": "sql_injection_vector",
                            "message": "Potential SQL injection vector via string concatenation in Java detected"
                        })
        return violations

    # --- C# CST Analyzers ---
    def _analyze_slop_csharp_cst(self, tree: Any, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        content_bytes = content.encode("utf-8", errors="ignore")
        for node in _walk_cst(tree.root_node):
            if node.type == "catch_clause":
                body = node.child_by_field_name("body")
                if body:
                    non_comment = [c for c in body.named_children if "comment" not in c.type]
                    if len(non_comment) == 0:
                        violations.append({
                            "file": rel_path,
                            "line": node.start_point[0] + 1,
                            "type": "silent_exception_swallowing",
                            "message": "Empty catch block swallows Csharp exception without logging or re-raising"
                        })
            elif node.type in ("string_literal", "verbatim_string_literal", "comment"):
                text = content_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore").lower()
                for term in PLACEHOLDER_TERMS:
                    if term in text:
                        violations.append({
                            "file": rel_path,
                            "line": node.start_point[0] + 1,
                            "type": "dummy_placeholder_string",
                            "message": f"Hardcoded placeholder string found: '{term}'"
                        })
                        break
        return violations

    def _analyze_leaks_csharp_cst(self, tree: Any, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        content_bytes = content.encode("utf-8", errors="ignore")
        for node in _walk_cst(tree.root_node):
            if node.type == "object_creation_expression":
                type_node = node.child_by_field_name("type")
                if type_node:
                    t_name = content_bytes[type_node.start_byte:type_node.end_byte].decode("utf-8", errors="ignore")
                    if t_name in ("FileStream", "StreamReader", "StreamWriter", "TcpClient", "DbContext"):
                        curr = node.parent
                        inside_using = False
                        while curr:
                            if curr.type == "using_statement":
                                inside_using = True
                                break
                            if curr.type == "local_declaration_statement":
                                if any(c.type == "using" for c in curr.children):
                                    inside_using = True
                                    break
                            curr = curr.parent
                        if not inside_using and (b".Dispose()" not in content_bytes and b".Close()" not in content_bytes):
                            violations.append({
                                "file": rel_path,
                                "line": node.start_point[0] + 1,
                                "type": "unclosed_resource_leak",
                                "message": "Csharp resource initialized without try-with-resources / using / Dispose() call"
                            })
        return violations

    def _analyze_security_csharp_cst(self, tree: Any, rel_path: str, content: str) -> List[Dict[str, Any]]:
        violations = []
        content_bytes = content.encode("utf-8", errors="ignore")
        for node in _walk_cst(tree.root_node):
            if node.type == "invocation_expression":
                m_text = content_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")
                if "Process.Start" in m_text:
                    violations.append({
                        "file": rel_path,
                        "line": node.start_point[0] + 1,
                        "type": "shell_command_injection",
                        "message": "Unchecked system command execution in Csharp detected"
                    })
            elif node.type == "binary_expression":
                left = node.child_by_field_name("left")
                right = node.child_by_field_name("right")
                if left and right:
                    left_text = content_bytes[left.start_byte:left.end_byte].decode("utf-8", errors="ignore")
                    right_text = content_bytes[right.start_byte:right.end_byte].decode("utf-8", errors="ignore")
                    has_sql = any(kw in left_text.upper() or kw in right_text.upper() for kw in SQL_KEYWORDS)
                    if has_sql and (left.type in ("string_literal", "verbatim_string_literal") or right.type in ("string_literal", "verbatim_string_literal")) and not (left.type.endswith("string_literal") and right.type.endswith("string_literal")):
                        violations.append({
                            "file": rel_path,
                            "line": node.start_point[0] + 1,
                            "type": "sql_injection_vector",
                            "message": "Potential SQL injection vector via string concatenation in Csharp detected"
                        })
            elif node.type == "interpolated_string_expression":
                text = content_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")
                has_sql = any(kw in text.upper() for kw in SQL_KEYWORDS)
                if has_sql:
                    violations.append({
                        "file": rel_path,
                        "line": node.start_point[0] + 1,
                        "type": "sql_injection_vector",
                        "message": "Potential SQL injection vector via string concatenation in Csharp detected"
                    })
        return violations
