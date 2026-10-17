# Stage 1: exact makespans, compact QUBOs, quantum runs for both instances

Updated 17 October 2026 (Europe/Warsaw). Current selection:
`output/stage1-selected.json` → `output/stage1-compact-ready/`.

Both official schedules are actual measured QAOA outputs, independently feasible
and globally optimal: **A = 4 h; B = 8 h**. ODRA5 and VeloxQ remain on hold.
Organizer acceptance, repository publication and submission are separate.

| Instance | Selected method | Logical qubits | QAOA layers | Measured optimal samples |
| --- | --- | --- | --- | --- |
| A, 2×2 | QAOA, shared X mixer | 1 | 1 | 4,096 / 4,096 |
| B, 3×3 | QAOA, independent X mixer | 3 | 2 | 4,096 / 4,096 |

Twenty fresh optimization/sampling seeds, 200–219, independently returned
81,920/81,920 optimal measurements **for each instance**, at these settings.
These are fixed-instance, noiseless simulator results, not guarantees, hardware
results, quantum advantage, or evaluation on unseen scheduling instances.

## Why this is stronger than the previous baseline

The retained time-indexed implementation used a four-qubit, p=3 circuit for A and
a 39-variable classical annealer for B. The selected implementation uses genuine
simulator QAOA for both, meeting §4.1 and the preferred method category in §4.2.
It minimizes makespan directly, without supplying H=4 or H=8 to the formulation.

B uses three logical bits instead of 72 naive, 39 pruned or 30 domain-wall bits.
This is a 92.3% reduction relative to the 39-bit model, **with a different state
space**: all common job orders, rather than every allowed timed schedule.
The earlier code, runs and formulation audit remain available as comparisons.

## Variables, decoder and objective

All machines use a common job permutation, a sequence representation explicitly
allowed in challenge §2. For a chosen order, each operation starts as early as
its job predecessor and its machine predecessor permit:

`start(j,m) = max(completion(previous job,m), completion(j,previous machine))`.

This constructs integer, nonoverlapping intervals with all operations once and
correct technological precedence. For any fixed order, later starts cannot
improve makespan in the baseline, which has no release dates or other costs.

For A, `a=1` means Z1 before Z2. Both orders are represented:

`E_A(a) = 4 + a`.

For B, use `a=(Z1 before Z2)`, `b=(Z1 before Z3)`, `c=(Z2 before Z3)`:

`E_B(a,b,c) = 9 - a + 3b - c - 2ab + 3ac - 3bc`.

| abc, in variable order | Common order | Energy | Decoded makespan |
| --- | --- | --- | --- |
| 000 | Z3, Z2, Z1 | 9 | 9 h |
| 001 | Z2, Z3, Z1 | 8 | 8 h |
| 010 | cyclic | 12 | rejected |
| 011 | Z2, Z1, Z3 | 8 | 8 h |
| 100 | Z3, Z1, Z2 | 8 | 8 h |
| 101 | cyclic | 10 | rejected |
| 110 | Z1, Z3, Z2 | 9 | 9 h |
| 111 | Z1, Z2, Z3 | 8 | 8 h |

The upper-triangular B coefficient matrix is
`[[-1,-2,3], [0,3,-3], [0,0,-1]]`, with separate offset 9.
For valid assignments, **energy equals makespan**, rather than zero indicating
feasibility. A feasible 9 h sample remains feasible and is counted separately
from an optimal sample. Cycles are rejected, never sorted into a repaired answer.

## How coefficients are constructed, and what it costs

`solver/sequence.py` computes the earliest-start makespan for **every** one of the
2! or 3! common orders. The construction uses no independent reference answer,
known optimum horizon, answer-dependent pruning or solution warm start.

For three jobs, the eight-entry truth table has six fixed valid costs and two
free cyclic-state costs. Initially assign both cycles `M=max(valid costs)+1`.
The cubic coefficient of the Boolean polynomial is

`d = E111 - E110 - E101 - E011 + E100 + E010 + E001 - E000`.

Raise E010 by `max(0,-d)` and E101 by `max(0,d)`. This cancels the cubic term
exactly while both cycles remain strictly worse than every valid order. The
integer Boolean Möbius transform then produces the constant, linear and quadratic
coefficients. For B, M=10 and d=-2, giving E010=12 and E101=10.

This method supports exactly two or three jobs. **Its factorial classical cost
construction already reveals the permutation optimum.** It is an inspectable,
exact encoding for the tiny mandated baselines, not a scalable quantum scheduling
algorithm or a claim that quantum computation was needed. The one-qubit A
circuit has no entangling gate. The older four-qubit A remains a richer circuit
demonstration. Stage 2 requires its own formulation and evidence.

## Exact scope and minimality

Every common job order has a distinct state: two orders need at least one bit;
six orders need at least `ceil(log2(6))=3` bits. The selected QUBOs meet those
information bounds with no auxiliary bits. This is a minimum **within that
order-preserving representation requirement**, not an unrestricted minimum over
encodings that discard orders, bake in an answer or identify equal-cost states.

The representation excludes independent orders on different machines and
additional idle-time variants. The full independent reference enumerates **all
4 machine-order combinations for A and all 216 for B**, computes earliest starts
for acyclic combinations, and verifies that their optima are also 4 and 8 h.
Every feasible nonpreemptive schedule induces one such machine-order combination;
earliest starts cannot worsen its makespan. Therefore the selected domain loses
no better schedule on either official instance. No broad dominance theorem is
needed for these certificates.

`output/stage1-compact-ready/formulation-certificates.json` retains every compact
bitstring energy, decoded makespan and the independent references. Tests also
check all bitstrings for 40 deterministic random-duration two/three-job instances;
these test encoding correctness, not quantum-solver generalization or global
permutation dominance for arbitrary extensions.

## Iteration, selection and matched comparison

Eleven settings were screened on seeds 0,1,2. Every attempted setting and its
samples/angles remain in `output/stage1-compact/screen/`:

| B quantum configuration | Optimal measurements in screening |
| --- | --- |
| p=1, shared X, 8 restarts | 80.583% |
| p=1, independent X, 8 restarts | 95.207% |
| p=2, shared X, 8 restarts | 99.626% |
| p=2, independent X, 2 / 4 / 8 restarts | 100% for each setting |
| p=3, independent X, 4 restarts | 100% |

Two layers retain the observed quality of three with fewer cost gates. At p=2,
B uses 6 RZZ, 6 RZ and 6 RX gates, 3 initial H gates, and 8 trainable angles.
The selected budget retains eight random BFGS restarts, maxiter=500 each.

Seven settings then used fresh seeds 200–219, with all outcomes retained in
`output/stage1-compact/validation/`. The 2/4/8-restart B variants each produced
81,920/81,920 optimal measured shots. The two-restart variant's worst ideal
ground-state probability was approximately 0.99998991; four and eight restarts
reached at least 0.99999999999986. Eight is a conservative training budget;
four matched its observed validation quality at less training cost. Neither
budget offers a guarantee for arbitrary seeds. A used one restart and two angles.

The same three-bit B QUBO was also sampled by classical simulated annealing with
16,64,256 geometric sweeps. Every setting gave 10,240/10,240 optimal samples
over the twenty seeds. The retained 256-sweep comparison is deliberately cheap:
its median sampler work was about 0.0032 s, compared with 1.35 s for selected B
QAOA training/sampling. These timings exclude imports, cost construction, evidence
writing and verification, and are not an end-to-end benchmark. Classical
solution of this tiny problem is straightforward.

## Evidence and independent acceptance

Each run retains model, samples including failures, official schedule, replay,
method/settings, timestamps, package versions and input/model/source hashes.
Quantum runs additionally retain actual Aer measurement counts, QASM, circuit
text, trained angles and losslessly compressed optimization history. Each
experiment phase retains a source snapshot. All solver runs block socket
connections, and use no service credential.

The verifier rebuilds the model from the official instance, checks every sample
and interval, reconstructs circuit probabilities/energy from saved angles,
reconciles raw shot counts, and checks compact-run QASM. Tamper tests cover
model replacement even with a recomputed hash, angles, counts and QASM. This
establishes internal evidence consistency, not independent authentication of
execution. Python and browser interval checkers validate both selected exports.

## Reproduction

Use the existing pinned Python 3.11 solver environment, or install from
`requirements-solver.lock.txt` as in the README. Choose fresh output directories:

```sh
.venv/bin/python scripts/prepare-stage1.py --output output/new-stage1
# Export only after the bundle verifies; also refreshes guide evidence:
.venv/bin/python -m solver.compact --phase bundle --output output/new-compact --export-final
.venv/bin/python -m solver.compact --phase screen --output output/new-compact-screen
.venv/bin/python -m solver.compact --phase validate --output output/new-compact-validation
.venv/bin/python -m solver.verify --run output/stage1-compact-ready/quantum-2x2
.venv/bin/python -m solver.verify --run output/stage1-compact-ready/quantum-3x3
```

`scripts/prepare-stage1.py` runs the solver tests, original time-indexed encoding
audit and a compact bundle. `--time-indexed` reproduces the older 4/39-bit methods.
No remote adapter is invoked by default. Both root schedule files and the
selection manifest refer to the selected quantum samples; the browser guide
uses their actual metadata. Nothing here establishes a physical-device or
VeloxQ result, event submission, or completion of the wider human deliverables.

Final verification (17 October): all 179 retained compact run bundles pass the strengthened verifier and every run returns an exact optimum. Full preparation reproduces both required quantum schedules and the 512,000-assignment legacy audit. All 26 core Python tests pass (2 optional IQM tests skipped), all 52 Node tests and the static build pass, and the local browser renders the selected quantum panels and compact formulas correctly. Automatic guide evidence regeneration matches the checked public summary exactly.
