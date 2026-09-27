#!/usr/bin/env python3
"""Contract tests for temporal, scope-bound AuraCode build iterations."""

import json
import tempfile
import unittest
from pathlib import Path
import sys

from tools.generated_artifact import reproduce_artifact
from tools.iteration import (
    _json_hash,
    begin_iteration,
    integrate_iteration,
    seal_iteration,
    verify_iteration,
)


class IterationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "src" / "service.py").write_text("value = 1\n", encoding="utf-8")
        (self.root / "README.md").write_text("base\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_iteration_measures_changes_since_begin(self) -> None:
        opened = begin_iteration(
            self.root,
            iteration_id="ac-f01-wizard",
            requirement="AC-F01",
            scope=["src/*.py"],
        )
        self.assertEqual(opened["status"], "OPEN")

        (self.root / "src" / "service.py").write_text(
            "value = 1\nvalue = 2\n", encoding="utf-8"
        )
        result = verify_iteration(self.root, "ac-f01-wizard")

        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["total_lines_added"], 1)
        self.assertEqual(result["total_lines_deleted"], 0)
        self.assertEqual(result["changed_files"], ["src/service.py"])
        self.assertTrue(result["evidence_sha256"])
        evidence_path = Path(result["evidence_path"])
        self.assertTrue(evidence_path.is_file())
        self.assertIn(result["evidence_sha256"], evidence_path.name)
        self.assertEqual(
            json.loads(evidence_path.read_text(encoding="utf-8")),
            result,
        )

    def test_out_of_scope_change_blocks_iteration(self) -> None:
        begin_iteration(self.root, "scope-check", "AC-F01", ["src/*.py"])
        (self.root / "README.md").write_text("changed\n", encoding="utf-8")

        result = verify_iteration(self.root, "scope-check")

        self.assertFalse(result["success"])
        self.assertIn("README.md", result["out_of_scope_files"])

    def test_transient_python_build_roots_do_not_contaminate_inventory(self) -> None:
        build_file = self.root / "build" / "lib" / "module.py"
        egg_file = self.root / "sample.egg-info" / "PKG-INFO"
        dist_file = self.root / "dist" / "sample.whl"
        for path in (build_file, egg_file, dist_file):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("transient\n", encoding="utf-8")

        begin_iteration(self.root, "clean-build-roots", "D074", ["src/*.py"])
        (self.root / "src" / "service.py").write_text("value = 2\n", encoding="utf-8")
        for path in (build_file, egg_file, dist_file):
            path.unlink()

        result = verify_iteration(self.root, "clean-build-roots")

        self.assertTrue(result["success"])
        self.assertEqual(result["changed_files"], ["src/service.py"])
        self.assertEqual(result["out_of_scope_files"], [])

    def test_legacy_baseline_transient_roots_are_filtered(self) -> None:
        begin_iteration(self.root, "legacy-build-roots", "D074", ["src/*.py"])
        record_path = self.root / ".auracode" / "iterations" / "legacy-build-roots.json"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["baseline_inventory"].update(
            {
                "build/lib/module.py": {"sha256": "legacy", "bytes": 1},
                "sample.egg-info/PKG-INFO": {"sha256": "legacy", "bytes": 1},
            }
        )
        record["baseline_sha256"] = _json_hash(record["baseline_inventory"])
        record.pop("manifest_sha256")
        record["manifest_sha256"] = _json_hash(record)
        record_path.write_text(json.dumps(record), encoding="utf-8")
        (self.root / "src" / "service.py").write_text("value = 2\n", encoding="utf-8")

        result = verify_iteration(self.root, "legacy-build-roots")

        self.assertTrue(result["success"])
        self.assertEqual(result["changed_files"], ["src/service.py"])
        self.assertEqual(result["out_of_scope_files"], [])

    def test_excessive_churn_blocks_iteration(self) -> None:
        begin_iteration(
            self.root,
            "line-limit",
            "AC-F01",
            ["src/*.py"],
            max_lines=2,
        )
        (self.root / "src" / "service.py").write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")

        result = verify_iteration(self.root, "line-limit")

        self.assertFalse(result["success"])
        self.assertTrue(any(item["rule"] == "excessive_diff_churn" for item in result["violations"]))

    def test_test_change_requires_explicit_authorization(self) -> None:
        test_file = self.root / "tests" / "test_service.py"
        test_file.write_text("assert True\n", encoding="utf-8")
        begin_iteration(self.root, "test-guard", "AC-F01", ["tests/*.py"])
        test_file.write_text("assert 1 == 1\n", encoding="utf-8")

        result = verify_iteration(self.root, "test-guard")

        self.assertFalse(result["success"])
        self.assertTrue(any(item["rule"] == "unauthorized_test_tampering" for item in result["violations"]))

    def test_missing_required_metadata_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            begin_iteration(self.root, "bad id", "", [])

    def test_generated_artifact_is_exempt_only_with_matching_reproduction_evidence(self) -> None:
        generator = self.root / "generator.py"
        audit = self.root / "audit.py"
        generator.write_text(
            "from pathlib import Path\nPath('generated.lock').write_text('locked\\n', encoding='utf-8')\n",
            encoding="utf-8",
        )
        audit.write_text("raise SystemExit(0)\n", encoding="utf-8")
        begin_iteration(
            self.root,
            "generated-lock",
            "D074",
            ["generated.lock"],
            generated_artifacts=["generated.lock"],
        )
        reproduction = reproduce_artifact(
            self.root,
            "generated.lock",
            ["generator.py", "audit.py"],
            [sys.executable, "generator.py"],
            [sys.executable, "audit.py"],
            "test-generator@1",
        )
        self.assertEqual(reproduction["status"], "PASS")

        result = verify_iteration(self.root, "generated-lock")

        self.assertTrue(result["success"])
        self.assertEqual(result["total_lines_added"], 0)
        self.assertIn("generated.lock", result["generated_artifact_evidence"])

    def test_manually_written_generated_artifact_is_rejected(self) -> None:
        begin_iteration(
            self.root,
            "manual-lock",
            "D074",
            ["generated.lock"],
            generated_artifacts=["generated.lock"],
        )
        (self.root / "generated.lock").write_text("manual\n", encoding="utf-8")

        result = verify_iteration(self.root, "manual-lock")

        self.assertFalse(result["success"])
        self.assertTrue(
            any(item["rule"] == "generated_artifact_evidence_missing" for item in result["violations"])
        )

    def test_generated_directory_descendants_use_one_matching_evidence(self) -> None:
        generator = self.root / "generator.py"
        audit = self.root / "audit.py"
        generator.write_text(
            "from pathlib import Path\n"
            "Path('compiled').mkdir()\n"
            "Path('compiled/index.html').write_text('ready', encoding='utf-8')\n",
            encoding="utf-8",
        )
        audit.write_text("raise SystemExit(0)\n", encoding="utf-8")
        begin_iteration(
            self.root,
            "generated-tree",
            "D074",
            ["compiled/**"],
            generated_artifacts=["compiled"],
        )
        reproduction = reproduce_artifact(
            self.root,
            "compiled",
            ["generator.py", "audit.py"],
            [sys.executable, "generator.py"],
            [sys.executable, "audit.py"],
            "test-generator@1",
        )
        self.assertEqual(reproduction["status"], "PASS")

        result = verify_iteration(self.root, "generated-tree")

        self.assertTrue(result["success"])
        self.assertEqual(result["total_lines_added"], 0)
        self.assertIn("compiled", result["generated_artifact_evidence"])

    def test_certified_child_can_be_integrated_before_parent_resumes(self) -> None:
        begin_iteration(self.root, "parent-build", "AC-F07", ["src/*.py"])
        (self.root / "src" / "service.py").write_text("value = 1\nvalue = 2\n", encoding="utf-8")
        begin_iteration(
            self.root,
            "child-fix",
            "D073",
            ["src/helper.py", "bugs/bug.md"],
        )
        (self.root / "src" / "helper.py").write_text("fixed = True\n", encoding="utf-8")
        (self.root / "bugs").mkdir()
        (self.root / "bugs" / "bug.md").write_text("fixed\n", encoding="utf-8")
        before = verify_iteration(self.root, "parent-build")
        self.assertFalse(before["success"])

        integration = integrate_iteration(self.root, "parent-build", "child-fix")
        after = verify_iteration(self.root, "parent-build")

        self.assertEqual(integration["status"], "PASS")
        self.assertTrue(after["success"])
        self.assertEqual(after["changed_files"], ["src/service.py"])
        self.assertEqual(after["integrations"][0]["child_iteration"], "child-fix")

    def test_invalid_child_does_not_mutate_parent_manifest(self) -> None:
        begin_iteration(self.root, "safe-parent", "AC-F07", ["src/*.py"])
        begin_iteration(self.root, "oversized-child", "D073", ["bugs/bug.md"], max_lines=1)
        (self.root / "bugs").mkdir()
        (self.root / "bugs" / "bug.md").write_text("one\ntwo\n", encoding="utf-8")
        parent_record = self.root / ".auracode" / "iterations" / "safe-parent.json"
        before = parent_record.read_bytes()

        with self.assertRaises(ValueError):
            integrate_iteration(self.root, "safe-parent", "oversized-child")

        self.assertEqual(parent_record.read_bytes(), before)

    def test_child_with_out_of_scope_change_cannot_be_integrated(self) -> None:
        begin_iteration(self.root, "scoped-parent", "AC-F07", ["src/*.py"])
        begin_iteration(self.root, "scoped-child", "D073", ["src/helper.py"])
        (self.root / "src" / "helper.py").write_text("fixed = True\n", encoding="utf-8")
        (self.root / "README.md").write_text("unauthorized\n", encoding="utf-8")
        parent_record = self.root / ".auracode" / "iterations" / "scoped-parent.json"
        before = parent_record.read_bytes()

        with self.assertRaisesRegex(ValueError, "out_of_scope_change"):
            integrate_iteration(self.root, "scoped-parent", "scoped-child")

        self.assertEqual(parent_record.read_bytes(), before)

    def test_parent_with_only_certified_integrations_is_not_empty(self) -> None:
        begin_iteration(self.root, "integrated-parent", "AC-F07", ["src/*.py"])
        begin_iteration(self.root, "whole-child", "D073", ["src/*.py"])
        (self.root / "src" / "service.py").write_text("value = 2\n", encoding="utf-8")

        integrate_iteration(self.root, "integrated-parent", "whole-child")
        result = verify_iteration(self.root, "integrated-parent")

        self.assertTrue(result["success"])
        self.assertEqual(result["changed_files"], [])
        self.assertEqual(result["integrations"][0]["child_iteration"], "whole-child")

    def test_passed_iteration_can_be_sealed_after_unrelated_work_continues(self) -> None:
        begin_iteration(self.root, "completed-work", "AC-F07", ["src/*.py"])
        (self.root / "src" / "service.py").write_text("value = 2\n", encoding="utf-8")
        passed = verify_iteration(self.root, "completed-work")
        self.assertEqual(passed["status"], "PASS")

        (self.root / "README.md").write_text("later work\n", encoding="utf-8")
        self.assertEqual(verify_iteration(self.root, "completed-work")["status"], "FAIL")

        sealed = seal_iteration(self.root, "completed-work")
        historical = verify_iteration(self.root, "completed-work")

        self.assertEqual(sealed["status"], "SEALED")
        self.assertEqual(historical["status"], "PASS")
        self.assertEqual(historical["iteration_status"], "SEALED")
        self.assertEqual(historical["verification_mode"], "sealed_historical_evidence")
        self.assertFalse(historical["current_workspace_evaluated"])
        self.assertEqual(historical["sealed_evidence_sha256"], passed["evidence_sha256"])

    def test_iteration_without_pass_evidence_cannot_be_sealed(self) -> None:
        begin_iteration(self.root, "failed-work", "AC-F07", ["src/*.py"])
        (self.root / "README.md").write_text("outside scope\n", encoding="utf-8")
        self.assertEqual(verify_iteration(self.root, "failed-work")["status"], "FAIL")

        with self.assertRaisesRegex(ValueError, "PASS evidence"):
            seal_iteration(self.root, "failed-work")

    def test_tampered_sealed_evidence_is_rejected(self) -> None:
        begin_iteration(self.root, "tamper-check", "AC-F07", ["src/*.py"])
        (self.root / "src" / "service.py").write_text("value = 2\n", encoding="utf-8")
        passed = verify_iteration(self.root, "tamper-check")
        seal_iteration(self.root, "tamper-check")
        evidence_path = Path(passed["evidence_path"])
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        evidence["total_lines_added"] = 999
        evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "sealed iteration evidence integrity"):
            verify_iteration(self.root, "tamper-check")


if __name__ == "__main__":
    unittest.main()
