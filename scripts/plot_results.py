"""Generate figures from checked-in raw reports; no hand-entered measurements."""

import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(".mpl-cache").resolve()))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLORS = {"easy": "#55a8dd", "medium": "#e9a23b", "hard": "#58b88a"}


def save(fig, name):
    fig.tight_layout()
    fig.savefig(Path("assets") / name, dpi=150)
    plt.close(fig)


def main():
    Path("assets").mkdir(exist_ok=True)
    game = Path("benchmarks/results/exhaustive/report.json")
    if game.exists():
        data = json.loads(game.read_text())
        groups = list(data["groups"].values())
        subtitle = "n=4; all 10,000 secrets per strategy; seed=42"
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(
            [g["difficulty"] for g in groups],
            [g["mean_guesses"] for g in groups],
            color=list(COLORS.values()),
        )
        ax.set(title="Average Guesses by Difficulty\n" + subtitle, ylabel="Mean guesses (rounds)")
        ax.set_ylim(0, 12)
        save(fig, "average-guesses.png")
        fig, ax = plt.subplots(figsize=(7, 4))
        for g in groups:
            hist = g["guess_histogram"]
            ax.plot(
                list(map(int, hist)),
                list(hist.values()),
                marker=".",
                label=g["difficulty"],
                color=COLORS[g["difficulty"]],
            )
        ax.set(
            title="Guess Count Distribution\n" + subtitle,
            xlabel="Guesses (rounds)",
            ylabel="Number of secrets",
        )
        ax.legend()
        save(fig, "guess-distribution.png")
        fig, ax = plt.subplots(figsize=(7, 4))
        for g in groups:
            trace = g["remaining_candidates_by_round"]
            ax.plot(
                list(map(int, trace)),
                list(trace.values()),
                label=g["difficulty"],
                color=COLORS[g["difficulty"]],
            )
        ax.set(
            title="Remaining Candidates by Round\nConditional mean among games reaching each round; seed=42",
            xlabel="Round",
            ylabel="Mean remaining candidates (exact count)",
            yscale="log",
        )
        ax.legend()
        save(fig, "remaining-candidates.png")
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(
            [g["difficulty"] for g in groups],
            [g["average_decision_seconds"] * 1000 for g in groups],
            color=list(COLORS.values()),
        )
        ax.set(
            title="Decision Time by Strategy\n" + subtitle + "; shared decision cache",
            ylabel="Mean wall time (ms per round)",
        )
        save(fig, "decision-time.png")
    else:
        reports = [
            json.loads(p.read_text())
            for p in [
                Path("benchmarks/results/small/report.json"),
                Path("benchmarks/results/large/report.json"),
            ]
        ]
        groups = [g for r in reports for g in r["groups"].values()]
        subtitle = "seed=42; n<=4: up to 1000 secrets; n>=5: 8 stratified secrets"
        for metric, title, ylabel, filename in [
            (
                "average_decision_seconds",
                "Solver Decision Runtime by Code Length",
                "Mean wall time (seconds per round)",
                "solver-runtime.png",
            ),
            (
                "mean_guesses",
                "Guess Count by Code Length",
                "Mean guesses among completed games (rounds)",
                "guesses-by-length.png",
            ),
            (
                "average_validation_seconds",
                "Constraint Validation Time",
                "Mean validation time (seconds per round)",
                "validation-time.png",
            ),
        ]:
            fig, ax = plt.subplots(figsize=(8, 4))
            for level, color in COLORS.items():
                selected = sorted(
                    [g for g in groups if g["difficulty"] == level], key=lambda g: g["length"]
                )
                ax.plot(
                    [g["length"] for g in selected],
                    [g[metric] for g in selected],
                    marker="o",
                    label=level,
                    color=color,
                )
            ax.set(title=title + "\n" + subtitle, xlabel="Code length (digits)", ylabel=ylabel)
            ax.legend()
            save(fig, filename)
        validation = json.loads(Path("benchmarks/results/validation.json").read_text())
        fig, ax = plt.subplots(figsize=(8, 4))
        bottom = [0] * 10
        for status, color in [
            ("consistent", "#58b88a"),
            ("contradictory", "#e9a23b"),
            ("unknown", "#a395ce"),
        ]:
            counts = [
                sum(r["length"] == n and r["status"] == status for r in validation["rows"])
                for n in range(1, 11)
            ]
            ax.bar(range(1, 11), counts, bottom=bottom, label=status, color=color)
            bottom = [a + b for a, b in zip(bottom, counts)]
        ax.set(
            title="Constraint Validation Outcomes\n310 known-oracle cases; seed=19; 10 deliberately exhausted budgets",
            xlabel="Code length (digits)",
            ylabel="Validation cases",
        )
        ax.legend()
        save(fig, "validation-outcomes.png")
        fig, ax = plt.subplots(figsize=(8, 4))
        for level, color in COLORS.items():
            selected = sorted(
                [g for g in groups if g["difficulty"] == level], key=lambda g: g["length"]
            )
            ax.plot(
                [g["length"] for g in selected],
                [g["timeouts"] / g["sample_size"] * 100 for g in selected],
                marker="o",
                color=color,
                label=level,
            )
        ax.set(
            title="Search Completion Limits by Strategy\n" + subtitle,
            xlabel="Code length (digits)",
            ylabel="Unknown / timeout rate (%)",
        )
        ax.legend()
        save(fig, "search-performance.png")


if __name__ == "__main__":
    main()
