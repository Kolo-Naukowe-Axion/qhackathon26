# Axion Kitchen: timecoded voiceover draft

Silent visual cut: **4:20**. Record a human voiceover after final result selection.
The VeloxQ paragraph is explicitly unfinished; replace it before submission.
This script follows `scripts/catering-showcase/story.json`; update that source first.
Do not narrate the five-minute video script over the shorter live route.

## 0:00–0:12 · Twenty lunches. One shared batch.

> Our baseline schedules finish in four and eight hours. For Stage Two, we asked a different production question: can shared batches deliver complete meals without wasting their components?

## 0:12–0:40 · A main and a side, before departure.

> Each order is for ten people. The first main is already cooking. We choose a new main for Order B and one twenty-portion side batch shared across both orders. The plan assigns preparation, cooking, packing and cleaning to actual equipment and workers. Separate cookers allow overlap, while one packing line links each portion to its departure.

## 0:40–1:00 · Skip the side. Lose both meals.

> Here we manually skip the shared side. The mains can still finish, but neither customer receives a complete meal. Twenty component portions become waste. This intervention explains the service objective. It is independently checked, and it is not another optimizer run.

## 1:00–1:34 · One bit chooses one local batch program.

> A program specifies quantity, allocations, equipment, workers and phase times for one batch. It is not a pre-solved whole-kitchen schedule. Programs sharing a unit demand anchor form a one-hot block, including idle. Cross-block conflicts forbid double delivery and shared-resource overlaps. The complete small cell keeps all thirty-two legal programs and three idle choices.

## 1:34–2:10 · The meal creates the quadratic coupling.

> Main coverage times side coverage tells us whether a meal is complete. Their sum minus twice their product counts unpaired components. These expressions expand directly into quadratic program-selection terms, without product qubits. We prioritize missed meals, then waste, then new batches and plan changes. Integer bounds prove that priority order. A separate full-objective bound makes every global ground state feasible.

## 2:10–2:35 · Repair ends. Cleaning still has to happen.

> In the larger disruption case, the repaired cooker cannot resume immediately. Its qualified worker first finishes committed work, then cleans the repaired cooker. The clean occupies both worker and equipment. Freshness, calendars and departures are checked from raw operation records, independently of the QUBO conflict graph.

## 2:35–3:00 · A fresh sample. Frozen QAOA angles.

> We now run the local quantum simulator with retained angles. This generates fresh samples without retraining or contacting a quantum device. Every returned bitstring passes through the independent checker. The output shows the objective tuple, complete meals, waste and valid shots. The visible kitchen replay has its own retained source label.

## 3:00–3:35 · Correctness, search loss and representation loss.

> All six small-cell QAOA trials found its optimum, and the simple controls found it too. On the larger pilot, six of eight final incumbents match their final offered-pool optimum. All eight still trail the full-grid reference. Final-step controls also tie. This separates the cost of restricted choices from search quality, without claiming a quantum advantage.

## 3:35–4:05 · The same meal model, at larger scale.

> VeloxQ receives larger instances of this same paired-meal formulation, at five hundred twelve through two thousand forty-eight variables. Our integration preserves integer coefficients, checks the spin convention and validates raw returned schedules. The first cold jobs identify a feasibility bottleneck. This section will feature the owner's final checked settings and comparisons when those results are frozen.

## 4:05–4:20 · Every sampled bit has a kitchen consequence.

> The project connects a quadratic production model to checked meal handovers. Our source, proofs and development log explain the decisions, the corrections and the limits. One shared side batch makes the difference visible.

## Recording order

1. Lock the selected method and final VeloxQ numbers, then update the story and visual evidence.
2. Record one speaker in a quiet room, one paragraph at a time, leaving a short gap between takes.
3. Align narration to the visual beats; retime clips if needed. Keep code and equations visible long enough to read.
4. Add final subtitles after editing, then check the exported file end to end. The present cut has no audio.

Current narration: 479 words. Allow pauses for the actual launch, code excerpt and equation.
