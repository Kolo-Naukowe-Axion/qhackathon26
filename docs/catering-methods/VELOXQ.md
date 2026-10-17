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
