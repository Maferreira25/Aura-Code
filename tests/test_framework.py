import json, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class FrameworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=json.loads((ROOT/"controls/catalog.json").read_text(encoding="utf-8"))
        cls.sources=json.loads((ROOT/"controls/source-registry.json").read_text(encoding="utf-8"))["sources"]
        cls.fm=json.loads((ROOT/"controls/failure-modes.json").read_text(encoding="utf-8"))["failure_modes"]

    def test_unique_control_ids(self):
        ids=[c["id"] for c in self.catalog["controls"]]
        self.assertEqual(len(ids),len(set(ids)))

    def test_all_control_sources_exist(self):
        for c in self.catalog["controls"]:
            for r in c["references"]:
                self.assertIn(r,self.sources,c["id"])

    def test_failure_modes_are_covered(self):
        ids={c["id"] for c in self.catalog["controls"]}
        for f in self.fm:
            self.assertTrue(f["controls"],f["id"])
            for c in f["controls"]:
                self.assertIn(c,ids,f["id"])

    def test_profiles_monotonic(self):
        levels=self.catalog["assurance_levels"]
        prior=set()
        for level in levels:
            p=json.loads((ROOT/f"profiles/{level.lower()}.json").read_text(encoding="utf-8"))
            current=set(p["included_controls"])
            self.assertTrue(prior.issubset(current))
            prior=current

    def test_no_http_sources(self):
        for sid,s in self.sources.items():
            self.assertTrue(s["url"].startswith("https://"),sid)

    def test_validate_framework_programmatic(self):
        from tools.validate_framework import validate_framework
        result = validate_framework(ROOT)
        self.assertTrue(result["success"], result["errors"])
        self.assertEqual(len(result["errors"]), 0)

    def test_no_gitignored_files_in_manifest(self):
        from tools.validate_framework import load_gitignore_patterns, is_ignored_by_framework
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        gitignore_patterns = load_gitignore_patterns(ROOT)
        violations = []
        for rel_path in manifest.get("files", {}):
            if is_ignored_by_framework(Path(rel_path), gitignore_patterns):
                violations.append(rel_path)
        self.assertEqual(violations, [], f"Gitignored or excluded files present in MANIFEST.json: {violations}")

if __name__=="__main__":
    unittest.main()
