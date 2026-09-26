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

    def test_audit_workspace_structure(self):
        """Verify report keys and health score calculation."""
        res = audit_workspace(ROOT)
        self.assertIn("health_score", res)
        self.assertIn("grade", res)
        self.assertIn("violations_summary", res)
        self.assertIn("findings", res)
        self.assertGreaterEqual(res["health_score"], 0)
        self.assertLessEqual(res["health_score"], 100)

    def test_format_executive_report(self):
        """Verify plain-language executive report generation."""
        res = audit_workspace(ROOT)
        report_text = format_executive_report(res)
        self.assertIn("LAUDO MESTRE DE AUDITORIA E SAUDE DO SOFTWARE", report_text)
        self.assertIn("PONTUACAO DE SAUDE:", report_text)
        self.assertIn("AVALIACAO POR ANALOGIAS DO MUNDO FISICO:", report_text)

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
            self.assertLess(res["health_score"], 100)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
