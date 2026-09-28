#!/usr/bin/env python3
"""Contract tests for packaged AuraCode skills and installation diagnostics."""

import hashlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools import assurance
from tools.doctor import run_doctor
from tools.skill_packages import (
    REQUIRED_MANIFEST_FIELDS,
    install_bundled_skills,
    load_skill_bundle,
    verify_skill_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILLS = {
    "auracode",
    "auracode-adversary",
    "auracode-agents-help",
    "auracode-audit",
    "auracode-brainstorm",
    "auracode-cage",
    "auracode-clarify",
    "auracode-debate",
    "auracode-debugger",
    "auracode-forward",
    "auracode-guard",
    "auracode-loop",
    "auracode-new",
    "auracode-refactor",
    "auracode-worktree",
}


class SkillPackagingTests(unittest.TestCase):
    def test_bundle_contains_every_official_skill_with_complete_manifest(self) -> None:
        bundle = load_skill_bundle()
        self.assertEqual(bundle["framework_version"], "0.3.0.dev0")
        self.assertEqual({item["manifest"]["id"] for item in bundle["skills"]}, EXPECTED_SKILLS)
        for item in bundle["skills"]:
            manifest = item["manifest"]
            with self.subTest(skill=manifest["id"]):
                self.assertTrue(REQUIRED_MANIFEST_FIELDS.issubset(manifest))
                self.assertTrue(manifest["description"]["pt"])
                self.assertTrue(manifest["description"]["en"])
                self.assertEqual(manifest["files"][0]["path"], "SKILL.md")
                content = item["files"]["SKILL.md"].encode("utf-8")
                self.assertEqual(manifest["files"][0]["sha256"], hashlib.sha256(content).hexdigest())
                self.assertEqual(manifest["files"][0]["bytes"], len(content))

    def test_bundle_is_valid_and_matches_development_skill_sources(self) -> None:
        result = verify_skill_bundle(source_skills_dir=ROOT / ".agents" / "skills")
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["verified_skills"], len(EXPECTED_SKILLS))

    def test_install_materializes_exact_skills_without_checkout_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            result = install_bundled_skills(target)
            self.assertEqual(result["status"], "PASS", result)
            installed_root = target / ".agents" / "skills"
            self.assertEqual({path.name for path in installed_root.iterdir()}, EXPECTED_SKILLS)
            self.assertEqual(
                verify_skill_bundle(source_skills_dir=installed_root)["status"],
                "PASS",
            )

            changed = installed_root / "auracode" / "SKILL.md"
            changed.write_text("user-owned change\n", encoding="utf-8")
            refused = install_bundled_skills(target)
            self.assertEqual(refused["status"], "FAIL")
            self.assertIn("auracode/SKILL.md", refused["conflicts"])
            self.assertEqual(changed.read_text(encoding="utf-8"), "user-owned change\n")

    def test_doctor_validates_studio_workflows_and_packaging(self) -> None:
        report = run_doctor(package_root=ROOT)
        checks = {item["id"]: item for item in report["checks"]}
        self.assertEqual(checks["skills"]["status"], "PASS")
        self.assertEqual(checks["templates"]["status"], "PASS")
        self.assertEqual(checks["studio"]["status"], "PASS")
        self.assertEqual(checks["studio_workflows"]["status"], "PASS")
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["complete"])

    def test_public_cli_exposes_doctor_and_skill_verification(self) -> None:
        output = io.StringIO()
        with patch.object(sys, "argv", ["auracode", "doctor", "--json"]), redirect_stdout(output):
            with self.assertRaises(SystemExit) as doctor_exit:
                assurance.main()
        self.assertEqual(doctor_exit.exception.code, 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "PASS")

        output = io.StringIO()
        with patch.object(sys, "argv", ["auracode", "skills", "verify", "--json"]), redirect_stdout(output):
            with self.assertRaises(SystemExit) as skills_exit:
                assurance.main()
        self.assertEqual(skills_exit.exception.code, 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
