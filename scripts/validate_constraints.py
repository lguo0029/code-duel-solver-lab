"""Cross-check feasibility against enumeration and known witnesses/proofs."""

import json
import random
import time
import tracemalloc
from pathlib import Path

from code_duel.constraints import solve_constraints
from code_duel.models import Clue
from code_duel.rules import score, universe


def main() -> None:
    rng = random.Random(19)
    rows = []
    tracemalloc.start()
    for length in range(1, 11):
        for case in range(30):
            secret = "".join(rng.choice("0123456789") for _ in range(length))
            guesses = ["".join(rng.choice("0123456789") for _ in range(length)) for _ in range(4)]
            clues = tuple(Clue(g, score(secret, g)) for g in guesses)
            expected = "consistent"
            if case % 3 == 1:
                clues = (Clue("0" * length, 1), Clue("1" * length, length))
                expected = "contradictory"
            elif case % 3 == 2 and length <= 4:
                clues = tuple(Clue(g, rng.randrange(length + 1)) for g in guesses)
                expected = (
                    "consistent"
                    if any(
                        all(score(c, h.guess) == h.feedback for h in clues)
                        for c in universe(length)
                    )
                    else "contradictory"
                )
            started = time.perf_counter()
            result = solve_constraints(length, clues, cap=1, timeout=1.0)
            rows.append(
                dict(
                    length=length,
                    case=case,
                    expected=expected,
                    status=result.status.value,
                    seconds=time.perf_counter() - started,
                    nodes=result.nodes,
                )
            )
        # A deliberately exhausted budget must be UNKNOWN, even for SAT input.
        result = solve_constraints(length, (), cap=1, budget=0)
        rows.append(
            dict(
                length=length,
                case="forced_budget",
                expected="unknown",
                status=result.status.value,
                seconds=result.seconds,
                nodes=result.nodes,
            )
        )
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    report = dict(
        seed=19,
        cases=len(rows),
        correct=sum(r["expected"] == r["status"] for r in rows),
        false_contradictions=sum(
            r["expected"] == "consistent" and r["status"] == "contradictory" for r in rows
        ),
        unknown_count=sum(r["status"] == "unknown" for r in rows),
        forced_unknown_count=10,
        python_peak_allocated_bytes=peak,
        memory_note="tracemalloc peak includes enumeration oracle and stored rows; not OS RSS or only solver memory.",
        validation_timing_note="Measured with tracemalloc enabled; includes instrumentation overhead.",
        rows=rows,
    )
    destination = Path("benchmarks/results/validation.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2))
    print({k: v for k, v in report.items() if k != "rows"})
    if report["false_contradictions"] or report["correct"] != len(rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
