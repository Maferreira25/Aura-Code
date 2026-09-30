import unittest
from pathlib import Path

from tools.multilang_ast import HAS_TREE_SITTER
from validation.tools.qualify_multilang import qualify


ROOT = Path(__file__).resolve().parents[1]


class MultiLanguageQualificationTests(unittest.TestCase):
    def setUp(self):
        if not HAS_TREE_SITTER:
            self.skipTest("Tree-sitter optional multi-language dependencies are not installed")

    def test_public_qualification_corpus_is_deterministic_baseline(self):
        report = qualify(
            ROOT / "validation" / "multilang-qualification" / "corpus.json",
            "test-revision",
        )
        self.assertEqual(report["qualification_status"], "VALID")
        self.assertTrue(report["public_corpus"])
        self.assertIn("not sufficient alone", report["claim_boundary"])

        py = report["languages"]["python"]
        ts = report["languages"]["typescript"]
        for result in (py, ts):
            self.assertEqual(result["cases"], 8)
            self.assertEqual(result["true_positive"], 4)
            self.assertEqual(result["true_negative"], 4)
            self.assertEqual(result["false_positive"], 0)
            self.assertEqual(result["false_negative"], 0)

    def test_report_contains_corpus_commitment_and_revision(self):
        report = qualify(
            ROOT / "validation" / "multilang-qualification" / "corpus.json",
            "abc123",
        )
        self.assertEqual(report["revision"], "abc123")
        self.assertEqual(len(report["corpus_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
