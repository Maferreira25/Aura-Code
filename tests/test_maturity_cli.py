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

    def test_build_subcommand_routes_to_package_builder(self):
        import tempfile, json
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = root / "p2.json"
            results = root / "results"
            results.mkdir()
            plan.write_text(json.dumps({
                "study_id": "P2-X",
                "preregistered": True,
                "private_or_fresh_split": True,
                "arms": ["A0", "A1", "A2"],
                "repetitions_per_arm": 5,
                "private_split_commitment_sha256": "a" * 64,
                "model_agent_pairings": [{
                    "model_family": "family",
                    "model_display_name": "Model X",
                    "agent": "Agent X",
                    "reasoning_effort": "medium",
                }],
                "scenarios": [
                    {
                        "id": f"S{i:02d}",
                        "family": [
                            "security","data-integrity","supply-chain",
                            "evaluator-integrity","architecture","reliability"
                        ][i % 6],
                    }
                    for i in range(30)
                ],
            }), encoding="utf-8")
            output = root / "package.json"
            code, text_output = self._run([
                "build", "p2",
                "--root", str(root),
                "--plan", str(plan),
                "--results-dir", str(results),
                "--output", str(output),
                "--allow-incomplete",
            ])
            self.assertEqual(code, 0)
            self.assertTrue(output.is_file())
            package = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(package["completed"])
            self.assertEqual(package["expected_attempts"], 450)
            self.assertEqual(package["builder"]["missing"], 450)


if __name__ == "__main__":
    unittest.main()
