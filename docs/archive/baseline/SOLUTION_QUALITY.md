# Solution quality against classical references

This is the evidence for the challenge's five-point solution-quality criterion.
The organizer awards the score; no experiment can guarantee five points.
The [challenge](../../../Quantum_Hackathon_2026_ERP_Challenge.pdf), §11, asks for
makespan against a reference/classical baseline. Quantum advantage is not a
requirement. We distinguish exact makespan comparisons from the extended
factory's lexicographic missing-order/deadline-debt/cost objectives.

## What is established

| Problem | Best checked solution | Reference | What the comparison establishes |
|---|---:|---:|---|
| Mandatory A | 4 hours, actual simulator QAOA | Exact optimum 4 | Zero makespan gap |
| Mandatory B | 8 hours, actual simulator QAOA | Exact optimum 8 | Zero makespan gap |
| Deterministic two-pump extension | 863 minutes, CP-SAT | Proven optimum 863 | Zero gap for the declared extended reference domain |
| Deterministic three-pump extension | 1,191 minutes, CP-SAT | Proven optimum 1,191 | Zero gap for the declared extended reference domain |
| Deterministic four-pump extension | 1,541 minutes, checked derived CP witness | Optimum in [1,524, 1,541] | At most 17 minutes, or 1.116%, excess over optimum |

The two-pump and three-pump references have 32/48 operations and 38/57 part
transfers, matched three-component assembly, machine blocking, finite reserved
inputs, one shared worker with hall walks and one shared AGV. They are substantive
extensions, with exact comparisons on the **same numerical model**. They disable
quality risk, staffing calendars, variable energy and other flagship mechanisms.
Their optima do not bound the full stochastic factory. The strongest retained
development heuristics take 1,238/1,860 minutes, respectively. The CP solutions
reduce those completion times by 30.29%/35.97%; this is classical optimization,
not a quantum speedup. [Reference domains and evidence](../manufacturing/STAGE2_REFERENCE_MULTI.md).

The four-pump raw CP output allows early future-pump empty reservation. A separate
derived witness delays one parked reservation to the pump's birth and passes both
unchanged physical and identity checkers. Its operations, physical legs,
pickup/drop, shipments and metrics do not change. The broader CP lower bound also
bounds the stricter dispatch-at-birth subset. The exact optimum is still unknown.

The supplemental local search also retains negative results: a five-minute,
eight-worker alternative CP formulation and three worker-order neighborhood
searches did not improve 1,541. The new global search's bound 1,457 is weaker than
the earlier 1,524, so the combined interval stays [1,524,1,541]. The fixed-worker
and two eight-operation-block neighborhoods prove only their own restricted
optima; their bounds are not global certificates. Their measured reference-search
process CPU total is 2,374.76 seconds (0.660 CPU-hours), separate from earlier
research accounting and excluding test/audit work.
[Local search results and accounting](../../../output/solution-quality-20261017/closeout.json).

## Full physical factory: a quantified primary gap

The supplemental [complete audit](../../../output/solution-quality-20261017/full-factory-compound-gaps/report.json)
reconstructs all 2,048 distinct numerical configuration/tapes and audits all
23,552 retained outcome rows, covering every one of the 74 frozen method/context
groups. It does not rerun those factory episodes, select new policies, or turn
actor replicas into independent factories. The original full physical/identity
checks remain the evidence for unretained traces.

For each realized tape, let `L` be the necessary quality/material missing-order
bound, `U_best` the fewest misses in any valid retained execution on that identical
tape, and `U_method` the method's misses. Then:

```
L <= realized primary optimum <= U_best
U_method - U_best <= method's realized primary gap <= U_method - L
```

When `U_method = L`, that execution is globally optimal for missing orders on that
realized tape. All methods face the same physical instance; selecting `U_best`
with hindsight is only an offline upper bound, not a deployed controller. These
intervals do not prove optimality of a nonanticipating stochastic policy, nor
optimality for deadline debt, cost or carbon.

The preselected controllers remain unchanged:

| Initial orders | Calendar | Mean missing | Mean excess above realized optimum | Weighted primary-optimum certificate rate |
|---:|---:|---:|---:|---:|
| 10 | 96 hours | 0.01031 | [0, 0.00406] | 99.59% |
| 11 | 96 hours | 0.03172 | [0, 0.02547] | 98.55% |
| 12 | 96 hours | 0.07500 | [0.06469, 0.06875] | 95.61% |
| 13 | 96 hours | 0.14922 | [0.09375, 0.14297] | 88.84% |
| 14 | 96 hours | 0.27813 | [0.12344, 0.27187] | 80.88% |
| 16 | 96 hours | 2.69062 | [1.14031, 2.68219] | 8.80% |
| 24 | 96 hours | 10.02094 | [0.57063, 10.01250] | 0% |
| 32 | **240 hours** | 0.10234 | [0, 0.04719] | 95.28% |

These are exact probability-weighted empirical aggregates of this fixed sample,
rounded for display; they are not population guarantees or confidence bounds.
No useful relative percentage gap exists when the optimum is zero, so we use
absolute excess missing orders. High-load failures remain visible. The 32-order
case grants a longer calendar and substantial lateness; it is not evidence for
32-order completion over 96 hours.

For the 12-order QAOA method, the same realized primary gap is [0.14000, 0.14406]
mean missing orders, with a 92.44% weighted primary-optimum certificate rate.
The matched SA/uniform controls and the original family-adjusted comparisons
remain in the [frozen results](../manufacturing/STAGE2_RESULTS.md). **No quantum advantage is
demonstrated.** The selected classical controller's numbers must never be
attributed to QAOA.

## Stronger proof without changing outcomes

The original quality relaxation used the largest single mandatory step's minimum
legal-mode defect risk. The new bound uses the executed recurrence
`r <- 1 - (1-r)(1-p)` across every mandatory manufacturing step:

```
minimum final first-inspection risk >= 1 - product(1 - minimum legal p_step)
```

Wear is nonnegative and is granted zero in this relaxation. Exact fractions and
a conservative 1e-10 rounding margin prevent near-threshold floating comparisons
from becoming certificates. Repair retains its fixed audited residual risk. A
unit whose first and repair draws are below those necessary floors must scrap;
finite blank stock then bounds which matched BOMs can possibly ship. This uses
no assumption of independent inspection draws. Hidden keyed draws appear only
in the offline certificate, never in a controller or planning future.

The stronger proof raises the unchanged 32-order primary certificate rate from
93.44% to 95.28%, tightening mean excess from at most 0.07406 to 0.04719 missing
orders. It changes no performance outcome, policy, random tape or frozen source.

Reproduce the complete gap audit, in a fresh output directory:

```sh
.venv-stage2/bin/python -m stage2.quality_gap_audit --bound-kind compound \
  --output output/new-solution-quality-audit
.venv-stage2/bin/python -m unittest discover -s tests/stage2 -p 'test_quality_*'
```

The audit retains exact rational aggregates, per-tape certificates, input hashes
and source snapshots. All invalid outcomes, identity mismatches, missing actor
replicas, duplicate executions and inconsistent weights fail closed.

## What to explain to the jury

Show actual Stage 1 QAOA results, then one exact extended reference and its
checked physical resource use. Explain why the full factory uses local quantum
subproblems with classical state maintenance. Show the same-model classical
controls, the full-factory certificate table and a retained negative result.
Keep makespan, missing-order optimum and secondary costs separate. Being able to
explain these distinctions is part of the scoring evidence.

VeloxQ is not used anywhere in these results. All QAOA runs are local algorithm
simulation. There are no physical-QPU calls or service costs in this supplement.
