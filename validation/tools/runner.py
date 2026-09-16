#!/usr/bin/env python3
"""Execution Runner with Isolation Boundaries for AI Software Assurance Harness.

Provides pluggable, boundary-enforced execution for untrusted candidate workspaces:
1. DockerRunner: Disposable OCI container with disabled network, non-root identity,
   read-only protected tests, and resource quotas (memory, CPU, PIDs).
2. SubprocessSanitizedRunner: Isolated host execution with stripped environment
   (eliminating host credentials/secrets), process group boundaries, and process
   tree cleanup on timeout.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

DEFAULT_CONTAINER_IMAGE = "python:3.13-slim"

# Minimal safe environment keys required for Python execution on the host
SAFE_HOST_ENV_KEYS: Set[str] = {
    "PATH",
    "SYSTEMROOT",
    "SYSTEMDRIVE",
    "WINDIR",
    "TEMP",
    "TMP",
    "LOCALAPPDATA",
    "APPDATA",
    "PROGRAMDATA",
    "COMSPEC",
    "PATHEXT",
    "HOME",
    "USER",
    "USERNAME",
    "LOGNAME",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PYTHONIOENCODING",
    "PYTHONUTF8",
}

# Forbidden substring patterns indicating sensitive credentials or host variables
SENSITIVE_KEY_PATTERNS = (
    "KEY",
    "TOKEN",
    "SECRET",
    "PASS",
    "AUTH",
    "CREDENTIAL",
    "AURACODE_",
    "PRIVATE",
    "API",
)


def is_docker_available() -> bool:
    """Check if docker CLI is available and docker daemon is responding."""
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return False
    try:
        res = subprocess.run(
            [docker_bin, "info"],
            capture_output=True,
            timeout=5,
            text=True,
        )
        return res.returncode == 0
    except Exception:
        return False


def sanitize_environment(
    env: Optional[Dict[str, str]] = None,
    extra_env: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Strip sensitive host credentials and environment variables."""
    source_env = env if env is not None else os.environ
    sanitized: Dict[str, str] = {}

    for k, v in source_env.items():
        k_upper = k.upper()
        # Keep only explicitly safe runtime variables
        if k_upper in SAFE_HOST_ENV_KEYS:
            sanitized[k] = v
        # Never allow sensitive tokens or sentinels
        elif any(pat in k_upper for pat in SENSITIVE_KEY_PATTERNS):
            continue

    if extra_env:
        for k, v in extra_env.items():
            k_upper = k.upper()
            if not any(pat in k_upper for pat in SENSITIVE_KEY_PATTERNS):
                sanitized[k] = v

    return sanitized


class ExecutionRunner(ABC):
    """Abstract execution boundary runner."""

    @abstractmethod
    def run_tests(
        self,
        workspace: Path,
        test_dir: Path,
        env_vars: Optional[Dict[str, str]] = None,
        timeout: int = 15,
        protected_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Execute test discovery within an isolation boundary."""
        pass

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Name of the isolation backend."""
        pass

    @property
    @abstractmethod
    def is_strong_isolation(self) -> bool:
        """Indicates whether this runner provides true container/sandbox isolation."""
        pass


RUNNER_ORACLE_WRAPPER_CODE = """
import os
import sys
import unittest

if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

_CRITICAL_METHODS = [
    "assertEqual",
    "assertNotEqual",
    "assertTrue",
    "assertFalse",
    "assertIs",
    "assertIsNot",
    "assertIsNone",
    "assertIsNotNone",
    "assertIn",
    "assertNotIn",
    "assertIsInstance",
    "assertRaises",
    "fail",
]

_ORIGINAL_ORACLES = {m: getattr(unittest.TestCase, m) for m in _CRITICAL_METHODS}

class TamperResistantResult(unittest.TextTestResult):
    def startTest(self, test):
        self._check_tampering(test)
        super().startTest(test)

    def stopTest(self, test):
        self._check_tampering(test)
        super().stopTest(test)

    def _check_tampering(self, test):
        for name, orig in _ORIGINAL_ORACLES.items():
            if getattr(unittest.TestCase, name, None) is not orig:
                sys.stderr.write(f"\\nORACLE_TAMPERING_DETECTED: Class method unittest.TestCase.{name} was modified\\n")
                sys.exit(101)
            if name in getattr(test, "__dict__", {}):
                sys.stderr.write(f"\\nORACLE_TAMPERING_DETECTED: Instance attribute {name} was overridden\\n")
                sys.exit(101)
            val = getattr(test, name, None)
            func = getattr(val, "__func__", val)
            if func is not orig:
                sys.stderr.write(f"\\nORACLE_TAMPERING_DETECTED: Oracle method '{name}' was modified\\n")
                sys.exit(101)

test_dir = sys.argv[1]
suite = unittest.defaultTestLoader.discover(test_dir)
runner = unittest.TextTestRunner(resultclass=TamperResistantResult, verbosity=2)
result = runner.run(suite)

for name, orig in _ORIGINAL_ORACLES.items():
    if getattr(unittest.TestCase, name, None) is not orig:
        sys.stderr.write(f"\\nORACLE_TAMPERING_DETECTED: Post-suite check detected modified '{name}'\\n")
        sys.exit(101)

sys.exit(0 if result.wasSuccessful() else 1)
"""


class SubprocessSanitizedRunner(ExecutionRunner):
    """Host execution runner with stripped environment and process tree containment."""

    @property
    def backend_name(self) -> str:
        return "subprocess_sanitized"

    @property
    def is_strong_isolation(self) -> bool:
        return False

    def _kill_process_tree(self, proc: subprocess.Popen) -> None:
        """Recursively terminate child and descendant processes."""
        try:
            if os.name == "nt":
                # Windows taskkill /F /T kills child tree
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    capture_output=True,
                    timeout=5,
                )
            else:
                import signal
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            try:
                proc.kill()
            except (ProcessLookupError, OSError):
                return

    def run_tests(
        self,
        workspace: Path,
        test_dir: Path,
        env_vars: Optional[Dict[str, str]] = None,
        timeout: int = 15,
        protected_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        workspace = Path(workspace).resolve()
        test_dir = Path(test_dir).resolve()

        clean_env = sanitize_environment(extra_env=env_vars)
        clean_env["TARGET_WORKSPACE"] = str(workspace)
        clean_env["PYTHONUNBUFFERED"] = "1"

        cmd = [sys.executable, "-c", RUNNER_ORACLE_WRAPPER_CODE, str(test_dir)]

        popen_kwargs: Dict[str, Any] = {
            "cwd": str(workspace),
            "env": clean_env,
            "text": True,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
        }

        if os.name == "nt":
            # Start new process group for Windows tree tracking
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            popen_kwargs["start_new_session"] = True

        proc = None
        try:
            proc = subprocess.Popen(cmd, **popen_kwargs)
            stdout, stderr = proc.communicate(timeout=timeout)
            tampered = (proc.returncode == 101) or ("ORACLE_TAMPERING_DETECTED" in (stderr or ""))
            return {
                "returncode": proc.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "timed_out": False,
                "backend": self.backend_name,
                "isolation_boundary_enforced": True,
                "oracle_tampering_detected": tampered,
            }
        except subprocess.TimeoutExpired:
            if proc:
                self._kill_process_tree(proc)
                try:
                    stdout, stderr = proc.communicate(timeout=2)
                except Exception:
                    stdout, stderr = "", ""
            else:
                stdout, stderr = "", ""
            return {
                "returncode": 124,
                "stdout": stdout or "",
                "stderr": (stderr or "") + "\nEVALUATION TIMEOUT (Process tree terminated)",
                "timed_out": True,
                "backend": self.backend_name,
                "isolation_boundary_enforced": True,
            }


class DockerRunner(ExecutionRunner):
    """Disposable container runner with network disabled and resource quotas."""

    def __init__(self, image: str = DEFAULT_CONTAINER_IMAGE):
        self.image = image

    @property
    def backend_name(self) -> str:
        return "docker"

    @property
    def is_strong_isolation(self) -> bool:
        return True

    def run_tests(
        self,
        workspace: Path,
        test_dir: Path,
        env_vars: Optional[Dict[str, str]] = None,
        timeout: int = 15,
        protected_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        workspace = Path(workspace).resolve()
        test_dir = Path(test_dir).resolve()

        docker_bin = shutil.which("docker")
        if not docker_bin:
            raise RuntimeError("Docker binary not found on host PATH")

        # Mount candidate workspace at /workspace
        mounts = ["-v", f"{workspace}:/workspace:rw"]

        # If protected tests are executed, mount them read-only inside /evaluator/protected
        if protected_dir:
            protected_dir = Path(protected_dir).resolve()
            mounts.extend(["-v", f"{protected_dir}:/evaluator/protected:ro"])
            container_test_dir = "/evaluator/protected"
        else:
            container_test_dir = "/workspace/tests"

        # Build sanitized environment flags
        env_args = [
            "-e", "TARGET_WORKSPACE=/workspace",
            "-e", "PYTHONPATH=/workspace",
            "-e", "PYTHONUNBUFFERED=1",
        ]
        if env_vars:
            for k, v in env_vars.items():
                if not any(pat in k.upper() for pat in SENSITIVE_KEY_PATTERNS):
                    env_args.extend(["-e", f"{k}={v}"])

        container_cmd = [
            "python", "-c", RUNNER_ORACLE_WRAPPER_CODE, container_test_dir
        ]

        # Docker invocation with strict isolation boundaries
        full_cmd = (
            [docker_bin, "run", "--rm"]
            + ["--network", "none"]           # No external network
            + ["--memory", "512m"]            # 512MB RAM limit
            + ["--cpus", "1.0"]               # 1 CPU core limit
            + ["--pids-limit", "100"]         # Fork-bomb protection
            + ["--user", "1000:1000"]         # Non-root user
            + ["-w", "/workspace"]            # Working directory
            + mounts
            + env_args
            + [self.image]
            + container_cmd
        )

        try:
            cp = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            tampered = (cp.returncode == 101) or ("ORACLE_TAMPERING_DETECTED" in (cp.stderr or ""))
            return {
                "returncode": cp.returncode,
                "stdout": cp.stdout,
                "stderr": cp.stderr,
                "timed_out": False,
                "backend": self.backend_name,
                "isolation_boundary_enforced": True,
                "oracle_tampering_detected": tampered,
            }
        except subprocess.TimeoutExpired as exc:
            out = exc.stdout or ""
            err = exc.stderr or ""
            return {
                "returncode": 124,
                "stdout": out,
                "stderr": err + "\nEVALUATION TIMEOUT (Container terminated)",
                "timed_out": True,
                "backend": self.backend_name,
                "isolation_boundary_enforced": True,
            }


def get_runner(
    mode: str = "auto",
    strict_mode: bool = False,
    image: str = DEFAULT_CONTAINER_IMAGE,
) -> ExecutionRunner:
    """Factory to acquire the appropriate execution runner based on policy."""
    mode = (mode or "auto").lower()

    if mode == "container":
        if not is_docker_available():
            raise RuntimeError(
                "Container isolation requested (--isolation container) but Docker daemon is not responding. "
                "Failing closed to prevent unsandboxed code execution."
            )
        return DockerRunner(image=image)

    elif mode == "local":
        return SubprocessSanitizedRunner()

    elif mode == "auto":
        if is_docker_available():
            return DockerRunner(image=image)
        elif strict_mode:
            raise RuntimeError(
                "Strict mode enabled: container isolation required but Docker daemon is unavailable. "
                "Failing closed to prevent untrusted candidate execution on host."
            )
        else:
            return SubprocessSanitizedRunner()

    else:
        raise ValueError(f"Unknown isolation mode: '{mode}'. Expected one of: auto, container, local.")
