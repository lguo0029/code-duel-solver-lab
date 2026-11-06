"""Shared positional scoring, preserving leading zeros."""

from functools import lru_cache
from itertools import product


def validate_length(length: int) -> int:
    if type(length) is not int or not 1 <= length <= 10:
        raise ValueError("invalid_length")
    return length


def validate(code: str, length: int = 4) -> str:
    validate_length(length)
    if (
        not isinstance(code, str)
        or len(code) != length
        or not code.isascii()
        or not code.isdecimal()
    ):
        raise ValueError(f"Expected exactly {length} ASCII digits (0-9).")
    return code


@lru_cache(maxsize=4)
def universe(length: int) -> tuple[str, ...]:
    validate_length(length)
    if length > 4:
        raise ValueError("Long codes require constraint search.")
    return tuple("".join(p) for p in product("0123456789", repeat=length))


ALL_CODES = universe(4)


def score(secret: str, guess: str) -> int:
    if not isinstance(secret, str):
        raise ValueError("Codes must be strings.")
    validate(secret, len(secret))
    validate(guess, len(secret))
    return sum(a == b for a, b in zip(secret, guess))
