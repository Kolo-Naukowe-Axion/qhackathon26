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
| 0:00–0:08 | Start the rehearsal timer; show the kitchen. | Stage One reaches four and eight hours. Our extension schedules batches so each catering order leaves with both courses. |
| 0:08–0:30 | Play this chapter through both departures; it then holds. | Each customer needs ten meals. Main A is already cooking. We choose a new Main B and one shared side batch. Preparation, cooking, packing and cleaning reserve real equipment and workers. Both orders share the packing line. |
| 0:30–0:42 | Show the checked side-batch removal. | Remove the side batch and we serve no complete meals. Twenty component portions become waste. This is a checked manual intervention. |
| 0:42–1:04 | Play past halfway for the compiler excerpt. | A bit selects one batch program: quantity, allocations, resources and times. One-hot blocks choose a program or idle; pairwise penalties forbid clashes. The small cell offers all thirty-two legal programs, plus three idle bits. |
| 1:04–1:29 | Point to MS, then the priority order. | Main coverage times side coverage gives complete service. Their sum minus twice the product counts unpaired food. Both expand quadratically without product bits. We prove the objective priority order and a penalty bound that makes every ground state feasible. |
| 1:29–1:49 | Click Sample frozen-angle QAOA. | QAOA uses cost phases and blockwise XY mixing. The mixer preserves one choice per block, while the checker still rejects cross-block conflicts. This button samples saved angles locally and checks the returned schedules. |
| 1:49–2:14 | Show the cell outcome and larger comparison. | Six cell trials find the optimum, as do the controls. Six of eight larger final plans attain their offered-pool optimum, but all trail the full grid. We distinguish missing choices from poor search; neither is hidden by a success headline. |
| 2:14–2:34 | Use the final owner receipt before presenting. | VeloxQ solves the larger version of this same meal model: five hundred twelve to two thousand forty-eight variables. We verify the coefficient conversion and every returned schedule. The initial settings expose a feasibility bottleneck; the final comparison will measure usable-plan quality and runtime. |
| 2:34–2:45 | Show completed handovers, then stop. | The checked schedule serves twenty meals with zero discarded portions. Our code, proofs, raw trials and development log document how we reached and verified it. |

291 spoken words. The VeloxQ paragraph describes retained initial runs, not a final quality result.
Replace it with one measured finding before presenting. Rehearse three times
under 2:50 with the actual speaker, operator and final result set.

## What the launch does

The button verifies frozen input hashes, reuses the p=1/seed-2026 angles and
samples 4096 shots with fixed sampling seed 17102026. It independently checks
every distinct returned bitstring. Rehearsals returned (U,W,B,R)=(0,0,2,2),
20 complete meals, zero waste and 3771 valid shots. This is repeat execution
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
