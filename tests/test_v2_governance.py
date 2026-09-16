#!/usr/bin/env python3
"""Comprehensive Automated Test Suite for V2 Active Governance Engines.

Tests AST-based architectural linter, supply chain anti-hallucination engine,
surgical diff analyzer, and JSON-RPC stdio MCP Server.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.check_architecture import check_architecture, check_file_architecture
from tools.verify_dependencies import verify_package, verify_requirements_file, parse_requirements
from tools.check_surgical_diff import check_surgical_diff, is_path_in_scope, is_test_file
from tools.assurance_mcp import process_message, TOOLS_MANIFEST


class TestArchitectureLinter(unittest.TestCase):
    """Test AST inspection against architectural boundary rules."""

    def test_clean_domain_passes(self):
        code = (
            "from dataclasses import dataclass\n"
            "from typing import Optional\n\n"
            "@dataclass\n"
            "class Entity:\n"
            "    id: str\n"
        )
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "domain.py"
            p.write_text(code, encoding="utf-8")
            layer_cfg = {
                "allowed_imports": ["dataclasses", "typing"],
                "forbidden_imports": ["json", "sqlite3"],
                "allow_wildcard_imports": False
            }
            viols, err = check_file_architecture(p, "domain", layer_cfg, {}, Path(td))
            self.assertIsNone(err)
            self.assertEqual(len(viols), 0)

    def test_forbidden_import_detected(self):
        code = (
            "import json\n"
            "class Service:\n"
            "    def export(self, data):\n"
            "        return json.dumps(data)\n"
        )
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "service.py"
            p.write_text(code, encoding="utf-8")
            layer_cfg = {
                "forbidden_imports": ["json", "sqlite3", "requests"],
                "allow_wildcard_imports": False
            }
            viols, err = check_file_architecture(p, "service", layer_cfg, {}, Path(td))
            self.assertIsNone(err)
            self.assertEqual(len(viols), 1)
            self.assertEqual(viols[0]["rule"], "forbidden_import")
            self.assertEqual(viols[0]["module"], "json")

    def test_wildcard_import_forbidden(self):
        code = "from math import *\nx = sin(1.0)\n"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "calc.py"
            p.write_text(code, encoding="utf-8")
            layer_cfg = {"allow_wildcard_imports": False}
            viols, err = check_file_architecture(p, "domain", layer_cfg, {}, Path(td))
            self.assertIsNone(err)
            self.assertTrue(any(v["rule"] == "no_wildcard_imports" for v in viols))

    def test_whitelist_not_allowed_import(self):
        code = "import os\nx = os.getcwd()\n"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "domain.py"
            p.write_text(code, encoding="utf-8")
            layer_cfg = {
                "allowed_imports": ["typing", "dataclasses"],
                "forbidden_imports": []
            }
            viols, err = check_file_architecture(p, "domain", layer_cfg, {}, Path(td))
            self.assertIsNone(err)
            self.assertTrue(any(v["rule"] == "disallowed_import" and v["module"] == "os" for v in viols))

    def test_max_file_lines_rule(self):
        code = "\n".join([f"x_{i} = {i}" for i in range(50)])
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "large.py"
            p.write_text(code, encoding="utf-8")
            layer_cfg = {"max_file_lines": 30}
            viols, err = check_file_architecture(p, "domain", layer_cfg, {}, Path(td))
            self.assertIsNone(err)
            self.assertTrue(any(v["rule"] == "max_file_lines" for v in viols))

    def test_full_project_check_with_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "domain.py").write_text("from dataclasses import dataclass\n", encoding="utf-8")
            (root / "service.py").write_text("import sqlite3\n", encoding="utf-8")
            contract = {
                "project": "test-prj",
                "version": "1.0",
                "layers": {
                    "domain": {"path": "domain.py", "forbidden_imports": ["sqlite3"]},
                    "service": {"path": "service.py", "forbidden_imports": ["sqlite3"]}
                }
            }
            res = check_architecture(root, contract_data=contract)
            self.assertFalse(res["success"])
            self.assertEqual(res["violations_count"], 1)
            self.assertEqual(res["violations"][0]["module"], "sqlite3")

    def test_uncontracted_files_reported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "domain.py").write_text("class Domain: pass\n", encoding="utf-8")
            (root / "untracked_script.py").write_text("x = 1\n", encoding="utf-8")
            contract = {
                "project": "test-prj",
                "version": "1.0",
                "layers": {
                    "domain": {"path": "domain.py"}
                }
            }
            res = check_architecture(root, contract_data=contract)
            self.assertTrue(res["success"])
            self.assertIn("untracked_script.py", res.get("uncontracted_files", []))


class TestSupplyChainVerification(unittest.TestCase):
    """Test package anti-hallucination and PyPI verification engine."""

    def test_stdlib_collision_detected(self):
        res = verify_package("json")
        self.assertEqual(res["status"], "STDLIB_COLLISION")
        self.assertFalse(res["is_hallucinated"])
        self.assertEqual(res["severity"], "warning")

    @patch("tools.verify_dependencies.query_pypi_package")
    def test_hallucinated_package_detected(self, mock_query):
        mock_query.return_value = (None, "NOT_FOUND")
        res = verify_package("hallucinated-agent-lib-v999")
        self.assertEqual(res["status"], "HALLUCINATED_PACKAGE")
        self.assertTrue(res["is_hallucinated"])
        self.assertEqual(res["severity"], "critical")

    @patch("tools.verify_dependencies.query_pypi_package")
    def test_verified_package_success(self, mock_query):
        mock_query.return_value = ({
            "info": {"version": "2.31.0", "summary": "HTTP library"},
            "releases": {"2.31.0": []},
            "urls": [{"upload_time_iso_8601": "2023-05-22T00:00:00Z"}]
        }, None)
        res = verify_package("requests", requested_version="2.31.0")
        self.assertEqual(res["status"], "VERIFIED")
        self.assertFalse(res["is_hallucinated"])
        self.assertEqual(res["latest_version"], "2.31.0")

    @patch("tools.verify_dependencies.query_pypi_package")
    def test_nonexistent_version_detected(self, mock_query):
        mock_query.return_value = ({
            "info": {"version": "1.0.0"},
            "releases": {"1.0.0": []},
            "urls": []
        }, None)
        res = verify_package("my-lib", requested_version="9.9.9")
        self.assertEqual(res["status"], "NONEXISTENT_VERSION")
        self.assertTrue(res["is_hallucinated"])

    def test_parse_requirements_file(self):
        with tempfile.TemporaryDirectory() as td:
            req_file = Path(td) / "requirements.txt"
            req_file.write_text("requests==2.31.0\n# comment\nflask>=2.0.0\nurllib3\n", encoding="utf-8")
            pkgs = parse_requirements(req_file)
            self.assertEqual(len(pkgs), 3)
            self.assertEqual(pkgs[0]["name"], "requests")
            self.assertEqual(pkgs[0]["version"], "2.31.0")
            self.assertEqual(pkgs[1]["name"], "flask")


class TestSurgicalDiff(unittest.TestCase):
    """Test surgical diff boundaries and anti-reward-hacking checks."""

    def test_scope_matching(self):
        self.assertTrue(is_path_in_scope("src/core/utils.py", ["src/*.py", "src/**/*.py"]))
        self.assertTrue(is_path_in_scope("TASK.md", ["TASK.md", "src/*"]))
        self.assertFalse(is_path_in_scope("database/secret.py", ["src/*"]))

    def test_is_test_file(self):
        self.assertTrue(is_test_file("tests/test_users.py"))
        self.assertTrue(is_test_file("tests/integration/test_auth.py"))
        self.assertTrue(is_test_file("validation/scenarios/scenario.json"))
        self.assertFalse(is_test_file("src/service.py"))
        self.assertFalse(is_test_file("domain.py"))
        self.assertFalse(is_test_file("src/validation/rules.py"))

    def test_unauthorized_test_modification_blocked(self):
        changes = [
            {"status": "M", "file": "src/domain.py"},
            {"status": "M", "file": "tests/test_domain.py"}
        ]
        res = check_surgical_diff(
            repo_dir=Path("."),
            allowed_scope=["src/*.py", "tests/*.py"],
            allow_test_modifications=False,
            direct_changes=changes,
            direct_stats={"total_added": 10, "total_deleted": 2}
        )
        self.assertFalse(res["success"])
        self.assertEqual(res["violations_count"], 1)
        self.assertEqual(res["violations"][0]["rule"], "unauthorized_test_tampering")

    def test_out_of_scope_change_detected(self):
        changes = [
            {"status": "M", "file": "src/domain.py"},
            {"status": "M", "file": "config/production.env"}
        ]
        res = check_surgical_diff(
            repo_dir=Path("."),
            allowed_scope=["src/*.py"],
            allow_test_modifications=True,
            direct_changes=changes,
            direct_stats={"total_added": 5, "total_deleted": 1}
        )
        self.assertFalse(res["success"])
        self.assertTrue(any(v["rule"] == "out_of_scope_change" for v in res["violations"]))

    def test_excessive_churn_warning(self):
        changes = [{"status": "M", "file": "src/domain.py"}]
        res = check_surgical_diff(
            repo_dir=Path("."),
            allowed_scope=["src/*.py"],
            allow_test_modifications=True,
            max_modified_lines=100,
            direct_changes=changes,
            direct_stats={"total_added": 200, "total_deleted": 50}
        )
        # Warning does not fail hard success
        self.assertTrue(res["success"])
        self.assertTrue(any(v["rule"] == "excessive_diff_churn" for v in res["violations"]))


class TestAssuranceMCPServer(unittest.TestCase):
    """Test JSON-RPC 2.0 stdio MCP Server implementation."""

    def test_mcp_initialize(self):
        msg = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        resp = process_message(msg)
        self.assertEqual(resp["id"], 1)
        self.assertEqual(resp["result"]["serverInfo"]["name"], "auracode-mcp")
        self.assertIn("tools", resp["result"]["capabilities"])

    def test_mcp_tools_list(self):
        msg = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        resp = process_message(msg)
        self.assertEqual(resp["id"], 2)
        tool_names = [t["name"] for t in resp["result"]["tools"]]
        self.assertIn("check_architecture", tool_names)
        self.assertIn("verify_dependency", tool_names)
        self.assertIn("verify_requirements", tool_names)
        self.assertIn("check_surgical_diff", tool_names)

    def test_mcp_tools_call_verify_dependency_stdlib(self):
        msg = json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "verify_dependency",
                "arguments": {"package_name": "sqlite3"}
            }
        })
        resp = process_message(msg)
        self.assertEqual(resp["id"], 3)
        self.assertIn("content", resp["result"])
        parsed_out = json.loads(resp["result"]["content"][0]["text"])
        self.assertEqual(parsed_out["status"], "STDLIB_COLLISION")

    def test_mcp_unknown_method_error(self):
        msg = json.dumps({"jsonrpc": "2.0", "id": 4, "method": "unknown_rpc_method"})
        resp = process_message(msg)
        self.assertEqual(resp["id"], 4)
        self.assertEqual(resp["error"]["code"], -32601)


class TestContractsSchemaAndTemplate(unittest.TestCase):
    """Validate schema and template coherence."""

    def test_template_json_syntax(self):
        tmpl = json.loads((ROOT / "templates/contracts.template.json").read_text(encoding="utf-8"))
        self.assertIn("layers", tmpl)
        self.assertIn("domain", tmpl["layers"])
        self.assertIn("service", tmpl["layers"])
        self.assertIn("repository", tmpl["layers"])

    def test_schema_json_syntax(self):
        schema = json.loads((ROOT / "schemas/contracts.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["title"], "Architecture Contract Specification")


class TestAssessEngine(unittest.TestCase):
    """Validate profile assessment and path traversal defenses."""

    def test_assess_valid_al2_data(self):
        from tools.assess import assess_data
        data = {
            "project": "test-project",
            "assurance_level": "AL2",
            "controls": {
                "INT-01": {"status": "PASS", "evidence": ["docs/decisions/001-req.md"]},
            }
        }
        res = assess_data(data)
        self.assertFalse(res["success"])
        self.assertEqual(res["level"], "AL2")
        self.assertIn("INT-01", res["passed"])
        self.assertGreater(len(res["not_assessed"]), 0)

    def test_assess_pass_without_evidence_rejected(self):
        from tools.assess import assess_data
        data = {
            "project": "test-project",
            "assurance_level": "AL1",
            "controls": {
                "INT-01": {"status": "PASS"},  # Missing evidence
            }
        }
        res = assess_data(data)
        self.assertFalse(res["success"])
        self.assertIn("INT-01", res["invalid_pass"])
        self.assertNotIn("INT-01", res["passed"])

    def test_assess_invalid_profile_fails_gracefully(self):
        from tools.assess import assess_data
        data = {
            "project": "escape",
            "assurance_level": "../../malicious",
            "controls": {}
        }
        res = assess_data(data)
        self.assertFalse(res["success"])
        self.assertIn("Invalid or missing assurance_level", res["error"])

    def test_assess_nonexistent_file(self):
        from tools.assess import assess_file
        res = assess_file(Path("nonexistent_assessment.json"))
        self.assertFalse(res["success"])
        self.assertIn("not found", res["error"])

    def test_assess_rejects_nonexistent_evidence_file(self):
        from tools.assess import assess_data
        data = {
            "project": "fake-project",
            "assurance_level": "AL1",
            "controls": {
                "INT-01": {"status": "PASS", "evidence": ["this_file_does_not_exist_xyz.txt"]},
            }
        }
        res = assess_data(data, project_root=Path.cwd(), verify_evidence_paths=True)
        self.assertFalse(res["success"])
        self.assertIn("INT-01", res["invalid_pass"])
        self.assertNotIn("INT-01", res["passed"])
        self.assertIn("INT-01", res.get("missing_evidence", {}))


class TestHarnessSafety(unittest.TestCase):
    """Validate harness safeguards against destructive prepare/eval."""

    def test_prepare_refuses_repository_or_root_destination(self):
        from validation.tools.harness import cmd_prepare
        import argparse
        args = argparse.Namespace(
            scenario="DAT-ATOMIC-001",
            destination=str(ROOT),
            force=True,
            allow_advanced=False,
        )
        with self.assertRaises(SystemExit) as ctx:
            cmd_prepare(args)
        self.assertIn("Refusing to prepare scenario directly into root", str(ctx.exception))

    def test_prepare_refuses_protected_repo_subdir(self):
        from validation.tools.harness import cmd_prepare
        import argparse
        args = argparse.Namespace(
            scenario="DAT-ATOMIC-001",
            destination=str(ROOT / "controls"),
            force=True,
            allow_advanced=False,
        )
        with self.assertRaises(SystemExit) as ctx:
            cmd_prepare(args)
        self.assertIn("Refusing to overwrite protected repository directory", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
