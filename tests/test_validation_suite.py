import json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCROOT=ROOT/"validation"/"scenarios"/"public"

class ValidationSuiteTests(unittest.TestCase):
    def test_scenario_ids_unique(self):
        ids=[]
        for p in SCROOT.glob("*/scenario.json"):
            ids.append(json.loads(p.read_text(encoding="utf-8"))["id"])
        self.assertEqual(len(ids),len(set(ids)))

    def test_scenario_controls_exist(self):
        catalog=json.loads((ROOT/"controls"/"catalog.json").read_text(encoding="utf-8"))
        known={c["id"] for c in catalog["controls"]}
        for p in SCROOT.glob("*/scenario.json"):
            m=json.loads(p.read_text(encoding="utf-8"))
            for c in m["controls"]:
                self.assertIn(c,known,m["id"])

    def test_automated_scenarios_have_protected_tests(self):
        for p in SCROOT.glob("*/scenario.json"):
            m=json.loads(p.read_text(encoding="utf-8"))
            if m["evaluation_mode"]=="automated":
                self.assertTrue(list((p.parent/"protected").glob("test*.py")),m["id"])

    def test_current_antigravity_metadata_schema(self):
        schema=json.loads((ROOT/"validation"/"schemas"/"result.schema.json").read_text(encoding="utf-8"))
        props=schema["properties"]
        for field in ["execution_surface","model_family","model_display_name","reasoning_effort","antigravity_version"]:
            self.assertIn(field,props)

    def test_antigravity_operational_docs_do_not_require_historical_modes(self):
        paths=[
            ROOT/"adapters"/"antigravity"/"README.md",
            ROOT/"validation"/"ANTIGRAVITY-EXPERIMENT.md",
            ROOT/"validation"/"P1-ANTIGRAVITY-IDE-STEP-BY-STEP.pt-BR.md",
        ]
        for path in paths:
            body=path.read_text(encoding="utf-8")
            # Historical terms may appear only in an explicit negative/deprecation explanation.
            for line in body.splitlines():
                if "Planning Mode" in line or "Fast Mode" in line:
                    self.assertTrue(any(k in line.lower() for k in ["do not","não","histor","lagging","not use"]), (path,line))

if __name__=="__main__":
    unittest.main()
