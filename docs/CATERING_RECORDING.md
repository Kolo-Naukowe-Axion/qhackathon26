# Recording sheet — 4:20

Generated from [story.json](../scripts/catering-showcase/story.json). The method
emphasis is frozen: QAOA fresh local execution, VQE comparison with unequal
budgets, and the proved VeloxQ representation change. Human voiceover and
final capture remain pending. The old v2 MP4 predates these screens.

## Dry run now

For capture only, install Playwright once: `npm install --no-save --package-lock=false playwright@1.62.1`, then `npx playwright install chromium`. Start the [local studio](../scripts/catering-showcase/README.md), then run:

```sh
.venv-catering/bin/python scripts/check-catering-demo.py
node scripts/capture-catering-showcase.mjs --dry-run \
  --output output/playwright/catering-showcase-final/dry-run
```

This captures chapter stills and a hash receipt only. It blocks the sampler
endpoint, records zero video, and makes no service/QPU calls. Check all twelve
stills at full size, the compiler excerpt, and the live-mode still. The receipt
must say dry_run=true, sampling_runs=0 and continuous_studio_capture=false.

## Picture and edit plan

| Video time | Picture | Hold / edit cue |
|---|---|---|
| 0:00–0:26 | Four-second Axion Kitchen title over the kitchen, then the implemented problem. | Opening is 0:00–0:04 within this chapter. Reveal the problem at 0:04; keep all constraints and the priority order readable. |
| 0:26–0:50 | Retained solver plan replays through both departures. | Hold the final 20/20 count long enough to read. The label must say retained QAOA sample. |
| 0:50–1:02 | Same plan with only side C removed. | Show 0/20 meals and 20 discarded portions. Retain the manual-intervention label; this is not a new optimizer result. |
| 1:02–1:28 | Side-C program bit, one-hot block, then actual compiler excerpt. | Show the program first, then actual code after 55%: product(...) expands coverage products; span+1 bounds the hard penalty. Point at the highlighted source lines. |
| 1:28–1:56 | Paired coverage truth table, quadratic objective and penalty. | Point to the main-times-side term; keep priority and ground-state proof readable. R=B is a fixture caveat, not a claimed stability gain. |
| 1:56–2:14 | S3 repair/clean timestamps and actual resource replay. | This is the independently checked raw reference. Keep it distinct from the cell QAOA replay. |
| 2:14–2:39 | Actual local launch, followed by its fresh checked receipt. | Preserve the click-to-completion sequence. Hold meals, waste and valid shots; do not replace a failed launch with an unlabeled saved result. |
| 2:39–3:08 | Held-out QAOA trained-versus-random probability bars. | Keep 256 evaluations, ten seeds and offered-pool scope on screen; do not crop the restriction gap. |
| 3:08–3:28 | VQE/QAOA per-shot probabilities with unequal-budget note. | Show reported medians and final shot counts. No matched-budget ranking or hardware-speed claim. |
| 3:28–3:56 | Idle elimination: best plan serves 10→50 of 140 meals; validity 17→512/512 at equal steps. | Keep 20,000 steps and single-job scope visible. Waste rises 30→60 portions because service has priority. Same source programs/objective, different sampling matrices; CP/SA still better. |
| 3:56–4:08 | Program/conflict growth and distinct compute regimes. | Keep portfolio qubits separate from VeloxQ solver variables. Benchmark link is the optional inspection route. |
| 4:08–4:20 | Finished retained plan: 20 meals/0 waste beside three concrete development-log decisions. | Keep correction of repair cleaning, paired-service objective and idle-elimination proof visible; these summarize the development log. Final source links stay below. |

## Final capture, later

After the team approves the words and rehearses, use the same capture command
with `--record` instead of `--dry-run` and a fresh recording directory. This
records the continuous 4:20 studio route and executes the frozen-angle
local sampler. Keep its raw sample receipt alongside the MP4. No new training
or backend job is needed. Do not mix a dry-run still of an unlaunched circuit
with narration claiming a completed live execution.

Record human narration from [CATERING_VOICEOVER.md](CATERING_VOICEOVER.md), one
paragraph per take. Leave the model, code and result numbers readable; subtitles
must preserve method names, units and scope. Review the final file with sound,
verify duration ≤5:00, and check final public links after release. Upload and
submission are separate steps.
