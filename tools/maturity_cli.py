#!/usr/bin/env python3
"""Unified stable-maturity CLI router with backwards-compatible gate behavior."""
from __future__ import annotations

import sys
from typing import Optional, Sequence

SUBCOMMANDS = {
    "gate",
    "readiness",
    "study",
    "queue",
    "prepare",
    "infrastructure",
    "handoff",
}


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])

    # Backwards compatibility:
    #   auracode maturity . --json
    # remains the stable-release maturity gate.
    if not args or args[0] not in SUBCOMMANDS:
        from tools import maturity_gate
        return maturity_gate.main(args)

    command = args.pop(0)
    if command == "gate":
        from tools import maturity_gate
        return maturity_gate.main(args)

    if command == "readiness":
        from validation.tools import maturity_readiness
        return maturity_readiness.main(args)

    if command == "study":
        from validation.tools import maturity_studies
        return maturity_studies.main(args)

    if command == "queue":
        from validation.tools import maturity_queue
        return maturity_queue.main(args)

    if command == "prepare":
        from validation.tools import prepare_maturity_evidence
        return prepare_maturity_evidence.main(args)

    if command == "infrastructure":
        from validation.tools import validate_maturity_infrastructure
        return validate_maturity_infrastructure.main(args)

    if command == "handoff":
        from validation.tools import maturity_handoff
        return maturity_handoff.main(args)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
