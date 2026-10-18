# VeloxQ owner: larger workloads on the shared catering model

Updated 17 October 2026. **The scale track is part of the same project.**
The 35-qubit complete cell is for correctness and direct cross-method comparison;
it is not the main VeloxQ workload. The owner should evaluate larger coupled
paired-meal QUBOs and show what that changes operationally.

## Inputs already prepared offline

Start with `catering/README.md` and `docs/CATERING_SOLVER_CONTRACT.md`.
After pulling, restore the losslessly compressed large matrices:

```sh
node scripts/restore-compressed-evidence.mjs
```

| Tier | Frozen input | Actual data variables | Couplers | Purpose |
|---|---|---:|---:|---|
| Shared complete cell | output/catering-complete-cell-v3/quantum-qubo.json | 35 | 520 | Correctness; same input as the quantum methods |
| Integration | output/catering-foundation-v3/S0..S3/scale-128-qubo.json and scale-256-qubo.json | 128 / 256 | See each bundle | Offline adapter checks and four-event comparisons |
| Scale 1 | output/catering-velox-scale-v3/scale-512-qubo.json | 512 | 37,008 | Larger paired-meal problem |
| Scale 2 | output/catering-velox-scale-v3/scale-1024-qubo.json | 1,024 | 156,129 | Same raw input, nested offered programs |
| Scale 3 | output/catering-velox-scale-v3/scale-2048-qubo.json | 2,048 | 636,882 | Largest currently prepared tier |

The scale release uses **12 customer orders plus the committed meal and an urgent
order**, S3, with both courses, shared batch yields, resource/worker conflicts,
fixed handovers, freshness, the outage and mandatory recovery clean. Its full
generated local domain contains **18,182 programs**, across **26 anchor blocks**.
The prepared tiers are nested, lossy restrictions of that domain. Variables
include idle choices: 486+26, 998+26 and 2,022+26. These are QUBO variable counts,
not a request to simulate equally wide quantum circuits.

Graph density is measured at approximately 28.3%, 29.8% and 30.4%. **Do not
advertise these matrices as sparse or assume VeloxQ will win.** Enlarging the
number of orders is a separate scale axis from retaining more programs per
order. Do not add disjoint duplicate kitchens to inflate a variable count.

## What was actually run

Input preparation only: local generation, checking and CP-SAT references, with no
VeloxQ or IBM call at this stage. Later service jobs (137 ledger attempts) are
reported from Phase C onward and in the follow-up conditioning experiment.
Five-second, one-worker reference budgets were declared before the run:

| Width | Offered-domain CP status | Checked (U,W,B,R) |
|---:|---|---|
| 512 | FEASIBLE | (7,2,10,10) |
| 1,024 | FEASIBLE | (8,8,10,10) |
| 2,048 | UNKNOWN | No CP incumbent returned |

A separately checked all-idle witness is provided at every width. It is a
feasibility witness, not an optimizer result. The independent raw-grid CP run
returned FEASIBLE (8,1,7,7) under its five-second budget. Neither that run nor
these finite-budget offered-domain results certify an optimum or hardness.
A poorer incumbent at a larger width is possible under a fixed search budget;
only the unknown true nested-domain optimum is guaranteed not to worsen.

Read report.json, experiment-plan.json, *-reference.json, *-witness.json and
manifest.json for hashes, bounds, timing, actual sizes and limitations.

### Stronger local controls (additional frozen run)

`output/catering-classical-scale-v3/` retains a separate predeclared 30-second,
one-worker CP pass and two-second cold literal-QUBO SA controls, seed2026.
The original five-second receipts remain unchanged. The longer raw CP run is
FEASIBLE (5,1,11,11), **not certified optimal**.

| Width | 30-second offered CP | Checked (U,W,B,R) | Cold SA |
|---:|---|---|---|
| 512 | FEASIBLE | (6,1,10,10) | Best valid returned tuple (12,15,9,9) |
| 1,024 | FEASIBLE | (7,2,11,11) | Best valid returned tuple (12,12,9,9) |
| 2,048 | FEASIBLE | (8,3,8,8) | No valid returned state |

These are reference incumbents, not target optima or evidence that classical
methods cannot do better. Cold SA starts from unrestricted random bits; it is
not the same initializer/sector as XY-QAOA. Raw feasibility and scope must
accompany any comparison. Runtime caps, loader time and whole-call wall times
are recorded separately; solver/presolve/scheduler overhead may exceed a nominal
cap. No VeloxQ, hardware or remote compute was used.

Reproduce into a new directory:

```sh
.venv-stage2/bin/python -m catering.benchmark_meal_scale \
  --output output/NEW-CLASSICAL-SCALE
```

## Owner deliverables and service gate

1. Build and test the offline adapter on the shared small case. Preserve semantic
   bit order, offsets and literal integer energies; report invalid raw returns.
2. Load the larger inputs above without silently truncating or decomposing them.
   Inspect the backend's coefficient precision and actual upload/size constraints.
3. Prepare a **capped pilot manifest**: exact bundle hashes, job count, repeats,
   settings, requested solutions, maximum credits/runtime and no automatic retries.
   Begin with one scale tier, then escalate only within the approved cap.
4. **Do not upload or execute until the user explicitly releases the service hold.**
   This handoff does not authorize account usage. No credentials are needed to
   prepare the adapter, payloads and estimate.
5. On authorized runs, save raw responses/failures, actual account usage and all
   preprocessing/upload/solve/download/check times. Independently decode every
   returned sample before comparing operational tuples.
6. Compare against the same literal-QUBO SA control and the supplied offered-domain
   reference. The independent raw-grid reference assesses representation loss;
   it is not the same-matrix performance baseline.

The new scale inputs use tighter, proven feasible anchor bounds for lexicographic
weights. This preserves the same ordering of (U,W,B,R), while reducing unnecessary
coefficient growth. The encoding, physical rules and priority order are unchanged.
Hashes/energies differ from earlier bundles: compare operational tuples across
bundles, and use identical coefficients for methods on a given bundle. The
compiler still chooses P above the absolute nonconstant objective span.
The conservative absolute energy bounds for these three inputs are below 2^53,
but floating normalization, backend arithmetic and resolution still require
validation; binary64 exact integer range alone does not certify a solver.

## Reproduce or extend locally

```sh
.venv-stage2/bin/python -m catering.meal_scale \
  --output output/NEW-VELOX-SCALE \
  --customers 12 --scenario S3 --widths 512 1024 2048 \
  --reference-seconds 5
```

This calls no service. Output directories must be new. The generator checks every
local program, retains every anchor, validates the literal bundle and idle witness,
records actual density/coefficient ranges, and stops at a declared coupler guard.
No exact-sector enumeration is attempted on the large tiers.

Further 4,096-variable or 24-customer cases are **optional next workloads**, not
already generated or required before the other owners begin. Check local memory,
coefficient ranges, upload constraints and the agreed account cap first. A
well-measured 2,048-variable study is preferable to an unsupported size claim.

---

## Owner status (Person 1, 17 October 2026)

**Deliverables 1–3 are done; phase D steps 1–4 have run** (user approval
17 October 2026, ledger total 20: the phase C smoke, three scale tiers,
eight four-event integration bundles and five shared small QUBOs, one
user-approved repeat of S3 quantum after a connection failure, and two post-hoc
longer runs). See "Phase D result". A post-hoc local-penalty study (phase E)
brought the ledger to 30, a low-conflict pool study (phase F) to 34, a
parameter study (phase G) to 42 and new cost functions on the largest problems
(phase H) to 54. See phases E–H below and the handoff in
[VELOXQ_HANDOFF.md](VELOXQ_HANDOFF.md).

| Path | Content |
|---|---|
| `catering/methods/veloxq.py` | Adapter 0.2.0: `solve_qubo(bundle, budget, method_config, output_dir)` and CLI |
| `tests/catering/test_veloxq_adapter.py` | 66 offline tests, no token or network |
| `output/catering-methods/veloxq/pilot_manifest.json` | Caps, frozen settings, case hashes, baselines and comparison declared before results |
| `output/catering-methods/veloxq/offline-readiness-v3.json` | One `not_run` record per released v3 bundle (16), with sizes, coefficient ranges, packet dtype/size and timings |
| `output/catering-methods/veloxq/job_ledger.json` | Every attempted service submission (currently 54) |
| `output/catering-methods/veloxq/smoke-20261017T162002/` | Phase C raw input/output and result |
| `output/catering-methods/veloxq/paired-*-*/` | Phase D/E runs: raw packet, raw result, `result.json` and shared-checker `evaluation.json` |
| `catering/methods/veloxq_penalty.py`, `veloxq_penalty_sa.py` | Phase E: local-penalty variant builder and same-SA comparison |
| `tests/catering/test_veloxq_penalty.py` | 17 offline tests for the variants |
| `catering/methods/veloxq_lowconflict.py`, `output/catering-methods/veloxq/lowconflict-v1/` | Phase F: low-conflict pools, CP references, SA results |
| `output/catering-methods/veloxq/penalty-study-v1/` | Phase E variant bundles, `sa-plan.json`, `sa-comparison.json`, per-run SA results |

### Conventions (checked by tests)

- Input: literal integer QUBO (`constant`, `linear`, `quadratic`, `variable_order`)
  from the bundle's top level or a `qubo` object. Malformed, non-canonical or
  duplicate entries are rejected. Variable order and bundle hash pass through.
- Spin form sent to VeloxQ: `s = 2x - 1`, scaled by 4 so it stays integral:
  `h_i = 2a_i + sum_j b_ij`, `J_ij = b_ij`, `offset = 4c + 2*sum a + sum b`,
  `E_spin = 4E` exactly. This equals the foundation's Pauli-Z form
  (`z = 1 - 2x = -s`) with the linear sign flipped; a test checks this on every
  frozen bundle.
- Returned rows: labels must be exactly `0..n-1`; SPIN or BINARY values. Each
  reported energy must equal `4E` (full model) or `4E - offset`, consistently,
  within a tolerance set by the returned dtype. Otherwise the job is `failed`.
  Literal energies are always recomputed exactly; no repair.

### Coefficient precision (deliverable 2)

The SDK's HDF5 writer (veloxq-sdk 1.0.0) stores coefficients as **float32
unless it receives Python integers**, in which case it picks an exact integer
dtype. On the v3 scale bundles, 90–100% of spin coefficients are not
representable in float32 (dynamic range up to 1.7e8 at width 2,048), so a float
packet would silently solve a rounded model. Adapter 0.2.0 therefore:

- sends exact integer packets (int32/int64; 20.6 MB at width 2,048),
- re-reads every packet and refuses upload unless it equals the model exactly,
- records `packet_coefficient_dtype`, `float32_inexact_spin_coefficients`,
  `spin_dynamic_range` and `spin_l1` in each result,
- accepts float32 returned energies (VeloxQ returns them; phase C did) with a
  dtype-scaled tolerance, still rejecting shifts beyond rounding.

Phase D answered the first question: the service accepted the exact integer
packets for every phase D bundle (int64), and every reported energy matched
the exact model within the float32 tolerance. The backend's internal arithmetic
remains unverified and is a possible cause of the weak results below.

### Phase C smoke result

Contract section 5 example, one job, 60 s, no retries:
`job_id 717caf69-b5c0-4b90-bd5c-a2ce846f7058`, backend `VeloxQH100_1`,
`num_rep=512`, `num_steps=2000`. Best `[1,0]`, E = -4 (454/512 rows); `[0,1]`,
E = -3 (58 rows). Quota 46, solver cost 0.55, total cost 0.0; running 0.046 s,
pending 0.73 s; end-to-end 6.39 s (upload 2.04, backend wait 3.20).
Energy convention: **SPIN, Ising offset omitted** (`reported = 4E - offset`),
float32 energies. This result predates the v1 schema alignment and stays in the
draft schema.

### Result format

`result.json` follows `catering-method-result.v1` (`catering/contracts.py`) and
is accepted as-is by `python -m catering.run evaluate`. VeloxQ-specific fields
(`bundle` identity, `budget`, `representation`, `failure`, `backend_statistics`,
`backend_timeline`, per-sample `reported_energy_spin_scaled`) are kept alongside.
The shared-checker gate above was run on the adapter's offline results for the
complete cell, scale-512 and scale-2048 (accepted; no samples, status `not_run`),
and on fake-service results with samples in the tests. This machine has no
`.venv-stage2`; `.venv` was used.

### Offline verification on released inputs

All 16 bundles (complete cell; v3 S0–S3 quantum/scale-128/scale-256;
scale-512/1024/2048) plus the v2 regression `complete-qubo` files:

- literal energy equals `catering.qubo.energy`, spin energy equals `4E`,
- every sample in v3 `*-reference.json` and `*-sa.json` recomputes to its
  stated energy,
- fake service runs on v3 S1 quantum/scale-128/scale-256, returning reference,
  SA and random rows with float32 energies, pass `catering.run evaluate`, with
  the reference solution ranked first and decoded valid.

Build + serialize + exact re-read takes 2.6 s at width 2,048 (local CPU).

### Frozen baselines (before any VeloxQ result)

| Bundle | Vars | Offered-domain CP | Same-QUBO cold SA |
|---|---:|---|---|
| v3 S0–S3 scale-128 | 128 | OPTIMAL (E 7.83e6–1.04e7) | best E 1.66–1.75× optimum |
| v3 S0–S3 scale-256 | 256 | 3 OPTIMAL, S0 FEASIBLE (gap to bound) | best E 1.25–2.5× incumbent; some returns invalid |
| scale-512 | 512 | 30 s FEASIBLE, E 237,205, (6,1,10,10) | best valid E 483,579, (12,15,9,9); 4/4 valid |
| scale-1024 | 1,024 | 30 s FEASIBLE, E 277,328, (7,2,11,11) | best valid E 481,392, (12,12,9,9); 1/1 valid |
| scale-2048 | 2,048 | 30 s FEASIBLE, E 317,339, (8,3,8,8) | no valid returned state |

Scale-tier rows use the stronger controls in `output/catering-classical-scale-v3/`
(30 s one-worker CP, 2 s cold SA, seed 2026). Their bundle hashes were checked
to equal the frozen scale bundles, and every returned sample recomputes to its
stated literal energy. None of these incumbents is a certified optimum. Exact
values and hashes are in `pilot_manifest.json`.

### Phase D result

#### Steps 1–2: scale tiers

One cold-start job per width, `num_rep=512`, `num_steps=2000`, 60 s, no retries
and no tuning. Every returned row was decoded by `catering.run evaluate` with
repair off (`evaluation.json` in each run directory).

| Width | Job | Valid rows | Best valid E | Best valid (U,W,B,R) | Running / end-to-end | Quota |
|---:|---|---:|---:|---|---|---:|
| 512 | 8e8a89bc… | 5 / 512 | 516,244 | (13,6,4,4) | 0.17 s / 8.0 s | 170 |
| 1,024 | 64cf8366… | 1 / 512 | 557,068 | (14,8,4,4) | 0.55 s / 8.0 s | 549 |
| 2,048 | 5c6e1a25… | 0 / 512 | — | — | 1.93 s / 14.2 s | 1,930 |

Solver cost was 0.55 per job; total cost was reported as 0.0.

Against the frozen baselines, under these settings VeloxQ is **worse than every
classical control**. At 512 it beats the all-idle witness (E 551,853, U=14), but
not cold SA (E 483,579) or 30 s CP (E 237,205). At 1,024 its only valid state is
worse than all-idle. At 2,048 it returns no valid state, the same as cold SA.
Most rows break one-hot groups: the lowest returned energy at 2,048 is 1.5e10,
dominated by the penalty. This is one untuned setting per width, with a backend
running time of 2 s or less. It shows the penalty-heavy matrices are hard for
default settings; it does not measure VeloxQ's best attainable quality.

#### Steps 3–4: four-event integration and shared small QUBOs

Same frozen settings and shared-checker decode. Reference columns come from
`pilot_manifest.json` (offered-domain CP and cold SA, both frozen before results).

| Bundle | Vars | Valid rows | Best valid E | (U,W,B,R) | Offered CP E | Cold SA best E |
|---|---:|---:|---:|---|---:|---:|
| S0 scale-128 | 128 | 29 / 512 | 13,093,156 | (5,3,4,4) | 7,832,094 opt | 13,093,273 |
| S1 scale-128 | 128 | 15 / 512 | 18,285,487 | (7,0,1,1) | 7,876,266 opt | 13,100,543 |
| S2 scale-128 | 128 | 18 / 512 | 13,100,845 | (5,2,4,4) | 7,858,194 opt | 13,128,459 |
| S3 scale-128 | 128 | 22 / 512 | 15,685,314 | (6,4,4,4) | 10,435,105 opt | 18,303,864 |
| S0 scale-256 | 256 | 3 / 512 | 147,471,652 | (6,5,4,4) | 49,059,134 feas | 122,883,529 |
| S1 scale-256 | 256 | 1 / 512 | 198,883,830 | (8,4,2,2) | 74,494,866 opt | 149,222,044 |
| S2 scale-256 | 256 | 1 / 512 | 171,551,696 | (7,2,1,1) | 49,041,901 opt | 122,752,355 |
| S3 scale-256 | 256 | 6 / 512 | 197,046,513 | (8,1,0,0) | 98,554,001 opt | 123,295,532 |
| complete cell | 35 | 26 / 512 | 53,429 | (1,1,2,2) | 68 opt | — |
| S0 quantum | 33 | 500 / 512 | **66,216** | (5,0,3,3) | 66,216 opt | — |
| S1 quantum | 35 | 505 / 512 | **101,893** | (7,0,1,1) | 101,893 opt | — |
| S2 quantum | 31 | 464 / 512 | **63,684** | (5,4,4,4) | 63,684 opt | — |
| S3 quantum (repeat) | 35 | 494 / 512 | **103,668** | (6,4,4,4) | 103,668 opt | — |

The first S3 quantum attempt failed with `ConnectError` before a job was created
(`job_id` null, zero VeloxQ calls). It counts in the ledger. The user approved one
manual repeat with identical settings (ledger total 18); the row above is that repeat.

Each job's backend running time was 0.05–0.09 s, its end-to-end time 4.2–6.7 s,
its quota 47–89 and its solver cost 0.55.

Reading: on all four 31–35-variable four-event QUBOs, VeloxQ reaches the
CP-certified optimum (S0–S3 quantum: 11, 16, 1 and 4 rows), with 91–99% valid rows. On the
35-variable complete cell, only 5% of rows are valid and the best is far from
the optimum (53,429 vs 68). At 128 variables it never reaches the optimum, but it
beats cold SA's best on S0, S2 and S3 (S1 is worse). At 256 variables and above it
is worse than cold SA on every bundle. Valid-row rates fall steeply with width
(about 3–6% at 128, at most 1.2% at 256 and above). The same caveat applies: one untuned
setting and sub-second backend time.

#### Post-hoc longer runs (num_steps 20,000)

Approved by the user **after** seeing the results above, and declared in
`pilot_manifest.json` before running. This is tuning after results, not a frozen
setting. One job per bundle; only `num_steps` changed (2,000 → 20,000), with
`num_rep` 512, cold start and 60 s unchanged.

| Bundle | Steps | Valid rows | Distinct | Best valid E | (U,W,B,R) | Rows at CP optimum | Running time | Quota |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| scale-512 | 2,000 | 5 / 512 | 173 | 516,244 | (13,6,4,4) | 0 | 0.17 s | 170 |
| scale-512 | 20,000 | 10 / 512 | 176 | 554,096 | (14,4,2,2) | 0 | 1.66 s | 1,662 |
| complete cell | 2,000 | 26 / 512 | 37 | 53,429 | (1,1,2,2) | 0 | 0.05 s | 50 |
| complete cell | 20,000 | 14 / 512 | 15 | **68** | (0,0,2,2) | 1 | 0.49 s | 491 |

On scale-512, ten times more steps doubled the valid rows, but the best valid
state is worse than with 2,000 steps and worse than the all-idle witness
(E 551,853). Without seed control, one job per setting cannot separate the step
count from run-to-run variation. On the complete cell, one row reached the
CP-certified optimum. The returned set collapsed from 37 to 15 distinct states, and
valid rows fell from 5% to 2.7%.

The scale-512 run's adapter call ended with `ConnectError` after the job was
created. The completed result was fetched later by its saved job id
(`Job.from_id`, no new submission), parsed with the adapter's own
`parse_samples` and checked by `catering.run evaluate`. `result.json` keeps the
original failure under `recovery`.

### Phase E: local-penalty study (post-hoc)

**Hypothesis:** the global penalty P (sum of all |objective coefficients| + 1)
grows with width. At 2,048 variables it is ~196,000× the weight of one missed
meal lot, which might hide the objective and exceed float32 resolution.

**Variants** are built by `catering/methods/veloxq_penalty.py` from the frozen
bundles; the sources are not modified. Variables, groups and conflicts stay the
same, so decoded tuples are comparable.

- `local`: each one-hot block and each conflict pair gets its own penalty,
  computed from the objective coefficients of the variables it touches.
  A 1- or 2-flip argument proves every minimum is feasible (module docstring;
  checked by randomized repair on every built bundle).
- `local-uw`: as `local`, with only (bound_W+1)·U + W in the QUBO. B and R are
  linear, so they are subtracted exactly; B/R become post-hoc tie-breaks.
- `-m8`: every local penalty ×8 (still provably safe).

| Source | Max coefficient: source → local-uw | Penalty / w_U: source → local |
|---|---:|---:|
| S3 quantum | 856,680 → 376 | 25 → 5 |
| scale-512 | 8.9e8 → 9,638 | 11,000 → 89 |
| scale-2048 | 1.5e10 → 32,934 | 196,000 → 305 |

#### Same-SA comparison (offline)

Repo SA (`catering.methods.classical.solve_qubo`), declared in `sa-plan.json`
before running: seed 2026, 32 restarts × 200 sweeps, cold random bits, no
repair. Valid samples / 32 and best valid (U,W,B,R):

| Bundle | CP reference | source | local | local-m8 | local-uw | local-uw-m8 |
|---|---|---|---|---|---|---|
| complete cell | (0,0,2,2) opt | 32 (0,0,2,2) | 31 (0,0,2,2) | 32 (0,0,2,2) | 32 (0,0,2,2) | 32 (0,0,2,2) |
| S0 quantum | (5,0,3,3) opt | 32 (5,1,3,3) | 28 (5,0,3,3) | 32 (5,0,3,3) | 31 (5,0,3,3) | 32 (5,1,4,4) |
| S1 quantum | (7,0,1,1) opt | 32 (7,0,1,1) | 29 (7,0,1,1) | 32 (7,1,2,2) | 30 (7,1,2,2) | 32 (7,0,1,1) |
| S2 quantum | (5,4,4,4) opt | 32 (6,1,2,2) | 31 (5,4,4,4) | 32 (5,4,4,4) | 32 (6,1,2,2) | 32 (6,2,2,2) |
| S3 quantum | (6,4,4,4) opt | 32 (6,4,4,4) | 32 (7,3,2,2) | 32 (7,3,2,2) | 30 (6,4,4,4) | 32 (6,4,4,4) |
| S0 scale-128 | (3,0,6,6) | 32 (4,3,5,5) | 12 (4,3,6,6) | 22 (4,3,4,4) | 18 (4,1,5,5) | 19 (4,2,5,5) |
| S1 scale-128 | (3,3,6,6) | 32 (5,3,5,5) | 15 (5,6,6,6) | 19 (6,3,5,5) | 20 (6,3,4,4) | 20 (6,3,4,4) |
| S2 scale-128 | (3,1,6,6) | 32 (3,4,6,6) | 24 (5,2,5,5) | 19 (4,3,5,5) | 20 (5,4,6,6) | 24 (5,2,3,3) |
| S3 scale-128 | (4,1,5,5) | 32 (5,4,5,5) | 30 (5,3,5,5) | 26 (6,3,3,3) | 27 (6,3,5,5) | 25 (6,3,3,3) |
| S0 scale-256 | (2,0,6,6) | 32 (3,5,8,8) | 10 (3,2,7,7) | 14 (4,5,6,6) | 10 (4,3,6,6) | 13 (4,5,6,6) |
| S1 scale-256 | (3,0,6,6) | 32 (4,3,6,6) | 8 (6,6,5,5) | 14 (5,3,5,5) | 18 (5,3,5,5) | 13 (6,2,3,3) |
| S2 scale-256 | (2,1,6,6) | 32 (4,3,6,6) | 14 (5,5,4,4) | 10 (5,3,4,4) | 12 (5,3,4,4) | 14 (5,4,5,5) |
| S3 scale-256 | (4,1,5,5) | 32 (5,2,5,5) | 12 (5,5,6,6) | 12 (6,6,5,5) | 11 (7,5,4,4) | 11 (6,6,5,5) |
| scale-512 | (6,1,10,10) | 32 (8,9,11,11) | 8 (10,11,10,10) | 6 (12,7,8,8) | 6 (9,6,8,8) | 5 (11,12,10,10) |
| scale-1024 | (7,2,11,11) | 32 (9,10,10,10) | 1 (12,14,10,10) | 1 (13,13,9,9) | 0 | 1 (13,10,11,11) |
| scale-2048 | (8,3,8,8) | 32 (9,7,10,10) | 2 (9,10,11,11) | 2 (12,11,9,9) | 0 | 0 |

The CP references for 128 and above are finite-budget incumbents; most 128/256
references are CP-optimal on the offered domain (see the frozen baselines).

SA on the **source** bundles is best or tied almost everywhere: 32/32 valid at
every width, and the best U at 128 and above. Local penalties cut valid rates
(to 0–2/32 at 1,024–2,048) and rarely improve the tuple. The exception is
S2 quantum, where `local`/`local-m8` reach the optimum and source does not.
With a much larger budget than the frozen 2 s control, SA on the source bundles
also beats every VeloxQ result in phase D (e.g. scale-512 (8,9,11,11) vs
(13,6,4,4); scale-2048 (9,7,10,10) vs no valid state).

#### VeloxQ on the variants

The cap was set to ledger total 30 before running and recorded in
`pilot_manifest.json`. Settings were unchanged from phase D (num_rep 512,
num_steps 2,000, 60 s, no retries). Packets became almost entirely
float32-exact (0–736 inexact of up to 638,930 spin coefficients, vs 90–100%
before).

| Case | Phase D source | local-uw | local-uw-m8 |
|---|---|---|---|
| complete cell | 26/512 (1,1,2,2) | ConnectError, no job | 34/512 (1,1,1,1) |
| S3 scale-256 | 6/512 (8,1,0,0) | 9/512 (8,2,1,1) | ConnectError, no job |
| scale-512 | 5/512 (13,6,4,4) | 2/512 (14,3,1,1) | 6/512 (13,5,5,5) |
| scale-1024 | 1/512 (14,8,4,4) | 1/512 (14,6,4,4) | 0/512 |
| scale-2048 | 0/512 | ConnectError, no job | 0/512 |

Three attempts failed to connect before a job existed. They count in the ledger
and were not retried. Job 21 failed after creation and was recovered by its job
id.

**Conclusion:** the penalty magnitude is not the main obstacle. Smaller
penalties fix float32 representability but do not improve U for VeloxQ, and they
hurt SA validity. The likely obstacle is structural: a valid state needs exactly
one choice in each of 26 blocks and no active pair among 27,801–487,167
conflicts, and changing a block's choice is a 2-flip move. Fewer conflicts
(smaller, better-chosen program pools) or a constraint-preserving method
(XY-mixer QAOA) address that; penalty rescaling does not. One seed, one SA
schedule and one VeloxQ setting per case; not a hardness claim.

### Phase F: low-conflict pools (post-hoc)

**Hypothesis:** phase E pointed to dense conflicts as the obstacle.
`catering/methods/veloxq_lowconflict.py` builds pools of the same widths from the
same full local domain (18,182 programs, hash checked against the frozen
release). It keeps one seed per anchor, then goes round-robin over blocks, each
time adding the program with the fewest conflicts with already selected
programs. No reference or solver output is used. The unchanged compiler builds
the QUBO (same weights, same global penalty rule). Only 46 of 486 (512) and 102
of 998 (1,024) programs are shared with the frozen pools.

| Pool | Conflicts | Couplers (density) | P | CP-SAT 30 s | SA 32×200 | VeloxQ (2,000 steps) |
|---|---:|---:|---:|---|---|---|
| frozen 512 | 27,801 | 37,008 (28%) | 4.4e8 | FEASIBLE (6,1,10,10) | 32/32 (8,9,11,11) | 5/512 (13,6,4,4) |
| low-conflict 512 | 13,620 | 20,242 (15%) | 2.0e8 | **OPTIMAL** (6,1,13,13) | 32/32 (9,9,12,12) | 1/512 (14,6,4,4) |
| frozen 1,024 | 118,165 | 156,129 (30%) | 1.9e9 | FEASIBLE (7,2,11,11) | 32/32 (9,10,10,10) | 1/512 (14,8,4,4) |
| low-conflict 1,024 | 62,538 | 90,558 (17%) | 8.4e8 | **OPTIMAL** (6,1,13,13) | 32/32 (10,9,12,12) | 0/512, 0/512 |

The cap was set to ledger total 34 before running: two replicate jobs per pool,
because there is no seed control. The first 512 job failed with `ConnectError`
before job creation and was not retried, so 512 has one replicate.

**Reading:** halving the conflicts made the problem easier for CP-SAT (now
proven optimal within 30 s), but not for VeloxQ (no or one valid row). SA quality
is unchanged, and SA runs 4–7× faster because there are fewer couplers. Across
phases D–F, no tested change to penalty magnitude or conflict density improved
VeloxQ's U at 512 variables or more under default settings. Remaining untested
levers are VeloxQ's own parameters beyond `num_steps` and a different encoding.
Same caveats: one setting, one or two jobs per case, no seed.

### Phase G: VeloxQ parameters (post-hoc)

`VeloxQParameters` exposes only `num_rep` and `num_steps`. The SDK defaults
(4,096 × 5,000) are about 20× the frozen 512 × 2,000 budget. The grid was
declared in `pilot_manifest.json` before running; the cap was ledger total 46,
and 42 were used. Frozen bundles unless noted:

| Bundle | num_rep × num_steps | Valid rows | Best valid (U,W,B,R) | Running time |
|---|---|---:|---|---:|
| scale-512 | 512 × 2,000 (phase D) | 5 / 512 | (13,6,4,4) | 0.17 s |
| scale-512 | 4,096 × 5,000 | 52 / 4,096 | (12,6,5,5) | 2.7 s |
| scale-512 | 16,384 × 5,000 | 227 / 16,384 | (13,2,2,2) | 10.9 s |
| scale-512 | 65,536 × 2,000 | 588 / 65,536 | (11,7,6,6) | 17.5 s |
| complete cell | 4,096 × 5,000 | 103 / 4,096 | **(0,0,2,2)** opt, 4 rows | 0.19 s |
| complete cell | 16,384 × 5,000 | 440 / 16,384 | **(0,0,2,2)** opt, 8 rows | 0.46 s |
| scale-1024 | 4,096 × 5,000 | 16 / 4,096 | (14,2,1,1) | 10.4 s |
| scale-2048 | 4,096 × 5,000 | 0 / 4,096 | — | 38.2 s |
| lowconflict-512 | 16,384 × 5,000 | 18 / 16,384 | (12,5,6,6) | 6.6 s |

A larger budget helps only slowly. The best U at 512 goes from 13 to 11 with
128× more samples, while SA 32×200 reaches 8 and CP-SAT 6. The valid-row rate
stays at about 1%. The complete cell now hits its optimum reliably. Nothing is
valid at 2,048.

### Phase H: new cost functions on the largest problems (post-hoc)

All jobs used 4,096 × 5,000, declared before running; the cap was ledger total
56, and 54 were used. `lowconflict-2048` was built like phase F (289,770
conflicts vs 487,167 frozen; CP-SAT 30 s FEASIBLE (8,5,12,12)). Local-penalty
variants of the low-conflict pools are in `penalty-study-v2/`.

| Bundle | Valid rows | Best valid (U,W,B,R) |
|---|---:|---|
| frozen scale-1024 (phase G) | 16 / 4,096 | (14,2,1,1) |
| scale-1024 local-uw | 6 / 4,096 | (13,6,5,5) |
| scale-1024 local-uw-m8 | 6 / 4,096 | (13,4,3,3) |
| lowconflict-1024 | 3 / 4,096 | (14,3,2,2) |
| lowconflict-1024 local-uw | 3 / 4,096 | (13,3,3,3) |
| lowconflict-1024 local-uw-m8 | 1 / 4,096 | (14,4,2,2) |
| frozen scale-2048 (phase G), scale-2048 local-uw / -m8 | 0 / 4,096 each | — |
| lowconflict-2048, local-uw / -m8 | 0 / 4,096 each | — |

SA 32×200 on lowconflict-2048 returned 32/32 valid, best (10,9,11,11).

Two attempts failed with `ConnectError` before a job existed and were
resubmitted once each, as declared. Two failed after creation and were recovered
by job id.

**Overall (phases D–H):** VeloxQ matches CP-SAT optima on the 31–35-variable
QUBOs. From 256 variables up it is behind seeded SA on the same matrix. At
2,048 it returns no valid state under any tested cost function, pool or budget.
Penalty magnitude, conflict density and a 20–128× larger budget each moved U by
at most 1–2 lots.

### Service plan

Steps 1–4 are done (above). Following "begin with one scale tier": step 1 was one job on scale-512 (ledger
total 2); step 2 added scale-1024 and scale-2048 only if step 1 is useful (total 4);
optional steps add the v3 four-event scale-128/256 set (total 12) and the shared
small QUBOs (total 17). Settings: `num_rep=512`, `num_steps=2000`, cold start,
60 s, one job per case, no retries, no tuning before step 1.

    # offline (packet + not_run result):
    .venv/bin/python -m catering.methods.veloxq --bundle output/catering-velox-scale-v3/scale-512-qubo.json
    # only after the user sets the cap; N is the LEDGER TOTAL incl. phase C:
    .venv/bin/python -m catering.methods.veloxq --bundle output/catering-velox-scale-v3/scale-512-qubo.json \
        --allow-external --max-service-jobs 2 --timeout 60

Each remote attempt is recorded in the ledger before upload and counts even if
it fails. A GPU service result is not physical quantum execution; the service
returns only final samples, so time-to-first-feasible is not observable.
Warm start (`init_state`) is not used.

## Follow-up conditioning experiment

The user asked the foundation agent to improve this track on 17 October.
See [the proof and bounded pilot](../CATERING_VELOXQ_TUNING.md). A new, separately
hashed penalty variant preserves feasible objectives and global optima while
reducing P by 126–642x. Original owner receipts and inputs stay unchanged;
local controls do not constitute a new VeloxQ result. Adapter 0.3.0 additionally
supports a checked explicit warm-start Spectrum and recoverable storage downloads.
Seven additional service runs are retained. No-idle uses actual widths486/998/2022
for the frozen512/1024/2048 choices and returns512/512 valid at each tier.
Scheduling quality still trails CP and matching SA. The combined ledger has61
attempts (54 prior-owner plus seven follow-up),54 created job IDs. Reported new
quota usage36,640 and charged costUSD0. This later result supersedes the earlier
statement that no tested representation yields feasible large outputs.
