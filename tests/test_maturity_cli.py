import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools import maturity_cli


ROOT = Path(__file__).resolve().parents[1]


class MaturityCliTests(unittest.TestCase):
    def _run(self, args):
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = maturity_cli.main(args)
        return code, stream.getvalue()

    def test_legacy_maturity_invocation_still_routes_to_gate(self):
        code, output = self._run([str(ROOT), "--report-only"])
        self.assertEqual(code, 0)
        self.assertIn("Maturity target:", output)

    def test_explicit_gate_alias_is_supported(self):
        code, output = self._run(["gate", str(ROOT), "--report-only"])
        self.assertEqual(code, 0)
        self.assertIn("Decision:", output)

    def test_readiness_subcommand_is_report_only_capable(self):
        code, output = self._run(["readiness", str(ROOT), "--report-only"])
        self.assertEqual(code, 0)
        self.assertIn("Stable maturity:", output)
        self.assertIn("Remaining criteria:", output)

    def test_infrastructure_subcommand_validates_repository(self):
        code, output = self._run(["infrastructure", str(ROOT)])
        self.assertEqual(code, 0)
        self.assertIn("Maturity infrastructure: VALID", output)

    def test_study_subcommand_preserves_validator_failure(self):
        code, output = self._run([
            "study",
            "governance",
            str(ROOT / "validation" / "config" / "governance-1.0.example.json"),
        ])
        self.assertEqual(code, 1)
        self.assertIn("GOVERNANCE_1_0: INVALID", output)

    def test_handoff_subcommand_routes_to_exporter(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            code, output = self._run([
                "handoff",
                str(ROOT),
                "--revision",
                "deadbeef",
                "--output-dir",
                tmp,
            ])
            self.assertEqual(code, 0)
            self.assertIn("Maturity handoff generated", output)

    def test_record_subcommand_requires_explicit_confirmation(self):
        import tempfile, json
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "validation").mkdir()
            (root / "validation" / "maturity-evidence.json").write_text(
                json.dumps({
                    "target": "stable-1.0",
                    "criteria": {
                        "MAT-10": {
                            "status": "UNKNOWN",
                            "evidence": [],
                            "rationale": "not yet adopted",
                        }
                    },
                }),
                encoding="utf-8",
            )
            package = root / "governance.json"
            package.write_text("{}", encoding="utf-8")
            code, output = self._run([
                "record",
                "MAT-10",
                str(package),
                "--reviewed-by",
                "reviewer",
                "--reviewed-at",
                "2026-09-30T12:00:00Z",
                "--root",
                str(root),
            ])
            self.assertEqual(code, 2)
            self.assertIn("confirm-reviewed", output)


if __name__ == "__main__":
    unittest.main()
