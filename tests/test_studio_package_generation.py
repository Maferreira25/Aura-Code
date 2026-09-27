#!/usr/bin/env python3
"""Contracts for deterministic Aura Studio package generation."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STUDIO = ROOT / "studio"


class StudioPackageGenerationTests(unittest.TestCase):
    def test_asset_recipe_copies_only_the_reproduced_static_tree(self) -> None:
        recipe = json.loads((STUDIO / "package-assets.recipe.json").read_text(encoding="utf-8"))

        self.assertEqual(recipe["artifact_path"], "auracode/studio/assets")
        self.assertEqual(recipe["input_paths"], ["studio/out", "studio/scripts/package_assets.py"])
        self.assertEqual(recipe["command"], ["python", "studio/scripts/package_assets.py"])
        self.assertEqual(recipe["audit_command"], ["python", "studio/scripts/package_assets.py", "--verify"])

    def test_manifest_recipe_hashes_server_and_assets(self) -> None:
        recipe = json.loads((STUDIO / "package-manifest.recipe.json").read_text(encoding="utf-8"))

        self.assertEqual(recipe["artifact_path"], "auracode/studio/manifest.json")
        self.assertEqual(
            set(recipe["input_paths"]),
            {"VERSION", "auracode/studio/server.py", "auracode/studio/assets", "studio/scripts/package_manifest.py"},
        )
        self.assertEqual(recipe["audit_command"], ["python", "studio/scripts/package_manifest.py", "--verify"])

    def test_python_distribution_includes_nested_studio_assets(self) -> None:
        project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn('"auracode.studio" = ["assets/**/*"]', project)


if __name__ == "__main__":
    unittest.main()
