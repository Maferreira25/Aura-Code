#!/usr/bin/env python3
"""
Unit tests for AuraCode SARIF Aggregator and Multi-Language Phases 2 & 3 (Java, C#, SARIF).
"""

import os
import json
import tempfile
import pytest
from tools.multilang_ast import MultiLangASTAnalyzer
from tools.sarif_aggregator import SarifAggregator


def test_java_slop_leaks_and_security():
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
        assert "silent_exception_swallowing" in types
        assert "dummy_placeholder_string" in types

        leaks = analyzer.analyze_leaks(tmp_path)
        assert len(leaks) > 0
        assert leaks[0]["type"] == "unclosed_resource_leak"

        sec = analyzer.analyze_security(tmp_path)
        assert len(sec) > 0
        assert sec[0]["type"] == "shell_command_injection"
    finally:
        os.unlink(tmp_path)


def test_csharp_slop_leaks_and_security():
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
        assert "silent_exception_swallowing" in types
        assert "dummy_placeholder_string" in types

        leaks = analyzer.analyze_leaks(tmp_path)
        assert len(leaks) > 0
        assert leaks[0]["type"] == "unclosed_resource_leak"

        sec = analyzer.analyze_security(tmp_path)
        assert len(sec) > 0
        assert sec[0]["type"] == "shell_command_injection"
    finally:
        os.unlink(tmp_path)


def test_sarif_ingestion():
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
        assert res["status"] == "FAIL"
        assert res["findings_count"] == 1
        assert res["findings"][0]["tool"] == "ESLint"
        assert res["findings"][0]["rule_id"] == "no-eval"
        assert res["findings"][0]["line"] == 42
    finally:
        os.unlink(tmp_path)
