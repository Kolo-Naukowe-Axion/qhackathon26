# Presentation plan

One project: **Axion Kitchen**. Explain the catering decision, show its quadratic
model, then show measured outcomes. Keep the game UI; remove any screen or
sentence that does not help explain a decision or substantiate a result.

## Scripts and runnable demo

- [Video narration](CATERING_VOICEOVER.md): timed 4:52 route.
- [Live speaker/operator script](CATERING_LIVE.md): 2:45 route within a 3-minute slot.
- [Q&A sheet](CATERING_QA.md): eight likely questions first, technical detail below.
- [Recording sheet](CATERING_RECORDING.md): shot list, edit cues and stills-only dry run.
- [Studio guide](../scripts/catering-showcase/README.md): setup and capture commands.

Both scripts are generated from [story.json](../scripts/catering-showcase/story.json).
Edit that source and run `npm run docs:write`; `npm run docs:check` catches drift.
The studio uses the short `live_narration` in live mode, not the video paragraph.
Earlier competing timings and scripts are [archived](archive/2026-10-17/CATERING_PRESENTATION_PREVIOUS.md).

The opening chapter now includes the actual Stage 1 A/B schedules from 0:04
to 0:09 in both routes. Their makespans (4 h / 8 h) are independently checked
against the official instances and exact reference; the compact-QAOA classical
cost-tabulation scope remains visible. Timed routes remain 4:52 / 2:45.

## What the jury should understand

1. **Problem first:** orders, recipes/yields, calendars, qualified workers and
   the current kitchen state are inputs. Choose batches, quantities, shared
   allocations, equipment, crews and phase times. Enforce departures, freshness,
   attendance, clashes, cleaning and committed work. Urgent orders and cooker
   outages trigger replanning. Prioritize missed meals, waste, batches and changes.
   Then illustrate the decision with two ten-meal orders sharing one side batch.
2. **Mathematics:** a bit selects one local batch program. Main/side coverage
   products encode complete service and unpaired waste quadratically. One-hot
   and conflict terms enforce compatibility; proved bounds set priorities and penalties.
3. **Evidence:** the complete cell has an independently certified optimum.
   Controls tie the quantum result. Larger instances separate portfolio
   restriction from search loss. VeloxQ uses larger inputs of the same model.

The operational sequence is explicit: the retained solver plan serves both
orders; removing only its side batch leaves zero complete meals and twenty
wasted main portions; fresh local execution then returns to the original
choices and reports its own checked outcome. The manual intervention explains
the objective and is labeled separately from both solver paths. The live launch samples retained QAOA angles
locally and checks the returned schedules. Label replay and fresh execution separately.

## Three arguments to make explicit

| Question | On-screen evidence | Short explanation |
|---|---|---|
| Is this still manufacturing scheduling? | Machine/cooker, setup/cleaning and due-date/departure mapping in the opening problem frame. | It is batch-production scheduling with shared yields and coupled fulfillment. Those new decisions extend the original fixed-job model. |
| What makes the choices interact? | The actual x1/x3 C2 conflict, followed by the retained x3/x11 plan. | Each batch can be legal alone while a combination clashes. The solver must choose compatible batches and complete both meal components. |
| Why trust the math? | Coverage truth table, actual compiler excerpt, then the range-bound inequality. | Linear coverage products stay quadratic. Priority weights dominate lower costs; P=S+1 makes every invalid state's energy exceed every feasible state's energy. |

The loss chapter changes from the objective to the proof at 60% of its duration.
The final scale chapter distinguishes the small correctness cell from the
18,182-program generated domain and the actual offered source matrices. State
computational scope without presenting size as measured hardness.

## Current numbers and their sources

| Claim | Source and boundary |
|---|---|
| Stage 1: 4h / 8h | Root schedule JSONs and `output/stage1-selected.json` |
| Cell: 32 programs + 3 idle bits, 35 data qubits | `output/catering-complete-cell-v3/report.json`; complete on its declared narrow grid |
| 1045 sector states, 59 physically feasible | Exact invariant-sector audit; not a dense 35-qubit simulation |
| Cell optimum (0,0,2,2), six successful trials | Same report; both controls tie; best-of-run is distinct from per-shot success |
| 20 meals / zero discarded portions | `output/catering-complete-cell-demo-v3.json`; actual handover and disposal ledger |
| 6/8 final larger plans optimal within final offered pool | `output/catering-math-audit-v1/mathematics.json`; all trail raw-grid CP and final-step controls tie |
| QAOA held-out S2/S3: 10/10 optimum hits at both budgets | 400-run campaign, `output/catering-methods/qaoa/test-v1/summary.json`; at 256 evaluations, median per-shot optimum probability is about 11x/22x random-angle search |
| VQE primary held-out: 10/10 and 9/10 optimum hits | E5 CSV reports; five exported cell/S0–S3 schedules independently checked. Different optimizer/budget and 1024 final shots prohibit a matched-budget winner claim |
| VeloxQ: 486 / 998 / 2022 solver bits | [Representation study](CATERING_VELOXQ_TUNING.md); 512/512 valid at each width. At 512 source bits and equal 20,000-step budgets, best service rises 10→50 of 140 meals, waste 30→60 portions, validity 17→512/512. Raw handovers independently rechecked; service has priority and CP/SA still find better schedules |

[Quality audit](CATERING_QUALITY.md) contains the full comparisons. Compare
energies only on identical bundles; use checked tuples across scalarizations.
R=B in the current fixtures. Do not claim monetary optimization or unsupported capacities.

The VeloxQ frame additionally labels the pulled hybrid follow-up separately:
a 162-bit exact sub-QUBO improves a classical incumbent from (8,3,8,8) to
(7,4,9,9). Offline exact enumeration selected the neighborhood; the returned
plan does not attain its exact sub-optimum, and longer CP still does better.
See the [formal problem explanation](CATERING_PROBLEM.md) for the sub-QUBO
identity and the full-versus-restricted domain distinction.

## Benchmark browser and scale

Open `/catering/benchmarks/` from the kitchen or studio. It includes all 400
QAOA runs, all 137 service attempts, VQE experiment rows and five checked VQE
exports. Filters expose cases, budgets, failed attempts and source hashes. The
page downloads retained data only; no optimizer or service call runs there.
Regenerate with `.venv-catering/bin/python scripts/export-catering-benchmarks.py`.

QAOA and VQE use the same restricted 31–35-qubit portfolios. Report per-shot
probability, sampled optimum hits, feasibility and training work separately;
the current campaigns have unequal budgets. VeloxQ uses nested 512/1024/2048
source-bit pools, with redundant idle choices removed in the new representation.
The scaling screen distinguishes generated choices, offered source bits and
pair counts, actual solver width and exact-sector simulation. Neither size nor a timeout proves hardness.

## Remaining gates

- Primary emphasis is selected: QAOA fresh execution, VQE comparison and the
  VeloxQ representation study. Freeze the final release SHA after checks.
- Freeze spoken numbers and visuals, generate or record the narration, export and upload
  a playable video ≤5min. No new training or service jobs are needed for this.
- Rehearse three live runs under 2:50. Check the real speaker clock, not just
  animation progress. Keep saved replay, screenshots and the MP4 as fallbacks.
- Follow the [submission checklist](STAGE2_SUBMISSION.md) for public access and turn-in.

Earlier v4 stills-only capture dry run: ignored
`output/playwright/catering-showcase-v4/dry-run/`. It records no video and
blocks sampling. Earlier v3 browser checks: ignored
`output/playwright/catering-showcase-v3/`. The silent v2 recording in
`output/playwright/catering-showcase-v2/recording/` predates the new results,
problem overview and scaling chapters; it is a rough-cut fallback, not the
current submission video. Current routes remain 4:52 video and 2:45 live.

## 18 October screen and interaction review

The browser review covers 24 video states and 16 live states: every chapter,
opening/problem cut, both sides of the compiler and proof reveals, service
handover, recovery cleaning and the final hold. Layout checks found no remaining
text overflow in these states. All eleven live chapters were also checked with
speaker notes open; the operator area keeps a fixed height.

The encoding chapter now shows the selected x3 program's actual operation
intervals instead of compressing the whole application. The preflight compares
those records with the frozen bundle and checked plan, and compares the code
excerpt with the compiler source. Opening art contains no working viewer
controls. Probability bars state their scales; VeloxQ rows show best objective
quality as well as validity.

Verified interactions include scrubbing, chapter navigation, play/pause,
completed-video replay, live chapter replay/advance, audience-view restoration,
notes, terminal expansion, rehearsal timer and fullscreen controls. Browser
fullscreen availability is host-dependent; rejection offers audience view.
Two fixed-angle local launches each returned 20 meals, zero waste and 2,173
valid shots out of 4,096. A separate loopback-only fixture returned deliberate
HTTP 503 errors without starting a sampler: failed receipts keep both values
blank, offer Retry launch and link to the retained **same-cell** fallback.
The fixture and its browser tab were stopped after review.

Review captures remain outside the repository. This pass changes presentation,
controls and evidence checks; it starts no training, service or QPU jobs.
Live rehearsal, final 1920×1080 recording and narration remain required.

## Added capacity decision — video 4:08–4:36

The final video compares current kitchen, third cooker, prep helper and packing helper on the same larger S3 physical model. Best found plans serve 90, 90, 110 and 110 meals; discarded portions are 10, 0, 10 and 10. Each raw-input CP run has 240 seconds, two solver workers and seeds 2026/2027; both seeds agree on tuples, none proved optimality. W1 shares preparation and packing. This is classical decision support, with wages and capital prices still absent; do not call it a quantum-found investment optimum. The new chapter is video-only; the live route remains 2:45.

The video includes a technical equation sheet at **1:54–2:06**: exact QUBO/Ising coefficients, XY-QAOA, controlled Givens VQE and CVaR. It switches at 2:00 to conserved occupation, idle elimination and the exact conditional QUBO. Both sheets use local TeX typesetting and are excluded from the timed live route. For technical Q&A, open the studio video route at `?t=120` and pause there. [Operator sheet](assets/quantum-formulation.jpg) · [Structural reductions](assets/quantum-structure.jpg) · [derivation](CATERING_PROBLEM.md#9-ising-and-quantum-optimization).
