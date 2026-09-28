#!/usr/bin/env python3
"""AuraCode canonical CLI entrypoint."""
import importlib
import sys

try:
    from tools.assurance import main as _assurance_main
except ImportError:
    _tools_pkg = importlib.import_module("auracode.tools")
    sys.modules["tools"] = _tools_pkg
    _assurance_mod = importlib.import_module("auracode.tools.assurance")
    _assurance_main = getattr(_assurance_mod, "main")


def main() -> None:
    _assurance_main()


if __name__ == "__main__":
    main()
