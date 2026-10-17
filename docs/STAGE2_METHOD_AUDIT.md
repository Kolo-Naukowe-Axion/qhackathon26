# Stage 2 method and requirements audit

Audited 2026-10-16 against the local eight-page challenge PDF, the complete local
Zhang et al. paper, and the primary sources linked below. This records the method
actually implemented in `stage2/qubo.py`; factory integration and experimental
claims require their own saved results. No autoresearch workflow is used.

## What the challenge actually requires

The challenge's §5 permits an original manufacturing/scheduling extension; its
examples are optional. §14 explicitly permits extending or changing the Stage 2
JSON schema. Synthetic factories, multiple routes, integer quarter-hour ticks,
resource modes and stochastic disruptions are legitimate disclosed modeling
choices. The baseline's fixed route and integer-hour output contract still apply
to the two separate Stage 1 files. Do not silently replace their data.

The mandatory quantum-hardware-or-simulator requirement is specifically attached
to Instance A in §4.1. Instance B permits any classical, hybrid or quantum QUBO
solver (§4.2). The extension should formulate and solve a substantive scheduling
decision as QUBO, but §5 does not require executing the full extended factory on a
physical quantum processor. A small QPU demonstration is useful evidence only
when its returned samples actually affect a verified factory decision. Repeating
a classical result under a quantum label would not satisfy this requirement.

The most consequential §5 expectations are:

- Reduction, method comparisons and scaling should concern one integrated
  extended model, rather than independent sketches around the 3×3 baseline.
- Results need a classical reference for the **same model**. A fast solve of a
  factory with transport, rework or energy removed is not a valid comparator for
  one that retains those mechanisms.
- Report the cost of each added constraint in the naive encoding and ours.
  Count auxiliary bits and couplers as well as decision bits. State the horizon,
  discretization and candidate-domain assumptions behind every count.
- If a reduced formulation can lose an optimum, report that loss. A restricted
  candidate-pool optimum cannot establish the full factory optimum. Where the
  latter is unknown, explicitly report **global optimality gap unknown** and
  provide exact tiny full-model cases, exact frozen-boundary cases, and matched
  full-model classical incumbents. This is useful evidence, not a proof that the
  entire unrestricted model has been optimized globally.
- Still report the smallest correct baseline 3×3 QUBO separately. Rich extensions
  do not waive Stage 1 eligibility or the comparison count.

§§6–12 additionally require public MIT code, development log, precise project
design, README/run instructions and AI disclosure, both official baseline JSON
files, a video of at most five minutes, and a three-minute live presentation.
Neither visual polish nor a large mechanism count substitutes for these items.
VeloxQ integration is relevant to its separate prize, but the user's existing
hold on all VeloxQ calls remains in force.

## Architecture supported by the literature

[Zhang, Lo Bianco and Beck (ICAPS 2022)](https://ojs.aaai.org/index.php/ICAPS/article/view/19826)
is an architectural precedent for QUBO-guided large-neighborhood search, not a
solver for this complete factory. Their single-machine rank models guide a
multi-machine CP repair. The paper explicitly distinguishes a polynomial plain
assignment subproblem from assignment with conflicts, and notes that independently
combining machine orders can introduce cycles (pp.406–408). Their Digital Annealer
is classical specialized hardware. Its support for constraints outside the QUBO
and excluded communication time must not be copied into a purported pure-QUBO,
end-to-end timing comparison (p.409).

[Pichugina, Tan and Beck (2024), §5.2](https://arxiv.org/html/2404.03610v1)
supports compact valid penalties for specific constraint structures. It does not
permit replacing every inequality by a quadratic in the original variables.
For pairwise order bits, a directed triangle violation can be penalized with
`x_ij*x_jk + x_ik - x_ij*x_ik - x_ik*x_jk`; transitive tournament orders need
`n(n-1)/2` bits. That represents an order, not arbitrary timing, blocking, BOM
consumption, transport or battery dynamics. Our implemented selector instead
uses concrete candidate actions and explicit conflicts/capacity rows.

[Wu et al. (NeurIPS 2021)](https://papers.nips.cc/paper/2021/hash/fc9e62695def29ccdb9eb3fed5b4c8c8-Abstract.html)
provides precedent for learning which variables to release while a conventional
solver repairs the neighborhood. Its evidence concerns integer programming
benchmarks, not our simulator. Reusing this division of labor can make RL useful
without asking a policy to invent every physical action. It does not establish
that pretrained weights from a different scheduling model transfer here.

For this deadline, the defensible progression is: executable physical world;
independent trace checker; fixed heuristic and exact tiny/local references;
candidate-pool QUBO solver integrated into real schedules; equal-budget scaling;
then learning which decisions/neighborhoods merit additional optimization. Real
QPU access is not on that dependency path.

## Exact local action-selection formulation

Input candidate `i` has ID, finite real reward `w_i`, and nonnegative **integer**
resource demands `a_ri`. A binary `x_i` selects it. A conflict edge excludes two
actions sharing an exclusive worker, tool, machine, unit or route reservation.
An upper capacity row limits a cumulative resource. Every candidate must already
be individually legal in the current physical boundary state.

The constrained problem is

```
maximize  sum_i w_i x_i
subject to x_i + x_j <= 1              for each conflict edge (i,j)
           sum_i a_ri x_i <= C_r       for each resource r
           x_i in {0,1}.
```

The QUBO minimizes

```
E(x,s) = -sum_i w_i x_i
       + P sum_(i,j in edges) x_i x_j
       + P sum_r (sum_i a_ri x_i + sum_k b_rk s_rk - C_r)^2.
```

The bounded binary slack weights cover **every** integer from zero to `C_r` and
sum exactly to `C_r`. Their count is `ceil(log2(C_r+1))` for a general row, with
zero bits at zero capacity. Binary squares are folded into diagonal coefficients;
off-diagonal coefficients are stored once, never doubled by convention.

Three exact compact transformations are implemented before adding slack:

- A row whose total demand over all candidates is at most capacity is redundant.
- Zero capacity uses `P sum_{i:a_ri>0} x_i`, with no slack.
- Unit capacity with unit positive demands uses pairwise exclusion terms, with no
  slack. This covers exclusive machines/workers/tools when represented as rows.

The API rejects missing capacities, negative/noninteger demands, duplicate IDs,
unknown conflict endpoints, self-conflicts, nonfinite rewards and inadequate
penalties. Physical fractional kW must be converted to exact integer units; silent
truncation invalidates both feasibility and the following proof.

Choose `P > W+`, where `W+ = sum_i max(w_i,0)`. The empty action set is feasible
and has a zero-energy slack extension. Any infeasible core set violates a conflict
or an integer capacity, so every extension has penalty at least `P`. Its reward
term is bounded below by `-W+`; hence its total energy is strictly positive. Every
feasible core set has a zero-penalty slack extension with energy equal to negative
reward. Thus every global minimum is feasible and maximizes reward in this pool.
`P = W+ + 1` is the implemented sufficient bound. It is conservative and can make
annealing harder; a sound bound is not a performance guarantee.

The conflict graph is substantive: two individually legal actions may jointly
compete for several resources. Even with no capacity rows the model contains
weighted independent set. For example, a reward-10 action conflicting with two
mutually compatible reward-6 actions defeats simple descending greedy selection:
the exact optimum is 12, while greedy returns 10.

## The precise limits of that equivalence

QUBO equivalence is exact **for the enumerated fixed pool and declared rows**.
It requires that the caller enumerate all interactions relevant to simultaneous
execution. A physically legal pair does not prove a legal triple; cumulative
power/buffer capacities need explicit rows. A route occupancy window or worker
shift crossing must be encoded in candidate legality/conflicts, not inferred from
a single resource name. The simulator/checker remains responsible for event
ordering, future arrivals, battery state, defects and other dynamic constraints.

The current linear reward is a dispatch surrogate. It is not algebraically equal
to end-to-end tardiness, throughput, makespan or CVaR. Choosing the optimum action
set at each tick need not choose the optimum policy or schedule. Candidate pruning,
rolling commitment and incomplete lookahead can exclude the full-model optimum.
Report pool coverage, candidate construction time and end-to-end outcomes, rather
than equating a small local bit count with a lossless whole-factory compression.

The classical exact reference enumerates original core selections and checks the
declared constraints without evaluating QUBO coefficients or slack energies.
It shares the candidate specification; it is not an independent physical checker.
The seeded SA uses incremental single-bit Metropolis moves, restarts, and one
feasible greedy warm start. Raw bits/energy and any repair are preserved. A repair
is a classical intervention and must not be counted as a raw quantum feasible hit.
The warm start ensures SA's retained best energy is no worse than greedy when
arithmetic and implementation are correct; equal-budget comparisons should include
that initialization time. No solver here uses a QPU, VeloxQ or a GPU.

## Reproducible implementation checks

Run `python3 -m stage2.qubo --audit` from the repository root. The recorded audit
seed is 713 for 100 randomly generated tiny conflict/capacity QUBOs. Exhaustively
checking all 6,116 complete bit strings verifies that every ground state is
feasible and its energy matches the independent original-selection optimum.
Every feasible core selection is also checked to have a zero-penalty extension.
This covers unit/zero/redundant/general capacity transformations and negative,
zero and positive rewards. It supplements the general proof; it does not replace it.

A separate fixed smoke benchmark uses 30 generated 12-candidate instances with
generation seeds 0–29, random conflict probability .25, integer rewards 1–20,
integer power demands 1–6, capacity 15. With SA at 150 sweeps and four restarts:

| Metric | Descending greedy | Seeded SA |
| --- | ---: | ---: |
| Mean reward / exact pool optimum | 0.959598 | 0.983006 |
| Exact pool optimum hits | 19/30 | 23/30 |
| Repaired SA outputs | — | 0/30 |

This is a solver correctness/performance smoke test, **not factory evidence or a
held-out learning result**. Timing is machine-dependent and printed by the command.
During this test, a restart-indexing defect was detected by the warm-start energy
invariant and fixed before delivery: the incremental field array must be built
in variable-index order even when the flip sweep order was previously shuffled.

## Required reporting for the research push

Use immutable instance seeds and separate training/validation/test seed sets.
Compare policies under identical event/quality tapes, but reveal each event only
when its observation time or actual inspection occurs. Align defect randomness by
lineage, operation and attempt, rather than the policy's random draw order. Include
failed runs, deadlocks and unfinished orders; dropping them biases the result.

Time instance generation, candidate construction, encoding, solver, decoding,
checking and communication separately, then report total time. For stochastic
methods report repeated seeds and distributional outcomes, not the best seed.
Use a shared scenario/tick horizon, objective hierarchy and physical checker.
Declare whether wall-time, solver calls or CPU/GPU time is the matched budget.

If learning helps, include fresh/frozen/random and ordinary heuristic comparisons
on held-out instances and seeds; count training cost separately from inference.
Compare trained policies against a stronger matched-budget classical search, not
only an intentionally weak rule. Operational complexity should be measured by
real blocked resources, traffic contention, energy limits, join dependencies and
recovery events, not by adding dormant feature labels or unused GPUs.
