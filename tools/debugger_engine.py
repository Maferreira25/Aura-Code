#!/usr/bin/env python3
"""
AuraCode Debugger Engine (auracode-debugger).
Enforces the Mandatory Reproduction Rule:
1. Logs bug reports into _auracode_bugs/<bug_id>/bug.md.
2. Generates and executes a reproduction test that MUST fail first.
3. Coordinates surgical fix verification and regression audit.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.audit import audit_workspace


class DebuggerEngine:
    """Defect triage, automated failure reproduction, and regression verification engine."""

    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = (workspace_dir or Path.cwd()).resolve()

    def register_bug(self, bug_id: str, description: str, steps: Optional[List[str]] = None) -> Dict[str, Any]:
        """Register defect into _auracode_bugs/<bug_id>/bug.md."""
        bug_dir = self.workspace_dir / "_auracode_bugs" / bug_id
        bug_dir.mkdir(parents=True, exist_ok=True)
        bug_file = bug_dir / "bug.md"

        steps = steps or ["1. Executar a funcionalidade com entrada específica.", "2. Observar falha inesperada."]

        md_content = [
            f"# Registro de Defeito: {bug_id}",
            f"",
            f"> **Status:** ABERTO (Aguardando teste de reprodução)",
            f"> **Identificador:** `{bug_id}`",
            f"",
            f"---",
            f"",
            f"## 📝 Descrição da Falha",
            f"{description}",
            f"",
            f"## 🔁 Passos para Reproduzir",
        ]
        for s in steps:
            md_content.append(f"- {s}")

        md_content.extend([
            f"",
            f"## 🧪 Teste de Reprodução Obrigatório",
            f"Arquivo: `tests/test_reproduce_{bug_id}.py`",
            f"Regra: O teste DEVE falhar antes de qualquer alteração no código da aplicação.",
            f""
        ])

        bug_file.write_text("\n".join(md_content), encoding="utf-8")

        return {
            "status": "REGISTERED",
            "bug_id": bug_id,
            "bug_file": str(bug_file),
            "description": description
        }

    def generate_reproduction_test(
        self,
        bug_id: str,
        test_content: Optional[str] = None,
        target_module: Optional[str] = None,
        target_function: Optional[str] = None,
        expected_result: Optional[Any] = None,
    ) -> Path:
        """Create automated reproduction test file in tests/."""
        tests_dir = self.workspace_dir / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        test_file = tests_dir / f"test_reproduce_{bug_id}.py"

        if not test_content:
            if target_module and target_function:
                test_content = (
                    f'#!/usr/bin/env python3\n'
                    f'"""Reproduction test for bug {bug_id} targeting {target_module}.{target_function}."""\n'
                    f'import unittest\n'
                    f'import {target_module}\n\n'
                    f'class TestReproduce_{bug_id}(unittest.TestCase):\n'
                    f'    def test_{bug_id}_reproduction(self):\n'
                    f'        resultado = getattr({target_module}, "{target_function}")()\n'
                    f'        esperado = {repr(expected_result)}\n'
                    f'        self.assertEqual(resultado, esperado, "Defeito {bug_id} ainda nao corrigido no modulo real.")\n\n'
                    f'if __name__ == "__main__":\n'
                    f'    unittest.main()\n'
                )
            else:
                test_content = (
                    f'#!/usr/bin/env python3\n'
                    f'"""Reproduction test for bug {bug_id}. Must fail until the fix is implemented in real code."""\n'
                    f'import unittest\n\n'
                    f'class TestReproduce_{bug_id}(unittest.TestCase):\n'
                    f'    def test_{bug_id}_reproduction(self):\n'
                    f'        # Conecte esta assercao a chamada do modulo ou endpoint real do sistema.\n'
                    f'        # O teste falha aqui para comprovar a presenca do defeito antes da correcao.\n'
                    f'        self.fail("Defeito {bug_id} reproduzido ativamente: aguardando correcao no codigo real.")\n\n'
                    f'if __name__ == "__main__":\n'
                    f'    unittest.main()\n'
                )

        test_file.write_text(test_content, encoding="utf-8")
        return test_file

    def verify_reproduction(self, bug_id: str) -> Dict[str, Any]:
        """Run the reproduction test to verify that it actually fails (proves the defect)."""
        test_file = self.workspace_dir / "tests" / f"test_reproduce_{bug_id}.py"
        if not test_file.exists():
            return {
                "status": "MISSING_TEST",
                "message": f"Reproduction test not found: {test_file}"
            }

        cmd = [sys.executable, "-m", "unittest", str(test_file.relative_to(self.workspace_dir))]
        proc = subprocess.run(cmd, cwd=str(self.workspace_dir), capture_output=True, text=True)

        is_failing = proc.returncode != 0
        return {
            "status": "REPRODUCED" if is_failing else "PASSING_UNEXPECTEDLY",
            "bug_id": bug_id,
            "test_file": str(test_file),
            "fails_as_expected": is_failing,
            "stdout": proc.stdout,
            "stderr": proc.stderr
        }

    def verify_fix(self, bug_id: str) -> Dict[str, Any]:
        """Verify that the reproduction test now passes and run audit for zero regressions."""
        test_file = self.workspace_dir / "tests" / f"test_reproduce_{bug_id}.py"
        if not test_file.exists():
            return {"status": "ERROR", "message": "Test file does not exist"}

        cmd = [sys.executable, "-m", "unittest", str(test_file.relative_to(self.workspace_dir))]
        proc = subprocess.run(cmd, cwd=str(self.workspace_dir), capture_output=True, text=True)

        test_passed = proc.returncode == 0
        audit_res = audit_workspace(self.workspace_dir)

        fixed = test_passed and audit_res.get("status") == "PASS"
        return {
            "status": "RESOLVED" if fixed else "STILL_FAILING",
            "test_passed": test_passed,
            "audit_status": audit_res.get("status"),
            "guarantees": audit_res.get("guarantees")
        }


def main() -> None:
    args = sys.argv[1:]
    is_json = "--json" in args
    create_test = "--create-test" in args
    verify_rep = "--verify-repro" in args
    verify_fix = "--verify-fix" in args

    bug_id = "bug_001"
    desc = "Comportamento inesperado relatado"
    target_dir = Path.cwd()

    clean_args = []
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--desc="):
            desc = a.split("=", 1)[1]
        elif a in ("--desc", "-d") and i + 1 < len(args):
            i += 1
            desc = args[i]
        elif a.startswith("--target="):
            target_dir = Path(a.split("=", 1)[1]).resolve()
        elif a in ("--target", "-t") and i + 1 < len(args):
            i += 1
            target_dir = Path(args[i]).resolve()
        elif not a.startswith("-"):
            clean_args.append(a)
        i += 1

    if clean_args:
        bug_id = clean_args[0]

    engine = DebuggerEngine(workspace_dir=target_dir)

    if verify_fix:
        res = engine.verify_fix(bug_id)
    elif verify_rep:
        res = engine.verify_reproduction(bug_id)
    else:
        res = engine.register_bug(bug_id, desc)
        if create_test:
            tf = engine.generate_reproduction_test(bug_id)
            res["test_file"] = str(tf)

    if is_json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(f"\n=======================================================")
        print(f"   AURA CODE — TRATAMENTO DE BUGS E DEFEITOS")
        print(f"=======================================================")
        print(f"Status: {res.get('status')}")
        print(f"Bug ID: {bug_id}")
        if "bug_file" in res:
            print(f"Registro: {res.get('bug_file')}")
        if "test_file" in res:
            print(f"Teste de Reprodução: {res.get('test_file')}")


if __name__ == "__main__":
    main()
