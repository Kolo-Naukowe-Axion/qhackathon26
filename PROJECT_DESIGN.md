# Project design — current implementation and next solver boundary

Status: presentation environment and offline baseline QUBO preparation, 2026-10-16. Neither required-method solver run is complete.

## Official optimization problem

Each job visits the common machine route, with the fixed processing durations in `instances/`. Each operation runs once, machine processing intervals do not overlap, and a predecessor completes before a successor starts. Minimize the latest completion time. Baseline outputs use nonnegative integer hours and `end = start + duration`.

Instance A requires its QUBO to be solved using a quantum algorithm on hardware or a simulator. Instance B requires its QUBO to be solved using a QUBO solver; our plan uses VeloxQ. The implemented fixed-horizon time-indexed QUBO, exact weights, window bounds, feasibility argument, and classical reference algorithm are documented in [STAGE1_OFFLINE.md](docs/STAGE1_OFFLINE.md). Quantum simulator settings and actual required-method execution records remain outstanding.

## Implemented display model

The browser reads a versioned `axion-replay.v1` object:

```json
{
  "schema": "axion-replay.v1",
  "unit": "hours",
  "provenance": {
    "kind": "illustration",
    "method": "Manual transcription",
    "label": "Organizer slide",
    "description": "An illustration, not a solver run",
    "source": "Opening presentation",
    "jobId": null
  },
  "machines": [{ "id": "T", "name": "Turning" }],
  "jobs": [{ "id": "Z1", "color": "#648da3", "operations": [{ "machine": "T", "duration": 2 }] }],
  "schedule": [{ "job": "Z1", "machine": "T", "start": 0, "end": 2 }]
}
```

This schematic shows field shapes, not a complete loadable instance: the current viewer accepts two or three machines, one to twelve jobs, and a common route visiting each displayed machine once. `kind` is `illustration`, `imported`, or `solver`. Metadata is displayed as supplied, never treated as authenticated execution evidence. Optional backend, timestamp, job id, and declared makespan may accompany a replay.

The official schedule adapter chooses the known instance from `instance_2x2`/`instance_3x3`, attaches the authoritative processing durations, and preserves the declared method as unverified imported metadata. It rejects noninteger baseline times. Export produces a display replay, not a newly certified official solver output.

## Validation and replay semantics

- Structural parsing rejects unknown job/machine references, duplicate model ids, invalid colors, nonfinite/negative intervals, and unsupported routes.
- Coverage compares each required job-machine operation with the full schedule and rejects missing/duplicate operations.
- Duration compares every interval length against the input duration.
- Capacity compares all operation pairs sharing a machine.
- Precedence compares each job's adjacent operations.
- If provided, declared makespan must equal the maximum operation end.
- Intervals are half-open. At a boundary the previous machine is released and the successor can start immediately.
- Completed count requires all expected operations. Missing operations cannot silently produce a completed part.

This establishes schedule feasibility under the baseline model. It does not prove global optimality or establish that a named solver ran.

## Architecture and planned integration

`presentation/model.js` is a DOM-free parser/checker. `data.js` contains explicitly illustrative records. `scene.js` creates original pixel art and positions parts from replay state. `app.js` synchronizes the views and handles local imports. `scripts/serve.mjs` serves only the presentation folder on loopback.

The solver pipeline will save actual samples, model coefficients, parameters, job metadata and decoded official schedules. A replay will be derived from those artifacts. Secrets remain in the backend environment; the browser needs no solver token. Exact classical reference results will be stored separately for comparison on the same model.

The offline pipeline measures 8 variables at H=4 for A and 39 at H=8 for B. It independently establishes classical optima of 4 and 8 hours and checks their zero-energy QUBO round trips. Exhaustive 2×2 bitstring checks and sampled 3×3 constraint checks exercise the formulation. No quantum or VeloxQ performance result exists yet. See `docs/VELOXQ_IDEAS.md` for further experiment and presentation ideas.
