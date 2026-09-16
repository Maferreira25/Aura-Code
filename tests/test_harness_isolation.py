import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from validation.tools.runner import (
    sanitize_environment,
    get_runner,
    SubprocessSanitizedRunner,
    DockerRunner,
    is_docker_available,
)
from validation.tools import harness

ROOT = Path(__file__).resolve().parents[1]


class HarnessIsolationTests(unittest.TestCase):
    def test_sanitize_environment_filters_secrets(self):
        dirty_env = {
            "PATH": "C:\\bin;/usr/bin",
            "TEMP": "/tmp",
            "AWS_SECRET_ACCESS_KEY": "AKIAIOSFODNN7EXAMPLE",
            "GITHUB_TOKEN": "ghp_xxxxxxxxxxxx",
            "OPENAI_API_KEY": "sk-proj-xxxxxx",
            "DATABASE_PASSWORD": "supersecretpassword",
            "AURACODE_AUDIT_SENTINEL": "sensitive_marker_123",
            "AUTH_HEADER": "Bearer token",
            "CUSTOM_API_ENDPOINT": "https://api.internal",
        }
        clean = sanitize_environment(env=dirty_env)
        self.assertIn("PATH", clean)
        self.assertIn("TEMP", clean)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", clean)
        self.assertNotIn("GITHUB_TOKEN", clean)
        self.assertNotIn("OPENAI_API_KEY", clean)
        self.assertNotIn("DATABASE_PASSWORD", clean)
        self.assertNotIn("AURACODE_AUDIT_SENTINEL", clean)
        self.assertNotIn("AUTH_HEADER", clean)
        self.assertNotIn("CUSTOM_API_ENDPOINT", clean)

    def test_fail_closed_container_mode_when_docker_unavailable(self):
        with patch("validation.tools.runner.is_docker_available", return_value=False):
            with self.assertRaises(RuntimeError) as ctx:
                get_runner("container")
            self.assertIn("Failing closed", str(ctx.exception))

    def test_strict_mode_fails_closed_when_docker_unavailable(self):
        with patch("validation.tools.runner.is_docker_available", return_value=False):
            with self.assertRaises(RuntimeError) as ctx:
                get_runner("auto", strict_mode=True)
            self.assertIn("Strict mode enabled", str(ctx.exception))

    def test_auto_mode_falls_back_to_sanitized_subprocess_in_permissive_mode(self):
        with patch("validation.tools.runner.is_docker_available", return_value=False):
            runner = get_runner("auto", strict_mode=False)
            self.assertIsInstance(runner, SubprocessSanitizedRunner)
            self.assertEqual(runner.backend_name, "subprocess_sanitized")
            self.assertFalse(runner.is_strong_isolation)

    def test_docker_runner_selected_when_docker_is_available(self):
        with patch("validation.tools.runner.is_docker_available", return_value=True):
            runner = get_runner("auto", strict_mode=False)
            self.assertIsInstance(runner, DockerRunner)
            self.assertEqual(runner.backend_name, "docker")
            self.assertTrue(runner.is_strong_isolation)

    def test_sanitized_subprocess_does_not_leak_host_secrets_to_tests(self):
        temp_dir = Path(tempfile.mkdtemp(prefix="test_iso_"))
        try:
            test_dir = temp_dir / "tests"
            test_dir.mkdir()
            test_file = test_dir / "test_leak.py"
            # This test asserts that sensitive keys are not present in the process env
            test_file.write_text(
                "import os, unittest\n"
                "class LeakCheck(unittest.TestCase):\n"
                "    def test_no_secrets(self):\n"
                "        for k in os.environ:\n"
                "            for bad in ['TOKEN', 'SECRET', 'KEY', 'PASS', 'AURACODE_']:\n"
                "                if bad in k.upper():\n"
                "                    self.fail(f'Leaked secret {k}')\n",
                encoding="utf-8",
            )
            # Inject host secrets into current process env
            with patch.dict(os.environ, {
                "AURACODE_SECRET_TOKEN": "should_not_leak",
                "MY_SUPER_SECRET_KEY": "topsecret",
            }):
                runner = SubprocessSanitizedRunner()
                res = runner.run_tests(temp_dir, test_dir, timeout=10)
                self.assertEqual(res["returncode"], 0, f"STDOUT: {res['stdout']}\nSTDERR: {res['stderr']}")
                self.assertTrue(res["isolation_boundary_enforced"])
                self.assertEqual(res["backend"], "subprocess_sanitized")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_sanitized_subprocess_timeout_termination(self):
        temp_dir = Path(tempfile.mkdtemp(prefix="test_timeout_"))
        try:
            test_dir = temp_dir / "tests"
            test_dir.mkdir()
            test_file = test_dir / "test_hang.py"
            test_file.write_text(
                "import time, unittest\n"
                "class HangTest(unittest.TestCase):\n"
                "    def test_hang(self):\n"
                "        time.sleep(5)\n",
                encoding="utf-8",
            )
            runner = SubprocessSanitizedRunner()
            res = runner.run_tests(temp_dir, test_dir, timeout=1)
            self.assertTrue(res["timed_out"])
            self.assertEqual(res["returncode"], 124)
            self.assertIn("TIMEOUT", res["stderr"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_harness_evaluate_records_isolation_metadata(self):
        ws = ROOT / "validation" / "reference" / "public" / "SEC-AUTHZ-001"
        res = harness.evaluate("SEC-AUTHZ-001", ws, run_id="iso-test", isolation="local")
        self.assertIn("isolation_backend", res)
        self.assertEqual(res["isolation_backend"], "subprocess_sanitized")
        self.assertTrue(res.get("isolation_boundary_enforced"))
        self.assertTrue(res["qualified_success"])

    def test_sanitized_subprocess_detects_and_aborts_on_oracle_tampering(self):
        temp_dir = Path(tempfile.mkdtemp(prefix="test_tamper_"))
        try:
            test_dir = temp_dir / "tests"
            test_dir.mkdir()
            test_file = test_dir / "test_cheat.py"
            test_file.write_text(
                "import unittest\n"
                "class MaliciousTest(unittest.TestCase):\n"
                "    def test_subvert(self):\n"
                "        unittest.TestCase.assertEqual = lambda self, a, b, *args, **kwargs: None\n"
                "        self.assertEqual(1, 2)\n",
                encoding="utf-8",
            )
            runner = SubprocessSanitizedRunner()
            res = runner.run_tests(temp_dir, test_dir, timeout=10)
            self.assertNotEqual(res["returncode"], 0)
            self.assertEqual(res["returncode"], 101)
            self.assertTrue(res.get("oracle_tampering_detected"))
            self.assertIn("ORACLE_TAMPERING_DETECTED", res["stderr"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
