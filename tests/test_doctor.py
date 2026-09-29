#!/usr/bin/env python3
"""Truthfulness checks for installation diagnostics."""

import unittest
from pathlib import Path
from unittest.mock import patch

from typing import Dict
from tools.doctor import run_doctor


ROOT = Path(__file__).resolve().parents[1]


def _extract_checks(report: Dict[str, object]) -> Dict[str, Dict[str, object]]:
    raw_checks = report.get("checks", [])
    checks_list = raw_checks if isinstance(raw_checks, list) else []
    return {
        str(item["id"]): item
        for item in checks_list
        if isinstance(item, dict) and "id" in item
    }


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

        checks = _extract_checks(report)
        self.assertEqual(checks["studio"]["status"], "PASS")
        self.assertEqual(checks["studio_workflows"]["status"], "NOT_RUN")
        self.assertEqual(report["status"], "NOT_RUN")
        self.assertFalse(report["complete"])

    def test_docker_check_distinguishes_cli_from_running_daemon(self) -> None:
        report_down = run_doctor(
            package_root=ROOT,
            executable_lookup=lambda name: "/usr/bin/docker" if name == "docker" else None,
            docker_daemon_check=lambda path: False,
        )
        checks_down = _extract_checks(report_down)
        self.assertEqual(checks_down["docker"]["status"], "NOT_RUN")
        self.assertIn("daemon is not running", str(checks_down["docker"]["reason"]))

        report_up = run_doctor(
            package_root=ROOT,
            executable_lookup=lambda name: "/usr/bin/docker" if name == "docker" else None,
            docker_daemon_check=lambda path: True,
        )
        checks_up = _extract_checks(report_up)
        self.assertEqual(checks_up["docker"]["status"], "PASS")
        self.assertIn("daemon is responsive", str(checks_up["docker"]["reason"]))


if __name__ == "__main__":
    unittest.main()
