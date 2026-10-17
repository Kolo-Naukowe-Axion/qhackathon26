# Live presentation — 2:45 route

Generated from [story.json](../scripts/catering-showcase/story.json). Edit that
source, then run `npm run docs:write`. The slot is at most three minutes plus
about two minutes Q&A. This 2:45 route leaves 15 seconds of margin; chapter
holds do not pause the jury's clock.

## Setup and controls

Run `.venv-stage2/bin/python scripts/serve-catering-showcase.py --port 4193`.
Open [the live studio](http://127.0.0.1:4193/?mode=live). Use one speaker and
one operator. Share only the audience window; keep [Q&A notes](CATERING_QA.md)
outside the share.

- Right/Left Arrow: next/previous chapter.
- Space: play/pause animation; live chapters hold at their end.
- P: hide or restore operator controls and notes. F: full screen.
- R: start/reset the rehearsal timer at the first spoken word. Animation holds do not
  pause it. Target 2:45; stop before 3:00.

## Read-aloud script and operator cues

| Target time | Operator | Speaker |
|---|---|---|
| 0:00–0:20 | Start R; explain the full problem before the small example. | We plan catering batches, allocations, equipment, workers and times. The constraints include freshness, departures, cleaning and resource calendars. Urgent orders and cooker outages change the plan; started work stays fixed. We prioritize complete meals, then waste, batches and changes. |
| 0:20–0:36 | Play this chapter through both departures; it then holds. | Each customer needs ten meals. Main A is already cooking. We choose a new Main B and one shared side batch. Preparation, cooking, packing and cleaning reserve real equipment and workers. Both orders share the packing line. |
| 0:36–0:43 | Show the checked side-batch removal. | Remove the side batch and we serve no complete meals. Twenty component portions become waste. This is a checked manual intervention. |
| 0:43–0:59 | Play past halfway for the compiler excerpt. | A bit selects one batch program: quantity, allocations, resources and times. One-hot blocks choose a program or idle; pairwise penalties forbid clashes. The small cell offers all thirty-two legal programs, plus three idle bits. |
| 0:59–1:17 | Point to MS, then the priority order. | Main coverage times side coverage gives complete service. Their sum minus twice the product counts unpaired food. Both expand quadratically without product bits. We prove the objective priority order and a penalty bound that makes every ground state feasible. |
| 1:17–1:37 | Click Run trained QAOA; read the fresh checked receipt. | This button runs the trained depth-three circuit with saved angles. It samples four thousand ninety-six shots locally and checks every returned schedule. The angles are frozen; the samples are fresh. |
| 1:37–1:57 | Compare trained and random probabilities, then point to the restriction gap. | On both held-out disruption cases, QAOA finds the offered-pool optimum in all ten seeds. With two hundred fifty-six evaluations, optimum probability per shot is about eleven and twenty-two times random-angle search. The full kitchen still has better schedules than these restricted portfolios. |
| 1:57–2:09 | Compare per-shot probabilities; point to the different budgets and final shots. | VQE concentrates about twelve percent probability on the optimum in both cases. Its budgets and shot count differ from QAOA, so we show the methods separately. |
| 2:09–2:28 | Show the equal-budget 17 → 512 comparison and all three actual widths. | For VeloxQ, we remove redundant idle choices and prove the optimum is preserved. At the same step budget, valid returns rise from seventeen to five hundred twelve out of five hundred twelve. All three tested scales return valid schedules; classical controls still find better plans. |
| 2:28–2:38 | Show source choices, actual solver widths and the benchmark browser link. | Orders, time choices and conflicts drive scale. Quantum circuits use small portfolios; VeloxQ handles larger matrices. Size alone does not establish hardness. |
| 2:38–2:45 | Show the completed handovers and benchmark link; stop. | Twenty meals, no waste in this cell. The benchmark page contains the comparisons, scope and scaling limits. |

352 spoken words. The results use the integrated QAOA campaign and checked no-idle VeloxQ study. Rehearse three times
under 2:50 with the actual speaker, operator and final result set.

## What the launch does

The button verifies frozen input hashes, reuses the frozen p=3/cell/budget256/seed-2026 angles and
samples 4096 shots with fixed sampling seed 17102026. It independently checks
every distinct returned bitstring. Local checks returned (U,W,B,R)=(0,0,2,2),
20 complete meals, zero waste and 2173 valid shots. This is repeat execution
of one fixed setup, not another independent training trial. It uses no paid
service, training or physical QPU. The kitchen replay retains its own label.

Terminal fallback, with a fresh directory:

```sh
.venv-stage2/bin/python scripts/catering_live.py --output output/NEW-LIVE-RUN
```

If the launch fails, say: “The fresh launch hasn't completed; we'll use the
retained checked schedule.” Continue with the saved kitchen replay. If the
studio fails, open the [standalone viewer](http://127.0.0.1:4192/catering/)
with its separate static server running. Keep the local MP4 and screenshots
on the presenting laptop. Do not wait for a remote queue during the slot.
