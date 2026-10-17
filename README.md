# Axion Kitchen

QUBO optimization for catering production, built for the QPoland Quantum Hackathon 2026.

Choose batch quantities, allocations, equipment, workers and timing so orders
leave with both a main and a side. The objective prioritizes missed complete
meals, discarded food, new batches and changes to the unstarted plan. Shared
yields, freshness, resource conflicts and mandatory cleaning couple the choices.

## Run the demo

The saved-schedule viewer needs Node.js 20 or newer:

```sh
PORT=4192 npm run dev
```

Open [the kitchen](http://127.0.0.1:4192/catering/). It starts with the larger
outage-and-urgent-order case; choose Complete small cell for the encoding walkthrough.
This replays checked results;
it does not launch a solver. Click a batch to inspect its instructions or skip
it in a checked intervention. The board reports meal handovers and discarded
component portions at the current replay time. Use **Jump to final outcome**
on the production clipboard to see the completed service; playback holds there.
Open [Benchmarks](http://127.0.0.1:4192/catering/benchmarks/) to filter retained
QAOA, VQE, VeloxQ and classical results by case, configuration and budget.

For the presentation studio and fresh local QAOA sampling, create the pinned
foundation environment with **Python 3.12+** (verified with 3.14.6):

```sh
python3 -m venv .venv-catering
.venv-catering/bin/python -m pip install -r catering/requirements.txt
.venv-catering/bin/python scripts/serve-catering-showcase.py --port 4193
```

Dependencies were verified with Python 3.14.6. Open [the live route](http://127.0.0.1:4193/?mode=live).
The sample button reuses saved QAOA angles; it performs no training or backend
call. Arrow keys change chapters, Space plays the current chapter, P hides
operator controls, F enters full screen, and R starts the rehearsal clock. See the [studio guide](scripts/catering-showcase/README.md).

## Read and present

| Need | Start here |
|---|---|
| Model, variables, constraints and correctness proofs | [Project design](PROJECT_DESIGN.md) |
| Measured quality, controls and scope limits | [Quality audit](docs/CATERING_QUALITY.md) |
| Interactive comparisons and source hashes | [Benchmark browser](http://127.0.0.1:4192/catering/benchmarks/) |
| Setup, reproduction and frozen inputs | [Catering guide](catering/README.md) |
| Video narration | [Timecoded script](docs/CATERING_VOICEOVER.md) |
| Video capture and edit preparation | [Recording sheet](docs/CATERING_RECORDING.md) |
| Live demo and speaker cues | [Live runbook](docs/CATERING_LIVE.md) |
| Likely jury questions | [Q&A sheet](docs/CATERING_QA.md) |
| Deliverables, scoring and remaining gates | [Submission checklist](docs/STAGE2_SUBMISSION.md) |
| Other documents and historical work | [Documentation index](docs/README.md) |

## Evidence and current status

The selected baseline B QUBO uses **3 bits**, compared with the official
72-variable time-indexed model at H=8, or 39 after start-window pruning. This
represents all six common job permutations with classical cost tabulation;
it is not an encoding of every timed schedule. See the [baseline derivation](docs/STAGE1_COMPACT.md).
The [price-of-realism ledger](PROJECT_DESIGN.md#51-the-price-of-realism) compares
the extension's register costs with an explicitly defined time-indexed comparator.

- Stage 1: checked QAOA simulator schedules at **4 h / 8 h** in
  [schedule_2x2.json](schedule_2x2.json) and [schedule_3x3.json](schedule_3x3.json).
- Complete catering cell: all 32 legal programs, **35 data qubits**, and an
  exactly simulated 1,045-state one-hot sector. Six QAOA trials and both controls
  find the certified tuple **(0,0,2,2)**: 20 meals, zero waste, two new batches.
- Larger QAOA pilot: six of eight final incumbents attain their final offered-pool
  optimum; all eight trail the full-grid reference. This measures representation
  and search losses, without establishing quantum superiority.
- Trained QAOA: **400 retained runs**; the frozen setup samples each held-out
  portfolio optimum in 10/10 seeds at both evaluation budgets.
- VQE: primary held-out CSV median optimum probabilities **12.4% / 12.8%**,
  with 10/10 and 9/10 sampled hits; five exported schedules independently checked.
  Budgets and final shots differ from QAOA, so no matched-budget winner is claimed.
- VeloxQ: proven idle elimination returns **512/512 valid samples** at actual
  widths **486 / 998 / 2,022**. The [representation study](docs/CATERING_VELOXQ_TUNING.md)
  retains all jobs; CP/SA still find better schedules. These are solver bits.
- The revised 4:20 video script and 2:45 live route are prepared. The old silent
  v2 cut predates these result screens. Final human voiceover/recording, upload,
  rehearsal and submission remain open.
  No catering physical-QPU result is claimed.

## Verify

```sh
.venv-catering/bin/python scripts/check-catering-demo.py
npm run build
```

For the complete local release check, run
`.venv-catering/bin/python scripts/check-catering-release.py --output /tmp/axion-check-01`
after the setup above. It checks retained evidence and performs three fresh
sampling executions; it records no video, retrains no campaign and calls no
service. Add `--full-qaoa` to independently recheck every archived QAOA return.
The receipt keeps human rehearsal and final release/submission gates pending.
The [final review receipt](output/catering-submission-review-v1/verification.json)
records the tested source commit, all 13 checks and remaining human steps.

The build runs site tests and syntax checks, then copies only `presentation/`
to `dist/`. See the [catering guide](catering/README.md) for Python math,
checker, circuit and adapter checks. Restore large retained matrices with
`node scripts/restore-compressed-evidence.mjs`; never overwrite differing evidence.

Frozen inputs, result JSONs and source snapshots retain their paths and hashes.
Earlier factory studies and planning notes are under [the archive](docs/archive/README.md).
The earlier executable implementation remains in [stage2/](stage2/README.md).

## License, AI use and release

Source is [MIT-licensed](LICENSE). Organizer PDFs and third-party art/fonts retain
their own terms; attribution is bundled with the assets.

OpenAI Codex assisted with formulation, code, checks, experiments, UI and docs.
The team supplied the problem choices, constraints and corrections, and reviews
and defends the work. Actual executions and their limitations are recorded in
[the development log](DEVELOPMENT_LOG.md) and retained evidence. AI-written
explanations are not experimental results.

Production opens [the catering demo](https://qfactoria.com/catering/); the
[Stage 1 viewer](https://qfactoria.com/baseline/) remains available. The production
root redirects to catering.

GitHub remains private until the final release step. A push to `main` triggers
the configured static-viewer deployment; it does not publish repository docs or
local videos. Public source access, the final video URL and submission receipt
must be verified before turn-in. No new paid backend or QPU call is authorized
by these instructions.
