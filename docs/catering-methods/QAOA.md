# QAOA for the catering kitchen

Owner: QAOA track. Code: `catering/methods/qaoa.py`, tests: `tests/catering/test_qaoa.py`,
branch `iwosmu/catering-qaoa`. Simulator only: no IBM or VeloxQ call is made.

This document explains the idea and the code. Results of the agreed protocol
(section 7) are in sections 10–11.

## 1. The problem in one paragraph

A central kitchen must deliver lunches. A meal counts as delivered only if both
its main course and its side arrive before the customer's departure, fresh
enough. The kitchen chooses which batches to cook, how big, on which cooker,
with which workers, and which orders each batch serves. Cookers, prep stations,
the packing line and workers can do one thing at a time. After an event at
10:50 (urgent order and/or cooker outage, scenarios S0–S3) the remaining plan
is re-optimized. Plans are ranked lexicographically by
**(U, W, B, R)** = missed meals, wasted component lots, new batches, plan changes.

## 2. From the kitchen to qubits

The shared foundation (integrator-owned) turns this into a QUBO; the QAOA code
only consumes it.

- **One qubit = one legal local batch program.** A program is a complete recipe
  for one batch: menu, yield, cooker, workers, prep/cook/pack/clean times and
  which order lots it serves. Selecting it means "cook this batch this way".
- **Blocks.** Programs are grouped by the order component they cover. Each block
  also has an **idle qubit** meaning "choose nothing here". Exactly one qubit per
  block must be 1 ("one-hot"). The set of bitstrings obeying this in every block
  is the **one-hot sector**.
- **Energy** `E(x) = constant + Σ aᵢxᵢ + Σ_{i<j} bᵢⱼxᵢxⱼ` with integer coefficients:
  - objective: weighted (U, W, B, R). A meal is complete only if main *and* side
    are covered, which gives the quadratic term `priority·(1 − M·S)`;
  - penalties: two programs that clash on a cooker/worker/time, serve the same
    lot, or break one-hot get a large penalty. The penalty exceeds every possible
    objective difference, so the lowest energy is always a legal plan.
- **Ising form** (for circuits): substitute `xᵢ = (1 − Zᵢ)/2`. Linear terms become
  single-qubit Z rotations, pair terms become ZZ rotations. The repo helper
  `catering.qubo.ising()` returns these coefficients times 4.

Sizes of the frozen v3 inputs:

| Bundle | Qubits | One-hot sector states |
|---|---:|---:|
| complete cell (train) | 35 | 1,045 |
| S0 (train) | 33 | 139,968 |
| S1 (train) | 35 | 248,832 |
| S2 (test) | 31 | 62,208 |
| S3 (test) | 35 | 279,936 |

## 3. The QAOA idea, applied here

QAOA prepares a quantum state, applies `p` rounds of two operations and measures:

1. **Start state.** A superposition of many candidate plans.
2. **Cost layer** `exp(−iγ·E/scale)`. Every bitstring gets a phase proportional to
   its energy. Probabilities do not change yet; good and bad plans are "labelled".
3. **Mixer layer.** Moves amplitude between neighbouring plans. Because of the
   phases, amplitudes interfere: with good angles, low-energy plans add up and
   high-energy plans cancel.
4. **Repeat** steps 2–3 `p` times (depth), each round with its own angles γ, β.
5. **Measure** all qubits: each shot returns one bitstring = one candidate plan.

A classical optimizer adjusts the angles to lower a loss computed from the
measured energies, then the final circuit is sampled. Every returned bitstring
is decoded into a full kitchen plan and checked by the independent central
checker. Nothing is repaired.

**Loss.** Either the average energy, or **CVaR** (Barkoutsos et al. 2020): the
average over the best α fraction of outcomes (default α = 0.1). CVaR rewards
putting weight on the very best plans instead of improving the average.

**Why a special mixer.** With the standard X mixer, almost all of the 2³⁵
bitstrings break the one-hot rule, so probability is wasted on non-plans. An
**XY mixer** only swaps the "1" between qubits of the same block; started from a
valid state it never leaves the one-hot sector (Hadfield et al. 2019). This is
the catering version of the tutorial's one-hot/XY lesson.

**Why it is classically simulable.** Because the XY variants never leave the
one-hot sector, the simulator stores only the sector's amplitudes (at most
279,936) instead of 2³⁵. This is an exact simulation of the circuit, not an
approximation, but it also means these small instances are not beyond classical
reach; that is not the claim.

## 4. The three variants

| Variant | Start state | Cost layer | Mixer | Simulated on |
|---|---|---|---|---|
| `standard` | uniform over all bitstrings, \|+⟩ⁿ | one γ on the full penalized energy | X on every qubit | full 2ⁿ vector, ≤ 26 qubits |
| `xy` | uniform over the one-hot sector (a W-state per block) | one γ on the literal energy | XY ring inside each block | one-hot sector |
| `xy_multiangle_warm` | biased toward an incumbent plan (85% weight), the integrator pilot's start | separate angles for objective and conflicts | XY ring inside each block | one-hot sector |

- `standard` is the textbook baseline. It cannot run on the 31–35-qubit v3
  bundles (2³⁵ amplitudes ≈ 512 GiB) and refuses them explicitly.
- `xy` is plain QAOA with a constraint-preserving mixer.
- `xy_multiangle_warm` reproduces the pilot's circuit exactly (unit-tested) but
  trains it with a real optimizer instead of random angle draws.

## 5. Code walkthrough (`catering/methods/qaoa.py`)

| Function | What it does |
|---|---|
| `energy_table` | Exact int64 energy of every bitstring. Bit `i` of the index is `x_i` in `variable_order` (little-endian, same as Qiskit). |
| `_full_space` | Energy table plus "valid" mask (zero penalty) for the `standard` variant; refuses more than 26 qubits. |
| `_sector_space` | Uses the shared `meal_blocks.sector_data` to list one-hot states with their energies, objective values and conflict counts. |
| `apply_x_mixer` | `exp(−iβΣX)` applied qubit by qubit on the state vector. |
| `initial_state` | Uniform start for `standard`/`xy`; the pilot's warm start for `xy_multiangle_warm`. |
| `evolve` | Applies the `p` cost and mixer layers for the chosen variant. The XY mixer is the shared `meal_blocks.xy_mix`. |
| `cvar` | CVaR of the exact output distribution. |
| `default_scale` | Divides energies by the U weight (one missed meal) so angles have a sensible range; recorded in the output. |
| `train` | The optimizer loop: COBYLA, Nelder-Mead or L-BFGS-B with random restarts; `layerwise` (optimize depth 1, extend the best angles by one layer, re-optimize, up to p; budget shared in proportion to depth); or `random` (best of N random angle sets, kept as a baseline). Every loss evaluation is counted; the evaluation and wall-time budgets are enforced even inside an optimizer run. |
| `solve_qubo` | The contract entry point. Builds the space, trains, evolves the best angles, draws `shots` samples, checks each sample's energy against the literal QUBO, and returns a `MethodResult`. |
| `main` | Command-line wrapper. |

The campaign runner `catering/methods/qaoa_campaign.py` freezes the plan
(`freeze`), then runs every (case, configuration, budget, seed) of one split in
parallel (`run --split train|test`). It refuses to run if a bundle or the
adapter source changed since freezing, checks every sample with the central
decoder/checker and writes per-run evidence, `runs.json`, `summary.json` and a
hashed `manifest.json`.

**Output (`MethodResult`).** Raw samples (bits in `variable_order`, counts,
literal energy), `execution_kind="quantum_simulation"`, status, every setting
and seed, best angles and loss, distribution statistics (P(valid), P(optimum)
and the number of tied optimal states), timings and work counts. With an
`output_dir`, `training.json` (full loss trace) and `result.json` are written
with hashes; existing folders are never overwritten.

**Regime labels.** Training uses exact simulator probabilities. Only the final
samples are shot-based. Shot-noisy training would be a separate, separately
labelled experiment.

## 6. Tests (`tests/catering/test_qaoa.py`) and what they prove

- **Tutorial worked numbers:** example A energy table and bit order; its Ising
  coefficients 2.5, (−2.5, 0), 1; the two-job toy at γ = π/2, β = 3π/8 gives
  exactly −(|01⟩+|10⟩)/√2; the one-qubit formula P(1) = ½(1 − sin2β·sin2γh).
- **Simulator = circuit:** the NumPy kernel matches the tutorial's gate list
  (H, RZ(2γh), RZZ(2γJ), RX(2β)) run in Qiskit, up to global phase.
- **Variant consistency:** one-hot sector energies equal the full literal table;
  single-γ XY equals multi-angle XY with tied angles; the multi-angle variant
  reproduces the pilot's `meal_search.evolve`; depth 0 returns the start
  distribution; XY samples always obey one-hot.
- **Contract:** the solver contract's smoke QUBO is solved ([1, 0] at −4); budgets
  are enforced; equal seeds give equal samples; samples from every variant pass
  the central evaluator (`catering.run evaluate`); invalid requests are refused.

## 7. Agreed evaluation protocol (shared with VQE and VeloxQ)

- **Inputs:** the five v3 bundles above, identified by `bundle_sha256`.
- **Split:** settings (depth, optimizer, loss, restarts) are chosen on the
  complete cell, S0 and S1 only, frozen in a written plan, then run once on S2
  and S3 and reported as they come out.
- **Budgets:** 256 and 2,048 circuits per run (a gradient counts 2 circuits per
  parameter, the hardware parameter-shift cost); restarts count toward the budget.
- **Final sampling:** 4,096 shots per run. **Seeds:** 2026–2035.
- **Metrics (central checker):** P(optimum) with the tie count, P(valid), best
  (U, W, B, R) and gap to the raw CP optimum, success rate over seeds, circuits,
  shots, parameters and wall time.
- **Baselines:** random angle search, uniform sampling, start state only and
  the release's simulated-annealing runs.

## 8. How to run

    .venv/bin/python -m unittest tests/catering/test_qaoa.py -v
    .venv/bin/python -m catering.methods.qaoa \
        --bundle output/catering-foundation-v3/S0/quantum-qubo.json \
        --variant xy --depth 2 --optimizer COBYLA --restarts 4 \
        --evaluations 256 --shots 4096 --seed 2026 \
        --output output/catering-methods/qaoa/NEW-RUN

Then check the samples centrally:

    .venv/bin/python -m catering.run evaluate \
        --bundle output/catering-foundation-v3/S0/quantum-qubo.json \
        --samples output/catering-methods/qaoa/NEW-RUN/result.json \
        --output output/catering-methods/qaoa/NEW-RUN-evaluation.json

Reproduce the full campaign (fresh output folders; `run` checks the frozen hashes):

    .venv/bin/python -m catering.methods.qaoa_campaign run \
        --plan output/catering-methods/qaoa/plan-v1.json --split train --output output/NEW-TRAIN
    .venv/bin/python -m catering.methods.qaoa_campaign run \
        --plan output/catering-methods/qaoa/plan-v1.json --split test --output output/NEW-TEST

## 9. Limitations

- Exact simulation of small instances; no quantum advantage is claimed or implied.
- The fixed v3 portfolios are restrictions of the full kitchen: even their exact
  optimum misses more meals than the raw CP reference (integrator report).
- `standard` QAOA cannot be compared at 31–35 qubits on a laptop.
- L-BFGS-B uses finite-difference gradients here; exact gradients are not
  implemented yet.
- The v3 fixtures have no previous plan, so R = B and plan stability is not tested.

## 10. Results

### 10.1 Selection (training cases only)

`output/catering-methods/qaoa/selection-v1/`: five angle-optimization
strategies × two variants × depths 1–3 × 64/256 evaluations × 5 seeds on the
cell, S0 and S1. Ranked by median P(optimum): layerwise and random-then-COBYLA
best, random search worse, L-BFGS-B with finite-difference gradients worst.
**Frozen** (`plan-v1.json`, before any S2/S3 run): `xy_multiangle_warm`,
depth 3, `layerwise`, CVaR α = 0.1.

### 10.2 Frozen protocol results

Median over 10 seeds (2026–2035), 4,096 shots, exact-simulator training.
"Hit" = seeds whose best checked plan equals the exact portfolio optimum.
P(opt) = probability of the optimal plan per shot (one optimal state in S0–S3,
two in the cell). Every sample was checked by the central checker.

| Case | Split | Setup | Budget | Hit | P(opt) | P(valid) |
|---|---|---|---:|---:|---:|---:|
| cell | train | **frozen** | 256 / 2,048 | 10/10, 10/10 | 0.010 / 0.021 | 0.56 / 0.56 |
| | | random angles | 256 / 2,048 | 10/10, 10/10 | 0.006 / 0.010 | 0.47 / 0.40 |
| | | uniform sampling | — | 10/10 | 0.002 | 0.06 |
| S0 | train | **frozen** | 256 / 2,048 | 10/10, 10/10 | 0.021 / 0.024 | 0.62 / 0.63 |
| | | random angles | 256 / 2,048 | 10/10, 10/10 | 0.004 / 0.009 | 0.28 / 0.36 |
| | | plain XY layerwise | 256 / 2,048 | 8/10, 9/10 | 0.0006 / 0.001 | 0.18 / 0.35 |
| | | start state only | — | 8/10 | 0.0003 | 0.63 |
| S1 | train | **frozen** | 256 / 2,048 | 10/10, 10/10 | 0.062 / 0.070 | 0.52 / 0.49 |
| | | random angles | 256 / 2,048 | 10/10, 10/10 | 0.032 / 0.055 | 0.47 / 0.45 |
| | | plain XY layerwise | 256 / 2,048 | 8/10, 9/10 | 0.004 / 0.014 | 0.23 / 0.36 |
| | | start state only | — | 10/10 | 0.015 | 0.56 |
| **S2** | **test** | **frozen** | 256 / 2,048 | **10/10, 10/10** | **0.0087 / 0.0140** | 0.60 / 0.60 |
| | | random angles | 256 / 2,048 | 10/10, 10/10 | 0.0008 / 0.0016 | 0.32 / 0.50 |
| | | plain XY layerwise | 256 / 2,048 | 4/10, 2/10 | ~0 / ~0 | 0.21 / 0.37 |
| | | start state only | — | 1/10 | ~0 | 0.66 |
| **S3** | **test** | **frozen** | 256 / 2,048 | **10/10, 10/10** | **0.0101 / 0.0130** | 0.47 / 0.43 |
| | | random angles | 256 / 2,048 | 6/10, 10/10 | 0.0005 / 0.0012 | 0.39 / 0.44 |
| | | plain XY layerwise | 256 / 2,048 | 6/10, 5/10 | ~0 / 0.0003 | 0.19 / 0.28 |
| | | start state only | — | 0/10 | ~0 | 0.58 |

Uniform sampling over the one-hot sector never found the optimum on S0–S3
(0/10; P(valid) ≤ 0.006).

**Restriction gap.** QAOA reaches each portfolio's optimum; the portfolio
itself is a restriction of the full kitchen:

| Case | Portfolio optimum (U,W,B,R) | Raw CP full-kitchen optimum |
|---|---|---|
| cell | (0, 0, 2, 2) | (0, 0, 2, 2) |
| S0 | (5, 0, 3, 3) | (2, 0, 6, 6) |
| S1 | (7, 0, 1, 1) | (3, 0, 5, 5) |
| S2 | (5, 4, 4, 4) | (2, 1, 6, 6) |
| S3 | (6, 4, 4, 4) | (3, 1, 6, 6) |

### 10.3 Interpretation

- The frozen setup found the portfolio optimum in every seed of every case,
  including both held-out cases.
- Its advantage over random angle search (the pilot's method) at 256 circuits
  grows with difficulty: about 2–5× higher P(opt) on the training cases, about
  11× on S2 and about 22× on S3, where random search also misses the optimum in
  4 of 10 seeds.
- The untrained start state finds the S2/S3 optimum in 1/10 and 0/10 seeds, so
  the held-out result comes from training, not from the initializer. On S1 the
  start state alone already reaches P(opt) 0.015 because S1's optimum cooks a
  single batch, close to the all-idle start.
- Going from 256 to 2,048 circuits adds little (for example S2 0.0087 → 0.0140).
- With 4,096 shots, "hit" saturates for most trained setups; P(opt) per shot
  is the discriminating metric.

### 10.4 Caveats

- Exact simulation of instances with at most 279,936 one-hot states, which a
  laptop also enumerates instantly: a verified method, not a quantum advantage.
- Training used exact probabilities; hardware would give noisy shot estimates.
- The shared QUBO's penalty is 20–213× larger than needed to keep the optimum.
  This mainly hurts single-angle variants (plain XY), so part of the
  multi-angle advantage reflects the shared QUBO's scaling.
- CVaR α = 0.1, warm-start weight 0.85, angle ranges and the energy scale were
  declared, not tuned.
- No matched-budget head-to-head with classical solvers in this document; the
  release's exact optima and SA runs are the references.

## 11. Status

- Adapter, campaign runner and tests: done (all catering tests pass).
- Selection, frozen training runs and the one-time S2/S3 test: done.
- Raw per-run files are large; committed evidence is the plan, summaries,
  run tables, manifests and selection data, with the raw run folders archived
  separately (hashes in the manifests).

## Integration verification and packaging fix

The integrator checked all 400 archived runs: 715,166 returned bitstrings covering
1,638,400 shot counts, exact literal energies, independent physical checks,
training budgets, 1,204 campaign-manifest file hashes and regenerated summaries.
Both held-out frozen setups hit their offered-pool optimum in 10/10 seeds at each
budget. These are independently trained angles per instance; the held-out split
concerns configuration selection, not zero-shot transfer of trained angles.

V1 embedded a stale self-hash in result.json. Campaign manifests are correct and
remain authoritative for those unchanged archives. Adapter v2 fixes future output
packaging with an external artifacts.json; it changes no circuit, optimizer,
loss, budget or sample rule. The exact v1 adapter is retained at
output/catering-methods/qaoa/source-v1/qaoa.py with the plan's original hash, and
the campaign runner selects that frozen source when reproducing plan-v1.
No campaign was retrained for this integration. Review receipt:
output/catering-qaoa-review-v1/verification.json.

Portable verification from any checkout, without the old local audit script's
temporary path or extraction into frozen result folders:

```sh
python scripts/check-catering-qaoa.py --output /tmp/NEW-QAOA-CHECK.json
python scripts/check-catering-qaoa.py --full-samples --output /tmp/NEW-QAOA-FULL-CHECK.json
```

Both verify all archive/campaign hashes and regenerate summaries. The second
also independently decodes every raw return; the default relies on the
hash-verified retained evaluation records. Neither trains or rewrites evidence.
