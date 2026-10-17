# Exact deadline decision formulation — 17 October 2026

Three independent review tracks challenged the combined plan before a second
implementation pass. The main improvement here is a full-recipe **decision
formulation**, rather than an unrelated smaller factory or an assertion that
more variables necessarily help VeloxQ.

## The exact question

Given the unchanged manufacturing input, **can every terminal operation meet its
own due date, with all operations finished by a declared cap C?** The original
horizon, grid, calendars, machine/worker skills, attendance, metric setups,
transfer lags and assembly dependencies remain unchanged. Every original
operation is mandatory.

Generate all original unary-legal assignments. Remove rows ending after C and
terminal rows ending after their due date. Optional binary support propagation
preserves every schedule that satisfies this query. Each retained operation row
has one bit; there is no makespan register or soft-objective term:

`E = sum_operations (sum_assignments x - 1)^2 + sum_incompatible_pairs x_i*x_j`.

Each incompatible pair of distinct operations is counted once. Every term is a
nonnegative integer. Thus **E=0 iff the decoded original-model schedule satisfies
the full deadline query**. Unit penalties suffice because no soft objective
competes with feasibility. Linear coefficients are -1; quadratic coefficients
are 1 or2. A positive-energy heuristic sample is a failure to find a witness,
never an infeasibility certificate.

This is not a lossless replacement of weighted-tardiness/makespan optimization.
A zero-energy result proves optimal primary tardiness0; it does not generally
prove the smallest makespan. Compare returned schedules using their actual
tardiness, makespan and original objective, rather than comparing energy numbers
between the two formulations.

## Independent check and results

`deadline_reference.py` independently builds raw resource/calendar tables and
optional machine/worker intervals, with explicit terminal due and cap constraints.
It never reads compiler assignment lists or conflict predicates. It returns
True for a checked witness, False only for proven infeasibility, and None for an
unresolved solve. Construction time and solve time are separate. Compiler and
reference independently produce the same query hash.

| Recovery input | Completion cap | Query QUBO variables / couplers | Native reference |
|---|---:|---:|---|
| Heat capacity withdrawn | 900 | 796 / 32,760 | INFEASIBLE |
| Replacement from minute360 | 900 | 818 / 33,817 | Feasible; checked completion855 |
| Replacement from minute360 | 855 | 818 / 33,817 | Feasible; checked completion855 |
| Replacement from minute360 | 854 | 632 / 21,152 | INFEASIBLE |

All use the saved recovery-v2 input. No native-reference plan initializes a
sampler. The reference witness is retained for an energy/decoder audit only.
The four-query compilation/reference campaign took7.416seconds locally. The
cap900 replacement native feasibility reference took0.706seconds including
construction; query compilation took1.428seconds. These are local observations,
not equal-task comparisons to historical cost-optimization solve times.

For the replacement cap900 query, compare818 variables/33,817couplers to the
previous full optimization QUBO's2,499/381,371. The reduction comes from an exact
change to the specified decision question, deadline filtering/support and removal
of the completion register. Do not call it exact compression of every original
soft-objective schedule. Under `s=2x-1`, maximum absolute Ising field/coupling is
51 in the query versus42,698,404 in the original saved optimization Hamiltonian;
unit QUBO coefficients do not imply unit Ising fields. Backend storage/internal
precision and performance remain unverified.

## Verification and practical limits

The tests exhaust every tiny binary state against the independent raw schedule
checker, enumerate all tiny query-feasible assignments to check pruning, and
cross-check native/compiled feasibility with calendars, worker travel, machine
setups and releases. They distinguish preprocessing certificates from memory
guards, UNKNOWN and heuristic nonzero energy. Construction has explicit variable,
pair-count and coupler guards; these are local limits, not scaling claims.
Compiled problems are copied to prevent caller mutation changing their meaning.

```sh
.venv-stage2/bin/python -m unittest discover -s tests/stage2 -p 'test_deadline*.py' -v
.venv-stage2/bin/python -m stage2.deadline_study --output output/NEW-DEADLINE-STUDY
```

Evidence: [source-sealed study](../../../output/deadline-decision-review-v1/report.json).
Implementation: [compiler](../../../stage2/deadline_qubo.py),
[independent native reference](../../../stage2/deadline_reference.py),
[study driver](../../../stage2/deadline_study.py).
All results are known-fixture development evidence, not held-out generalization.
VeloxQ, physical hardware and external compute calls are zero.

Expanded cold binary and one-hot annealing controls have now run on original and
query formulations:40runs/640samples, with no physically valid schedule found at
the declared budgets. A reporting-only audit independently confirms this from
all retained bitstrings. This does not establish native problem hardness or
predict VeloxQ success. See [the review record](STAGE2_REVIEW_PASSES.md).
