#!/usr/bin/env python3
"""Tests for AuraCode Local Preflight & Git Pre-Push Guardrail."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from tools.preflight import get_preflight_steps, run_preflight_checks
from tools.pre_tool_guard import install_git_pre_push_hook, install_hooks

ROOT = Path(__file__).resolve().parents[1]


class PreflightTests(unittest.TestCase):
    """Test suite for local preflight CI-mirror and pre-push hook."""

    def test_get_preflight_steps_structure(self):
        """Verify that preflight steps include all 10 expected CI gates."""
        steps = get_preflight_steps(ROOT)
        self.assertGreaterEqual(len(steps), 10)
        step_names = [s["name"] for s in steps]
        self.assertIn("Integridade do Framework e Manifesto Criptografico", step_names)
        self.assertIn("Limites de Camadas (Clean Architecture)", step_names)
        self.assertIn("AI Slop e Erros Silenciados (except: pass)", step_names)
        self.assertIn("Vazamentos de Recursos (Arquivos e Conexoes)", step_names)
        self.assertIn("Tipagem Estrita (Type Annotations)", step_names)
        self.assertIn("Integridade de Assercoes nos Testes", step_names)
        self.assertIn("Vetores de Injecao e Seguranca (sec)", step_names)
        self.assertIn("Ambiguidade de Requisitos (Gate G1)", step_names)

    def test_preflight_report_structure_mocked_success(self):
        """Verify report keys when all steps pass."""
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "OK"
        mock_res.stderr = ""

        with patch("subprocess.run", return_value=mock_res):
            report = run_preflight_checks(workspace_root=ROOT, quiet=True)
            self.assertEqual(report["status"], "PASS")
            self.assertIsNone(report["failed_step"])
            self.assertGreaterEqual(report["passed_steps"], 1)
            self.assertEqual(report["steps_executed"], report["passed_steps"])

    def test_preflight_catches_failure(self):
        """Verify that when a step fails, preflight halts and reports the failure."""
        mock_fail = MagicMock()
        mock_fail.returncode = 1
        mock_fail.stdout = "Violation detected"
        mock_fail.stderr = "Traceback error"

        with patch("subprocess.run", return_value=mock_fail):
            report = run_preflight_checks(workspace_root=ROOT, quiet=True)
            self.assertEqual(report["status"], "FAIL")
            self.assertIsNotNone(report["failed_step"])
            self.assertEqual(report["failed_step"]["returncode"], 1)
            self.assertIn("Violation detected", report["failed_step"]["stdout"])

    def test_missing_required_inputs_block_without_running_later_gates(self):
        """Missing verification inputs cannot silently reduce gate coverage."""
        for missing, expected_executions in (
            ("manifest", 0), ("benchmark", 1), ("tests", 2)
        ):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                if missing != "manifest":
                    (root / "MANIFEST.json").write_text("{}", encoding="utf-8")
                if missing != "benchmark":
                    suite = root / "validation" / "tools" / "validate_suite.py"
                    suite.parent.mkdir(parents=True)
                    suite.write_text("", encoding="utf-8")
                if missing != "tests":
                    (root / "tests").mkdir()
                success = MagicMock(returncode=0, stdout="OK", stderr="")
                with patch("subprocess.run", return_value=success) as run:
                    report = run_preflight_checks(root, quiet=True)
                self.assertEqual(report["status"], "FAIL")
                self.assertEqual(report["failed_step"]["status"], "NOT_ASSESSED")
                self.assertIsNone(report["failed_step"]["returncode"])
                self.assertEqual(report["steps_executed"], expected_executions)
                self.assertEqual(report["passed_steps"], expected_executions)
                self.assertEqual(run.call_count, expected_executions)

    def test_empty_gate_plan_cannot_pass(self):
        """An empty verification plan is absence of proof, not approval."""
        with patch("tools.preflight.get_preflight_steps", return_value=[]):
            report = run_preflight_checks(ROOT, quiet=True)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["steps_executed"], 0)
        self.assertEqual(report["failed_step"]["status"], "NOT_ASSESSED")

    def test_missing_inputs_exit_nonzero_in_cli(self):
        """CLI consumers and pre-push hooks receive a blocking exit code."""
        from tools.preflight import main
        with tempfile.TemporaryDirectory() as directory:
            with patch("sys.argv", ["preflight", directory, "--quiet"]):
                with self.assertRaises(SystemExit) as raised:
                    main()
        self.assertEqual(raised.exception.code, 1)

    def test_install_git_pre_push_hook(self):
        """Verify that pre-push hook is written to .git/hooks/pre-push when .git exists."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # When .git doesn't exist, returns None without error
            res = install_git_pre_push_hook(temp_dir)
            self.assertIsNone(res)

            # When .git exists, creates .git/hooks/pre-push
            (temp_dir / ".git").mkdir()
            hook_file = install_git_pre_push_hook(temp_dir)
            self.assertIsNotNone(hook_file)
            self.assertTrue(hook_file.is_file())
            content = hook_file.read_text(encoding="utf-8")
            self.assertIn("AURA CODE -- GIT PRE-PUSH ASSURANCE GUARD", content)
            self.assertIn("tools/assurance.py preflight", content)
            self.assertIn("auracode preflight", content)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_install_hooks_integrates_pre_push(self):
        """Verify that install_hooks sets up both .agents/hooks.json and .git/hooks/pre-push."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            (temp_dir / ".git").mkdir()
            hooks_json = install_hooks(temp_dir)
            self.assertTrue(hooks_json.is_file())
            pre_push = temp_dir / ".git" / "hooks" / "pre-push"
            self.assertTrue(pre_push.is_file())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
