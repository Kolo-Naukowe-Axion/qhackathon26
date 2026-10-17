# Presentation plan

One project: **Axion Kitchen**. Explain the catering decision, show its quadratic
model, then show measured outcomes. Keep the game UI; remove any screen or
sentence that does not help explain a decision or substantiate a result.

## Scripts and runnable demo

- [Video narration](CATERING_VOICEOVER.md): timed 4:20 route.
- [Live speaker/operator script](CATERING_LIVE.md): 2:45 route within a 3-minute slot.
- [Q&A sheet](CATERING_QA.md): eight likely questions first, technical detail below.
- [Studio guide](../scripts/catering-showcase/README.md): setup and capture commands.

Both scripts are generated from [story.json](../scripts/catering-showcase/story.json).
Edit that source and run `npm run docs:write`; `npm run docs:check` catches drift.
The studio uses the short `live_narration` in live mode, not the video paragraph.
Earlier competing timings and scripts are [archived](archive/2026-10-17/CATERING_PRESENTATION_PREVIOUS.md).

## What the jury should understand

1. **Decision:** two ten-meal orders share a side batch. Main A is committed;
   choose the other batches, resources and times before departures.
2. **Mathematics:** a bit selects one local batch program. Main/side coverage
   products encode complete service and unpaired waste quadratically. One-hot
   and conflict terms enforce compatibility; proved bounds set priorities and penalties.
3. **Evidence:** the complete cell has an independently certified optimum.
   Controls tie the quantum result. Larger instances separate portfolio
   restriction from search loss. VeloxQ uses larger inputs of the same model.

The shared-side removal is a checked manual intervention, not a solver result.
Use it to explain the objective. The live launch samples retained QAOA angles
locally and checks the returned schedules. Label replay and fresh execution separately.

## Current numbers and their sources

| Claim | Source and boundary |
|---|---|
| Stage 1: 4h / 8h | Root schedule JSONs and `output/stage1-selected.json` |
| Cell: 32 programs + 3 idle bits, 35 data qubits | `output/catering-complete-cell-v3/report.json`; complete on its declared narrow grid |
| 1045 sector states, 59 physically feasible | Exact invariant-sector audit; not a dense 35-qubit simulation |
| Cell optimum (0,0,2,2), six successful trials | Same report; both controls tie; best-of-run is distinct from per-shot success |
| 20 meals / zero discarded portions | `output/catering-complete-cell-demo-v3.json`; actual handover and disposal ledger |
| 6/8 final larger plans optimal within final offered pool | `output/catering-math-audit-v1/mathematics.json`; all trail raw-grid CP and final-step controls tie |
| VeloxQ: 512 / 1024 / 2048 variables | [Owner report](catering-methods/VELOXQ.md); actual cold jobs, not physical qubits |

[Quality audit](CATERING_QUALITY.md) contains the full comparisons. Compare
energies only on identical bundles; use checked tuples across scalarizations.
R=B in the current fixtures. Do not claim monetary optimization or unsupported capacities.

## Remaining gates

- Integrate each selected method owner's source-hashed result, settings, raw
  samples and reproducible launch. Feature one primary quantum method clearly.
- Replace the VeloxQ drafting row with one supported quality/runtime finding.
  Correct integration and scale alone do not establish outperformance.
- Keep current cold runs; any formulation or penalty alternative needs its
  own identity and correctness check. Service experiments require the owner's cap.
- Freeze spoken numbers and visuals, record human voiceover, export and upload
  a playable video ≤5min. The local silent cut is preparation, not a submission.
- Rehearse three live runs under 2:50. Check the real speaker clock, not just
  animation progress. Keep saved replay, screenshots and the MP4 as fallbacks.
- Follow the [submission checklist](STAGE2_SUBMISSION.md) for public access and turn-in.

Current silent cut: ignored `output/playwright/catering-showcase-v2/recording/`.
The wording is still a draft until final result integration. No new model,
training run, remote job or paid allowance is required to prepare these materials.
