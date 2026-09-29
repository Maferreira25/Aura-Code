#!/usr/bin/env python3
"""Fail-closed installation diagnostics for the AuraCode distribution."""

import importlib.util
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional

from tools.skill_packages import BUNDLE_PATH, verify_skill_bundle
from tools.studio_package import verify_studio_package
from tools.version import FRAMEWORK_VERSION


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _check(check_id: str, status: str, required: bool, reason: str, remedy: str = "") -> Dict[str, object]:
    return {
        "id": check_id,
        "status": status,
        "required": required,
        "reason": reason,
        "remedy": remedy,
    }


def _template_check(package_root: Path) -> Dict[str, object]:
    profiles = {"micro": 1, "lite": 3, "standard": 7, "enterprise": 15}
    missing: List[str] = []
    for profile, minimum_files in profiles.items():
        profile_dir = package_root / "templates" / "sdd" / profile
        count = len(list(profile_dir.glob("*.md"))) if profile_dir.is_dir() else 0
        if count < minimum_files:
            missing.append(f"{profile} ({count}/{minimum_files})")
    if missing:
        return _check(
            "templates",
            "FAIL",
            True,
            f"Specification templates are incomplete: {', '.join(missing)}.",
            "Reinstall AuraCode from a complete official distribution.",
        )
    return _check("templates", "PASS", True, "All four specification profiles are packaged.")


def _verifier_check() -> Dict[str, object]:
    modules = (
        "tools.audit",
        "tools.check_architecture",
        "tools.check_injection_vectors",
        "tools.check_requirements_ambiguity",
        "tools.check_resource_leaks",
        "tools.check_slop_code",
        "tools.check_strict_types",
        "tools.check_test_integrity",
        "tools.iteration",
        "tools.studio_package",
    )
    missing = [name for name in modules if importlib.util.find_spec(name) is None]
    if missing:
        return _check(
            "verifiers",
            "FAIL",
            True,
            f"Required verifier modules are missing: {', '.join(missing)}.",
            "Reinstall AuraCode; do not continue with a partial package.",
        )
    return _check("verifiers", "PASS", True, "Required assurance modules are importable.")


def _is_docker_daemon_running(docker_path: str) -> bool:
    try:
        proc = subprocess.run(
            [docker_path, "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2.0,
        )
        return proc.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def run_doctor(
    package_root: Path = PACKAGE_ROOT,
    executable_lookup: Optional[Callable[[str], Optional[str]]] = None,
    docker_daemon_check: Optional[Callable[[str], bool]] = None,
) -> Dict[str, object]:
    """Inspect internal package completeness and relevant host capabilities."""
    root = Path(package_root).resolve()
    lookup = executable_lookup or shutil.which
    checks: List[Dict[str, object]] = []

    python_ok = sys.version_info >= (3, 9)
    checks.append(
        _check(
            "python",
            "PASS" if python_ok else "FAIL",
            True,
            f"Python {platform.python_version()} detected.",
            "Install Python 3.9 or newer." if not python_ok else "",
        )
    )
    system = platform.system()
    supported_os = system in {"Windows", "Linux"}
    checks.append(
        _check(
            "operating_system",
            "PASS" if supported_os else "NOT_APPLICABLE",
            True,
            f"Host operating system: {system}.",
            "Use Windows or Linux for the currently supported release." if not supported_os else "",
        )
    )

    bundle_path = root / "auracode" / BUNDLE_PATH.name
    source_skills = root / ".agents" / "skills"
    skill_result = verify_skill_bundle(
        bundle_path=bundle_path,
        source_skills_dir=source_skills if source_skills.is_dir() else None,
    )
    checks.append(
        _check(
            "skills",
            str(skill_result["status"]),
            True,
            f"Verified {skill_result.get('verified_skills', 0)} packaged skills.",
            "Reinstall or rebuild the skill bundle." if skill_result["status"] != "PASS" else "",
        )
    )
    checks.append(_template_check(root))
    checks.append(_verifier_check())

    studio_result = verify_studio_package(root)
    checks.append(
        _check(
            "studio",
            str(studio_result["status"]),
            True,
            str(studio_result["reason"]),
            "Do not describe this distribution as a complete builder until Studio is present and verified."
            if studio_result["status"] != "PASS"
            else "",
        )
    )
    checks.append(
        _check(
            "studio_workflows",
            str(studio_result.get("workflow_status", "NOT_RUN")),
            True,
            str(studio_result.get("workflow_reason") or "Aura Studio workflows have not been validated."),
            "Complete and validate the guided Studio journeys before claiming an end-to-end builder."
            if studio_result.get("workflow_status") != "PASS"
            else "",
        )
    )

    git_path = lookup("git")
    checks.append(
        _check(
            "git",
            "PASS" if git_path else "NOT_RUN",
            True,
            f"Git found at {git_path}." if git_path else "Git was not found.",
            "Install Git before using checkpoints or isolated worktrees." if not git_path else "",
        )
    )
    docker_path = lookup("docker")
    daemon_checker = docker_daemon_check or _is_docker_daemon_running
    if docker_path:
        daemon_ok = daemon_checker(docker_path)
        checks.append(
            _check(
                "docker",
                "PASS" if daemon_ok else "NOT_RUN",
                False,
                f"Docker found at {docker_path} and daemon is responsive."
                if daemon_ok
                else f"Docker CLI found at {docker_path}, but daemon is not running.",
                "" if daemon_ok else "Start Docker Desktop or dockerd if containerized workflows are needed.",
            )
        )
    else:
        checks.append(
            _check(
                "docker",
                "NOT_APPLICABLE",
                False,
                "Docker is optional until cage, preview, or deployment is requested.",
                "Install Docker before using container-dependent workflows.",
            )
        )

    required_states = {str(item["status"]) for item in checks if item["required"]}
    if "ERROR" in required_states or "FAIL" in required_states:
        status = "FAIL"
    elif "NOT_RUN" in required_states or "NOT_APPLICABLE" in required_states:
        status = "NOT_RUN"
    else:
        status = "PASS"
    return {
        "status": status,
        "complete": status == "PASS",
        "framework_version": FRAMEWORK_VERSION,
        "checks": checks,
    }


def print_doctor_report(report: Dict[str, object], as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    print(f"AuraCode doctor: {report['status']}")
    raw_checks = report.get("checks", [])
    checks = raw_checks if isinstance(raw_checks, list) else []
    for item in checks:
        if isinstance(item, dict):
            print(f"[{item.get('status')}] {item.get('id')}: {item.get('reason')}")
            if item.get("remedy"):
                print(f"  Next step: {item.get('remedy')}")


def main(argv: Optional[List[str]] = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    as_json = "--json" in args
    report = run_doctor()
    print_doctor_report(report, as_json=as_json)
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
