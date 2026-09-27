#!/usr/bin/env python3
"""Fail-closed contract tests for packaged Aura Studio artifacts."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.studio_package import verify_studio_package
from tools.version import FRAMEWORK_VERSION


class StudioPackagingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.package_root = Path(self.temp_dir.name)
        self.studio_root = self.package_root / "auracode" / "studio"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_manifest(self, manifest: dict) -> None:
        self.studio_root.mkdir(parents=True, exist_ok=True)
        (self.studio_root / "manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

    def test_missing_manifest_is_not_run(self) -> None:
        result = verify_studio_package(self.package_root)

        self.assertEqual(result["status"], "NOT_RUN")
        self.assertFalse(result["complete"])

    def test_declared_incomplete_manifest_is_not_run(self) -> None:
        self._write_manifest(
            {
                "schema_version": 1,
                "framework_version": FRAMEWORK_VERSION,
                "status": "NOT_RUN",
                "reason": "Compiled assets are absent.",
            }
        )

        result = verify_studio_package(self.package_root)

        self.assertEqual(result["status"], "NOT_RUN")
        self.assertIn("Compiled assets are absent", result["reason"])

    def test_ready_manifest_requires_bilingual_hashed_assets(self) -> None:
        self._write_manifest(
            {
                "schema_version": 1,
                "framework_version": FRAMEWORK_VERSION,
                "status": "READY",
                "entrypoint": "server.py",
                "locales": ["pt-BR"],
                "assets": [],
            }
        )

        result = verify_studio_package(self.package_root)

        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(result["findings"])

    def test_ready_manifest_with_matching_assets_passes(self) -> None:
        self.studio_root.mkdir(parents=True, exist_ok=True)
        server = self.studio_root / "server.py"
        page = self.studio_root / "assets" / "index.html"
        page.parent.mkdir()
        server.write_text("def main():\n    return 0\n", encoding="utf-8")
        page.write_text("<h1>Aura Studio</h1>\n", encoding="utf-8")

        def asset(path: Path) -> dict:
            content = path.read_bytes()
            return {
                "path": path.relative_to(self.studio_root).as_posix(),
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }

        self._write_manifest(
            {
                "schema_version": 1,
                "framework_version": FRAMEWORK_VERSION,
                "status": "READY",
                "workflow_status": "NOT_RUN",
                "workflow_reason": "End-to-end workflows are not connected.",
                "entrypoint": "server.py",
                "locales": ["pt-BR", "en"],
                "assets": [asset(server), asset(page)],
            }
        )

        result = verify_studio_package(self.package_root)

        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["complete"])
        self.assertEqual(result["verified_assets"], 2)
        self.assertEqual(result["workflow_status"], "NOT_RUN")
        self.assertIn("not connected", result["workflow_reason"])

    def test_asset_path_cannot_escape_studio_directory(self) -> None:
        self._write_manifest(
            {
                "schema_version": 1,
                "framework_version": FRAMEWORK_VERSION,
                "status": "READY",
                "entrypoint": "../secret.txt",
                "locales": ["pt-BR", "en"],
                "assets": [{"path": "../secret.txt", "bytes": 1, "sha256": "0" * 64}],
            }
        )

        result = verify_studio_package(self.package_root)

        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("escapes" in item for item in result["findings"]))


if __name__ == "__main__":
    unittest.main()
