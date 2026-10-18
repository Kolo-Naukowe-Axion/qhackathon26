# Video narration — 4:20

Generated from [story.json](../scripts/catering-showcase/story.json). Edit that
source, then run `npm run docs:write`. This is a human voiceover draft; the
QAOA and VeloxQ paragraphs use integrated checked results; VQE separates
reported campaign medians from checked exported schedules.

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

> VQE uses one-hot Givens gates and controlled rotations between coupled blocks. With exact CVaR and adjoint gradients, median optimum probability is about twelve percent on both held-out cases. That exceeds our QAOA probability, but parameter counts, training budgets and final shots differ. The primary VQE setup hits ten of ten and nine of ten seeds.

## 3:28–3:56 · VeloxQ: representation and a VeloxQ-driven loop

> VeloxQ uses the same larger kitchen model. Proved idle elimination raises best cold-start service from ten to fifty meals. Alone, VeloxQ still returns mostly empty plans. So we made it the engine of a checked neighbourhood loop: forty-bit block-pair subproblems, every move rechecked. From its own plans it reaches six and seven missed lots at 998 and 2,022 bits, one lot better than thirty-second CP. Exact enumeration matches it; longer CP still wins.

## 3:56–4:08 · What makes the choices difficult?

> The cell is deliberately small. Larger inputs generate eighteen thousand batch programs. Equipment, workers and paired demand couple their choices. We measure restriction loss and search quality separately.

## 4:08–4:20 · Checked results and benchmarks

> Our log records three decisions: correct repair cleaning, complete-meal service, proved idle elimination. A what-if adds one more: a packing helper serves twenty more meals; a third cooker, none. Code linked.

## Recording notes

623 spoken words; the fastest chapter is 165 words/minute. Leave pauses for the code, equation and actual launch.
The earlier local MP4 is silent and has obsolete result screens. Record the
current route and narration for this result set.

Record one paragraph at a time in a quiet room. Align and retime the visuals,
add final subtitles, and check the export end to end. Keep the submitted video
below five minutes. The screen recording and live slot are separate deliverables.
