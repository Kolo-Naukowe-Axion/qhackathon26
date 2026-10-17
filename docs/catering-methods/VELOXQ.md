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

Only local generation, checking and CP-SAT references. **Zero VeloxQ or IBM calls.**
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

**Deliverables 1–3 are done; phase D steps 1–2 have run** (user approval
17 October 2026, ledger total 4: the phase C smoke plus scale-512, scale-1024
and scale-2048). Steps 3–4 are not authorized. See "Phase D steps 1–2 result".

| Path | Content |
|---|---|
| `catering/methods/veloxq.py` | Adapter 0.2.0: `solve_qubo(bundle, budget, method_config, output_dir)` and CLI |
| `tests/catering/test_veloxq_adapter.py` | 66 offline tests, no token or network |
| `output/catering-methods/veloxq/pilot_manifest.json` | Caps, frozen settings, case hashes, baselines and comparison declared before results |
| `output/catering-methods/veloxq/offline-readiness-v3.json` | One `not_run` record per released v3 bundle (16), with sizes, coefficient ranges, packet dtype/size and timings |
| `output/catering-methods/veloxq/job_ledger.json` | Every attempted service submission (currently 4) |
| `output/catering-methods/veloxq/smoke-20261017T162002/` | Phase C raw input/output and result |
| `output/catering-methods/veloxq/paired-lunch-12-v1_S3_meal-block-{486,998,2022}-*/` | Phase D raw packet, raw result, `result.json` and shared-checker `evaluation.json` |

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
packets at all three widths (int64), and every reported energy matched
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

### Phase D steps 1–2 result

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

### Service plan

Steps 1–2 are done (above). Following "begin with one scale tier": step 1 was one job on scale-512 (ledger
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
supports a checked explicit warm-start Spectrum, offline tested.
