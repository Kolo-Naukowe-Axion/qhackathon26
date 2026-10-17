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
Arrows change chapters. Space plays/pauses. F enters full screen.
Speaker notes stay outside the recorded stage. Use a dedicated shared window.

## What the live button actually does

It runs `scripts/catering_live.py`: loads the frozen complete-cell bundle,
checks manifest hashes, loads the retained p1/seed2026 parameters, evolves
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

`story.json` is the editable chapter order, duration and narration source.
`evidence.json` is a small read-only export of the retained audited results,
including source hashes and an actual compiler excerpt. Final method-owner
selection and the VeloxQ final comparison remain replacement slots.

Record the actual local studio with the capture script:

```sh
AXION_NODE_MODULES=/path/to/bundled/node_modules \
node scripts/capture-catering-showcase.mjs \
  --output output/playwright/catering-showcase-v1/recording --record
```

The optional environment path is unnecessary if `playwright` is installed
normally. Chromium and ffmpeg are required. Capture makes preview stills,
then opens a separate context for a continuous studio recording. It performs
one local sample during still QA and one during the recorded execution chapter.
The result is a silent MP4, with a receipt and actual fresh-sampling metadata.

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
