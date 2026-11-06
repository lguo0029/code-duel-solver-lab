import random
import unittest
from unittest.mock import patch

from code_duel.constraints import (
    ConsistencyStatus,
    SearchLimit,
    solve_constraints,
)
from code_duel.i18n import STRINGS, text
from code_duel.models import Clue
from code_duel.rules import score, universe
from code_duel.solver import Solver


class LocalizationTests(unittest.TestCase):
    def test_all_strings_have_both_languages(self):
        for key, translations in STRINGS.items():
            self.assertEqual(len(translations), 2)
            self.assertTrue(all(translations), key)
        self.assertEqual(text("start", "en"), "Start duel")
        self.assertEqual(text("start", "zh"), "开始对决")


class ConstraintTests(unittest.TestCase):
    def test_cross_check_against_complete_enumeration(self):
        rng = random.Random(9)
        for length in range(1, 5):
            codes = universe(length)
            for _ in range(20):
                clues = tuple(Clue(rng.choice(codes), rng.randrange(length + 1)) for _ in range(3))
                truth = any(all(score(c, h.guess) == h.feedback for h in clues) for c in codes)
                result = solve_constraints(length, clues, cap=1, budget=150000, timeout=3)
                self.assertEqual(
                    result.status,
                    ConsistencyStatus.CONSISTENT if truth else ConsistencyStatus.CONTRADICTORY,
                )
                self.assertTrue(
                    all(
                        all(score(c, h.guess) == h.feedback for h in clues)
                        for c in result.witnesses
                    )
                )

    def test_long_truthful_histories_and_proven_unsat(self):
        rng = random.Random(11)
        for length in range(5, 11):
            for _ in range(8):
                secret = "".join(rng.choice("0123456789") for _ in range(length))
                guesses = [
                    "".join(rng.choice("0123456789") for _ in range(length)) for _ in range(5)
                ]
                clues = tuple(Clue(g, score(secret, g)) for g in guesses)
                result = solve_constraints(length, clues, cap=1)
                self.assertEqual(result.status, ConsistencyStatus.CONSISTENT)
            unsat = solve_constraints(
                length, (Clue("0" * length, 1), Clue("1" * length, length)), cap=1
            )
            self.assertEqual(unsat.status, ConsistencyStatus.CONTRADICTORY)

    def test_explicit_unknown_and_transactional_recovery(self):
        unknown = solve_constraints(10, (), budget=0)
        self.assertEqual(unknown.status, ConsistencyStatus.UNKNOWN)
        self.assertEqual(unknown.witnesses, ())
        solver = Solver(5)
        guess = solver.candidates[0]
        before = (solver.history, solver.candidates)
        with patch("code_duel.solver.solve_constraints", return_value=unknown):
            with self.assertRaises(SearchLimit):
                solver.observe(guess, 0)
        self.assertEqual(before, (solver.history, solver.candidates))
        solver.observe(guess, 5)
        self.assertEqual(solver.candidates, (guess,))

    def test_witness_then_budget_is_consistent(self):
        result = solve_constraints(10, (), budget=12)
        self.assertEqual(result.status, ConsistencyStatus.CONSISTENT)
        self.assertTrue(result.witnesses)
        self.assertEqual(result.reason, "resource budget")

    def test_deadline_zero_is_unknown(self):
        self.assertEqual(solve_constraints(10, (), timeout=0).status, ConsistencyStatus.UNKNOWN)
