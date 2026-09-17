#!/usr/bin/env python3
"""Comprehensive Unit Test Suite for AuraCode AST Inspection Engines and CLI.

Tests slop code detection, resource leaks, strict types, test integrity,
injection vectors, requirements ambiguity, and CLI dispatchers.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.check_slop_code as slop_engine
import tools.check_resource_leaks as leaks_engine
import tools.check_strict_types as types_engine
import tools.check_test_integrity as integrity_engine
import tools.check_injection_vectors as sec_engine
import tools.check_requirements_ambiguity as ambiguity_engine
from tools.assurance import main as cli_main


class TestSlopCodeDetector(unittest.TestCase):
    """Unit tests for tools.check_slop_code."""

    def test_clean_code_passes(self):
        code = (
            "def calculate_total(price: float, tax: float) -> float:\n"
            "    subtotal = price * (1.0 + tax)\n"
            "    return round(subtotal, 2)\n"
        )
        with tempfile.TemporaryDirectory() as td:
            fpath = Path(td) / "clean.py"
            fpath.write_text(code, encoding="utf-8")
            violations = slop_engine.check_file(str(fpath), td)
            self.assertEqual(len(violations), 0)

    def test_unreachable_code_detected(self):
        code = (
            "def broken_function():\n"
            "    return True\n"
            "    print('This line is dead code')\n"
        )
        with tempfile.TemporaryDirectory() as td:
            fpath = Path(td) / "unreachable.py"
            fpath.write_text(code, encoding="utf-8")
            violations = slop_engine.check_file(str(fpath), td)
            types = [v["type"] for v in violations]
            self.assertIn("unreachable_code", types)

    def test_silent_exception_swallowing_detected(self):
        code = (
            "def risky_operation():\n"
            "    try:\n"
            "        do_something()\n"
            "    except ValueError:\n"
            "        pass\n"
        )
        with tempfile.TemporaryDirectory() as td:
            fpath = Path(td) / "swallow.py"
            fpath.write_text(code, encoding="utf-8")
            violations = slop_engine.check_file(str(fpath), td)
            types = [v["type"] for v in violations]
            self.assertIn("silent_exception_swallowing", types)

    def test_dummy_placeholder_string_detected(self):
        code = (
            "def generate_report():\n"
            "    msg = 'TODO: implement detailed summary here'\n"
            "    return msg\n"
        )
        with tempfile.TemporaryDirectory() as td:
            fpath = Path(td) / "dummy.py"
            fpath.write_text(code, encoding="utf-8")
            violations = slop_engine.check_file(str(fpath), td)
            types = [v["type"] for v in violations]
            self.assertIn("dummy_placeholder_string", types)


class TestResourceLeaksDetector(unittest.TestCase):
    """Unit tests for tools.check_resource_leaks."""

    def test_managed_context_resource_passes(self):
        code = (
            "def read_data(path: str) -> str:\n"
            "    with open(path, 'r', encoding='utf-8') as f:\n"
            "        return f.read()\n"
        )
        with tempfile.TemporaryDirectory() as td:
            fpath = Path(td) / "managed.py"
            fpath.write_text(code, encoding="utf-8")
            leaks = leaks_engine.check_file(str(fpath), td)
            self.assertEqual(len(leaks), 0)

    def test_unmanaged_open_detected(self):
        code = (
            "def unmanaged_read(path: str):\n"
            "    f = open(path, 'r')\n"
            "    data = f.read()\n"
            "    return data\n"
        )
        with tempfile.TemporaryDirectory() as td:
            fpath = Path(td) / "leak.py"
            fpath.write_text(code, encoding="utf-8")
            leaks = leaks_engine.check_file(str(fpath), td)
            self.assertGreater(len(leaks), 0)
            self.assertEqual(leaks[0]["type"], "potential_unclosed_resource")
            self.assertEqual(leaks[0]["resource"], "open")


class TestStrictTypesDetector(unittest.TestCase):
    """Unit tests for tools.check_strict_types."""

    def test_fully_typed_function_passes(self):
        code = (
            "def greet(name: str, count: int) -> str:\n"
            "    return f'Hello {name}' * count\n"
        )
        with tempfile.TemporaryDirectory() as td:
            fpath = Path(td) / "typed.py"
            fpath.write_text(code, encoding="utf-8")
            violations = types_engine.check_file(str(fpath), td)
            self.assertEqual(len(violations), 0)

    def test_missing_return_and_arg_type_hints_detected(self):
        code = (
            "def untyped_func(name, age):\n"
            "    return f'{name} is {age}'\n"
        )
        with tempfile.TemporaryDirectory() as td:
            fpath = Path(td) / "untyped.py"
            fpath.write_text(code, encoding="utf-8")
            violations = types_engine.check_file(str(fpath), td)
            types = [v["type"] for v in violations]
            self.assertIn("missing_return_annotation", types)
            self.assertIn("missing_arg_annotation", types)

    def test_forbidden_any_type_detected(self):
        code = (
            "from typing import Any\n"
            "def loose_function(payload: Any) -> Any:\n"
            "    return payload\n"
        )
        with tempfile.TemporaryDirectory() as td:
            fpath = Path(td) / "loose.py"
            fpath.write_text(code, encoding="utf-8")
            violations = types_engine.check_file(str(fpath), td)
            any_violations = [v for v in violations if v["type"] == "forbidden_any_type"]
            self.assertGreater(len(any_violations), 0)


class TestTestIntegrityDetector(unittest.TestCase):
    """Unit tests for tools.check_test_integrity."""

    def test_test_with_assertions_passes(self):
        code = (
            "import unittest\n"
            "class SampleTest(unittest.TestCase):\n"
            "    def test_valid(self):\n"
            "        self.assertEqual(1 + 1, 2)\n"
            "    def test_with_assert_statement(self):\n"
            "        assert True\n"
        )
        with tempfile.TemporaryDirectory() as td:
            fpath = Path(td) / "test_sample.py"
            fpath.write_text(code, encoding="utf-8")
            import ast
            tree = ast.parse(code, filename=str(fpath))
            visitor = integrity_engine.TestIntegrityVisitor(str(fpath))
            visitor.visit(tree)
            self.assertEqual(len(visitor.vacuous_tests), 0)
            self.assertEqual(visitor.test_functions, 2)

    def test_vacuous_test_without_assertions_detected(self):
        code = (
            "import unittest\n"
            "class VacuousTest(unittest.TestCase):\n"
            "    def test_doing_nothing(self):\n"
            "        x = 10\n"
            "        y = 20\n"
            "        z = x + y\n"
        )
        with tempfile.TemporaryDirectory() as td:
            fpath = Path(td) / "test_vacuous.py"
            fpath.write_text(code, encoding="utf-8")
            import ast
            tree = ast.parse(code, filename=str(fpath))
            visitor = integrity_engine.TestIntegrityVisitor(str(fpath))
            visitor.visit(tree)
            self.assertEqual(len(visitor.vacuous_tests), 1)
            self.assertEqual(visitor.vacuous_tests[0]["function"], "test_doing_nothing")


class TestInjectionVectorsDetector(unittest.TestCase):
    """Unit tests for tools.check_injection_vectors."""

    def test_safe_calls_pass(self):
        code = (
            "import re\n"
            "import subprocess\n"
            "def safe_operations(text: str) -> None:\n"
            "    pattern = re.compile(r'^[a-z]+$')\n"
            "    subprocess.run(['ls', '-l'], shell=False)\n"
        )
        with tempfile.TemporaryDirectory() as td:
            fpath = Path(td) / "safe.py"
            fpath.write_text(code, encoding="utf-8")
            findings = sec_engine.check_file(str(fpath), td)
            self.assertEqual(len(findings), 0)

    def test_unsafe_eval_detected(self):
        code = (
            "def calculate(expr: str):\n"
            "    return eval(expr)\n"
        )
        with tempfile.TemporaryDirectory() as td:
            fpath = Path(td) / "eval.py"
            fpath.write_text(code, encoding="utf-8")
            findings = sec_engine.check_file(str(fpath), td)
            types = [f["type"] for f in findings]
            self.assertIn("unsafe_eval_exec", types)

    def test_shell_true_detected(self):
        code = (
            "import subprocess\n"
            "def run_command(cmd: str):\n"
            "    subprocess.Popen(cmd, shell=True)\n"
        )
        with tempfile.TemporaryDirectory() as td:
            fpath = Path(td) / "shell.py"
            fpath.write_text(code, encoding="utf-8")
            findings = sec_engine.check_file(str(fpath), td)
            types = [f["type"] for f in findings]
            self.assertIn("command_injection_shell_true", types)

    def test_sql_injection_fstring_detected(self):
        code = (
            "def find_user(username: str):\n"
            "    query = f'SELECT * FROM users WHERE username = {username}'\n"
            "    return query\n"
        )
        with tempfile.TemporaryDirectory() as td:
            fpath = Path(td) / "sql.py"
            fpath.write_text(code, encoding="utf-8")
            findings = sec_engine.check_file(str(fpath), td)
            types = [f["type"] for f in findings]
            self.assertIn("potential_sql_injection", types)


class TestRequirementsAmbiguityDetector(unittest.TestCase):
    """Unit tests for tools.check_requirements_ambiguity."""

    def test_clear_workspace_passes(self):
        with tempfile.TemporaryDirectory() as td:
            doc = Path(td) / "spec.md"
            doc.write_text("# Clear Specification\n\nAll endpoints require OAuth2 bearer tokens.\n", encoding="utf-8")
            res = ambiguity_engine.analyze_workspace(td)
            self.assertEqual(res["status"], "PASS")
            self.assertEqual(res["total_ambiguity_findings"], 0)

    def test_ambiguity_markers_detected(self):
        with tempfile.TemporaryDirectory() as td:
            doc = Path(td) / "draft.md"
            doc.write_text(
                "# Unclear Spec\n"
                "- Login behavior: maybe redirect to dashboard, or something like that.\n"
                "- Data retention: TBD.\n"
                "- Backup: normal behavior.\n"
                "- Status: TODO finalize.\n",
                encoding="utf-8"
            )
            res = ambiguity_engine.analyze_workspace(td)
            self.assertIn(res["status"], ["WARN", "FAIL"])
            self.assertGreater(res["total_ambiguity_findings"], 0)
            self.assertGreater(len(res["suggested_non_technical_questions"]), 0)


class TestCLIEntrypoint(unittest.TestCase):
    """Unit tests for auracode CLI argument parsing and dispatching."""

    def test_cli_help_flag(self):
        from unittest.mock import patch
        import io
        test_args = ["auracode", "--help"]
        with patch.object(sys, "argv", test_args):
            with patch("sys.stdout", new=io.StringIO()) as fake_out:
                with self.assertRaises(SystemExit) as cm:
                    cli_main()
                self.assertEqual(cm.exception.code, 0)
                self.assertIn("AuraCode - Agentic Unified Reliability & Assurance", fake_out.getvalue())

    def test_cli_slop_command_dispatched(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "clean.py"
            p.write_text("def ok() -> int:\n    return 42\n", encoding="utf-8")
            test_args = ["auracode", "slop", td]
            with patch.object(sys, "argv", test_args):
                with patch("sys.exit") as mock_exit:
                    cli_main()
                    # Exit should not be called with 1 since the file is clean
                    if mock_exit.called:
                        self.assertEqual(mock_exit.call_args[0][0], 0)


class TestProgrammaticAPI(unittest.TestCase):
    """Test top-level auracode package programmatic access and facade."""

    def test_import_auracode_metadata(self):
        import auracode
        self.assertEqual(auracode.__version__, "0.1.1")
        self.assertTrue(callable(auracode.cli))
        self.assertTrue(callable(auracode.check_architecture))
        self.assertTrue(callable(auracode.check_slop))
        self.assertTrue(callable(auracode.check_leaks))
        self.assertTrue(callable(auracode.check_types))
        self.assertTrue(callable(auracode.check_sec))
        self.assertTrue(callable(auracode.check_ambiguity))
        self.assertTrue(callable(auracode.verify_package))

    def test_programmatic_slop_call(self):
        import auracode
        with tempfile.TemporaryDirectory() as td:
            fpath = Path(td) / "clean.py"
            fpath.write_text("def valid() -> bool:\n    return True\n", encoding="utf-8")
            violations = auracode.check_slop(str(fpath), td)
            self.assertEqual(len(violations), 0)


if __name__ == "__main__":
    unittest.main()
