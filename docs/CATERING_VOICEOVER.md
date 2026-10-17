# Video narration — 4:20

Generated from [story.json](../scripts/catering-showcase/story.json). Edit that
source, then run `npm run docs:write`. This is a human voiceover draft; the
QAOA and VeloxQ paragraphs use integrated checked results; VQE separates
reported campaign medians from checked exported schedules.

## 0:00–0:26 · The catering problem

> Stage One reaches four and eight hours. Our extension plans catering production: batch quantities and shared allocations, cookers and qualified workers, and preparation, cooking, packing and cleaning. Departures, freshness and resource calendars constrain the plan. Urgent orders and outages trigger replanning while started work stays fixed. We minimize missed meals, waste, batches and changes.

## 0:26–0:50 · Two orders sharing a side batch

> Two customers each need ten meals. Main A is already cooking. We choose Main B and a twenty-portion side batch shared between both orders. The schedule assigns equipment, workers, preparation, cooking, packing and cleaning. Separate cookers can overlap, but both orders use the same packing line.

## 0:50–1:02 · What happens without the side batch

> Remove the side batch and neither order receives a complete meal, despite both mains being cooked. Twenty component portions are discarded. This is a checked manual intervention that exposes the consequence of a batch choice.

## 1:02–1:28 · Batch selection and scheduling constraints

> Each program describes one batch: quantity, allocations, equipment, crew and phase times. A bit selects it. Programs sharing an anchor demand form a one-hot block with an idle choice. Cross-block penalties forbid duplicate allocations and resource clashes. The small cell includes all thirty-two legal programs, plus three idle bits.

## 1:28–1:56 · Complete meals and food waste

> For a meal lot, binary main coverage times side coverage gives complete service. Their sum minus twice their product counts unpaired components. Coverage is linear in batch-selection bits, so both expressions remain quadratic without auxiliary product bits. We prioritize missed meals, waste, batches and plan changes. Integer bounds prove that ordering and the hard-constraint penalty.

## 1:56–2:14 · Mandatory cleaning after repair

> A repaired cooker still needs cleaning. Here the qualified worker first finishes committed work, then cleans the repaired cooker from eleven forty to eleven fifty. Both worker and cooker are reserved. The independent checker reconstructs these intervals, freshness and meal handovers from raw schedule records.

## 2:14–2:39 · Run the trained QAOA circuit locally

> We now run the trained depth-three circuit locally with its saved angles. Cost and conflict phases alternate with blockwise XY mixing. That mixer preserves one choice per block; the checker still rejects cross-block resource and allocation clashes. We sample four thousand ninety-six shots and check every distinct schedule. This is fresh sampling of the selected training-case circuit, with no retraining or remote calls.

## 2:39–3:08 · QAOA: trained angles improve sampling

> We selected the QAOA configuration on the cell and S0/S1. On held-out S2/S3, it finds the offered-pool optimum in all ten seeds at both budgets. At two hundred fifty-six evaluations, median optimum probability per shot is about eleven and twenty-two times random-angle search. Angles are optimized per instance. These restricted portfolios still exclude better full-grid schedules.

## 3:08–3:28 · VQE concentrates more probability on the optimum

> VQE uses one-hot Givens gates and controlled rotations between coupled blocks. With exact CVaR and adjoint gradients, median optimum probability is about twelve percent on both held-out cases. That exceeds our QAOA probability, but parameter counts, training budgets and final shots differ. The primary VQE setup hits ten of ten and nine of ten seeds.

## 3:28–3:56 · VeloxQ: fix the representation

> VeloxQ uses the larger version of the same kitchen. We proved that idle choices can be removed: selecting no program in a block means idle. A tighter deletion bound preserves feasibility and the optimal schedules. On the five-hundred-twelve-bit source at equal twenty-thousand steps, valid returns rise from seventeen to all five hundred twelve. The new representation also returns all-valid samples at nine hundred ninety-eight and two thousand twenty-two solver variables. Classical controls still find better schedules.

## 3:56–4:08 · What scales, and where each method fits

> More orders and time choices create more programs and conflicts. QAOA uses thirty-one to thirty-five qubits in explicitly restricted portfolios. VeloxQ runs the larger coupled matrices. Classical references measure quality and representation loss. Variable count alone does not prove classical hardness or quantum advantage.

## 4:08–4:20 · Checked results and benchmarks

> The checked cell serves twenty meals with no discarded portions. The benchmark page compares every retained campaign and explains the scaling limits. Our repository contains the formulation, proofs, source-hashed results and development log.

## Recording notes

611 spoken words. Leave pauses for the code, equation and actual launch.
The current local MP4 is silent. Its pictures remain useful, but record the
updated narration for this result set. Earlier cuts have obsolete result slides.

Record one paragraph at a time in a quiet room. Align and retime the visuals,
add final subtitles, and check the export end to end. Keep the submitted video
below five minutes. The screen recording and live slot are separate deliverables.
