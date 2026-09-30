import json
import shutil
import tempfile
import unittest
from pathlib import Path

from validation.tools.validate_maturity_infrastructure import (
    EXPECTED_CRITERIA,
    validate_maturity_infrastructure,
)


ROOT = Path(__file__).resolve().parents[1]


class MaturityInfrastructureTests(unittest.TestCase):
    def test_repository_has_full_mat01_mat10_infrastructure(self):
        report = validate_maturity_infrastructure(ROOT)
        self.assertEqual(report["status"], "VALID", report["errors"])
        self.assertEqual(report["criteria_count"], 10)
        self.assertEqual(EXPECTED_CRITERIA[0], "MAT-01")
        self.assertEqual(EXPECTED_CRITERIA[-1], "MAT-10")
        self.assertIn("does not prove", report["claim_boundary"])

    def test_missing_template_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Copy only the maturity files needed to reach artifact coverage checks.
            for rel in [
                "validation/maturity-criteria.json",
                "validation/maturity-evidence.json",
                "validation/benchmark-registry.json",
                "validation/multilang-qualification/corpus.json",
            ]:
                src = ROOT / rel
                dst = root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

            report = validate_maturity_infrastructure(root)
            self.assertEqual(report["status"], "INVALID")
            self.assertTrue(
                any("missing maturity artifact" in error or "missing common maturity artifact" in error
                    for error in report["errors"])
            )

    def test_criterion_order_drift_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "validation", root / "validation")
            (root / "tools").mkdir()
            for rel in [
                "tools/maturity_gate.py",
            ]:
                shutil.copy2(ROOT / rel, root / rel)

            criteria_path = root / "validation" / "maturity-criteria.json"
            data = json.loads(criteria_path.read_text(encoding="utf-8"))
            data["criteria"] = list(reversed(data["criteria"]))
            criteria_path.write_text(json.dumps(data), encoding="utf-8")

            report = validate_maturity_infrastructure(root)
            self.assertEqual(report["status"], "INVALID")
            self.assertIn("canonical order", "\n".join(report["errors"]))

    def test_operational_maturity_tools_are_covered(self):
        from validation.tools.validate_maturity_infrastructure import COMMON_ARTIFACTS
        for rel in [
            "validation/tools/maturity_queue.py",
            "validation/tools/maturity_readiness.py",
            "validation/tools/maturity_handoff.py",
            "validation/tools/validate_maturity_infrastructure.py",
            "tools/maturity_cli.py",
        ]:
            self.assertIn(rel, COMMON_ARTIFACTS)


if __name__ == "__main__":
    unittest.main()
