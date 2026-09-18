#!/usr/bin/env python3
"""
Unit tests for AuraCode SARIF Aggregator and Multi-Language Phases 2 & 3 (Java, C#, SARIF).
Uses standard unittest without external test runner dependencies.
"""

import os
import json
import tempfile
import unittest
from tools.multilang_ast import MultiLangASTAnalyzer
from tools.sarif_aggregator import SarifAggregator


class TestSarifAggregatorAndPhase2(unittest.TestCase):

    def test_java_slop_leaks_and_security(self):
        analyzer = MultiLangASTAnalyzer()
        with tempfile.NamedTemporaryFile("w", suffix=".java", delete=False) as tmp:
            tmp.write("""
            public class App {
                public static void main(String[] args) {
                    try {
                        FileInputStream fis = new FileInputStream("test.txt");
                        Runtime.getRuntime().exec("rm -rf /tmp");
                    } catch (Exception e) {}
                    
                    String todo = "TODO: implement authentication";
                }
            }
            """)
            tmp_path = tmp.name

        try:
            slop = analyzer.analyze_slop(tmp_path)
            types = [s["type"] for s in slop]
            self.assertIn("silent_exception_swallowing", types)
            self.assertIn("dummy_placeholder_string", types)

            leaks = analyzer.analyze_leaks(tmp_path)
            self.assertTrue(len(leaks) > 0)
            self.assertEqual(leaks[0]["type"], "unclosed_resource_leak")

            sec = analyzer.analyze_security(tmp_path)
            self.assertTrue(len(sec) > 0)
            self.assertEqual(sec[0]["type"], "shell_command_injection")
        finally:
            os.unlink(tmp_path)

    def test_csharp_slop_leaks_and_security(self):
        analyzer = MultiLangASTAnalyzer()
        with tempfile.NamedTemporaryFile("w", suffix=".cs", delete=False) as tmp:
            tmp.write("""
            using System;
            using System.Diagnostics;
            using System.IO;

            class Program {
                static void Main() {
                    try {
                        FileStream fs = new FileStream("data.bin", FileMode.Open);
                        Process.Start("calc.exe");
                    } catch (Exception) {}

                    string dummy = "dummy response data";
                }
            }
            """)
            tmp_path = tmp.name

        try:
            slop = analyzer.analyze_slop(tmp_path)
            types = [s["type"] for s in slop]
            self.assertIn("silent_exception_swallowing", types)
            self.assertIn("dummy_placeholder_string", types)

            leaks = analyzer.analyze_leaks(tmp_path)
            self.assertTrue(len(leaks) > 0)
            self.assertEqual(leaks[0]["type"], "unclosed_resource_leak")

            sec = analyzer.analyze_security(tmp_path)
            self.assertTrue(len(sec) > 0)
            self.assertEqual(sec[0]["type"], "shell_command_injection")
        finally:
            os.unlink(tmp_path)

    def test_sarif_ingestion(self):
        aggregator = SarifAggregator()
        sample_sarif = {
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "ESLint"
                        }
                    },
                    "results": [
                        {
                            "ruleId": "no-eval",
                            "level": "error",
                            "message": {
                                "text": "eval() call detected"
                            },
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "src/app.js"
                                        },
                                        "region": {
                                            "startLine": 42
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        with tempfile.NamedTemporaryFile("w", suffix=".sarif", delete=False) as tmp:
            json.dump(sample_sarif, tmp)
            tmp_path = tmp.name

        try:
            res = aggregator.parse_sarif_file(tmp_path)
            self.assertEqual(res["status"], "FAIL")
            self.assertEqual(res["findings_count"], 1)
            self.assertEqual(res["findings"][0]["tool"], "ESLint")
            self.assertEqual(res["findings"][0]["rule_id"], "no-eval")
            self.assertEqual(res["findings"][0]["line"], 42)
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
