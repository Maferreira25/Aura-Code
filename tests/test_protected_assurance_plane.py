#!/usr/bin/env python3
"""Tests for Protected Assurance Plane boundaries."""

import json
import unittest
from pathlib import Path

from tools.protected_assurance_plane import (
    PLANE_APPEND_ONLY,
    PLANE_DEVELOPER,
    PLANE_HELD_OUT,
    PLANE_PROTECTED,
    PLANE_PUBLIC_TEST,
    can_read,
    can_write,
    classify_path,
    evaluate_changes,
    load_policy,
)


ROOT = Path(__file__).resolve().parents[1]


class TestProtectedAssurancePlane(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_policy(ROOT / "policies" / "protected-assurance-plane.json")

    def test_policy_schema_is_strict(self):
        schema = json.loads(
            (ROOT / "schemas" / "protected-assurance-plane.schema.json").read_text(encoding="utf-8")
        )
        self.assertFalse(schema["additionalProperties"])

    def test_classifies_critical_planes(self):
        cases = {
            "tools/assess.py": PLANE_PROTECTED,
            "schemas/evidence.schema.json": PLANE_PROTECTED,
            ".github/workflows/validate.yml": PLANE_PROTECTED,
            "validation/held_out/secret_test.py": PLANE_HELD_OUT,
            "_auracode_evidence/run.json": PLANE_APPEND_ONLY,
            "tests/test_app.py": PLANE_PUBLIC_TEST,
            "src/app.py": PLANE_DEVELOPER,
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(classify_path(path, self.policy), expected)

    def test_developer_cannot_write_protected_assets(self):
        for path in (
            "tools/assess.py",
            "controls/catalog.json",
            "profiles/al4.json",
            "schemas/evidence.schema.json",
            ".github/workflows/validate.yml",
            "MANIFEST.json",
        ):
            with self.subTest(path=path):
                self.assertFalse(can_write(path, self.policy, actor="developer"))

    def test_property_engine_is_protected(self):
        self.assertEqual(classify_path("tools/property_engine.py", self.policy), PLANE_PROTECTED)
        self.assertFalse(can_write("tools/property_engine.py", self.policy, actor="developer"))

    def test_developer_cannot_read_or_write_held_out(self):
        path = "validation/held_out/secret_case.py"
        self.assertFalse(can_read(path, self.policy, actor="developer"))
        self.assertFalse(can_write(path, self.policy, actor="developer"))

    def test_evidence_is_append_only(self):
        path = "_auracode_evidence/EV-1.json"
        self.assertTrue(can_write(path, self.policy, status="??", actor="developer"))
        self.assertTrue(can_write(path, self.policy, status="A", actor="developer"))
        self.assertFalse(can_write(path, self.policy, status="M", actor="developer"))
        self.assertFalse(can_write(path, self.policy, status="D", actor="developer"))

    def test_public_tests_are_not_self_modifiable(self):
        self.assertFalse(can_write("tests/test_auth.py", self.policy, actor="developer"))

    def test_developer_source_is_writable(self):
        self.assertTrue(can_write("src/auth.py", self.policy, actor="developer"))

    def test_change_set_fails_closed_on_protected_tampering(self):
        result = evaluate_changes(
            [
                {"file": "src/auth.py", "status": "M"},
                {"file": "tools/assess.py", "status": "M"},
            ],
            self.policy,
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["violations"][0]["rule"], "protected_assurance_tampering")

    def test_change_set_blocks_existing_evidence_mutation(self):
        result = evaluate_changes(
            [{"file": "_auracode_evidence/EV-1.json", "status": "M"}],
            self.policy,
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["violations"][0]["rule"], "evidence_not_append_only")


if __name__ == "__main__":
    unittest.main()
