#!/usr/bin/env python3
"""Aura Guard: Real-time Pre-Tool Execution Safety Guardrail.

Intercepts, tokenizes, and inspects shell commands, scripts, and tool actions
before execution to prevent catastrophic operating system destruction,
repository data loss, secret credential leaks, and high-risk database drops.

Combines token-level semantic inspection with regex boundary heuristics.
Zero external dependencies (uses standard library 're', 'shlex', 'pathlib', 'argparse', 'json').
"""

import argparse
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Critical OS targets that must never be recursively removed
FORBIDDEN_RM_TARGETS = {
    "/", "/*", "~", "~/*", "*", "..", "../", "./*",
    "/bin", "/boot", "/dev", "/etc", "/lib", "/lib64",
    "/proc", "/root", "/sbin", "/sys", "/usr", "/var",
    "c:", "c:\\", "c:/", "c:\\*", "c:/*",
    "%systemroot%", "%windir%"
}

# Protected branches that must never be deleted
PROTECTED_BRANCHES = {"main", "master", "develop", "prod", "production", "release"}

# Inspection binaries that read file content to stdout
INSPECTION_BINARIES = {
    "cat", "type", "more", "less", "head", "tail",
    "grep", "egrep", "fgrep", "awk", "sed", "strings",
    "base64", "xxd", "hexdump", "od", "gc", "get-content"
}

# Regex heuristics for direct script and command line patterns
DIRECT_DANGER_PATTERNS = [
    # Forkbomb
    (
        r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",
        "CRITICAL",
        "DESTRUCTIVE_OS",
        "Classic shell forkbomb detected",
    ),
    # Raw block device overwrite via dd
    (
        r"\bdd\s+.*(?:of=/dev/[hs]d[a-z]|of=/dev/nvme|of=/dev/null\b(?!\s))",
        "CRITICAL",
        "DESTRUCTIVE_OS",
        "Raw block device overwrite via dd detected",
    ),
    # Disk formatting or partitioning
    (
        r"\b(?:mkfs(?:\.[a-z0-9]+)?|format\s+[a-zA-Z]:|fdisk\s+/dev/|diskpart)(?:\s|/|$)",
        "CRITICAL",
        "DESTRUCTIVE_OS",
        "Filesystem formatting or disk partitioning command detected",
    ),
    # System shutdown or reboot
    (
        r"\b(?:shutdown\s+-[hHrR]|reboot|init\s+[06]|halt\s+-p|poweroff)\b",
        "HIGH",
        "DESTRUCTIVE_OS",
        "System shutdown or reboot command detected",
    ),
    # SQL Drop commands
    (
        r"(?i)\bDROP\s+DATABASE\b",
        "CRITICAL",
        "DANGEROUS_DB",
        "High-risk database destruction (DROP DATABASE) detected",
    ),
    (
        r"(?i)\bDROP\s+TABLE\b",
        "HIGH",
        "DANGEROUS_DB",
        "High-risk table destruction (DROP TABLE) detected without migration harness",
    ),
    (
        r"(?i)\bTRUNCATE\s+TABLE\b",
        "HIGH",
        "DANGEROUS_DB",
        "High-risk table truncation (TRUNCATE TABLE) detected without migration harness",
    ),
    # Secret exfiltration pipeline into network tools
    (
        r"\b(?:cat|type|gc|get-content)\s+.*(?:\.env|id_rsa|credentials).*\|\s*(?:curl|wget|nc|netcat|iwr|irm|invoke-webrequest|invoke-restmethod)\b",
        "CRITICAL",
        "SECRET_LEAK",
        "Exfiltration pipeline detected: streaming sensitive file into network tool",
    ),
    # PowerShell disk formatting or partitioning cmdlets
    (
        r"(?i)\b(?:format-volume|clear-disk|remove-partition|initialize-disk)\b",
        "CRITICAL",
        "DESTRUCTIVE_OS",
        "PowerShell disk formatting or partitioning cmdlet detected",
    ),
    # PowerShell system shutdown or restart
    (
        r"(?i)\b(?:stop-computer|restart-computer)\b",
        "HIGH",
        "DESTRUCTIVE_OS",
        "PowerShell system shutdown or restart cmdlet detected",
    ),
]

# PowerShell aliases/cmdlets that recursively and forcibly delete filesystem entries
POWERSHELL_DELETE_COMMANDS = re.compile(r"\b(?:remove-item|ri|rmdir|rd|del|erase)\b", re.IGNORECASE)

# Drive roots, home directory, and system environment variables that must never be
# targeted by a recursive, forced PowerShell delete
POWERSHELL_DANGEROUS_TARGET = re.compile(
    r"(?:^|[\s'\"])(?:[a-zA-Z]:\\?['\"]?|[a-zA-Z]:/?['\"]?|~[\\/]?|"
    r"\$env:(?:systemroot|windir|userprofile|homedrive|programfiles(?:\(x86\))?)\b)(?:[\s'\"]|$)",
    re.IGNORECASE,
)


def split_shell_pipeline(cmd_str: str) -> List[str]:
    """Splits a composite shell command line by operators (;, &&, ||, |, &)."""
    if not cmd_str or not cmd_str.strip():
        return []

    tokens = re.split(r"(?:&&|\|\||;|\||\n)", cmd_str)
    commands = []
    for token in tokens:
        cleaned = token.strip()
        if cleaned:
            commands.append(cleaned)
    return commands


def tokenize_command(cmd_str: str) -> List[str]:
    """Tokenizes a command string using shlex with a safe fallback."""
    try:
        return shlex.split(cmd_str, posix=False)
    except Exception:
        return cmd_str.split()


def normalize_target_path(token: str) -> str:
    """Normalizes a file or directory path for deterministic safety checking."""
    val = token.strip("'\"").lower().replace("\\", "/")
    if val in {"/", "c:", "c:/"}:
        return val
    # Strip trailing slashes for directories longer than 1 character
    if len(val) > 1 and val.endswith("/"):
        val = val.rstrip("/")
    return val


def is_target_sensitive(token: str) -> bool:
    """Checks whether a file path token points to a sensitive secret or key."""
    cleaned = token.strip("'\"").replace("\\", "/")
    filename = Path(cleaned).name.lower()

    # Check .env files (excluding .example, .sample, .template)
    if filename == ".env" or (filename.startswith(".env.") and not (filename.endswith(".example") or filename.endswith(".sample") or filename.endswith(".template"))):
        return True

    # Check SSH keys (excluding public keys .pub)
    if filename in {"id_rsa", "id_ed25519", "id_ecdsa", "id_dsa"}:
        return True

    # Check certificates & private keys
    if filename.endswith((".pem", ".key", ".p12", ".pfx", ".pkcs12")):
        return True

    # Check credentials
    if filename in {"credentials.json", "client_secret.json", "service_account.json"}:
        return True

    # Check cloud credentials
    if "aws/credentials" in cleaned or ".config/gcloud" in cleaned or ".azure/credentials" in cleaned:
        return True

    # Check system authentication files
    if cleaned in {"/etc/shadow", "/etc/passwd", "etc/shadow", "etc/passwd"}:
        return True

    return False


def inspect_subcommand(sub_cmd: str) -> Optional[Dict[str, Any]]:
    """Evaluates a single atomic subcommand."""
    sub_clean = sub_cmd.strip()
    if not sub_clean:
        return None

    # Layer 1: Check direct regex heuristics
    for pattern, severity, rule, reason in DIRECT_DANGER_PATTERNS:
        if re.search(pattern, sub_clean, re.IGNORECASE):
            return {
                "safe": False,
                "rule": rule,
                "reason": reason,
                "severity": severity,
                "command": sub_clean,
            }

    # Layer 2: Semantic token analysis
    tokens = tokenize_command(sub_clean)
    if not tokens:
        return None

    bin_name = Path(tokens[0].strip("'\"")).name.lower()
    if bin_name.endswith(".exe"):
        bin_name = bin_name[:-4]

    # --- Check Disk Partitioning & Formatting Binaries ---
    if bin_name in {"fdisk", "gdisk", "parted", "diskpart"}:
        return {
            "safe": False,
            "rule": "DESTRUCTIVE_OS",
            "reason": f"Disk partitioning tool detected: '{bin_name}'",
            "severity": "CRITICAL",
            "command": sub_clean,
        }
    if bin_name.startswith("mkfs") or bin_name == "format":
        return {
            "safe": False,
            "rule": "DESTRUCTIVE_OS",
            "reason": f"Filesystem formatting tool detected: '{bin_name}'",
            "severity": "CRITICAL",
            "command": sub_clean,
        }

    # --- Check RM / UNLINK ---
    if bin_name in {"rm", "unlink"}:
        for t in tokens[1:]:
            val = normalize_target_path(t)
            if val in FORBIDDEN_RM_TARGETS or val.startswith("/etc") or val.startswith("/boot") or val.startswith("/bin") or val.startswith("/usr"):
                return {
                    "safe": False,
                    "rule": "DESTRUCTIVE_OS",
                    "reason": f"Destructive rm command targeting vital system location: '{t}'",
                    "severity": "CRITICAL",
                    "command": sub_clean,
                }
            if val == ".git" or val.endswith("/.git"):
                return {
                    "safe": False,
                    "rule": "DESTRUCTIVE_GIT",
                    "reason": "Destruction of internal .git metadata directory detected",
                    "severity": "CRITICAL",
                    "command": sub_clean,
                }

    # --- Check Windows RMDIR / RD ---
    if bin_name in {"rmdir", "rd"}:
        has_s = any(t.lower() in {"/s", "-s"} for t in tokens[1:])
        for t in tokens[1:]:
            val = normalize_target_path(t)
            if has_s and (val in FORBIDDEN_RM_TARGETS or val in {"c:", "c:/"}):
                return {
                    "safe": False,
                    "rule": "DESTRUCTIVE_OS",
                    "reason": f"Destructive rmdir /s targeting vital drive: '{t}'",
                    "severity": "CRITICAL",
                    "command": sub_clean,
                }
            if val == ".git" or val.endswith("/.git"):
                return {
                    "safe": False,
                    "rule": "DESTRUCTIVE_GIT",
                    "reason": "Destruction of internal .git metadata directory detected",
                    "severity": "CRITICAL",
                    "command": sub_clean,
                }

    # --- Check DEL / ERASE ---
    if bin_name in {"del", "erase"}:
        has_s = any(t.lower() in {"/s", "-s"} for t in tokens[1:])
        has_f = any(t.lower() in {"/f", "-f", "/q", "-q"} for t in tokens[1:])
        for t in tokens[1:]:
            val = normalize_target_path(t)
            if (has_s or has_f) and (val in {"*.*", "*", "c:/*.*", "c:/*"} or val in FORBIDDEN_RM_TARGETS):
                return {
                    "safe": False,
                    "rule": "DESTRUCTIVE_OS",
                    "reason": f"Destructive del command targeting entire drive or wildcards: '{t}'",
                    "severity": "CRITICAL",
                    "command": sub_clean,
                }
            if val == ".git" or val.endswith("/.git"):
                return {
                    "safe": False,
                    "rule": "DESTRUCTIVE_GIT",
                    "reason": "Destruction of internal .git directory via del detected",
                    "severity": "CRITICAL",
                    "command": sub_clean,
                }

    # --- Check PowerShell Remove-Item / rd / del aliases used recursively and forced ---
    if POWERSHELL_DELETE_COMMANDS.search(sub_clean):
        lower_sub = sub_clean.lower()
        has_recurse = "-recurse" in lower_sub or "-r " in lower_sub
        has_force = "-force" in lower_sub or "-f " in lower_sub or "-confirm:$false" in lower_sub
        if has_recurse and has_force and POWERSHELL_DANGEROUS_TARGET.search(sub_clean):
            return {
                "safe": False,
                "rule": "DESTRUCTIVE_OS",
                "reason": "Destructive PowerShell recursive/forced delete targeting a drive root, home, or system environment path detected",
                "severity": "CRITICAL",
                "command": sub_clean,
            }
        if has_force and (".git" in lower_sub) and re.search(r"\.git\b(?!\w)", lower_sub):
            return {
                "safe": False,
                "rule": "DESTRUCTIVE_GIT",
                "reason": "Destruction of internal .git metadata directory detected via PowerShell",
                "severity": "CRITICAL",
                "command": sub_clean,
            }

    # --- Check GIT Operations ---
    if bin_name == "git":
        git_args = [t.strip("'\"").lower() for t in tokens[1:]]
        if not git_args:
            return None
        sub_action = git_args[0]

        # git push --force / -f
        if sub_action == "push":
            if any(a in {"--force", "-f"} or a.startswith("+refs/") or a in {"+master", "+main"} for a in git_args[1:]):
                return {
                    "safe": False,
                    "rule": "DESTRUCTIVE_GIT",
                    "reason": "Destructive Git force push detected (overwrites remote repository history)",
                    "severity": "HIGH",
                    "command": sub_clean,
                }

        # git reset --hard
        if sub_action == "reset":
            if "--hard" in git_args:
                return {
                    "safe": False,
                    "rule": "DESTRUCTIVE_GIT",
                    "reason": "Unsafe git reset --hard detected (destroys uncommitted working directory changes)",
                    "severity": "HIGH",
                    "command": sub_clean,
                }

        # git clean -fdx
        if sub_action == "clean":
            joined_flags = "".join([a for a in git_args[1:] if a.startswith("-")])
            if "f" in joined_flags and ("d" in joined_flags or "x" in joined_flags):
                return {
                    "safe": False,
                    "rule": "DESTRUCTIVE_GIT",
                    "reason": "Aggressive git clean -fdx detected without dry-run",
                    "severity": "HIGH",
                    "command": sub_clean,
                }

        # git branch -D / -d protected
        if sub_action == "branch":
            if any(a in {"-d", "-d", "--delete"} for a in git_args[1:]):
                target_branches = [a for a in git_args[1:] if not a.startswith("-")]
                if any(b in PROTECTED_BRANCHES for b in target_branches):
                    return {
                        "safe": False,
                        "rule": "DESTRUCTIVE_GIT",
                        "reason": f"Deletion of protected repository branch detected: {target_branches}",
                        "severity": "HIGH",
                        "command": sub_clean,
                    }

    # --- Check SECRET LEAKS / INSPECTION ---
    if bin_name in INSPECTION_BINARIES:
        for t in tokens[1:]:
            if t.startswith("-"):
                continue
            if is_target_sensitive(t):
                return {
                    "safe": False,
                    "rule": "SECRET_LEAK",
                    "reason": f"Unauthorized inspection of sensitive credential/secret file: '{t}'",
                    "severity": "CRITICAL",
                    "command": sub_clean,
                }

    return None


def inspect_command(command: str) -> Dict[str, Any]:
    """Inspects a complete shell command string across pipelines and operators."""
    cmd_clean = command.strip()
    if not cmd_clean:
        return {
            "safe": True,
            "rule": None,
            "reason": "Empty command approved",
            "severity": "NONE",
            "command": command,
        }

    # Evaluate direct danger heuristics on the entire command line first (catches forkbombs and composite pipelines)
    for pattern, severity, rule, reason in DIRECT_DANGER_PATTERNS:
        if re.search(pattern, cmd_clean, re.IGNORECASE):
            return {
                "safe": False,
                "rule": rule,
                "reason": reason,
                "severity": severity,
                "command": cmd_clean,
            }

    sub_commands = split_shell_pipeline(cmd_clean)
    if not sub_commands:
        sub_commands = [cmd_clean]

    for sub in sub_commands:
        violation = inspect_subcommand(sub)
        if violation:
            return violation

    return {
        "safe": True,
        "rule": None,
        "reason": "Command passed all safety guardrail checks",
        "severity": "NONE",
        "command": command,
    }


def generate_hooks_config(workspace_root: Path) -> Dict[str, Any]:
    """Generates standard hooks.json configuration for Antigravity and Agent IDEs."""
    has_local_tool = (workspace_root / "tools" / "pre_tool_guard.py").is_file()
    guard_cmd = "python tools/pre_tool_guard.py check" if has_local_tool else "auracode guard check"
    diff_cmd = "python -m tools.assurance diff . --max-lines 500" if has_local_tool else "auracode diff . --max-lines 500"
    return {
        "$schema": "https://json-schemas.org/draft/2020-12/schema",
        "version": "1.0.0",
        "framework": "AuraCode Guard",
        "description": "Active PreToolUse and PostToolUse security hooks for agent guardrails.",
        "hooks": {
            "PreToolUse": [
                {
                    "name": "aura-guard-pre-command",
                    "description": "Intercepts terminal commands before execution to block destructive actions and secret exfiltration.",
                    "match_tools": ["run_command", "bash", "terminal", "execute_command", "shell"],
                    "action": "execute",
                    "command": guard_cmd,
                    "input_field": "CommandLine",
                    "fail_closed": True,
                }
            ],
            "PostToolUse": [
                {
                    "name": "aura-guard-post-audit",
                    "description": "Verifies that surgical diff and repository integrity were preserved after tool execution.",
                    "match_tools": ["write_to_file", "replace_file_content", "multi_replace_file_content"],
                    "action": "execute",
                    "command": diff_cmd,
                    "fail_closed": False,
                }
            ]
        }
    }


def install_git_pre_push_hook(workspace_root: Path) -> Optional[Path]:
    """Installs or updates the .git/hooks/pre-push hook in the target git repository."""
    git_dir = workspace_root / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        return None

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    pre_push_file = hooks_dir / "pre-push"

    script_content = (
        "#!/bin/sh\n"
        "# AuraCode Git Pre-Push Guardrail Hook\n"
        "# Deterministically enforces local CI preflight gates before push.\n\n"
        "echo \"================================================================================\"\n"
        "echo \"   AURA CODE -- GIT PRE-PUSH ASSURANCE GUARD\"\n"
        "echo \"================================================================================\"\n"
        "PY_BIN=\"\"\n"
        "for cand in python python3 py; do\n"
        "    if command -v \"$cand\" >/dev/null 2>&1; then\n"
        "        if \"$cand\" -c \"import sys; sys.exit(0)\" >/dev/null 2>&1; then\n"
        "            PY_BIN=\"$cand\"\n"
        "            break\n"
        "        fi\n"
        "    fi\n"
        "done\n\n"
        "if [ -z \"$PY_BIN\" ]; then\n"
        "    echo \"[ERRO] Interpretador Python funcional nao encontrado no PATH.\"\n"
        "    exit 1\n"
        "fi\n\n"
        "if [ -f \"tools/assurance.py\" ]; then\n"
        "    \"$PY_BIN\" tools/assurance.py preflight\n"
        "    STATUS=$?\n"
        "elif command -v auracode >/dev/null 2>&1; then\n"
        "    auracode preflight\n"
        "    STATUS=$?\n"
        "else\n"
        "    echo \"[AVISO] Aura Code CLI nao encontrado; prosseguindo sem preflight.\"\n"
        "    exit 0\n"
        "fi\n\n"
        "if [ $STATUS -ne 0 ]; then\n"
        "    echo \"\"\n"
        "    echo \"[BLOQUEIO DE PUSH] O envio foi cancelado pelo Aura Code Preflight.\"\n"
        "    echo \"Corrija os problemas apontados acima antes de tentar 'git push' novamente.\"\n"
        "    echo \"================================================================================\"\n"
        "    exit 1\n"
        "fi\n\n"
        "exit 0\n"
    )

    with open(pre_push_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(script_content)

    try:
        current_mode = pre_push_file.stat().st_mode
        pre_push_file.chmod(current_mode | 0o755)
    except (OSError, PermissionError):
        return pre_push_file

    return pre_push_file


def install_hooks(workspace_root: Path) -> Path:
    """Installs or updates the .agents/hooks.json file in the target workspace."""
    agents_dir = workspace_root / ".agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    hooks_file = agents_dir / "hooks.json"
    
    config = generate_hooks_config(workspace_root)
    with open(hooks_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Install Git pre-push hook if inside a git repository
    install_git_pre_push_hook(workspace_root)

    return hooks_file


def main(argv: Optional[List[str]] = None) -> int:
    """CLI Entrypoint for Aura Guard."""
    parser = argparse.ArgumentParser(
        prog="auracode guard",
        description="Aura Guard: Real-time Pre-Tool Execution Safety Guardrail"
    )
    subparsers = parser.add_subparsers(dest="guard_action", help="Guard action to execute")

    # Subcommand: check
    check_p = subparsers.add_parser("check", help="Check command safety before execution")
    check_p.add_argument("command_str", nargs="?", default="", help="Command line string to evaluate")
    check_p.add_argument("--cmd", type=str, default=None, help="Command line string to evaluate (flag alias)")
    check_p.add_argument("--tool", type=str, default=None, help="Tool or harness name issuing the command")
    check_p.add_argument("--json", action="store_true", help="Output result in JSON format")

    # Subcommand: install
    install_p = subparsers.add_parser("install", help="Install .agents/hooks.json in target workspace")
    install_p.add_argument("target", nargs="?", default=".", help="Workspace root directory")

    args = parser.parse_args(argv)

    if not args.guard_action:
        parser.print_help()
        return 0

    if args.guard_action == "check":
        cmd_to_check = args.cmd if args.cmd is not None else args.command_str
        if not cmd_to_check:
            # Read from stdin if piped
            if not sys.stdin.isatty():
                cmd_to_check = sys.stdin.read().strip()

        if not cmd_to_check:
            sys.stderr.write("Error: No command provided to inspect.\n")
            return 1

        result = inspect_command(cmd_to_check)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if not result["safe"]:
                sys.stderr.write(f"\n[AURA GUARD BLOCKED] Severity: {result['severity']} | Rule: {result['rule']}\n")
                sys.stderr.write(f"Reason: {result['reason']}\n")
                sys.stderr.write(f"Blocked Command: {result['command']}\n\n")
            else:
                print(f"[AURA GUARD OK] {result['reason']}")
        return 0 if result["safe"] else 1

    elif args.guard_action == "install":
        root_dir = Path(args.target).resolve()
        hooks_path = install_hooks(root_dir)
        git_hook = root_dir / ".git" / "hooks" / "pre-push"
        print(f"[AURA GUARD] Hooks installed successfully at: {hooks_path}")
        if git_hook.exists():
            print(f"[AURA GUARD] Git Pre-Push Hook active at: {git_hook}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
