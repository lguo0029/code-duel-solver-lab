from dataclasses import dataclass
from enum import Enum


class LogicError(RuntimeError):
    """An inconsistent inference state; never silently recovered."""


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass(frozen=True)
class Clue:
    guess: str
    feedback: int


@dataclass(frozen=True)
class Round:
    number: int
    player_guess: str
    player_score: int
    ai_guess: str
    ai_score: int
    candidates: int


@dataclass(frozen=True)
class DecisionInfo:
    """Measured strategy diagnostics; None means that metric was not evaluated."""

    strategy: str
    seconds: float
    entropy_bits: float | None = None
    worst_bucket: int | None = None
    answer_sample: int = 0
    guess_sample: int = 0
    exact_distribution: bool = False
