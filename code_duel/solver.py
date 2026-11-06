"""Transactional feedback validation, without any human-secret reference."""

import time
from functools import lru_cache

from .constraints import (
    ConsistencyStatus,
    Contradiction,
    SearchLimit,
    ValidationResult,
    solve_constraints,
)
from .models import Clue, LogicError
from .rules import score, universe, validate, validate_length


@lru_cache(maxsize=10000)
def filter_history(history: tuple[Clue, ...], length: int = 4) -> tuple[str, ...]:
    """Exact enumeration is only available for lengths one to four."""
    if not history:
        return universe(length)
    previous = filter_history(history[:-1], length)
    return tuple(c for c in previous if all(score(c, h.guess) == h.feedback for h in history))


class Solver:
    """State contains public feedback and feasible candidates only."""

    def __init__(self, length: int = 4):
        self.length = validate_length(length)
        self._history: tuple[Clue, ...] = ()
        self.last_validation: ValidationResult | None = None
        if length <= 4:
            self._candidates = filter_history((), length)
        else:
            result = solve_constraints(length, ())
            if result.status != ConsistencyStatus.CONSISTENT:
                raise SearchLimit("Validation timed out: no contradiction has been proved.")
            self._candidates = result.witnesses

    @property
    def history(self) -> tuple[Clue, ...]:
        return self._history

    @property
    def candidates(self) -> tuple[str, ...]:
        return self._candidates

    @property
    def count_label(self) -> str:
        return (
            str(len(self.candidates))
            if self.length <= 4
            else f">= {len(self.candidates)} (samples; total not counted)"
        )

    def check(self, guess: str) -> None:
        validate(guess, self.length)
        if not self.candidates:
            raise LogicError("No valid candidates remain.")
        if (self.length <= 4 and guess not in self.candidates) or any(
            h.guess == guess for h in self.history
        ):
            raise LogicError("AI guess is excluded or repeated.")
        if not all(score(guess, h.guess) == h.feedback for h in self.history):
            raise LogicError("AI guess violates feedback history.")

    def observe(self, guess: str, feedback: int) -> ValidationResult:
        """Commit only consistent feedback; keep history intact on UNSAT/UNKNOWN."""
        self.check(guess)
        if type(feedback) is not int or not 0 <= feedback <= self.length:
            raise ValueError(f"Expected an integer feedback from 0 to {self.length}.")
        history = self.history + (Clue(guess, feedback),)
        if self.length <= 4:
            start = time.perf_counter()
            candidates = filter_history(history, self.length)
            status = ConsistencyStatus.CONSISTENT if candidates else ConsistencyStatus.CONTRADICTORY
            result = ValidationResult(
                status, candidates, 0, time.perf_counter() - start, "exact enumeration"
            )
        else:
            result = solve_constraints(self.length, history)
        self.last_validation = result
        if result.status == ConsistencyStatus.UNKNOWN:
            raise SearchLimit("Validation timed out: no contradiction has been proved.")
        if result.status == ConsistencyStatus.CONTRADICTORY:
            raise Contradiction(
                "Feedback contradicts the current or earlier clues; this round was not saved."
            )
        self._history, self._candidates = history, result.witnesses
        return result
