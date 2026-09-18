#!/usr/bin/env python3
"""
Unit tests for AuraCode Multi-Language AST Engine (TypeScript, JavaScript, Go).
Uses standard unittest without external test runner dependencies.
"""

import os
import tempfile
import unittest
from tools.multilang_ast import MultiLangASTAnalyzer


class TestMultiLangAST(unittest.TestCase):

    def test_jsts_slop_and_empty_catch(self):
        analyzer = MultiLangASTAnalyzer()
        with tempfile.NamedTemporaryFile("w", suffix=".ts", delete=False) as tmp:
            tmp.write("""
            function processData(data: string) {
                try {
                    console.log(data);
                } catch (e) {}
                
                const dummy = "TODO: implement payment flow";
            }
            """)
            tmp_path = tmp.name

        try:
            violations = analyzer.analyze_slop(tmp_path)
            types = [v["type"] for v in violations]
            self.assertIn("silent_exception_swallowing", types)
            self.assertIn("dummy_placeholder_string", types)
        finally:
            os.unlink(tmp_path)

    def test_jsts_resource_leaks_and_security(self):
        analyzer = MultiLangASTAnalyzer()
        with tempfile.NamedTemporaryFile("w", suffix=".ts", delete=False) as tmp:
            tmp.write("""
            import fs from 'fs';
            import cp from 'child_process';

            function unsafeRun() {
                const handle = fs.openSync('/tmp/test', 'r');
                eval("console.log('danger')");
                cp.exec("rm -rf " + process.argv[2]);
            }
            """)
            tmp_path = tmp.name

        try:
            leaks = analyzer.analyze_leaks(tmp_path)
            self.assertTrue(len(leaks) > 0)
            self.assertEqual(leaks[0]["type"], "unclosed_resource_leak")

            sec = analyzer.analyze_security(tmp_path)
            types = [s["type"] for s in sec]
            self.assertIn("eval_execution", types)
            self.assertIn("shell_command_injection", types)
        finally:
            os.unlink(tmp_path)

    def test_go_slop_leaks_and_security(self):
        analyzer = MultiLangASTAnalyzer()
        with tempfile.NamedTemporaryFile("w", suffix=".go", delete=False) as tmp:
            tmp.write("""
            package main

            import (
                "net/http"
                "os/exec"
            )

            func main() {
                resp, err := http.Get("https://example.com")
                _ = err

                cmd := exec.Command("sh", "-c", "echo hello")
                cmd.Run()
            }
            """)
            tmp_path = tmp.name

        try:
            slop = analyzer.analyze_slop(tmp_path)
            self.assertTrue(any(v["type"] == "silent_exception_swallowing" for v in slop))

            leaks = analyzer.analyze_leaks(tmp_path)
            self.assertTrue(any(v["type"] == "unclosed_resource_leak" for v in leaks))

            sec = analyzer.analyze_security(tmp_path)
            self.assertTrue(any(v["type"] == "shell_command_injection" for v in sec))
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
