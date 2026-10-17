# QPoland Quantum Hackathon — running context

## Presentation iteration and live playback — 17 October

Reworked the opening around two concrete orders and departures, enlarged the
kitchen view, removed duplicated hero headings and replaced the vanity stat
strip with order details. The close now seeks the actual 12:10 end state and
shows 20/20 delivered; previously it displayed an unfinished 11:39 replay
beside final outcome text. The math screen includes the complete weighted
objective and explicit hard-penalty term. QAOA has a prepare/cost/XY/sample/check
sequence, and the results table identifies tuple units and domain differences.

The live route holds each chapter at its end; Right Arrow advances when the
speaker is ready. P toggles audience view, hiding controls and notes. A small
playback module separates live holds from continuous video timing, with three
regression cases. Browser checks at 1280×800 and 1440×900 verify chapter holds,
iframe keyboard navigation, audience toggling, private notes and the actual
closing handover count. All 141 site tests and the build pass.

The game viewer now also shows discarded component portions beside meal service.
This follows disposal timestamps rather than displaying final waste early.
Browser checks verify zero waste in the saved cell, 0→10→20 discarded portions
across the manual intervention's departures, and 10 in the larger raw S3 case.
This small viewer addition follows the v2 recording's initial page load; its
numbers use exactly the same retained ledger. It requires no solver reruns.

Refreshed the narration/operator docs and added an eight-question quick table
to the detailed Q&A sheet. The revised silent 4:20 capture is under ignored
output/playwright/catering-showcase-v2/recording/. Its receipt preserves studio
source hashes and the actual raw local samples. Final owner result selection,
VeloxQ comparison, human voiceover and upload remain open. Shared solver models,
input contracts and quantum parameters remain unchanged. No training, remote
compute, VeloxQ call or physical QPU execution was performed.

## Presentation copy revision — 17 October

Replaced the “Two courses. One meal.” headline and related slogans with
concrete scheduling descriptions across the kitchen viewer, private studio,
chapter headings and speaker docs. Kept the game visuals. Changed display
text only; no model, objective, encoding or frozen solver workload changed.
The previously captured MP4 retains the older copy and needs a final re-record.

## Local recording, live studio and Q&A pack — 17 October

Prepared scripts/catering-showcase outside the deployed presentation root: actual
kitchen replay plus large model/code/results frames, a 4:20 silent video route
and 2:45 live route. The loopback server runs on 4193; the existing 4192 viewer
is untouched. docs/CATERING_LIVE.md, CATERING_VOICEOVER.md and CATERING_QA.md give
operator cues, timed human narration and likely questions with concise answers.
The Q&A pack includes clarifying bridges and direct disclosures for unmeasured
claims. It does not fabricate answers or quantum/VeloxQ superiority.

Recorded and visually checked the actual continuous studio capture: H.264,
1920×1080, 259.96 seconds, no audio; zero browser errors. The recorded launch
performs fresh 4096-shot sampling of retained p1/2026 QAOA angles: 3771 valid
shots, (0,0,2,2), 20 complete meals, zero waste. The displayed retained bitstring
also appeared 8 times. Training/service/QPU calls: zero. This remains one fixed
instance/seed execution, not another independent training trial. Outputs and
raw samples are preserved locally under ignored output/playwright/. The
method-owner selection and final VeloxQ finding remain visible draft slots.
Live browser checks passed for keyboard chapter navigation (including iframe
focus), the 20-meal counter, actual sampling and hostile-Origin rejection.
Python/JavaScript syntax checks and the static build with 138 tests pass.
No shared model, input contract, matrix or current game-viewer source changed.
No video upload, repository visibility change or submission was performed.

## Formulation review, proofs and quality audit — 17 October

The user emphasized that method owners are actively running models and that
changes are inconvenient. Keep loss/encoding/coefficient/input contracts frozen.
The review's validation guards do not alter current frozen workloads or require
any owner migration. Flag any future input/encoding change and its rerun impact
to the user before proceeding. No teammate message was sent.

PROJECT_DESIGN.md is now the standalone active catering specification, with
anchor equivalence, physical semantics, quadratic loss, exact lexicographic
weights, all-bitstring penalty proof, Ising convention and actual multi-angle
XY-QAOA settings. Prior factory design remains folded history in the same file.
docs/CATERING_QUALITY.md gives exact statuses, sampling probabilities and
raw/offered/returned comparisons. New read-only catering.audit_math checks 13
small bundles, independent physical pairs and complete-cell subset enumeration.

Three subagent reviews found no algebraic loss/encoding defect in the retained
fixtures. They identified two input-boundary gaps: unsupported future/malformed
outages and future-revealed active demand. Domain/snapshot validation and the
independent checker now reject those; the checker also validates snapshot time.
New regression tests cover constructor bypasses, unequal meal priorities and a
nonempty previous plan. Frozen inputs/samples/schedules remain unchanged.

Fresh checks: 51 core unittest cases (50 pass, 1 optional Qiskit skip), dedicated
Qiskit equivalence test passed, 66 offline adapter pytest cases passed; site build
passes 138 tests. Retained check validates 965 hashes, 152340 returned bitstrings,
467003sample frequencies and 8 final plans. Official Stage 1 selected quantum
evidence and root schedules recheck at 4h/8h. Six of eight final incumbents
attain the exact optimum of their final attempted pool, but all trail raw CP;
all eight final-step controls also tie their quantum outcome. This is a
representation/search-loss finding, not quantum superiority. Receipts are in
output/catering-math-audit-v1/. No quantum training or service calls occurred.

## Submission coverage and release privacy — 17 October

docs/STAGE2_SUBMISSION.md now contains the active catering deliverables and
all eight scoring categories (30 points), a separate VeloxQ criteria map and
release checklist. Current headline: QAOA plus larger same-model VeloxQ, with
classical references; VQE becomes a featured method only after checked results
justify it. No separate VQE result package was present on fetched main at this
audit. Do not equate method count with points.

GitHub was checked private. The user explicitly wants it private until the
final submission step to avoid early copying. Review the release beforehand,
then leave enough time to verify public access and submit before 18 October 15:00
Warsaw time. No visibility change or publication was performed. Repo cleanup
remains deferred; preserve evidence/manifests and avoid a last-minute history
rewrite. Public website exposure is a separate consideration from GitHub privacy.

## Presentation preparation and service update — 17 October

Active talk/demo planning is in docs/CATERING_PRESENTATION.md: the two-course
shared-side story, timed three-minute script, five-minute video storyboard,
exact kitchen interactions, current claim sheet and remaining launch/rehearsal
work. Preserve the game visual style. The current project design entry now
points to catering; the factory submission package is marked historical.

The VeloxQ owner committed four authorized service submissions: one contract
smoke and one cold job at each of 512/1024/2048 bits. Phase D valid rows were 5/512,
1/512,0/512; see docs/catering-methods/VELOXQ.md for receipts and scope. Earlier
blanket no-service statements below describe the earlier local release. Further
calls need their own concrete cap; this chat has performed none. Improving
feasibility and measuring a useful result is the prize-track priority, alongside
correct integration and reproducible scale evidence. No new training is requested.

## V3 implementation, frozen inputs and local verification — 17 October

The dual-award direction is now concrete. Read catering/README.md and the top
of docs/CATERING_QUANTUM_FIRST.md. Paired-meal scoring/checking, one-hot XY
compiler, exact-sector QAOA pilot, actual Qiskit exporter, offered-domain CP,
lossless bounded allocation enumeration, immutable input builder and evidence
verifier are implemented. No IBM or VeloxQ call, token use or credit spending.

Frozen research release output/catering-foundation-v3 has four six-customer
cases,33/35/31/35bit quantum portfolios and nested128/256bit scale pools.
Raw release optima: S0(2,0,6,6),S1(3,0,5,5),S2(2,1,6,6),S3(3,1,6,6).
Fixed quantum portfolios still lose service; they are not final kitchen solves.
Eight predeclared dynamic QAOA runs at output/catering-paired-pilot-v1 all
improve their empty initializers but trail raw CP. Preserve every negative run.

The separate output/catering-complete-cell-v3 includes all32legal programs,
35data qubits (3idle),1045sector states,59physically feasible states. Raw CP,
encoded CP, subset audit and exact-sector reference agree on(0,0,2,2). All6
p1/p2simulator trials recover that optimum, as do initializer/mixer-only controls.
It is a complete small-cell correctness example, not advantage. An actual
QAOA sample is exported to output/catering-complete-cell-demo-v3.json for UI.
The presentation/catering exporter now reads V3 evidence: five cases, sixteen
checked method/source views, complete-meal counters and mandatory recovery clean.
The actual game replay, equation/results panel and sources are integrated.

Independent output/catering-v3-verification.json rechecks965artifact hashes,
152340retained bitstrings,467003sample frequencies and8final raw plans.
Offline35qubit circuit audits give925CX(pilot) and1914CX(complete cell) on
synthetic57nodeheavyhex, not actual IBM target estimates. Width alone is not
hardware readiness. Current tests:45Python cases (one SDK test skipped there),
separate Qiskit test passes; npm run build passes with138site tests.
Preserve concurrent UI/package/test edits. V2inputs remain unchanged.
Older unbuilt/unpushed-profile notes below are historical; consult actual Git
state for remote publication, and do not assume teammate notification.

## Accepted priority: one entry targeting both prizes — 17 October

The user explicitly chose optimizing for winning the hackathon rather than
demonstrating quantum advantage, and wants to target VeloxQ too. Keep catering
as the integrated production-scheduling extension; finish correct paired-meal
math, checked quantum outputs, matched references/scaling and the game-style
demo/docs. QAOA is the current working default; compare with the existing VQE
human track and feature whichever method's real results justify. Standalone
SAT/exact-cover advantage research and speculative cluster growth are parked.
The other three people retain VeloxQ/QAOA/VQE ownership; no messages sent.

VeloxQ should solve larger/broader cases of this same declared model, share
smallQUBOs/checker with the other methods and produce measured quality,
feasibility, reference gaps and full runtime insight. Paper capacity is not
account entitlement and no service advantage is promised. The supplied PDF
Section15lists2000PLNoverall and1000PLNbestVeloxQ, with no explicit exclusion;
simultaneous awards to one team are not explicitly confirmed. Calls/uploads/
credentials/credit spending and IBM execution remain on hold. Preparing a
dual-award entry does not itself lift the spending hold. The V3 foundation is published at2fd816f and the larger scale handoff atd29038ad.
Do not infer that any teammate has pulled or completed their method.

## Paired-meal quantum workload and hardness gate — 17 October

The user wants a meaningful quantum-first problem given reported156-qubitIBM,
48GBMac and90+GBH100 access. New local paired-course v3 code requires main AND
side for a delivered meal, encodes completion/disposal quadratically without
product auxiliaries, and uses one-hot anchor blocks with local XY mixers.
Cross-block conflicts remain penalized; it is not a fully feasible mixer.
Quantum-led changing portfolios preserve incumbents; noCPteacher/repair.
The frozen remote handoff is now available. See the current top sections of
docs/CATERING_QUANTUM_FIRST.md; its older MIS-only section is historical.

Fresh local screen output/catering-paired-classical-screen-v1: S3customers4/8/12,
five seconds each, fourCPworkers, seed2026. N4OPTIMAL0.492s (3,1,4,4);
N8FEASIBLE5.002s (4,1,7,7), with minimumU4already certified by scalar bound;
N12FEASIBLE5.005s (5,1,11,11), bound permits U3. A timeout is not intrinsic
hardness or difficulty finding good plans. A35-qubit one-hot sector may contain
only279,936states and be exactly enumerable. Existing exploratory quantum
pilots remain worse than rawCP; no quantum advantage is established.
Prioritize matched controller/mixer comparisons and actual compiled depth over
qubit padding or arbitrary complexity. NoIBM/VeloxQ/H100 calls accompanied this
screen. Preserve other people's UI edits and all execution holds.

## Classical reference design — 17 October

The user requested the classical solution design. The concrete design is now
docs/catering-methods/CLASSICAL.md: direct raw batch-slot CP-SAT, exact references
on the actual quantum bundles and same-QUBO no-repair SA. It specifies quantities,
intervals, staffing, freshness, mandatory cleaning, semantic plan changes, exact
lexicographic priorities, statuses and comparisons. Distinguish full-model
representation loss from within-pool quantum search loss. Existing implementations
cover the current small cases; a larger independent-set exact adapter is optional
future work, not a new implemented result. Quantum remains the central method.
This design pass does not alter the frozen physics/encoding, spend service/QPU
credits or start external compute. Concurrent UI edits remain separate.

## Current correction and quantum-first priority — 17 October

The user clarified that the quantum method is the main project; classical
optimization is a reference/sanity check. See docs/CATERING_QUANTUM_FIRST.md.
Shared unit-demand encoding and a tested conflict-preserving mixer primitive
exist, with logical fixed-angle audits. They are not trained QAOA or hardware
results. Current capped pools lose one lot against the broader optimum and
fail the main-workload gate. Do not oversell them.

A user audit caught the omitted post-repair clean. The current profile is
core-contiguous-repair-clean.v2: mandatory W2/C2 clean at70–80 in S2/S3 because
A already uses W2 at60–70. Cooking on C2 must wait until80. Correct exact tuples:
S0=(0,0,1,0), S1=(0,0,1,2), S2=(1,0,0,1), S3=(1,0,1,2).
S3 serves the urgent order on C1. Use output/catering-foundation-v2/.
V1 outage results and any replay still using them are superseded. Cleanup time
is fixed by an explicit earliest-fixed-compatible conservative policy; movable
mandatory tasks and phase-aware recovery remain future extensions.
All32catering tests pass. Classical raw slots and exact/SA provide reference
checks. No IBM, VeloxQ or new remote allocations were used. Preserve existing
teammate UI edits and refresh stale replay data before a current-results demo.

Earlier entries below are historical; this section overrides conflicting status.

## Active direction: try catering; shared foundation then methods — 17 October

**First runnable handoff released:** catering/README.md points to the shared
compiler, loader, Ising conversion, decoder/checker and frozen
output/catering-foundation-v1/ inputs. Complete core widths27/91/9/46; deterministic
cap16 widths17/18/9/18. Native optional-interval master and independent selection
enumeration agree; quantum-size matrices also pass exhaustive bitstring audits.
All four cases have zero missed lots/waste and one new batch; this is an easy
small core, not a quantum/service advantage or full flagship.15tests pass.
The user has sent the assignment to the other people; they can start now using
our shared encoding rather than creating one per method. Our next classical
work is a raw decision model independent of program enumeration.

**Ownership clarification:** the user and this chat take classical benchmarking
and the shared foundation. The other three people take VeloxQ, QAOA and VQE.
The user authorized pushing the handoff to main now and starting our work.

The user now explicitly selected catering to try, superseding the earlier
factory-selected/catering-parked status below. Keep the verified factory as a
fallback. They requested four asynchronous human workstreams and clarified the
split: Codex first builds/freezes the common problem, QUBO, decoder, independent
checker and fixture bundles; then people independently own VeloxQ, QAOA, VQE
(interpreting “qve”) and classical native/SA benchmarks. Do not split the four
people into different kitchen-model implementations.

See [method work allocation](docs/CATERING_METHOD_WORKSPLIT.md) and
[solver contract](docs/CATERING_SOLVER_CONTRACT.md). These establish ownership,
handoff gates, exact coefficient/bit conventions, common outputs and controls.
No human names assigned, agent runs started or messages dispatched by this
allocation. Foundation code/bundles are not implemented by writing the plan.
Method work begins on immutable verified tiers as released. The ambitious
specification remains the target, with the same named core/stretch gates.
All IBM/QPU/VeloxQ execution holds and repository-cleanup deferral remain.

## Detailed catering specification requested — 17 October

The user requested a very detailed description of the most ambitious credible
catering version. Authored [the full specification](docs/CATERING_AMBITIOUS_SPEC.md):
batch creation/sharing, identified workers, fixed departures/freshness, explicit
discarded food/material, phase-aware WIP and interrupted cooking, four paired
event cases, finite ingredients/holding/power, exact QUBO/counter/factored options,
IBM budgets, validation, game-like demo and build/de-scoping gates. Proposed
10:50–11:30 outage addresses the earlier 09:30 fixture possibly missing the
fresh lunch production window. These are proposed new semantics, not executed
results or an activated pivot; preserve factory as the implemented main entry.
The full ambitious register additionally counts cumulative-capacity slacks and
recovery-task options. A deliberately unpruned initial capacity construction
would add 363 slack bits (385 with nominal demand slacks) before batch options;
this is accounting, not a compiled size or lower bound. No full-140-qubit claim.
All existing service/QPU execution holds remain.

## User-reported compute envelope — 17 October

**Live verification supersedes the earlier unverified-access notes:** see
[compute access and quantum budget](docs/STAGE2_COMPUTE_ACCESS.md). Mac hardware
is verified (M5 Pro, 15 CPU cores, 16 GPU cores, 48 GB). WCSS SSH works; the
Axion account accepted non-submitting 128 GB Bem/Lem CPU, 1 TB Lem CPU and one
Hopper GPU request tests. Queue predictions vary widely; no nodes were allocated.
Vast.ai lists zero current instances; pracus SSH timed out. The user clarified
the free-minute provider is IBM Quantum, whose public Open Plan is 10 QPU minutes
per 28-day window. Personal balance/backend is unverified; IQM uses free credits.
No simulation job, rental, QPU call or VeloxQ call accompanied these checks.

User reports140qubits as the maximum accessible physical-device size, and possible
H100/128GBCPU simulation resources. Use140as a ceiling, not a useful-QAOA target.
Resources/backend/calibrations are not independently verified; no remote compute
or quantum execution is authorized by this statement. Generic complex128 states
need4/16/32/64/128GiB for28/30/31/32/33qubits, before workspace. Start with a small
useful18–28qubit quantum core;30–32generic simulation is a measured stretch,
not a guarantee. Exact reductions first; restricted domains need loss accounting.
The broader model and integrated VeloxQ path need not fit a quantum register.
See catering proposal resource notes; factory remains the chosen main entry.

## Factory selected; current improvement work — 17 October

The user explicitly chose the factory over catering. Keep catering parked;
strengthen the same factory entry rather than split into a second project.
Priorities are an explainable recovery/representation result, bounded integrated
VeloxQ evidence after quota/authorization, an honest hardware feasibility check,
and a reliable demo/code defense/final submission. Actual remote-use holds remain.

A new offline post-hoc membership/energy diagnostic found that the retained
cap64on-time witness uses31of32assignments already in the original781-bit pool.
The single absent row is P02/pump/step0 on A1 with W06 at720–780. Its H3row was
already present. Adding this known-reference row gives782bits/26357couplers;
the checked encoded witness has energy855, equal to the retained full optimum.
Evidence: output/recovery-pool-diagnostic-v1/. This uses a known optimal plan as
a diagnostic teacher; it is not a new blind search method or lossless encoding.
Do not imply2078bits are necessary: that count belongs to the independently
constructed deterministic enrichment experiment. No optimizer/VeloxQ/QPU ran.

Current restricted QAOAcircuits retain all32operations at18/28/36circuitqubits
(default28), not the full assignment domain. Replacement p2all-connectivity
counts are196/548/932CX, depth71/185/250, before physical routing/calibration.
The complete optimization encoding has2499binary variables; its direct
one-bit-per-qubit QAOA register would require2499circuitqubits. No hardware
readiness or error-corrected logical-qubit claim follows from those counts.

## Latest extension-scope guidance — 17 October

The user supplied a later response described as official: manufacturing is
particularly valuable, but another domain may be equally interesting if it
adds genuine mathematical/algorithmic complexity, value, originality and
correctness. Saved verbatim in `docs/STAGE2_MENTOR_FEEDBACK.md`; author/date/link
were not supplied. Do not treat the earlier manufacturing preference as a ban
on other domains or the new response as approval of a specific model/award.

The user asked to reassess catering. The proposal chooses batches/yields,
shares output across customer demand and couples freshness to departure timing.
Only the18/16-bit fixed-option algebra audit exists; both toy optima remain
(missing,tardiness,excess,batches)=(0,0,0,2). No full flagship kitchen, native
raw-model comparison, large benchmark, QAOA or VeloxQ result exists for it.
Current recommendation: factory is the stronger evidenced submission today;
catering has potential as a substantive alternative/generalization only after
a bounded offline result justifies a pivot. Neither a new project nor limited
VeloxQ spending is authorized by this question. Keep one integrated Stage2 story.

## Technical merit complete — 17 October, supersedes historical status below

**Closeout:** all 14 agreed non-VeloxQ core requirements passed. The completed goal was technical merit implementation; actual VeloxQ, final synchronized video, human rehearsal and public release/submission remain open. [Current status](docs/STAGE2_STATUS.md) links evidence, limits and next actions. Final checks passed 52 targeted Python tests, all 113 site tests and the static build.

The user emphasized doing the scoped merit, math, visuals and docs thoroughly, and explicitly requested UI improvement. The main-model [math specification](docs/STAGE2_MANUFACTURING_MATH.md) is independently reviewed, with coefficient/penalty proofs and scope boundaries. The user prefers the game-like factory style and authorized it as the main demo. The current manufacturing workspace combines four recovery decisions, detailed machines/actual processing and attendance, complete pump progress, focused presentation and separate evidence views;120site tests/build and desktop browser checks pass. A fresh local28-qubit run returns0/855. VeloxQ belongs within this same Stage2 factory extension, not a separate project; officialPDFSections5/11/15 support integrated use. See [UI verification](docs/STAGE2_UI_DESIGN.md); mobile appearance is not visually certified. Final video/formal release remains deferred until after VeloxQ; its authorization hold is unchanged.

The user resumed work, explicitly requested multiple subagent passes, fixes and completion of the merit side except actual VeloxQ, and requested ongoing documentation. Current centerpiece: [complete-recipe manufacturing recovery](docs/STAGE2_MANUFACTURING_STUDY.md), [combined direction](docs/STAGE2_COMBINED_DIRECTION.md). Recovery-v2 certifies full-model weighted tardiness45→0 with replacement heat capacity; the original781-bit pool stays45. Deterministic enrichment restores0/855 using2078bits. Complete optimization has2499bits; exact deadline feasibility has818bits. Distinguish lossless pruning, lossy choice restrictions and a changed query.

The [recipe bridge](docs/STAGE2_RECIPE_BRIDGE.md) integrates simulated QAOA with all32operations through complete component choices at18–36logical qubits. QAOA and sectorSA each return18/18 valid same-pool optimal schedules; the constructor already finds the best plan, and sector enumeration is classical. No quantum advantage. Failed boundary-release attempts remain preserved. Six fixed-horizon feature ablations,32/64/128 scaling, exact count-only dense audit,135 synthetic economic sensitivities and four cold sponsor packets are implemented. Economics values checked priority-optimal plans rather than optimizing money. Cold operation-level annealing returns0valid of640; it does not prove those instances hard.

Current local studio: http://127.0.0.1:4192/manufacturing/ with `stage2.entry_demo`; it includes fresh recipe QAOA, representation comparisons, feature costs and adjustable economic assumptions. Final requirements/evidence are in [acceptance](docs/STAGE2_MERIT_ACCEPTANCE.md). No VeloxQ or physical QPU calls. The user authorized all-work private-remote sync and automatic site deployment; snapshot cdc4b8d is pushed and live, with this game-style refinement following it. Human presentation/video/public-source-release duties remain separate. The older paused state below is historical.

Updated: 2026-10-17 (Europe/Warsaw). Maintained as context arrives.

## Historical pause: explanation completed before refinement resumed

The user explicitly paused research on 17 October to understand the work.
No optimization processes remain running and no further search/training/hardware
jobs are scheduled. The latest larger probes completed before the pause; their
UNKNOWN results are retained, not classified as interrupted runs.

Start with [the current full explanation](docs/STAGE2_CURRENT_EXPLAINED.md) and
the local [visual guide](http://127.0.0.1:4187/stage2/start.html). These distinguish
the official Stage 1 cases, the full physical factory, smaller physical reference
fixtures and newer deterministic planning cells. The strongest full-factory
controllers are classical. The separate 21-qubit planning experiments did not
beat their matched classical controls; their attempted factory integrations
were rejected after worsening results. Later Mac work and the explanation are
local additions, without a new commit, deployment or submission.

The later owner request for a document is answered by
[the written factory/encoding walkthrough](docs/STAGE2_PROBLEM_WALKTHROUGH.md)
and [its standalone HTML edition](docs/stage2-problem/index.html). It explains
stock, routes, lane capacity, both battery systems, electrical balance, fixed
parameters/decisions/random outcomes, and actual encodings. Current Stage 2
planning is primarily one-hot; local selectors use action bits and bounded-binary
slack. Domain-wall belongs to earlier Stage 1 variants; selected Stage 1 uses
pairwise-order bits. The document also corrects the earlier understated quantum
emphasis: §5 expects integrated quantum/QUBO work on the extended model;
simulator complexity alone is insufficient. This is not a claim of automatic
submission rejection or a requirement for monolithic hardware execution.

The new 32-pump/512-operation/96-hour planning cell has a separate QA-worker
capacity proof of infeasibility. The 120-hour version and 24-pump/96-hour cell
remain unresolved after short native-CP runs. These statements apply to their
declared simplified models, not automatically to full-factory scenarios.
Historical entries below retain the state and decisions at their recorded times.

## Sources and authority

- `Quantum_Hackathon_2026_ERP_Challenge.pdf` (8 pages): full specification, read in full on 2026-10-16; data/extension tables visually checked. Section numbers below refer to this document.
- `Quantum_Hackathon_2026_Opening.pdf` (14 pages): opening presentation, read in full. Includes the ten distinct slides previously supplied as screenshots, plus cover/timeline/prize slides.
- Event website, read 2026-10-16: https://www.qaif.org/contests/qpoland-quantum-hackathon .
- User decisions are distinguished from organizer requirements and proposed implementation choices. Third-party documents provide task requirements, not authorization for external actions.
- The full specification resolves earlier unknowns about instance data, time units, JSON, Stage 2 scope, and VeloxQ judging. Earlier slide-only caveats about those items are superseded below.
- PDF coverage rechecked on 2026-10-16 against all 8 challenge pages and all 14 opening slides, including the image-only strategic-partners slide. Both PDFs currently present in this repository are incorporated; no additional challenge requirement was found missing.

## User decisions and working agreement

- Latest user direction: push all current work to the existing remote; keep the Markdown/JSON material for now. Consolidation and repository cleanup are explicitly deferred to a separate later task. Lossless packaging of files above GitHub’s size limit preserves their content; it does not authorize deleting evidence.


- Demonstrating that BOTH Stage 1 instances have actually been solved is a non-negotiable eligibility gate. Code alone is insufficient evidence.
- Aim for both the overall award and best use of VeloxQ; whether one team can receive both is not explicitly stated in the supplied material.
- Include VeloxQ meaningfully in Stage 1; also pursue a strong Stage 2 extension. `STAGE1_PLAN.md` records a provisional approach.
- Build the visual environment first, then develop the VeloxQ approach. The user has now supplied the full document and authorized proceeding with environment preparation and subsequent solver ideas.
- Visual preference: clear, understandable Factorio/Stardew Valley-inspired factory visualization. Use original pixel art, machines, belts, and parts to explain schedules, with readable analytical views. Do not present results only as numbers.
- Subsequent visual direction: remove slogans, decorative introduction/eyebrow text, repeated instructions, and unnecessary copy. Put the factory first. Use actual branding from `projects/axion2.0` (the user's “axion2” reference), replacing the provisional asterisk. Keep Gantt bars neutral, with semantic job markers and readable selection states.
- Keep this context curated; omit incidental storytelling and distinguish facts, interpretations, plans, and completed work.
- Stage 2 direction (2026-10-16): the user explicitly wants the most ambitious coherent/explainable environment first, even if solving it becomes much harder. Start complex; simplify only after actual modeling/solution difficulties, not preemptively for convenience.
- User explicitly authorized sharing `CONTEXT.md` by committing/pushing to `main`, superseding the earlier temporary privacy request. That initial context snapshot was pushed as `1123ff4`; later changes have not automatically been published.
- User has received VeloxQ onboarding and reports exporting `VELOX_TOKEN`, but explicitly directs **DO NOT use VeloxQ yet**. Do not make service calls, connectivity/quick tests, uploads or jobs until new explicit authorization. Token stays private in the execution environment, never code, logs or commits. Availability to this process is not verified.
- Remote: `origin` → https://github.com/Kolo-Naukowe-Axion/qhackathon26 .

## Fixed baseline problem (§§1–4)

Minimize makespan: completion time of the last operation of the batch.

- Every job visits each required machine exactly once, in fixed order T → F → S (T → F for Instance A).
- T = lathe/turning; F = milling; S = welding.
- Every operation starts once; machine operations cannot overlap; job precedence must hold.
- This is a flow-shop special case of JSSP. The document explicitly permits sequence-based encodings, asserting that an optimal permutation schedule exists for two/three machines. Treat that as scoped to the stated baseline; do not extend it to richer constraints without justification.
- Baseline output times are integer HOURS, starting at 0, with `end = start + duration` (§14).

### Instance A: 2 jobs × 2 machines (§4.1)

| Job | T [h] | F [h] |
| --- | --- | --- |
| Z1 | 2 | 1 |
| Z2 | 1 | 2 |

Required: its QUBO solved using a quantum algorithm on quantum hardware or a simulator, returning a feasible schedule. The QUBO requirement is explicit in the full document, beyond the abbreviated slide wording.

The document's §14 illustrative schedule has makespan 4: Z2/T [0,1), Z2/F [1,3), Z1/T [1,3), Z1/F [3,4). It is not evidence that this project has run QAOA.

### Instance B: 3 jobs × 3 machines (§4.2)

| Job | T [h] | F [h] | S [h] |
| --- | --- | --- | --- |
| Z1 | 2 | 1 | 2 |
| Z2 | 1 | 2 | 1 |
| Z3 | 2 | 2 | 1 |

Required: its QUBO solved with any quantum, hybrid, or classical QUBO solver, returning a feasible schedule. Quantum/hybrid methods are preferred and may improve the solution-quality score. VeloxQ is a planned choice, not mandatory for baseline eligibility.

These data match the introductory slide. Its displayed schedule has makespan 8:

| Machine | First | Second | Third |
| --- | --- | --- | --- |
| T | Z2 [0,1) | Z1 [1,3) | Z3 [3,5) |
| F | Z2 [1,3) | Z1 [3,4) | Z3 [5,7) |
| S | Z2 [3,4) | Z1 [4,6) | Z3 [7,8) |

The opening slide labels this optimal. The saved independent classical machine-order enumeration reference confirms the 8 h optimum (`output/stage1-preparation/instance_3x3.reference.json`; see `docs/STAGE1_OFFLINE.md`). This is classical reference evidence, not a quantum or VeloxQ result.

### Input/output contract (§14)

Official input JSON: `{ "problem": "erp_scheduling", "jobs": [{ "id": "Z1", "operations": [{ "machine": "T", "duration": 2 }] }] }`, with the complete operation arrays from the tables above. Transcribed inputs live in `instances/instance_2x2.json` and `instances/instance_3x3.json`.

Official output JSON fields:

- `instance`: `instance_2x2` or `instance_3x3`.
- `method`: actual method used; do not copy the example's QAOA label without running it.
- `makespan`: completion time of the last operation.
- `schedule`: objects with `job`, `machine`, integer `start`, integer `end`.

Required output files: `schedule_2x2.json` and `schedule_3x3.json`. Global baseline routes may be hard-coded. Stage 2 may extend/change the schema for realistic factory scenarios. The viewer's `axion-replay.v1` wrapper is a display format, not the official submission schema.

## Stage 2 freedom and competitive substance (§§3,5)

- Start from the baseline and develop an ambitious extension within a realistic manufacturing/scheduling context. Other ideas beyond the listed examples are permitted.
- Separate implementation is not prohibited; Stage 2 should remain conceptually connected to scheduling/manufacturing. A completely unrelated domain is not supported by the specification.
- Main scoring emphasis: richer realistic model, smaller correct formulation, justified algorithm, rigorous analysis. One fully formulated, solved, verified constraint is better than several sketches.
- Integrate reduction, algorithm comparisons, and scaling analysis on the EXTENDED model, rather than demonstrating each only on the original 3×3.
- Check every result against a classical reference (e.g. CP-SAT) for the SAME model. Report optimality gaps if a reduced formulation loses the optimum.
- For every added constraint, report variable costs in a naive time-indexed formulation and in ours.
- Also report the smallest correct QUBO for the baseline 3×3 so different teams can be compared. Organizer references: 72 variables at H=8 in the plain formulation; 39 after simple start-window pruning. These are organizer reference counts, not results achieved by this project.
- A polished interactive Gantt/end-to-end presentation earns credit when it showcases a strong extension; it cannot substitute for one (§5, p.4).

Suggested directions (optional; combine freely):

- Qubit reduction, alternative/logarithmic/binary/permutation encodings, decomposition, partitioning, XY-mixer QAOA.
- Compelling VeloxQ application: quality, scalability, performance, and insight into where the solver works best.
- QAOA/VQE/annealing/recursive-QAOA comparisons, error mitigation, warm starts from heuristics or LP relaxations.
- Scaling and statistical variability across repeated runs/seeds/parameters.
- Due dates/tardiness, sequence-dependent setup times, robust disruptions/outages, rolling planning with mid-operation state.
- More machines/longer routes and cost-benefit analysis of an extra machine.

Working Stage 2 proposal: **MetalTech under pressure**, documented in `docs/STAGE2_ENVIRONMENT.md` and `docs/STAGE2_IDEATION.md`. Two-hall pump manufacturing combines 24 known orders, 72 component lots, 384 nominal operations, 15 machines, 4 AGVs, 10 workers, BOM joins, batches, setups/tooling/wear, finite buffers/blocking, energy/batteries, quality/rework and causal rolling recovery. This is a design proposal developed in response to the ambition mandate, not an implemented or solved factory model. The full model stays the target; small audit cases do not replace it.

## Deliverables and scoring (§§6–12)

- Public MIT Git repository containing clearly separated/documented Instances A, B, and Stage 2 extension.
- Both baseline schedule JSON files included in the repository.
- README with run instructions and an explicit AI-use disclosure.
- Dated Markdown Development Log in the repository: development sequence, problems/fixes, decisions/reasons (including penalties/encoding/algorithm), rejected options, and learning about how the solution works.
- Project Design: exact model/state/variables/parameters, objective's linear/quadratic terms, constraints/interactions/weights, assumptions/simplifications, and feasibility conditions.
- Demo video ≤5 minutes, unlisted link allowed: launch and results, key code/own contributions, detailed model/method explanation, Development Log summary.
- Live program demo and presentation ≤3 minutes plus ~2 minutes of jury Q&A; explain design choices and conclusions. Slots assigned on 18 October.

| Criterion | Points |
| --- | --- |
| Correct QUBO formulation for quantum implementation | 5 |
| Makespan quality against reference/classical baseline | 5 |
| Extension creativity and complexity | 5 |
| Development Log | 3 |
| Project Design | 3 |
| Demo video | 3 |
| Live presentation and answers | 3 |
| Consistency: log ↔ code ↔ presentation | 3 |
| **Total** | **30** |

AI is fully allowed and encouraged. Participants must understand, explain, and take responsibility for the solution, record their learning, and disclose AI use in the README.

VeloxQ judging (§11): backend integration elegance/correctness, solution quality, scaling with size/complexity, experimental insight, clarity and reproducibility. Special prize (§15): most effective end-to-end integration, showing a compelling role alongside classical and quantum approaches. Merely calling the SDK does not establish a strong prize entry (our interpretation).

## Logistics and prizes (§§13,15–16; opening deck)

- Team size 1–5; fully remote, English default, Discord communication.
- Declare the team in `#lock-in-teams` before submission. Completion is not confirmed here.
- Kickoff: 16 October 2026, 18:00 UTC+2.
- Submit via Google Form before 18 October 2026, 15:00 UTC+2 (Warsaw time). Form URL still pending. Only the repository state at the deadline counts (opening slide).
- Live presentations: 18 October at 18:00 UTC+2. Website lists winners at 19:30.
- Awards: PLN 2,000 overall; PLN 1,000 best VeloxQ use (website labels amounts gross).
- Organizers/mentors welcome questions on Discord.
- After the event starts and the team is declared, one designated representative requests VeloxQ access from the email address the team will use for service communication: to `support@veloxq.com`, cc `contact@qaif.org`, subject `QPoland QUANTUM HACKATHON 2026`.
- Response supplies an individual token and connection instructions. Token is confidential and shared only within the team. Access status is unknown; no request email was sent in this chat.

## Compute and tooling

- User reports effectively unlimited CPU/GPU resources including H100 hours, and a local M5 Pro with 48 GB memory. Capacity/quota is not verified.
- User explicitly directs WCSS work to Axion quantum group resources.
- 2026-10-16 live check: `ssh wcss` successfully authenticated; group membership includes `knaxion` and `knaxion-knaxion-qc`; Hopper GPU partitions are visible.
- Slurm lists two other HPC allocations, without the Axion quantum association. Non-submitting `sbatch --test-only` using `knaxion-knaxion-qc` as the account failed with `Invalid account or account/partition combination specified`. Correct mapping remains unidentified. SSH access is confirmed; usable Axion GPU allocation/quota is not. Do not substitute unrelated allocations.
- No WCSS compute job was submitted or default account changed.
- VeloxQ SDK: https://github.com/quantumz-io/veloxq_sdk ; inspected README/wiki. Python API client with remote `VeloxQSolver.sample(...)` jobs; requires `VELOX_TOKEN`. SDK documents H100 backends and physics-inspired/metaheuristic algorithms. WCSS H100 access is separate from VeloxQ service access, and GPU hardware alone does not establish a quantum-algorithm run.

## Current work and outstanding items

- First presentation environment implemented: original pixel-art factory, replay/scrubbing, linked Gantt/part selection, schedule validation, provenance/evidence view, official schedule JSON/replay import, replay export, and presentation mode. Run with `npm run dev` (Node 20+, no dependencies).
- Ten automated tests pass. Browser checks confirmed timeline selection/seeking, evidence labels, 2×2/3×3 switching, playback completion at 4 h, and official-format JSON import. This verifies presentation/checker behavior, not solver execution.
- Built-in illustrations remain labeled as illustrations. Both actual mandatory baseline methods have now run locally: four-qubit QAOA for A (4 h), classical QUBO simulated annealing for B (8 h). Independently checked root schedule files and current evidence/replays are selected by `output/stage1-selected.json` under `output/stage1-local-ready/`; earlier runs remain under `output/stage1-ready/`. No VeloxQ or physical ODRA5 result exists yet.
- Stage 1 method distinction: §4.1 requires a quantum algorithm for A, including simulation; §4.2 explicitly permits any QUBO solver for B, with quantum/hybrid preferred. The working classical B result covers the baseline while VeloxQ integration remains an intended upgrade. Earlier ODRA5 authorization is superseded by the current hold on both remote backends; continue locally.
- Remaining dependencies: permission to use the now-reported VeloxQ access plus actual service verification; an authenticated IQM token route for physical ODRA5; team declaration status, submission form URL, explicit award compatibility, and full Stage 2 parameter/transition tables with a reachable WIP snapshot.
- Initial VeloxQ directions are recorded in `docs/VELOXQ_IDEAS.md`. The richer Stage 2 proposal supersedes its single-disruption candidate: investigate closed recovery neighborhoods within the full physical factory, with explicit restricted-domain claims and matched classical comparisons.
- Stage 2 structural blueprint: `instances/stage2/metaltech_pressure.json` and `scripts/stage2_blueprint.py`; generated workload/audit in `output/stage2-design/`. Audit confirms 384 nominal operations, 1,752 machine/mode alternatives and 8 exogenous leaves summing to probability 1. The 665,760 duration-window start choices are a partial size count, not a total QUBO or physical qubit count. The script does not simulate, solve or prove feasibility; missing tables are listed in its output.
- Next Stage 2 work: complete tables, transition semantics, independent event-trace checker and valid burn-in snapshot, then exact small references and recovery encoding experiments with all flagship rules retained. Stage 1 execution remains a separate eligibility gate.
- Formulations: one-hot 8/39 variables and domain-wall 4/30 for A/B at horizons 4/8. The corrected domain-wall encoding removes the binary-only exactly-one expansion before substitution; a proven incident-degree penalty prevents invalid-wall zero energies. All 512,000 pruned start assignments for B match independent constraints; 13 are feasible. The SDK BINARY→SPIN/HDF5 path, canonical variable order and result-label parsing are tested offline. See `docs/STAGE1_OFFLINE.md`.
- Earlier shared-X QAOA p=5/BFGS/eight restarts/4,096 shots gave 99.61% measured feasibility at seed 2026, with additional seeds about 98.12% and 98.54%; these are simulator results. A shallow four-qubit circuit is also prepared for IQM native compilation. Local Adonis noise proxies are not ODRA5 calibration or physical results.
- User authorized using the existing Axion e-science/SSH/VPN route for ODRA5 and generating a personal IQM token if needed. WCSS manual requires IQM client 35.0.3 and a personal API token even from SSH. The existing SSH login and active Axion quantum service were verified; no token was configured in the checked environments. The Axion CPU association `hpc-iwowoj-1781179048` is now verified, superseding the earlier unidentified-allocation caveat for CPU client work. Physical QPU access remains unverified.
- Current instruction: do not use ODRA5 or VeloxQ for now. Local refinement screened eighteen settings and validated the selections on ten new seeds: p=3 independent-X QAOA gave 40,960/40,960 valid shots; linear QUBO annealing at 32,000 sweeps gave 5,110/5,120 valid samples. Both remained optimal. Current selection is output/stage1-selected.json, pointing to output/stage1-local-ready/. See docs/STAGE1_REFINEMENT.md. Team submission/demo and Stage 2 remain separate requirements.

## Documentation and release rule — 2026-10-16

- User directs that documentation be updated to match the implementation and evidence before every commit and push.
- Current browser interface is the full factory world with a control-desk menu and `/problem-explanation` Stage 1 manual. The manual is linked from top navigation and footer, and its current solver evidence is checked against `output/stage1-selected.json`.
- Current verification: 18 Node viewer/manual tests and static build; 19 Python core tests in the solver environment and 2 optional compilation tests in the separate IQM environment.
- User explicitly authorizes committing/pushing all current new work to `main` and deploying the personal `iwos/qfactoria` project. This authorization does not change either external-solver hold.

- Stage 1 guide chapter 03 includes the actual matrix derivation, inspectable 8×8 coefficient ledger, triangular/symmetric conventions, offset and compact 4×4 example. The matrix is computed from the official durations and tested against the Python-generated model.

## Lunar appearance selection and release scope — 2026-10-16

- User chose 1 / Lunar Assembly as the fixed site appearance; update factory,
  control desk, Stage 1 guide and error page consistently. No live style picker.
- Preserve 2 / Frostline Works and 3 / Blueprint Bureau in the refined design
  archive, along with their preview images; retain the earlier seven separately.
- User explicitly requests updating docs, committing and pushing the completed
  current work. Clarification: **push completed Lunar + guide now; keep new Stage 2
  work local**. Use an isolated release checkout to preserve concurrent Stage 2 edits.
- Include the current QUBO matrix/dimensions guide improvements and hardware-access
  evidence note already present when this release began. Preserve newer remote
  methods-tutorial commits. Neither external solver hold is lifted.

## Stage 1 compact selection — 17 October 2026

- Latest Stage 1 selection supersedes the earlier time-indexed run selection above: `output/stage1-selected.json` now points to `output/stage1-compact-ready/`. Both official instances were solved by actual QAOA simulator sampling, at globally optimal 4/8 h.
- `solver/sequence.py` preserves both/all six common job orders using 1/3 bits; `E_A=4+a`, `E_B=9-a+3b-c-2ab+3ac-3bc`. Cycles cost 12/10 and are rejected. Full independent machine-order references establish zero loss on the official inputs. Minimality is only for distinct representation of every common order.
- Cost construction enumerates all n! common orders and therefore already reveals their optimum; this is a tiny exact representation, not scalable compilation or quantum advantage. A's one-qubit circuit is non-entangling. Earlier four-qubit A and classical 39-bit B remain comparison evidence.
- Eleven new settings were screened, seven confirmed on twenty fresh seeds (200–219). Selected A p=1/shared-X/one restart and B p=2/local-X/eight restarts each returned 81,920/81,920 optimal validation shots; root seed-2026 runs each give 4,096/4,096. Same-QUBO classical B annealing gave 10,240/10,240 optimal samples. Full details: `docs/STAGE1_COMPACT.md`.
- Default preparation now runs tests, original formulation audit and a compact quantum/classical bundle; `--time-indexed` retains the old path. Verified exports refresh root schedules, selection and guide evidence together. Source snapshots, counts, QASM, optimizer histories, certificates and per-run verification are retained.
- No remote backend use, public-repository change, event submission, commit, push or deployment is part of this refinement. Existing ODRA5/VeloxQ holds remain in force.

## Stage2 implementation and active research — 17 October 2026

The earlier Stage2 proposal-only / missing-tables statements above are historical. The full numerical one-minute factory, physical transition engine and independent trace checker now execute under `stage2/`; current scope and run instructions are in `stage2/README.md`. Preserve the separate Stage1 and site release work.

The user authorized8–9hours of active research from16October20:13UTC, up to500GPU-hours with ampleCPU, aiming to find the largest coherent explainable model with defensible results. Ordinary Axion SSH/CPU simulations work; ODRA/VPN troubleshooting and VeloxQ are held. No autoresearch workflow. Keep Stage2 local under the existing commit/push/deploy hold.

Current evidence includes physical kit-deadlock recovery, tool homes and QA-worker protection, paired TRAIN/VAL policy studies, small real simulated QAOA factory decisions, independently checked deterministic reference optima and a nonzero quality/material primary certificate at32orders/240hours. Full secondary factory optimality and quantum advantage remain unknown. A separate CPU statevector prototype reaches24total bits and has negative23-bit saved-pool results against fast exact/SA controls.

Source-sealed experiments, failures, costs and limitations: `docs/STAGE2_EXPERIMENT_LOG.md`, `docs/STAGE2_CLAIM_REGISTER.md`, and `output/stage2-search/compute-ledger.json`. Reserved final256tapes (firstseeds≥10000,32perexogenousleaf) are still untouched as of16October23:56UTC; all ordinary1000–1031 data are development-inspected. Current6-action PPO gains are matched by a fixedWIP6/QAguard4 control; do not imply dynamic policy advantage. Final policy selection/evaluation and delivery documentation are still ongoing.

### Stage2 research update — 17 October 2026, 00:58 UTC

The Stage2 final benchmark is now running from the globally sealed `output/stage2-search/final-frozen-bundle-v20p2/` (indexSHA496e56ca28b89a94a2bc86a3dcabd22bcfe8ed09b6f82355a497ac959473f44f). Ten cohorts/jobs6117508–6117517 use the same256 reserved tapes, true eight-leaf weights and fresh actor seeds. Eight completed cohorts have23,040 valid executions and576 independently rechecked original retained traces;16/24-order MPC remain pending. Sources/policies stay fixed. Stage2 remains local-only: do not commit, push, deploy, use ODRA/VPN, VeloxQ or autoresearch under the current hold. Preserve concurrent Stage1/site changes.

Current partial result report: `output/stage2-search/final-partial-0051-report/` (seven cohorts; MPC12 finished later). Original cheap selections remain12/static-grid,16/CEM6,24/CEM6 even when final results reverse development rankings. Final CEM16 meanmissing2.6906 vs PPO's constant-control2.4194 and broadstatic2.6030; CEM24 improves11.5992original→10.0209, versus10.3953broadstatic. The two predeclared QAOA mean-loss intervals both crosszero; no quantum advantage. Full factory primary/secondary gap is not generally known.

A fixed32-order policy at240hours fulfills everything on91.0156% probability-weighted final tapes; offline necessary quality/material bounds certify primary optimum on93.4375%, including trivial all-fulfilled cases. A separately declared posthoc audit-only replay of firstascendingpositive-boundattained finalseed10020 proves32demands/31shipments globally primary-optimal: P32's final pump necessarily fails both inspections, even under the safest legal mode. Its witness is excluded from all256-tape estimates and predeclared presentation replays. See `final-independent-audit/nontrivial-proof-seed10020/`. Tiny four-pump reference separately improved to[1480,1567]; it is not a fullfactory gap.

A new bounded TRAIN-only schedule-neighborhood audit (job6117537,32CPU,30min,0GPU) is an offline headroom/flatness study, not a selected policy or reopened final test: enumerate41single-coordinate schedules at12orders and741distance≤2 schedules at16/24, all TRAIN0–7. Per-tape minimum is explicitly clairvoyant and finite-neighborhood only, not a deployable policy/global6^8optimum. Preserve failures/incomplete envelopes. Remaining work includes audits, reporting, source-portability checks, docs and the actual-results visualization.

Live read-only GitHub metadata confirms `Kolo-Naukowe-Axion/qhackathon26` is private; the public-source requirement is currently unmet. Submission/video/team details are not verified. Two fresh portable demos (static and actualQAOA) pass in a clean stdlib-only environment in~1.3seconds; the selected CEM replay needs onlyNumPy and also passes. These are TRAIN0 reproducibility checks, not additional final estimates.

### Stage2 complete final campaign —17October2026,01:23UTC

All10frozen final cohorts now completed:74method/context groups,23,552valid executions and41declared paired contrasts in `output/stage2-search/final-complete-report/`. Independent audits verify592original retained traces, all-row fresh numerical anchors and unchanged43-file globalbundle/both40-file runtime archives. Read `docs/STAGE2_RESULTS.md` first; earlier partial snapshots remain historical.

MPC16 meanmissing2.30141/Pall.17406 improves selectedCEM2.69063; paired exploratory95% difference−.38922,[−.56797,−.21625]. MPC24 meanmissing11.26766 is worse than selectedCEM10.02094. The fixed selected-incumbent map stays unchanged; no final-policy retuning. Both predeclared family-of-two quantum intervals includezero. The rarePPO posthoc audit proves a real3→1→3switch on10062 that changes no shipments and worsens secondary metrics; don't claim globallyconstantPPO or adaptiveRL benefit.

Final campaign70.42allocatedCPUh/68.58measured episodeCPUh is INCLUDED in research386.68finishedCPUh as-of01:22; two diagnostics were still running in that accounting snapshot, not omitted free work. GPUrecorded0, QPU0. The fixed TRAIN-neighborhood job6117537 has since completed12184grid+24oracle-witnessreplays and is being audited, not used for new final selection. One bounded fresh reference search6117555 uses16CPU/2h with unchanged four-pump model/instance and checked1567hint; optimum interval remains[1480,1567] until a checked stronger result exists.

Portable package verification now checks literal file hashes plus24first-tape/first-actor final traces against fresh numerical instances, physical/identity/terminal/metric checks. Posthoc audit traces and TRAINdemos are separate. Publication/commit/push/deploy, ODRA/VPN and VeloxQ holds remain; publicrepo/video/form duties remain unmet or unverified.


### Stage2 technical research closeout — 2026-10-17 03:29:54 UTC

All tracked research cluster jobs are finished; the requested monitoring and handoff window remains active. The immutable 03:16 ledger records 431.9967 allocated CPU-hours including failed jobs, zero recorded GPU-hours and zero physical-QPU/VeloxQ calls. Final evaluation used 70.4178 allocated CPU-hours within that total. Local setup, audits and agent inference are not a complete host-wide meter. ODRA/VPN troubleshooting remains stopped under the user hold. No autoresearch, Stage2 commit, push, deployment or submission was performed.

The unchanged final benchmark has 74 groups, 23,552 valid executions and 41 contrasts. Independent audits freshly check 592 original retained traces and rebuild every row's numerical anchor. Preselected classical fulfillment is 94.9844% at 12 initial orders/96 hours and 91.0156% at 32 initial orders/240 hours, with substantial lateness in the latter. This is the tested-controller frontier; failures at 16/24 do not prove physical infeasibility. MPC improves 16 but worsens 24 against the selected CEM. Useful adaptive-RL and quantum advantage remain unestablished. Actual QAOA uses at most five total bits, including slack, in restricted local decisions with recorded classical fallback.

Exact reference job 6117555 reports FEASIBLE 1541 and CP lower bound 1524 on the identical four-pump fixture: interval [1524,1541]. Raw CP/hint identity rejections for reservations before pump birth remain preserved. A separate derived witness changes only move74.start from 1382 to 1420, preserving physical actions, timings and recomputed metrics; both unchanged general checkers pass. Six mutation/scope tests and a second independent review pass. Auditing and normalization run no new factory or solver, change no frozen checker and add no final sample. Evidence: final-independent-audit/reference-2h-6117555/ and reference-2h-methodology-review/. This does not bound the rich stochastic factory's global gap.

Portable v2 is 10,097,277 bytes, SHA 8a54050496537a794e17bdf73c7d47ed323798f0ae7e67e8152f6d49e3c0aaa1. Its 2,436 indexed files, 24 predeclared replays and 29 separate supplements verify in 10.84 seconds in isolated Python 3.14.6 with only NumPy 2.5.4 and pip installed. Supplemental records are hashed; their entire analyses are not rerun by this compact verifier. Portable v1 and the full 116.8 MB v2 archive remain byte-stable; the full archive independently reproduces all 41 contrasts and 592 retained replays. Read docs/STAGE2_RESULTS.md and output/stage2-search/stage2-portable-final-v2-closeout-receipt.json.

The local 4187 research view shows the final frontier, TRAIN neighborhood, conditional leaves, posthoc proof and current reference interval with qualifications. Frozen final-export SHA 6a66d36b2ea032b773a2b550d8773c13a0c4ea3f1fab0ef3565894853746fd60 remains unchanged. GitHub rechecked at 03:26 UTC is still private: the public-MIT requirement is unmet; completed video, team and form receipt remain unverified. Preserve the other chat's Stage1/root presentation changes and the publication hold.


Stage2 authorized eight-hour research window completed at 2026-10-17T04:14:35.500900+00:00. Technical evidence and local handoff are complete; all tracked research jobs are finished. See output/stage2-search/research-closeout.json and docs/STAGE2_RESULTS.md. Publication hold remains; repository private at the04:11UTC live recheck, with video/team/form receipt unverified. No further experiments or policy changes were scheduled at that closeout.

### Manufacturing entry refinement resumed — 17 October 2026

The user subsequently authorized improving the current manufacturing Stage 2
entry, problem definition and remaining local deliverables. This supersedes the
optimization/explanation pause. **Do not run VeloxQ or consume its credits.**
Existing physical-hardware and publication/commit/push/deploy holds remain.

Read `docs/STAGE2_ENTRY.md` as the current entry narrative; the original factory
and its frozen final evidence remain unchanged. A new explicitly synthetic
complete residual cell (not an extracted factory snapshot) combines alternate
machines, shared workers/skills, calendars, assembly join and weighted due dates.
Actual QAOA preserves all assignment one-hot groups using W/XY, with 18–34 logical
qubits and exact invariant-sector simulation. Sector memory is not qubit
compression; complete classical diagonal enumeration already reveals the optimum.

`output/stage2-entry-v2/`: source-sealed TRAIN selection p=2/CVaR .25; six instances
×ten TEST seeds ×three methods. QAOA gives 60 optimal actual schedules / 57 exact
QUBO minima, SA 60/60 both, uniform 59 schedules / 52 minima. Three QAOA makespan
registers overshoot 30; no operation repair or reference substitution. No quantum
advantage. TEST generalizes randomness, not unseen industrial instances.

Independent Qiskit audit v1 replays the18-qubit emitted circuit to1.0062e-15
probability error; larger QASM parsed/transpiled, not full-Hilbert replayed.
Nine offline SDK packets in `output/stage2-entry-velox-offline-v4/` include a
1,602-variable model. v2 caught float32 energy loss; final ×4 integer scaling
passes576 round-trip energies exactly. Platform acceptance/precision remain
unverified. No remote call. Final offline v4 forces an empty token in its own process before SDK import; earlier zero-token-lookup receipts count only explicit preparer lookups and overlook SDK import defaults. No credential was printed or used for authentication. Failed artifact versions are retained.

Fresh local demonstration: `.venv-stage2/bin/python -m stage2.entry_demo --port
4189`, then `/entry/`. It writes timestamped files under
`output/stage2-entry-live/`; static deployment exposes retained evidence only.
`python3 scripts/verify-stage2-entry.py` checks frozen hashes, every TEST plan and
generated view totals without optimization or network. Preserve all concurrent
older local edits and original Stage1/factory results. No user-owned new thread,
subagent delegation or recurring automation was requested.

Final local video review draft: `output/stage2-entry-video-v6/qfactoria-stage2-draft.mp4` (~173.217seconds), synthetic narration and edited real UI evidence with actual timestamped action frames. Submission/release duties remain in `docs/STAGE2_SUBMISSION.md`. The supplied mentor preference reinforces manufacturing but is pending wider jury consultation. No external message was sent.


### 17 October — larger offline VeloxQ handoff

Added catering/meal_scale.py and output/catering-velox-scale-v3/: same V3 model,
12-customer S3, 512/1024/2048 total bits including 26 idle bits. Read
 docs/catering-methods/VELOXQ.md. The larger matrices are losslessly compressed;
node scripts/restore-compressed-evidence.mjs restores exact hashed JSON locally.
No service calls or quota use; the service hold persists. Current game UI work
is still being ported and is separate from this scale handoff commit.


### 17 October — V3 game viewer integration

presentation/catering/ now exports five V3 cases and 16 checked method/source
views. CELL replays the actual p1/seed2026 QAOA sample (count13), its controls and
raw reference. Larger S0–S3 trace the final accepted seed2026 sample, same-step
exact portfolio reference and raw CP reference. Full pilot results are shown,
including all gaps. Complete-meal handovers replace component-allocation counts.
Mandatory recovery clean is rendered in the worker and resource timelines.
Skip-batch interventions remain explicitly manual. Model/results include equations,
actual sizes, scope, source hashes and limitations. No IBM/VeloxQ calls.


### 17 October — stronger classical scale controls

output/catering-classical-scale-v3/ uses the frozen scale bundle hashes,30second
one-worker references and2second cold SA, seed2026. Raw CP FEASIBLE(5,1,11,11).
Offered CP FEASIBLE(6,1,10,10)/(7,2,11,11)/(8,3,8,8). No optima certified; SA has
no valid returned state at2048. See docs/catering-methods/VELOXQ.md for the table,
initializer/scope caveats and reproduction. Zero service or hardware calls.


### 17 October — production order UI

presentation/catering/production-sequence.js projects cook/packing order, per-course
states and event times from the saved checked plan. The timeline opens in batch
view by default, with equipment switching and visible departures/parallel cleaning.
Cooking and Packing→orders tabs, Next/Previous event, and component tickets make
prep B→C versus cook C→B explicit. Replay duration is last action/departure rather
than unused model-horizon tail; physical instance/bundle files are unchanged.
No new training or solver/service execution. Current VQE split question was
informational; the user explicitly directed continuing the UI without training.
