"""Negative and physical execution tests for evidence v1."""
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.evidence_engine import execute, verify, main, canonical_bytes, digest_bytes


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "source.txt").write_text("original", encoding="utf-8")
        self.commit_patch = patch("tools.evidence_engine.current_commit", return_value="a" * 40)
        self.commit_patch.start()
        self.addCleanup(self.commit_patch.stop)

    def run_record(self, script="print('verified')"):
        return execute(self.root, "VER-01", "test-python", ["source.txt"],
                       [sys.executable, "-c", script])

    def test_real_execution_round_trip(self):
        record = self.run_record()
        self.assertEqual(verify(record, self.root)["status"], "PASS")
        self.assertEqual(bytes.fromhex(record["stdout_hex"]), b"verified\n")

    def test_failed_execution_never_passes(self):
        record = self.run_record("raise SystemExit(7)")
        self.assertEqual(record["returncode"], 7)
        self.assertEqual(verify(record, self.root)["status"], "FAIL")

    def test_mutation_during_execution_is_stale(self):
        record = self.run_record("from pathlib import Path; Path('source.txt').write_text('changed')")
        self.assertEqual(record["status"], "STALE")
        self.assertEqual(verify(record, self.root)["status"], "STALE")

    def test_later_scope_change_is_stale(self):
        record = self.run_record()
        (self.root / "source.txt").write_text("changed", encoding="utf-8")
        self.assertEqual(verify(record, self.root)["status"], "STALE")

    def test_changed_commit_is_stale(self):
        record = self.run_record()
        with patch("tools.evidence_engine.current_commit", return_value="b" * 40):
            self.assertEqual(verify(record, self.root)["status"], "STALE")

    def test_tampered_and_incomplete_records_block(self):
        record = self.run_record()
        record["control_id"] = "SEC-01"
        self.assertEqual(verify(record, self.root)["status"], "TAMPERED")
        del record["verification_id"]
        self.assertEqual(verify(record, self.root)["status"], "INCOMPLETE")

    def test_output_hash_is_checked_even_after_record_rehash(self):
        record = self.run_record()
        record["stdout_hex"] = b"forged".hex()
        record["digest"] = digest_bytes(canonical_bytes({k: v for k, v in record.items() if k != "digest"}))
        self.assertEqual(verify(record, self.root)["status"], "TAMPERED")

    def test_missing_command_is_error(self):
        record = execute(self.root, "VER-01", "test", ["source.txt"],
                         [str(self.root / "missing-executable")])
        self.assertEqual(record["status"], "ERROR")
        self.assertEqual(verify(record, self.root)["status"], "FAIL")

    def test_paths_cannot_escape_or_be_empty(self):
        for scope in ([], ["../outside"], [str(self.root / "source.txt")],
                      ["source.txt", "source.txt"]):
            with self.subTest(scope=scope), self.assertRaises(ValueError):
                execute(self.root, "VER-01", "test", scope, [sys.executable, "-V"])

    def test_duplicate_json_fields_block_cli(self):
        path = self.root / "bad.json"
        path.write_text('{"status":"FAIL","status":"PASS"}', encoding="utf-8")
        with patch("sys.stdout", new=io.StringIO()) as output:
            code = main(["verify", str(path), "--root", str(self.root)])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["status"], "INVALID")

    def test_timeout_never_passes(self):
        import subprocess
        with patch("tools.evidence_engine.subprocess.run", side_effect=subprocess.TimeoutExpired("test", 1)):
            record = self.run_record()
        self.assertEqual(record["status"], "ERROR")
        self.assertEqual(verify(record, self.root)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
