#!/usr/bin/env python3
"""Tests for independent static analyzer adapters and detector diversity."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tools.static_analyzer_adapter import (
    AnalyzerSpec,
    _command_identity_ok,
    detector_diversity_gaps,
    evaluate_static_suite,
)


class TestStaticAnalyzerAdapter(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _writer(self, severity="error"):
        script = self.root / "fake_analyzer.py"
        script.write_text(
            "import json, sys\n"
            "out = sys.argv[1]\n"
            f"level = {severity!r}\n"
            "data = {'version':'2.1.0','runs':[{'tool':{'driver':{'name':'FakeAnalyzer'}},"
            "'results':[{'ruleId':'taint-flow','level':level,'message':{'text':'flow'},"
            "'locations':[{'physicalLocation':{'artifactLocation':{'uri':'src/app.py'},"
            "'region':{'startLine':12}}}]}]}]}\n"
            "open(out,'w',encoding='utf-8').write(json.dumps(data))\n",
            encoding="utf-8",
        )
        return script

    def _manifest(self, severity="error"):
        script = self._writer(severity)
        return {
            "schema_version": "1.0.0",
            "suite_id": "STATIC-TEST-001",
            "analyzers": [
                {
                    "analyzer_id": "fake",
                    "kind": "custom_sarif",
                    "command": [sys.executable, script.name, "out.sarif"],
                    "sarif_output": "out.sarif",
                    "accepted_exit_codes": [0],
                    "timeout_seconds": 10,
                    "required": True,
                }
            ],
            "diversity": {"enabled": True, "line_tolerance": 2},
        }

    def test_named_adapter_identity_validation(self):
        self.assertTrue(_command_identity_ok(AnalyzerSpec("s","semgrep",["semgrep","scan"],"x", [0], 1, True)))
        self.assertTrue(_command_identity_ok(AnalyzerSpec("c","codeql",["codeql","database","analyze"],"x", [0], 1, True)))
        self.assertFalse(_command_identity_ok(AnalyzerSpec("s","semgrep",["python","fake.py"],"x", [0], 1, True)))

    def test_high_external_finding_is_fail(self):
        result = evaluate_static_suite(self.root, self._manifest("error"), native_findings=[])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["progression"]["state"], "BLOCKED")
        self.assertEqual(result["assurance_gaps_count"], 1)

    def test_lower_external_finding_is_inconclusive(self):
        result = evaluate_static_suite(self.root, self._manifest("warning"), native_findings=[])
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_matching_native_location_closes_diversity_gap(self):
        result = evaluate_static_suite(
            self.root,
            self._manifest("error"),
            native_findings=[{"file": "src/app.py", "line": 11}],
        )
        self.assertEqual(result["assurance_gaps_count"], 0)

    def test_external_only_finding_is_assurance_gap_not_confirmed_claim(self):
        result = evaluate_static_suite(self.root, self._manifest("error"), native_findings=[])
        gap = result["assurance_gaps"][0]
        self.assertEqual(gap["type"], "ASSURANCE_GAP")
        self.assertNotIn("confirmed", gap["message"].lower())

    def test_required_missing_analyzer_is_error(self):
        manifest = self._manifest()
        manifest["analyzers"][0]["command"] = ["definitely-missing-aura-analyzer"]
        result = evaluate_static_suite(self.root, manifest, native_findings=[])
        self.assertEqual(result["status"], "ERROR")

    def test_optional_missing_analyzer_is_not_tested_and_blocks(self):
        manifest = self._manifest()
        manifest["analyzers"][0]["command"] = ["definitely-missing-aura-analyzer"]
        manifest["analyzers"][0]["required"] = False
        result = evaluate_static_suite(self.root, manifest, native_findings=[])
        self.assertEqual(result["status"], "NOT_TESTED")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_sarif_path_escape_is_error(self):
        manifest = self._manifest()
        manifest["analyzers"][0]["sarif_output"] = "../outside.sarif"
        result = evaluate_static_suite(self.root, manifest, native_findings=[])
        self.assertEqual(result["status"], "ERROR")


class TestStaticAnalyzerSchema(unittest.TestCase):
    def test_schema_is_strict(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "schemas" / "static-analysis-suite.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["properties"]["analyzers"]["items"]["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
