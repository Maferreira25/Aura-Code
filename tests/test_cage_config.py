#!/usr/bin/env python3
"""Comprehensive Unit Test Suite for Aura Cage (DevContainer Sandbox & Firewall).

Tests template syntax, devcontainer.json schema compliance, firewall script integrity,
cage scaffolding into projects, and container environment detection.
"""

import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.manage_cage import (
    CAGE_TEMPLATE_DIR,
    init_cage,
    verify_cage,
    is_running_in_container,
    main,
)


class TestManageCage(unittest.TestCase):
    """Test suite for Aura Cage DevContainer sandbox."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_templates_exist_and_valid(self):
        self.assertTrue(CAGE_TEMPLATE_DIR.exists(), "Cage template directory missing")
        expected_files = ["devcontainer.json", "Dockerfile", "init-firewall.sh", "allowed-domains.txt"]
        for f in expected_files:
            file_path = CAGE_TEMPLATE_DIR / f
            self.assertTrue(file_path.exists(), f"Missing cage file: {f}")
            self.assertGreater(file_path.stat().st_size, 50, f"Cage file too small: {f}")

    def test_devcontainer_json_schema_compliance(self):
        devcontainer_file = CAGE_TEMPLATE_DIR / "devcontainer.json"
        with open(devcontainer_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("name", data)
        self.assertIn("capAdd", data)
        self.assertIn("NET_ADMIN", data["capAdd"])
        self.assertIn("NET_RAW", data["capAdd"])
        self.assertEqual(data.get("remoteUser"), "vscode")

        # Verify readonly mounts
        mounts = data.get("mounts", [])
        self.assertTrue(len(mounts) > 0)
        for m in mounts:
            self.assertTrue(m.get("readonly"), "Mounted credential volume must be strictly readonly")

    def test_firewall_script_rules(self):
        firewall_script = (CAGE_TEMPLATE_DIR / "init-firewall.sh").read_text(encoding="utf-8")
        self.assertTrue(firewall_script.startswith("#!/bin/bash"))
        self.assertIn("iptables -A OUTPUT -j DROP", firewall_script, "Must contain default DROP rule")
        self.assertIn("allowed-domains", firewall_script)
        self.assertIn("dport 53", firewall_script, "Must allow DNS queries")

    def test_init_cage_scaffolding(self):
        res = init_cage(self.temp_dir)
        self.assertTrue(res["success"])
        devcontainer_dest = self.temp_dir / ".devcontainer"
        self.assertTrue(devcontainer_dest.exists())
        self.assertTrue((devcontainer_dest / "devcontainer.json").exists())
        self.assertTrue((devcontainer_dest / "init-firewall.sh").exists())
        self.assertTrue((devcontainer_dest / "allowed-domains.txt").exists())
        self.assertTrue((devcontainer_dest / "Dockerfile").exists())

    def test_verify_cage_detection(self):
        with patch.dict(os.environ, {"AURA_CAGE": "1"}):
            self.assertTrue(is_running_in_container())
            res = verify_cage()
            self.assertTrue(res["in_container"])

        with patch.dict(os.environ, {}, clear=True):
            with patch("pathlib.Path.exists", return_value=False):
                res = verify_cage()
                self.assertFalse(res["in_container"])

    def test_cli_cage(self):
        # CLI init
        code = main(["init", str(self.temp_dir), "--json"])
        self.assertEqual(code, 0)

        # CLI verify
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = main(["verify", "--json"])
            self.assertEqual(code, 0)
            data = json.loads(fake_out.getvalue())
            self.assertIn("in_container", data)


if __name__ == "__main__":
    unittest.main()
