"""Reproducible headless experiments; secrets stay outside decision interfaces."""

import argparse
import csv
import gzip
import json
import math
import platform
import random
import statistics
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from .constraints import SearchLimit
from .models import Difficulty
from .rules import score, validate
from .solver import Solver
from .strategies import DEFAULT_CONFIG, choose

PROJECT = "code-duel-solver-lab"


@lru_cache(maxsize=40000)
def decision(difficulty: str, history: tuple, seed: int, length: int = 4):
    solver = Solver(length)
    for clue in history:
        solver.observe(clue.guess, clue.feedback)
    guess = choose(solver, difficulty, random.Random(f"{seed}:{history}"))
    return guess, solver.last_decision


def simulate(secret: str, difficulty: str = "hard", seed: int = 42, max_rounds: int = 200) -> dict:
    """Generate truthful feedback externally; never pass the secret into choose()."""
    length = len(secret)
    validate(secret, length)
    solver = Solver(length)
    records = []
    start = time.perf_counter()
    for _ in range(max_rounds):
        decision_start = time.perf_counter()
        if length <= 4:
            guess, info = decision(Difficulty(difficulty).value, solver.history, seed, length)
        else:
            guess = choose(solver, difficulty, random.Random(f"{seed}:{solver.history}"))
            info = solver.last_decision
        decision_seconds = time.perf_counter() - decision_start
        solver.check(guess)
        feedback = score(secret, guess)
        validation_start = time.perf_counter()
        result = solver.observe(guess, feedback)
        records.append(
            dict(
                guess=guess,
                feedback=feedback,
                candidates=len(solver.candidates),
                count_exact=length <= 4,
                decision_seconds=decision_seconds,
                validation_seconds=time.perf_counter() - validation_start,
                strategy_seconds=info.seconds,
                solver_nodes=result.nodes,
            )
        )
        if feedback == length:
            return dict(rounds=len(records), history=records, seconds=time.perf_counter() - start)
    raise RuntimeError("Round limit reached without convergence.")


def summarize(rows: list[dict]) -> dict:
    values = sorted(r["rounds"] for r in rows if r["status"] == "completed")
    total_rounds = sum(values)
    return dict(
        completed=len(values),
        failed_games=sum(r["status"] == "failed" for r in rows),
        timeouts=sum(r["status"] == "unknown" for r in rows),
        mean_guesses=statistics.mean(values) if values else None,
        median_guesses=statistics.median(values) if values else None,
        p95_guesses=values[math.ceil(0.95 * len(values)) - 1] if values else None,
        worst_case_guesses=max(values) if values else None,
        average_decision_seconds=sum(r.get("decision_seconds", 0) for r in rows)
        / max(total_rounds, 1),
        average_validation_seconds=sum(r.get("validation_seconds", 0) for r in rows)
        / max(total_rounds, 1),
        guess_histogram={str(n): values.count(n) for n in sorted(set(values))},
    )


def benchmark(
    count: int = 1000,
    seeds: tuple[int, ...] = (42,),
    lengths: tuple[int, ...] = (4,),
    output: str = "benchmarks/results",
) -> dict:
    """Batch experiments, reporting errors rather than silently dropping failures."""
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    rows = []
    groups = {}
    traces = {}
    invalid = 0
    started = time.perf_counter()
    for length in lengths:
        for seed in seeds:
            rng = random.Random(seed)
            if length <= 4:
                from .rules import universe

                codes = rng.sample(universe(length), min(count, 10**length))
            else:
                codes = list(
                    dict.fromkeys(
                        ["0" * length, "7" * length, "0" + "123456789"[: length - 1]]
                        + [
                            "".join(rng.choice("0123456789") for _ in range(length))
                            for _ in range(count)
                        ]
                    )
                )[:count]
            for difficulty in Difficulty:
                subset = []
                trajectory = {}
                for secret in codes:
                    row = dict(
                        length=length,
                        seed=seed,
                        difficulty=difficulty.value,
                        secret=secret,
                        status="completed",
                        rounds=0,
                    )
                    try:
                        result = simulate(secret, difficulty.value, seed)
                        row.update(
                            rounds=result["rounds"],
                            runtime_seconds=result["seconds"],
                            decision_seconds=sum(h["decision_seconds"] for h in result["history"]),
                            validation_seconds=sum(
                                h["validation_seconds"] for h in result["history"]
                            ),
                        )
                        for n, h in enumerate(result["history"], 1):
                            trajectory.setdefault(n, []).append(h["candidates"])
                        traces.setdefault(f"{length}:{seed}:{difficulty.value}", result["history"])
                    except SearchLimit as exc:
                        row.update(status="unknown", error=str(exc))
                    except Exception as exc:
                        invalid += int("guess" in str(exc).lower())
                        row.update(status="failed", error=f"{type(exc).__name__}: {exc}")
                    rows.append(row)
                    subset.append(row)
                key = f"{length}:{seed}:{difficulty.value}"
                groups[key] = dict(
                    length=length,
                    seed=seed,
                    difficulty=difficulty.value,
                    sample_size=len(codes),
                    **summarize(subset),
                    remaining_candidates_by_round={
                        str(k): statistics.mean(v) for k, v in trajectory.items()
                    },
                )
                print(
                    key,
                    groups[key]["mean_guesses"],
                    "completed",
                    groups[key]["completed"],
                    "unknown",
                    groups[key]["timeouts"],
                    flush=True,
                )
    report = dict(
        project=PROJECT,
        version="0.1.0",
        date=datetime.now(timezone.utc).isoformat(),
        environment=dict(python=sys.version, platform=platform.platform()),
        parameters=asdict(DEFAULT_CONFIG),
        seeds=seeds,
        lengths=lengths,
        requested_count=count,
        total_runtime_seconds=time.perf_counter() - started,
        invalid_guesses=invalid,
        groups=groups,
        representative_traces=traces,
        timing_note="Decision-tree cache shared for n<=4; wall decision time includes cache lookup and history validation. These are not cold-start timings. Large-n strategy uses samples, not full model counts.",
    )
    (destination / "report.json").write_text(json.dumps(report, indent=2))
    fields = [
        "length",
        "seed",
        "difficulty",
        "secret",
        "status",
        "rounds",
        "runtime_seconds",
        "decision_seconds",
        "validation_seconds",
        "error",
    ]
    with gzip.open(destination / "games.csv.gz", "wt", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--all", action="store_true", help="All 10000 four-digit secrets")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42])
    parser.add_argument("--lengths", type=int, nargs="+", default=[4])
    parser.add_argument("--output", default="benchmarks/results")
    parser.add_argument("--secret")
    parser.add_argument("--difficulty", choices=[d.value for d in Difficulty], default="hard")
    args = parser.parse_args()
    if args.secret is not None:
        print(json.dumps(simulate(args.secret, args.difficulty, args.seeds[0]), indent=2))
        return
    if args.count < 1 or any(n < 1 or n > 10 for n in args.lengths):
        parser.error("Invalid count or length.")
    if PROJECT == "code-duel-game" and (
        args.lengths != [4] or (args.secret and len(args.secret) != 4)
    ):
        parser.error("The game benchmark uses four-digit codes only.")
    report = benchmark(
        10000 if args.all else args.count,
        tuple(args.seeds),
        (4,) if args.all else tuple(args.lengths),
        args.output,
    )
    if report["invalid_guesses"] or any(g["failed_games"] for g in report["groups"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
