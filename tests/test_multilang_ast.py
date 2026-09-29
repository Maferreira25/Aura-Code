#!/usr/bin/env python3
"""
Unit tests for AuraCode Multi-Language AST Engine (Python, TypeScript, JavaScript, Go, Java, C#).
Uses standard unittest without external test runner dependencies.
"""

import os
import tempfile
import unittest
from tools.multilang_ast import MultiLangASTAnalyzer, HAS_TREE_SITTER


class TestMultiLangAST(unittest.TestCase):

    def setUp(self):
        if not HAS_TREE_SITTER:
            self.skipTest("Tree-sitter optional multi-language dependencies are not installed")
        self.analyzer = MultiLangASTAnalyzer()

    def test_jsts_slop_and_empty_catch(self):
        with tempfile.NamedTemporaryFile("w", suffix=".ts", delete=False) as tmp:
            tmp.write("""
            function processData(data: string) {
                try {
                    console.log(data);
                } catch (e) {
                    // empty catch with inner comment
                }
                
                const dummy = "TODO: implement payment flow";
            }
            """)
            tmp_path = tmp.name

        try:
            violations = self.analyzer.analyze_slop(tmp_path)
            types = [v["type"] for v in violations]
            self.assertIn("silent_exception_swallowing", types)
            self.assertIn("dummy_placeholder_string", types)
        finally:
            os.unlink(tmp_path)

    def test_jsts_resource_leaks_and_security(self):
        with tempfile.NamedTemporaryFile("w", suffix=".ts", delete=False) as tmp:
            tmp.write("""
            import fs from 'fs';
            import cp from 'child_process';

            function unsafeRun() {
                const handle = fs.openSync('/tmp/test', 'r');
                eval("console.log('danger')");
                cp.exec("rm -rf " + process.argv[2]);
                const query = "SELECT * FROM users WHERE id = " + process.argv[3];
            }
            """)
            tmp_path = tmp.name

        try:
            leaks = self.analyzer.analyze_leaks(tmp_path)
            self.assertTrue(len(leaks) > 0)
            self.assertEqual(leaks[0]["type"], "unclosed_resource_leak")

            sec = self.analyzer.analyze_security(tmp_path)
            types = [s["type"] for s in sec]
            self.assertIn("eval_execution", types)
            self.assertIn("shell_command_injection", types)
            self.assertIn("sql_injection_vector", types)
        finally:
            os.unlink(tmp_path)

    def test_go_slop_leaks_and_security(self):
        with tempfile.NamedTemporaryFile("w", suffix=".go", delete=False) as tmp:
            tmp.write("""
            package main

            import (
                "fmt"
                "net/http"
                "os/exec"
            )

            func main() {
                resp, err := http.Get("https://example.com")
                _ = err
                if err != nil {
                    // silent
                }

                cmd := exec.Command("sh", "-c", "echo hello")
                cmd.Run()

                q := fmt.Sprintf("SELECT * FROM accounts WHERE id = %s", "123")
                _ = q
            }
            """)
            tmp_path = tmp.name

        try:
            slop = self.analyzer.analyze_slop(tmp_path)
            types = [v["type"] for v in slop]
            self.assertIn("silent_exception_swallowing", types)

            leaks = self.analyzer.analyze_leaks(tmp_path)
            self.assertTrue(any(v["type"] == "unclosed_resource_leak" for v in leaks))

            sec = self.analyzer.analyze_security(tmp_path)
            types = [s["type"] for s in sec]
            self.assertIn("shell_command_injection", types)
            self.assertIn("sql_injection_vector", types)
        finally:
            os.unlink(tmp_path)

    def test_java_slop_leaks_and_security(self):
        with tempfile.NamedTemporaryFile("w", suffix=".java", delete=False) as tmp:
            tmp.write("""
            import java.io.FileInputStream;

            public class UnsafeJava {
                public void run() {
                    try {
                        FileInputStream fis = new FileInputStream("secret.txt");
                    } catch (Exception e) {
                        // swallowed exception
                    }

                    try {
                        Runtime.getRuntime().exec("calc");
                    } catch (Exception ignored) {}

                    String sql = "SELECT * FROM users WHERE id = " + "1";
                }
            }
            """)
            tmp_path = tmp.name

        try:
            slop = self.analyzer.analyze_slop(tmp_path)
            types = [v["type"] for v in slop]
            self.assertIn("silent_exception_swallowing", types)

            leaks = self.analyzer.analyze_leaks(tmp_path)
            self.assertTrue(any(v["type"] == "unclosed_resource_leak" for v in leaks))

            sec = self.analyzer.analyze_security(tmp_path)
            types = [s["type"] for s in sec]
            self.assertIn("shell_command_injection", types)
        finally:
            os.unlink(tmp_path)

    def test_java_safe_try_with_resources_has_no_leaks(self):
        with tempfile.NamedTemporaryFile("w", suffix=".java", delete=False) as tmp:
            tmp.write("""
            import java.io.FileInputStream;

            public class SafeJava {
                public void run() {
                    try (FileInputStream fis = new FileInputStream("safe.txt")) {
                        System.out.println(fis.read());
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }
            }
            """)
            tmp_path = tmp.name

        try:
            leaks = self.analyzer.analyze_leaks(tmp_path)
            self.assertEqual(len(leaks), 0)

            slop = self.analyzer.analyze_slop(tmp_path)
            self.assertEqual(len(slop), 0)
        finally:
            os.unlink(tmp_path)

    def test_csharp_slop_leaks_and_security(self):
        with tempfile.NamedTemporaryFile("w", suffix=".cs", delete=False) as tmp:
            tmp.write("""
            using System.IO;
            using System.Diagnostics;

            public class UnsafeCSharp {
                public void Execute() {
                    try {
                        var stream = new FileStream("data.bin", FileMode.Open);
                    } catch (System.Exception ex) {
                        // swallowed
                    }

                    Process.Start("cmd.exe");
                    string query = $"SELECT * FROM accounts WHERE id = {1}";
                }
            }
            """)
            tmp_path = tmp.name

        try:
            slop = self.analyzer.analyze_slop(tmp_path)
            types = [v["type"] for v in slop]
            self.assertIn("silent_exception_swallowing", types)

            leaks = self.analyzer.analyze_leaks(tmp_path)
            self.assertTrue(any(v["type"] == "unclosed_resource_leak" for v in leaks))

            sec = self.analyzer.analyze_security(tmp_path)
            types = [s["type"] for s in sec]
            self.assertIn("shell_command_injection", types)
            self.assertIn("sql_injection_vector", types)
        finally:
            os.unlink(tmp_path)

    def test_csharp_safe_using_var_has_no_leaks(self):
        with tempfile.NamedTemporaryFile("w", suffix=".cs", delete=False) as tmp:
            tmp.write("""
            using System.IO;

            public class SafeCSharp {
                public void Execute() {
                    using var stream = new FileStream("data.bin", FileMode.Open);
                    try {
                        System.Console.WriteLine(stream.Length);
                    } catch (System.Exception ex) {
                        System.Console.Error.WriteLine(ex);
                    }
                }
            }
            """)
            tmp_path = tmp.name

        try:
            leaks = self.analyzer.analyze_leaks(tmp_path)
            self.assertEqual(len(leaks), 0)

            slop = self.analyzer.analyze_slop(tmp_path)
            self.assertEqual(len(slop), 0)
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
