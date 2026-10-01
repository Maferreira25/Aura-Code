import json
import tempfile
import unittest
from pathlib import Path

from validation.tools.private_split import build_commitment, verify_commitment


class PrivateSplitCommitmentTests(unittest.TestCase):
    def test_commitment_verifies_unchanged_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.json").write_text('{"x":1}', encoding="utf-8")
            (root / "nested").mkdir()
            (root / "nested" / "b.txt").write_text("secret scenario", encoding="utf-8")
            commitment = build_commitment(root)
            result = verify_commitment(root, commitment)
            self.assertEqual(result["status"], "PASS")
            self.assertTrue(result["matched"])
            self.assertFalse(commitment["paths_disclosed"])
            self.assertNotIn("a.json", json.dumps(commitment))

    def test_any_content_change_breaks_commitment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "scenario.txt"
            path.write_text("v1", encoding="utf-8")
            commitment = build_commitment(root)
            path.write_text("v2", encoding="utf-8")
            result = verify_commitment(root, commitment)
            self.assertEqual(result["status"], "FAIL")
            self.assertFalse(result["matched"])

    def test_file_addition_breaks_commitment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "one.txt").write_text("one", encoding="utf-8")
            commitment = build_commitment(root)
            (root / "two.txt").write_text("two", encoding="utf-8")
            result = verify_commitment(root, commitment)
            self.assertFalse(result["matched"])
            self.assertNotEqual(result["expected_file_count"], result["actual_file_count"])

    def test_empty_split_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                build_commitment(Path(tmp))


if __name__ == "__main__":
    unittest.main()
