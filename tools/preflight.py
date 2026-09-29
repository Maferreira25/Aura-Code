#!/usr/bin/env python3
"""AuraCode Local Preflight & CI Mirror Validator.

Executes the complete deterministic assurance battery locally on the developer machine
mirroring the exact gates enforced by the GitHub Actions CI workflow:
1. Framework Integrity & Cryptographic Manifest (validate_framework.py)
2. Empirical Assurance Benchmark Scenarios (validate_suite.py)
3. Unit Test Suite Execution (unittest discover)
4. Clean Architecture Layer Contracts (auracode arch)
5. AI Slop & Silent Swallowed Exceptions (auracode slop)
6. Unclosed Resource Leaks (auracode leaks)
7. Strict Type Annotations (auracode types)
8. Test Integrity & Semantic Asserts (auracode tests)
9. Security Injection Vectors (auracode sec)
10. Requirement Ambiguity Evaluation (auracode ambiguity)

Zero external runtime dependencies (Pure Python Standard Library).
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def get_preflight_steps(root: Path) -> List[Dict[str, Any]]:
    """Build list of preflight gates dynamically resolved against workspace root."""
    assurance_script = str(root / "tools" / "assurance.py") if (root / "tools" / "assurance.py").is_file() else str(ROOT_DIR / "tools" / "assurance.py")
    framework_val = str(root / "tools" / "validate_framework.py") if (root / "tools" / "validate_framework.py").is_file() else str(ROOT_DIR / "tools" / "validate_framework.py")

    return [
        {
            "name": "Integridade do Framework e Manifesto Criptografico",
            "cmd": [sys.executable, framework_val],
            "condition": lambda r: (r / "MANIFEST.json").is_file(),
            "description": "Verifica se todos os arquivos correspondem aos hashes SHA-256 do MANIFEST.json.",
        },
        {
            "name": "Cenarios Empiricos de Referencia",
            "cmd": [sys.executable, str(root / "validation" / "tools" / "validate_suite.py")],
            "condition": lambda r: (r / "validation" / "tools" / "validate_suite.py").is_file(),
            "description": "Verifica a consistencia dos cenarios de teste empiricos.",
        },
        {
            "name": "Suite Completa de Testes Unitarios",
            "cmd": [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            "condition": lambda r: (r / "tests").is_dir(),
            "description": "Executa todos os testes unitarios da aplicacao.",
        },
        {
            "name": "Limites de Camadas (Clean Architecture)",
            "cmd": [sys.executable, assurance_script, "arch"],
            "description": "Verifica se nenhuma camada externa viola as regras de dominio.",
        },
        {
            "name": "AI Slop e Erros Silenciados (except: pass)",
            "cmd": [sys.executable, assurance_script, "slop"],
            "description": "Caca codigo morto, stubs abandonados e excecoes engolidas.",
        },
        {
            "name": "Vazamentos de Recursos (Arquivos e Conexoes)",
            "cmd": [sys.executable, assurance_script, "leaks"],
            "description": "Exige context managers ('with') em todos os arquivos e conexoes.",
        },
        {
            "name": "Tipagem Estrita (Type Annotations)",
            "cmd": [sys.executable, assurance_script, "types"],
            "description": "Garante assinaturas tipadas e combate o abuso irrestrito de 'Any'.",
        },
        {
            "name": "Integridade de Assercoes nos Testes",
            "cmd": [sys.executable, assurance_script, "tests"],
            "description": "Verifica que nenhum teste e viciado ou vazio (sem assercoes).",
        },
        {
            "name": "Vetores de Injecao e Seguranca (sec)",
            "cmd": [sys.executable, assurance_script, "sec"],
            "description": "Bloqueia eval, exec, shell=True e injecoes de SQL.",
        },
        {
            "name": "Ambiguidade de Requisitos (Gate G1)",
            "cmd": [sys.executable, assurance_script, "ambiguity"],
            "description": "Avalia o grau de clareza das especificacoes teoricas.",
        },
    ]


PREFLIGHT_STEPS = get_preflight_steps(ROOT_DIR)


def run_preflight_checks(workspace_root: Optional[Path] = None, quiet: bool = False) -> Dict[str, Any]:
    """Execute all preflight verification steps, returning complete summary report."""
    root = workspace_root.resolve() if workspace_root else ROOT_DIR

    if not quiet:
        print("=" * 80)
        print("   AURA CODE -- VERIFICACAO PREFLIGHT LOCAL (ESPELHO DA ESTEIRA CI/CD)")
        print("=" * 80)
        print(f">> Diretorio Raiz: {root}")
        print(">> Inspecionando conformidade local antes do envio para o GitHub...\n")

    steps = get_preflight_steps(root)
    steps_executed = 0
    passed_steps = 0
    failed_step: Optional[Dict[str, Any]] = None

    run_env = os.environ.copy()
    run_env["PYTHONPATH"] = str(root) + os.pathsep + run_env.get("PYTHONPATH", "")

    for idx, step in enumerate(steps, 1):
        condition = step.get("condition")
        if condition and not condition(root):
            continue

        steps_executed += 1
        name = step["name"]
        cmd = step["cmd"]

        if not quiet:
            sys.stdout.write(f"[{steps_executed:02d}] {name} ... ")
            sys.stdout.flush()

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=root,
                env=run_env,
                timeout=60.0
            )

            if res.returncode == 0:
                passed_steps += 1
                if not quiet:
                    print("APROVADO [OK]")
            else:
                if not quiet:
                    print("FALHOU [X]")
                failed_step = {
                    "step_number": steps_executed,
                    "name": name,
                    "description": step["description"],
                    "command": " ".join(cmd),
                    "returncode": res.returncode,
                    "stdout": res.stdout.strip(),
                    "stderr": res.stderr.strip()
                }
                break

        except subprocess.TimeoutExpired:
            if not quiet:
                print("TIMEOUT [X]")
            failed_step = {
                "step_number": steps_executed,
                "name": name,
                "description": step["description"],
                "command": " ".join(cmd),
                "returncode": -1,
                "stdout": "",
                "stderr": "O comando excedeu o tempo limite de 60 segundos."
            }
            break
        except Exception as exc:
            if not quiet:
                print(f"ERRO [{exc}] [X]")
            failed_step = {
                "step_number": steps_executed,
                "name": name,
                "description": step["description"],
                "command": " ".join(cmd),
                "returncode": -1,
                "stdout": "",
                "stderr": str(exc)
            }
            break

    if failed_step is not None:
        if not quiet:
            print("\n" + "=" * 80)
            print("[BLOQUEIO PREFLIGHT - AURA CODE]")
            print(f">> A verificacao #{failed_step['step_number']} ({failed_step['name']}) FALHOU!")
            print(">> O envio para o repositorio remoto DEVE SER CANCELADO para evitar quebra da esteira.")
            print("-" * 80)
            print("Detalhes do Erro:")
            output_msg = failed_step["stderr"] if failed_step["stderr"] else failed_step["stdout"]
            lines = [l for l in output_msg.splitlines() if l.strip()]
            display_lines = lines[-25:] if len(lines) > 25 else lines
            for line in display_lines:
                print(f"   {line}")
            print("-" * 80)
            print("Como Resolver:")
            print("   1. Analise o arquivo e linha apontados no relatorio acima.")
            print("   2. Se foi erro de slop (except: pass), remova o pass e adicione tratamento explicito.")
            print("   3. Se foi teste ou linter, execute o comando individualmente para ver a prescricao.")
            print("   4. Atualize o manifesto se novos arquivos foram criados: python tools/update_manifest.py")
            print("   5. Execute `auracode preflight` novamente ate obter aprovacao 100%.")
            print("=" * 80 + "\n")

        return {
            "status": "FAIL",
            "steps_executed": steps_executed,
            "passed_steps": passed_steps,
            "failed_step": failed_step
        }

    if not quiet:
        print("\n" + "=" * 80)
        print("[AURA PREFLIGHT APROVADO] 100% DE CONFORMIDADE COM A ESTEIRA DO CI/CD!")
        print(f">> Todos os {passed_steps} gates de garantia estatica e testes foram aprovados.")
        print(">> O codigo esta limpo, sem erros silenciosos e seguro para 'git push'.")
        print("=" * 80 + "\n")

    return {
        "status": "PASS",
        "steps_executed": steps_executed,
        "passed_steps": passed_steps,
        "failed_step": None
    }


def main() -> None:
    """CLI entrypoint for auracode preflight."""
    args = sys.argv[1:]
    quiet = "--quiet" in args or "-q" in args
    is_json = "--json" in args

    target = None
    for a in args:
        if not a.startswith("-"):
            target = Path(a)
            break

    res = run_preflight_checks(workspace_root=target, quiet=quiet or is_json)
    if is_json:
        import json
        print(json.dumps(res, indent=2, ensure_ascii=False))

    sys.exit(0 if res.get("status") == "PASS" else 1)


if __name__ == "__main__":
    main()
