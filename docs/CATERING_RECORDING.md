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
| 0:00–0:26 | Four-second title, five-second Stage 1 schedule frame, then production-scheduling inputs and factory-to-kitchen mapping. | Opening 0:00–0:04; actual Stage 1 A/B Gantts 0:04–0:09; extension inputs and mapping from 0:09. Selected compact baselines use classically tabulated permutation costs. |
| 0:26–0:50 | Two locally valid batch programs clash on C2; the selected alternative serves both orders. | The displayed x1/x3 witness is from the frozen cell, not a fabricated conflict. The retained QAOA plan selects x3 and x11. Hold 20/20 at the end. |
| 0:50–1:02 | Same plan with only side C removed. | Show 0/20 meals and 20 discarded portions. Retain the manual-intervention label; this is not a new optimizer result. |
| 1:02–1:28 | Selected side-C program, one-hot block and its actual operation timeline; then the compiler excerpt. | Show prep, cooking, packing and parallel cleaning from the frozen x3 program. After 55%, replace the operation timeline with actual code in the same space; point to product(...) and span+1. |
| 1:28–1:56 | Paired-coverage truth table, then the actual penalty-bound argument. | At 60% switch to the proof. Define S over the full bit domain, show P=S+1 and E(invalid)≥E(feasible)+1. A heuristic need not reach a ground state; R=B here. |
| 1:56–2:14 | S3 repair/clean timestamps and actual resource replay. | This is the independently checked raw reference. Keep it distinct from the cell QAOA replay. |
| 2:14–2:39 | Actual local launch, followed by its fresh checked receipt. | Preserve the click-to-completion sequence. Hold meals, waste and valid shots; do not replace a failed launch with an unlabeled saved result. |
| 2:39–3:08 | Held-out QAOA trained-versus-random probability bars. | Keep 256 evaluations, ten seeds and offered-pool scope on screen; do not crop the restriction gap. |
| 3:08–3:28 | VQE/QAOA per-shot probabilities with unequal-budget note. | Show reported medians and final shot counts. No matched-budget ranking or hardware-speed claim. |
| 3:28–3:56 | Cold-start representation improvement, plus a separately labeled checked 162-bit hybrid improvement of the larger full plan. | Keep cold-start and hybrid evidence separate. Cold: 10→50 of 140 meals, waste30→60, equal20k steps. Hybrid: (8,3,8,8)→(7,4,9,9); offline exact enumeration selected the neighborhood, and longer CP remains better. |
| 3:56–4:08 | Source QUBO widths and pair counts beside the joint-choice explanation. | The table reports source matrices, not circuit qubits or the full generated domain. 636,882 pairs is measured; no hardness or speedup conclusion follows. |
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
