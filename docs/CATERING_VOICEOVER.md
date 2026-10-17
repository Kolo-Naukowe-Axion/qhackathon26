# Video narration — 4:20

Generated from [story.json](../scripts/catering-showcase/story.json). Edit that
source, then run `npm run docs:write`. This is a human voiceover draft; the
QAOA and VeloxQ paragraphs use integrated checked results; VQE separates
reported campaign medians from checked exported schedules.

## 0:00–0:26 · The catering problem

> Axion Kitchen: quantum optimization for catering production. We plan batch quantities and shared allocations, cookers and qualified workers, and preparation, cooking, packing and cleaning. Departures, freshness and calendars constrain the plan. Urgent orders and outages trigger replanning while started work stays fixed. We minimize missed meals, waste, batches and changes.

## 0:26–0:50 · Two orders sharing a side batch

> Two customers each need ten meals. Main A is already cooking. A checked QAOA sample selects Main B and one twenty-portion side batch shared between both orders. Its schedule assigns equipment, workers and phase times. Both orders leave complete by their departures, using one packing line.

## 0:50–1:02 · What happens without the side batch

> Remove only the side batch. Neither order receives a complete meal; twenty main portions are wasted. This checked manual intervention shows why the objective couples main and side.

## 1:02–1:28 · Batch selection and scheduling constraints

> A bit selects one batch program: quantity, allocations, equipment, crew and phase times. Anchor blocks choose a program or idle; pairwise penalties exclude clashes. In the code, product expands main and side coverage into quadratic terms. The coefficient span plus one sets a safe hard penalty. This complete cell has thirty-two programs and three idle bits.

## 1:28–1:56 · Complete meals and food waste

> For a meal lot, binary main coverage times side coverage gives complete service. Their sum minus twice their product counts unpaired components. Coverage is linear in batch-selection bits, so both expressions remain quadratic without auxiliary product bits. We prioritize missed meals, waste, batches and plan changes. Integer bounds prove that ordering and the hard-constraint penalty.

## 1:56–2:14 · Mandatory cleaning after repair

> A repaired cooker still needs cleaning. Here the qualified worker first finishes committed work, then cleans the repaired cooker from eleven forty to eleven fifty. Both worker and cooker are reserved. The independent checker reconstructs these intervals, freshness and meal handovers from raw schedule records.

## 2:14–2:39 · Run QAOA

> Return to the original batch choices and run the trained depth-three QAOA circuit locally. Cost and conflict phases alternate with blockwise XY mixing. The mixer preserves one choice per block; the independent checker rejects physical clashes. We draw four thousand ninety-six fresh samples with saved angles. The receipt reports the best checked outcome, separately from the retained kitchen replay.

## 2:39–3:08 · QAOA results

> We selected the QAOA configuration on the cell and S0/S1. On held-out S2/S3, it finds the offered-pool optimum in all ten seeds at both budgets. Random-angle search also hits all ten on S2. At two hundred fifty-six evaluations, median optimum probability per shot is about eleven and twenty-two times random-angle search. Angles are optimized per instance. These restricted portfolios still exclude better full-grid schedules.

## 3:08–3:28 · VQE comparison

> VQE uses one-hot Givens gates and controlled rotations between coupled blocks. With exact CVaR and adjoint gradients, median optimum probability is about twelve percent on both held-out cases. That exceeds our QAOA probability, but parameter counts, training budgets and final shots differ. The primary VQE setup hits ten of ten and nine of ten seeds.

## 3:28–3:56 · VeloxQ: remove idle bits

> VeloxQ solves the larger kitchen. Removing redundant idle bits preserves feasible schedules and their objective. At equal twenty-thousand-step budgets, the best checked plan serves fifty meals instead of ten, out of one hundred forty. Waste rises from thirty to sixty portions: complete service has priority. Valid returns rise from seventeen to all five hundred twelve. This is one exploratory job per representation; classical controls still find better plans.

## 3:56–4:08 · From 35 qubits to 2,022 variables

> More orders and time choices create programs and conflicts. Quantum circuits use restricted portfolios; VeloxQ uses larger matrices. The benchmark page separates search quality, restriction loss and feasibility.

## 4:08–4:20 · Checked results and benchmarks

> Our log records three decisions: correct repair cleaning, optimize complete-meal service, and prove idle elimination. The checked cell serves twenty meals without waste. Benchmarks and code are linked.

## Recording notes

582 spoken words; the fastest chapter is 165 words/minute. Leave pauses for the code, equation and actual launch.
The earlier local MP4 is silent and has obsolete result screens. Record the
current route and narration for this result set.

Record one paragraph at a time in a quiet room. Align and retime the visuals,
add final subtitles, and check the export end to end. Keep the submitted video
below five minutes. The screen recording and live slot are separate deliverables.
