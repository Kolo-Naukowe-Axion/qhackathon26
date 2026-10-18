# Axion Kitchen — final handoff

One submission: the required factory baselines and a catering batch-production
extension, with QAOA, VQE, VeloxQ and checked classical references.

## Links to submit

| Field | Value |
|---|---|
| Project | **Axion Kitchen** |
| Repository | https://github.com/Kolo-Naukowe-Axion/qhackathon26 |
| Interactive demo | https://qfactoria.com/ |
| Benchmarks | https://qfactoria.com/catering/benchmarks/ |
| Baseline outputs | [A: 4 h](../schedule_2x2.json) · [B: 8 h](../schedule_3x3.json) |
| Formal problem and mathematics | [CATERING_PROBLEM.md](CATERING_PROBLEM.md) · [Project Design](../PROJECT_DESIGN.md) |
| Development record | [DEVELOPMENT_LOG.md](../DEVELOPMENT_LOG.md) |
| Video URL | [Final 4:48 video — public playback checked](https://qfactoria.com/video/) |
| Submitted commit | Record the final checked `git rev-parse HEAD` after the remaining video/documentation edits |

Suggested description:

> Axion Kitchen extends factory scheduling to shared batch production with
> paired-meal fulfillment, food waste, worker qualifications, freshness and
> outage recovery. A proved QUBO formulation supports constrained QAOA and VQE
> comparisons, while a VeloxQ-driven neighborhood loop improves larger plans.
> Independent schedule checks and classical references expose both search and
> representation losses.

The local final media package is at `output/submission-4k-v2/`:
`axion-kitchen.mp4`, `voiceover.wav`, `captions.srt`, `voice-manifest.json` and
`manifest.json`. The MP4 is **4:48, 3840×2160**, with H.264 video, AAC narration,
English subtitles and chapter markers. Probe checks and manifest hashes match
the exported media and studio sources. Narration uses the stock Kokoro
`af_heart` synthetic voice, with no voice cloning; timing, clipping, caption
overlap and key spoken numbers have automated checks. These checks do not
constitute subjective human listening approval. This local path is **not a
submission URL**. Do not
upload the obsolete silent rough cut from `output/playwright/`.

## What is already in the source package

- MIT [license](../LICENSE), [run instructions](../README.md) and AI-use disclosure.
- Both required baseline JSONs, with independent feasibility and optimum checks.
- Implemented Stage 2 compiler, physical checker, priority/penalty proofs and
  reproducible retained results. The current benchmark data contains 400 QAOA
  runs, five checked VQE exports and 137 recorded VeloxQ submission attempts.
- A [4:48 narration script](CATERING_VOICEOVER.md), [2:45 live runbook](CATERING_LIVE.md)
  and [Q&A sheet](CATERING_QA.md). The video must show the actual local launch and
  returned receipt; the kitchen replay is labeled separately.

The [final media and release receipt](assets/catering-final-check.json) records
13 passing release stages and tested file fingerprints for the extended cut,
plus complete AV decode, local speech checks and public playback verification.
The earlier [committed technical receipt](../output/catering-submission-review-v1/verification.json)
identifies its tested source commit. A later rerun is not proof that an earlier
receipt covered later edits. Recheck the final release with:

```sh
.venv-catering/bin/python scripts/check-catering-release.py \
  --output /tmp/NEW-AXION-RELEASE
```

Use the installed foundation interpreter instead if its directory has another
name; setup is in [the catering guide](../catering/README.md). The checker needs
Node.js 20+ and npm. It performs three local executions with frozen QAOA angles
and one fixed sampling seed; it starts no training, VeloxQ job or QPU job.

## Final external steps

1. **Video:** the final cut is published at https://qfactoria.com/video/ and linked
   from the README. Public browser playback was checked: 288 seconds, 4K,
   time advancing and no error. Paste this URL into the organizer form. The
   package discloses its stock synthetic narration.
2. **Public source:** at the team's authorized release step, make the repository
   public and verify signed-out access to the README, license and baseline JSONs.
   A public demo website alone does not satisfy the public-repository requirement.
3. **Organizer form:** obtain the actual Google Form from the organizer channel.
   The supplied PDF says its link will be provided separately; no form URL or
   completed submission receipt was found in this repository. Use team-confirmed
   names/contact details and the final checked source commit. Do not infer those
   declarations from commit authors or service credentials.
4. **Receipt:** retain the organizer acknowledgment, exact submitted repository
   and video links, source commit and submission time.
5. **Live:** attend the assigned slot with the local studio running. The limit is
   three minutes plus approximately two minutes of questions; the prepared live
   route is 2:45. Check the assigned slot in the organizer channel.

The official deadline is **18 October 2026, 15:00 UTC+2**; presentations start
at **18:00 UTC+2**. Authority: [challenge PDF](../Quantum_Hackathon_2026_ERP_Challenge.pdf),
§§6, 9, 10, 12 and 13. Preparation does not constitute submission.

## Claims to keep precise

- Stage 1's 1/3-bit selected encoding tabulates the tiny permutation costs
  classically. The comparable time-indexed baseline-B count is **30** variables;
  neither count demonstrates a quantum speedup.
- The 35-data-qubit cell is simulated in a 1,045-state one-hot sector. Larger
  31–35-qubit quantum portfolios restrict the offered choices; their optimum
  can differ from the full physical-domain reference.
- QAOA and VQE use unequal training budgets. Show their measurements without
  declaring a matched-budget winner.
- VeloxQ-LNS reaches U=6/7 at 998/2,022 solver bits, versus U=7/8 for the retained
  30-second CP runs. This is an operational comparison with different budgets;
  longer CP and the exact-pair loop remain stronger controls. Backend time is
  distinct from end-to-end time.
- Investment what-ifs are finite-budget classical incumbents, not certified
  economic optima. One waste lot is **ten portions**, and no wages or equipment
  prices were supplied.

## Published video

The [watch page](https://qfactoria.com/video/) includes the [MP4 download](https://qfactoria.com/video/axion-kitchen.mp4) and English captions. Public browser playback was checked on 18 October: 288 seconds, 3840×2160, readyState 4, time advancing, no media error. The final MP4 is also retained in `presentation/video/`; [provenance](../presentation/video/provenance.json) records source and media hashes. Production deployment: `dpl_Arx1EkZkA7gJKpae7r2Za7aHrHKL`. This publication is not organizer submission.

Both [4K](https://qfactoria.com/video/axion-kitchen.mp4) and [1080p](https://qfactoria.com/video/axion-kitchen-1080p.mp4) now contain the same 4:48 cut, including the capacity comparison at 4:08–4:36. The 2:45 live route remains separate.
