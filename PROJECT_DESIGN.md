# Project design — active catering entry and factory archive

## Active catering design — 17 October

The current entry is Axion Kitchen, the paired-course catering-production
extension. Its implemented model, full equations, penalty argument, scope and
method evidence are in [CATERING_QUANTUM_FIRST.md](docs/CATERING_QUANTUM_FIRST.md).
Use that document with the [solver contract](docs/CATERING_SOLVER_CONTRACT.md)
and [run instructions](catering/README.md). The
[presentation plan](docs/CATERING_PRESENTATION.md) maps this design to the live
demo, recording, measured claims and remaining work.

A decision bit selects a legal local batch program with yield, order allocations,
resources and phase times. One-hot blocks include idle choices. Complete meals
need both main and side; coverage products give quadratic service and unpaired
waste terms without product-register qubits. Conflicts prohibit incompatible
program pairs. The objective prioritizes missed complete meals, discarded
components, new batches and changes to unstarted work; R=B in current fixtures.
An independent checker validates resources, meal handovers and material balance.

The complete small cell, larger restricted QAOA pilots and larger VeloxQ service
runs have different measured scopes. The latter's first cold settings have low
feasibility; improving them is active integration work. No hardware performance
or quantum advantage follows from these results. Below is preserved factory
design history, not the active catering formulation or its acceptance status.

## Current manufacturing centerpiece — 17 October update

The main demonstration uses complete 16-operation recipes (32–128 operations). Replacing heat capacity changes certified full-model weighted tardiness from 45 to 0; the original 781-bit operation pool stays at 45. Nested deterministic enrichment restores recovery with 2,078 bits, versus 2,499 for complete optimization. A distinct exact deadline-decision QUBO uses 818 bits and 33,817 couplers for the replacement query. Its zero-energy guarantee concerns feasibility, not the original soft-objective landscape.

The integrated [recipe bridge](docs/STAGE2_RECIPE_BRIDGE.md) keeps all 32 operations in eight component groups, recombining independently constructed complete routes. Its 18/28/36 logical-qubit models have 512/26,244/262,144 one-hot sector states. QAOA and sector annealing each produce 18/18 physically valid same-pool optimal schedules across two capacity cases, three caps and three seeds. The constructor already supplies an optimal incumbent; exact sector construction reveals minima classically. This is quantum integration and a sampling comparison, without advantage or scalable quantum-simulation claims. An independent circuit audit checks emitted QASM; the six 18-qubit circuits receive full-Hilbert probability checks, while larger circuits receive resource audits.

[Feature ablations](docs/STAGE2_REALISM_FRONTIER.md) fix horizon/grid and count unary/support bits, couplers and coefficient scale. All six ablations have exact native and restricted references. Larger 64/128-operation native runs remain UNKNOWN with checked bounds. [Economics](docs/STAGE2_CAPACITY_ECONOMICS.md) computes an exact rational ledger and 135 sensitivities for four checked saved plans under synthetic prices. It values schedules selected for deadline priority; it is not a minimum-money weekly optimizer. The studio exposes these assumptions and purchase/event-fee thresholds.

See [the evidence map](docs/STAGE2_MANUFACTURING_STUDY.md), [combined design](docs/STAGE2_COMBINED_DIRECTION.md), and [acceptance record](docs/STAGE2_MERIT_ACCEPTANCE.md). Local studio: http://127.0.0.1:4192/manufacturing/. Four new cold offline packets support the future integrated VeloxQ backend comparison, including matched original-objective penalties. VeloxQ is part of this same Stage2 extension. No VeloxQ execution or physical QPU call; private-remote sync and automatic site deployment are authorized, while public-source release/submission remain pending. Earlier sections below retain their explicitly smaller scopes.

Status: agreed non-VeloxQ technical merit scope complete, 17 October 2026; all 14 core requirements passed. See [current status](docs/STAGE2_STATUS.md) for evidence and the remaining VeloxQ, synchronized video, rehearsal and release duties. The complete-recipe bridge is integrated; the residual-cell study below retains its separate scope. No VeloxQ or physical ODRA5 execution is claimed.

## Main-model mathematical specification

[Mathematics of the complete-recipe manufacturing model](docs/STAGE2_MANUFACTURING_MATH.md)
is the readable formulation reference for the main32-operation entry. It defines
raw assignment domains, processing/attendance calendars, metric setup and worker
travel assumptions, material precedence, the completion register, full quadratic
polynomial and coefficient conventions. It proves the integer objective hierarchy
and represented-witness penalty bound, and distinguishes exact support pruning,
lossy grid/pool restrictions, the hard-deadline query and the component-route
quantum bridge. Owning code, exhaustive tests and frozen evidence are linked.

## Smaller quantum validation design

The smaller validation cell’s numerical definition, complete equations, reduction proof,
source-sealed experiment protocol, results, scopes and rubric map are in
[STAGE2_ENTRY.md](docs/STAGE2_ENTRY.md). The decision is how to schedule remaining
pump machining, a material-join assembly and inspections after capacity changes,
including shared workers, cross-training, alternate machines, calendars and due
dates. This stays within manufacturing. All data are explicitly synthetic.

Use the full two-hall factory below to explain the industrial system; use the
complete residual-cell QUBO to demonstrate the quantum formulation on a bounded,
explicit model. The residual cell is not a trace-extracted state or a lossless
full-factory reduction. Its independent native CP reference uses the same input
and objective. No CP schedule or pool of reference answers initializes QAOA.

`entry_core.py` defines instances; `window_qubo.py` compiles assignment and
completion bits; `assignment_qaoa.py` preserves every one-hot group through W
preparation and ordered XY mixing. CVaR .25 / p=2 is selected on TRAIN seeds only.
All 60 TEST quantum outputs are valid optimal actual schedules; 57 measured
bitstrings attain exact QUBO minima. Three completion registers exceed actual
completion by 30, and both values are disclosed. Annealing attains all 60 exact
minima too. The simulator classically enumerates the sector energy table; no
speedup or full-factory optimum is claimed.

`entry_demo.py` serves a loopback-only fresh-run action and `presentation/entry/`
shows retained evidence and counterfactual schedules. The static build contains
no Python service or credentials. `entry_velox_offline.py` has no submit option;
its nine SDK-format packets use exact integer Hamiltonian rescaling after an
audit detected float32 energy loss. Backend acceptance and internal precision
remain unverified. Source snapshots, counts, QASM, references and manifests are
retained; `scripts/verify-stage2-entry.py` rechecks claims and every TEST plan.

## Official optimization problem

Each job visits the common machine route, with the fixed processing durations in `instances/`. Each operation runs once, machine processing intervals do not overlap, and a predecessor completes before a successor starts. Minimize the latest completion time. Baseline outputs use nonnegative integer hours and `end = start + duration`.

Instance A requires its QUBO to be solved using a quantum algorithm on hardware or a simulator. Instance B requires its QUBO to be solved using a QUBO solver. Both selected outputs use actual local QAOA simulation of the compact order QUBOs, with exact makespans 4/8 hours; see [STAGE1_COMPACT.md](docs/STAGE1_COMPACT.md). The earlier fixed-horizon time-indexed QUBO, weights, window bounds, feasibility argument and classical reference remain comparison evidence in [STAGE1_OFFLINE.md](docs/STAGE1_OFFLINE.md) and [STAGE1_REFINEMENT.md](docs/STAGE1_REFINEMENT.md). Neither VeloxQ nor ODRA5 executed; both remain on user hold.

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

The factory world fills the viewport. Lunar Assembly is the fixed appearance, with cool deck plates, blue steel and ceramic controls shared by the manual and error page. Alternatives are archived outside the shipped viewer; there is no runtime style selector. Lunar instrument-panel navigation switches between the live world and the control desk, whose Timeline and Validation menus preserve replay time and part selection. Playback, part inventory and completion metrics live in the bottom HUD. Keyboard controls, native fullscreen with fallback, reduced motion and responsive layouts are supported.

`/problem-explanation` is an independent six-chapter manual in the same visual system, reachable from the top navigation and footer. It covers official inputs/rules, schedule calculation and optimality, fixed-horizon QUBO penalties, one-hot/domain-wall encodings, current selected local solver results, and complexity. Job-order, one-hot, compact-bit and scaling controls use deterministic teaching models. Their diagrams are labeled as illustrations rather than new solver runs. `evidence.js` summarizes the selected actual runs and is tested against the selection manifest. Directory routes are served by `scripts/serve.mjs`; the static build copies the manual into `dist/problem-explanation/`.

## Architecture and planned integration

`presentation/model.js` is a DOM-free parser/checker. `data.js` contains explicitly illustrative records. `lunar.js` supplies fixed scene materials/scenery and removes obsolete comparison query parameters; `lunar.css` shares the Lunar material palette across pages. `scene.js` creates original pixel art and positions parts from replay state. `app.js` synchronizes the views and handles local imports. `scripts/serve.mjs` serves only the presentation folder on loopback.

The solver pipeline saves actual samples, model coefficients, parameters, source/model/instance hashes, versions, run metadata and decoded official schedules, plus derived replays. Secrets remain in the execution environment; the browser needs no solver token. Classical references remain separate from returned solver samples. Current selection is recorded in `output/stage1-selected.json`, pointing to `output/stage1-compact-ready/`; previous runs remain retained.

One-hot sizes are 8 variables at H=4 for A and 39 at H=8 for B; domain-wall sizes are 4 and 30. All 512,000 allowed operation-start combinations for B agree with the independent checker in both encodings; invalid-wall correctness uses an explicit penalty bound and exhaustive small-model tests. These earlier methods remain comparison evidence. The selected `solver/sequence.py` models preserve every common job order using 1 bit for A and 3 bits for B: `E_A=4+a`, `E_B=9-a+3b-c-2ab+3ac-3bc`. Each valid state's energy is its earliest-start makespan; cyclic B states cost 12/10, above valid costs 8/9. Both are solved by QAOA: A p=1/shared-X/one restart, B p=2/local-X/eight restarts, with 4,096/4,096 optimal measurements each. Twenty fresh seeds gave 81,920/81,920 optimal shots per instance. All n! permutation costs are computed classically to construct these tiny QUBOs; this reveals the permutation optimum before quantum execution. The representation excludes extra idle time and independent machine orders, with zero loss to the full independent reference on the official instances. No scalable compilation or quantum advantage is claimed. Three bits attain the information minimum only for distinct representation of all six common orders; no unrestricted minimum is claimed. See `docs/STAGE1_COMPACT.md` for coefficients, proof, matched comparisons and evidence. Exact independent optima are 4 h and 8 h. SDK serialization/result parsing is tested locally; remote performance is unknown. See `docs/STAGE1_OFFLINE.md` for formulas, settings, proof and limitations, and `docs/ODRA5.md` for native compilation and hardware access.

## Stage 2 implemented factory and research artifacts

`docs/STAGE2_ENVIRONMENT.md` specifies the working ambitious factory proposal;
`docs/STAGE2_IDEATION.md` records alternatives, design iterations and critiques.
The user directed us to begin at high complexity and simplify only following
demonstrated obstacles. The 24-order, 15-machine model joins component production,
transport, assembly, energy, people/tooling, quality and uncertain recovery.

`instances/stage2/metaltech_pressure.json` supplies design parameters;
`stage2/spec.py` expands complete numerical instances. `stage2/engine.py` executes
the physical factory and `stage2/check.py` independently replays resource use,
movement, genealogy, quality, energy and revealed events. The original
`scripts/stage2_blueprint.py` remains a structural design tool. Its historical
missing-table list does not describe the implemented minute-resolution profile.

The exact finite-state encoding remains conceptual and potentially enormous.
The implemented quantum experiment selects compatible ready starts from a
restricted boundary-frozen pool, with all slack variables counted. Exact local
equivalence does not establish full-policy optimality. Matched classical controls,
learned policies, scenario lookahead, independent replay and scoped deterministic
CP references provide separate evidence. Physical quantum hardware and VeloxQ
are not used in the current research scope. The versioned trace contract is
`stage2/TRACE_CONTRACT.md`; the separate viewer is `presentation/stage2/`.

See `stage2/README.md`, `docs/STAGE2_METHOD_AUDIT.md` and
`docs/STAGE2_EXPERIMENT_LOG.md` for actual mechanisms, limitations, results and
precomputation costs. Reserved final tapes remain distinct from development.

The frozen campaign is complete: 23,552 valid executions across 74 method/context
groups, with 41 declared comparisons. The later [solution-quality supplement](docs/SOLUTION_QUALITY.md)
quantifies realized-primary gap intervals using unchanged final outcomes and
stronger offline necessary-quality bounds. Exact deterministic reference makespans
and full-factory missing-order certificates have separate scopes; neither implies
optimal full-factory deadline debt/cost or a quantum advantage.
