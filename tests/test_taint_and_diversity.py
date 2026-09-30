#!/usr/bin/env python3
"""Tests for taint analysis, external adapters and detector diversity."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.detector_diversity import compare_detectors
from tools.static_analyzer_adapters import normalize_sarif
from tools.taint_engine import analyze_workspace


class TestNativeTaint(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_parameter_to_eval_is_detected(self):
        (self.root / "app.py").write_text(
            "def run(user_code):\n    return eval(user_code)\n",
            encoding="utf-8",
        )
        result = analyze_workspace(self.root)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["findings"][0]["sink"], "eval")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_taint_propagates_through_assignment(self):
        (self.root / "app.py").write_text(
            "import os\ndef run(command):\n    value = command\n    os.system(value)\n",
            encoding="utf-8",
        )
        result = analyze_workspace(self.root)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["findings"][0]["source"], "value")

    def test_simple_sanitizer_breaks_modeled_flow(self):
        (self.root / "app.py").write_text(
            "def run(value):\n    clean = int(value)\n    return eval(str(clean))\n",
            encoding="utf-8",
        )
        result = analyze_workspace(self.root)
        self.assertEqual(result["status"], "PASS")

    def test_syntax_error_prevents_pass(self):
        (self.root / "app.py").write_text("def broken(:\n", encoding="utf-8")
        result = analyze_workspace(self.root)
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_no_supported_files_is_not_tested(self):
        (self.root / "README.md").write_text("x", encoding="utf-8")
        result = analyze_workspace(self.root)
        self.assertEqual(result["status"], "NOT_TESTED")


class TestExternalAnalyzerAdapter(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_missing_report_is_not_tested(self):
        result = normalize_sarif(self.root / "missing.sarif", analyzer_id="semgrep")
        self.assertEqual(result["status"], "NOT_TESTED")

    def test_malformed_report_is_error(self):
        path = self.root / "bad.sarif"
        path.write_text("{bad", encoding="utf-8")
        result = normalize_sarif(path, analyzer_id="codeql")
        self.assertEqual(result["status"], "ERROR")

    def test_sarif_finding_normalizes(self):
        path = self.root / "report.sarif"
        path.write_text(json.dumps({
            "version": "2.1.0",
            "runs": [{
                "tool": {"driver": {"name": "Semgrep"}},
                "results": [{
                    "ruleId": "python.lang.security.audit.eval-detected",
                    "level": "error",
                    "message": {"text": "eval detected"},
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {"uri": "app.py"},
                            "region": {"startLine": 4}
                        }
                    }]
                }]
            }]
        }), encoding="utf-8")
        result = normalize_sarif(path, analyzer_id="semgrep")
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["findings"][0]["severity"], "HIGH")


class TestDetectorDiversity(unittest.TestCase):
    def test_external_only_finding_becomes_assurance_gap(self):
        native = {
            "analyzer_id": "native-taint",
            "findings": [],
        }
        external = {
            "analyzer_id": "semgrep",
            "findings": [{
                "fingerprint": "a" * 64,
                "rule_id": "x",
                "file": "app.py",
                "line": 1,
                "sink": None,
            }],
        }
        result = compare_detectors([native, external])
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertEqual(result["assurance_gaps"][0]["type"], "ASSURANCE_GAP")
        self.assertEqual(result["assurance_gaps"][0]["detected_by"], ["semgrep"])

    def test_single_detector_is_not_tested(self):
        result = compare_detectors([{"analyzer_id": "native", "findings": []}])
        self.assertEqual(result["status"], "NOT_TESTED")

    def test_duplicate_detector_id_is_error(self):
        report = {"analyzer_id": "same", "findings": []}
        result = compare_detectors([report, report])
        self.assertEqual(result["status"], "ERROR")


class TestStaticAnalyzerSchema(unittest.TestCase):
    def test_schema_is_strict(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "schemas" / "static-analyzer-report.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
