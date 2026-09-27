#!/usr/bin/env python3
"""Truthfulness checks for installation diagnostics."""

import unittest
from pathlib import Path
from unittest.mock import patch

from tools.doctor import run_doctor


ROOT = Path(__file__).resolve().parents[1]


class DoctorTests(unittest.TestCase):
    def test_packaged_studio_does_not_imply_workflows_are_complete(self) -> None:
        studio = {
            "status": "PASS",
            "complete": True,
            "reason": "Package assets are intact.",
            "workflow_status": "NOT_RUN",
            "workflow_reason": "End-to-end workflows have not been validated.",
        }
        skills = {"status": "PASS", "verified_skills": 11}
        with (
            patch("tools.doctor.verify_studio_package", return_value=studio),
            patch("tools.doctor.verify_skill_bundle", return_value=skills),
            patch("tools.doctor._template_check", return_value={
                "id": "templates", "status": "PASS", "required": True,
                "reason": "ok", "remedy": "",
            }),
            patch("tools.doctor._verifier_check", return_value={
                "id": "verifiers", "status": "PASS", "required": True,
                "reason": "ok", "remedy": "",
            }),
        ):
            report = run_doctor(package_root=ROOT, executable_lookup=lambda name: name)

        checks = {item["id"]: item for item in report["checks"]}
        self.assertEqual(checks["studio"]["status"], "PASS")
        self.assertEqual(checks["studio_workflows"]["status"], "NOT_RUN")
        self.assertEqual(report["status"], "NOT_RUN")
        self.assertFalse(report["complete"])


if __name__ == "__main__":
    unittest.main()
