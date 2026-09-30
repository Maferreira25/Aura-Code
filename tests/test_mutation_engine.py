#!/usr/bin/env python3
"""Comprehensive Unit Test Suite for AuraCode Lightweight AST Mutation Engine.

Verifies mutant generation across relational, arithmetic, boolean, and return operations,
as well as execution verification distinguishing real semantic tests from vitiated oracles.
"""

import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from tools.mutation_engine import (
    generate_mutants_for_source,
    execute_mutation_analysis,
    format_prescriptive_report,
)


class TestMutationEngine(unittest.TestCase):
    """Test suite for AST mutation analysis and vitiated oracle detection."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_mutant_generation_relational(self):
        code = "def is_positive(x):\n    return x > 0\n"
        mutants = generate_mutants_for_source(code)
        self.assertGreater(len(mutants), 0)
        types = [m.mutation_type for m in mutants]
        self.assertIn("RELATIONAL", types)
        rel_mutant = [m for m in mutants if m.mutation_type == "RELATIONAL"][0]
        self.assertEqual(rel_mutant.original_op, "Gt")
        self.assertEqual(rel_mutant.mutated_op, "LtE")

    def test_mutant_generation_arithmetic(self):
        code = "def calc(a, b):\n    return a + b\n"
        mutants = generate_mutants_for_source(code)
        self.assertGreater(len(mutants), 0)
        types = [m.mutation_type for m in mutants]
        self.assertIn("ARITHMETIC", types)
        arith_mutant = [m for m in mutants if m.mutation_type == "ARITHMETIC"][0]
        self.assertEqual(arith_mutant.original_op, "Add")
        self.assertEqual(arith_mutant.mutated_op, "Sub")

    def test_mutant_generation_boolean_and_return(self):
        code = "def flag_check():\n    val = True\n    return val\n"
        mutants = generate_mutants_for_source(code)
        types = [m.mutation_type for m in mutants]
        self.assertTrue("BOOLEAN_CONSTANT" in types or "RETURN_NULLIFICATION" in types)

    def test_mutation_execution_kills_mutants_with_real_assertions(self):
        # Production code
        prod_file = self.temp_dir / "calculator.py"
        prod_file.write_text(
            "def multiply(a, b):\n    return a + b\n",
            encoding="utf-8"
        )

        # Real test checking output
        test_file = self.temp_dir / "test_calc.py"
        test_file.write_text(
            "import unittest\n"
            "from calculator import multiply\n\n"
            "class TestCalc(unittest.TestCase):\n"
            "    def test_multiply(self):\n"
            "        self.assertEqual(multiply(2, 3), 5)\n\n"
            "if __name__ == '__main__':\n"
            "    unittest.main()\n",
            encoding="utf-8"
        )

        res = execute_mutation_analysis(prod_file, test_file)
        self.assertEqual(res["status"], "PASS")
        self.assertGreater(res["total_mutants"], 0)
        self.assertGreater(res["killed"], 0)
        self.assertFalse(res["vitiated_oracles_detected"])
        self.assertEqual(res["canonical_result"]["status"], "PASS")

    def test_timeout_is_not_counted_as_killed(self):
        prod_file = self.temp_dir / "timeout_target.py"
        prod_file.write_text("def f(x):\n    return x + 1\n", encoding="utf-8")
        test_file = self.temp_dir / "test_timeout_target.py"
        test_file.write_text(
            "import unittest\n"
            "from timeout_target import f\n"
            "class T(unittest.TestCase):\n"
            "    def test_f(self):\n"
            "        self.assertEqual(f(1), 2)\n",
            encoding="utf-8",
        )

        ok = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        with patch(
            "tools.mutation_engine.subprocess.run",
            side_effect=[ok, subprocess.TimeoutExpired(cmd=["python"], timeout=1)],
        ):
            res = execute_mutation_analysis(prod_file, test_file, max_mutants=1, timeout_sec=1)

        self.assertEqual(res["status"], "ERROR")
        self.assertEqual(res["killed"], 0)
        self.assertEqual(res["timeouts"], 1)
        self.assertEqual(res["evaluated_mutants"], 0)
        self.assertEqual(res["canonical_result"]["status"], "ERROR")

    def test_evaluator_exception_is_not_counted_as_killed(self):
        prod_file = self.temp_dir / "error_target.py"
        prod_file.write_text("def f(x):\n    return x + 1\n", encoding="utf-8")
        test_file = self.temp_dir / "test_error_target.py"
        test_file.write_text(
            "import unittest\n"
            "from error_target import f\n"
            "class T(unittest.TestCase):\n"
            "    def test_f(self):\n"
            "        self.assertEqual(f(1), 2)\n",
            encoding="utf-8",
        )

        ok = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        with patch(
            "tools.mutation_engine.subprocess.run",
            side_effect=[ok, RuntimeError("evaluator crashed")],
        ):
            res = execute_mutation_analysis(prod_file, test_file, max_mutants=1)

        self.assertEqual(res["status"], "ERROR")
        self.assertEqual(res["killed"], 0)
        self.assertEqual(res["errors"], 1)
        self.assertEqual(res["evaluated_mutants"], 0)
        self.assertEqual(res["canonical_result"]["status"], "ERROR")

    def test_mutation_execution_detects_vitiated_oracle(self):
        # Production code
        prod_file = self.temp_dir / "service.py"
        prod_file.write_text(
            "def compute_score(x):\n"
            "    if x > 10:\n"
            "        return 100\n"
            "    return 50\n",
            encoding="utf-8"
        )

        # Vitiated test that asserts nothing about the return value (tautological)
        test_file = self.temp_dir / "test_service.py"
        test_file.write_text(
            "import unittest\n"
            "from service import compute_score\n\n"
            "class TestService(unittest.TestCase):\n"
            "    def test_compute(self):\n"
            "        compute_score(15)\n"
            "        compute_score(5)\n"
            "        self.assertTrue(True)  # Vacuous assertion!\n\n"
            "if __name__ == '__main__':\n"
            "    unittest.main()\n",
            encoding="utf-8"
        )

        res = execute_mutation_analysis(prod_file, test_file)
        # Because the test passes regardless of mutations, mutants will SURVIVE!
        self.assertEqual(res["status"], "WARN")
        self.assertTrue(res["vitiated_oracles_detected"])
        self.assertGreater(res["survived"], 0)
        self.assertEqual(res["canonical_result"]["status"], "INCONCLUSIVE")
        self.assertIn("remediations", res)
        self.assertGreater(len(res["remediations"]), 0)

        first_rem = res["remediations"][0]
        self.assertIn("diagnosis", first_rem)
        self.assertIn("missing_scenario", first_rem)
        self.assertIn("plain_language_analogy", first_rem)
        self.assertIn("suggested_test_snippet", first_rem)
        self.assertIn("def test_", first_rem["suggested_test_snippet"])

        # Test prescriptive report formatting
        report_str = format_prescriptive_report(res)
        self.assertIn("AUDITORIA DE MUTAÇÃO AST & PRESCRIÇÃO DE CORREÇÃO", report_str)
        self.assertIn("PRESCRIÇÃO DE CORREÇÃO #", report_str)
        self.assertIn("Sugestão de Teste Unitário", report_str)


if __name__ == "__main__":
    unittest.main()
