"""Constraint propagation and bounded backtracking with explicit tri-state results."""

import random
import time
from dataclasses import dataclass
from enum import Enum

from .models import Clue, LogicError
from .rules import validate, validate_length


class ConsistencyStatus(str, Enum):
    CONSISTENT = "consistent"
    CONTRADICTORY = "contradictory"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ValidationResult:
    status: ConsistencyStatus
    witnesses: tuple[str, ...]
    nodes: int
    seconds: float
    reason: str


class SearchLimit(LogicError):
    """No witness and no proof: preserve the pending feedback for correction."""


class Contradiction(LogicError):
    """An exhaustive feasibility search proved that the history is unsatisfiable."""


def solve_constraints(
    length: int,
    history: tuple[Clue, ...],
    *,
    cap: int = 180,
    budget: int = 150000,
    timeout: float = 1.0,
) -> ValidationResult:
    """Return SAT with witnesses, UNSAT with a proof by exhaustion, or UNKNOWN.

    Witnesses are randomized feasible samples, never an exact model count.
    A budget reached after a witness is found is still SAT, not UNKNOWN.
    """
    validate_length(length)
    if cap < 1 or budget < 0 or timeout < 0:
        raise ValueError("Invalid search budget.")
    for clue in history:
        validate(clue.guess, length)
        if type(clue.feedback) is not int or not 0 <= clue.feedback <= length:
            raise ValueError("Feedback is out of range.")
    start = time.perf_counter()
    rng = random.Random(repr(history))
    nodes = 0

    def find(domains: list[set[str]]) -> str | None:
        nonlocal nodes
        nodes += 1
        if nodes > budget or time.perf_counter() - start >= timeout:
            raise SearchLimit("Validation timed out: no contradiction has been proved.")
        domains = [set(d) for d in domains]
        changed = True
        while changed:
            changed = False
            for clue in history:
                forced = [i for i, d in enumerate(domains) if d == {clue.guess[i]}]
                possible = [i for i, d in enumerate(domains) if clue.guess[i] in d]
                if not len(forced) <= clue.feedback <= len(possible):
                    return None
                if len(forced) == clue.feedback:
                    for i in possible:
                        if i not in forced:
                            domains[i].remove(clue.guess[i])
                            changed = True
                elif len(possible) == clue.feedback:
                    for i in possible:
                        if len(domains[i]) > 1:
                            domains[i] = {clue.guess[i]}
                            changed = True
            if any(not d for d in domains):
                return None
        undecided = [i for i, d in enumerate(domains) if len(d) > 1]
        if not undecided:
            return "".join(next(iter(d)) for d in domains)
        size = min(len(domains[i]) for i in undecided)
        i = rng.choice([i for i in undecided if len(domains[i]) == size])
        digits = sorted(domains[i])
        rng.shuffle(digits)
        for digit in digits:
            branch = list(domains)
            branch[i] = {digit}
            result = find(branch)
            if result is not None:
                return result
        return None

    found: set[str] = set()
    reason = "sample budget"
    for _ in range(cap):
        try:
            answer = find([set("0123456789") for _ in range(length)])
        except SearchLimit:
            reason = "resource budget"
            break
        if answer is None:
            return ValidationResult(
                ConsistencyStatus.CONTRADICTORY,
                (),
                nodes,
                time.perf_counter() - start,
                "exhaustive infeasibility proof",
            )
        found.add(answer)
        if any(h.feedback == length for h in history):
            reason = "fully specified witness"
            break
    status = ConsistencyStatus.CONSISTENT if found else ConsistencyStatus.UNKNOWN
    return ValidationResult(
        status, tuple(sorted(found)), nodes, time.perf_counter() - start, reason
    )


def candidate_pool(
    length: int,
    history: tuple[Clue, ...],
    cap: int = 180,
    budget: int = 150000,
    timeout: float = 1.0,
) -> tuple[str, ...]:
    """Compatibility wrapper; UNKNOWN cannot be mistaken for an empty result."""
    result = solve_constraints(length, history, cap=cap, budget=budget, timeout=timeout)
    if result.status == ConsistencyStatus.UNKNOWN:
        raise SearchLimit("Validation timed out: no contradiction has been proved.")
    return result.witnesses
