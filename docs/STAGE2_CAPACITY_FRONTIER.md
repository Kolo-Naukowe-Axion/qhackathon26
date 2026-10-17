# Nested capacity-pool frontier — 17 October 2026

This local development pass tests whether the complete 2,499-bit recovery QUBO
is necessary to retain the benefit of replacement heat capacity. **It is not:
a deterministic, answer-independent 2,078-bit pool retains the same on-time
optimum.** This does not establish a minimum sufficient size.

## Protocol and generation

Use the saved `manufacturing-recovery-v2` problem, immutable original candidate
pool and original heuristic parents for both 32-operation heat cases. Preserve
every original assignment. Append unary-legal rows in round-robin
machine/worker mode order. Alternate nearest-anchor starts with starts maximizing
temporal distance from already retained rows of that mode. Unlike the old
radius-limited generation, the append ordering spans the whole legal horizon.

Freeze caps 24, 32, 48, 64 and all unary rows before outcomes. Caps apply per
operation; every later pool is a superset of the earlier pool. The all-unary
case is not support-pruned. The generator receives only the raw problem and
original columns: no native-reference plan, objective, missing-row identity or
CP result is supplied. All pools are saved before references are imported or
read. The original heuristic witness is a disclosed CP hint and does not become
a returned solver success by retention.

Each pool is solved by the independent raw optional-interval pool reference,
one worker and a five-second solve cap. Its construction time is additional.
The full QUBO is compiled to count coefficients, and each returned plan is
checked against the raw model and exact QUBO energy. Implementation snapshots,
copied problem/baseline inputs, protocol, every pool and reference result, counts
and hashes are retained. Reproduction also reads the original heuristic parents
from the retained source campaign; the new output does not copy parents.json.

## Complete result

All ten references prove OPTIMAL within their declared domains.

| Pool | Outage bits / couplers | Outage tardiness / makespan | Replacement bits / couplers | Replacement tardiness / makespan |
|---|---:|---:|---:|---:|
| Original cap24 | 781 / 25,818 | 45 / 945 | 781 / 26,307 | 45 / 945 |
| Nested cap32 | 1,040 / 46,758 | 45 / 945 | 1,041 / 47,837 | 45 / 945 |
| Nested cap48 | 1,560 / 108,321 | 45 / 945 | 1,561 / 109,971 | 45 / 945 |
| Nested cap64 | 2,078 / 196,162 | 45 / 945 | 2,078 / 196,228 | **0 / 855** |
| All unary rows | 3,745 / 625,776 | 45 / 945 | 3,969 / 700,806 | **0 / 855** |

The 2,078-bit recovery pool retains the certified complete-model optimum with
16.85% fewer variables and48.55% fewer couplers than the previously compiled
2,499-bit/381,371-coupler support-pruned complete QUBO. Those counts compare
different domain constructions and compiler register conventions; they do not
prove an optimum encoding or attribute all savings to the append method.
The pool remains deliberately lossy despite preserving this instance's optimum.

The whole experiment takes20.748 seconds wall time, including generation,
ten native references and ten QUBO compilations. Replacement cap64 reference
construction plus solving takes1.107 seconds; full unary takes4.222 seconds.
These local timing observations are not a normalized solver tournament.
All source hashes remain stable. No annealing, quantum, VeloxQ, token access,
hardware, remote compute, publication or credit use occurred.

The interpretation is now **measured recovery-value versus retained domain**.
The old cap24 pool loses a useful coordinated schedule; larger deterministic
pools can recover it. The disappearance is not caused by omitting replacement
machine H3 entirely. A posthoc audit of the saved complete reference finds four
missing coordinated assignments elsewhere in the schedule; that diagnosis was
not provided to the new generator. Do not describe2,499 bits as necessary or
claim VeloxQ must search the complete domain to find the benefit.

## Verification and reproduction

Implementation: [capacity_frontier.py](../stage2/capacity_frontier.py).
Tests: [test_capacity_frontier.py](../tests/stage2/test_capacity_frontier.py).
The two tests cover immutable baseline, nestedness, unary legality, completeness,
determinism, teacher independence and invalid input rejection.

```sh
.venv-stage2/bin/python -m unittest tests.stage2.test_capacity_frontier -v
.venv-stage2/bin/python -m stage2.capacity_frontier --output output/NEW-FRONTIER --seconds 5
```

Evidence: [complete report](../output/capacity-frontier-review-v1/report.json)
and [predeclared protocol](../output/capacity-frontier-review-v1/protocol.json).
Existing output directories are refused. Results constitute development
evidence on the known recovery fixture, not held-out manufacturing performance.
