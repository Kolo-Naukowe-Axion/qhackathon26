# Recording and live-presentation studio

[Watch the final video](https://qfactoria.com/video/) · [Live script](../../docs/CATERING_LIVE.md) · [Narration](../../docs/CATERING_VOICEOVER.md)

The final local export is [axion-kitchen.mp4](../../output/submission-4k/axion-kitchen.mp4):
**4:20, 3840×2160**, H.264/AAC, with English selectable subtitles and twelve chapters.
It edits actual UI captures and includes a real local QAOA launch and checked
receipt. Narration uses Kokoro's stock `af_heart` synthetic voice, without cloning.
The [export manifest](../../output/submission-4k/manifest.json) records source
and media hashes. See the [recording notes](../../docs/CATERING_RECORDING.md) for
capture provenance and replacement-export instructions. These artifacts do not
assert organizer submission.

## Start the studio

From the repository root, after installing the documented catering environment:

```sh
.venv-catering/bin/python scripts/serve-catering-showcase.py --port 4193
```

- [Video route](http://127.0.0.1:4193/): 260 seconds (4:20).
- [Live route](http://127.0.0.1:4193/?mode=live): 165 seconds (2:45), holding at each chapter.
- [Full-resolution capture](http://127.0.0.1:4193/?export=2): a fixed 3840×2160 stage, with controls below the picture. Crop those controls from exports; this mode intentionally need not fit a smaller viewport.

Before presenting, run `.venv-catering/bin/python scripts/check-catering-demo.py`.
It checks dependencies, frozen hashes and displayed evidence without sampling.
The studio stays outside the deployed static viewer; the final watch page is
published separately. Its kitchen iframe uses the checked viewer and does not
modify shared models or frozen inputs.

## Controls

Arrows change chapters. Space plays or pauses; in live mode it replays a held
chapter, and Right Arrow advances. Replay cut restarts a completed video.
P hides or restores operator controls and notes. F toggles full screen; if the
browser rejects it, audience view remains available. R resets the rehearsal
clock, which continues during animation holds and marks 2:45 as wrap-up and
3:00 as overtime. Share the audience window, keeping speaker notes outside it.

## The local launch

The button runs `scripts/catering_live.py`. It verifies the frozen complete-cell
bundle and trained depth-three parameters, evolves the exact 1,045-state
one-hot sector, draws 4,096 samples with a declared fixed seed, and independently
checks the decoded outcomes. It performs no training, paid-service, remote-GPU
or physical-QPU call. Repeating that fixed seed is reproducible execution, not
an independent training trial. Fresh receipts and retained replay keep separate
labels; editorial video holds do not measure runtime.

The captured launch at 2026-10-18 10:38:11 UTC returned 20 complete meals, zero
waste and 2,173 valid shots. A later launch must be described using its own receipt.
The server binds only to 127.0.0.1, and the sampler endpoint checks Origin.

Terminal fallback, using a fresh output directory:

```sh
.venv-catering/bin/python scripts/catering_live.py --output output/NEW-LIVE-RUN
```

If execution fails, disclose the failure and use the separately labeled
[retained complete-cell replay](http://127.0.0.1:4192/catering/?case=CELL).

## Source and reproduction

`story.json` controls narration, chapter durations, speaker cues and edit cues.
`npm run docs:write` regenerates the three speaker/recording documents;
`npm run docs:check` catches drift. `playback.js` implements route timing and
live holds. `evidence.json` retains source hashes, the actual compiler excerpt,
QAOA results, reported VQE aggregates and checked plans, and VeloxQ's representation
and replanning-loop studies. [Benchmarks](https://qfactoria.com/catering/benchmarks/)
expose run budgets and source identities.

The final edited video was assembled from browser captures. The optional
`scripts/capture-catering-showcase.mjs` helper is an alternative: `--dry-run`
captures stills with no sampling or video; `--record` produces a silent continuous
route and two frozen-angle local samples. It requires Chromium, Playwright and
ffmpeg, and was not used for the final edited video. Preserve raw receipts and
hashes with any replacement export.

See the [presentation plan](../../docs/CATERING_PRESENTATION.md),
[recording notes](../../docs/CATERING_RECORDING.md) and [Q&A sheet](../../docs/CATERING_QA.md).
