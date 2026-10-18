# Axion Kitchen — final handoff

One submission: the required factory baselines and a catering batch-production
extension, with QAOA, VQE, VeloxQ and checked classical references.

## Submission status

**Prepared, not submitted.** The user requires confirmation before the form is
sent. The final video is intended for YouTube; the website will embed it after
the upload is ready. The current MP4 watch page is a review/fallback link.

## Links and pending fields

| Field | Value |
|---|---|
| Project | **Axion Kitchen** |
| Repository | https://github.com/Kolo-Naukowe-Axion/qhackathon26 |
| Interactive demo | https://qfactoria.com/ |
| Benchmarks | https://qfactoria.com/catering/benchmarks/ |
| Baseline outputs | [A: 4 h](../schedule_2x2.json) · [B: 8 h](../schedule_3x3.json) |
| Formal problem and mathematics | [CATERING_PROBLEM.md](CATERING_PROBLEM.md) · [Project Design](../PROJECT_DESIGN.md) |
| Development record | [DEVELOPMENT_LOG.md](../DEVELOPMENT_LOG.md) |
| Official form | https://forms.gle/t5YxsRpvUiG1rbdz7 — read only; nothing entered or submitted |
| Final video URL | **Pending YouTube upload and team review** |
| Review / fallback video | https://qfactoria.com/video/ — hosted MP4, not the final YouTube URL |
| Form-entry draft | [CATERING_SUBMISSION_DRAFT.md](CATERING_SUBMISSION_DRAFT.md) |
| Submitted commit | Record the final checked `git rev-parse HEAD` after the remaining video/documentation edits |

Suggested description:

> Axion Kitchen extends factory scheduling to shared batch production with
> paired-meal fulfillment, food waste, worker qualifications, freshness and
> outage recovery. A proved QUBO formulation supports constrained QAOA and VQE
> comparisons, while a VeloxQ-driven neighborhood loop improves larger plans.
> Independent schedule checks and classical references expose both search and
> representation losses.

The current local media package is at `output/submission-male-v3/`:
`axion-kitchen.mp4`, `voiceover.wav`, `captions.srt`, `voice-manifest.json` and
`manifest.json`. The MP4 is **4:52, 3840×2160**, with H.264 video, AAC narration,
English subtitles and chapter markers. Check the refreshed manifests and release receipt against the
final export before uploading; presentation edits can invalidate older hashes. Narration uses the stock Kokoro
`am_fenrir` synthetic voice, with no voice cloning; timing, clipping, caption
overlap and key spoken numbers have automated checks. These checks do not
constitute subjective human listening approval. This local path is **not a
submission URL**. Do not
upload the obsolete silent rough cut from `output/playwright/`.

## What is already in the source package

- MIT [license](../LICENSE), [run instructions](../README.md) and AI-use disclosure.
- Both required baseline JSONs, with independent feasibility and optimum checks.
- Implemented Stage 2 compiler, physical checker, priority/penalty proofs and
  reproducible retained results. The current benchmark data contains 400 QAOA
  runs, ten checked VQE exports (E5 plus latest E6 CVaR→Gibbs) and 137 recorded VeloxQ submission attempts.
- A [4:52 narration script](CATERING_VOICEOVER.md), [2:45 live runbook](CATERING_LIVE.md)
  and [Q&A sheet](CATERING_QA.md). The video must show the actual local launch and
  returned receipt; the kitchen replay is labeled separately.

The [media and release receipt](assets/catering-final-check.json) records
checks for a particular export. Compare its duration, hashes and deployment
with the final 4:52 cut before treating it as current verification. Previous
public-playback checks do not verify a later render or a YouTube upload.
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

1. **Video:** review the current 4:52, 4K cut, then upload the approved cut to
   YouTube. Confirm signed-out playback, English captions and the five-minute
   limit. Add the actual YouTube URL to the README, organizer draft and website
   embed. Keep the hosted MP4 as a fallback. No YouTube upload is claimed here.
2. **Public source:** the repository is public. Anonymous reads of the README,
   MIT license, development log, project design and both baseline JSONs succeeded
   on 18 October. Recheck the final pushed commit before submitting.
3. **Organizer form:** the user supplied
   https://forms.gle/t5YxsRpvUiG1rbdz7. Its fields were inspected without entering
   responses. Complete the [local draft](CATERING_SUBMISSION_DRAFT.md) with
   team-confirmed full names and Discord IDs, the final YouTube URL and checked
   source commit. **Show the completed entry to the user and obtain confirmation
   before submitting.** Do not infer identities from commit authors or accounts.
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
- Latest VQE uses E6 CVaR→Gibbs concentration, with 99.54% / 99.55% median
  offered-optimum probability on S2/S3 (10 seeds each). Its five saved states
  reproduce without training. The staged gain did not survive shot-noise emulation.
- QAOA and VQE use unequal training budgets. Show their measurements without
  declaring a matched-budget winner.
- VeloxQ-LNS reaches U=6/7 at 998/2,022 solver bits, versus U=7/8 for the retained
  30-second CP runs. This is an operational comparison with different budgets;
  longer CP and the exact-pair loop remain stronger controls. Backend time is
  distinct from end-to-end time.
- Investment what-ifs are finite-budget classical incumbents, not certified
  economic optima. One waste lot is **ten portions**, and no wages or equipment
  prices were supplied.

## Video publication handoff

The [watch page](https://qfactoria.com/video/) currently serves the hosted MP4
review/fallback. The current local cut is 4:52, in
[4K](https://qfactoria.com/video/axion-kitchen.mp4) and
[1080p](https://qfactoria.com/video/axion-kitchen-1080p.mp4), with 14 chapters and
stock male Kokoro `am_fenrir` narration. These links are not evidence that the
latest export has been deployed or checked publicly. Record the final verified
deployment in [the release receipt](assets/catering-final-check.json), rather
than copying an older deployment ID. The [provenance file](../presentation/video/provenance.json)
records the packaged media and source hashes.

**YouTube upload, URL, website embed and final public-playback verification are
pending.** The 2:45 live route remains a separate deliverable. Publication and
organizer submission are separate actions.
