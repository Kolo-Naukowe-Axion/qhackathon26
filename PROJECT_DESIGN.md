# Project design — current implementation and next solver boundary

Status: presentation environment and both locally verified Stage 1 runs, 2026-10-16. VeloxQ remote and ODRA5 physical execution remain pending.

## Official optimization problem

Each job visits the common machine route, with the fixed processing durations in `instances/`. Each operation runs once, machine processing intervals do not overlap, and a predecessor completes before a successor starts. Minimize the latest completion time. Baseline outputs use nonnegative integer hours and `end = start + duration`.

Instance A requires its QUBO to be solved using a quantum algorithm on hardware or a simulator. Instance B requires its QUBO to be solved using a QUBO solver; our plan uses VeloxQ. The implemented fixed-horizon time-indexed QUBO, exact weights, window bounds, feasibility argument, and classical reference algorithm are documented in [STAGE1_OFFLINE.md](docs/STAGE1_OFFLINE.md). Both required methods have now run locally; the refined settings and validation are recorded in docs/STAGE1_REFINEMENT.md. Both remote backends are on user hold.

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

## Factory interface and Stage 1 manual

The factory world fills the viewport. Wooden navigation switches between the live world and the control desk, whose Timeline and Validation menus preserve replay time and part selection. Playback, part inventory and completion metrics live in the bottom HUD. Keyboard controls, native fullscreen with fallback, reduced motion and responsive layouts are supported.

`/problem-explanation` is an independent six-chapter manual in the same visual system, reachable from the top navigation and footer. It covers official inputs/rules, schedule calculation and optimality, fixed-horizon QUBO penalties, one-hot/domain-wall encodings, current selected local solver results, and complexity. Job-order, one-hot, compact-bit and scaling controls use deterministic teaching models. Their diagrams are labeled as illustrations rather than new solver runs. `evidence.js` summarizes the selected actual runs and is tested against the selection manifest. Directory routes are served by `scripts/serve.mjs`; the static build copies the manual into `dist/problem-explanation/`.

## Architecture and planned integration

`presentation/model.js` is a DOM-free parser/checker. `data.js` contains explicitly illustrative records. `scene.js` creates original pixel art and positions parts from replay state. `app.js` synchronizes the views and handles local imports. `scripts/serve.mjs` serves only the presentation folder on loopback.

The solver pipeline saves actual samples, model coefficients, parameters, source/model/instance hashes, versions, run metadata and decoded official schedules, plus derived replays. Secrets remain in the execution environment; the browser needs no solver token. Classical references remain separate from returned solver samples. Current selection is recorded in `output/stage1-selected.json`, pointing to `output/stage1-local-ready/`; previous runs remain retained.

One-hot sizes are 8 variables at H=4 for A and 39 at H=8 for B; domain-wall sizes are 4 and 30. All 512,000 allowed operation-start combinations for B agree with the independent checker in both encodings; invalid-wall correctness uses an explicit penalty bound and exhaustive small-model tests. A's selected p=3 independent-X QAOA simulator run returned 4 h with 4,096/4,096 feasible measurements; B's selected 32,000-sweep linear annealing run returned 8 h with 511/512 feasible samples. Exact independent optima are 4 h and 8 h. SDK serialization/result parsing is tested locally; remote performance is unknown. See `docs/STAGE1_OFFLINE.md` for formulas, settings, proof and limitations, and `docs/ODRA5.md` for native compilation and hardware access.

## Stage 2 proposal and structural artifact

`docs/STAGE2_ENVIRONMENT.md` specifies the working ambitious factory proposal;
`docs/STAGE2_IDEATION.md` records alternatives, design iterations and critiques.
The user directed us to begin at high complexity and simplify only following
demonstrated obstacles. The 24-order, 15-machine model joins component production,
transport, assembly, energy, people/tooling, quality and uncertain recovery.

`instances/stage2/metaltech_pressure.json` is a parameterized **blueprint**, not a
complete executable environment instance. `scripts/stage2_blueprint.py` expands
its nominal manufacturing DAG and exogenous scenario leaves and checks structural
properties. No controller, event simulator, independent physical trace checker,
complete classical reference, Stage 2 QUBO or Stage 2 viewer is implemented by this
artifact. Its missing-table list is part of the design contract.

The proposed exact finite-state encoding is a conceptual correctness route with
potentially prohibitive state growth. The practical VeloxQ research direction is
closed recovery neighborhoods with explicit resource/state boundaries. Any
restriction to generated candidates must be disclosed and compared on the same
restricted model; full-environment replay is still required. The new domain will
need its own versioned event/trace contract rather than relaxing the baseline
viewer's common-route assumptions.
