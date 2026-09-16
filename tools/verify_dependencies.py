#!/usr/bin/env python3
"""Supply Chain & Package Anti-Hallucination Engine.

Verifies Python dependencies in requirements.txt or single packages against
the official PyPI Registry to detect hallucinated libraries, nonexistent versions,
and supply chain hygiene risks without third-party dependencies.
"""

import argparse
import datetime
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Built-in Python Standard Library modules (never need installation)
if hasattr(sys, "stdlib_module_names"):
    PYTHON_STDLIB_MODULES = set(sys.stdlib_module_names)
else:
    PYTHON_STDLIB_MODULES = {
        "abc", "argparse", "ast", "asyncio", "base64", "collections", "contextlib",
        "copy", "csv", "ctypes", "dataclasses", "datetime", "decimal", "difflib", "enum",
        "errno", "fnmatch", "functools", "glob", "hashlib", "hmac", "html",
        "http", "importlib", "inspect", "io", "ipaddress", "itertools", "json", "logging",
        "math", "mimetypes", "multiprocessing", "operator", "os", "pathlib",
        "pickle", "platform", "pprint", "queue", "random", "re", "secrets",
        "shutil", "signal", "socket", "sqlite3", "ssl", "stat", "string",
        "subprocess", "sys", "tempfile", "threading", "time", "tomllib", "traceback",
        "types", "typing", "unittest", "urllib", "uuid", "warnings", "weakref",
        "xml", "zipfile", "zlib", "zoneinfo"
    }

PYPI_JSON_URL = "https://pypi.org/pypi/{package}/json"


def parse_requirements(file_path: Path) -> List[Dict[str, str]]:
    """Parse a requirements.txt or pyproject.toml file into normalized package and version constraints."""
    packages = []
    if not file_path.exists():
        return packages

    content = file_path.read_text(encoding="utf-8")
    lines_to_parse = []

    if file_path.name == "pyproject.toml" or file_path.suffix == ".toml":
        try:
            import tomllib
            data = tomllib.loads(content)
            deps = data.get("project", {}).get("dependencies", [])
            if isinstance(deps, list):
                lines_to_parse.extend(deps)
        except Exception:
            m = re.search(r"dependencies\s*=\s*\[(.*?)\]", content, re.DOTALL)
            if m:
                for item in re.findall(r'"([^"]+)"|\'([^\']+)\'', m.group(1)):
                    dep = item[0] or item[1]
                    if dep.strip():
                        lines_to_parse.append(dep.strip())
    else:
        lines_to_parse = content.splitlines()

    for line in lines_to_parse:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        
        # Remove environment markers like '; python_version >= "3.8"'
        if ";" in line:
            line = line.split(";")[0].strip()

        # Match package name and version specs with optional extras (e.g. fastapi[all]>=0.100.0)
        match = re.match(r"^([A-Za-z0-9_.\-]+)(?:\[[^\]]+\])?(?:([=><~!^]+)(.*))?$", line)
        if match:
            pkg_name = match.group(1).strip()
            operator = match.group(2).strip() if match.group(2) else ""
            version = match.group(3).strip() if match.group(3) else ""
            packages.append({
                "raw": line,
                "name": pkg_name,
                "operator": operator,
                "version": version
            })
    return packages


def query_pypi_package(package_name: str, timeout: int = 5) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Fetch package metadata from PyPI JSON API. Returns (data, error_code)."""
    if not re.match(r"^[A-Za-z0-9_.\-]+$", package_name):
        return None, "INVALID_NAME"

    url = PYPI_JSON_URL.format(package=package_name)
    headers = {"User-Agent": "AI-Software-Assurance-Framework/0.1.1"}
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                return data, None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, "NOT_FOUND"
        return None, f"HTTP_{e.code}"
    except urllib.error.URLError as e:
        return None, f"NETWORK_ERROR: {e.reason}"
    except Exception as e:
        return None, f"ERROR: {str(e)}"
    return None, "UNKNOWN_ERROR"


def verify_package(
    package_name: str,
    requested_version: Optional[str] = None,
    offline: bool = False,
    timeout: int = 5
) -> Dict[str, Any]:
    """Audit a single dependency for existence, hallucination, and risk indicators."""
    normalized_name = package_name.lower().replace("_", "-")

    # Check 1: Standard library confusion
    if normalized_name in PYTHON_STDLIB_MODULES:
        return {
            "package": package_name,
            "status": "STDLIB_COLLISION",
            "is_hallucinated": False,
            "severity": "warning",
            "message": f"'{package_name}' is a built-in Python standard library module. It should not be listed as an external dependency."
        }

    if offline:
        return {
            "package": package_name,
            "status": "OFFLINE_SKIPPED",
            "is_hallucinated": False,
            "severity": "info",
            "message": "Offline mode active; online PyPI verification skipped."
        }

    data, err = query_pypi_package(normalized_name, timeout=timeout)

    # Check 2: Hallucinated / Non-existent package
    if err == "NOT_FOUND":
        return {
            "package": package_name,
            "status": "HALLUCINATED_PACKAGE",
            "is_hallucinated": True,
            "severity": "critical",
            "message": f"Package '{package_name}' does not exist on PyPI! High probability of AI hallucination or malicious typosquatting."
        }

    if err and err.startswith("NETWORK_ERROR"):
        return {
            "package": package_name,
            "status": "NETWORK_UNAVAILABLE",
            "is_hallucinated": False,
            "severity": "warning",
            "message": f"Could not reach PyPI network to verify '{package_name}': {err}"
        }

    if not data:
        return {
            "package": package_name,
            "status": "VERIFICATION_ERROR",
            "is_hallucinated": False,
            "severity": "warning",
            "message": f"Error querying PyPI for '{package_name}': {err}"
        }

    info = data.get("info", {})
    releases = data.get("releases", {})
    latest_version = info.get("version", "unknown")
    summary = info.get("summary", "")

    # Check 3: Nonexistent version
    if requested_version and requested_version not in releases:
        return {
            "package": package_name,
            "status": "NONEXISTENT_VERSION",
            "is_hallucinated": True,
            "severity": "error",
            "latest_version": latest_version,
            "message": f"Package '{package_name}' exists, but requested version '{requested_version}' was never published! Latest is '{latest_version}'."
        }

    # Check 4: Package age / freshness risk (created within last 30 days)
    risk_notes = []
    urls = data.get("urls", [])
    if urls and "upload_time_iso_8601" in urls[0]:
        try:
            upload_dt = datetime.datetime.fromisoformat(urls[0]["upload_time_iso_8601"].replace("Z", "+00:00"))
            age_days = (datetime.datetime.now(datetime.timezone.utc) - upload_dt).days
            if age_days < 30:
                risk_notes.append(f"Package release is brand new ({age_days} days old); potential supply-chain poisoning risk.")
        except (ValueError, TypeError, KeyError):
            risk_notes.append("Could not determine package release age.")

    return {
        "package": package_name,
        "status": "VERIFIED",
        "is_hallucinated": False,
        "severity": "none",
        "latest_version": latest_version,
        "summary": summary[:100] if summary else "",
        "risk_notes": risk_notes,
        "message": f"Package '{package_name}' verified successfully on PyPI (latest: {latest_version})."
    }


def verify_requirements_file(
    file_path: Path,
    offline: bool = False,
    allow_unverified_network: bool = False,
    timeout: int = 5,
    max_file_bytes: int = 100_000,
    max_packages: int = 100,
    total_timeout: Optional[float] = 30.0,
) -> Dict[str, Any]:
    """Verify all packages inside a requirements.txt file within resource limits."""
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        return {
            "success": False,
            "complete": False,
            "error": f"Requirements file not found at {file_path}",
            "findings": []
        }

    try:
        file_size = file_path.stat().st_size
    except OSError as e:
        return {
            "success": False,
            "complete": False,
            "error": f"Failed to stat requirements file {file_path}: {e}",
            "findings": []
        }

    if file_size > max_file_bytes:
        return {
            "success": False,
            "complete": False,
            "error": f"Requirements file size ({file_size} bytes) exceeds limit ({max_file_bytes} bytes)",
            "file": str(file_path),
            "total_packages": 0,
            "hallucinated_count": 0,
            "unverified_network_count": 0,
            "warnings_count": 0,
            "findings": []
        }

    parsed = parse_requirements(file_path)
    if len(parsed) > max_packages:
        return {
            "success": False,
            "complete": False,
            "error": f"Requirements package count ({len(parsed)}) exceeds limit ({max_packages})",
            "file": str(file_path),
            "total_packages": len(parsed),
            "hallucinated_count": 0,
            "unverified_network_count": 0,
            "warnings_count": 0,
            "findings": []
        }

    if not parsed:
        return {
            "success": True,
            "complete": True,
            "file": str(file_path),
            "total_packages": len(parsed),
            "hallucinated_count": 0,
            "unverified_network_count": 0,
            "warnings_count": 0,
            "findings": []
        }

    findings = []
    hallucinated_count = 0
    unverified_network_count = 0
    warnings_count = 0
    complete = True
    start_time = time.monotonic()

    for item in parsed:
        if total_timeout is not None:
            elapsed = time.monotonic() - start_time
            remaining = total_timeout - elapsed
            if remaining <= 0:
                complete = False
                break
            req_timeout = min(timeout, max(1, int(remaining)))
        else:
            req_timeout = timeout

        ver = item["version"] if item["operator"] == "==" else None
        res = verify_package(item["name"], requested_version=ver, offline=offline, timeout=req_timeout)
        findings.append(res)
        if res.get("is_hallucinated"):
            hallucinated_count += 1
        elif res.get("status") in ("NETWORK_UNAVAILABLE", "VERIFICATION_ERROR"):
            unverified_network_count += 1
        elif res.get("severity") in ("warning", "error"):
            warnings_count += 1

    # Security policy: Fail-closed on network errors unless offline or explicitly permitted
    passed = complete and (hallucinated_count == 0) and (offline or allow_unverified_network or unverified_network_count == 0)
    return {
        "success": passed,
        "complete": complete,
        "file": str(file_path),
        "total_packages": len(parsed),
        "hallucinated_count": hallucinated_count,
        "unverified_network_count": unverified_network_count,
        "warnings_count": warnings_count,
        "findings": findings
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify Python package dependencies against PyPI to prevent AI hallucinations."
    )
    parser.add_argument(
        "target", nargs="?", help="Path to requirements.txt or package name"
    )
    parser.add_argument(
        "--package", "-p", type=str, help="Verify a specific package name"
    )
    parser.add_argument(
        "--version", "-v", type=str, help="Verify a specific version (when --package is used)"
    )
    parser.add_argument(
        "--offline", action="store_true", help="Run in offline mode (only check stdlib collisions)"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results in machine-readable JSON format"
    )
    parser.add_argument(
        "--allow-unverified-network", action="store_true", help="Do not fail verification when network is unreachable"
    )
    parser.add_argument(
        "--max-file-bytes", type=int, default=100000, help="Maximum file size in bytes (default: 100000)"
    )
    parser.add_argument(
        "--max-packages", type=int, default=100, help="Maximum number of packages to verify (default: 100)"
    )
    parser.add_argument(
        "--total-timeout", type=float, default=30.0, help="Total execution timeout in seconds (default: 30.0)"
    )
    args = parser.parse_args()

    if args.package or (args.target and not Path(args.target).exists() and not args.target.endswith(".txt") and not args.target.endswith(".toml")):
        pkg = args.package or args.target
        res = verify_package(pkg, requested_version=args.version, offline=args.offline)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"[{res['status']}] {res['message']}")
        sys.exit(0 if res["status"] in ("VERIFIED", "STDLIB_COLLISION") else 1)

    if args.target:
        target_path = Path(args.target).resolve()
        if target_path.is_dir():
            if (target_path / "requirements.txt").exists():
                target_file = target_path / "requirements.txt"
            elif (target_path / "pyproject.toml").exists():
                target_file = target_path / "pyproject.toml"
            else:
                target_file = target_path / "requirements.txt"
        else:
            target_file = target_path
    else:
        if Path("requirements.txt").exists():
            target_file = Path("requirements.txt").resolve()
        elif Path("pyproject.toml").exists():
            target_file = Path("pyproject.toml").resolve()
        else:
            target_file = Path("requirements.txt").resolve()
    result = verify_requirements_file(
        target_file,
        offline=args.offline,
        allow_unverified_network=args.allow_unverified_network,
        max_file_bytes=args.max_file_bytes,
        max_packages=args.max_packages,
        total_timeout=args.total_timeout,
    )

    if args.json:
        print(json.dumps(result, indent=2))
        if result.get("error"):
            sys.exit(2)
        sys.exit(0 if result.get("success") else 1)
    else:
        print(f"Supply Chain Verification: {result.get('file', target_file)}")
        print(f"Packages checked: {result.get('total_packages', 0)}")
        print(f"Hallucinated packages: {result.get('hallucinated_count', 0)}")
        print("-" * 60)

        for f in result.get("findings", []):
            badge = f"[{f['status']}]"
            print(f"{badge:24} {f['package']}: {f['message']}")
            for note in f.get("risk_notes", []):
                print(f"   └── WARNING: {note}")

        if result.get("success"):
            print("\nSUPPLY CHAIN DEPENDENCIES VERIFIED")
            sys.exit(0)
        else:
            print("\nSUPPLY CHAIN INTEGRITY VIOLATED")
            sys.exit(1)


if __name__ == "__main__":
    main()
