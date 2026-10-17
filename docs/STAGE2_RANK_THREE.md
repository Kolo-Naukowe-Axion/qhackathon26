# Baseline B: three semantic bits with a nonlinear decoder

**The official three-job instance at deadline H=8 has an exact three-bit QUBO that retains all five feasible full machine orders.** The eliminated comparison is reconstructed by a proved Boolean relation. This improves the earlier four-bit candidate without modifying it, the official Stage 1 code or selected artifacts.

Implementation: `stage2/rank_three.py`. Evidence: `output/stage2-search/rank-three-final/`. Structural construction uses the standard library; QAOA simulation and offline IQM routing use their existing separate environments:

```sh
python3 -m stage2.rank_three --output /path/to/new-root
.venv/bin/python -m stage2.rank_three --phase qaoa --output /path/to/new-root
.venv-odra/bin/python -m stage2.rank_three --phase iqm --output /path/to/new-root
```

Each phase creates a new directory and refuses to overwrite it. All original four-bit experiments remain intact.

## What the three bits mean

The original nine comparison bits are T:`x0,x1,x2`, F:`x3,x4,x5`, S:`x6,x7,x8`, with each triple comparing Z1/Z2, Z1/Z3 and Z2/Z3. Previous structural SAT proofs establish the aliases:

`a=x0=x3`, `b=x1=x4=x7`, `c=x2=x5=x8`, `d=x6`.

We now retain **a,b,d** and decode:

`c = 1 − a + ab = NOT a OR b`.

Thus the complete machine-order vector is `[a,b,c,a,b,c,d,b,c]`. This is a deterministic nonlinear semantic decoder. It is not omission of a comparison, restriction to permutation schedules, or a table mapping codes to preselected answers.

The resulting QUBO is:

`E3(a,b,d) = a + d + ab − 2ad − bd`.

It has three pair couplers, integer coefficients of magnitude at most two, zero offset and no auxiliary encoding bits. Positive energies do **not** generally equal the previous four-bit energies; the equivalence concerns exactly their zero sets under the decoder.

## Why the elimination is valid

The certified four-bit model is the sum of six nonnegative penalties:

```text
b(1−c)
(1−a)(1−c)
(1−c)(1−d)
a(1−d)
b−ab−bc+ac        [T/F tournament triangle]
b−bd−bc+cd        [S tournament triangle]
```

At zero energy, `c=0` forces `b=0,a=1` through the first two cuts. Conversely, `a=1,b=0` makes the first triangle equal `c`, so it forces `c=0`. Therefore `c=0` iff `a=1,b=0`, proving the decoder relation.

After substitution, the first two penalties and the T/F triangle vanish identically. Let `A=a(1−d)` and `S=b−bd−bc+cd`. The remaining physical cut is `(1−c)(1−d)=a(1−b)(1−d)`, which is bounded by A. Consequently the old sum is zero iff `A=0` and `S=0`.

Both A and S are nonnegative on binary variables. Since `1+b>0`, `(1+b)A+S` has the same zero set. Expanding it with the proved expression for c cancels all cubic terms exactly and produces E3. The implementation performs this binary polynomial algebra; it does not fit coefficients against makespan labels.

## Proofs and classical cost

Construction reuses the earlier certified physical-cut model, whose disclosed work was 770 partial-DAG longest-path checks, 90 SAT queries and 172 DPLL search nodes. The new constructor:

- Rechecks all 78 retained physical cuts against the actual processing durations and deadline.
- Reproves each of five alias edges using ten UNSAT queries.
- Proves all four counterexamples to `c=NOT a OR b` impossible using four more UNSAT queries.
- Independently replays every new contradiction proof, then derives the polynomial symbolically.

The fourteen additional queries use fourteen DPLL search nodes. No LP or complete-schedule labels enter construction. The new structural work took approximately one millisecond locally, excluding the prior compiler and subsequent exhaustive validation. These are tiny-instance measurements, not scalability evidence. SAT presolve is real classical computation and can itself find solutions.

Only **after** construction, all eight decoder assignments and all 512 original bitstrings are independently checked. All 216 transitive full machine-order schedules also pass the unchanged official Stage 1 validator. The accepted original states are exactly `73,292,438,502,511`; state 502 retains a different order on the final machine.

| a,b,d | Derived c | E3 | Decoded earliest makespan |
|---|---:|---:|---:|
| 0,0,0 | 1 | 0 | 8 |
| 1,0,0 | 0 | 1 | 10 |
| 0,1,0 | 1 | 0 | 8 |
| 1,1,0 | 1 | 2 | 9 |
| 0,0,1 | 1 | 1 | Cyclic S order |
| 1,0,1 | 0 | 0 | 8 |
| 0,1,1 | 1 | 0 | 8 |
| 1,1,1 | 1 | 0 | 8 |

Five distinct feasible orders need at least five distinct codes under a deterministic computational-basis decoder. Two bits supply only four codes, so **three is minimal within the explicit requirement to retain every feasible order through such a decoder**. This is not a lower bound on arbitrary quantum algorithms, other readout models, formulations retaining only one optimum, or general scheduling solvers.

## Actual QAOA simulation

The same genuine QAOA cost/mixer circuit implementation is used on three qubits. Coordinate angle search minimizes exact expected energy with a 512-evaluation cap and four starts. Seeds 2026, 17 and 83 are run for p1/p2, with 1024 actual Aer measurement shots each. Exported QASM circuits are independently checked against Qiskit's exact statevector; maximum probability discrepancy is `2.22e−16`.

| Circuit | Mean ideal deadline probability | Range across angle seeds | Mean measured ground fraction |
|---|---:|---:|---:|
| Uniform | 62.50% | Exact | Retained per run |
| QAOA p1 | 92.95% | 92.95–92.95% | 92.90% |
| QAOA p2 | 95.09% | 93.37–97.05% | 94.30% |

All six selected samples are actually observed, have zero energy, and decode to officially validated makespan-eight schedules. The p1 searches converge to the same angles; p2 varies across optimizer seeds. Each run retains all raw counts, angles, circuit, probabilities, sampled selection, source hashes and classical construction costs.

This raises single-shot concentration relative to uniform. It does not demonstrate quantum speedup: five of eight codes already succeed, and equal-shot uniform also finds a feasible order in every recorded run. The classical SAT/compiler and tiny exhaustive reference are sufficient to solve the instance without a quantum computer.

## Offline IQM star proxy

The source angle seed 2026 circuits compile through the unchanged `solver.odra.compile_candidate`, searching eight routing seeds. Actual native costs are:

| Circuit | Native R | Native CZ | Depth including measurement | Classical outputs |
|---|---:|---:|---:|---:|
| p1 | 18 | 9 | 19 | 3 |
| p2 | 30 | 18 | 36 | 3 |

The allocated proxy circuit register has five physical wires; only three encode scheduling decisions. All eight classical outcome probabilities are preserved after actual measurement wiring and ancilla marginalization, with maximum error `9.16e−16`. Source seed 2026's ideal ground probabilities are 92.95% and 97.05%, respectively; these are individual example circuits, not new multi-seed averages.

Native QASM3, QPY, initial/final layouts, measurement maps before/after measurement removal, native counts/depth, versions and hashes are retained. This uses IQMFakeAdonis with Qiskit 2.1.2 / IQM client 35.0.3. **No physical ODRA5 job, current calibration, noise tolerance or hardware success rate was tested.**

## Scope and tests

The result is specific to this numerical instance, H8 and the certified semantic relations. The earlier varied-duration/deadline diagnostic remains valid evidence against a generic compression claim. No large-factory global encoding or quantum advantage follows.

`python3 -m unittest discover -s tests/stage2 -p test_rank_three.py -v` passes five tests. They verify nonnegative-factor algebra, all fourteen UNSAT proof replays, exhaustive 512-state coverage / 216 official schedules, retention of all five orders, rejection of tampered polynomials/cuts, and that poisoning the old answer list cannot affect construction.
