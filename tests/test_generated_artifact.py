#!/usr/bin/env python3
"""Tests for deterministic generated-artifact evidence."""

import json
import inspect
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.generated_artifact import _copy_artifact, reproduce_artifact, reproduce_from_recipe


class GeneratedArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "input.txt").write_text("approved input\n", encoding="utf-8")
        (self.root / "generator.py").write_text(
            "from pathlib import Path\n"
            "data = Path('input.txt').read_text(encoding='utf-8')\n"
            "Path('generated.lock').write_text(data.upper(), encoding='utf-8')\n",
            encoding="utf-8",
        )
        (self.root / "audit.py").write_text("raise SystemExit(0)\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _run(self) -> dict:
        return reproduce_artifact(
            workspace=self.root,
            artifact_path="generated.lock",
            input_paths=["input.txt", "generator.py", "audit.py"],
            command=[sys.executable, "generator.py"],
            audit_command=[sys.executable, "audit.py"],
            generator="test-generator@1",
        )

    def test_two_clean_runs_and_audit_produce_evidence(self) -> None:
        result = self._run()

        self.assertEqual(result["status"], "PASS")
        self.assertEqual((self.root / "generated.lock").read_text(encoding="utf-8"), "APPROVED INPUT\n")
        evidence = Path(result["evidence_path"])
        self.assertTrue(evidence.is_file())
        self.assertEqual(json.loads(evidence.read_text(encoding="utf-8")), result)
        self.assertEqual(result["first_sha256"], result["reproduction_sha256"])

    def test_non_deterministic_output_is_rejected_without_copying(self) -> None:
        (self.root / "generator.py").write_text(
            "from pathlib import Path\nimport uuid\n"
            "Path('generated.lock').write_text(str(uuid.uuid4()), encoding='utf-8')\n",
            encoding="utf-8",
        )

        result = self._run()

        self.assertEqual(result["status"], "FAIL")
        self.assertFalse((self.root / "generated.lock").exists())
        self.assertIn("not reproducible", result["reason"])

    def test_failed_audit_is_rejected_without_copying(self) -> None:
        (self.root / "audit.py").write_text("raise SystemExit(3)\n", encoding="utf-8")

        result = self._run()

        self.assertEqual(result["status"], "FAIL")
        self.assertFalse((self.root / "generated.lock").exists())
        self.assertIn("audit command failed", result["reason"])

    def test_parent_environment_secrets_are_not_forwarded(self) -> None:
        (self.root / "generator.py").write_text(
            "import os\nfrom pathlib import Path\n"
            "Path('generated.lock').write_text(os.getenv('SECRET_CANARY', 'missing'), encoding='utf-8')\n",
            encoding="utf-8",
        )
        with patch.dict(os.environ, {"SECRET_CANARY": "must-not-leak"}):
            result = self._run()

        self.assertEqual(result["status"], "PASS")
        self.assertEqual((self.root / "generated.lock").read_text(encoding="utf-8"), "missing")

    def test_paths_cannot_escape_workspace(self) -> None:
        with self.assertRaises(ValueError):
            reproduce_artifact(
                workspace=self.root,
                artifact_path="../escape.lock",
                input_paths=["input.txt"],
                command=[sys.executable, "generator.py"],
                audit_command=[sys.executable, "audit.py"],
                generator="test-generator@1",
            )

    def test_recipe_drives_the_same_reproduction_contract(self) -> None:
        recipe = self.root / "artifact-recipe.json"
        recipe.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "artifact_path": "generated.lock",
                    "input_paths": ["input.txt", "generator.py", "audit.py"],
                    "command": [sys.executable, "generator.py"],
                    "audit_command": [sys.executable, "audit.py"],
                    "generator": "test-generator@1",
                    "working_directory": ".",
                    "timeout": 30,
                }
            ),
            encoding="utf-8",
        )

        result = reproduce_from_recipe(self.root, "artifact-recipe.json")

        self.assertEqual(result["status"], "PASS")

    def test_directory_output_is_reproduced_as_a_canonical_tree(self) -> None:
        (self.root / "generator.py").write_text(
            "from pathlib import Path\n"
            "Path('compiled/assets').mkdir(parents=True)\n"
            "Path('compiled/index.html').write_text('<h1>Ready</h1>', encoding='utf-8')\n"
            "Path('compiled/assets/app.js').write_text('ready();', encoding='utf-8')\n",
            encoding="utf-8",
        )

        result = reproduce_artifact(
            self.root,
            "compiled",
            ["generator.py", "audit.py"],
            [sys.executable, "generator.py"],
            [sys.executable, "audit.py"],
            "test-generator@1",
        )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["artifact_kind"], "directory")
        self.assertEqual([item["path"] for item in result["files"]], ["assets/app.js", "index.html"])
        self.assertTrue((self.root / "compiled" / "index.html").is_file())

    def test_final_directory_staging_does_not_inherit_private_temp_acl(self) -> None:
        source = inspect.getsource(_copy_artifact)

        self.assertNotIn("tempfile.mkdtemp", source)


if __name__ == "__main__":
    unittest.main()
