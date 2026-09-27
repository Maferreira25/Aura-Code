#!/usr/bin/env python3
"""Source contracts for the editor-independent Aura Studio web shell."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STUDIO = ROOT / "studio"


class StudioSourceTests(unittest.TestCase):
    def test_dependencies_are_exact_and_approved(self) -> None:
        package = json.loads((STUDIO / "package.json").read_text(encoding="utf-8"))

        self.assertEqual(
            package["dependencies"],
            {"next": "16.3.5", "react": "19.3.0", "react-dom": "19.3.0"},
        )
        self.assertEqual(
            package["devDependencies"],
            {
                "@types/node": "26.6.3",
                "@types/react": "19.3.0",
                "@types/react-dom": "19.3.0",
                "typescript": "7.0.2",
            },
        )
        for version in (*package["dependencies"].values(), *package["devDependencies"].values()):
            self.assertRegex(version, r"^\d+\.\d+\.\d+$")

    def test_next_build_is_static_and_offline_capable(self) -> None:
        config = (STUDIO / "next.config.ts").read_text(encoding="utf-8")
        package = json.loads((STUDIO / "package.json").read_text(encoding="utf-8"))

        self.assertIn('output: "export"', config)
        self.assertEqual(package["scripts"]["build"], "next build")

    def test_portuguese_and_english_have_identical_message_ids(self) -> None:
        messages = json.loads((STUDIO / "lib" / "messages.json").read_text(encoding="utf-8"))

        self.assertEqual(set(messages), {"pt-BR", "en"})
        self.assertEqual(set(messages["pt-BR"]), set(messages["en"]))
        self.assertGreaterEqual(len(messages["pt-BR"]), 20)

    def test_shell_exposes_accessible_structure_and_honest_status(self) -> None:
        page = (STUDIO / "app" / "page.tsx").read_text(encoding="utf-8")

        for marker in ("<main", "<nav", "aria-label", "aria-live", "NOT_RUN"):
            self.assertIn(marker, page)
        self.assertNotIn("100%", page)

    def test_readiness_copy_separates_package_from_guided_workflows(self) -> None:
        messages = json.loads((STUDIO / "lib" / "messages.json").read_text(encoding="utf-8"))
        readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
        readme_pt = (ROOT / "README.pt-BR.md").read_text(encoding="utf-8")

        self.assertIn("fluxos guiados", messages["pt-BR"]["reason"])
        self.assertIn("guided workflows", messages["en"]["reason"])
        self.assertNotIn("ainda não foram validados", messages["pt-BR"]["reason"])
        self.assertNotIn("have not been validated", messages["en"]["reason"])
        self.assertNotIn("not packaged yet", readme_en)
        self.assertNotIn("ainda não está empacotado", readme_pt)
        for readme in (readme_en, readme_pt):
            self.assertIn("studio_workflows", readme)
            self.assertIn("NOT_RUN", readme)


if __name__ == "__main__":
    unittest.main()
