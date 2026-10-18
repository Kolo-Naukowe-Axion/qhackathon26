# Live presentation — 2:45 route

Generated from [story.json](../scripts/catering-showcase/story.json). Edit that
source, then run `npm run docs:write`. The slot is at most three minutes plus
about two minutes Q&A. This 2:45 route leaves 15 seconds of margin; chapter
holds do not pause the jury's clock.

## Setup and controls

[Final narrated video](https://qfactoria.com/video/) · [Local MP4](../output/submission-final/axion-kitchen.mp4). The video is a fallback and a separate deliverable.

Run `.venv-catering/bin/python scripts/serve-catering-showcase.py --port 4193`.
Open [the live studio](http://127.0.0.1:4193/?mode=live). Use one speaker and
one operator. Share only the audience window; keep [Q&A notes](CATERING_QA.md)
outside the share.

- Right/Left Arrow: next/previous chapter.
- Space: play/pause animation; at a live chapter hold, replay that chapter.
- P: hide or restore operator controls and notes. F: full screen.
- R: start/reset the rehearsal timer at the first spoken word. Animation holds do not
  pause it. Target 2:45; stop before 3:00.

## Read-aloud script and operator cues

| Target time | Operator | Speaker |
|---|---|---|
| 0:00–0:20 | Start R. Play the four-second opening, show both Stage 1 schedules for five seconds, then explain the factory-to-kitchen mapping. | Axion Kitchen. Factory baselines: four and eight hours, both checked optimal. Our extension chooses shared batches, workers and phase times under freshness, calendar and outage constraints. Cookers are machines, cleaning is setup, and departures are due dates. Complete meals come first, then waste, batches and changes. |
| 0:20–0:36 | Point to the actual x1/x3 cooker conflict; the retained plan uses x11 on C1. Play through both departures. | Two customers share a twenty-portion side batch. One Main B option clashes with it on C2. The checked QAOA plan instead chooses Main B on C1, so both orders leave complete. |
| 0:36–0:43 | Show the checked side-batch removal. | Remove the side: zero complete meals and twenty wasted portions. This is a manual intervention. |
| 0:43–0:59 | Explain the actual x3 operation timeline and same-anchor exclusivity. Play past halfway; point to product(...) and penalty=span+1 in the compiler excerpt. | A bit selects a local batch and its schedule. Same-anchor programs share demand, so each block chooses one or idle. Conflicts forbid clashes. The code expands coverage products and sets the penalty to span plus one. This cell uses thirty-five bits. |
| 0:59–1:20 | Explain MS and waste first; after 60% the screen shows the range bound and penalty inequality. State the ground-state guarantee. | Linear main and side coverage multiply into quadratic service and waste terms. Priority weights dominate lower costs. For hard constraints, the objective range is at most S. Set P to S plus one: every invalid state costs more than every feasible state. That proves the ground-state guarantee. |
| 1:20–1:37 | Click Run trained QAOA. Only after completion, read actual meals and waste aloud: expected 20 meals/0 waste. If launch fails or values differ, describe the actual receipt and use the labeled retained fallback. | Return to the original choices. We run the saved depth-three circuit, draw four thousand ninety-six fresh samples, and independently check the outcomes. |
| 1:37–1:57 | Compare trained and random probabilities, then point to the restriction gap. | On both held-out disruption cases, QAOA finds the offered-pool optimum in all ten seeds. Random-angle search also hits all ten on S2. With two hundred fifty-six evaluations, optimum probability per shot is about eleven and twenty-two times random-angle search. The full kitchen still has better schedules than these restricted portfolios. |
| 1:57–2:09 | Compare per-shot probabilities; point to the different budgets and final shots. | VQE concentrates about twelve percent probability on the optimum in both cases. Its budgets and shot count differ from QAOA, so we show the methods separately. |
| 2:09–2:28 | Follow the loop, then read the three starting and final missed-lot counts. Distinguish total adapter time from backend time; retain the exact-control and longer-CP comparison. | VeloxQ starts from its own plan and repeatedly changes two blocks. Missed meal lots fall from nine to seven, eleven to six, and thirteen to seven. All improvements pass the checker. Exact neighborhood controls do as well or better; longer classical runs still win. |
| 2:28–2:38 | Distinguish the 1,045-state correctness cell from the 18,182-program generated domain and the offered QUBO tiers. | Small cells test correctness. Larger inputs generate eighteen thousand programs with shared-resource conflicts. More variables alone do not establish hardness; benchmarks show quality and runtime. |
| 2:38–2:45 | Show final handovers and the three development-log decisions; stop. | Twenty meals, zero waste. We fixed cleaning, paired main and side, and proved idle elimination. |

362 scripted words; the fastest chapter is 154 words/minute. The results use the integrated QAOA campaign and checked VeloxQ replanning loop. Rehearse three times
under 2:50 with the actual speaker, operator and final result set.

## Reading the live result

When the receipt completes, say: “The fresh receipt shows twenty complete meals and zero waste” only if those displayed values match. Otherwise read the actual values; use the fallback wording if execution fails.
Read the short success sentence within the launch chapter; it is conditional on the actual displayed receipt.

## What the launch does

The button verifies frozen input hashes, reuses the frozen p=3/cell/budget256/seed-2026 angles and
samples 4096 shots with fixed sampling seed 17102026. It independently checks
every distinct returned bitstring. Local checks returned (U,W,B,R)=(0,0,2,2),
20 complete meals, zero waste and 2173 valid shots. This is repeat execution
of one fixed setup, not another independent training trial. It uses no paid
service, training or physical QPU. The kitchen replay retains its own label.

Terminal fallback, with a fresh directory:

```sh
.venv-catering/bin/python scripts/catering_live.py --output output/NEW-LIVE-RUN
```

If the launch fails, say: “The fresh launch hasn't completed; we'll use the
retained checked schedule.” Continue with the saved kitchen replay. If the
studio fails, open the [standalone viewer](http://127.0.0.1:4192/catering/?case=CELL)
with its separate static server running. Keep the local MP4 and screenshots
on the presenting laptop. Do not wait for a remote queue during the slot.
