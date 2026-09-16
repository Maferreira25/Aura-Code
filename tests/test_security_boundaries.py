#!/usr/bin/env python3
"""Regression tests for hostile-input boundaries in AuraCode tooling."""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.assurance_mcp import process_message, run_stdio_server
from tools.check_architecture import check_architecture
from tools.check_surgical_diff import (
    get_git_diff_stats,
    get_git_status,
)
from tools.verify_dependencies import verify_requirements_file


class TestArchitectureBudget(unittest.TestCase):
    def test_pattern_cannot_escape_target_root(self):
        with tempfile.TemporaryDirectory() as td:
            parent = Path(td)
            target = parent / "target"
            target.mkdir()
            (parent / "outside.py").write_text("import os\n", encoding="utf-8")
            result = check_architecture(
                target,
                contract_data={
                    "project": "escape",
                    "layers": {
                        "domain": {"path": "../outside.py", "forbidden_imports": ["os"]}
                    },
                },
            )
            self.assertFalse(result["success"])
            self.assertFalse(result["complete"])
            self.assertTrue(any("escapes" in reason for reason in result["limit_reasons"]))

    def test_oversized_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "large.py").write_text("x = 1\n" * 20, encoding="utf-8")
            result = check_architecture(
                root,
                contract_data={"project": "large", "layers": {"all": {"path": "*.py"}}},
                max_file_bytes=32,
            )
            self.assertFalse(result["success"])
            self.assertFalse(result["complete"])
            self.assertEqual(result["files_inspected"], 0)

    def test_file_count_budget_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for index in range(3):
                (root / f"module_{index}.py").write_text("x = 1\n", encoding="utf-8")
            result = check_architecture(
                root,
                contract_data={"project": "many", "layers": {"all": {"path": "*.py"}}},
                max_files=2,
            )
            self.assertFalse(result["success"])
            self.assertFalse(result["complete"])
            self.assertLessEqual(result["files_discovered"], 2)


class TestRequirementsBudget(unittest.TestCase):
    def test_oversized_requirements_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            requirements = Path(td) / "requirements.txt"
            requirements.write_text("requests==2.31.0\n", encoding="utf-8")
            result = verify_requirements_file(
                requirements,
                offline=True,
                max_file_bytes=8,
            )
            self.assertFalse(result["success"])
            self.assertFalse(result["complete"])
            self.assertEqual(result["findings"], [])

    def test_package_count_budget_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            requirements = Path(td) / "requirements.txt"
            requirements.write_text("one\ntwo\nthree\n", encoding="utf-8")
            result = verify_requirements_file(
                requirements,
                offline=True,
                max_packages=2,
            )
            self.assertFalse(result["success"])
            self.assertFalse(result["complete"])
            self.assertEqual(result["findings"], [])

    def test_total_deadline_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            requirements = Path(td) / "requirements.txt"
            requirements.write_text("requests\n", encoding="utf-8")
            result = verify_requirements_file(
                requirements,
                offline=False,
                total_timeout=0,
            )
            self.assertFalse(result["success"])
            self.assertFalse(result["complete"])
            self.assertEqual(result["total_packages"], 1)


class TestMCPFraming(unittest.TestCase):
    def test_direct_oversized_message_is_rejected(self):
        response = process_message(
            json.dumps({"jsonrpc": "2.0", "id": 7, "method": "ping", "padding": "x" * 80}),
            max_message_bytes=64,
        )
        self.assertEqual(response["error"]["code"], -32001)

    def test_non_object_message_is_invalid_request(self):
        response = process_message("[]")
        self.assertEqual(response["error"]["code"], -32600)

    def test_non_object_params_is_invalid_request(self):
        response = process_message(
            json.dumps({"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": []})
        )
        self.assertEqual(response["error"]["code"], -32602)

    def test_server_drains_oversized_frame_and_recovers(self):
        oversized = b'{"jsonrpc":"2.0","id":1,"method":"ping","padding":"' + b"x" * 80 + b'"}\n'
        valid = b'{"jsonrpc":"2.0","id":2,"method":"ping"}\n'
        output = io.StringIO()
        run_stdio_server(
            input_stream=io.BytesIO(oversized + valid),
            output_stream=output,
            max_message_bytes=64,
        )
        responses = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(responses[0]["error"]["code"], -32001)
        self.assertEqual(responses[1]["id"], 2)
        self.assertEqual(responses[1]["result"], {})


@unittest.skipUnless(shutil := __import__("shutil").which("git"), "git is required")
class TestGitExecutionBoundary(unittest.TestCase):
    def _init_repo(self, root: Path) -> None:
        subprocess.run([shutil, "init", "-q", str(root)], check=True)
        subprocess.run([shutil, "-C", str(root), "config", "user.email", "audit@example.invalid"], check=True)
        subprocess.run([shutil, "-C", str(root), "config", "user.name", "Audit Test"], check=True)

    def _fsmonitor_hook(self, repo: Path, marker: Path) -> Path:
        if os.name == "nt":
            hook = repo / "fsmonitor.cmd"
            hook.write_text(f'@echo off\r\necho executed>"{marker}"\r\nexit /b 0\r\n', encoding="utf-8")
        else:
            hook = repo / "fsmonitor.sh"
            hook.write_text(f'#!/bin/sh\nprintf executed > "{marker}"\nexit 0\n', encoding="utf-8")
            hook.chmod(0o700)
        return hook

    def test_repository_fsmonitor_is_not_executed(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._init_repo(repo)
            marker = repo / "executed.txt"
            hook = self._fsmonitor_hook(repo, marker)
            subprocess.run(
                [shutil, "-C", str(repo), "config", "core.fsmonitor", hook.as_posix()],
                check=True,
            )
            changes, error = get_git_status(repo)
            self.assertIsNone(error)
            self.assertIsInstance(changes, list)
            self.assertFalse(marker.exists())

    def test_stats_include_staged_unstaged_and_untracked(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._init_repo(repo)
            staged = repo / "staged.txt"
            unstaged = repo / "unstaged.txt"
            staged.write_text("base\n", encoding="utf-8")
            unstaged.write_text("base\n", encoding="utf-8")
            subprocess.run([shutil, "-C", str(repo), "add", "."], check=True)
            subprocess.run([shutil, "-C", str(repo), "commit", "-qm", "base"], check=True)

            staged.write_text("base\nstaged\n", encoding="utf-8")
            subprocess.run([shutil, "-C", str(repo), "add", "staged.txt"], check=True)
            unstaged.write_text("base\nunstaged\n", encoding="utf-8")
            (repo / "untracked.txt").write_text("one\ntwo\n", encoding="utf-8")

            changes, error = get_git_status(repo)
            self.assertIsNone(error)
            stats = get_git_diff_stats(repo, changes=changes)
            self.assertTrue(stats["complete"])
            self.assertEqual(stats["total_added"], 4)
            self.assertEqual(stats["total_deleted"], 0)


if __name__ == "__main__":
    unittest.main()
