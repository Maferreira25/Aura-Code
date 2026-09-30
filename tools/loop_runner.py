#!/usr/bin/env python3
"""Aura Loop: Autonomous Loop Runner based on Ralph Architecture (Geoffrey Huntley).

Executes tasks iteratively with fresh context per cycle to prevent the 'Dumb Zone'
(context degradation >100k tokens), verifies each step with 5-level deterministic
AST gates, and enforces strict Anti-Reward-Hacking circuit breakers.

Zero external dependencies (uses standard library 'subprocess', 'pathlib', 'argparse', 'json', 'time', 'sys').
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tools.assurance_result import aggregate_status, build_result, progression_state

ROOT_DIR = Path(__file__).resolve().parents[1]


def _run_cmd(cmd: List[str], cwd: Path, env: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]:
    """Runs a command safely and captures output."""
    try:
        res = subprocess.run(
            cmd,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


class LoopStateManager:
    """Manages persistent loop state on disk to enable stateless agent iterations."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.forward_dir = workspace_root / "_auracode_forward"
        self.forward_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.forward_dir / "loop_state.json"
        self.tasks_file = self.forward_dir / "tasks.json"

    def _default_state(self) -> Dict[str, Any]:
        return {
            "status": "INITIALIZED",
            "current_iteration": 0,
            "max_iterations": 10,
            "completed_tasks": [],
            "failed_tasks": [],
            "active_task": None,
            "consecutive_failures": 0,
            "last_verification": None,
            "history": [],
        }

    def load_state(self) -> Dict[str, Any]:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return self._default_state()
        return self._default_state()

    def save_state(self, state: Dict[str, Any]) -> None:
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
            f.write("\n")

    def load_tasks(self, custom_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        target = custom_path or self.tasks_file
        if target.exists():
            try:
                with open(target, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and "tasks" in data:
                        return data["tasks"]
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def save_tasks(self, tasks: List[Dict[str, Any]], custom_path: Optional[Path] = None) -> None:
        target = custom_path or self.tasks_file
        with open(target, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
            f.write("\n")


def run_5_level_verification(workspace_root: Path, allow_tests: bool = False) -> Dict[str, Any]:
    """Executes the 5 levels of deterministic assurance verification on the workspace.
    
    Level 1: AST Linters (slop, leaks, sec, types, arch)
    Level 2: Test Suite Integrity (non-vacuous check)
    Level 3: Test Execution (pytest / unittest)
    Level 4: Surgical Diff & Anti-Reward-Hacking
    Level 5: Gate synthesis
    """
    results: Dict[str, Any] = {
        "passed": False,
        "levels": {},
        "reward_hacking_detected": False,
        "errors": [],
        "canonical_results": [],
    }

    def record_canonical(check_id: str, status: str, reason: str, exit_code: Optional[int]) -> None:
        results["canonical_results"].append(
            build_result(
                check_id=check_id,
                status=status,
                producer_tool="loop_runner",
                producer_method="subprocess_gate",
                workspace=str(workspace_root),
                reason=reason,
                exit_code=exit_code,
                legacy={"source": "tools/loop_runner.py"},
            )
        )

    assurance_mod = [sys.executable, "-m", "tools.assurance"]

    # --- LEVEL 1: AST Linters ---
    l1_passed = True
    l1_checks = ["slop", "leaks", "sec", "types", "arch"]
    l1_details = {}

    for check in l1_checks:
        code, out, err = _run_cmd(assurance_mod + [check, str(workspace_root)], workspace_root)
        if code != 0:
            l1_passed = False
            results["errors"].append(f"Level 1 AST check failed: {check}")
        record_canonical(
            check,
            "PASS" if code == 0 else "INCONCLUSIVE",
            (
                f"Loop subprocess gate '{check}' completed successfully."
                if code == 0
                else f"Loop subprocess gate '{check}' returned non-zero; failure class is not yet canonicalized."
            ),
            code,
        )
        l1_details[check] = {"code": code, "output": out[:200]}

    results["levels"]["level_1_ast_linters"] = {"passed": l1_passed, "details": l1_details}

    # --- LEVEL 2: Test Integrity ---
    code_ti, out_ti, err_ti = _run_cmd(assurance_mod + ["tests", str(workspace_root)], workspace_root)
    l2_passed = (code_ti == 0)
    if not l2_passed:
        results["errors"].append("Level 2 Test integrity check failed (vacuous tests or syntax error)")
    record_canonical(
        "test-integrity",
        "PASS" if l2_passed else "INCONCLUSIVE",
        "Test-integrity gate completed successfully." if l2_passed else "Test-integrity gate returned non-zero; failure class is not yet canonicalized.",
        code_ti,
    )
    results["levels"]["level_2_test_integrity"] = {"passed": l2_passed, "output": out_ti[:200]}

    # --- LEVEL 3: Test Execution ---
    code_t, out_t, err_t = _run_cmd([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], workspace_root)
    l3_passed = (code_t == 0)
    if not l3_passed:
        results["errors"].append("Level 3 Unit test execution failed")
    record_canonical(
        "unit-tests",
        "PASS" if l3_passed else "INCONCLUSIVE",
        "Unit-test execution completed successfully." if l3_passed else "Unit-test execution returned non-zero; assertion failure versus evaluator error is not yet classified.",
        code_t,
    )
    results["levels"]["level_3_test_execution"] = {"passed": l3_passed, "output": out_t[:200] or err_t[:200]}

    # --- LEVEL 4: Surgical Diff & Anti-Reward-Hacking ---
    diff_args = assurance_mod + ["diff", str(workspace_root)]
    if allow_tests:
        diff_args.append("--allow-tests")

    code_d, out_d, err_d = _run_cmd(diff_args, workspace_root)
    l4_passed = (code_d == 0)
    if not l4_passed:
        protected_tamper_markers = (
            "potential reward-hacking",
            "without explicit authorization",
            "protected assurance asset",
            "held-out evaluator asset",
            "evidence plane is append-only",
            "public test/evaluator modification",
        )
        if any(marker in out_d.lower() for marker in protected_tamper_markers):
            results["reward_hacking_detected"] = True
            results["errors"].append(
                "CRITICAL: Assurance-plane tampering detected; the implementing agent attempted "
                "to modify tests, evaluators, policy, held-out assets, or existing evidence."
            )
        else:
            results["errors"].append("Level 4 Surgical diff check failed (scope/churn/integrity violation)")
    record_canonical(
        "surgical-diff",
        "PASS" if l4_passed else ("FAIL" if results["reward_hacking_detected"] else "INCONCLUSIVE"),
        (
            "Surgical diff and anti-reward-hacking gate passed."
            if l4_passed
            else (
                "Unauthorized test/evaluator tampering was detected."
                if results["reward_hacking_detected"]
                else "Surgical diff gate returned non-zero; failure class is not yet canonicalized."
            )
        ),
        code_d,
    )
    results["levels"]["level_4_surgical_diff"] = {"passed": l4_passed, "output": out_d[:200]}

    # --- LEVEL 5: Gate Synthesis ---
    all_levels_passed = l1_passed and l2_passed and l3_passed and l4_passed
    results["levels"]["level_5_gate_synthesis"] = {"passed": all_levels_passed}
    results["passed"] = all_levels_passed
    results["canonical_status"] = aggregate_status(
        item["status"] for item in results["canonical_results"]
    ).value
    results["canonical_progression"] = progression_state(results["canonical_results"])

    return results


def run_loop(
    workspace_root: Path,
    tasks_file: Optional[Path] = None,
    max_iterations: int = 10,
    stop_on_fail: bool = True,
    dry_run: bool = False,
    agent_cmd: Optional[str] = None,
    require_churn: bool = False,
) -> Dict[str, Any]:
    """Executes the autonomous loop machine using Ralph stateless architecture."""
    state_mgr = LoopStateManager(workspace_root)
    state = state_mgr.load_state()
    tasks = state_mgr.load_tasks(tasks_file)

    if not tasks:
        return {
            "status": "NO_TASKS",
            "message": "No pending tasks found in backlog. Populate _auracode_forward/tasks.json to start.",
            "iterations_run": 0,
        }

    state["max_iterations"] = max_iterations
    state["status"] = "RUNNING"
    iterations_run = 0

    while iterations_run < max_iterations:
        # Find next pending task
        pending_task = None
        for t in tasks:
            if t.get("status") in {"pending", "todo"}:
                pending_task = t
                break

        if not pending_task:
            state["status"] = "COMPLETED"
            state["message"] = "All tasks completed and verified."
            state_mgr.save_state(state)
            return {
                "status": "COMPLETED",
                "message": "All backlog tasks have been successfully implemented and verified.",
                "iterations_run": iterations_run,
                "completed_tasks": state["completed_tasks"],
            }

        iterations_run += 1
        state["current_iteration"] += 1
        task_id = pending_task.get("id", f"task-{iterations_run}")
        task_title = pending_task.get("title", "Unnamed Task")

        print(f"\n[AURA LOOP ITERATION {iterations_run}/{max_iterations}] Starting Task: [{task_id}] {task_title}")
        pending_task["status"] = "in_progress"
        pending_task["attempts"] = pending_task.get("attempts", 0) + 1
        state["active_task"] = task_id
        state_mgr.save_tasks(tasks, tasks_file)
        state_mgr.save_state(state)

        if agent_cmd:
            print(f"[AURA LOOP AGENT] Dispatching task [{task_id}] to agent: {agent_cmd}")
            import shlex
            cmd_parts = shlex.split(agent_cmd, posix=os.name != "nt")
            env = os.environ.copy()
            env["AURA_TASK_ID"] = str(task_id)
            env["AURA_TASK_TITLE"] = str(task_title)
            env["AURA_TASK_DESCRIPTION"] = str(pending_task.get("description", ""))
            agent_rc, _, agent_err = _run_cmd(cmd_parts, workspace_root, env=env)
            if agent_rc != 0:
                print(f"[AURA LOOP AGENT WARNING] Agent returned code {agent_rc}: {agent_err}")
        elif not dry_run:
            print(f"[AURA LOOP NOTICE] No --agent-cmd specified. Verifying workspace state for task [{task_id}].")

        churn_rc, churn_stdout, _ = _run_cmd(["git", "status", "--porcelain"], workspace_root)
        has_churn = churn_rc == 0 and bool(churn_stdout.strip())
        if require_churn and not dry_run and not has_churn:
            print(f"[AURA LOOP CHURN] Warning: No file changes detected for task [{task_id}].")
            state["consecutive_failures"] += 1
            pending_task["status"] = "failed"
            state["failed_tasks"].append(task_id)
            state_mgr.save_tasks(tasks, tasks_file)
            state_mgr.save_state(state)
            return {
                "status": "NO_CHURN_DETECTED",
                "error": f"Task [{task_id}] produced no code changes. Cannot commit empty diff.",
                "iterations_run": iterations_run,
                "task": task_id,
            }

        if dry_run:
            print(f"[DRY-RUN] Simulating verification for task {task_id}...")
            verification = {
                "passed": True,
                "levels": {"level_1": {"passed": True}},
                "reward_hacking_detected": False,
                "errors": [],
            }
        else:
            # Run the 5-level verification suite
            verification = run_5_level_verification(workspace_root, allow_tests=False)

        state["last_verification"] = verification

        # Check circuit breaker: Reward Hacking
        if verification["reward_hacking_detected"]:
            state["status"] = "REWARD_HACKING_DETECTED"
            state["message"] = f"Emergency brake engaged: Task '{task_id}' attempted to tamper with test suite."
            state_mgr.save_state(state)
            return {
                "status": "REWARD_HACKING_DETECTED",
                "error": state["message"],
                "iterations_run": iterations_run,
                "task": task_id,
            }

        if verification["passed"]:
            print(f"[AURA LOOP OK] Task [{task_id}] PASSED all 5 levels of assurance verification!")
            pending_task["status"] = "completed"
            state["completed_tasks"].append(task_id)
            state["consecutive_failures"] = 0

            # Commit changes to Git if inside git repo and churn was detected
            if has_churn:
                commit_msg = f"feat(agent): [{task_id}] {task_title} [Assurance 5-Level Pass]"
                _run_cmd(["git", "add", "."], workspace_root)
                _run_cmd(["git", "commit", "-m", commit_msg], workspace_root)
        else:
            print(f"[AURA LOOP FAIL] Task [{task_id}] FAILED verification: {verification['errors']}")
            state["consecutive_failures"] += 1

            # Check circuit breaker: Oscillation / Stuck Loop
            if state["consecutive_failures"] >= 3:
                pending_task["status"] = "failed"
                state["failed_tasks"].append(task_id)
                state["status"] = "STUCK_LOOP"
                state["message"] = f"Circuit breaker tripped: 3 consecutive verification failures on task '{task_id}'."
                state_mgr.save_state(state)
                state_mgr.save_tasks(tasks, tasks_file)
                return {
                    "status": "STUCK_LOOP",
                    "error": state["message"],
                    "iterations_run": iterations_run,
                    "task": task_id,
                }

            if pending_task.get("attempts", 0) < 3:
                # Keep pending so next iteration retries with fresh context
                pending_task["status"] = "pending"
            else:
                pending_task["status"] = "failed"
                state["failed_tasks"].append(task_id)

            if stop_on_fail:
                state["status"] = "STOPPED_ON_FAIL"
                state_mgr.save_state(state)
                state_mgr.save_tasks(tasks, tasks_file)
                return {
                    "status": "STOPPED_ON_FAIL",
                    "error": f"Verification failed on task [{task_id}]: {verification['errors']}",
                    "iterations_run": iterations_run,
                    "task": task_id,
                }

        state_mgr.save_tasks(tasks, tasks_file)
        state_mgr.save_state(state)

    state["status"] = "MAX_ITERATIONS_REACHED"
    state_mgr.save_state(state)
    return {
        "status": "MAX_ITERATIONS_REACHED",
        "message": f"Reached maximum allowed iterations ({max_iterations}).",
        "iterations_run": iterations_run,
    }


def main(argv: Optional[List[str]] = None) -> int:
    """CLI Entrypoint for Aura Loop."""
    parser = argparse.ArgumentParser(
        prog="auracode loop",
        description="Aura Loop: Autonomous Loop Runner based on Ralph Architecture"
    )
    subparsers = parser.add_subparsers(dest="loop_action", help="Loop action to perform")

    # run
    run_p = subparsers.add_parser("run", help="Start or resume the autonomous loop runner")
    run_p.add_argument("--max-iterations", "-n", "--max-turns", dest="max_iterations", type=int, default=10, help="Maximum iterations before pausing (default: 10)")
    run_p.add_argument("--tasks-file", "-t", type=str, default=None, help="Path to custom tasks JSON backlog")
    run_p.add_argument("--dry-run", action="store_true", help="Simulate loop execution without running full suites")
    run_p.add_argument("--continue-on-fail", action="store_true", help="Do not stop loop on verification failure")
    run_p.add_argument("--agent-cmd", "-a", type=str, default=None, help="Agent CLI command to invoke per iteration")
    run_p.add_argument("--require-churn", action="store_true", help="Require genuine git file modifications before verification")
    run_p.add_argument("--json", action="store_true", help="Output summary in JSON format")

    # status
    status_p = subparsers.add_parser("status", help="Display telemetry and current progress of the loop")
    status_p.add_argument("--json", action="store_true", help="Output status in JSON format")

    # reset
    reset_p = subparsers.add_parser("reset", help="Reset loop state and failure counters")

    args = parser.parse_args(argv)

    if not args.loop_action:
        parser.print_help()
        return 0

    workspace_root = Path.cwd().resolve()
    state_mgr = LoopStateManager(workspace_root)

    if args.loop_action == "run":
        tasks_p = Path(args.tasks_file).resolve() if args.tasks_file else None
        res = run_loop(
            workspace_root=workspace_root,
            tasks_file=tasks_p,
            max_iterations=args.max_iterations,
            stop_on_fail=not args.continue_on_fail,
            dry_run=args.dry_run,
            agent_cmd=args.agent_cmd,
            require_churn=args.require_churn,
        )
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(f"\n[AURA LOOP RESULT] Status: {res['status']}")
            print(f"Iterations: {res.get('iterations_run', 0)}")
            if "message" in res:
                print(f"Message: {res['message']}")
            if "error" in res:
                sys.stderr.write(f"Error: {res['error']}\n")
        return 0 if res["status"] in {"COMPLETED", "NO_TASKS"} else 1

    elif args.loop_action == "status":
        st = state_mgr.load_state()
        if args.json:
            print(json.dumps(st, indent=2, ensure_ascii=False))
        else:
            print(f"Aura Loop Telemetry:")
            print(f" - Status: {st.get('status')}")
            print(f" - Iteration: {st.get('current_iteration', 0)} / {st.get('max_iterations', 10)}")
            print(f" - Completed Tasks: {len(st.get('completed_tasks', []))}")
            print(f" - Failed Tasks: {len(st.get('failed_tasks', []))}")
            print(f" - Consecutive Failures: {st.get('consecutive_failures', 0)}")
        return 0

    elif args.loop_action == "reset":
        state_mgr.save_state({
            "status": "RESET",
            "current_iteration": 0,
            "max_iterations": 10,
            "completed_tasks": [],
            "failed_tasks": [],
            "active_task": None,
            "consecutive_failures": 0,
            "last_verification": None,
            "history": [],
        })
        print("[AURA LOOP] Loop state and circuit breaker counters reset successfully.")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
