# Stage 1: verified local solvers

Updated 2026-10-16. Both mandatory method requirements have been exercised locally: A by QAOA on a simulator, B by classical QUBO simulated annealing. Exported makespans are 4 h and 8 h, independently verified optimal. No VeloxQ service or physical ODRA5 run is claimed.

## Reproduce

The standard-library formulation/reference export still works with `python3 -m solver.stage1`. For the actual solver bundle:

```sh
uv venv --python 3.11 .venv
uv pip sync --python .venv/bin/python requirements-solver.lock.txt
.venv/bin/python scripts/prepare-stage1.py --output output/stage1-reproduction
```

Choose a new output directory per run. Add `--export-final` to export verified schedules to the root `schedule_2x2.json` and `schedule_3x3.json`, and update the selection manifest at `output/stage1-selected.json`. The default command runs local solvers and the formulation audit; it does not invoke either remote adapter or prepare SDK packets. Both ODRA5 and VeloxQ are on user hold. Current evidence is in `output/stage1-local-ready/`; earlier runs remain in `output/stage1-ready/`.

```sh
.venv/bin/python -m solver.verify --run output/stage1-local-ready/qaoa-2x2
.venv/bin/python -m solver.verify --run output/stage1-local-ready/anneal-3x3
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

Import the selected run's `replay.json` into the viewer to show actual samples. Built-in viewer choices remain illustrations. Python and the browser's independent interval checker both validate actual exports.

## Fixed-horizon QUBO

Allow integer starts in `[sum(predecessor durations), H - sum(duration of this operation and its successors)]`. These chain bounds remove only impossible starts.

`E = sum_o (sum_t x(o,t) - 1)^2 + sum_machine_conflicts x(a)*x(b) + sum_precedence_conflicts x(a)*x(b)`.

Exactly-one expansion gives offset 1 per operation, linear coefficient -1 per start, and coefficient 2 between starts of one operation. Capacity terms penalize overlapping half-open intervals; precedence terms penalize adjacent job operations violating completion order. All weights are one. E=0 iff the schedule is feasible inside H. Empty domains retain an unsatisfied constant.

Makespan optimization is an outer horizon search. For these tiny baselines we independently certify the optimum, then solve the QUBO at that horizon. A heuristic failure does not prove infeasibility. The reference enumerates independent orders on every machine (4 combinations for A, 216 for B), rejects cycles, and computes earliest starts. Every feasible schedule induces these orders, so this covers non-permutation schedules too. It is factorial and intentionally limited to tiny problems.

## Compact encoding and correctness

One-hot models have 8 variables for A at H=4 and 39 for B at H=8. Domain-wall encoding uses d-1 bits for d starts: `x_0=1-y_0`, `x_t=y_(t-1)-y_t`, `x_last=y_last`. Monotone y selects exactly one start. Counts become 4 and 30, preserving every allowed operation-start assignment.

Remove the exactly-one polynomial and substitute indicators into conflict terms only; retain a constant for each empty domain. Substituting the binary-simplified exactly-one polynomial would be incorrect on invalid walls, where an indicator can be -1 and `x*x=x` fails. This was corrected during review. Earlier experimental compact packets in `output/stage1/` are superseded by `output/stage1-ready/`.

Add `P * sum_k (1-y_k)*y_(k+1)`. Let D be the largest weighted conflict degree of any start indicator; choose P=D+1. Every rising wall produces one negative indicator. Negative conflict energy can be charged to negative endpoints, totaling at worst -D per rising wall. Thus invalid-wall energy is at least the number of rising walls, strictly positive. On valid walls energy equals the original conflict count. For B, P=10. Fewer variables cost larger coefficients; this is not a smallest-QUBO or novelty claim.

Checks include every 2×2 bitstring, exhaustive invalid-wall checks on small models with larger domains, and all 512,000 one-start-per-operation assignments for B at H=8. Both encodings agree with the direct constraint checker; 13 assignments are feasible. This does not enumerate all 2^30 or 2^39 arbitrary bitstrings; the structural penalty proof covers invalid walls.

## QAOA execution

The four-qubit circuit starts in |+> and alternates `exp(-i gamma E/scale)` with X rotations. The shared mixer uses one beta per layer; the improved `local-x` variant uses an independently trained beta for each qubit and layer. Dimod uses `s=2x-1`, opposite to Qiskit's Z eigenvalue; cost gates are `RZ(-2 gamma h/scale)` and `RZZ(2 gamma J/scale)`. Tests independently check the cost phase and qubit-specific mixer action on all basis amplitudes.

Selected settings: p=3, `local-x` mixer, sixteen BFGS restarts, 500 iterations per restart, seed 2026, 4,096 Aer shots. Optimization minimizes mean QUBO energy. The full diagonal computes simulator expectations; it is not used to replace returned samples. Circuit QASM, parameters, optimizer histories/statuses, counts, hashes, versions and selected schedule are retained. Ten new validation seeds each produced 4,096/4,096 valid measurements. The verifier reconstructs the quantum state from saved angles and reconciles raw counts against the retained samples and shot budget. These results apply to this tiny simulator instance, not unseen instances or physical hardware.

The selected B solver uses one-hot encoding at H=8, 512 reads and 32,000 sweeps with the sampler's default beta range and a linear cooling schedule. Ten new validation seeds produced 5,110/5,120 valid samples; every run returned an 8 h optimum. The exported seed-2026 run has 511/512 valid samples. This takes more sampling work than the old 2,000-sweep baseline. See [STAGE1_REFINEMENT.md](STAGE1_REFINEMENT.md) for settings, comparisons and reproduction.

## VeloxQ handoff

The initial remote candidate is the 39-variable one-hot model at H=8, with 512 repetitions and 2,000 steps as an initial budget, not tuned VeloxQ parameters. Ten local seeds found an optimum every time for both encodings; one-hot had a higher feasible-sample rate and smaller coefficients. Local performance does not predict the remote solver. The 30-variable candidate is ready for comparison.

`to_dimod` creates BINARY variables in canonical order before adding edges. SDK 1.0.0 converts to SPIN and writes HDF5. Tests check labels, coefficients and energy preservation; the actual SDK result parser is exercised with synthetic HDF5 fixtures, including shuffled labels. Decoder respects vartype/labels, recomputes energies and independently checks schedules. Only a consistent, explicitly recorded omission of the Ising constant is allowed as an energy-convention difference.

Prepare a packet without a token:
```sh
.venv/bin/python -m solver.velox --output output/new-velox-packet
```

**Current hold:** the user reports obtaining access and setting `VELOX_TOKEN`, but explicitly forbids using VeloxQ yet. Do not run a connectivity test, upload or submit until the user lifts this hold. The following is a future command only, after authorization and reviewing team connection instructions:
```sh
.venv/bin/python -m solver.velox --submit --output output/stage1-ready/velox-3x3
```

Use `--backend-id` only with a provided id; `VELOXQ_API_URL` supports an instructed endpoint override. The SDK-default backend remains unverified for the team. Submission saves the job id immediately. `--resume` retrieves that job without resubmitting. Waiting failures retain the id; ambiguous submission failures are not automatically retried. After real success, use `solver.verify --run ... --export schedule_3x3.json` to export the actual VeloxQ result.

Authentication, quota, backend availability and real result behavior remain unverified. The [official SDK](https://github.com/quantumz-io/veloxq_sdk) provides physics-inspired/metaheuristic optimization; a GPU call does not establish quantum/hybrid execution. Challenge §4.2 permits classical QUBO solvers for B, while §4.1 separately requires a quantum algorithm for A, including simulation.

Challenge §16 says one team representative requests access after kickoff and team declaration: to `support@veloxq.com`, cc `contact@qaif.org`, subject `QPoland QUANTUM HACKATHON 2026`. No email was sent here. See [ODRA5.md](ODRA5.md) for physical hardware preparation.
