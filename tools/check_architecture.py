#!/usr/bin/env python3
"""AST-based Architectural Linter for AI Software Assurance Framework.

Inspects Python source code against machine-readable contracts (contracts.json)
to enforce Clean Architecture, modular boundaries, and forbidden/allowed imports
without running target code. Zero external dependencies (uses standard library 'ast').
"""

import ast
import argparse
import fnmatch
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ImportVisitor(ast.NodeVisitor):
    """AST Visitor to extract all imports with line and column numbers."""

    def __init__(self):
        self.imports: List[Dict[str, object]] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            top_level = alias.name.split(".")[0]
            self.imports.append({
                "type": "import",
                "module": alias.name,
                "top_level": top_level,
                "is_wildcard": False,
                "lineno": node.lineno,
                "col_offset": node.col_offset,
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        base_mod = node.module or ""
        is_wildcard = any(alias.name == "*" for alias in node.names)
        
        for alias in node.names:
            if base_mod:
                mod_name = base_mod
                top_level = base_mod.split(".")[0]
            else:
                mod_name = alias.name
                top_level = alias.name.split(".")[0]

            self.imports.append({
                "type": "from_import",
                "module": mod_name,
                "base_module": base_mod,
                "top_level": top_level,
                "imported_name": alias.name,
                "is_wildcard": alias.name == "*",
                "lineno": node.lineno,
                "col_offset": node.col_offset,
                "level": node.level,  # > 0 indicates relative import (e.g. from . import foo)
            })
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Intercept dynamic import bypasses like __import__('pkg') or importlib.import_module('pkg')
        target_mod = ""
        if isinstance(node.func, ast.Name) and node.func.id == "__import__":
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                target_mod = node.args[0].value
        elif isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                target_mod = node.args[0].value

        if target_mod:
            self.imports.append({
                "type": "dynamic_import",
                "module": target_mod,
                "base_module": target_mod,
                "top_level": target_mod.split(".")[0],
                "imported_name": target_mod,
                "is_wildcard": False,
                "lineno": node.lineno,
                "col_offset": node.col_offset,
                "level": 0,
            })
        self.generic_visit(node)


def check_pattern_escapes(root_dir: Path, pattern: str) -> bool:
    """Check if a pattern attempts to escape root_dir."""
    pat_path = Path(pattern)
    if pat_path.is_absolute():
        try:
            return not pat_path.resolve().is_relative_to(root_dir)
        except ValueError:
            return True
    prefix_parts = []
    for part in pat_path.parts:
        if any(c in part for c in ["*", "?", "[", "]"]):
            break
        prefix_parts.append(part)
    if prefix_parts:
        try:
            prefix_path = (root_dir / Path(*prefix_parts)).resolve()
            if not prefix_path.is_relative_to(root_dir):
                return True
        except ValueError:
            return True
    return False


def find_files_for_layer(root_dir: Path, pattern: str) -> List[Path]:
    """Find files matching glob/pattern relative to root_dir."""
    files = []
    if "/" not in pattern and "\\" not in pattern:
        matched = list(root_dir.glob(pattern))
        if not matched:
            matched = list(root_dir.rglob(pattern))
        files.extend([p for p in matched if p.is_file() and p.suffix == ".py"])
    else:
        for p in root_dir.glob(pattern):
            if p.is_file() and p.suffix == ".py":
                files.append(p)
            elif p.is_dir():
                files.extend([f for f in p.rglob("*.py") if f.is_file()])
    # Ensure every discovered file is strictly inside root_dir
    safe_files = []
    for f in sorted(list(set(files))):
        try:
            if f.resolve().is_relative_to(root_dir):
                safe_files.append(f)
        except ValueError:
            continue
    return safe_files


def check_file_architecture(
    file_path: Path,
    layer_name: str,
    layer_config: Dict[str, object],
    global_rules: Dict[str, object],
    base_dir: Path,
) -> Tuple[List[Dict[str, object]], Optional[str]]:
    """Check a single python file against layer and global rules."""
    violations: List[Dict[str, object]] = []
    
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [], f"Failed to read {file_path}: {e}"

    lines = content.splitlines()
    line_count = len(lines)
    rel_path = str(file_path.relative_to(base_dir)).replace("\\", "/")

    # Check max file lines
    max_lines = layer_config.get("max_file_lines", global_rules.get("max_file_lines"))
    if max_lines and line_count > max_lines:
        violations.append({
            "file": rel_path,
            "layer": layer_name,
            "lineno": line_count,
            "col_offset": 0,
            "rule": "max_file_lines",
            "message": f"File has {line_count} lines, exceeding limit of {max_lines}",
            "severity": "warning" if line_count < max_lines * 1.5 else "error",
        })

    # Parse AST
    try:
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError as se:
        violations.append({
            "file": rel_path,
            "layer": layer_name,
            "lineno": se.lineno or 1,
            "col_offset": se.offset or 0,
            "rule": "syntax_error",
            "message": f"Python syntax error: {se.msg}",
            "severity": "error",
        })
        return violations, None

    visitor = ImportVisitor()
    visitor.visit(tree)

    forbidden_imports = layer_config.get("forbidden_imports", [])
    allowed_imports = layer_config.get("allowed_imports")
    allow_wildcard = layer_config.get("allow_wildcard_imports", global_rules.get("allow_wildcard_imports", False))

    for imp in visitor.imports:
        if imp["is_wildcard"] and not allow_wildcard:
            violations.append({
                "file": rel_path,
                "layer": layer_name,
                "lineno": imp["lineno"],
                "col_offset": imp["col_offset"],
                "rule": "no_wildcard_imports",
                "message": f"Wildcard import 'from {imp['module']} import *' is forbidden",
                "severity": "error",
            })

        top = imp["top_level"]
        mod = imp["module"]

        # Check forbidden imports
        base_mod = imp.get("base_module", "")
        for forbidden in forbidden_imports:
            if top == forbidden or mod == forbidden or mod.startswith(f"{forbidden}.") or base_mod == forbidden:
                violations.append({
                    "file": rel_path,
                    "layer": layer_name,
                    "lineno": imp["lineno"],
                    "col_offset": imp["col_offset"],
                    "rule": "forbidden_import",
                    "module": mod,
                    "forbidden": forbidden,
                    "message": f"Forbidden import '{mod}' detected in layer '{layer_name}' (rule: {forbidden})",
                    "severity": "error",
                })

        # Check allowed imports whitelist (if configured)
        if allowed_imports is not None:
            is_allowed = False
            for allowed in allowed_imports:
                if top == allowed or mod == allowed or mod.startswith(f"{allowed}.") or base_mod == allowed:
                    is_allowed = True
                    break
            if not is_allowed and (top or mod):
                violations.append({
                    "file": rel_path,
                    "layer": layer_name,
                    "lineno": imp["lineno"],
                    "col_offset": imp["col_offset"],
                    "rule": "disallowed_import",
                    "module": mod,
                    "message": f"Import '{mod}' is not in allowed whitelist for layer '{layer_name}'",
                    "severity": "error",
                })

    return violations, None


def check_architecture(
    target_dir: Path,
    contracts_path: Optional[Path] = None,
    contract_data: Optional[Dict[str, object]] = None,
    max_files: int = 1000,
    max_file_bytes: int = 1_000_000,
    max_depth: int = 20,
) -> Dict[str, object]:
    """Audit target directory against an architectural contract with resource bounds."""
    target_dir = Path(target_dir).resolve()

    if contract_data is None:
        if contracts_path is None:
            candidates = [
                target_dir / "contracts.json",
                target_dir / ".assurance" / "contracts.json",
                target_dir / "architecture.json",
            ]
            for c in candidates:
                if c.exists():
                    contracts_path = c
                    break
        
        if contracts_path is None or not contracts_path.exists():
            return {
                "success": False,
                "complete": False,
                "limit_reasons": [],
                "error": f"No architecture contract file found in {target_dir}. Specify --contracts <path>.",
                "target_directory": str(target_dir),
                "violations_count": 0,
                "violations": [],
                "files_inspected": 0,
                "files_discovered": 0,
            }
        
        try:
            contract_data = json.loads(contracts_path.read_text(encoding="utf-8"))
        except Exception as e:
            return {
                "success": False,
                "complete": False,
                "limit_reasons": [],
                "error": f"Failed to parse contract JSON at {contracts_path}: {e}",
                "target_directory": str(target_dir),
                "violations_count": 0,
                "violations": [],
                "files_inspected": 0,
                "files_discovered": 0,
            }

    layers = contract_data.get("layers", {})
    global_rules = contract_data.get("global_rules", {})
    all_violations: List[Dict[str, object]] = []
    inspected_files = set()
    errors = []
    complete = True
    limit_reasons: List[str] = []

    file_to_layers: Dict[Path, List[Tuple[str, Dict[str, object]]]] = {}

    for layer_name, layer_cfg in layers.items():
        pattern = layer_cfg.get("path", "")
        if not pattern:
            continue

        if check_pattern_escapes(target_dir, pattern):
            complete = False
            limit_reasons.append(f"Pattern '{pattern}' escapes target directory {target_dir}")
            continue

        matched = find_files_for_layer(target_dir, pattern)
        for f in matched:
            if f not in file_to_layers:
                if len(file_to_layers) >= max_files:
                    complete = False
                    limit_reasons.append(f"File count budget ({max_files}) reached")
                    break
                file_to_layers[f] = []
            file_to_layers[f].append((layer_name, layer_cfg))
        if len(file_to_layers) >= max_files and not complete:
            break

    files_discovered_count = len(file_to_layers)

    for f, layer_list in file_to_layers.items():
        try:
            file_size = f.stat().st_size
        except OSError as e:
            errors.append(f"Could not stat {f}: {e}")
            continue

        if file_size > max_file_bytes:
            complete = False
            limit_reasons.append(f"File '{f.name}' size ({file_size} bytes) exceeds limit ({max_file_bytes} bytes)")
            continue

        inspected_files.add(str(f))
        for layer_name, layer_cfg in layer_list:
            viols, err = check_file_architecture(
                f, layer_name, layer_cfg, global_rules, target_dir
            )
            if err:
                errors.append(err)
            all_violations.extend(viols)

    # Sort violations deterministically: file, lineno, col_offset
    all_violations.sort(key=lambda v: (v["file"], v["lineno"], v["col_offset"]))

    # Detect uncontracted Python files in target_dir (REM-025)
    uncontracted_files = []
    ignored_dirs = {".git", "__pycache__", "graphify-out", "dist", "build", ".venv", ".pytest_cache"}
    for py_file in target_dir.rglob("*.py"):
        if not py_file.is_file():
            continue
        rel = py_file.relative_to(target_dir)
        if any(p in ignored_dirs for p in rel.parts) or (rel.parts and rel.parts[0] == ".agents"):
            continue
        if py_file not in file_to_layers:
            uncontracted_files.append(str(rel).replace("\\", "/"))

    uncontracted_files.sort()

    passed = len(all_violations) == 0 and len(errors) == 0 and complete
    return {
        "success": passed,
        "complete": complete,
        "limit_reasons": limit_reasons,
        "project": contract_data.get("project", "unnamed"),
        "assurance_level": contract_data.get("assurance_level", "AL2"),
        "target_directory": str(target_dir),
        "files_discovered": files_discovered_count,
        "files_inspected": len(inspected_files),
        "uncontracted_files": uncontracted_files,
        "violations_count": len(all_violations),
        "violations": all_violations,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify source code against architectural boundary contracts."
    )
    parser.add_argument(
        "target", nargs="?", default=".", help="Directory to inspect (default: current dir)"
    )
    parser.add_argument(
        "--contracts", "-c", type=str, help="Path to contracts.json specification"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results in machine-readable JSON format"
    )
    parser.add_argument(
        "--max-files", type=int, default=1000, help="Maximum number of files to inspect (default: 1000)"
    )
    parser.add_argument(
        "--max-file-bytes", type=int, default=1000000, help="Maximum bytes per file (default: 1000000)"
    )
    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    cpath = Path(args.contracts).resolve() if args.contracts else None

    result = check_architecture(
        target_path,
        cpath,
        max_files=args.max_files,
        max_file_bytes=args.max_file_bytes,
    )

def print_architecture_result(result: dict, target_path: Path, is_json: bool = False) -> int:
    """Format and print architecture inspection result. Returns exit code."""
    if is_json:
        print(json.dumps(result, indent=2))
        if result.get("error"):
            return 2
        return 0 if result.get("success") else 1

    if result.get("error"):
        print(f"ERROR: {result['error']}")
        return 2

    print(f"Architecture Inspection: {result.get('project', 'Project')}")
    print(f"Directory: {result.get('target_directory', str(target_path))}")
    print(f"Files inspected: {result.get('files_inspected', 0)}")
    print(f"Violations detected: {result.get('violations_count', 0)}")
    print("-" * 60)

    for v in result["violations"]:
        print(
            f"{v['file']}:{v['lineno']}:{v['col_offset']}: [{v['rule'].upper()}] in layer '{v['layer']}': {v['message']}"
        )

    if result["errors"]:
        print("-" * 60)
        for err in result["errors"]:
            print(f"ERROR: {err}")

    if result.get("uncontracted_files"):
        print("-" * 60)
        print(f"Notice: {len(result['uncontracted_files'])} uncontracted Python file(s) found outside layer specs:")
        for uf in result["uncontracted_files"][:10]:
            print(f"  ? {uf}")
        if len(result["uncontracted_files"]) > 10:
            print(f"  ... and {len(result['uncontracted_files']) - 10} more")

    if result["success"]:
        print("\nARCHITECTURE CONTRACT SATISFIED")
        return 0
    else:
        print(f"\nARCHITECTURE CONTRACT VIOLATED ({result['violations_count']} issues)")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect Python source code against architectural boundary contracts."
    )
    parser.add_argument(
        "target", nargs="?", default=".", help="Directory to inspect (default: .)"
    )
    parser.add_argument(
        "--contracts", "-c", type=str, help="Path to contracts.json specification"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results in machine-readable JSON format"
    )
    parser.add_argument(
        "--max-files", type=int, default=1000, help="Maximum number of files to inspect (default: 1000)"
    )
    parser.add_argument(
        "--max-file-bytes", type=int, default=1000000, help="Maximum bytes per file (default: 1000000)"
    )
    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    cpath = Path(args.contracts).resolve() if args.contracts else None

    result = check_architecture(
        target_path,
        cpath,
        max_files=args.max_files,
        max_file_bytes=args.max_file_bytes,
    )

    code = print_architecture_result(result, target_path, is_json=args.json)
    sys.exit(code)


if __name__ == "__main__":
    main()
