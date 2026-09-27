#!/usr/bin/env python3
"""Contracts for the reproducible Aura Studio compilation recipe."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STUDIO = ROOT / "studio"


class StudioBuildContractTests(unittest.TestCase):
    def test_build_id_is_fixed_and_static_export_remains_enabled(self) -> None:
        config = (STUDIO / "next.config.ts").read_text(encoding="utf-8")

        self.assertIn('output: "export"', config)
        self.assertIn('generateBuildId: async () => "auracode-studio-0.3.0-dev.0"', config)

    def test_recipe_authorizes_every_build_input_and_directory_output(self) -> None:
        recipe = json.loads((STUDIO / "build.recipe.json").read_text(encoding="utf-8"))

        self.assertEqual(recipe["artifact_path"], "studio/out")
        self.assertEqual(recipe["working_directory"], ".")
        self.assertEqual(recipe["command"], ["python", "studio/scripts/build.py"])
        self.assertEqual(recipe["audit_command"], ["python", "studio/scripts/audit.py"])
        self.assertEqual(
            set(recipe["input_paths"]),
            {
                "studio/package.json", "studio/package-lock.json", "studio/tsconfig.json",
                "studio/next-env.d.ts", "studio/next.config.ts", "studio/app",
                "studio/lib", "studio/scripts",
            },
        )

    def test_drivers_never_use_a_command_shell(self) -> None:
        for name in ("build.py", "audit.py"):
            source = (STUDIO / "scripts" / name).read_text(encoding="utf-8")
            self.assertIn("shell=False", source)
            self.assertNotIn("shell=True", source)

    def test_build_install_does_not_omit_development_tools(self) -> None:
        source = (STUDIO / "scripts" / "build.py").read_text(encoding="utf-8")

        self.assertNotIn('"NODE_ENV": "production"', source)
        self.assertIn('"--include=dev"', source)


if __name__ == "__main__":
    unittest.main()
