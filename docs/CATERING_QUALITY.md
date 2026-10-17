# Catering: correctness and solution-quality audit

17 October 2026. This audit uses frozen V3 evidence and fresh local verification.
No quantum training, paid backend job or hardware call accompanies it.

The implemented QUBO has a correctness argument in
[PROJECT_DESIGN.md](../PROJECT_DESIGN.md): anchor encoding, service/waste
expansion, exact objective priorities, the all-bitstring penalty bound and
the scaled Ising map. Tiny exhaustive tests and a separate physical checker
support those arguments. Correct formulation does not guarantee that a heuristic
will return the ground state.

Current quality is strongest on the complete small cell. Larger runs measure
restriction and search losses; they are not certified full-kitchen quantum
optima. The tables below state those distinctions explicitly.

## Complete small cell

All 32 legal local programs on this narrow recipe/calendar grid are offered.
Three idle choices make 35 data qubits, with 520 couplers. There are 1045 one-hot
states, 59 physically feasible. Independent raw CP, offered CP, physical subset
enumeration and exact-sector optimization agree on (U,W,B,R)=(0,0,2,2).
The encoded scalar optimum is 68 under the cell's stated weights. The raw CP
model uses different lexicographic weights and reports 10 for the same tuple;
those scalar values must not be compared as a quality gap.

All six predeclared QAOA simulator trials find that tuple in 4096 shots each.
Initializer and mixer-only controls also find it. The probability column is
the exact noiseless final-state probability of a QUBO ground state; it is
not the probability of obtaining a ground state in every shot.

| Depth | Seed | Physically valid shots / 4096 | Ideal ground-state probability | Best checked tuple |
|---:|---:|---:|---:|---|
| 1 | 2026 | 3784 | 0.3370% | (0,0,2,2) |
| 1 | 2027 | 3264 | 0.3037% | (0,0,2,2) |
| 1 | 2028 | 2910 | 0.4282% | (0,0,2,2) |
| 2 | 2026 | 2217 | 0.3982% | (0,0,2,2) |
| 2 | 2027 | 1585 | 0.6189% | (0,0,2,2) |
| 2 | 2028 | 3369 | 0.7253% | (0,0,2,2) |

Source: `output/catering-complete-cell-v3/report.json` and all six trial
directories. Six successful runs of this one instance are not six independent
problem instances, nor evidence of a classical speedup. The sector itself is
classically tractable and explicitly enumerated by the simulator.

## Fixed six-customer release: cost of restricting the domain

Tuples are lexicographic (U,W,B,R), smaller first. Every raw reference below
has an OPTIMAL status. The fixed quantum-pool optima are freshly re-enumerated
by the audit; they are not the final results of the changing-portfolio pilot.

| Case | Raw-grid optimum | Fixed quantum-pool optimum | 128-bit offered reference | 256-bit offered reference |
|---|---|---|---|---|
| S0 | (2,0,6,6) | (5,0,3,3) | (3,0,6,6), OPTIMAL | (2,0,6,6), FEASIBLE, matches raw optimum |
| S1 | (3,0,5,5) | (7,0,1,1) | (3,3,6,6), OPTIMAL | (3,0,6,6), OPTIMAL |
| S2 | (2,1,6,6) | (5,4,4,4) | (3,1,6,6), OPTIMAL | (2,1,6,6), OPTIMAL |
| S3 | (3,1,6,6) | (6,4,4,4) | (4,1,5,5), OPTIMAL | (4,1,5,5), OPTIMAL |

Source: `output/catering-foundation-v3/report.json`, each case's raw/encoded
reference, and fresh exact small-portfolio checks. The S0/256 solver itself
did not certify optimality before its limit. Its checked tuple equals the
certified raw-grid optimum, and its domain is a restriction of that grid, so
the operational tuple is optimal by that independent bound. Preserve both facts.

This illustrates a genuine representation cost. Perfectly solving a restricted
QUBO can still miss meals that the raw model can serve. Enrichment need not
remove every gap: at 256 bits S1 still uses an extra batch, and S3 misses one
extra meal. Raw energies from different bundles cannot quantify these gaps.

## Changing-portfolio QAOA pilot: final search versus representation loss

Four cases, two seeds, eight portfolio updates per run, 16 parameter candidates
and 2048 shots per update, at most 35 data qubits. Each final incumbent is retained
inside the final attempted portfolio (step07). The audit re-encodes the actual
final plan in that exact bundle and recomputes its sector optimum.

| Case / seed | Certified raw optimum | Exact optimum of final offered pool | Actual final quantum incumbent | Same-pool optimal? |
|---|---|---|---|---|
| S0 / 2026 | (2,0,6,6) | (3,1,6,6) | (3,1,6,6) | Yes |
| S0 / 2027 | (2,0,6,6) | (4,1,5,5) | (4,2,5,5) | No: one waste lot |
| S1 / 2026 | (3,0,5,5) | (5,1,5,5) | (5,1,5,5) | Yes |
| S1 / 2027 | (3,0,5,5) | (5,1,4,4) | (5,1,4,4) | Yes |
| S2 / 2026 | (2,1,6,6) | (4,2,5,5) | (4,2,5,5) | Yes |
| S2 / 2027 | (2,1,6,6) | (4,2,5,5) | (4,2,5,5) | Yes |
| S3 / 2026 | (3,1,6,6) | (4,1,6,6) | (5,2,5,5) | No: extra missed meal first |
| S3 / 2027 | (3,1,6,6) | (5,3,6,6) | (5,3,6,6) | Yes |

**Six of eight final incumbents match their final offered-pool optimum. All
eight still trail the certified raw optimum.** The represented choices limit
quality even when the quantum sampler finds the same-pool minimum. Two runs
also leave a search gap in that final pool. This is a finite pilot result,
not a universal property of the method.

All eight final-step initializer and mixer-only controls also attain the same
best tuple as their run's final quantum outcome. None of the final updates
accepts an improvement; the last accepted updates occur earlier. The 6/8 finding
therefore explains representation versus search loss, not a benefit from the
trained cost phases or a successful fresh improvement at the last step.

The UI traces a retained quantum sample to the last accepted update, which can
precede step07. That source's offered reference is a different bundle from
the final attempted pool used here. Keep its ID/hash when explaining either
comparison; do not combine one pool's energy or optimality with the other.

Source: `output/catering-paired-pilot-v1/*/report.json`, final plans and step07
bundles; `output/catering-math-audit-v1/mathematics.json` records the fresh
exact optima, source hashes, physical-pair checks and decoded incumbents.
Per-step controls share the quantum incumbent. They are not independent full
controller baselines. Two seeds on four fixed inputs are development evidence,
without a held-out problem generalization claim or an independently frozen VQE
train/test partition. Ordinary instance-wise variational optimization itself
does not require a supervised-learning split.

## Larger same-model VeloxQ workload

These are twelve-customer S3 inputs, with nested restrictions of 18182 generated
local programs. Width includes idle bits. Each service row is one cold job
with 512 returns, 2000 steps and no tuning. Backend running times are 0.17/0.55/1.93 s;
end-to-end times are 8.0/8.0/14.2 s. Those different timing definitions must stay
separate. No time-to-first-feasible is available from final-only returns.

| Variables | Couplers | Best checked VeloxQ tuple | Valid returned rows | 30-second offered CP incumbent | 2-second-cap cold raw-bit SA best valid |
|---:|---:|---|---:|---|---|
| 512 | 37008 | (13,6,4,4) | 5/512 | (6,1,10,10), FEASIBLE | (12,15,9,9) |
| 1024 | 156129 | (14,8,4,4) | 1/512 | (7,2,11,11), FEASIBLE | (12,12,9,9) |
| 2048 | 636882 | None | 0/512 | (8,3,8,8), FEASIBLE | None |

The separate 30-second raw reference has a checked FEASIBLE tuple (5,1,11,11).
No scale CP row is a proven optimum. Cold SA's different initializer/search
space and the unequal measured budgets prevent a fair speedup claim from
this table. Best valid means best among returned valid states, not all visited
states. Larger QUBOs are approximately 28–30% dense, not demonstrated sparse.

Sources: `docs/catering-methods/VELOXQ.md`, each committed service
`evaluation.json`, and `output/catering-classical-scale-v3/report.json`.
Service rows here are the owner's independently evaluated retained receipts;
the new small-domain mathematical audit does not rerun those service jobs.

The scale inputs exercise integration and expose the current feasibility
bottleneck. Improved settings or a new proven penalty construction need a
new version/hash, checked results and a capped authorized experiment. Current
evidence neither establishes VeloxQ's best attainable quality nor a win over
the retained classical controls.

## What correctness verification covers

The fresh retained-evidence check validates 965 artifact hashes, 152340 returned
bitstrings, 467003 sample frequencies and 8 final raw plans. In addition:

- The mathematical audit rechecks 13 small bundles: the complete cell, four fixed
  quantum portfolios and the eight final attempted pilot pools. It independently
  checks local and pairwise physical feasibility, anchor layout, objective bounds,
  lexicographic weights, literal penalties and exact 4E Ising probe identities.
- The complete-cell independent physical subset audit agrees with its exact
  sector optimum. It does not enumerate all 2^35 bitstrings; tiny tests exhaust
  the whole Hilbert space and the general penalty proof handles larger spaces.
- Two adversarial tests cover nonempty previous plans with unequal priorities,
  and a bijection between independently feasible subsets and anchor encodings.
- Native/routed Qiskit equivalence is tested on a small full-statevector fixture.
  This checks the circuit implementation, not physical hardware performance.
- Offline VeloxQ adapter tests check its integer/spin/packet boundary without
  a token, upload or service execution.

Verification artifacts and exact test receipts are retained under
`output/catering-math-audit-v1/`. A passing audit establishes internal
correctness/evidence consistency within this declared model, not jury acceptance,
real-world calibration, an optimum outside the offered domain or quantum benefit.

## Independent formulation review passes

Three separate read-only reviews examined loss semantics, encoding/proofs and
reference/evidence consistency. They found no algebraic or material-balance
defect in the retained fixtures. Deterministic probes confirmed the paired loss,
all 1045 cell-sector states, 130 independent arbitrary-string objective probes,
exact circuit equivalence and the reported 6/8 final-pool optima.

The reviews identified two supported-input boundary gaps, now rejected explicitly:

- Future, off-grid, reversed or non-cooker outages previously passed the domain
  validator even though the profile only handles an ongoing observed withdrawal.
  Validation now requires a grid-aligned cooker outage with 0<=start<=now<end
  within the horizon; the physical checker enforces the same observed scope.
- Future-revealed ordinary demand previously entered the snapshot and could
  inform early preparation. Snapshot construction now rejects unrevealed active
  groups, and the independent checker rejects a forged snapshot exposing them.

Regression tests include malformed times/resources, a valid already ongoing
outage, an unrevealed paired meal, a hidden future urgent meal and constructor
bypass attempts. Current frozen inputs obey both boundaries; no retained QUBO,
sample, schedule or objective tuple needs replacement. The controlled fixtures
remain an evidence limitation rather than a proof of broad model generality.

## Quality acceptance before recording

Select a source-hashed primary quantum result. Show hard feasibility, best
checked (U,W,B,R), repeated runs and the appropriate exact/reference status.
State whether the domain is complete, offered or conditional. Freeze every
displayed comparison to its actual bundle. Report invalid raw samples instead
of silently repairing them. Keep preprocessing/training/sampling/checking and
remote latency in their proper runtime categories. Improve larger-domain
performance where possible, but do not replace the evidence with projections.

Reproduce the mathematical audit and retained checks without training:

```sh
.venv-stage2/bin/python -m catering.audit_math --output output/NEW-MATH-AUDIT.json
.venv-stage2/bin/python -m catering.verify_meals \
  output/catering-foundation-v3 output/catering-paired-pilot-v1 \
  output/catering-complete-cell-v3 --output output/NEW-RETAINED-CHECK.json
```
