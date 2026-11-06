import random

from .models import DecisionInfo, Difficulty, LogicError, Round
from .rules import score, validate, validate_length
from .solver import Solver
from .strategies import choose


class Game:
    """Human keeps their secret offline. Feedback is checked before committing."""

    def __init__(
        self,
        length: int = 4,
        difficulty: str = "medium",
        *,
        seed: int | None = None,
        ai_secret: str | None = None,
    ):
        self.__length = validate_length(length)
        self.__rng = random.Random(seed)
        self.__ai_secret = (
            validate(ai_secret, length)
            if ai_secret is not None
            else "".join(self.__rng.choice("0123456789") for _ in range(length))
        )
        self.__difficulty = Difficulty(difficulty)
        self.__solver = Solver(length)
        self.__rounds = ()
        self.__outcome = None
        self.__pending = None

    @property
    def length(self):
        return self.__length

    @property
    def difficulty(self):
        return self.__difficulty

    @property
    def rounds(self):
        return self.__rounds

    @property
    def outcome(self):
        return self.__outcome

    @property
    def candidate_count(self):
        return len(self.__solver.candidates)

    @property
    def candidate_label(self):
        return self.__solver.count_label

    @property
    def pending(self):
        return self.__pending

    @property
    def decision(self) -> DecisionInfo | None:
        return getattr(self.__solver, "last_decision", None)

    @property
    def validation(self):
        return self.__solver.last_validation

    def begin_round(self, player_guess: str) -> str:
        if self.outcome is not None:
            raise LogicError("The game has ended.")
        if self.pending is not None:
            raise LogicError("Confirm the pending feedback first.")
        validate(player_guess, self.length)
        ai_guess = choose(self.__solver, self.difficulty, self.__rng)
        self.__solver.check(ai_guess)
        self.__pending = (player_guess, ai_guess)
        return ai_guess

    def finish_round(self, feedback: int) -> Round:
        if self.outcome is not None or self.pending is None:
            raise LogicError("No round is awaiting feedback.")
        player_guess, ai_guess = self.pending
        self.__solver.observe(ai_guess, feedback)
        player_score = score(self.__ai_secret, player_guess)
        record = Round(
            len(self.rounds) + 1,
            player_guess,
            player_score,
            ai_guess,
            feedback,
            self.candidate_count,
        )
        self.__rounds += (record,)
        self.__pending = None
        if player_score == feedback == self.length:
            self.__outcome = "draw"
        elif player_score == self.length:
            self.__outcome = "player"
        elif feedback == self.length:
            self.__outcome = "ai"
        return record

    def reveal(self) -> str:
        if self.outcome is None:
            raise LogicError("The AI secret is hidden until the game ends.")
        return self.__ai_secret
