# Video narration — 4:52

[Watch the final video](https://qfactoria.com/video/) · [Local MP4](../output/submission-male-v3/axion-kitchen.mp4)

The completed narration uses Kokoro's stock `am_fenrir` synthetic voice;
no voice was cloned. [Voice manifest](../output/submission-male-v3/voice-manifest.json)
records the engine/model attribution, pronunciation adjustments and chapter timing.
English selectable subtitles are included in the MP4 and available as
[captions.srt](../output/submission-male-v3/captions.srt).

This text is generated from [story.json](../scripts/catering-showcase/story.json).
Edit that source, then run `npm run docs:write`. QAOA and VeloxQ use integrated
checked results; VQE separates reported campaign medians from checked exported schedules.

## 0:00–0:26 · The catering problem

> This is Axion Kitchen. We first solved the factory baselines: optimal schedules of four and eight hours. Our extension schedules catering production. Cookers are machines, cleaning is setup, and departures are deadlines. We choose shared batches, qualified workers and timings, while respecting freshness, calendars and outages. First, serve complete meals. Then reduce waste, extra batches and changes to the plan.

## 0:26–0:50 · Two orders sharing a side batch

> Two customers need ten meals each. Main A is already cooking, and one batch of twenty side portions can serve both orders. Here's the conflict: that side batch and one Main B option need cooker C2 at the same time. QAOA selects a different Main B schedule on C1. Both orders get a main and a side, packed before departure. Sharing the side batch saves making it twice.

## 0:50–1:00 · What happens without the side batch

> Remove just the side batch. Neither order gets a complete meal. Twenty main portions go to waste. That's why we optimize meals, rather than dishes.

## 1:00–1:26 · Batch selection and scheduling constraints

> Each bit selects a batch program: how much to make, which orders it serves, who does the work, and when. Programs competing for the same demand sit in one block; we choose one, or leave it idle. Penalties rule out clashes between blocks. The code builds those pair terms directly. This small case has thirty-two programs and three idle bits. A restricted set of programs can miss better schedules.

## 1:26–1:54 · Complete meals and food waste

> Multiply main coverage by side coverage to count complete meals. Their sum minus twice that product counts unpaired food. Coverage is linear in our bits, so both expressions stay quadratic. Our weights make each priority outweigh all lower costs combined. For constraints, we bound how much the objective can vary across all bitstrings, then set the penalty one higher. That proves feasible ground states. It doesn't guarantee a solver finds them.

## 1:54–2:06 · The quantum formulation

> We map the QUBO to an Ising Hamiltonian. The mixer preserves block occupation. Fixing the rest of the schedule turns global interactions into local fields for VeloxQ.

## 2:06–2:24 · Mandatory cleaning after repair

> An outage also changes what happens after repair. The cooker still needs cleaning. Here, the worker must finish committed work first, then clean from eleven forty to eleven fifty. Both resources stay reserved. Our checker rebuilds those intervals from the schedule, along with freshness and delivery checks.

## 2:24–2:49 · Run QAOA

> Let's run the saved depth-three QAOA circuit locally. Cost and conflict phases alternate with an XY mixer. The mixer keeps one choice per block, but clashes between blocks still need checking. We draw four thousand ninety-six fresh samples, using the saved angles. The result on the right comes from this run. The kitchen animation is a separate replay of a saved result.

## 2:49–3:18 · QAOA results

> Does training help? We chose the settings on the small cell and S0/S1, then tested S2/S3. Training finds the best available plan in all ten seeds. Random-angle search also hits ten on S2. At two hundred fifty-six evaluations, training gives roughly eleven and twenty-two times the optimum probability per shot. We optimize the angles separately for each instance. And these limited program sets miss better full-grid plans.

## 3:18–3:38 · VQE comparison

> VQE uses Givens and controlled Givens rotations. Its median probability of the offered-pool optimum is about twelve percent in each disruption case. Using CVaR and adjoint gradients, it samples that optimum in ten seeds out of ten, and nine out of ten. Its budgets and shots differ from QAOA.

## 3:38–4:06 · VeloxQ inside the replanning loop

> For larger plans, VeloxQ sits inside a replanning loop. It starts from its own plan. We free two blocks, solve their conditional QUBO, and keep a change only if it passes the checker and improves the objective. Across three sizes, missed meal lots drop from nine to seven, eleven to six, and thirteen to seven. That took seventy-one submissions. Exact neighborhood controls do as well or better, and longer classical runs still win.

## 4:06–4:18 · What makes the choices difficult?

> The small cell tests correctness. Larger inputs generate eighteen thousand batch programs with shared resources and demand. We measure the cost of restricting choices separately from solver quality.

## 4:18–4:42 · Capacity: equipment or staff

> What capacity should we add? Our best current-capacity plan serves ninety meals. A third cooker still serves ninety, but removes the waste. A prep or packing helper reaches one hundred ten. The same worker currently does both jobs. Each variant gets the same classical budget and two seeds. These are feasible plans, not proven optima. We'd need prices before recommending a purchase.

## 4:42–4:52 · Checked results and benchmarks

> Our log records why we changed cleaning, meal coverage and idle encoding. Twenty meals, no waste in the small case. The demo links to code, proofs and benchmarks.

## Editing notes

736 source words; the fastest chapter is 170 words/minute.
Narration is generated sentence by sentence and aligned to the chapter route.
The voice manifest records actual pronunciation text and time stretch. Preserve
pauses for the model, source code and real launch; do not claim a result absent
from the receipt. The final video uses edited actual UI captures, not an unedited
continuous recording.

The separate live presentation uses [its shorter script](CATERING_LIVE.md).
Organizer submission is not implied by this completed local video.
