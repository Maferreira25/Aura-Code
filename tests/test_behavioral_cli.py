#!/usr/bin/env python3
"""CLI smoke tests for behavioral assurance engines."""

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestBehavioralCLI(unittest.TestCase):
    def test_help_exposes_behavioral_assurance_commands(self):
        cp = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "assurance.py"), "--help"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        self.assertEqual(cp.returncode, 0)
        for command in ("property", "metamorphic", "differential"):
            with self.subTest(command=command):
                self.assertIn(command, cp.stdout)


if __name__ == "__main__":
    unittest.main()
