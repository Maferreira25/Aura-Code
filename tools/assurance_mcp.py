#!/usr/bin/env python3
"""Native Stdio MCP (Model Context Protocol) Server for AI Software Assurance.

Provides active software assurance guardrail tools to any MCP-compatible client
(Antigravity IDE, Cursor, Claude Desktop, VS Code) via standard JSON-RPC 2.0 over stdio.
Zero external dependencies (pure Python standard library).
"""

import json
import sys
import os
import ast
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Union

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.check_architecture import check_architecture
from tools.verify_dependencies import verify_package, verify_requirements_file
from tools.check_surgical_diff import check_surgical_diff
import tools.check_slop_code as check_slop_code
import tools.check_resource_leaks as check_resource_leaks
import tools.check_strict_types as check_strict_types
import tools.check_test_integrity as check_test_integrity
import tools.check_injection_vectors as check_injection_vectors
import tools.check_requirements_ambiguity as check_requirements_ambiguity


SERVER_NAME = "auracode-mcp"
SERVER_VERSION = "0.1.1"
PROTOCOL_VERSION = "2024-11-05"


TOOLS_MANIFEST = [
    {
        "name": "check_architecture",
        "description": "Inspect source code against architecture contracts (contracts.json) to verify Clean Architecture and layer boundary rules using AST.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_directory": {
                    "type": "string",
                    "description": "Path to the project directory to inspect"
                },
                "contracts_path": {
                    "type": "string",
                    "description": "Optional path to the contracts.json specification file"
                }
            },
            "required": ["target_directory"]
        }
    },
    {
        "name": "verify_dependency",
        "description": "Verify a Python package against official PyPI registry to prevent AI hallucinations, invalid versions, and supply chain risks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "package_name": {
                    "type": "string",
                    "description": "Name of the Python package to check"
                },
                "requested_version": {
                    "type": "string",
                    "description": "Optional specific version to verify against published releases"
                },
                "offline": {
                    "type": "boolean",
                    "description": "Run in offline mode (only check stdlib collision)",
                    "default": False
                }
            },
            "required": ["package_name"]
        }
    },
    {
        "name": "verify_requirements",
        "description": "Verify all packages in a requirements.txt file against PyPI to identify any hallucinated dependencies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirements_path": {
                    "type": "string",
                    "description": "Path to requirements.txt file"
                },
                "offline": {
                    "type": "boolean",
                    "description": "Run in offline mode",
                    "default": False
                }
            },
            "required": ["requirements_path"]
        }
    },
    {
        "name": "check_surgical_diff",
        "description": "Analyze git diff to ensure changes are surgical, strictly bounded within authorized scope, and do not tamper with tests.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_directory": {
                    "type": "string",
                    "description": "Path to the git repository root"
                },
                "allowed_scope": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of glob patterns allowed to be modified"
                },
                "allow_test_modifications": {
                    "type": "boolean",
                    "description": "Whether modifying test files is permitted (default: false to prevent reward hacking)",
                    "default": False
                }
            },
            "required": ["repo_directory"]
        }
    },
    {
        "name": "check_slop",
        "description": "Scan Python AST for dead code, unreachable statements, and swallowed errors.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_directory": {
                    "type": "string",
                    "description": "Target workspace or file path"
                }
            }
        }
    },
    {
        "name": "check_leaks",
        "description": "Scan Python AST for unclosed resource leaks (file handles, sockets, DBs).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_directory": {
                    "type": "string",
                    "description": "Target workspace or file path"
                }
            }
        }
    },
    {
        "name": "check_types",
        "description": "Scan Python AST for strict type hints and annotations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_directory": {
                    "type": "string",
                    "description": "Target workspace or file path"
                }
            }
        }
    },
    {
        "name": "check_tests",
        "description": "Scan test suite integrity and detect vacuous tests without assertions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_directory": {
                    "type": "string",
                    "description": "Target workspace or file path"
                }
            }
        }
    },
    {
        "name": "check_security",
        "description": "Scan Python AST for injection vectors, eval/exec, and shell=True risks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_directory": {
                    "type": "string",
                    "description": "Target workspace or file path"
                }
            }
        }
    },
    {
        "name": "check_ambiguity",
        "description": "Evaluate requirement ambiguity and non-technical questions (Gate G1).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_directory": {
                    "type": "string",
                    "description": "Target workspace or file path"
                }
            }
        }
    }
]


def handle_initialize(req_id: Union[str, int, None], params: Dict[str, object]) -> Dict[str, object]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION
            }
        }
    }


def handle_tools_list(req_id: Union[str, int, None]) -> Dict[str, object]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "tools": TOOLS_MANIFEST
        }
    }


def validate_path_in_root(p: Path, root: Optional[Path]) -> Tuple[bool, Optional[str]]:
    """Verify that path p is inside allowed root directory."""
    if root is None:
        return True, None
    try:
        resolved = p.resolve()
        resolved_root = root.resolve()
        if not resolved.is_relative_to(resolved_root):
            return False, f"Path '{p}' ({resolved}) is outside allowed root '{root}' ({resolved_root})"
    except Exception as e:
        return False, f"Failed to validate path '{p}': {e}"
    return True, None


def handle_tools_call(req_id: Union[str, int, None], params: Dict[str, object], allowed_root: Optional[Path] = None) -> Dict[str, object]:
    if not isinstance(params, dict):
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32602, "message": "Invalid params: params must be a JSON object"}
        }

    name = params.get("name")
    args = params.get("arguments", {})
    if not isinstance(args, dict):
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32602, "message": "Invalid params: arguments must be an object"}
        }

    try:
        if name == "check_architecture":
            target = Path(args.get("target_directory", ".")).resolve()
            ok, err = validate_path_in_root(target, allowed_root)
            if not ok:
                raise PermissionError(err)

            cpath = None
            if args.get("contracts_path"):
                cpath = Path(args["contracts_path"]).resolve()
                ok, err = validate_path_in_root(cpath, allowed_root)
                if not ok:
                    raise PermissionError(err)

            max_f = args.get("max_files", 1000)
            max_b = args.get("max_file_bytes", 1000000)
            res = check_architecture(target, contracts_path=cpath, max_files=max_f, max_file_bytes=max_b)
        elif name == "verify_dependency":
            pkg = args["package_name"]
            ver = args.get("requested_version")
            off = args.get("offline", False)
            res = verify_package(pkg, requested_version=ver, offline=off)
        elif name == "verify_requirements":
            req_path = Path(args["requirements_path"]).resolve()
            ok, err = validate_path_in_root(req_path, allowed_root)
            if not ok:
                raise PermissionError(err)

            off = args.get("offline", False)
            max_b = args.get("max_file_bytes", 100000)
            max_p = args.get("max_packages", 100)
            tot_to = args.get("total_timeout", 30.0)
            res = verify_requirements_file(
                req_path,
                offline=off,
                max_file_bytes=max_b,
                max_packages=max_p,
                total_timeout=tot_to,
            )
        elif name == "check_surgical_diff":
            repo = Path(args.get("repo_directory", ".")).resolve()
            ok, err = validate_path_in_root(repo, allowed_root)
            if not ok:
                raise PermissionError(err)

            scope = args.get("allowed_scope")
            allow_tests = args.get("allow_test_modifications", False)
            res = check_surgical_diff(repo, allowed_scope=scope, allow_test_modifications=allow_tests)
        elif name == "check_slop":
            target = Path(args.get("target_directory", ".")).resolve()
            ok, err = validate_path_in_root(target, allowed_root)
            if not ok:
                raise PermissionError(err)
            py_files = list(target.rglob("*.py")) if target.is_dir() else [target]
            ignored = ['.git', 'node_modules', 'venv', '__pycache__', '.agents', '.auracode', '_auracode', 'validation/scenarios', 'validation/reference']
            py_files = [str(f) for f in py_files if not any(x in str(f).replace('\\', '/') for x in ignored)]
            violations = [v for f in py_files for v in check_slop_code.check_file(f, str(target))]
            res = {"status": "FAIL" if violations else "PASS", "violations_count": len(violations), "violations": violations}
        elif name == "check_leaks":
            target = Path(args.get("target_directory", ".")).resolve()
            ok, err = validate_path_in_root(target, allowed_root)
            if not ok:
                raise PermissionError(err)
            py_files = list(target.rglob("*.py")) if target.is_dir() else [target]
            ignored = ['.git', 'node_modules', 'venv', '__pycache__', '.agents', '.auracode', '_auracode', 'validation/scenarios', 'validation/reference']
            py_files = [str(f) for f in py_files if not any(x in str(f).replace('\\', '/') for x in ignored)]
            leaks = [l for f in py_files for l in check_resource_leaks.check_file(f, str(target))]
            res = {"status": "FAIL" if leaks else "PASS", "leaks_count": len(leaks), "leaks": leaks}
        elif name == "check_types":
            target = Path(args.get("target_directory", ".")).resolve()
            ok, err = validate_path_in_root(target, allowed_root)
            if not ok:
                raise PermissionError(err)
            py_files = list(target.rglob("*.py")) if target.is_dir() else [target]
            ignored = ['.git', 'node_modules', 'venv', '__pycache__', '.agents', '.auracode', '_auracode', 'tests', 'validation']
            py_files = [str(f) for f in py_files if not any(x in str(f).replace('\\', '/') for x in ignored)]
            all_v = [v for f in py_files for v in check_strict_types.check_file(f, str(target))]
            missing = [v for v in all_v if v["type"] != "forbidden_any_type"]
            res = {"status": "FAIL" if missing else "PASS", "missing_annotations_count": len(missing), "violations": missing}
        elif name == "check_tests":
            target = Path(args.get("target_directory", ".")).resolve()
            ok, err = validate_path_in_root(target, allowed_root)
            if not ok:
                raise PermissionError(err)
            test_files = list(target.rglob("test_*.py")) + list(target.rglob("*_test.py"))
            test_files = [str(f) for f in test_files if not any(x in str(f) for x in ['.git', 'node_modules', 'venv', '__pycache__', '.agents'])]
            total_t = 0
            all_vac = []
            for tf in test_files:
                try:
                    code = Path(tf).read_text(encoding="utf-8", errors="ignore")
                    tree = ast.parse(code, filename=tf)
                    vis = check_test_integrity.TestIntegrityVisitor(os.path.relpath(tf, str(target)))
                    vis.visit(tree)
                    total_t += vis.test_functions
                    all_vac.extend(vis.vacuous_tests)
                except Exception:
                    continue
            res = {"status": "FAIL" if all_vac else "PASS", "total_tests": total_t, "vacuous_count": len(all_vac), "vacuous_tests": all_vac}
        elif name == "check_security":
            target = Path(args.get("target_directory", ".")).resolve()
            ok, err = validate_path_in_root(target, allowed_root)
            if not ok:
                raise PermissionError(err)
            py_files = list(target.rglob("*.py")) if target.is_dir() else [target]
            ignored = ['.git', 'node_modules', 'venv', '__pycache__', '.agents', '.auracode', '_auracode', 'validation/scenarios', 'validation/reference']
            py_files = [str(f) for f in py_files if not any(x in str(f).replace('\\', '/') for x in ignored)]
            findings = [fd for f in py_files for fd in check_injection_vectors.check_file(f, str(target))]
            res = {"status": "FAIL" if findings else "PASS", "critical_vulnerabilities_count": len(findings), "findings": findings}
        elif name == "check_ambiguity":
            target = Path(args.get("target_directory", ".")).resolve()
            ok, err = validate_path_in_root(target, allowed_root)
            if not ok:
                raise PermissionError(err)
            res = check_requirements_ambiguity.analyze_workspace(str(target))
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Tool '{name}' not found"
                }
            }

        is_error = not res.get("success", True) if "success" in res else res.get("is_hallucinated", False)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(res, indent=2)
                    }
                ],
                "isError": bool(is_error)
            }
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"Execution error in tool '{name}': {str(e)}"
                    }
                ],
                "isError": True
            }
        }


def process_message(
    msg_str: str,
    max_message_bytes: int = 1_000_000,
    allowed_root: Optional[Path] = None,
    permit_unrestricted: bool = False,
) -> Optional[Dict[str, object]]:
    """Process a single JSON-RPC message and return response dict if appropriate."""
    effective_root = allowed_root if (allowed_root is not None or permit_unrestricted) else Path.cwd().resolve()
    msg_str = msg_str.strip()
    if not msg_str:
        return None

    raw_bytes = msg_str.encode("utf-8") if isinstance(msg_str, str) else msg_str
    if len(raw_bytes) > max_message_bytes:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32001,
                "message": f"Message size ({len(raw_bytes)} bytes) exceeds limit ({max_message_bytes} bytes)"
            }
        }

    try:
        msg = json.loads(msg_str)
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": f"Parse error: {e}"}
        }

    if not isinstance(msg, dict):
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32600, "message": "Invalid Request: expected a JSON object"}
        }

    req_id = msg.get("id")
    method = msg.get("method")

    if "params" in msg and not isinstance(msg["params"], dict):
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32602, "message": "Invalid params: expected object"}
        }
    params = msg.get("params", {})

    # Handle notifications (no id)
    if req_id is None and method:
        if method == "notifications/initialized":
            return None
        return None

    if method == "initialize":
        return handle_initialize(req_id, params)
    elif method == "tools/list":
        return handle_tools_list(req_id)
    elif method == "tools/call":
        return handle_tools_call(req_id, params, allowed_root=effective_root)
    elif method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}
    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method '{method}' not found"}
        }


def run_stdio_server(
    input_stream: Optional[object] = None,
    output_stream: Optional[object] = None,
    max_message_bytes: int = 1_000_000,
    allowed_root: Optional[Path] = None,
    permit_unrestricted: bool = False,
) -> None:
    """Main stdio server loop for MCP with framing limits and drainage."""
    if input_stream is None:
        input_stream = getattr(sys.stdin, "buffer", sys.stdin)
    if output_stream is None:
        output_stream = sys.stdout

    while True:
        chunk = input_stream.readline(max_message_bytes + 1)
        if not chunk:
            break

        is_bytes = isinstance(chunk, bytes)
        has_newline = chunk.endswith(b"\n") if is_bytes else chunk.endswith("\n")
        length = len(chunk)

        if length > max_message_bytes or (not has_newline and length == max_message_bytes + 1):
            while not has_newline:
                drain = input_stream.readline(4096)
                if not drain:
                    break
                has_newline = drain.endswith(b"\n") if isinstance(drain, bytes) else drain.endswith("\n")

            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32001,
                    "message": f"Message size exceeds limit of {max_message_bytes} bytes"
                }
            }
            output_stream.write(json.dumps(err_resp) + "\n")
            if hasattr(output_stream, "flush"):
                output_stream.flush()
            continue

        line_str = chunk.decode("utf-8", errors="replace") if is_bytes else chunk
        resp = process_message(
            line_str,
            max_message_bytes=max_message_bytes,
            allowed_root=allowed_root,
            permit_unrestricted=permit_unrestricted,
        )
        if resp is not None:
            output_stream.write(json.dumps(resp) + "\n")
            if hasattr(output_stream, "flush"):
                output_stream.flush()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AuraCode Model Context Protocol (MCP) Server")
    parser.add_argument("--allowed-root", type=str, default=None, help="Root directory for allowed tool operations (default: current working directory)")
    parser.add_argument("--unrestricted-root", action="store_true", help="Permit unrestricted filesystem access (insecure, not recommended)")
    parser.add_argument("--max-message-bytes", type=int, default=1_000_000, help="Maximum incoming JSON-RPC frame size")
    cli_args = parser.parse_args()
    if cli_args.unrestricted_root or cli_args.allowed_root == "*":
        root_path = None
        unrestricted = True
    elif cli_args.allowed_root:
        root_path = Path(cli_args.allowed_root).resolve()
        unrestricted = False
    else:
        root_path = Path.cwd().resolve()
        unrestricted = False
    run_stdio_server(max_message_bytes=cli_args.max_message_bytes, allowed_root=root_path, permit_unrestricted=unrestricted)
