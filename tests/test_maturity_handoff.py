import json
import tempfile
import unittest
from pathlib import Path

from validation.tools.maturity_handoff import build_handoff, write_handoff


ROOT = Path(__file__).resolve().parents[1]


class MaturityHandoffTests(unittest.TestCase):
    def test_handoff_freezes_revision_hashes_and_remaining_work(self):
        report = build_handoff(ROOT, "deadbeef")
        self.assertEqual(report["revision"], "deadbeef")
        self.assertFalse(report["ready_at_export"])
        self.assertEqual(report["decision_at_export"], "BLOCK")
        self.assertGreater(report["remaining_count"], 0)
        self.assertEqual(len(report["manifest_sha256"]), 64)
        self.assertIn("does not change maturity status", report["claim_boundary"])

    def test_handoff_does_not_embed_private_split_content(self):
        report = build_handoff(ROOT, "deadbeef")
        serialized = json.dumps(report)
        self.assertNotIn("validation/private/", serialized)
        self.assertIn("does not embed private/fresh scenario contents", report["privacy_boundary"])

    def test_write_handoff_creates_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = write_handoff(ROOT, "deadbeef", Path(tmp))
            json_path = Path(result["json"])
            md_path = Path(result["markdown"])
            self.assertTrue(json_path.is_file())
            self.assertTrue(md_path.is_file())
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["format"], "AURACODE-MATURITY-HANDOFF-V1")
            self.assertIn("Frozen revision", md_path.read_text(encoding="utf-8"))

    def test_empty_revision_is_rejected(self):
        with self.assertRaises(ValueError):
            build_handoff(ROOT, "   ")


if __name__ == "__main__":
    unittest.main()
