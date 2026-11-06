# Stratified benchmark method

| Digits | Secrets / strategy | Easy mean | Medium mean | Hard mean | Unknown / games |
|---|---:|---:|---:|---:|---:|
| 1 | 10 | 5.500 | 5.500 | 5.500 | 0 / 30 |
| 2 | 100 | 7.600 | 7.600 | 7.600 | 0 / 300 |
| 3 | 1000 | 9.017 | 8.979 | 8.978 | 0 / 3000 |
| 4 | 1000 | 10.271 | 10.040 | 10.019 | 0 / 3000 |
| 5 | 8 | 10.000 | 12.125 | 11.375 | 0 / 24 |
| 6 | 8 | 13.250 | 12.125 | 12.125 | 0 / 24 |
| 7 | 8 | 15.125 | 14.125 | 14.250 | 0 / 24 |
| 8 | 8 | 14.375 | 14.625 | 14.250 | 0 / 24 |
| 9 | 8 | 16.429 | 15.750 | 15.750 | 1 / 24 |
| 10 | 8 | 16.875 | 16.875 | 18.000 | 1 / 24 |

Lengths are never pooled into a single efficiency ranking. For n<=3 the complete
space is tested; n=4 samples 1000 secrets. Each long-code stratum contains eight
secrets including zero, repeated, leading-zero and pseudorandom patterns.
The two real UNKNOWN cases are not misclassified as contradictions. Completed-only
means have survivorship bias and are labeled accordingly. Node and wall budgets
are explicit; reruns can differ in timeout rate under a different CPU load.

Validation accuracy is measured only against enumerated or constructive oracles.
The 10 forced UNKNOWN cases test semantics, not a natural timeout rate. Python
traced allocations include instrumentation and the oracle; this is not a resident
memory estimate. See validation.json for every expected and observed outcome.

No all-ten-digit brute force was attempted. The four-digit --all mode remains
available independently. These experiments establish exercised invariants and
limits, not universal feasibility or unbiased sample distributions.
