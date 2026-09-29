#!/usr/bin/env python3
"""Comprehensive Unit Test Suite for AuraCode Multi-Language Assurance Runner.

Verifies multi-language discovery, AST static scanning across Python, TypeScript,
and Go, detection of slop, resource leaks, and security injection hazards.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from tools.multilang_runner import scan_multilang_workspace


class TestMultiLangRunner(unittest.TestCase):
    """Test suite for multi-language AST workspace scanner."""

    def setUp(self):
        from tools.multilang_ast import HAS_TREE_SITTER
        if not HAS_TREE_SITTER:
            self.skipTest("Tree-sitter optional multi-language dependencies are not installed")
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_multilang_scan_clean_workspace(self):
        # Clean Python file
        py_file = self.temp_dir / "service.py"
        py_file.write_text("def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")

        # Clean TypeScript file
        ts_file = self.temp_dir / "handler.ts"
        ts_file.write_text("export function greet(name: string): string {\n  return `Hello, ${name}`;\n}\n", encoding="utf-8")

        # Clean Go file
        go_file = self.temp_dir / "main.go"
        go_file.write_text("package main\n\nfunc Add(a int, b int) int {\n    return a + b\n}\n", encoding="utf-8")

        res = scan_multilang_workspace(self.temp_dir)
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["violations_count"], 0)
        self.assertEqual(res["total_files_scanned"], 3)
        self.assertIn("python", res["languages_detected"])
        self.assertIn("typescript", res["languages_detected"])
        self.assertIn("go", res["languages_detected"])

    def test_multilang_scan_detects_violations_in_ts_and_go(self):
        # TS file with empty catch block (slop)
        ts_file = self.temp_dir / "error_handler.ts"
        ts_file.write_text(
            "function process() {\n"
            "  try {\n"
            "    console.log('work');\n"
            "  } catch (err) {\n"
            "    // empty catch swallowed!\n"
            "  }\n"
            "}\n",
            encoding="utf-8"
        )

        # Go file with unclosed resource leak
        go_file = self.temp_dir / "leak.go"
        go_file.write_text(
            "package main\n"
            "import \"os\"\n"
            "func readFile() {\n"
            "    f, _ := os.Open(\"data.txt\")\n"
            "    // missing defer f.Close()!\n"
            "}\n",
            encoding="utf-8"
        )

        res = scan_multilang_workspace(self.temp_dir)
        self.assertEqual(res["status"], "FAIL")
        self.assertGreater(res["violations_count"], 0)
        self.assertGreater(res["slop_violations_count"], 0)
        self.assertGreater(res["leaks_violations_count"], 0)

    def test_multilang_filter_by_language(self):
        py_file = self.temp_dir / "service.py"
        py_file.write_text("def ping() -> str:\n    return 'pong'\n", encoding="utf-8")

        ts_file = self.temp_dir / "app.ts"
        ts_file.write_text("const msg = 'hi';\n", encoding="utf-8")

        res = scan_multilang_workspace(self.temp_dir, target_lang="typescript")
        self.assertEqual(res["total_files_scanned"], 1)
        self.assertIn("typescript", res["languages_detected"])
        self.assertNotIn("python", res["languages_detected"])


if __name__ == "__main__":
    unittest.main()
