#!/usr/bin/env python3
"""Tests for AuraCode Executive Health Audit Engine."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.audit import audit_workspace, discover_source_files, format_executive_report

ROOT = Path(__file__).resolve().parents[1]


class AuditTests(unittest.TestCase):
    """Test suite for the comprehensive audit engine."""

    def test_discover_source_files(self):
        """Verify discovery returns application and test files separately."""
        app_files, test_files = discover_source_files(ROOT)
        self.assertGreater(len(app_files), 10)
        self.assertGreater(len(test_files), 5)
        # Ensure tests are in test_files, not app_files
        for f, _ in app_files:
            self.assertFalse(Path(f).name.startswith("test_"))
            self.assertNotIn("tests", Path(f).parts)

    def test_discovery_excludes_auracode_generated_workspaces(self):
        """Built wheels and managed evidence must not duplicate audited source."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            (temp_dir / "app.py").write_text("value = 1\n", encoding="utf-8")
            generated = temp_dir / "_auracode_forward" / "wheel-install"
            generated.mkdir(parents=True)
            (generated / "copied.py").write_text("eval('unsafe')\n", encoding="utf-8")

            app_files, test_files = discover_source_files(temp_dir)

            self.assertEqual([Path(path).name for path, _ in app_files], ["app.py"])
            self.assertEqual(test_files, [])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_audit_workspace_structure(self):
        """Verify report exposes explicit guarantees instead of a score."""
        res = audit_workspace(ROOT)
        self.assertIn(res["status"], ("PASS", "FAIL", "NOT_RUN", "ERROR"))
        self.assertIn("target", res)
        self.assertIn("guarantees", res)
        self.assertIn("violations_summary", res)
        self.assertIn("findings", res)
        self.assertNotIn("health_score", res)
        self.assertNotIn("grade", res)

        for guarantee in res["guarantees"].values():
            self.assertIn(
                guarantee["status"],
                ("PASS", "FAIL", "NOT_RUN", "NOT_APPLICABLE", "ERROR"),
            )
            self.assertIn("method", guarantee)
            self.assertIn("files_scanned", guarantee)

    def test_format_executive_report(self):
        """Verify plain-language executive report generation."""
        res = audit_workspace(ROOT)
        report_text = format_executive_report(res)
        self.assertIn("LAUDO MESTRE DE AUDITORIA E SAUDE DO SOFTWARE", report_text)
        self.assertIn("RESULTADO GERAL:", report_text)
        self.assertIn("GARANTIAS VERIFICADAS:", report_text)
        self.assertNotIn("PONTUACAO DE SAUDE", report_text)
        self.assertNotIn("Engenharia Senior", report_text)

    def test_missing_target_is_error_without_false_approval(self):
        """A path that does not exist must never produce PASS."""
        missing = Path(tempfile.gettempdir()) / "auracode-target-that-does-not-exist"
        self.assertFalse(missing.exists())

        res = audit_workspace(missing)

        self.assertEqual(res["status"], "ERROR")
        self.assertEqual(res["target"]["status"], "MISSING")
        self.assertEqual(res["total_files_scanned"], 0)
        self.assertNotIn("health_score", res)
        self.assertTrue(all(g["status"] == "NOT_RUN" for g in res["guarantees"].values()))

    def test_empty_target_is_not_run_without_false_approval(self):
        """An empty directory is an unperformed audit, not a perfect audit."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            res = audit_workspace(temp_dir)

            self.assertEqual(res["status"], "NOT_RUN")
            self.assertEqual(res["target"]["status"], "NO_SUPPORTED_FILES")
            self.assertEqual(res["total_files_scanned"], 0)
            self.assertTrue(all(g["status"] == "NOT_RUN" for g in res["guarantees"].values()))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_missing_required_evidence_prevents_pass(self):
        """Clean source alone cannot prove architecture, requirements, or tests."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            (temp_dir / "app.py").write_text(
                "def answer(value: int) -> int:\n    return value + 1\n",
                encoding="utf-8",
            )

            res = audit_workspace(temp_dir)

            self.assertEqual(res["status"], "NOT_RUN")
            self.assertEqual(res["guarantees"]["architecture"]["status"], "NOT_RUN")
            self.assertEqual(res["guarantees"]["requirements"]["status"], "NOT_RUN")
            self.assertEqual(res["guarantees"]["test_integrity"]["status"], "NOT_RUN")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_audit_catches_intentional_flaws(self):
        """Verify audit detects unclosed resources or slop in a sample directory."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            bad_file = temp_dir / "bad.py"
            bad_file.write_text(
                "def leak():\n"
                "    f = open('data.txt', 'r')\n"
                "    return f.read()\n\n"
                "def slop():\n"
                "    try:\n"
                "        1 / 0\n"
                "    except Exception:\n"
                "        pass\n",
                encoding="utf-8"
            )
            res = audit_workspace(temp_dir)
            self.assertIn(res["status"], ("WARN", "FAIL"))
            self.assertGreater(res["violations_summary"]["resource_leaks"], 0)
            self.assertGreater(res["violations_summary"]["slop_and_swallowed_errors"], 0)
            self.assertEqual(res["guarantees"]["resource_leaks"]["status"], "FAIL")
            self.assertEqual(res["guarantees"]["slop"]["status"], "FAIL")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
