# Axion Kitchen: live operator and speaker sheet

The prerecorded submission video and the live slot are separate requirements:
video ≤5 minutes; live presentation ≤3 minutes plus about 2 minutes Q&A. This is the
shorter live route. Aim for 2:45 and leave transition margin.

## Before the slot

Run `.venv-stage2/bin/python scripts/serve-catering-showcase.py --port 4193`
from the repository root. Open <http://127.0.0.1:4193/?mode=live> and the
[Q&A sheet](CATERING_QA.md) in a separate private window. Keep the existing
<http://127.0.0.1:4192/catering/> replay available as a fallback. Do not start a
second server if the studio is already running.

Share only the presentation window. Enter full screen. The live route starts
paused. One operator advances with Right Arrow while one speaker talks. The
notes, browser tabs, terminal paths and Q&A sheet should stay outside the share.
Press Space to animate a chapter. It holds automatically at the end; Right
Arrow advances when the speaker is ready. Arrows alone change screens without
playing them. Press P for audience view: it hides controls and speaker notes;
press P again to restore them. F enters full screen. For service, let the timeline reach the
second departure; for encoding, play past halfway to reveal the source excerpt.
Use the sample button in the execution chapter; no API credentials are needed.

## Timed route and short script

| Target | Screen / operator action | Read-aloud cue |
|---|---|---|
|0:00–0:08 | Hook | “Our baseline schedules finish in four and eight hours. Our extension schedules batches that must become complete meals.” |
|0:08–0:30 | Service; let playback illustrate the schedule or seek toward the departure | “Each order needs a main and a side before departure. Main A is committed. We choose Main B and one shared twenty-portion side batch. Separate cookers overlap, but packing still has to serve both tickets.” |
|0:30–0:42 | Counterfactual | “Skipping that side leaves both orders incomplete and discards twenty component portions. This is a checked manual intervention.” |
|0:42–1:04 | Encoding; optionally play the chapter to reveal the code excerpt | “Each bit selects one locally valid batch program, including quantity, resources and times. An anchor block chooses one program or idle. Pairwise conflicts enforce compatibility. We offer every legal program of this small cell.” |
|1:04–1:29 | Loss | “Main times side represents complete service. Their sum minus twice that product counts unpaired food. Both expand quadratically without product qubits. We prioritize missed meals, waste, batches and changes. Proven bounds establish the priority order and hard-constraint penalty.” |
|1:29–1:49 | Run; click Sample frozen-angle QAOA | “QAOA applies cost phases and blockwise XY mixing, then samples. The mixer preserves one choice per block; the checker still rejects resource and allocation conflicts. This button reuses saved angles for a fresh local sample.” |
|1:49–2:14 | Results | “All six small-cell trials found the optimum, as did the controls. Six of eight larger final incumbents match their offered-pool optimum, while all trail the raw-grid reference. That measures representation loss separately from search loss.” |
|2:14–2:34 | VeloxQ | “The same meal model scales to larger VeloxQ workloads. We preserve integer packets and verify returned schedules. This frame will use the owner's final checked settings and comparison.” |
|2:34–2:45 | Close | “The selected schedule serves twenty meals with no discarded portions. The repository contains the model, proofs, code, all measured trials and the development log.” |

The VeloxQ sentence is a rehearsal placeholder. Replace it with one precise
measured finding before the final talk. Likewise update the primary-method
name only when its source-hashed result is integrated. The route is a speaking
aid; avoid reading long appendix tables during the three minutes.

## Freeze-angle launch details

The runner verifies the retained complete-cell input/parameter hashes, uses
p=1 and seed 17102026, samples 4096 shots locally, saves raw samples and rechecks
them. Current rehearsal output is (U,W,B,R)=(0,0,2,2), 20 complete meals and 0 waste
portions, with 3771/4096 valid shots. It observed the displayed retained replay's
exact bitstring 8 times. The two labels remain distinct: retained replay and
fresh sampler output. These are repeated executions of one fixed instance,
not additional independent research trials or evidence of a speedup.

Its sample/evolve/check stage took roughly 0.07–0.18 seconds after imports in
local rehearsals. Browser startup, Python imports and the full request have additional
cost. Do not present that partial timing as an end-to-end solver comparison.

## Recovery plan

- If the button fails: say, “The fresh launch hasn't completed; we'll use the
  retained checked schedule to explain the result.” Continue in the kitchen.
- If the studio fails: switch to the existing `/catering/` viewer and use the
  shared-side/timeline walkthrough. That is saved evidence, clearly labeled.
- If the network/video service fails: keep the local studio, MP4 and screenshots
  on the presenting laptop. The normal local demo requires no internet.
- If the question is unclear: ask whether they mean raw-grid or offered-domain
  quality, or encoding correctness versus solver performance. Then answer one point.

Practice three timed runs. Keep each under 2:50. After final result selection,
check every spoken number against the frozen release; do not update model inputs
or interrupt other owners' runs merely to prepare this presentation.
