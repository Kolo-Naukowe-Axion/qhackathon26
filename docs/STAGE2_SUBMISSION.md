# Submission preparation — catering active, factory package archived below

**Active direction, 17 October:** use the
[Axion Kitchen presentation/demo plan](CATERING_PRESENTATION.md) and
[current catering design](CATERING_QUANTUM_FIRST.md). The timed script, live
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

The default Stage 2 headline is **QAOA plus VeloxQ**, with classical references:

- QAOA supplies the currently checked quantum method and sampled schedules.
- VeloxQ solves larger instances of the same versioned meal model and supplies
  the integrated backend/scaling study for its prize criteria.
- Raw CP, same-domain CP, exact small audits and SA establish feasibility,
  quality and representation loss. These remain supporting evidence.
- VQE is an additional method comparison if its owner delivers a checked,
  reproducible result before the freeze. It replaces QAOA as the headline only
  if measured quality/reliability and the explanation justify the change.

Present one primary quantum method well. Keep additional implemented methods
in the repository and comparison table. The official rubric has no separate
points for algorithm count, largest qubit count or physical hardware use.
Neither method names nor adding VQE automatically increases creativity credit.

**Current verification, 17 October:** fetched remote main; it contains the
retained QAOA catering pilot and VeloxQ receipts, but no separately delivered
VQE result package. GitHub reports this repository private, default branch main.
Both root baseline JSONs and MIT LICENSE exist. No visibility change or service
call is authorized or performed by this checklist.

## All 30 points: evidence and remaining gates

This is a coverage audit, not a prediction of jury scores. The rules define
the categories; the jury determines the points.

| Criterion | Points | Evidence we should put in the jury's path | Remaining gate / risk |
|---|---:|---|---|
| Correct QUBO formulation for quantum implementation | 5 | A concrete program bit; paired main/side objective; one-hot and conflict penalties; penalty bound; exact Ising convention; independent decoding/checks. Full derivation: CATERING_QUANTUM_FIRST.md. | Final chosen method must consume the declared bundle, preserve bit order and return raw samples with source hashes. Keep exact versus restricted domains explicit. |
| Solution quality versus reference | 5 | Stage 1 actual QAOA schedules A=4h and B=8h; Stage 2 small-cell optimum (0,0,2,2), all six QAOA trials and controls; larger method/reference table. | Largest substantive technical risk: larger quantum pilots trail raw CP. Improve the quantum search/representation where feasible, then freeze the strongest reproducible result. Stage 2 uses (U,W,B,R), not makespan; show that extension objective explicitly. |
| Creativity and complexity beyond baseline | 5 | Joint batch yields/sharing and paired-course service/waste terms without product-register qubits; constrained scheduling and compulsory recovery clean; measured loss from restricted portfolios. | Show why this changes the mathematics and decisions beyond a domain reskin. Do not claim unimplemented ingredients, power or money. No extra feature backlog needed for this argument. |
| Development log | 3 | Dated decisions and actual failures/corrections in DEVELOPMENT_LOG.md: repair clean, pairing formulation, encoding scope, precision, method trials. | Add a short reader route to pivotal entries and final method choices. Record AI-assisted work and the team's own review. Do not rewrite failed experiments as successes. |
| Project design | 3 | PROJECT_DESIGN.md active catering section, linked complete formulation, data model, assumptions and solver contract. | Produce one readable active narrative including units, feasibility, objective weights, proofs, method settings and known limits. Archived factory material must be visibly historical. |
| Demo video | 3 | At most five minutes: actual program launch/result, core-code/model explanation, method and development-log summary. CATERING_PRESENTATION.md links the executable studio and silent 4:20 rough cut. | Fresh frozen-angle sampling is rehearsed and recorded. Freeze owner results, add human voiceover, upload and verify the playable URL. A static replay alone does not demonstrate a fresh solver launch. |
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
| Quality of obtained solutions | Checked cold runs at 512/1024/2048 variables, with classical controls and idle witnesses. | Main priority: improve feasible-return rate, then valid objective quality under a capped authorized experiment. Feature the best reproducible checked setting with its scope and budget. |
| Scaling with size/complexity | Nested larger portfolios of the same 12-customer input, measured bits/couplers/density. | Compare quality and feasibility along with loader/upload/queue/backend/total times. Escalate only when the smaller-tier result is useful. Large matrices alone are weak evidence. |
| Experimental insight | Current cold returns expose one-hot violations and penalty-dominated energies. | Show a controlled change and what it fixes. Preserve the unchanged control and disclose any new bundle/coefficient version. |
| Clarity and reproducibility | Frozen inputs, hashes, method result schema, ledger, offline packet checks and retained evaluations. | One documented restore/run/check path and a compact result table linked to raw artifacts. |

Do not treat backend running time as end-to-end time. The current service
returns final samples, so time-to-first-feasible is not observed; do not invent
it from job duration. If future instrumentation supports it, label that new
measurement. See the owner's report for approved versus still-proposed work.

## Required submission package

| Deliverable | Current status | Before turn-in |
|---|---|---|
| Working Stage 1 A and B | Selected simulator QAOA evidence and root schedule files exist; 4h/8h. | Re-run selected-evidence validator and inspect official JSON format at the release commit. Failure of either baseline excludes further assessment. |
| Stage 2 source and selected results | Implemented catering compiler, checker, QAOA pilot, references, VeloxQ adapter/receipts. | Select primary method, evaluate returned samples, freeze settings/result IDs and reproduce the documented launch. |
| Clearly separated baseline / extension | solver/, catering/ and corresponding viewer paths exist. | README should offer the jury one obvious route to Stage1 and one to current catering; archive links stay subordinate. |
| Public Git repository with MIT | MIT file exists. GitHub visibility checked private on 17 October. User wants it kept private during development. | Review credentials/private assets beforehand. Publish only at the final submission step, then verify access while signed out and submit. A public website does not satisfy public-source access. |
| README with run instructions and AI-use description | Both sections exist, including current catering and service disclosure. | Keep disclosure aligned with final delivered methods; verify commands from a clean environment. |
| Dated Development Log | Exists. | Final entry records chosen methods, measured outcomes, decisions and verification. |
| Project Design | Exists with active catering entry and linked math. | Finish coherent current design and cross-check it against selected implementation. |
| Demo video URL, at most 5 min | Silent 4:20 rough cut and timecoded voiceover draft exist; final owner results and audio pending. | Upload and play through as a viewer. Include real launch/result, code/model/method walkthrough and log summary. |
| Live presentation, at most 3 min plus about 2 min Q&A | 2:45 executable live route, operator cues, fresh sample and Q&A cheats prepared. | Rehearse actual launch and screen-share layout, prepare fallback, attend assigned slot. |
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
5. Repo cleanup remains deferred. At packaging, improve the entry path and
   separate current work from archives first. Before moving/deleting anything,
   preserve evidence and check imports, tests, manifests and source-hash links.
   Do not rewrite history or remove raw results during the final freeze.

Rules authority: local `Quantum_Hackathon_2026_ERP_Challenge.pdf`, §§6–12 and 15.
No document completeness or proposed experiment guarantees points or either award.

## Archived factory package

17 October 2026. This is prepared local content, not a submitted entry or a
public release. Actual VeloxQ use, physical QPU calls, public-source publication
and final submission remain held. The user authorized syncing the private
repository and its configured automatic site deployment; see [current status](STAGE2_STATUS.md).

**Technical acceptance:** all 14 agreed non-VeloxQ core requirements passed.
The final test/build receipt records 52 targeted Python tests and 113 site tests.
See [current status](STAGE2_STATUS.md) and the [acceptance matrix](STAGE2_MERIT_ACCEPTANCE.md).
This closes technical merit; it does not complete the external/human duties below.

## Suggested title and description

**QFactoria: preserve the choices that recover a factory deadline**

QFactoria asks which capacity rescues manufacturing deadlines and which QUBO
representations preserve its value. Two complete 16-operation pump recipes
jointly assign machines, qualified workers and start times, with assembly joins,
calendars, transfers and family changeovers. Replacing heat capacity eliminates
45 weighted late minutes in a certified complete-model comparison. An exactly
solved 781-bit pool misses that recovery; deterministic enrichment restores it
at 2,078 bits. Our support-pruned complete optimization encoding uses 2,499 bits, while an exact hard-deadline
query needs 818 bits. These alternatives have different guarantees.

A whole-recipe QAOA bridge recombines all 32 operations through eight component
groups, using 18–36 logical qubits. QAOA and classical annealing each return
18/18 valid same-pool optimal schedules; uniform sampling returns 6/18 valid
optimal encodings. The constructor already finds the optimal recovery plan,
sector energies are enumerated classically, and budgets differ. No quantum
advantage is claimed. Independent circuit replay verifies the six 18-qubit
circuits; larger circuits receive logical resource audits.

Six fixed-horizon feature ablations quantify bits, couplers, coefficient scale
and solution quality. Scaling reaches 128 operations with explicit UNKNOWN
complete references and checked bounds. An exact economic ledger values four
checked plans under synthetic energy, standby, labor, night premiums, startup and
lateness prices, with 135 sensitivities and purchase/event-fee thresholds. It
values priority-optimal schedules; it is not calibrated industrial ROI or full
weekly minimum-cost optimization. Failed representations and cold annealing
controls remain part of the evidence.

## Prepared material

| Item | Authoritative local evidence |
|---|---|
| Official Stage 1 outputs | `schedule_2x2.json`, `schedule_3x3.json`, `output/stage1-selected.json`; QAOA simulation, independent optima 4/8 hours |
| Design and full merit map | `PROJECT_DESIGN.md`, `docs/STAGE2_COMBINED_DIRECTION.md`, `docs/STAGE2_MERIT_ACCEPTANCE.md` |
| Complete recovery pair | `output/manufacturing-recovery-v2/`, `output/manufacturing-full-recovery-v1/` |
| Nested enriched frontier | `output/capacity-frontier-review-v1/` |
| Exact deadline query | `output/deadline-decision-review-v1/` |
| Cold controls | `output/deadline-anneal-review-v1/`, physically rechecked in `output/deadline-anneal-report-audit-v2/`: 0/640 raw-valid returned samples at stated budgets |
| Full-recipe QAOA | `output/recipe-bridge-review-v2/`, circuit audit `output/recipe-bridge-circuit-audit-v1/`, return/count audit `output/recipe-bridge-reporting-audit-v1.json` |
| Feature and scaling costs | `output/realism-frontier-v1/`, exact dense count supplement `output/realism-continuous-counts-v2/` |
| Capacity economics | `output/capacity-economics-v2/`, `output/capacity-economics-independent-audit-v1.json` |
| Four current cold SDK files | `output/sponsor-merit-packets-v1/` plus `output/sponsor-enriched-matched-penalty-v1/`: 818 deadline, 2078 enriched at two penalties, 2499 complete; 815,121 coefficient/constant equality checks |
| Smaller independent quantum study | `output/stage2-entry-v2/`, its circuit/claim audits; 60/60 optimal actual schedules, 57/60 exact measured minima. Separate scope from the bridge |
| Demo | `.venv-stage2/bin/python -m stage2.entry_demo --port 4192`; `/manufacturing/` includes saved comparisons, fresh local whole-recipe QAOA, economics and feature table |
| Reproducibility | `scripts/verify-stage2-merit.py`, final validation and independent consistency receipts linked by the acceptance matrix |
| Explanation and disclosure | `docs/STAGE2_LIVE_SCRIPT.md`, `DEVELOPMENT_LOG.md`, README AI-use disclosure |

Frozen artifacts retain input definitions, literal source snapshots, parameters,
raw samples, checks, QASM where applicable and SHA-256 manifests. Final checks
verify those historical bytes without requiring them to equal later code.
The static website does not execute Python or contain credentials.

The earlier six-model cold/witness packet campaign is retained separately; it
is not the four-file current comparison. Offline SDK serialization proves no
backend speed, sample quality, acceptance, credit availability or sponsor
eligibility. Native CP solves these small decision queries quickly; failed local
annealing does not establish intrinsic hardness or predict a VeloxQ win.

## Video and external duties

The existing [161.9493-second manufacturing review cut](../output/manufacturing-video-v3/qfactoria-manufacturing-review.mp4)
predates the enriched/deadline/whole-recipe/economics additions. It remains a
review draft, made from edited real UI captures with synthetic narration. It
is not the final synchronized video. Use the current live script for the final
recording; human review and accessible hosting are still required.

Human actions remain: review the exact release and narration, rehearse the live
slot and Q&A, confirm team declarations, authorize the public MIT release,
record/upload the final video, and submit the required public repository,
schedules, design/log, team information and video URL through the official
form. Preserve a submission receipt. The recorded organizer deadline is
18 October, 15:00 Warsaw; verify the actual form before external submission.
No final video, publication or submission is implied by completed merit checks.

Actual VeloxQ requires separate explicit authorization for a bounded pilot,
current credits/access checks and a preserved raw result. The runbook specifies
same-input comparisons, feasible objective/target quality, time, returned-sample
counts and exact decode checks. No paid or remote action has occurred here.
