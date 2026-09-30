#!/usr/bin/env python3
"""Comprehensive Unit Test Suite for Aura Loop Runner (Ralph Architecture).

Tests state persistence, task backlog processing, 5-level verification integration,
circuit breakers (stuck loop, max iterations), and anti-reward-hacking detection.
"""

import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from tools.loop_runner import (
    LoopStateManager,
    run_5_level_verification,
    run_loop,
    main,
)


class TestLoopRunner(unittest.TestCase):
    """Test suite verifying Aura Loop Ralph Architecture execution machine."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()
        self.state_mgr = LoopStateManager(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_loop_state_manager(self):
        state = self.state_mgr.load_state()
        self.assertEqual(state["status"], "INITIALIZED")
        self.assertEqual(state["current_iteration"], 0)

        state["current_iteration"] = 1
        state["status"] = "RUNNING"
        self.state_mgr.save_state(state)

        reloaded = self.state_mgr.load_state()
        self.assertEqual(reloaded["current_iteration"], 1)
        self.assertEqual(reloaded["status"], "RUNNING")

        # Test tasks
        sample_tasks = [{"id": "t1", "title": "First task", "status": "pending"}]
        self.state_mgr.save_tasks(sample_tasks)
        loaded_tasks = self.state_mgr.load_tasks()
        self.assertEqual(len(loaded_tasks), 1)
        self.assertEqual(loaded_tasks[0]["id"], "t1")

    @patch("tools.loop_runner._run_cmd")
    def test_canonical_verification_pass_is_ready(self, mock_run_cmd):
        mock_run_cmd.return_value = (0, "OK", "")
        res = run_5_level_verification(self.temp_dir)
        self.assertTrue(res["passed"])
        self.assertEqual(res["canonical_status"], "PASS")
        self.assertEqual(res["canonical_progression"]["state"], "READY")

    @patch("tools.loop_runner._run_cmd")
    def test_canonical_verification_blocks_on_uncertain_gate(self, mock_run_cmd):
        calls = [(1, "", "scanner failed")] + [(0, "OK", "")] * 7
        mock_run_cmd.side_effect = calls
        res = run_5_level_verification(self.temp_dir)
        self.assertFalse(res["passed"])
        self.assertEqual(res["canonical_status"], "INCONCLUSIVE")
        self.assertEqual(res["canonical_progression"]["state"], "BLOCKED")
        self.assertTrue(any(item["status"] == "INCONCLUSIVE" for item in res["canonical_results"]))

    def test_run_loop_no_tasks(self):
        res = run_loop(self.temp_dir)
        self.assertEqual(res["status"], "NO_TASKS")
        self.assertEqual(res["iterations_run"], 0)

    def test_run_loop_completion_dry_run(self):
        tasks = [
            {"id": "t1", "title": "Setup Entity", "status": "pending"},
            {"id": "t2", "title": "Setup Use Case", "status": "pending"},
        ]
        self.state_mgr.save_tasks(tasks)

        res = run_loop(self.temp_dir, dry_run=True, max_iterations=5)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertEqual(res["iterations_run"], 2)
        self.assertEqual(len(res["completed_tasks"]), 2)

        # Check updated tasks file
        updated_tasks = self.state_mgr.load_tasks()
        self.assertTrue(all(t["status"] == "completed" for t in updated_tasks))

    def test_circuit_breaker_max_iterations(self):
        tasks = [
            {"id": f"t{i}", "title": f"Task {i}", "status": "pending"}
            for i in range(5)
        ]
        self.state_mgr.save_tasks(tasks)

        res = run_loop(self.temp_dir, dry_run=True, max_iterations=2)
        self.assertEqual(res["status"], "MAX_ITERATIONS_REACHED")
        self.assertEqual(res["iterations_run"], 2)

    @patch("tools.loop_runner.run_5_level_verification")
    def test_circuit_breaker_stuck_oscillation(self, mock_verify):
        # Mock repeated failure
        mock_verify.return_value = {
            "passed": False,
            "reward_hacking_detected": False,
            "errors": ["Compilation error"],
            "levels": {},
        }

        tasks = [{"id": "t1", "title": "Hard Task", "status": "pending"}]
        self.state_mgr.save_tasks(tasks)

        # Run loop with continue_on_fail to test the 3-failure threshold
        res = run_loop(self.temp_dir, stop_on_fail=False, max_iterations=5)
        self.assertEqual(res["status"], "STUCK_LOOP")
        self.assertEqual(res["task"], "t1")
        self.assertEqual(res["iterations_run"], 3)

    @patch("tools.loop_runner.run_5_level_verification")
    def test_anti_reward_hacking_emergency_brake(self, mock_verify):
        mock_verify.return_value = {
            "passed": False,
            "reward_hacking_detected": True,
            "errors": ["Test tampering detected"],
            "levels": {},
        }

        tasks = [{"id": "t1", "title": "Sneaky Task", "status": "pending"}]
        self.state_mgr.save_tasks(tasks)

        res = run_loop(self.temp_dir, dry_run=False)
        self.assertEqual(res["status"], "REWARD_HACKING_DETECTED")
        self.assertIn("tamper", res["error"].lower())

    def test_cli_loop(self):
        with patch("pathlib.Path.cwd", return_value=self.temp_dir):
            # Test status
            code = main(["status"])
            self.assertEqual(code, 0)

            # Test reset
            code = main(["reset"])
            self.assertEqual(code, 0)

    @patch("tools.loop_runner._run_cmd")
    def test_require_churn_fails_when_no_changes(self, mock_run_cmd):
        mock_run_cmd.return_value = (0, "", "")
        tasks = [{"id": "t1", "title": "Empty Task", "status": "pending"}]
        self.state_mgr.save_tasks(tasks)

        res = run_loop(self.temp_dir, dry_run=False, require_churn=True)
        self.assertEqual(res["status"], "NO_CHURN_DETECTED")
        self.assertIn("no code changes", res["error"])

    @patch("tools.loop_runner._run_cmd")
    def test_agent_cmd_invoked(self, mock_run_cmd):
        mock_run_cmd.return_value = (0, "", "")
        tasks = [{"id": "t1", "title": "Agent Task", "status": "pending"}]
        self.state_mgr.save_tasks(tasks)

        res = run_loop(self.temp_dir, dry_run=True, agent_cmd="echo hello")
        self.assertEqual(res["status"], "COMPLETED")
        called_cmds = [call.args[0] for call in mock_run_cmd.call_args_list]
        self.assertTrue(any("echo" in cmd for cmd in called_cmds))


if __name__ == "__main__":
    unittest.main()
