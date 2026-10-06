"""Policy binding and missing-proof regression tests."""
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.evidence_engine import execute, main
from tools.evidence_policy import decide
from tools.preflight import run_preflight_checks


class EvidencePolicyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "source.txt").write_text("source", encoding="utf-8")
        commit = patch("tools.evidence_engine.current_commit", return_value="a" * 40)
        commit.start()
        self.addCleanup(commit.stop)
        self.command = [sys.executable, "-c", "print('verified')"]
        self.record = execute(self.root, "VER-01", "python-test", ["source.txt"], self.command)
        self.policy = {"schema_version": "1", "policy_id": "POL-1", "requirements": [{
            "requirement_id": "REQ-1", "control_id": "VER-01", "verification_id": "python-test",
            "command": self.command, "scope": ["source.txt"],
        }]}

    def test_complete_chain_passes(self):
        report = decide(self.policy, [self.record], self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["links"][0]["evidence_digest"], self.record["digest"])

    def test_missing_wrong_and_duplicate_evidence_block(self):
        wrong = copy.deepcopy(self.record)
        wrong["control_id"] = "SEC-01"
        for records in ([], [wrong], [self.record, self.record]):
            with self.subTest(records=len(records)):
                self.assertEqual(decide(self.policy, records, self.root)["status"], "FAIL")

    def test_command_and_scope_must_match_trusted_policy(self):
        for field, value in (("command", ["echo", "PASS"]), ("scope", ["other.txt"])):
            policy = copy.deepcopy(self.policy)
            policy["requirements"][0][field] = value
            result = decide(policy, [self.record], self.root)
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["decisions"][0]["status"], "INVALID")

    def test_tampered_or_stale_evidence_cannot_support_link(self):
        changed = copy.deepcopy(self.record)
        changed["stdout_hex"] = "00"
        result = decide(self.policy, [changed], self.root)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["links"], [])
        (self.root / "source.txt").write_text("changed", encoding="utf-8")
        self.assertEqual(decide(self.policy, [self.record], self.root)["status"], "FAIL")

    def test_empty_and_malformed_policies_block(self):
        for policy in ({}, {"schema_version": "1", "policy_id": "p", "requirements": []}, None):
            self.assertEqual(decide(policy, [self.record], self.root)["status"], "FAIL")

    def test_one_pass_does_not_hide_missing_second_requirement(self):
        policy = copy.deepcopy(self.policy)
        missing = copy.deepcopy(policy["requirements"][0])
        missing.update(requirement_id="REQ-2", control_id="SEC-01")
        policy["requirements"].append(missing)
        result = decide(policy, [self.record], self.root)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual([x["status"] for x in result["decisions"]], ["PASS", "NOT_ASSESSED"])

    def test_cli_blocks_missing_evidence(self):
        policy = self.root / "policy.json"
        bundle = self.root / "bundle.json"
        policy.write_text(json.dumps(self.policy), encoding="utf-8")
        bundle.write_text("[]", encoding="utf-8")
        with patch("sys.stdout", new=io.StringIO()) as output:
            code = main(["gate", "--policy", str(policy), "--bundle", str(bundle), "--root", str(self.root)])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["status"], "FAIL")

    def test_preflight_blocks_missing_policy_or_bundle_before_other_gates(self):
        for kwargs in ({"evidence_policy": Path("missing.json")},
                       {"evidence_bundle": Path("missing.json")}):
            with patch("tools.preflight.subprocess.run") as process:
                result = run_preflight_checks(self.root, quiet=True, **kwargs)
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["failed_step"]["status"], "NOT_ASSESSED")
            process.assert_not_called()

    def test_preflight_blocks_empty_bundle_before_other_gates(self):
        policy = self.root / "policy.json"
        bundle = self.root / "bundle.json"
        policy.write_text(json.dumps(self.policy), encoding="utf-8")
        bundle.write_text("[]", encoding="utf-8")
        result = run_preflight_checks(self.root, quiet=True, evidence_policy=policy, evidence_bundle=bundle)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["steps_executed"], 1)
        self.assertEqual(result["passed_steps"], 0)
        self.assertIn('"status": "FAIL"', result["failed_step"]["stdout"])
