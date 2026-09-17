"""AuraCode — Agentic Unified Reliability & Assurance Framework.

Provides programmatic and CLI access to AST linters, Clean Architecture contracts,
supply chain anti-hallucination engines, and MCP guardrails.
"""

__version__ = "0.1.1"

from tools.assurance import main as cli
from tools.check_architecture import check_architecture
from tools.verify_dependencies import verify_package, verify_requirements_file
from tools.check_surgical_diff import check_surgical_diff
from tools.check_slop_code import check_file as check_slop
from tools.check_resource_leaks import check_file as check_leaks
from tools.check_strict_types import check_file as check_types
from tools.check_test_integrity import TestIntegrityVisitor
from tools.check_injection_vectors import check_file as check_sec
from tools.check_requirements_ambiguity import analyze_workspace as check_ambiguity
from tools.assess import assess_data, assess_file

__all__ = [
    "__version__",
    "cli",
    "check_architecture",
    "verify_package",
    "verify_requirements_file",
    "check_surgical_diff",
    "check_slop",
    "check_leaks",
    "check_types",
    "TestIntegrityVisitor",
    "check_sec",
    "check_ambiguity",
    "assess_data",
    "assess_file",
]
