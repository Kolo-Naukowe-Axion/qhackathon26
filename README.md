# QHackathon 2026

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

The built-in 2×2 and 3×3 schedules are **illustrations copied from the organizer documents**. The 9-hour comparison is a hand-authored illustration. Actual verified solver schedules now exist separately as `schedule_2x2.json` (QAOA simulator, 4 h) and `schedule_3x3.json` (classical QUBO annealing, 8 h). Import `output/stage1-local-ready/qaoa-2x2/replay.json` or `output/stage1-local-ready/anneal-3x3/replay.json` to show the selected real runs; `output/stage1-selected.json` records the selection. No VeloxQ or physical ODRA5 execution is claimed; both are on user hold.

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

The complete command executes QAOA and local annealing, verifies both results and audits the formulation, without invoking either remote adapter. Choose a fresh output directory. Add `--export-final` to update the root schedules and current selection. Eighteen local settings were compared; see [refinement results](docs/STAGE1_REFINEMENT.md) and [formulation and evidence](docs/STAGE1_OFFLINE.md).

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
- `instances/stage2/metaltech_pressure.json`: proposed synthetic flagship parameters; incomplete simulator tables are explicitly listed.
- `presentation/`: browser-native ES modules, original SVG art, and CSS; no frontend framework or external CDN dependency.

## Stage 2 design exploration

Stage 2 design exploration: the working proposal is a two-hall pump factory with
24 known orders, 72 component lots, 384 nominal manufacturing operations,
15 machines, 4 AGVs, 10 workers, assembly joins, batches, shared tooling,
energy constraints, quality rework and causal disruption recovery. The full
model is the intended target; small instances serve correctness checks.

```sh
python3 scripts/stage2_blueprint.py --output output/stage2-design
```

This writes `expanded-design.json` and `audit.json`, checking the nominal recipe
DAG, eligible machine/mode durations, order dates, probability mass and selected
resource bounds. It does **not** simulate, schedule, prove feasibility or solve a
QUBO. Missing tables and initial-state work are explicit. The browser environment
still displays Stage 1. Codex assisted with this proposal, critique and blueprint.

## AI use

OpenAI Codex assisted with extracting/checking requirements, planning, the presentation environment, original SVG illustration, baseline QUBO/domain-wall formulations, quantum/local solver code, SDK adapters, experiments, tests and documentation. The team supplied objectives, references, corrections and direction. Actual solver executions, parameters and samples are retained under `output/stage1-local-ready/` and the earlier `output/stage1-ready/` archive; neither VeloxQ nor physical ODRA5 success is claimed. Team members must review the code, understand the formulation and validation, and explain it during the live defense.

Project source is MIT-licensed. The supplied organizer PDFs are reference material from the organizers and are not relicensed by this project.

Axion's actual logo and brand typefaces are bundled in `presentation/assets/branding/`; font licenses and source attribution are included there.

## Commit and release workflow

Before every commit and push, update the documentation to match the code, selected evidence, commands and known limitations. Refresh the guide’s `presentation/problem-explanation/evidence.js` when `output/stage1-selected.json` changes; the test suite checks the public summary against the selected run metadata. Run the relevant checks before publishing. A push to `main` deploys the static viewer to the personal Vercel project. Deployment authorization does not lift the separate holds on VeloxQ and ODRA5.
