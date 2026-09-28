#!/usr/bin/env python3
"""
AuraCode Forward Engineering Engine (auracode-forward).
Orchestrates the construction phase strictly from the approved House Blueprint
(_auracode_sdd/), scaffolding Clean Architecture, verifying AST quality gates,
and maintaining bounded, surgical development increments.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.audit import audit_workspace
from tools.check_architecture import check_architecture

PROFILE_MINIMUM_SPECS = {
    "micro": 1,
    "lite": 3,
    "standard": 7,
    "enterprise": 15,
}

CLEAN_ARCHITECTURE_LAYERS = ["domain", "usecases", "adapters", "infrastructure", "tests"]


class ForwardEngine:
    """Execution engine for construction of software from approved specifications."""

    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = (workspace_dir or Path.cwd()).resolve()

    def check_prerequisites(self, profile: str = "standard") -> Dict[str, Any]:
        """Verify strict prerequisites before permitting any code generation."""
        sdd_dir = self.workspace_dir / "_auracode_sdd"
        if not sdd_dir.is_dir() and (self.workspace_dir / "_reversa_sdd").is_dir():
            sdd_dir = self.workspace_dir / "_reversa_sdd"

        exists = sdd_dir.is_dir()
        specs = list(sdd_dir.glob("*.md")) if exists else []
        min_required = PROFILE_MINIMUM_SPECS.get(profile.lower(), 1)
        count = len(specs)

        # Check for approval marker in specs or status
        approved = False
        approval_evidence = None
        for s in specs:
            try:
                content = s.read_text(encoding="utf-8", errors="ignore").lower()
                if "status: aprovado" in content or "status: approved" in content or "planta aprovada" in content:
                    approved = True
                    approval_evidence = str(s.name)
                    break
            except (OSError, UnicodeDecodeError):
                continue

        ready = exists and count >= min_required and approved
        status = "READY" if ready else "BLOCKED"

        reasons = []
        if not exists:
            reasons.append("Diretório _auracode_sdd/ não encontrado.")
        elif count < min_required:
            reasons.append(f"Cadernos insuficientes para perfil '{profile}': encontrados {count}, mínimo {min_required}.")
        if not approved:
            reasons.append("Aprovação humana explícita não registrada nos cadernos da Planta Teórica.")

        return {
            "status": status,
            "profile": profile,
            "sdd_directory": str(sdd_dir),
            "specs_found": count,
            "min_required": min_required,
            "approved": approved,
            "approval_evidence": approval_evidence,
            "reasons": reasons,
            "can_build": ready
        }

    def scaffold_clean_architecture(self, app_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Scaffold Clean Architecture directory structure and base contracts."""
        base = (app_dir or (self.workspace_dir / "_auracode_forward" / "app")).resolve()
        created_dirs = []

        for layer in CLEAN_ARCHITECTURE_LAYERS:
            d = base / layer
            d.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(d.relative_to(self.workspace_dir)))

            init_file = d / "__init__.py"
            if not init_file.exists():
                init_file.write_text(f'"""AuraCode Clean Architecture layer: {layer}."""\n', encoding="utf-8")

        # Generate base contracts.json if not present
        contracts_file = base / "contracts.json"
        if not contracts_file.exists():
            contracts_data = {
                "name": "AuraCode Clean Architecture Standard Contract",
                "version": "1.0.0",
                "rules": [
                    {
                        "layer": "domain",
                        "allowed_dependencies": []
                    },
                    {
                        "layer": "usecases",
                        "allowed_dependencies": ["domain"]
                    },
                    {
                        "layer": "adapters",
                        "allowed_dependencies": ["domain", "usecases"]
                    },
                    {
                        "layer": "infrastructure",
                        "allowed_dependencies": ["domain", "usecases", "adapters"]
                    }
                ]
            }
            with open(contracts_file, "w", encoding="utf-8") as f:
                json.dump(contracts_data, f, indent=2)

        return {
            "status": "SCAFFOLDED",
            "base_directory": str(base),
            "layers_created": created_dirs,
            "contracts_file": str(contracts_file)
        }

    def verify_quality(self, target_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Execute full AST assurance suite on the forward application code."""
        target = (target_dir or (self.workspace_dir / "_auracode_forward")).resolve()
        if not target.exists():
            return {
                "status": "NOT_RUN",
                "message": f"Target directory does not exist: {target}"
            }

        audit_res = audit_workspace(target)
        return {
            "status": audit_res.get("status"),
            "target": str(target),
            "guarantees": audit_res.get("guarantees"),
            "violations_summary": audit_res.get("violations_summary")
        }


def main() -> None:
    args = sys.argv[1:]
    is_json = "--json" in args
    do_scaffold = "--scaffold" in args
    check_prereqs = "--check-prereqs" in args
    do_audit = "--audit" in args

    profile = "standard"
    for i, a in enumerate(args):
        if a.startswith("--profile="):
            profile = a.split("=", 1)[1]
        elif a in ("--profile", "-p") and i + 1 < len(args):
            profile = args[i + 1]

    engine = ForwardEngine()

    if check_prereqs or (not do_scaffold and not do_audit):
        prereqs = engine.check_prerequisites(profile=profile)
        if is_json:
            print(json.dumps(prereqs, indent=2, ensure_ascii=False))
        else:
            print(f"\n=======================================================")
            print(f"   AURA CODE — PRÉ-REQUISITOS DA FASE FORWARD")
            print(f"=======================================================")
            print(f"Status: {prereqs['status']}")
            print(f"Perfil: {prereqs['profile']} (Mínimo de cadernos: {prereqs['min_required']})")
            print(f"Cadernos encontrados: {prereqs['specs_found']}")
            print(f"Aprovação humana registrada: {'SIM' if prereqs['approved'] else 'NÃO'}")
            if prereqs['reasons']:
                print("\nBloqueios identificados:")
                for r in prereqs['reasons']:
                    print(f" - {r}")
            if prereqs['can_build']:
                print("\n>> Autorização concedida: Pode iniciar scaffolding e programação.")
            else:
                print("\n>> AVISO: Construção pausada até que a Planta Teórica seja aprovada.")

    if do_scaffold:
        scaffold_res = engine.scaffold_clean_architecture()
        if is_json:
            print(json.dumps(scaffold_res, indent=2, ensure_ascii=False))
        else:
            print(f"\nScaffolding Clean Architecture concluído em: {scaffold_res['base_directory']}")
            for l in scaffold_res['layers_created']:
                print(f" + {l}")

    if do_audit:
        qual = engine.verify_quality()
        if is_json:
            print(json.dumps(qual, indent=2, ensure_ascii=False))
        else:
            print(f"\nAuditoria da pasta forward: {qual.get('status')}")


if __name__ == "__main__":
    main()
