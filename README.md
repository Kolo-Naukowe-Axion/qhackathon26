# QHackathon 2026

## Active Stage 2 direction: catering

We are building one catering-production extension for both the overall award
and best use of VeloxQ. The goal is a correct compact formulation, good checked
solutions and clear experiments; a quantum advantage is not a release requirement.
Read the [current method, mathematics and evidence](docs/CATERING_QUANTUM_FIRST.md),
[runnable quick start](catering/README.md), [four-person allocation](docs/CATERING_METHOD_WORKSPLIT.md)
and [solver contract](docs/CATERING_SOLVER_CONTRACT.md).

The [presentation and demo runbook](docs/CATERING_PRESENTATION.md) contains the
three-minute script, five-minute video storyboard, exact kitchen interactions,
live-launch preparation and the VeloxQ prize experiment priorities.
The [submission checklist](docs/STAGE2_SUBMISSION.md) maps all 30 points and the
separate VeloxQ criteria to evidence, remaining work and final release gates.
GitHub stays private during development; public release is deferred to the final
submission step, with time to verify access before the deadline.

The new paired-course profile requires both main and side for a complete meal,
counts unmatched food as waste, and adds a quadratic service objective without
product auxiliary qubits. It retains shared batches, freshness, equipment/crew
conflicts, committed work and mandatory post-repair cleaning. Frozen research
inputs in output/catering-foundation-v3/ provide33/35/31/35qubit portfolios and
nested128/256bit scale pools with independent raw and offered-domain references.
These portfolios have measured restriction gaps; they are not full-kitchen
optima or the accepted final quantum workload. The QAOA pilot and offline circuit
audit are separate from the input release. Method owners must opt into the new
profile explicitly; v2 component-demand inputs remain unchanged for regression.

The catering game viewer runs at `/catering/` in the static site. It replays actual
QAOA samples, controls and independent classical references, with complete-meal
handovers, the mandatory recovery clean and a model/results panel. A visible batch
timeline, cooking/packing queues and per-course tickets explain production order. See the
[viewer guide](presentation/catering/README.md). Start it with `PORT=4192 npm run dev`.

The VeloxQ owner has a [concrete scale handoff](docs/catering-methods/VELOXQ.md):
nested 512/1,024/2,048-variable workloads of the same model, with 12 customers,
checked witnesses and local reference statuses. After pulling, run
`node scripts/restore-compressed-evidence.mjs` to restore the large matrices.
These input files were generated locally. The owner has since committed the
first authorized service runs and raw evaluations; see the handoff's Phase D
results. Further calls require the owner's concrete budget authorization.

The [ambitious specification](docs/CATERING_AMBITIOUS_SPEC.md) describes additional
future mechanisms, not features already implemented or required before delivery.
No catering IBM hardware result is claimed. VeloxQ's retained cold runs are
actual service results; their quality and feasibility limits are documented.

The existing factory implementation, results and demo below remain intact as
a fallback. Its technical acceptance does not certify the new catering scope.

## Existing factory implementation and fallback

**Technical closeout, 17 October:** all 14 agreed non-VeloxQ core requirements passed; 52 targeted Python tests, 113 site tests and the static build passed. Read the [current status and remaining work](docs/STAGE2_STATUS.md). Actual VeloxQ execution, the final synchronized video, human rehearsal and public release/submission remain open.

The [manufacturing recovery study](docs/STAGE2_MANUFACTURING_STUDY.md) is the main demonstration: complete pump recipes, capacity recovery, representation loss, QAOA on the same 32 operations, feature ablations and an explicit cost ledger. The original 781-bit pool loses a certified 45→0 weighted-lateness recovery; deterministic enrichment restores it at 2,078 bits. A separate exact deadline query uses 818 bits. Complete optimization uses 2,499 bits. These are different representations with stated guarantees.

The [whole-recipe quantum bridge](docs/STAGE2_RECIPE_BRIDGE.md) recombines all eight component groups using 18–36 logical qubits. The constructor already finds an optimal recovery plan; QAOA and classical annealing both recover it. Sector enumeration is classical and budgets differ. This establishes integration, not quantum advantage. The [economics](docs/STAGE2_CAPACITY_ECONOMICS.md) values saved schedules under synthetic prices; it does not optimize monetary cost or establish calibrated ROI.

```sh
.venv-stage2/bin/python -m stage2.entry_demo --port 4192
```

Open [the local manufacturing studio](http://127.0.0.1:4192/manufacturing/). It provides checked schedule comparisons, a fresh whole-recipe QAOA action, adjustable capacity economics and the price-of-realism table. Static builds support retained evidence; fresh execution requires the Python server. The [combined direction](docs/STAGE2_COMBINED_DIRECTION.md), [acceptance record](docs/STAGE2_MERIT_ACCEPTANCE.md) and [submission preparation](docs/STAGE2_SUBMISSION.md) describe scope and remaining duties. Four new cold SDK packets cover deadline, enriched and complete models, including matched-penalty controls. VeloxQ calls, physical QPU work and public-source release remain held.

The game-like desktop studio follows four recovery decisions through detailed equipment, real scheduled workpieces and all16steps of a selected pump. It supports event stepping, replay speed and a focused presentation view; predicted deadline results stay separate from completed work. Maths and results remain one click away. Read the [complete main-model mathematics](docs/STAGE2_MANUFACTURING_MATH.md) for variables, constraints, coefficient conventions, penalty proofs and exact-versus-restricted scope. Current UI checks pass all120site tests, with desktop review and a fresh checked28-qubit run. [UI design and verification](docs/STAGE2_UI_DESIGN.md) records the limits. VeloxQ is an integrated backend path within this same Stage2 extension, currently prepared offline.

Team workspace for the QPoland Quantum Hackathon 2026.

## Production deployment

Vercel project: `qfactoria`, personal scope `iwos`. Custom domain: `qfactoria.com`.
The GitHub repository is `Kolo-Naukowe-Axion/qhackathon26` (currently private; the competition’s public-source requirement is still pending); production follows
`main`. Vercel reads the build settings from `vercel.json`. Keep the project root
at the repository root. Each new push to `main` builds and deploys automatically;
failed tests stop the deployment. Other branches get preview deployments.

Site: https://qfactoria.com (also available at https://qfactoria.vercel.app).
Dashboard: https://vercel.com/iwos/qfactoria.
The Vercel GitHub app has access to this repository only within the Axion organization.

The hosted site contains only the built viewer. Repository documents and organizer PDFs are not
included in `dist/`. To roll back, promote a previous ready deployment from the
personal project's Vercel dashboard.

## Run the presentation environment

The Stage 2 factory opens the frozen `static-grid-12` final replay: first
predeclared tape10004/actor900000, 12/12 shipped within its96-hour cutoff.
The header also selects the `selected-stretch-32` final replay, 32/32 shipped
over240 hours. These individual traces illustrate the policies; the final
probability-weighted results and limitations remain in
[Stage2 results](docs/STAGE2_RESULTS.md). Both controllers are classical.

The frozen final-evaluation bundle is retained on `main`, except three
files above GitHub's100MiB blob limit, preserved as release assets with exact
sizes and SHA-256 digests in
[the artifact index](output/stage2-search/REMOTE_ARTIFACTS.json).
To restore those optional full archives and the oversized development report:

```sh
gh release download stage2-final-2026-10-17 --repo Kolo-Naukowe-Axion/qhackathon26 --dir /tmp/qfactoria-release-assets
python3 scripts/restore-large-evidence.py --downloads /tmp/qfactoria-release-assets
```

The smaller10.1MB portable bundle, site assets and ordinary build/test inputs
are included directly in the repository. The hosted viewer contains only
`presentation/`; local Python environments and bulk research files are not
published as website assets.

Four additional development JSON files exceed the GitHub blob limit. Their
lossless gzip copies are included in Git with raw/compressed hashes in
[the compressed evidence index](output/COMPRESSED_EVIDENCE.json).
`npm test` (and therefore `npm run build`) restores and verifies these files
locally using Node built-ins, without a download or credentials. Existing raw
files must match the index; differing files are never overwritten.

Requires Node.js 20 or newer. No package installation or API key is needed for the viewer.

```sh
npm run dev
```

Open [the local factory replay](http://127.0.0.1:4173). The server listens only on this machine. Set `PORT` if 4173 is already occupied.

- **Stage 1 guide:** open `/problem-explanation` from the top navigation. Six chapters explain the problem, interactive schedules, optimality, QUBO penalties and a worked matrix derivation, encodings, selected solver evidence and complexity.
- **Appearance:** Lunar Assembly is the fixed design across the factory, control desk, Stage 1 guide and error page. Frostline and Blueprint are preserved with source and screenshots in `docs/design-archive/2026-10-16-refined-shortlist/`; the earlier seven directions are in the adjacent first-variants archive. The live site has no style picker.
- **Factory:** original pixel-art shop floor with moving parts, processing animations, replay/pause, time scrubbing, speed controls, and part selection.
- **Timeline:** a synchronized Gantt chart; click an operation to jump to it.
- **Validation:** independent checks for coverage, duration, capacity, and precedence, with source/method metadata.
- **Present:** a compact presentation layout, with fullscreen where the browser permits it. Space plays/pauses when the page background has focus.
- **Import JSON:** load either the official baseline output format or an `axion-replay.v1` file. Imported metadata is self-reported. Data is processed locally in the browser.
- **Export replay:** download the display wrapper with its source labels; this is separate from the required solver-generated baseline schedule files.

The built-in 2×2 and 3×3 schedules are **illustrations copied from the organizer documents**. The 9-hour comparison is a hand-authored illustration. Actual verified solver schedules now exist separately as `schedule_2x2.json` (QAOA simulator, 4 h) and `schedule_3x3.json` (QAOA simulator, 8 h). Import `output/stage1-compact-ready/quantum-2x2/replay.json` or `output/stage1-compact-ready/quantum-3x3/replay.json` to show the selected real runs; `output/stage1-selected.json` records the selection. No VeloxQ or physical ODRA5 execution is claimed; both are on user hold.

## Checks

Stage 1 formulation/reference preparation runs offline with Python 3, without an API token or additional packages:

```sh
python3 -m solver.stage1
python3 -m unittest discover -s tests -p 'test_stage1.py' -v
```

For actual solver runs, use the pinned Python 3.11 environment and complete preparation command:

```sh
uv venv --python 3.11 .venv
uv pip sync --python .venv/bin/python requirements-solver.lock.txt
.venv/bin/python scripts/prepare-stage1.py --output output/stage1-reproduction
```

The complete command runs the solver tests, original formulation audit, compact QAOA for both instances and a matched classical annealer, without invoking either remote adapter. Choose a fresh output directory. Add `--export-final` to update both root schedules, selection and guide evidence. A uses 1 qubit / 1 layer; B uses 3 qubits / 2 layers. Twenty fresh seeds returned 81,920/81,920 optimal measurements per instance, at exact makespans 4/8 h. See [current formulation, experiments and limitations](docs/STAGE1_COMPACT.md). The compact cost construction evaluates all 2/6 common orders classically; no quantum speedup or scalable compilation is claimed. Use `--time-indexed` to reproduce the earlier 4/39-bit methods and [earlier refinement](docs/STAGE1_REFINEMENT.md).

```sh
npm run check
npm test
npm run build
```

Tests cover schedule feasibility, boundary-time replay state, invalid data, the official JSON adapter, and agreement between the viewer's processing durations and the transcribed official inputs.

The build runs all model tests and syntax checks, then copies only `presentation/`
to `dist/`. No environment variables, backend, database, or third-party runtime
dependencies are required.

## Project material

- `CONTEXT.md`: authoritative requirements, user decisions, known limitations, and current status.
- `instances/`: the two official input datasets transcribed from §14.
- `STAGE1_PLAN.md`: baseline method and evidence plan.
- `DEVELOPMENT_LOG.md`: dated development record, including decisions and rejected approaches.
- `PROJECT_DESIGN.md`: current display model and planned solver interface.
- `docs/PRESENTATION_DESIGN.md`: visual and interaction direction.
- `docs/VELOXQ_IDEAS.md`: proposed VeloxQ formulation and experiment directions.
- `literature/`: curated papers and guides — `STAGE2_LITERATURE.md` (Stage 2 extension), `BASELINE_METHODS_REVIEW.md` (baseline formulation, encodings, QAOA variants, penalties, VeloxQ), `reading_list.csv`, local PDFs where openly available.
- `docs/METHODS_TUTORIAL.html`: self-contained beginner tutorial (open in a browser) on flow shops, QUBOs, time-indexed and domain-wall encodings, QAOA mixers, penalties and hybrid VeloxQ use, with an interactive 2×2 energy explorer.

- `docs/STAGE2_ENVIRONMENT.md`: ambitious Stage 2 factory proposal, physical/information rules, solver boundaries and evaluation plan.
- `docs/STAGE2_IDEATION.md`: eight design/critique iterations and alternatives considered.
- `instances/stage2/metaltech_pressure.json`: synthetic factory design parameters, expanded into complete numerical tables by `stage2/spec.py`.
- `stage2/README.md`: executable Stage 2 factory, controllers, checker, exact references, quantum experiments and current evidence boundaries.
- `presentation/`: browser-native ES modules, original SVG art, and CSS; no frontend framework or external CDN dependency.

## Stage 2 implementation and research

The [combined Stage 2 direction](docs/STAGE2_COMBINED_DIRECTION.md) joins
manufacturing recovery, the measured cost of compact formulations and conditional
capacity economics. It records the checked full-domain versus restricted-pool
recovery result and assesses QOBLIB as an optional external benchmark.
The [independent review passes](docs/STAGE2_REVIEW_PASSES.md) add deterministic
pool enrichment, an exact818-variable deadline decision formulation and measured
local-search/boundary-gate failures, with explicit scope and retained evidence.

**Manufacturing entry refinement resumed by the user, 17 October.** Start with
[the smaller quantum validation and point-by-point evidence](docs/STAGE2_ENTRY.md).
It adds a complete residual manufacturing cell, 18–34 logical-qubit simulated
QAOA, independent references, source-sealed TRAIN/TEST results and offline-only
VeloxQ packets. The larger factory and earlier failures remain separate evidence.
No VeloxQ service request, upload, credit use or physical QPU call was made.

For a fresh local solver demonstration:

```sh
.venv-stage2/bin/python -m stage2.entry_demo --port 4189
# Open http://127.0.0.1:4189/entry/
python3 scripts/verify-stage2-entry.py
```

The `Run fresh QAOA` action computes a new result and independent CP reference;
the static page shows labeled retained evidence. Publication holds still apply.

For the original, broader factory model, start with
[the written factory and encoding walkthrough](docs/stage2-problem/index.html)
([Markdown source](docs/STAGE2_PROBLEM_WALKTHROUGH.md)) for the step-by-step
problem definition, all factory systems and the domain-wall/one-hot distinction.
Then read
[what we actually have](docs/STAGE2_CURRENT_EXPLAINED.md): the full problem,
Stage 1 comparison, all implemented conditions, solver scope, measured results,
QUBO boundaries and limitations. The local interactive
[Start here guide](http://127.0.0.1:4187/stage2/start.html) walks through the same
distinctions visually. Later Mac planning experiments and this explanation are
local working-tree additions; the earlier frozen release does not imply that
these additions have been committed, published or deployed.

For the solution-quality scoring evidence, see
[solution quality against classical references](docs/SOLUTION_QUALITY.md): exact
extended makespan references, the four-pump certified interval, and the later
full-factory realized-primary gap audit. The latter preserves all frozen outcomes
and distinguishes missing-order certificates from deadline/cost optimality.

The implemented Stage 2 domain is a two-hall pump factory with
24 known orders, 72 component lots, 384 nominal manufacturing operations,
15 machines, 4 AGVs, 10 workers, assembly joins, batches, shared tooling,
energy constraints, quality rework and causal disruption recovery. The full
model remains the pressure benchmark; smaller workloads retain its physical
rules. The minute-resolution engine and independent physical checker are in
`stage2/`. Checked experiment records, negative results, source snapshots and
allocation costs are retained under `output/stage2-search/`.

See [`stage2/README.md`](stage2/README.md) for execution and solver scope,
[`docs/STAGE2_EXPERIMENT_LOG.md`](docs/STAGE2_EXPERIMENT_LOG.md) for measured
development results, and [`docs/STAGE2_FINAL_EVALUATION.md`](docs/STAGE2_FINAL_EVALUATION.md)
for the reserved final protocol. The separate local Stage 2 viewer is at
`/stage2/`; its sources distinguish illustrations, checked examples and cohorts.

The earlier structural blueprint remains available for design history:

```sh
python3 scripts/stage2_blueprint.py --output output/stage2-design
```

This legacy script writes `expanded-design.json` and `audit.json`, checking the nominal recipe
DAG, eligible machine/mode durations, order dates, probability mass and selected
resource bounds. It does **not** simulate, schedule, prove feasibility or solve a
QUBO. The executable simulator, controller experiments and trace checker are
separate artifacts. No physical ODRA run or full-factory quantum speedup is claimed.

## AI use

For the current catering extension, Codex also assisted with paired-meal
formulation, program enumeration, independent checking, quantum simulator and
classical reference code, evidence export, the game UI, presentation planning
and documentation. The team's method owners develop and review their adapters
and experiments. Actual catering QAOA evidence is under
`output/catering-complete-cell-v3/` and `output/catering-paired-pilot-v1/`;
the separately authorized initial VeloxQ service results and ledger are under
`output/catering-methods/veloxq/`. Those receipts establish actual calls and
checked outcomes, not a performance advantage. No catering physical-QPU result
is claimed. Team members must understand and defend the submitted work.

The manufacturing entry refinement also used Codex for the complete assignment mixer, offline SDK precision checks, generated evidence view and documentation. Any local draft demo marked synthetic narration uses the macOS text-to-speech voice; it is not a team member speaking. The team must review and can replace that narration before upload.

OpenAI Codex assisted with extracting/checking requirements, planning, the presentation environment, original SVG illustration, baseline QUBO/domain-wall formulations, quantum/local solver code, the exact compact sequence-QUBO construction, SDK adapters, experiments, tests and documentation. The team supplied objectives, references, corrections and direction. Actual solver executions, parameters and samples are retained under `output/stage1-compact-ready/`, the experiment archive `output/stage1-compact/`, and the earlier `output/stage1-local-ready/` / `output/stage1-ready/` archives; Stage 2 implementation and research evidence are under `stage2/` and `output/stage2-search/`. Neither VeloxQ nor physical ODRA5 success is claimed. Team members must review the code, understand the formulation and validation, and explain it during the live defense.

Project source is MIT-licensed. The supplied organizer PDFs are reference material from the organizers and are not relicensed by this project.

Axion's actual logo and brand typefaces are bundled in `presentation/assets/branding/`; font licenses and source attribution are included there.

## Commit and release workflow

Before every commit and push, update the documentation to match the code, selected evidence, commands and known limitations. Refresh the guide’s `presentation/problem-explanation/evidence.js` when `output/stage1-selected.json` changes; the test suite checks the public summary against the selected run metadata. Run the relevant checks before publishing. A push to `main` deploys the static viewer to the personal Vercel project. Deployment authorization does not lift the separate holds on VeloxQ and ODRA5.
