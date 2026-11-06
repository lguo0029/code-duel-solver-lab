# Project pitch

## 30 seconds

I built CodeDuel Solver Lab to study how a program can reason from human feedback without knowing the answer. It supports one to ten digits and distinguishes a valid explanation, a proved contradiction and an unfinished search. The key lesson was that a computation limit is not evidence of a contradiction.

## 90 seconds

The human keeps a secret outside the program, and each feedback report adds an equality constraint on matching positions. Up to four digits I can enumerate the feasible space. At ten digits the space is ten billion combinations, so I use finite-domain propagation and bounded backtracking to find witnesses. I made the validation contract explicit: a witness proves consistency, exhaustive failure proves contradiction, and an interrupted search is Unknown. Invalid or unverified feedback does not change committed history; the player can correct the pending report. I tested all lengths, cross-checked small problems against enumeration, and used known long-code witnesses and contradictions. The 310-case validation experiment matched every expected outcome. A separate long-code game experiment completed 142 of 144 games and recorded two Unknowns. I deliberately show those limits because biased sampling and load-dependent time budgets affect what the solver can claim.

## Three-minute technical explanation

The most useful way to explain this project is through evidence and state transitions. Each digit is a variable with a ten-value domain. A clue counts forced matches and still-possible matches. A branch is inconsistent if the reported count lies outside those bounds. When a bound equals the target, propagation can force or eliminate values. I then branch on a smallest remaining domain. This avoids generating the complete ten-digit universe, but it does not remove worst-case combinatorial complexity.

A central architectural choice is the result type. Returning only a Boolean would hide whether a failed search proved anything. My ValidationResult carries a status, witnesses, node count, time and termination reason. One witness establishes satisfiability even if a later sampling attempt reaches the limit. Without a witness, hitting the budget means Unknown. Only exhausted infeasibility is a contradiction. The solver records the proposed history separately, and the engine only commits it after a consistent result. That preserves both guesses while the human corrects feedback.

The AI policies consume feasible candidates only. For larger lengths those are biased witness samples; I label them as samples and never pretend their count is the entire remaining answer space. Entropy and Minimax therefore describe the sampled distribution, not a global optimum. I also never know the human secret, so a mistaken but self-consistent report cannot be detected.

For evidence, I used enumerative oracles on small cases, constructed long-code witnesses and contradictions, explicit zero-budget tests, GUI flows and stratified games. Two long games reached Unknown; hiding them would bias the story. The natural next steps are incremental solving, better sampling and unsat-core explanations, but each must preserve the same tested three-state contract.

## Three hardest problems

1. Representing a ten-billion-code domain without materializing it.
2. Preserving the semantic difference between UNSAT and resource exhaustion.
3. Rejecting a human report transactionally while retaining the locked round.

## Representative debugging case

When timing diagnostics were added to simulation histories, the old reproducibility
test compared complete dictionaries, including wall-clock times, and failed. I
fixed the test to compare semantic records (guess, feedback, candidates), leaving
runtime measurements explicitly nondeterministic. This was a test-contract bug,
not evidence of nondeterministic game rules. The failing run was not reported as
a passing result; the final suites were rerun after the correction.

## Optimization evidence

The existing implementation already cached shared-history decisions and avoided
initial distribution evaluation by symmetry. I preserved those mechanisms and
remeasured them rather than inventing an unavailable before/after comparison.
Hard still has a larger sampling cost. There is no justified quantified speedup
against an uncached baseline in this release.

## Next steps

Incremental constraint state, unsat-core hints, earlier-feedback editing and broader randomized stress corpora with independent runs.
