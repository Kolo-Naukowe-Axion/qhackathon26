# Video narration — 4:20

Generated from [story.json](../scripts/catering-showcase/story.json). Edit that
source, then run `npm run docs:write`. This is a human voiceover draft; the
VeloxQ paragraph must be replaced with its final checked result.

## 0:00–0:12 · Lunch service: 20 meals

> Stage One gives us checked four- and eight-hour schedules. Our extension schedules catering batches: both courses must reach the same departure, and unused food counts as waste.

## 0:12–0:40 · Two orders sharing a side batch

> Two customers each need ten meals. Main A is already cooking. We choose Main B and a twenty-portion side batch shared between both orders. The schedule assigns equipment, workers, preparation, cooking, packing and cleaning. Separate cookers can overlap, but both orders use the same packing line.

## 0:40–1:00 · What happens without the side batch

> Remove the side batch and neither order receives a complete meal, despite both mains being cooked. Twenty component portions are discarded. This is a checked manual intervention that exposes the consequence of a batch choice.

## 1:00–1:34 · Batch selection and scheduling constraints

> Each program describes one batch: quantity, allocations, equipment, crew and phase times. A bit selects it. Programs sharing an anchor demand form a one-hot block with an idle choice. Cross-block penalties forbid duplicate allocations and resource clashes. The small cell includes all thirty-two legal programs, plus three idle bits.

## 1:34–2:10 · Complete meals and food waste

> For a meal lot, binary main coverage times side coverage gives complete service. Their sum minus twice their product counts unpaired components. Coverage is linear in batch-selection bits, so both expressions remain quadratic without auxiliary product bits. We prioritize missed meals, waste, batches and plan changes. Integer bounds prove that ordering and the hard-constraint penalty.

## 2:10–2:35 · Mandatory cleaning after repair

> A repaired cooker still needs cleaning. Here the qualified worker first finishes committed work, then cleans the repaired cooker from eleven forty to eleven fifty. Both worker and cooker are reserved. The independent checker reconstructs these intervals, freshness and meal handovers from raw schedule records.

## 2:35–3:00 · Local QAOA sampling

> QAOA applies cost and conflict phases followed by blockwise XY mixing. We now sample the saved angles locally, without retraining. The mixer preserves one choice per block; equipment, worker and allocation conflicts still need checking. Every distinct returned bitstring is decoded and checked. The receipt reports complete meals, waste and valid shots.

## 3:00–3:35 · Results against exact and classical references

> All six small-cell trials find the certified optimum; the controls find it too. On the larger pilot, six of eight final plans match their final offered-pool optimum. All eight trail the full-grid reference, and final-step controls tie. A solver cannot recover a good schedule excluded by its representation: we measure that loss separately from search.

## 3:35–4:05 · VeloxQ at 512–2,048 variables

> VeloxQ solves larger QUBOs of the same meal model, from five hundred twelve to two thousand forty-eight variables. We preserve integer packets, verify the spin convention and check raw returned schedules. The initial cold runs return few feasible plans. This establishes the integration and identifies the next experiment: improve feasible solution quality under a fixed budget.

## 4:05–4:20 · Results and implementation

> The checked schedule serves twenty meals with no discarded portions. During development, we corrected recovery cleaning and separated portfolio restriction from solver quality. The repository contains the formulation, proofs, raw results and development log.

## Recording notes

454 spoken words. Leave pauses for the code, equation and actual launch.
The current local MP4 is silent. Its pictures remain useful, but record the
updated narration only after final result integration.

Record one paragraph at a time in a quiet room. Align and retime the visuals,
add final subtitles, and check the export end to end. Keep the submitted video
below five minutes. The screen recording and live slot are separate deliverables.
