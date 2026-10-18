# Final video and recording notes — 4:20

[Watch the final video](https://qfactoria.com/video/) · [Narration](CATERING_VOICEOVER.md) · [Live route](CATERING_LIVE.md)

The completed local export is [axion-kitchen.mp4](../output/submission-final/axion-kitchen.mp4):
1920×1080, 4:20, H.264 video with AAC narration, English selectable subtitles
and twelve chapter markers. [manifest.json](../output/submission-final/manifest.json)
records media hashes, source hashes and the export checks. Publication and organizer
submission are separate states; this document does not assert submission.

## What was captured

The video edits actual browser UI captures. The animated service section was
captured at five frames per second and encoded into a 30-fps output; model,
code and result frames are held for reading. It is not a continuous screen recording.
The QAOA chapter includes a real button launch, its RUNNING state and its CHECKED
receipt: 20 complete meals, zero waste and 2,173 valid shots from 4,096 samples
at 2026-10-18 10:18:04 UTC. Editorial holds do not measure process runtime.
The retained kitchen replay has a separate label. This capture made no training
runs, VeloxQ submissions or physical-QPU jobs.

Narration uses Kokoro's stock `af_heart` synthetic voice, with no voice cloning.
[voice-manifest.json](../output/submission-final/voice-manifest.json) records
model/engine attribution, pronunciation text and chapter alignment;
[captions.srt](../output/submission-final/captions.srt) retains the subtitles.

## Picture and edit plan

Generated from [story.json](../scripts/catering-showcase/story.json).

| Video time | Picture | Hold / edit cue |
|---|---|---|
| 0:00–0:26 | Four-second title, five-second Stage 1 schedule frame, then production-scheduling inputs and factory-to-kitchen mapping. | Opening 0:00–0:04; actual Stage 1 A/B Gantts 0:04–0:09; extension inputs and mapping from 0:09. Selected compact baselines use classically tabulated permutation costs. |
| 0:26–0:50 | Two locally valid batch programs clash on C2; the selected alternative serves both orders. | The displayed x1/x3 witness is from the frozen cell, not a fabricated conflict. The retained QAOA plan selects x3 and x11. Hold 20/20 at the end. |
| 0:50–1:02 | Same plan with only side C removed. | Show 0/20 meals and 20 discarded portions. Retain the manual-intervention label; this is not a new optimizer result. |
| 1:02–1:28 | Selected side-C program, one-hot block and its actual operation timeline; then the compiler excerpt. | Show prep, cooking, packing and parallel cleaning from the frozen x3 program. At 50% in video (75.0 s), replace the operation timeline with actual code in the same space; live switches at 55%. Point to product(...) and span+1. |
| 1:28–1:56 | Paired-coverage truth table, then the actual penalty-bound argument. | Switch to the proof at 53% in video (102.84 s), or 60% in live. Define S over the full bit domain, show P=S+1 and E(invalid)≥E(feasible)+1. A heuristic need not reach a ground state; R=B here. |
| 1:56–2:14 | S3 repair/clean timestamps and actual resource replay. | This is the independently checked raw reference. Keep it distinct from the cell QAOA replay. |
| 2:14–2:39 | Actual local launch, followed by its fresh checked receipt. | Preserve the click-to-completion sequence. Hold meals, waste and valid shots; do not replace a failed launch with an unlabeled saved result. |
| 2:39–3:08 | Held-out QAOA trained-versus-random probability bars. | Keep 256 evaluations, ten seeds and offered-pool scope on screen; do not crop the restriction gap. |
| 3:08–3:28 | VQE/QAOA per-shot probabilities with unequal-budget note. | Show reported medians and final shot counts. No matched-budget ranking or hardware-speed claim. |
| 3:28–3:56 | VeloxQ-only starting plans improved through repeated two-block conditional QUBOs; three widths with classical controls and total runtime. | All block pairs are swept; each subproblem is capped at 40 variables. 71 submissions include five failures. Total adapter time is 565.4 s, backend time 126.784 s; these exclude the earlier cold-start generation. One seed per width. Exact controls match or improve final tuples; CP at 240 s / four workers has lower U at every width. Do not call this a matched-budget win. |
| 3:56–4:08 | Source QUBO widths and pair counts beside the joint-choice explanation. | The table reports source matrices, not circuit qubits or the full generated domain. 636,882 pairs is measured; no hardness or speedup conclusion follows. |
| 4:08–4:20 | Finished retained plan: 20 meals/0 waste beside three concrete development-log decisions. | Keep correction of repair cleaning, paired-service objective and idle-elimination proof visible; these summarize the development log. Final source links stay below. |

## Optional replacement capture

Start the [local studio](../scripts/catering-showcase/README.md) and run
`.venv-catering/bin/python scripts/check-catering-demo.py` before capturing.
Use `http://127.0.0.1:4193/?export=1` for the fixed 1920×1080 stage; operator
controls sit below it and must stay outside the final crop. Retain source hashes
and actual launch receipts with any replacement export.

The separate `scripts/capture-catering-showcase.mjs --dry-run` helper captures
stills without sampling or video; `--record` instead creates a silent continuous
route and performs two frozen-angle local samples (preview and recording).
That optional helper requires Chromium, Playwright and ffmpeg. It was not the
capture method used for this final edited video.

If narration or evidence changes, regenerate the affected audio and picture
from the same story, update subtitles and hashes, and review the resulting file
with sound. Keep the export below five minutes and verify the public watch link
after deployment.
