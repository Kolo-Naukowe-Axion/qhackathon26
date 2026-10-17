# Submission preparation — catering active, factory package archived below

**Active direction, 17 October:** use the
[Axion Kitchen presentation/demo plan](CATERING_PRESENTATION.md) and
[current catering design](../PROJECT_DESIGN.md). The timed script, live
launch preparation, video storyboard, evidence map and VeloxQ improvement gates
are there. The owner has committed actual initial VeloxQ service receipts in
[the method report](catering-methods/VELOXQ.md). They are not factory results.

The archived section at the end is the earlier factory package. Its script, video, acceptance
counts and service holds are historical; do not copy them into the catering
submission as current evidence. Final catering video, rehearsal, public-source
check and submission receipt remain open.

The checklist below is the active catering turn-in plan.

**Correctness/design preparation:** the active standalone specification and
proofs are now in [PROJECT_DESIGN.md](../PROJECT_DESIGN.md). The
[quality audit](CATERING_QUALITY.md) adds fresh exact checks and separates
sampling, search and representation loss. Finish result selection and
reproduction at the release commit; these checks do not improve or replace
the measured larger-kitchen results.

## What we submit

One project: **Axion Kitchen**, a paired-course batch-production scheduling
extension of the original factory problem. Main plus side completes a meal;
unpaired components become waste. Scheduling decisions include shared yields,
equipment, qualified workers, phase times, freshness and recovery cleaning.

The frozen presentation emphasis is **QAOA plus VeloxQ**, with VQE comparison
and classical references:

- QAOA supplies the currently checked quantum method and sampled schedules.
- VeloxQ solves larger instances of the same versioned meal model and supplies
  the integrated backend/scaling study for its prize criteria.
- Raw CP, same-domain CP, exact small audits and SA establish feasibility,
  quality and representation loss. These remain supporting evidence.
- VQE is now integrated: five retained exports pass independent evaluation,
  and the E5 CSV reports higher per-shot optimum probability than QAOA on the
  same held-out portfolios. Training budgets differ; historical E5 angles and
  raw per-seed samples are absent. Showcase both with these limits; do not call
  this a matched-budget method win.

Present one primary quantum method well. Keep additional implemented methods
in the repository and comparison table. The official rubric has no separate
points for algorithm count, largest qubit count or physical hardware use.
Neither method names nor adding VQE automatically increases creativity credit.

**Current verification, 17 October:** main now includes the audited 400-run QAOA
campaign, the VeloxQ representation study, and all five checked VQE exports.
The benchmark browser links 148 retained source hashes. The [final review receipt](../output/catering-submission-review-v1/verification.json)
records 13 passing release stages on a clean export of `3653fd7d`. The last visibility check recorded GitHub private,
default branch main; recheck signed-out access only at the authorized release.
Both root baseline JSONs and MIT LICENSE exist. No visibility change or service
call is authorized or performed by this checklist.

## All 30 points: evidence and remaining gates

This is a coverage audit, not a prediction of jury scores. The rules define
the categories; the jury determines the points.

| Criterion | Points | Evidence we should put in the jury's path | Remaining gate / risk |
|---|---:|---|---|
| Correct QUBO formulation for quantum implementation | 5 | A concrete program bit; paired main/side objective; one-hot and conflict penalties; penalty bound; exact Ising convention; independent decoding/checks. Full derivation: PROJECT_DESIGN.md, including the price-of-realism count ledger. | Final chosen method must consume the declared bundle, preserve bit order and return raw samples with source hashes. Keep exact versus restricted domains explicit. |
| Solution quality versus reference | 5 | Stage 1 actual QAOA schedules A=4h and B=8h; Stage 2 small-cell optimum (0,0,2,2), all six QAOA trials and controls; larger method/reference table. | Largest substantive technical risk: larger quantum pilots trail raw CP. Improve the quantum search/representation where feasible, then freeze the strongest reproducible result. Stage 2 uses (U,W,B,R), not makespan; show that extension objective explicitly. |
| Creativity and complexity beyond baseline | 5 | Joint batch yields/sharing and paired-course service/waste terms without product-register qubits; constrained scheduling and compulsory recovery clean; measured loss from restricted portfolios. | Show why this changes the mathematics and decisions beyond a domain reskin. Do not claim unimplemented ingredients, power or money. No extra feature backlog needed for this argument. |
| Development log | 3 | Dated decisions and actual failures/corrections in DEVELOPMENT_LOG.md: repair clean, pairing formulation, encoding scope, precision, method trials. | The curated dated log links pivotal decisions and the full working archive. Its closing presentation frame summarizes three actual corrections. Verify the spoken summary at rehearsal. Do not rewrite failed experiments as successes. |
| Project design | 3 | PROJECT_DESIGN.md active catering section, linked complete formulation, data model, assumptions and solver contract. | The active design covers units, feasibility, objective weights, proofs and known limits; §5.1 derives variable counts by feature. Confirm the team can explain those choices. |
| Demo video | 3 | At most five minutes: actual program launch/result, core-code/model explanation, method and development-log summary. CATERING_PRESENTATION.md links the current executable 4:20 storyboard. | Technical fresh-sampling checks pass; human rehearsal and final recording remain pending. Record the current route, add human voiceover, upload and verify the playable URL. A static replay alone does not demonstrate a fresh solver launch. |
| Live presentation and Q&A | 3 | Three-minute story using the game UI, a short launch, readable objective/results and rehearsed answers. | Rehearse three times under 2:50. One speaker and operator, local fallback ready, all team members able to explain the central math. |
| Consistency of log/code/presentation | 3 | Versioned source/bundle hashes, common checker, explicit method labels and same metric definitions throughout. | Freeze one release commit and result set. Check every spoken number, screenshot, table and schedule against it. Separate fresh execution from saved samples and manual interventions. |

The five three-point categories total **15/30**. They are documentation,
demonstration and defense work, not a separate visual-design award. The game
style earns its place by explaining the actual optimization clearly.

## VeloxQ prize coverage

The official VeloxQ criteria do not list numerical weights. Cover all of them:

| Criterion | Existing contribution | Work that raises the case |
|---|---|---|
| Elegant, correct integration | Shared model/decoder, exact integer packets, sign/offset checks, no silent repair, raw receipts. | Keep the backend boundary small and reproducible; explain one concrete precision/encoding decision. |
| Quality of obtained solutions | The no-idle formulation returns 512/512 feasible samples at actual solver widths 486/998/2022. At 512 source bits and 20,000 steps the controlled change improves validity 17→512/512. | Valid objective quality still trails retained CP/SA. Explain the measured representation improvement; further service experiments need a separate capped budget. |
| Scaling with size/complexity | Nested larger portfolios of the same 12-customer input, measured bits/couplers/density. | Compare quality and feasibility along with loader/upload/queue/backend/total times. Escalate only when the smaller-tier result is useful. Large matrices alone are weak evidence. |
| Experimental insight | Proven penalty conditioning and redundant-idle elimination retain feasible optima while greatly improving service feasibility. Cold controls and failed attempts remain in the ledger. | Present the controlled comparison and its limits; feasibility improvement is distinct from best schedule quality. |
| Clarity and reproducibility | Frozen inputs, hashes, method result schema, ledger, offline packet checks and retained evaluations. | One documented restore/run/check path and a compact result table linked to raw artifacts. |

Do not treat backend running time as end-to-end time. The current service
returns final samples, so time-to-first-feasible is not observed; do not invent
it from job duration. If future instrumentation supports it, label that new
measurement. See the owner's report for approved versus still-proposed work.

## Required submission package

| Deliverable | Current status | Before turn-in |
|---|---|---|
| Working Stage 1 A and B | Selected simulator QAOA evidence and root schedule files exist; 4h/8h. | Re-run selected-evidence validator and inspect official JSON format at the release commit. Failure of either baseline excludes further assessment. |
| Stage 2 source and selected results | Compiler/checker, audited QAOA campaign, five checked VQE exports, classical references and VeloxQ representation study. Primary emphasis and live angles are fixed. | Freeze the final release commit and reproduce the documented launch; historical E5 VQE angles remain absent. |
| Clearly separated baseline / extension | solver/, catering/ and corresponding viewer paths exist. | README should offer the jury one obvious route to Stage1 and one to current catering; archive links stay subordinate. |
| Public Git repository with MIT | MIT file exists. GitHub visibility checked private on 17 October. User wants it kept private during development. | Review credentials/private assets beforehand. Publish only at the final submission step, then verify access while signed out and submit. A public website does not satisfy public-source access. |
| README with run instructions and AI-use description | Both sections exist, including current catering and service disclosure. | Keep disclosure aligned with final delivered methods; verify commands from a clean environment. |
| Dated Development Log | Exists. | Final entry records chosen methods, measured outcomes, decisions and verification. |
| Project Design | Exists with active catering entry and linked math. | Finish coherent current design and cross-check it against selected implementation. |
| Demo video URL, at most 5 min | Current 4:20 storyboard/script and verified v5 stills exist. The silent v2 rough cut is obsolete; final recording/audio are pending. | Record the current route, add human voiceover, upload and play through as a viewer. Include real launch/result, model/method walkthrough and log summary. |
| Live presentation, at most 3 min plus about 2 min Q&A | 2:45 executable live route with chapter holds, audience view, operator cues, fresh sample and Q&A cheats prepared. | Rehearse actual launch and screen-share layout, prepare fallback, attend assigned slot. |
| Organizer submission | No receipt recorded here. | Submit through the supplied form and retain acknowledgment, commit, video URL and team details. |

## Priorities and freeze

1. Preserve baseline correctness and the current evidence; do not spend effort
   adding algorithms or constraints for their names alone.
2. Technical work targets solution quality: quantum results on a useful declared
   domain, and VeloxQ feasibility/quality on the larger same-model workload.
   Quantum/VeloxQ owners keep their current assignments. This checklist starts
   no training, remote jobs or new spending.
3. In parallel, complete the runnable launch, objective/results frames, active
   design/log reading route and game demo. This work addresses half the points.
4. Target result freeze by **18 October 11:00 Europe/Warsaw**, final video and
   package check by 13:00. **Keep GitHub private until the final submission
   step**, per the user's instruction. Aim to publish at about 14:40, verify
   signed-out repository/video access, and submit by 14:45, leaving fifteen
   minutes before the official **15:00 UTC+2** deadline. These are preparation
   targets, not scheduled automation or authorization to publish before readiness.
   Live presentations start 18:00 UTC+2; use the assigned slot. A public demo
   website can expose the idea independently of repository visibility; its
   visibility must be considered separately before release.
5. The entry paths are consolidated: the current catering guide, project design
   and checklist lead to active evidence; older mixed handoffs and factory
   sections are archived with links. Frozen research artifacts remain at their
   source-hashed paths. Do not rewrite history or bulk-remove raw results.

## Release check and handoff

Run `python scripts/check-catering-release.py --output /tmp/NEW-RELEASE-CHECK`
in the documented foundation environment. It performs local technical checks,
including three fixed-angle sampling executions, and writes a release receipt.
Use `--full-qaoa` to independently decode every archived QAOA sample as well as
verify archive hashes. This command records no video and calls no service.

The package emphasis is fixed:

- Live circuit: complete-cell QAOA p=3, budget256/seed2026 trained angles,
  4096 fresh samples at sampling seed17102026.
- Method evidence: frozen QAOA400-run campaign, primary coupled-L2/CVaR0.1
  VQE E5 comparison and five checked exports; no equal-work winner claim.
- VeloxQ: equal20k-step source512 representation comparison plus the three
  actual solver widths. Keep changed matrix identities visible.
- Stage1: selected checked4h/8h JSONs. Design, log and MIT source accompany them.

Prepare these final form fields from the actual release; pending means pending:

| Field | Prepared value / remaining action |
|---|---|
| Project | Axion Kitchen |
| Description | Batch-production scheduling with paired-meal service and waste, quantum circuit optimization, and a proven VeloxQ representation improvement. |
| Repository | https://github.com/Kolo-Naukowe-Axion/qhackathon26 — keep private until the final authorized release; verify signed-out access then |
| Demo | https://qfactoria.com/catering/ |
| Benchmarks | https://qfactoria.com/catering/benchmarks/ |
| Source commit | Final checked release SHA; record it after the remaining edits are committed |
| Video URL | Pending current recording, human voiceover, upload and playback check |
| Team/contact declarations | Confirm actual organizer fields and team-provided details |
| Submission receipt | Pending; retain acknowledgment and exact submitted links |

See the [recording sheet](CATERING_RECORDING.md) and [Q&A/rehearsal sheet](CATERING_QA.md).
No public visibility change, upload or form submission is performed by this prep.

Rules authority: local `Quantum_Hackathon_2026_ERP_Challenge.pdf`, §§6–12 and 15.
No document completeness or proposed experiment guarantees points or either award.

## Archived factory package

[Preserved in the historical archive](archive/2026-10-17/FACTORY_PACKAGE_BEFORE_RELEASE.md#submission). It is not the active catering package.
