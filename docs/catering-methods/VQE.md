# Catering VQE method (v3 one-hot bundles)

Owner track: VQE. Code `catering/methods/vqe.py`, tests `tests/catering/test_vqe.py`,
runner `scripts/run-catering-vqe.py`, evidence `output/catering-methods/vqe/`.
Execution kind: `quantum_simulation`, exact ideal expectations, local CPU only.
No IBM, VeloxQ, network service or credit was used.

## Recommended configuration

| Choice | Selected | Why (evidence below) |
|---|---|---|
| Entanglement | one-hot-preserving Givens chains inside every anchor block + **controlled Givens on block pairs that share a QUBO coupling**, L = 2 | beats block-only, random pairs and all pairs under CVaR |
| Gates | real RY-type Givens (2 CNOT + RY each), controlled Givens across blocks | XY / extra Z phases add nothing; ZZ phases ~10x slower, no better |
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

| Case | Qubits | Valid-sample rate | Best valid (U,W,B,R) | Sector reference | Evaluations | Parameter-shift circuits |
|---|---:|---:|---|---|---:|---:|
| cell | 35 | 0.31 | (0, 0, 2, 2) | (0, 0, 2, 2) | 9 | 13,905 |
| S0 | 33 | 0.43 | (5, 0, 3, 3) | (5, 0, 3, 3) | 77 | 68,145 |
| S1 | 35 | 0.60 | (7, 0, 1, 1) | (7, 0, 1, 1) | 10 | 8,250 |
| S2 | 31 | 0.55 | (5, 4, 4, 4) | (5, 4, 4, 4) | 35 | 25,725 |
| S3 | 35 | 0.44 | (6, 4, 4, 4) | (6, 4, 4, 4) | 18 | 17,910 |

Best samples were checked with `catering.decode.decode`. The S0-S3 fixed portfolios themselves
miss 5/7/5/6 meal lots versus the raw full-kitchen reference 2/3/2/3 (README); that is a
portfolio restriction loss, not a VQE search loss.

## Experiments (selection used only cell, S0, S1)

* E1 (310 runs): entanglement ladder with mean energy. Product RY 0/30. With the mean-energy loss
  structure barely matters: S1 easy for all, S0 trapped 13.2k above optimum, cell 0/10 everywhere.
* E2 (560 runs + 40 voided by a guard bug, rerun in E3): optimiser x loss. Exact CVaR + L-BFGS
  takes the cell from 0/10 to 10/10 and S0 to 9/10; under CVaR cross-block coupling beats block-only on S0.
* E3 (410 runs): under CVaR 0.1 on S0, coupled pairs 8/10 (L=2: 10/10) > random pairs 6 > all pairs 4 >
  block-only 3 > product / generic RY+CNOT (shot CVaR) 0. Gate variants 7-9/10. Random start hurts the cell.
* Landscape screen: one-hot sector has only 3-16 single-block-switch local minima but 267-1,280
  single-bit-flip minima, which is why non-preserving ansatzes stall.

## Limitations

* Exact ideal expectations. CVaR here is computed from the exact distribution; with shots
  (SPSA/COBYLA, 1,024 shots) results are much weaker. Hardware counts are parameter-shift equivalents, not runs.
* "Hit" means the optimum appears among 1,024 samples drawn from the final exact state; CVaR deliberately
  leaves ~40-70 % of the mass on invalid or worse states.
* Seeds are algorithmic repeats on paired cases sharing one prefix, not independent instances.
* No noise model, routing or hardware run; controlled Givens is a 3-qubit gate (Toffoli-class cost).
