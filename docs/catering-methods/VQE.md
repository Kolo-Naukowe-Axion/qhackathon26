# Catering VQE method (v3 one-hot bundles)

Owner track: VQE. Code `catering/methods/vqe.py`, tests `tests/catering/test_vqe.py`,
runner `scripts/run-catering-vqe.py`, evidence `output/catering-methods/vqe/`.
Execution kind: `quantum_simulation`, exact ideal expectations, local CPU only.
No IBM, VeloxQ, network service or credit was used.

## Recommended configuration

| Choice | Selected | Why (evidence below) |
|---|---|---|
| Entanglement | one-hot-preserving Givens chains inside every anchor block + **controlled Givens on block pairs that share a QUBO coupling**, L = 2 | beats block-only, random pairs and all pairs under CVaR |
| Gates | real two-choice Givens rotations, controlled Givens across blocks | XY / extra Z phases did not improve these experiments; ZZ phases were slower |
| Loss | **exact CVaR, alpha = 0.1** (alpha = 0.05 equally good) | mean energy is trapped on 4 of 5 cases |
| Optimiser | L-BFGS-B with adjoint gradients | 9-77 evaluations; gradient-free shot methods weaker |
| Start | equal mix of every block's choices (W state), 0.2 rad noise | random angles fail on the cell (2/10) |

Every sample of a one-hot-preserving ansatz satisfies the one-hot constraint by construction;
cross-block physical conflicts are still only penalised, so valid-sample rates are 31-60 %.
The state lives only on the one-hot sector (1,045 to 279,936 amplitudes), which is exact
for these gates (`test_sector_engine_equals_dense_qubit_circuit`).

## Held-out confirmation (predeclared in `E5-predeclaration.json` before running S2/S3)

Seeds (of 10) whose 1,024 final samples contain the valid sector optimum:

| Configuration | S2 | S3 |
|---|---|---|
| **primary: coupled pairs, L=2, CVaR 0.1** | 10/10 | 9/10 |
| coupled pairs, L=1, CVaR 0.05 | 10/10 | 10/10 |
| random block pairs, L=2, CVaR 0.1 | 10/10 | 8/10 |
| block-only, CVaR 0.1 | 9/10 | 6/10 |
| coupled pairs, L=2, mean energy | 0/10 | 0/10 |

## Contract results (primary configuration, seed 0, `method-results/`)

The current five-case release uses `<case>/result.json`, `evaluation.json` and
`artifacts.json`. `solve_qubo(load_bundle(path), {"shots": 1024}, None, fresh_dir)`
selects the recommended configuration and writes a new result directory.

| Case | Qubits | Valid-sample rate | Best valid (U,W,B,R) | Sector reference | Evaluations | Legacy 2P+1 estimate* |
|---|---:|---:|---|---|---:|---:|
| cell | 35 | 0.31 | (0, 0, 2, 2) | (0, 0, 2, 2) | 9 | 13,905 |
| S0 | 33 | 0.43 | (5, 0, 3, 3) | (5, 0, 3, 3) | 77 | 68,145 |
| S1 | 35 | 0.60 | (7, 0, 1, 1) | (7, 0, 1, 1) | 10 | 8,250 |
| S2 | 31 | 0.55 | (5, 4, 4, 4) | (5, 4, 4, 4) | 35 | 25,725 |
| S3 | 35 | 0.44 | (6, 4, 4, 4) | (6, 4, 4, 4) | 18 | 17,910 |

Best samples were checked with `catering.decode.decode`. The S0-S3 fixed portfolios themselves
miss 5/7/5/6 meal lots versus the raw full-kitchen reference 2/3/2/3 (README); that is a
portfolio restriction loss, not a VQE search loss.

*These retained numbers use the original two-shift-per-parameter heuristic. They
are not validated hardware circuit counts. Givens generators have eigenvalues
0 and ±1/2, allowing frequencies 1/2 and 1; a general mean expectation needs a
four-shift rule. CVaR additionally needs probability derivatives, rather than
applying a shift rule directly to the nonlinear scalar CVaR. Actual experiments
used exact simulator adjoints. Gate routing and hardware shot costs are unmeasured.

## Experiments (selection used only cell, S0, S1)

* E1 (310 runs): entanglement ladder with mean energy. Product RY 0/30. With the mean-energy loss
  structure barely matters: S1 easy for all, S0 trapped 13.2k above optimum, cell 0/10 everywhere.
* E2 (560 runs + 40 voided by a guard bug, rerun in E3): optimiser x loss. Exact CVaR + L-BFGS
  takes the cell from 0/10 to 10/10 and S0 to 9/10; under CVaR cross-block coupling beats block-only on S0.
  The sector NFT control used a three-point, single-frequency coordinate update;
  that assumption is not generally valid for these gates. Its rows are retained
  as an exploratory heuristic, not evidence about correctly implemented NFT.
* E3 (410 runs): under CVaR 0.1 on S0, coupled pairs 8/10 (L=2: 10/10) > random pairs 6 > all pairs 4 >
  block-only 3 > product / generic RY+CNOT (shot CVaR) 0. Gate variants 7-9/10. Random start hurts the cell.
* Landscape screen: one-hot sector has only 3-16 single-block-switch local minima but 267-1,280
  single-bit-flip minima, which is why non-preserving ansatzes stall.

## Limitations

* Exact ideal expectations. CVaR here is computed from the exact distribution; with shots
  (SPSA/COBYLA, 1,024 shots) results are weaker. The old circuit estimates are only legacy heuristics.
* "Hit" means the optimum appears among 1,024 samples drawn from the final exact state; CVaR deliberately
  leaves ~40-70 % of the mass on invalid or worse states.
* Seeds are algorithmic repeats on paired cases sharing one prefix, not independent instances.
* No noise model, routing or hardware run; controlled Givens is a 3-qubit gate (Toffoli-class cost).

## Integration check and export fixes

Initial integration from catering-vqe at eaec8ae2. Twelve adapter/engine tests pass. Four retained
S0–S3 MethodResults were normalized by renaming multiplicity to contract count,
then all 4,096 sampled shots were independently evaluated on the exact frozen
bundles. No bits, frequencies, energies, optimizer or circuit changed; no
training was run. Originals remain intact. Normalized results and the check:
output/catering-methods/vqe/integration-v1/.

That initial release lost its cell export through an S0 filename collision.
Main at a3ce2135 then supplied fresh per-case exports for all five cases. The
second integration independently rechecked all 5,120 shot counts against the
raw checker and the retained evaluation files, including the new cell result;
see `output/catering-methods/vqe/integration-v2/verification.json`. Old results
and integration-v1 remain historical evidence. Future exports use fresh result
directories and refuse overwrites before training. The adapter writes count fields.
The original source is retained in source-v1/vqe.py at the predeclared hash.
Held-out CSV counts are source-backed, but per-seed parameters and raw samples
are not archived, so the integration does not claim to have rechecked those
100 training distributions. VQE and QAOA used different budgets and shot counts.

## Replay and model safeguards (adapter v2)

Future MethodResults retain `optimized_parameters`, seed, full Spec, exact
distribution diagnostics, and adapter SHA256. Future grid runs save each
parameter vector in `parameters/` beside the CSV. Existing campaigns are not
rerun or rewritten. `replay_parameters(bundle, Spec(**spec), seed, parameters)`
rebuilds the exact sector probabilities without optimization; match the saved
bundle SHA256 before replay. Random block-pair selection is reproduced by seed.

The adapter now preserves the optimizer's convergence flag instead of marking
every run converged, rejects shot-trained adjoint configurations that previously
silently used an exact loss, and refuses unsupported sector/CVaR three-point NFT.
The primary coupled L2 exact CVaR/L-BFGS configuration and frozen QUBO do not change.

E1/E2 provenance also remains qualified: their source hashes were taken when
the campaign finished, rather than at each worker launch. The teammate's review
reproduced 10 of 12 sampled rows bit-for-bit; two trapped mean-energy runs had
different numerical gaps with the same zero-optimum outcome. See the corrected
manifest provenance notes. This does not establish exact replay of every row.

Tests check fractional CVaR boundary mass, its adjoint gradient against finite
differences, exact dense-circuit agreement, replay without training, and safe
exports. A small coupled circuit also demonstrates why the naive two-shift rule
fails (maximum derivative error 0.0821), while the four-shift identity agrees to
1.2e-15. This is a mathematical simulator check, not a hardware benchmark.

For expectation f and these gate parameters, the checked identity is
`f'(t) = (f(t+pi/2)-f(t-pi/2))/2 + (1-sqrt(2))*(f(t+pi)-f(t-pi))/4`.
It follows by matching the sine/cosine coefficients at frequencies 1/2 and 1.

CVaR with alpha=0.1 can stop improving once 10% of probability is on optimal
states: the lower-tail loss has reached its minimum. Therefore the ~12% held-out
optimal probability is consistent with its loss; it is not a claim of a
deterministic optimum. Changing alpha or optimizing mean energy afterward would
be a new experiment requiring a new selection/evaluation record.
