import math
import random
import time
from dataclasses import dataclass

from .models import DecisionInfo, Difficulty, LogicError
from .rules import score
from .solver import Solver


@dataclass(frozen=True)
class StrategyConfig:
    medium_guesses: int = 50
    medium_answers: int = 70
    medium_tolerance: float = 0.08
    hard_guesses: int = 500
    hard_answers: int = 1500
    exact_threshold: int = 250
    entropy_tolerance: float = 0.02


DEFAULT_CONFIG = StrategyConfig()


def choose(
    solver: Solver,
    difficulty: Difficulty | str,
    rng: random.Random | None = None,
    config: StrategyConfig = DEFAULT_CONFIG,
) -> str:
    """Select only legal candidates; diagnostics describe measured distributions."""
    start = time.perf_counter()
    info = {}
    rng = rng or random.Random()
    difficulty = Difficulty(difficulty)
    candidates = solver.candidates
    available = [c for c in candidates if all(h.guess != c for h in solver.history)]
    if not available:
        raise LogicError("No unguessed valid candidates remain.")
    # With the unconstrained full universe, every guess has exactly the same
    # feedback distribution (independent per-position digit relabeling).
    if (
        len(available) == 1
        or difficulty == Difficulty.EASY
        or (not solver.history and len(candidates) == 10**solver.length)
    ):
        result = rng.choice(available)
    else:
        hard = difficulty == Difficulty.HARD
        exact = hard and len(candidates) <= config.exact_threshold
        ng = config.hard_guesses if hard else config.medium_guesses
        na = config.hard_answers if hard else config.medium_answers
        guesses = available if exact or len(available) <= ng else rng.sample(available, ng)
        answers = candidates if exact or len(candidates) <= na else rng.sample(candidates, na)
        evaluations = []
        for guess in guesses:
            bins = [0] * (solver.length + 1)
            for answer in answers:
                bins[score(answer, guess)] += 1
            if hard:
                entropy = -sum((n / len(answers)) * math.log2(n / len(answers)) for n in bins if n)
                evaluations.append((guess, entropy, max(bins)))
            else:
                expected = sum(n * n for n in bins) / len(answers)
                evaluations.append((guess, expected, max(bins)))
        if hard:
            best = max(e[1] for e in evaluations)
            near = [e for e in evaluations if e[1] >= best - config.entropy_tolerance]
            worst = min(e[2] for e in near)
            result = rng.choice([e[0] for e in near if e[2] == worst])
        else:
            best = min(e[1] for e in evaluations)
            result = rng.choice(
                [e[0] for e in evaluations if e[1] <= best * (1 + config.medium_tolerance)]
            )
    if "evaluations" in locals():
        selected = next(e for e in evaluations if e[0] == result)
        info = dict(
            entropy_bits=selected[1] if hard else None,
            worst_bucket=selected[2],
            answer_sample=len(answers),
            guess_sample=len(guesses),
            exact_distribution=(solver.length <= 4 and len(answers) == len(candidates)),
        )
    solver.check(result)
    solver.last_decision = DecisionInfo(difficulty.value, time.perf_counter() - start, **info)
    return result
