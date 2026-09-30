#!/usr/bin/env python3
"""Aura Code deterministic fuzzing engine.

The first adapter targets Python callables using a declared JSON corpus and
recorded PRNG seed. Target crashes and hangs are findings; runner/import errors
are evaluator ERROR. Generated failing inputs are preserved for reproduction.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple

from tools.assurance_result import build_result, progression_state


_CALLABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*$")


def load_fuzz_suite(path: Path) -> Dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Fuzz suite manifest not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Fuzz suite manifest cannot be parsed: {exc}") from exc

    required = {
        "schema_version", "suite_id", "title", "requirements", "adapter",
        "target", "corpus", "seed", "iterations", "timeout_seconds",
    }
    if not isinstance(data, dict) or not required.issubset(data):
        raise ValueError("Fuzz suite manifest is incomplete.")
    if data.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported fuzz suite schema version.")
    if data.get("adapter") != "python-callable":
        raise ValueError("Unsupported fuzz adapter.")
    if not isinstance(data.get("requirements"), list) or not data["requirements"]:
        raise ValueError("Fuzz suite must reference at least one requirement.")
    if not isinstance(data.get("corpus"), list) or not data["corpus"]:
        raise ValueError("Fuzz suite requires a non-empty seed corpus.")
    if not isinstance(data.get("target"), str) or not _CALLABLE_RE.fullmatch(data["target"]):
        raise ValueError("Invalid Python callable declaration.")
    if not isinstance(data.get("iterations"), int) or data["iterations"] < 1:
        raise ValueError("Fuzz iterations must be a positive integer.")
    return data


def _mutate_scalar(value: Any, rng: random.Random) -> Any:
    if value is None:
        return rng.choice([None, "", 0, False, [], {}])
    if isinstance(value, bool):
        return not value
    if isinstance(value, int) and not isinstance(value, bool):
        choices = [
            0, 1, -1, value + 1, value - 1,
            2**31 - 1, -(2**31), 2**63 - 1, -(2**63),
        ]
        return rng.choice(choices)
    if isinstance(value, float):
        return rng.choice([0.0, -0.0, 1.0, -1.0, value * 2, 1e308, -1e308])
    if isinstance(value, str):
        choices = [
            "",
            value + "\x00",
            value * 2,
            value[::-1],
            "../" + value,
            "' OR 1=1 --",
            "<script>alert(1)</script>",
            "\ud800",
            "A" * min(max(len(value) * 4, 64), 4096),
        ]
        return rng.choice(choices)
    return value


def mutate_value(value: Any, rng: random.Random, depth: int = 0) -> Any:
    """Generate a deterministic mutation of JSON-compatible input."""
    if depth >= 4:
        return _mutate_scalar(value, rng)
    if isinstance(value, list):
        out = deepcopy(value)
        if not out:
            return [rng.choice([None, 0, "", False])]
        action = rng.choice(["mutate", "delete", "duplicate", "append"])
        if action == "mutate":
            index = rng.randrange(len(out))
            out[index] = mutate_value(out[index], rng, depth + 1)
        elif action == "delete" and out:
            del out[rng.randrange(len(out))]
        elif action == "duplicate" and out:
            out.insert(rng.randrange(len(out) + 1), deepcopy(rng.choice(out)))
        else:
            out.append(rng.choice([None, 0, "", False, [], {}]))
        return out
    if isinstance(value, dict):
        out = deepcopy(value)
        if not out:
            out["fuzz"] = rng.choice([None, 0, "", False])
            return out
        action = rng.choice(["mutate", "delete", "extra"])
        keys = list(out)
        if action == "mutate":
            key = rng.choice(keys)
            out[key] = mutate_value(out[key], rng, depth + 1)
        elif action == "delete":
            del out[rng.choice(keys)]
        else:
            out["__fuzz_extra__"] = rng.choice([None, 0, "", False, [], {}])
        return out
    return _mutate_scalar(value, rng)


def generate_inputs(corpus: List[Any], seed: int, iterations: int) -> List[Any]:
    rng = random.Random(seed)
    generated: List[Any] = []
    for _ in range(iterations):
        base = deepcopy(rng.choice(corpus))
        generated.append(mutate_value(base, rng))
    return generated


def _runner_code() -> str:
    return (
        "import importlib,json,sys\n"
        "spec=sys.argv[1]\n"
        "payload=json.loads(sys.stdin.read())\n"
        "module_name,func_name=spec.split(':',1)\n"
        "module=importlib.import_module(module_name)\n"
        "func=getattr(module,func_name)\n"
        "if isinstance(payload,dict) and '__args__' in payload:\n"
        "    result=func(*payload.get('__args__',[]),**payload.get('__kwargs__',{}))\n"
        "else:\n"
        "    result=func(payload)\n"
        "try:\n"
        "    json.dumps(result)\n"
        "except TypeError:\n"
        "    pass\n"
    )


def _invoke(spec: str, payload: Any, workspace: Path, timeout: float) -> Tuple[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(workspace) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        run = subprocess.run(
            [sys.executable, "-c", _runner_code(), spec],
            cwd=str(workspace),
            env=env,
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "TIMEOUT", ""
    except (OSError, subprocess.SubprocessError) as exc:
        return "EVALUATOR_ERROR", str(exc)

    if run.returncode == 0:
        return "OK", ""
    digest = hashlib.sha256(
        (run.stdout + "\n" + run.stderr).encode("utf-8", errors="replace")
    ).hexdigest()
    return "CRASH", digest


def evaluate_fuzz_suite(workspace: Path, manifest_path: Path) -> Dict[str, Any]:
    workspace = workspace.resolve()
    if not workspace.is_dir():
        result = build_result(
            check_id="fuzzing", status="ERROR",
            producer_tool="fuzz_engine", producer_method="deterministic_python_callable",
            workspace=str(workspace), reason="Workspace does not exist or is not a directory."
        )
        return {"status": "ERROR", "canonical_result": result, "progression": progression_state([result])}

    try:
        manifest = load_fuzz_suite(manifest_path)
    except (OSError, ValueError) as exc:
        result = build_result(
            check_id="fuzzing", status="ERROR",
            producer_tool="fuzz_engine", producer_method="deterministic_python_callable",
            workspace=str(workspace), reason=f"Fuzz suite configuration error: {exc}"
        )
        return {"status": "ERROR", "canonical_result": result, "progression": progression_state([result])}

    seed = int(manifest["seed"])
    iterations = int(manifest["iterations"])
    timeout = float(manifest["timeout_seconds"])
    generated = generate_inputs(list(manifest["corpus"]), seed, iterations)
    findings: List[Dict[str, Any]] = []

    for index, payload in enumerate(generated):
        outcome, detail = _invoke(str(manifest["target"]), payload, workspace, timeout)
        if outcome == "EVALUATOR_ERROR":
            result = build_result(
                check_id=f"fuzz:{str(manifest['suite_id']).lower()}",
                status="ERROR",
                producer_tool="fuzz_engine",
                producer_method="deterministic_python_callable",
                workspace=str(workspace),
                reason=f"Fuzz evaluator failed at iteration {index}.",
                legacy={"seed": seed, "iteration": index, "detail": detail},
            )
            return {
                "status": "ERROR", "suite_id": manifest["suite_id"], "seed": seed,
                "iteration": index, "canonical_result": result,
                "progression": progression_state([result]),
            }

        if outcome in {"CRASH", "TIMEOUT"}:
            serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
            findings.append({
                "iteration": index,
                "outcome": outcome,
                "input": payload,
                "input_digest": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
                "detail_digest": detail or None,
            })

    status = "FAIL" if findings else "PASS"
    reason = (
        f"Fuzzing found {len(findings)} crash/hang input(s)."
        if findings else f"{iterations} deterministic fuzz iterations completed without crash or hang."
    )
    result = build_result(
        check_id=f"fuzz:{str(manifest['suite_id']).lower()}",
        status=status,
        producer_tool="fuzz_engine",
        producer_method="deterministic_python_callable",
        workspace=str(workspace),
        reason=reason,
        severity="HIGH",
        legacy={
            "suite_id": manifest["suite_id"],
            "requirements": list(manifest["requirements"]),
            "target": manifest["target"],
            "seed": seed,
            "iterations": iterations,
        },
    )
    return {
        "status": status,
        "suite_id": manifest["suite_id"],
        "requirements": list(manifest["requirements"]),
        "seed": seed,
        "iterations": iterations,
        "findings": findings,
        "canonical_result": result,
        "progression": progression_state([result]),
    }
