# v0.1.0 — portfolio prerelease

- Preserved and refactored 1–10-digit manual-feedback solver lab.
- English / Simplified Chinese setup, gameplay, errors and results.
- Legal candidate-only random, heuristic and entropy/Minimax strategies.
- Explicit Consistent / Contradictory / Unknown validation and correction of pending feedback.
- Real benchmark reports and Matplotlib charts, tests, packaging and CI definitions.
- Local macOS Python 3.14.6 + Tk 8.6 validation; 26 tests passed and real-window integration passed.

Install Python 3.11+ with Tk, then `pip install -e .` and `python main.py`.
Development commands are in the README. Linux/Windows validation depends on the
actual Actions run; do not infer it from local results.

Limitations: native UI screenshots could not be captured. Long-code samples are biased, not exact model counts; two of 144 long-code benchmark games returned Unknown. Consistent false human feedback is unobservable.
