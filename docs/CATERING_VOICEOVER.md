# Video narration — 4:20

[Watch the final video](https://qfactoria.com/video/) · [Local MP4](../output/submission-final/axion-kitchen.mp4)

The completed narration uses Kokoro's stock `af_heart` synthetic voice;
no voice was cloned. [Voice manifest](../output/submission-final/voice-manifest.json)
records the engine/model attribution, pronunciation adjustments and chapter timing.
English selectable subtitles are included in the MP4 and available as
[captions.srt](../output/submission-final/captions.srt).

This text is generated from [story.json](../scripts/catering-showcase/story.json).
Edit that source, then run `npm run docs:write`. QAOA and VeloxQ use integrated
checked results; VQE separates reported campaign medians from checked exported schedules.

## 0:00–0:26 · The catering problem

> Axion Kitchen: quantum optimization for catering production. We completed the factory baselines in four and eight hours, both checked optimal. Our extension chooses shared batch yields, allocations, equipment, qualified workers and phase times. Cookers are machines, cleaning is setup, and departures are due dates. Freshness, calendars, outages and committed work constrain replanning. Complete meals come first, then waste, batches and changes.

## 0:26–0:50 · Two orders sharing a side batch

> Two customers each need ten meals. Main A is already cooking. A shared twenty-portion side batch can serve both. But the side and one Main B option want cooker C2 at the same time. The checked QAOA plan pairs that side with a different Main B program on C1. Both orders depart complete.

## 0:50–1:02 · What happens without the side batch

> Remove only the side batch. Neither order receives a complete meal; twenty main portions are wasted. This checked manual intervention shows why the objective couples main and side.

## 1:02–1:28 · Batch selection and scheduling constraints

> A bit selects a locally valid batch: its quantity, allocations, resources and times. Programs with the same anchor share demand, so a block chooses one program or idle. Cross-block penalties exclude clashes. In the code, product expands coverage products; coefficient span plus one sets the penalty. This cell uses thirty-two programs and three idle bits. Restricted portfolios can exclude better schedules.

## 1:28–1:56 · Complete meals and food waste

> Main coverage times side coverage gives complete service; their sum minus twice the product counts unpaired food. Both coverages are linear in batch bits, so the objective stays quadratic. Each priority weight dominates all lower costs combined. For hard constraints, P equals the full objective coefficient span plus one. A violation therefore cannot beat any feasible schedule. This guarantees feasible ground states, not heuristic convergence.

## 1:56–2:14 · Mandatory cleaning after repair

> A repaired cooker still needs cleaning. Here the qualified worker first finishes committed work, then cleans the repaired cooker from eleven forty to eleven fifty. Both worker and cooker are reserved. The independent checker reconstructs these intervals, freshness and meal handovers from raw schedule records.

## 2:14–2:39 · Run QAOA

> Return to the original batch choices and run the trained depth-three QAOA circuit locally. Cost and conflict phases alternate with blockwise XY mixing. The mixer preserves one choice per block; the independent checker rejects physical clashes. We draw four thousand ninety-six fresh samples with saved angles. The receipt reports the best checked outcome, separately from the retained kitchen replay.

## 2:39–3:08 · QAOA results

> We selected the QAOA configuration on the cell and S0/S1. On held-out S2/S3, it finds the offered-pool optimum in all ten seeds at both budgets. Random-angle search also hits all ten on S2. At two hundred fifty-six evaluations, median optimum probability per shot is about eleven and twenty-two times random-angle search. Angles are optimized per instance. These restricted portfolios still exclude better full-grid schedules.

## 3:08–3:28 · VQE comparison

> VQE uses Givens gates within blocks and controlled rotations between coupled blocks. With exact CVaR and adjoint gradients, median optimum probability is about twelve percent in both held-out cases. Budgets and shots differ from QAOA. The primary setup hits ten of ten and nine of ten seeds.

## 3:28–3:56 · VeloxQ inside the replanning loop

> VeloxQ now drives the replanning loop. Start with its own full plan, free two blocks, solve the conditional QUBO, and accept only a checked improvement. Across three widths, missed meal lots fall from nine to seven, eleven to six, and thirteen to seven. These runs used seventy-one submissions. Exact neighborhood controls match or improve final quality, and longer classical runs remain better. This demonstrates integration, not a speedup.

## 3:56–4:08 · What makes the choices difficult?

> The cell is deliberately small. Larger inputs generate eighteen thousand batch programs. Equipment, workers and paired demand couple their choices. We measure restriction loss and search quality separately.

## 4:08–4:20 · Checked results and benchmarks

> Our log records three decisions: correct repair cleaning, optimize complete-meal service, and prove idle elimination. The checked cell serves twenty meals without waste. Benchmarks and code are linked.

## Editing notes

607 source words; the fastest chapter is 150 words/minute.
Narration is generated sentence by sentence and aligned to the chapter route.
The voice manifest records actual pronunciation text and time stretch. Preserve
pauses for the model, source code and real launch; do not claim a result absent
from the receipt. The final video uses edited actual UI captures, not an unedited
continuous recording.

The separate live presentation uses [its shorter script](CATERING_LIVE.md).
Organizer submission is not implied by this completed local video.
