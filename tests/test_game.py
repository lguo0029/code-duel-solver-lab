import random
import unittest
from unittest.mock import patch

from code_duel.engine import Game
from code_duel.models import Clue, Difficulty, LogicError
from code_duel.rules import ALL_CODES, score, validate
from code_duel.simulation import simulate
from code_duel.solver import Solver
from code_duel.strategies import choose


class RulesTests(unittest.TestCase):
    def test_examples(self):
        for secret, guess, expected in [
            ("1234", "1234", 4),
            ("1234", "4321", 0),
            ("6289", "1234", 1),
            ("1122", "1212", 2),
            ("0000", "1111", 0),
            ("0000", "0000", 4),
            ("0037", "0038", 3),
        ]:
            with self.subTest(secret=secret, guess=guess):
                self.assertEqual(score(secret, guess), expected)

    def test_invalid(self):
        for value in [1234, "", "123", "12345", "１２３４", "١٢٣٤", "12 4", None]:
            with self.assertRaises(ValueError):
                validate(value)

    def test_universe(self):
        self.assertEqual(len(set(ALL_CODES)), 10000)
        self.assertEqual(ALL_CODES[0], "0000")


class SolverTests(unittest.TestCase):
    def test_zero_and_multiple_history(self):
        solver = Solver()
        solver.observe("1234", 0)
        self.assertNotIn("6289", solver.candidates)
        solver.observe("0000", 1)
        self.assertTrue(
            all(
                all(score(c, h.guess) == h.feedback for h in solver.history)
                for c in solver.candidates
            )
        )
        self.assertIn("2105", solver.candidates)  # 1 and 2 still allowed elsewhere

    def test_truth_survives_random_histories(self):
        rng = random.Random(10)
        for secret in rng.sample(ALL_CODES, 100):
            solver = Solver()
            for _ in range(4):
                guess = rng.choice(solver.candidates)
                solver.observe(guess, score(secret, guess))
                self.assertIn(secret, solver.candidates)
                if guess == secret:
                    break

    def test_transactional_impossible_feedback(self):
        solver = Solver()
        solver.observe("0000", 4)
        before = (solver.history, solver.candidates)
        with self.assertRaises(LogicError):
            solver.observe("1111", 0)
        self.assertEqual(before, (solver.history, solver.candidates))

    def test_contradiction_does_not_commit(self):
        solver = Solver()
        solver.observe("0000", 0)
        solver.observe("1111", 3)
        before = (solver.history, solver.candidates)
        guess = solver.candidates[0]
        # An all-correct answer is always possible; choose an impossible bin instead.
        possible = {score(c, guess) for c in solver.candidates}
        impossible = next(i for i in range(5) if i not in possible)
        with self.assertRaises(LogicError):
            solver.observe(guess, impossible)
        self.assertEqual(before, (solver.history, solver.candidates))


class StrategyTests(unittest.TestCase):
    def test_all_difficulties_legal_and_converge(self):
        for level in Difficulty:
            solver = Solver()
            rng = random.Random(123)
            for _ in range(40):
                guess = choose(solver, level, rng)
                self.assertIn(guess, solver.candidates)
                self.assertNotIn(guess, [h.guess for h in solver.history])
                self.assertTrue(all(score(guess, h.guess) == h.feedback for h in solver.history))
                solver.observe(guess, score("0037", guess))
                if guess == "0037":
                    break
            else:
                self.fail("did not converge")

    def test_singleton_and_empty(self):
        for level in Difficulty:
            solver = Solver()
            solver._candidates = ("0037",)
            self.assertEqual(choose(solver, level), "0037")
            solver._candidates = ()
            with self.assertRaises(LogicError):
                choose(solver, level)

    def test_revalidate_corrupted_candidates(self):
        solver = Solver()
        solver.observe("1234", 0)
        solver._candidates = ("6289",)
        for level in Difficulty:
            with self.assertRaises(LogicError):
                choose(solver, level)

    def test_secret_is_not_in_interface(self):
        import inspect

        self.assertEqual(list(inspect.signature(Solver).parameters), ["length"])
        self.assertNotIn("secret", inspect.signature(choose).parameters)
        self.assertFalse(any("secret" in key for key in vars(Solver())))

    def test_simulation_reproducible(self):
        a = simulate("0007", "easy", 7)
        b = simulate("0007", "easy", 7)
        self.assertEqual(
            [(h["guess"], h["feedback"], h["candidates"]) for h in a["history"]],
            [(h["guess"], h["feedback"], h["candidates"]) for h in b["history"]],
        )


class EngineTests(unittest.TestCase):
    def test_outcomes_and_end_guard(self):
        for guess, ai_guess, feedback, expected in [
            ("9999", "1234", 0, "player"),
            ("1111", "0037", 4, "ai"),
            ("9999", "0037", 4, "draw"),
        ]:
            game = Game(4, "easy", ai_secret="9999")
            with patch("code_duel.engine.choose", return_value=ai_guess):
                self.assertEqual(game.begin_round(guess), ai_guess)
            self.assertIsNone(game.outcome)
            game.finish_round(feedback)
            self.assertEqual(game.outcome, expected)
            self.assertEqual(game.reveal(), "9999")
            with self.assertRaises(LogicError):
                game.begin_round("0000")

    def test_manual_feedback_and_atomic_correction(self):
        game = Game(1, "easy", ai_secret="9")
        with patch("code_duel.engine.choose", side_effect=["1", "2"]):
            game.begin_round("0")
            game.finish_round(0)
            game.begin_round("0")
        # For one digit, any unexcluded digit can still be the secret.
        before = (game.pending, game.rounds, game.candidate_count)
        with self.assertRaises(ValueError):
            game.finish_round(2)
        self.assertEqual(before, (game.pending, game.rounds, game.candidate_count))
        game.finish_round(1)
        self.assertEqual(game.outcome, "ai")
        self.assertFalse(any("player_secret" in key for key in vars(game)))

    def test_conflicting_feedback_keeps_pending(self):
        game = Game(2, "easy", ai_secret="99")
        with patch("code_duel.engine.choose", side_effect=["00", "01", "10"]):
            game.begin_round("22")
            game.finish_round(1)
            game.begin_round("22")
            game.finish_round(0)
            game.begin_round("22")
        with self.assertRaisesRegex(LogicError, "contradict"):
            game.finish_round(0)
        self.assertEqual(len(game.rounds), 2)
        self.assertEqual(game.pending, ("22", "10"))
        game.finish_round(1)
        self.assertEqual(len(game.rounds), 3)

    def test_fixed_hidden_pending_and_reset(self):
        game = Game(4, "easy", ai_secret="9999")
        with self.assertRaises(LogicError):
            game.reveal()
        with self.assertRaises(AttributeError):
            game.length = 10
        with patch("code_duel.engine.choose", return_value="1234"):
            game.begin_round("9999")
        with self.assertRaises(LogicError):
            game.begin_round("0000")
        self.assertEqual(game.pending, ("9999", "1234"))
        game.finish_round(0)
        self.assertEqual(game.reveal(), "9999")
        new = Game(4)
        self.assertEqual(new.rounds, ())
        self.assertIsNone(new.pending)
        with self.assertRaises(ValueError):
            new.begin_round("１２３４")
        self.assertEqual(new.rounds, ())


class LengthTests(unittest.TestCase):
    def test_every_length_and_difficulty(self):
        for length in range(1, 11):
            for level in Difficulty:
                solver = Solver(length)
                secret = "0" * length
                guess = choose(solver, level, random.Random(4))
                self.assertEqual(len(guess), length)
                solver.observe(guess, score(secret, guess))
                next_guess = choose(solver, level, random.Random(5))
                self.assertTrue(
                    all(score(next_guess, h.guess) == h.feedback for h in solver.history)
                )

    def test_long_contradiction_exact_check(self):
        solver = Solver(10)
        solver.observe("0" * 10, 1)
        guess = solver.candidates[0]
        # It is legal to guess; declaring it all-correct remains consistent.
        solver.observe(guess, 10)
        self.assertEqual(solver.candidates, (guess,))

    def test_constraint_search_proves_empty(self):
        from code_duel.constraints import SearchLimit, candidate_pool

        self.assertEqual(candidate_pool(10, (Clue("0" * 10, 1), Clue("1" * 10, 10))), ())
        with self.assertRaises(SearchLimit):
            candidate_pool(10, (), budget=0)

    def test_invalid_lengths_and_scores(self):
        for length in [0, 11, True, "4"]:
            with self.assertRaises(ValueError):
                Game(length)
        for length in [1, 5, 10]:
            self.assertEqual(score("0" * length, "0" * length), length)
            self.assertEqual(score("0" * length, "1" * length), 0)


if __name__ == "__main__":
    unittest.main()
