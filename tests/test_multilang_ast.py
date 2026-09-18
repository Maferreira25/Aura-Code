#!/usr/bin/env python3
"""
Unit tests for AuraCode Multi-Language AST Engine (TypeScript, JavaScript, Go).
"""

import os
import tempfile
import pytest
from tools.multilang_ast import MultiLangASTAnalyzer


def test_jsts_slop_and_empty_catch():
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
        assert "silent_exception_swallowing" in types
        assert "dummy_placeholder_string" in types
    finally:
        os.unlink(tmp_path)


def test_jsts_resource_leaks_and_security():
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
        assert len(leaks) > 0
        assert leaks[0]["type"] == "unclosed_resource_leak"

        sec = analyzer.analyze_security(tmp_path)
        types = [s["type"] for s in sec]
        assert "eval_execution" in types
        assert "shell_command_injection" in types
    finally:
        os.unlink(tmp_path)


def test_go_slop_leaks_and_security():
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
        assert any(v["type"] == "silent_exception_swallowing" for v in slop)

        leaks = analyzer.analyze_leaks(tmp_path)
        assert any(v["type"] == "unclosed_resource_leak" for v in leaks)

        sec = analyzer.analyze_security(tmp_path)
        assert any(v["type"] == "shell_command_injection" for v in sec)
    finally:
        os.unlink(tmp_path)
