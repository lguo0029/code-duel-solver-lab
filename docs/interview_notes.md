# Technical interview notes

## CSP model

The variables x_i are digits. Each feedback adds sum(x_i == g_i) = r.
`constraints.py::solve_constraints` applies bounds consistency: count matches
already forced and matches still possible. If r lies outside those bounds the
branch is impossible; equality with a bound forces or excludes individual values.
Backtracking selects a smallest remaining domain and randomizes digits. State is
copied per branch, avoiding accidental mutation of sibling branches.

## Why enumeration stops at four digits

10^4 strings are feasible; 10^10 are not an appropriate in-memory candidate set.
`rules.py::universe` rejects large lengths. `solver.py` uses exact enumeration for
1–4 and fresh searches from the complete history for 5–10. A sample that omits
the true secret never proves it impossible: it is a proposal pool, not the domain.

## SAT, UNSAT and UNKNOWN

A witness is enough to prove SAT. UNSAT requires exhaustive search with no witness.
The node/time budget can interrupt that proof; such a result is UNKNOWN. The code
returns `ValidationResult`, not a Boolean with ambiguous meaning. A limit after
finding a witness is still SAT, but its sample may be incomplete. `candidate_pool`
raises SearchLimit for UNKNOWN, so an empty tuple cannot silently mean timeout.

## Human-owned secrets and transactional feedback

`engine.py::begin_round` locks both guesses and `finish_round` asks `Solver.observe`
to validate the proposed history. Only a SAT result commits it. Contradiction and
Unknown preserve the pending guess and valid past history, allowing correction
without changing the human's guess or giving the AI a reroll. The human secret is
never an engine field or decision argument. A wrong report that is logically
consistent is unobservable; the UI and README say so explicitly.

## Evaluation

`tests/test_validation.py` cross-checks the bounded solver with complete small
universes and known long-code witnesses/contradictions. `scripts/validate_constraints`
records 310 expected/actual outcomes (seed 19), zero false contradictions and 10
intentionally forced Unknowns. Long-code games are stratified, not exhaustive:
142/144 completed and two reached Unknown. Completed-only means are biased and
must be reported with the missing outcomes. Tracemalloc peaks include oracle
allocations; they are not process RSS.

## Precision, speed and future improvements

Witness attempts, node budget and one-second wall limit trade diversity and
proof effort for latency. Randomized witnesses are biased and cannot be called
uniform answer samples. Entropy estimates can be misleading under that bias.
Current reasoning restarts from all clues rather than reusing an incremental
constraint state. Potential improvements include memoized infeasible states,
incremental CP/SMT backends, explicit unsat cores and historical-feedback editing.
A different backend would require license/dependency review and identical tri-state
contract tests. No ML training or LLM integration is needed to solve this CSP.
