# Local recording and live-presentation studio

This studio is outside `presentation/`, so the static deployment does not
publish its draft screens or speaker materials. The actual kitchen iframe
uses the existing checked viewer. No shared model or frozen input is modified.

Start from the repository root:

```sh
.venv-stage2/bin/python scripts/serve-catering-showcase.py --port 4193
```

Open `http://127.0.0.1:4193/` for the video cut, or
`http://127.0.0.1:4193/?mode=live` for the shorter manual presentation.
The video route is 260 seconds (4:20); the live route is 165 seconds (2:45).
Before presenting, run `.venv-stage2/bin/python scripts/check-catering-demo.py`.
It checks dependencies, frozen hashes and evidence without starting a sampler.

Arrows change chapters. Space plays/pauses. In live mode each chapter holds at
its end until Right Arrow advances. P toggles audience view, hiding all operator
controls and notes. F enters full screen. R starts/resets the actual rehearsal
clock. That clock continues while chapter animation is paused; it marks 2:45
as wrap-up and 3:00 as over time.
Speaker notes stay outside the recorded stage. Use a dedicated shared window.

## What the live button actually does

It runs `scripts/catering_live.py`: loads the frozen complete-cell bundle,
checks manifest hashes, loads the trained p3/seed2026 parameters from the selected cell/budget256 run, evolves
the exact one-hot sector, draws 4096 fresh local samples with a declared fixed
seed, then independently decodes and checks every raw return.

There is no training, model regeneration, paid service, remote GPU or physical
QPU call. A new execution with the same seed is reproducible, not an independent
training trial. Retained UI replay and fresh sample receipts keep separate labels.
The server binds 127.0.0.1 only; its fixed local sampler endpoint checks Origin.

Terminal fallback, using a fresh output directory each time:

```sh
.venv-stage2/bin/python scripts/catering_live.py --output output/NEW-LIVE-RUN
```

If fresh launch fails, use the retained kitchen viewer, disclose the fallback
and continue. Do not represent replay as completed fresh execution.

## Recording and human voiceover

`story.json` is the single source for video and live narration, actions and
durations, shot framing and edit cues. `npm run docs:write` regenerates the speaker
scripts and [recording sheet](../../docs/CATERING_RECORDING.md);
`npm run docs:check` prevents drift. Live mode shows `live_narration`.
`playback.js` handles continuous video timing and live chapter holds.
`evidence.json` is a small read-only export of the retained audited results,
including source hashes and an actual compiler excerpt. It includes the 400-run QAOA campaign, reported held-out VQE aggregates and
checked exported plans, plus the proven no-idle VeloxQ representation study.
The linked `/catering/benchmarks/` page exposes runs, budgets and source hashes.

Prepare stills without a video or sampler execution first:

```sh
AXION_NODE_MODULES=/path/to/bundled/node_modules \
node scripts/capture-catering-showcase.mjs --dry-run \
  --output output/playwright/catering-showcase-v4/dry-run
```

No flags also defaults to this stills-only dry run. `--sample` explicitly adds
one frozen-angle local sample to the stills. `--dry-run` refuses either
`--sample` or `--record`; its receipt must report zero sampling and video.

Later, record the actual local studio with the capture script:

```sh
AXION_NODE_MODULES=/path/to/bundled/node_modules \
node scripts/capture-catering-showcase.mjs \
  --output output/playwright/catering-showcase-v4/recording --record
```

The optional environment path is unnecessary if `playwright` is installed
normally. Chromium and ffmpeg are required. Capture makes preview stills,
then opens a separate context for a continuous studio recording. It performs
one local sample during still QA and one during the recorded execution chapter.
The result is a silent MP4, with a receipt, hashes of the studio sources and
preserved raw fresh samples. Current v3 stills and browser verification are under
`output/playwright/catering-showcase-v3/`. The existing silent v2 cut at
`output/playwright/catering-showcase-v2/recording/` predates the current problem
overview and new QAOA/VQE/VeloxQ/scaling chapters. Record v3 before final editing;
older footage is a fallback, not evidence of the current script.

The visual playback compresses schedule time and edits between explanatory
screens; it is not a 260-second unedited view of factory time. The sampler action
inside it is real. No synthetic narration or music is added. Record the final
human voiceover after results and wording are frozen, then align and retime the
clips. Keep the final submitted video below five minutes.

Large video/capture outputs remain local under the existing ignored
`output/playwright/` directory. Source and speaker materials can be synced to
the private repository. Uploading/submitting a final video is a later step.

See [presentation plan](../../docs/CATERING_PRESENTATION.md),
[live operator sheet](../../docs/CATERING_LIVE.md) and
[Q&A cheats](../../docs/CATERING_QA.md).
