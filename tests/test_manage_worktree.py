#!/usr/bin/env python3
"""Comprehensive Unit Test Suite for Aura Worktree Isolation.

Tests worktree creation, branch attachment, listing, clean teardown,
and merging back into target branch in isolated temporary Git repositories.
"""

import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.manage_worktree import (
    slugify_task,
    create_worktree,
    list_worktrees,
    clean_worktree,
    merge_worktree,
    main,
)


class TestManageWorktree(unittest.TestCase):
    """Test suite verifying Aura Worktree Git physical isolation."""

    def setUp(self):
        """Create a temporary Git repository with an initial commit."""
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()
        
        # Configure temporary git repo
        subprocess.run(["git", "init", "-b", "main"], cwd=str(self.temp_dir), capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "AuraTest"], cwd=str(self.temp_dir), capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "auratest@example.com"], cwd=str(self.temp_dir), capture_output=True, check=True)

        # Initial commit
        readme = self.temp_dir / "README.md"
        readme.write_text("# Test Repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=str(self.temp_dir), capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "chore: initial commit"], cwd=str(self.temp_dir), capture_output=True, check=True)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_slugify_task(self):
        self.assertEqual(slugify_task("Adicionar Autenticacao JWT"), "adicionar-autenticacao-jwt")
        self.assertEqual(slugify_task("Fix bug #123 (critical)!"), "fix-bug-123-critical")
        self.assertEqual(slugify_task("   "), "unnamed-task")

    def test_create_and_list_worktree(self):
        res = create_worktree(self.temp_dir, "implement-pix-payment")
        self.assertTrue(res["success"], f"Failed to create worktree: {res.get('error')}")
        self.assertTrue(res["created"])
        self.assertEqual(res["branch"], "feat/agent-implement-pix-payment")

        wt_path = Path(res["path"])
        self.assertTrue(wt_path.exists())
        self.assertTrue(wt_path.is_dir())

        # Verify listing shows the new worktree
        wts = list_worktrees(self.temp_dir)
        self.assertGreaterEqual(len(wts), 2)
        branches = [wt.get("branch") for wt in wts]
        self.assertIn("feat/agent-implement-pix-payment", branches)

    def test_idempotent_create_worktree(self):
        res1 = create_worktree(self.temp_dir, "my-feature")
        self.assertTrue(res1["created"])

        res2 = create_worktree(self.temp_dir, "my-feature")
        self.assertTrue(res2["success"])
        self.assertFalse(res2["created"])
        self.assertIn("already active", res2["message"])

    def test_merge_and_clean_worktree(self):
        # Create worktree
        res = create_worktree(self.temp_dir, "add-service-layer")
        wt_path = Path(res["path"])

        # Create a new file inside the worktree
        service_file = wt_path / "service.py"
        service_file.write_text("def run(): return True\n", encoding="utf-8")
        subprocess.run(["git", "add", "service.py"], cwd=str(wt_path), capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "feat: implement service layer"], cwd=str(wt_path), capture_output=True, check=True)

        # Merge worktree back to main
        merge_res = merge_worktree(self.temp_dir, "add-service-layer", target_branch="main")
        self.assertTrue(merge_res["success"], f"Merge failed: {merge_res.get('error')}")

        # Check that main repo now has service.py
        merged_file = self.temp_dir / "service.py"
        self.assertTrue(merged_file.exists())

        # Verify worktree directory was automatically removed
        self.assertFalse(wt_path.exists())

    def test_clean_worktree_explicit(self):
        res = create_worktree(self.temp_dir, "to-be-discarded")
        wt_path = Path(res["path"])
        self.assertTrue(wt_path.exists())

        clean_res = clean_worktree(self.temp_dir, "to-be-discarded", delete_branch=True)
        self.assertTrue(clean_res["success"])
        self.assertFalse(wt_path.exists())

    def test_cli_worktree(self):
        with patch("pathlib.Path.cwd", return_value=self.temp_dir):
            # Test create CLI
            code = main(["create", "cli-test-task", "--json"])
            self.assertEqual(code, 0)

            # Test list CLI
            code = main(["list"])
            self.assertEqual(code, 0)

            # Test clean CLI
            code = main(["clean", "cli-test-task", "--delete-branch", "--json"])
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
