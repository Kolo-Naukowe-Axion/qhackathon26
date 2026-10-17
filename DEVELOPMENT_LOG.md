# Development log

## 2026-10-17 — presentation iteration and live playback

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

## 2026-10-17 — remove slogan-style presentation copy

Replaced the “Two courses. One meal.” headline and related slogans with
concrete scheduling descriptions across the kitchen viewer, private studio,
chapter headings and speaker docs. Kept the game visuals. Changed display
text only; no model, objective, encoding or frozen solver workload changed.
The previously captured MP4 retains the older copy and needs a final re-record.

## 2026-10-17 — local recording, live studio and Q&A pack

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

## 2026-10-17 — three formulation reviews and a standalone project design

The user emphasized avoiding disruption to the other owners' in-flight models.
No loss, QUBO coefficient, variable ordering, frozen instance or bundle hash was
changed. Validation fixes affect only out-of-profile/malformed inputs. Current
owners need no new input or rerun; any future migration must first be raised
with the user. Kept the existing source snapshots and all retained runs.

Rebuilt PROJECT_DESIGN.md around the active paired-meal model and retained the
earlier factory design as folded history. The active document specifies the
data/decisions, finite-grid physical rules, unit-demand anchor bijection,
quadratic complete-meal/waste objective, exact lexicographic hierarchy,
full-polynomial penalty bound, 4E Ising mapping and actual quantum algorithm.
The proof deliberately handles negative objective values on invalid strings;
the actual cell's all-ones objective is negative while the penalty remains safe.

Added docs/CATERING_QUALITY.md and read-only catering.audit_math. Fresh checks
recompute 13 small-domain exact optima, compare independent physical pairs with
the conflict graph, verify polynomial/Ising identities and re-encode final
incumbents in their final offered pools. Six of eight are same-pool optimal;
all eight still trail raw CP. All eight final-step controls also tie the
quantum outcome, so this finding establishes no cost-phase advantage. Distinct
scalarizations, sampling success, feasibility, representation loss and search
loss are reported separately, including the FEASIBLE S0/256 incumbent whose
tuple matches a certified raw optimum.

The user requested several problem-formulation review passes. Three read-only
subagents examined loss/physical semantics, encoding/proofs and reference/quality
consistency. They found no algebraic/material-balance defect in current fixtures,
but reproduced two input-boundary bugs. Future, malformed or non-cooker outages
passed validation despite the observed-withdrawal profile; future ordinary
demand could enter a snapshot before reveal. Added fail-closed validation and
independent checker guards, including integer/grid/horizon snapshot time.
Regression tests cover those examples and constructor bypass, plus unequal
priorities/nonempty previous plans and physical-subset/anchor equivalence.
Current frozen artifacts satisfy the clarified boundaries and are unchanged.

The initial full unittest discovery exposed optional adapter imports in the
lightweight environment. Corrected the documented core test pattern and used
the separate SDK environment for Qiskit and adapter pytest. Installed pytest
as a local test tool; no runtime dependency or backend budget was changed.
Fresh results: 51 core tests (50passed, 1 optional SDK skip), the dedicated Qiskit
equivalence test passed, 66 offline adapter tests passed with three SDK deprecation
warnings; static build and all 138 site tests pass. Retained recheck covers 965
artifact hashes, 152340 bitstrings, 467003 sample frequencies and 8 final plans.
Stage 1 selected evidence verifies optimal 4h/8h and matches the root schedules.
Receipts and source hashes: output/catering-math-audit-v1/. No quantum training,
service submission, QPU use, public release or repo cleanup occurred.

## 2026-10-17 — paired-meal foundation, complete quantum cell and retained scaling pilot

Implemented paired-course v3: complete meals require main AND side, and reserved
unpaired components become explicit disposal at departure. The checker rebuilds
service records and per-batch material balances. Completion/waste are quadratic
in unit program coverage with zero product-register qubits. The full objective
span gives a safe penalty despite negative coefficients on invalid selections.
One-hot anchor blocks add real idle data qubits; local XY preserves one choice,
while crossing physical conflicts remain penalized. Old v2 inputs are unchanged.

Replaced exponential demand-quantity scanning with an exact bounded multiset
enumerator, tested against the Cartesian definition. Added offered-domain CP
with exact quadratic objective, separate from the independent raw batch-slot
model. New builders retain source snapshots and immutable experiment plans.
Frozen six-customer research inputs have33/35/31/35quantum bits and nested
128/256bit scale pools. All4raw release references reached OPTIMAL. Restricted
quantum pools lose service, and the predeclared eight-run QAOA portfolio pilot
still trails raw CP. These negative results remain part of the evidence.

Created a complete small physical cell with explicit preparation/attendance
calendars: all32legal programs,35data qubits,1045one-hot states,59physically
feasible states. Raw CP, offered CP, independent subset audit and sector minimum
agree on U0,W0,B2,R2. All6p1/p2simulator trials recover it, and initializer and
mixer-only controls do too. No quantum superiority is inferred. A separate demo
receipt selects an actual retained QAOA sample rather than relabeling a reference.

The independent verifier checks965artifact hashes,152340retained bitstrings,
467003sample frequencies and8final raw plans. Actual Qiskit9qubit/full-Hilbert
and routed-circuit tests validate the sector implementation. Synthetic heavy-hex
compilation of35qubit circuits requires925CX(pilot) and1914CX(cell); these are
not calibrated IBM results. The44test Python suite passes with one SDK skip;
the SDK test passes separately, and npm run build passes. The other chat's
existing catering UI still uses v1 evidence and needs a V3port before presentation.
Updated README, solver contract, work split, math/evidence, reference design,
compute notes and historical-proposal banners. No remote solver, QPU, new compute
allocation, credit spending, organizer message or teammate message was used.

## 2026-10-17 — classical reference formulation and comparison design

Authored docs/catering-methods/CLASSICAL.md at the user's request. The design
maps the existing direct batch-slot CP-SAT implementation to raw quantities,
allocations, timing, resource/worker intervals, mandatory repair clean and exact
lexicographic U/W/B/R. It explains slot-bound completeness and semantic prior-plan
matching, and documents the corrected S2/S3 regression answers. Separate raw
and same-input exact references distinguish representation loss from quantum
search loss; literal SA remains a no-repair heuristic control. The design sets
status/bound/timing rules and a minimal execution order so classical validation
does not become the project's centerpiece. Linked the quick start and work split.
No solver implementation, frozen release, service/QPU run or remote allocation
was changed by this documentation pass. The 32-test catering suite was the last
verified implementation state before the pass; no new experiment is implied.

## 2026-10-17 — quantum-first direction and mandatory repair-clean correction

The user redirected the project toward quantum-first modeling, with classical
methods as sanity/reference checks. Added a unit-demand coverage-reward QUBO
without missed registers, a full-objective-range penalty proof and a logical
conflict-preserving controlled-rotation mixer. Attributed the established mixer
construction. All32catering tests pass, including independent all-bitstring/raw
checks, norm/support invariants and cleanup omission/early-cook regressions.

A user audit identified the missing mandatory ten-minute post-repair clean.
Corrected snapshots, raw checking, local option generation, CP references and
decoding together. Conservative core policy reserves W2/C2 at70–80; A consumes
W2 at60–70. New output/catering-foundation-v2/ gives S2 U=1/B=0 and S3 U=1/B=1,
serving only the urgent order on C1. All four exact/native audits agree. V1
outage results are superseded and preserved without overwriting their receipts.
The clean is fixed by an explicit policy, not an optimized recovery-task choice.

Retained quantum-first v1 diagnostic had clique-only pools and was rejected.
V2 admits compatible batches but caps8/12/16/20 all still miss one lot relative
to the complete359-bit raw-reference domain. Fixed-angle logical probes verify
feasibility preservation, not trained performance or hardware feasibility.
These pools fail the main-workload gate; improving the restriction and costing
the controlled gates remain necessary. See docs/CATERING_QUANTUM_FIRST.md.

Direct raw batch-slot CP was completed before the quantum-first clarification.
The classical-v1 outage answers omit the clean and are historical. S0-only
calibration remains an old-profile diagnostic, not the new quantum workload.
Current small sanity cases are retained in output/catering-classical-v2/.
No service/QPU calls or remote allocations were made. Existing concurrent UI
work remains separate; any v1 replay needs refreshed data before presentation.

## 2026-10-17 — runnable catering foundation and first classical references

Implemented the complete finite-grid contiguous-packing conservative core,
four common-prefix event cases, explicit raw operation/material checker,
QUBO/register/Ising compiler, decoder, stable loader/evaluator, native optional-
interval program master, exact QUBO enumeration and seeded no-repair SA.
The user committed the in-progress shared code as94f6cf1while work continued;
preserved it and added boundary validation, quick start and frozen artifacts.

First input release output/catering-foundation-v1/ has42artifact hashes and
12source hashes verified. Full core widths/couplers:27/351,91/3782,9/36,46/946;
quantum cap16:17/136,18/149,9/36,18/140. Independent full-domain raw-subset audits
check27/4006/9/991selections. Restricted QUBOs exhaust131072/262144/512/262144
bitstrings. Native references are OPTIMAL and agree with independent minima.
All four optima have U=W=0 and B=1; R=0 for S0 and2otherwise. The restriction
retains these optima but is not a lossless-domain proof. These are easy starter
cases, not a performance/quantum advantage.15meaningful tests pass. Advanced
failure/WIP/capacity/money profiles remain explicitly unsupported. No external
compute, IBM or VeloxQ use. Method owners may now use our frozen encoding.

## 2026-10-17 — handoff push and classical ownership

The user assigned this chat the classical track plus the shared catering
foundation and authorized pushing the handoff to main so the three other
people/agents can take VeloxQ, QAOA and VQE. Updated the allocation and context.
Pre-push build found the explanatory guide's current README hash stale;
regenerated only its derived start-data export and updated the guide hash.
All120site tests, syntax checks and static build now pass. Four local QAOA
gradient tests pass with the optional SciPy fit test skipped in this environment.
Retained pending local studies/diagnostic are included in the repository sync;
no new experiment is implied. Fetched a teammate's newer VQE commit and preserve
it during integration. Catering runnable fixtures remain the next foundation
task; no catering solver, remote compute, IBM or VeloxQ usage yet.

## 2026-10-17 — catering activated; foundation then four async methods

The user selected catering to try and requested four asynchronous human
workstreams. Their clarification superseded a component-based split: Codex owns
the common foundation first, then people independently own VeloxQ, QAOA, VQE
(interpreting “qve”) and classical native/SA benchmarks. Authored
docs/CATERING_METHOD_WORKSPLIT.md and docs/CATERING_SOLVER_CONTRACT.md with file
ownership, copyable assignments, immutable fixture tiers, release gates, raw
result contract, coefficient/measurement conventions and centrally held usage caps.
Updated entry points so earlier parked-catering/factory-only guidance is
historical; factory code/evidence/demo remain intact as a fallback.

This creates a concrete handoff contract, not the actual foundation or method
implementations. No human names assigned, subagents launched or messages sent.
No branch/worktree, dependency change, solver job, external compute, quantum/
VeloxQ call, commit or deployment. Documentation/JSON cleanup remains deferred.

## 2026-10-17 — detailed ambitious catering specification

At the user's request, wrote docs/CATERING_AMBITIOUS_SPEC.md as a proposed
implementation contract. It expands the earlier sketch with real disposal
semantics, phase-aware WIP continuations and cooker-failure loss, mandatory
post-repair cleaning, ingredient/holding/power capacities, full QUBO energy and
penalty/scalarization conditions, compact/restricted alternatives, scenario
register accounting, classical/quantum controls, IBM budget, demo and build gates.
Proposed the explicit10:50–11:30 outage to intersect the lunch production window;
the older09:30 timing remains an optional declared sensitivity.

Two self-review passes clarified that mandatory recovery tasks need exactly-one
option groups/cross-option cleaning precedence, and that aggregate capacities
need slack registers rather than only pair conflicts. An unpruned initial-day
capacity example has363slack bits, plus22nominal demand bits, before any options.
This is not a compiled register or a lower bound. Verified local links, bounded
register coverage for128bounds, exhaustive lexicographic order on960tuples,
retained toy counts and shot/register arithmetic; git diff whitespace check passes.
An initial inline verification loop checked scalarization before finishing its
weights; corrected that check and reran successfully. No scheduling implementation,
solver/service call, remote compute, QPU execution, commit or deployment was added.
Factory remains the selected implemented entry; no cleanup was performed.

## 2026-10-17 — four catering cases versus IBM allowance

Mapped nominal/urgent/outage/combined cases to separate direct-register formulas
M_normal+22, M_urgent+26, M_outage+22 and M_both+26 before committing started work.
Full option counts remain uncompiled; only the smaller18/16-bit audit is measured.
Documented that excess production is a waste proxy, not actual measured disposal.
Added a24-circuit four-case shot-budget example to compute notes, explicitly
conditional on compiled timing and circuit construction/quality. No solver,
hardware or external compute job was started; factory main entry unchanged.

## 2026-10-17 — live read-only compute and public quantum allowance check

Verified the local M5 Pro/48 GB hardware and WCSS authentication, Axion account,
CPU/Hopper partitions and eligibility using non-submitting Slurm tests. Bem
128 GB CPU predicted a near-term start; Lem batch CPU/GPU predictions were later.
Interactive sbatch dry tests were refused by the srun-only policy; no allocation
was attempted. Vast.ai read-only listing has no instances; pracus SSH timed out.
The user clarified IBM Quantum, not IQM, as the free-minute provider. Checked
official Open Plan/conditional promotion and usage accounting; actual balance
and backend remain unknown. Saved inventory, limitations and illustrative shot
budget arithmetic in docs/STAGE2_COMPUTE_ACCESS.md. No QPU/VeloxQ/rental/compute
job; the user's queue remains empty. Also restated the catering objective in
conversation while continuing these checks; factory remains selected.

## 2026-10-17 — user compute envelope and reduction priorities

Recorded the user-reported140qubit hardware ceiling and possible H100/128GBRAM
simulation envelope, without treating access as verified or authorizing a job.
Checked official Aer dense-state memory accounting and NVIDIA H100 memory specs.
Documented24–28qubit routine generic simulation, benchmarked30–32stretch cases,
and small18–28qubit initial hardware-compilation targets subject to routing/gates.
Kept broader-model VeloxQ binary variables separate from physical qubits, exact
reductions separate from lossy restrictions, and held all external compute calls.

## 2026-10-17 — catering disruption retained and register accounting clarified

The user clarified that asking for the disruption's rationale did not authorize
dropping it. Recorded that it remains part of the parked catering proposal,
with event timing and committed-state semantics declared before evaluation.
Separated the verified18/16-bit toy counts from the uncompiled flagship and
the unrelated28-qubit factory bridge. Derived the direct option-model accounting:
M+22bits nominal, M'+26with two new urgent-order demand groups, before frozen
boundary substitution. Option counts remain unknown. Documented exact filtering
versus lossy restriction, conditional quantum neighborhoods, and bit/coupler/depth
tradeoffs. No experiments or service calls; main-entry factory decision unchanged.

## 2026-10-17 — factory locked and missing-choice diagnosis

The user chose the factory and asked how to strengthen it. Parked catering and
updated the priorities toward an explainable same-project contribution, bounded
VeloxQ measurements only after quota/authorization, honest hardware feasibility,
and a reliable demonstration/defense. No additional factory mechanisms were added.

Read retained evidence and found a specific counterfactual: an enriched optimal
0/855schedule uses31assignments already in the original pool. Only P02assembly
on A1/W06 at720–780is missing; its H3assignment is already retained. The new
`scripts/explain-recovery-pool-loss.py` compiles the original and augmented pools,
checks membership, encodes/decodes the known witness and verifies literal energy.
The augmented pool has782bits/26357couplers and attains855, matching the retained
complete-model lower bound. Source-sealed evidence is retained separately in
`output/recovery-pool-diagnostic-v1/`. No optimizer, sampling, SDK or network call.

This is deliberately post-hoc, using an already known optimum as a diagnostic
teacher. It is not presented as a new search algorithm, a lossless compression,
or a replacement for the blind2078-bit enrichment experiment. Existing packets
and all prior results stay untouched. This sharper explanation should help the
team defend why a smaller pool lost capacity value without claiming large
encodings are necessary for this one recovered optimum.


## 2026-10-17 — later scope response and catering reassessment

The user supplied a later response described as official, welcoming another
domain when it adds genuine mathematical/algorithmic complexity, value,
originality and correctness. Preserved it alongside the earlier mentor reply
in `docs/STAGE2_MENTOR_FEEDBACK.md`; author/date/permalink are not supplied.
Updated the catering proposal and priorities so manufacturing preference is
not treated as exclusion of other domains.

Reassessed the retained catering evidence without running new experiments:
only18/16-bit fixed-option algebra checks exist, both with optimum tuple
(0,0,0,2). Endogenous batch sizing, demand sharing and freshness provide a
substantive proposed distinction, but full-kitchen correctness, comparative
value and backend performance are unmeasured. The factory remains the stronger
implemented submission; any pivot should first earn stronger offline evidence.
No new solver/API call or VeloxQ usage accompanies this documentation update.

## 2026-10-17 — cluster-entangled VQE pilot: where does entanglement help?

Stage 2 idea from the team: a 2-D grid of problem size against the size and
structure of the entangled qubit "clusters" in a VQE. We first checked a claim
in the idea. With no gates between clusters the state is an exact tensor
product, so it is classically simulable (about sum_c 2^|c| amplitudes), not
unsimulable. We kept the idea and reframed it: simulable by design, which lets
the grid reach sizes beyond a full statevector, and it asks how much
entanglement, and where, scheduling needs.

Added `solver/cluster_vqe.py` (product-of-clusters simulator, real-amplitude
RY/CZ ansatz, adjoint gradients of the mean energy),
`scripts/run-cluster-vqe.py` and `tests/test_cluster_vqe.py` (energy vs
stage1, full-enumeration expectation, adjoint vs finite differences, the 13
optimal Instance B codewords). Go/no-go pilot on Instance B, domain wall,
H=8, 30 qubits, 100 random starts per cell, L-BFGS-B: per-operation clusters
(k<=4) reach an optimal schedule in 13/24/27% of starts at L=1/2/4. No
entanglement gives 4/4/1%, and random clusters of the same sizes 2-3%.
Per-machine and per-job clusters fall in between. Structure, not amount, of
entanglement drives the effect. The run was stopped after 40 minutes, so two
L=4 cells are partial or missing (recorded in the manifest). Results, figure
and limits: `docs/STAGE2_CLUSTER_VQE.md`, `output/cluster-vqe-3x3-v1/`.

Exact noiseless classical simulation only; no QPU or VeloxQ call; no advantage
claim. Next: larger instances with CP-SAT references for the problem-size
axis, and CVaR training with SPSA/COBYLA under shot noise.

AI use: the simulator, tests, experiment and write-up were produced with an AI
assistant at the team's direction. Recorded rows were re-run with the
committed module and matched exactly (70 of 70).

## 2026-10-17 — game-like recovery demo and integrated Stage2 framing

The user preferred the richer game-like factory over the formal workspace and
explicitly authorized combining that style with the verified study. Added a
pure cutaway-scene renderer and selected-pump progress inspector, preserving
actual processing, attendance, availability, all16recipe steps and final
inspection. No AGV execution, shipment or solver improvement is invented.
Guided choices retain the measured45→0→45→0lateness sequence; the original
and enriched replacement pools both retain H3 availability.

Added restart, next-event stepping, replay speed, paused-by-default playback,
focused presentation with Escape exit, unavailable-machine inspection and
recipe-to-operation seeking. Independent review caught replay continuing
across some plan changes and a consumed seek button losing focus. Centralized
pause-on-plan-change and stable focus fallbacks address both. Reduced-motion
support and no-live-chatter playback remain.

The user also clarified that VeloxQ must contribute within Stage2. Checked the
official challenge PDF: Sections5/11/15 support integrated use and end-to-end
comparison. The UI now presents one factory extension with classical references,
local simulated QAOA and prepared larger VeloxQ QUBOs. The sponsor prize is a
separate award, not a separate application; no simultaneous-eligibility claim.
Actual service calls remain held and unmeasured.

The static build passes120site tests, including six new semantic checks.
Desktop browser verification covers recovery choices, actual completion
progress, machine/recipe inspection, replay controls, focused view and current
Stage2 framing. A fresh28-qubit local action returns checked0lateness/855minutes
in0.54seconds, artifact `output/recipe-bridge-live/20261017T123902Z-3797789b`.
The constructor already finds the optimum; this is no advantage claim. Current
UI proof is kept in `output/manufacturing-game-qa-v1/`; historical receipts stay
intact. Mobile visual verification is not claimed. Numerical campaign/model
sources remain unchanged. Authorized private sync/site deployment continues;
Markdown/JSON cleanup, final video and public-source submission stay deferred.


## 2026-10-17 — authorized repository sync and lossless evidence packaging

The user requested committing and pushing all current work to the existing
private remote. This authorizes the configured automatic site deployment;
repository visibility, actual VeloxQ/QPU use and final submission remain held.
Three newer remote tutorial commits are preserved during integration.

Four development JSON files exceed GitHub's100MiB limit. They are retained
locally, represented in Git by deterministic gzip assets and a size/SHA-256
index, and restored by a Node-only pretest hook. This preserves literal bytes
and fresh-clone build inputs without network downloads. Earlier release assets
retain their existing restoration path. The user explicitly deferred Markdown
and JSON cleanup: no pruning or consolidation is part of this sync.

## 2026-10-17 — mathematical specification and manufacturing workspace refinement

The user emphasized verified merit and readable mathematics, then requested that
the UI meet the same standard. Added the independently reviewed main-model
`docs/STAGE2_MANUFACTURING_MATH.md`: raw domains/constraints, complete polynomial,
coefficient conventions, integer hierarchy, represented-witness penalty proof,
exact/lossy reductions, unit-deadline query and restricted quantum bridge.
Fifteen display equations,79inline expressions and31local links were checked.
No compiler correctness issue was found; actual measured advantage is not inferred.

Rebuilt the manufacturing page around a dark story rail, clear outcome and shop
floor, with separate recipe/timeline, model/results and questions views. The
math walkthrough ties a selected assignment to the objective and penalties.
Independent source review found and root fixed five UI defects: SVG keyboard
activation, focus loss after redraw, focus/status hidden by panel switches,
misplaced nominal comparison and processing-duration worker ghost bars.
Story semantic tests check the four actual retained0/45late schedule choices.
A full build passes114site tests and syntax checks. A stale hash in the older
Start guide was refreshed by its read-only exporter; frozen evidence stays intact.

The preview server now handles idle preconnections concurrently. After a browser
policy block was resolved by the user loading the HTTP preview, desktop review
checked story outcomes, keyboard selection/focus, tabs, nominal People comparison,
math rendering and a fresh local QAOA action. That28-qubit run returns checked
0weighted lateness/855-minute completion in1.43seconds, with a visible result
notice and timestamped artifact `output/recipe-bridge-live/20261017T121949Z-1a0a57ab`.
No browser warning/error logs. Mobile visual verification is not claimed.
Original pending-review workspace-v1sources remain a separate snapshot; current
browser evidence is in `output/manufacturing-workspace-qa-v1/`.

Actual VeloxQ, physical QPU, final video, publication and submission remain held
or deferred as recorded; no remote call, upload, commit, push or deploy occurs.

## 2026-10-17 — technical acceptance closeout and current documentation

The final strict acceptance snapshot, `output/merit-audit-final-v1/requirements.json`,
passes all 14 agreed non-VeloxQ core requirements with no incomplete core items.
The final implementation receipt records 52 targeted Python tests, 113 site
tests, syntax checks and a successful static build, with 269 source hashes.
Independent consistency-v2 checks 20 conditions, 34 files and 116 local links,
including the actual fresh 28-qubit artifact and complete raw 32-operation plan:
zero weighted lateness / 855-minute completion. These are dated snapshots.

The user then requested a documentation update. Added [current status](docs/STAGE2_STATUS.md)
and aligned README, context, design, combined plan, submission preparation and
implementation/earlier-explanation entrypoints with this closeout. Historical
pause, separate small-cell results and failed experiments remain scoped.
Documentation verification is refreshed in a new output directory rather than
rewriting any historical numerical or test receipt. No implementation or UI
behavior changes accompany this update, so model tests are not rerun.

Actual VeloxQ execution remains held. The final synchronized video, human live
rehearsal and public release/submission remain open; technical acceptance does
not imply these are complete. No service use, paid compute, new optimization,
commit, push, upload, deployment, publication or submission occurs in this update.

## 2026-10-17 — independent review passes and new formulation experiments

- Review closeout:19new tests pass. Expanded cold controls completed40runs with
  640returned bitstrings in54.04seconds. A separate reporting-only audit
  independently checks physical operation plans apart from completion-register
  validity:0encoded-valid,0physically-valid and0target. Original manifests and
  all input hashes verify; no resampling was needed for the reporting correction.
- Both declared boundary-release gates fail before quantum sampling:12freed
  operations leave98/60candidate bits and an empty mandatory domain. This is not
  proof every small block is impossible. At this point the larger-case quantum
  connection remained unresolved; the later whole-recipe bridge entry below
  resolves integration using a different representation. Full review and revised priorities are in
  `docs/STAGE2_REVIEW_PASSES.md`; no VeloxQ run, credits or publication occurred.

- User explicitly requested multiple subagent passes. Three reviewers challenged
  rubric integration, VeloxQ relevance and technical validity, then reviewed the
  resulting experiments. Their strongest objection was that a weak candidate
  pool does not prove the complete QUBO is necessary.
- Implemented deterministic nested mode/time enrichment with all original rows
  retained, no CP-plan teacher and saved pools before references. All ten pool
  references prove OPTIMAL. Replacement cap64 recovers0 tardiness/855min with
  2,078bits/196,228couplers; smaller tested caps stay45late. Saved evidence in
  `output/capacity-frontier-review-v1/` and `docs/STAGE2_CAPACITY_FRONTIER.md`.
- Implemented exact hard-terminal-deadline/cap QUBO with unit feasibility
  penalties, no makespan register and explicit pair/coupler guards. Independent
  raw CP reference preserves original calendars/horizon. Replacement query is
  818bits/33,817couplers; cap855 is feasible,854 infeasible; outage900 infeasible.
  Eleven deadline tests cover tiny exhaustive energies, pruning, richer resource
  rules, query hashes, guard semantics and unresolved native solves.
- `docs/STAGE2_DEADLINE_DECISION.md` records exact scope and study. Pure
  feasibility does not optimize the original secondary objective; positive-energy
  sampler returns do not prove infeasibility. No remote backend, SDK credentials,
  publication or credit use occurred. Expanded local controls and the same-model
  quantum headroom gates are complete with the negative outcomes recorded above.

## 2026-10-17 — complete-recipe recovery study and production studio

- Promoted complete16-operation pump recipes to the application centerpiece; retained the small QAOA fixture as a separately scoped validation microscope. Added `docs/STAGE2_MANUFACTURING_STUDY.md` alongside implementation.
- Ran nine manufacturing cases, then a separate due-date-matched recovery-v2 pair. Complete native CP certifies45→0 weighted late minutes with replacement heat capacity; the restricted-pool optima both remain45. Compiled complete recovery QUBOs with2,353/2,499 variables and343,682/381,371 couplers. Saved source snapshots and inputs distinguish old due dates.
- Added checked-incumbent penalty proof and60 CPU annealing controls on saved study-v1 models. No returned improvement over heuristic incumbents; tightened penalty yields1/240 feasible reads versus21/240 for the original bound at these settings. Retained the negative evidence; this is not a VeloxQ prediction.
- Built the saved-plan production studio, linking worker attendance, full recipes, actual Gantts, counterfactuals, domain loss and honest scaling bounds. Browser checks passed for outage/replacement, restricted-pool loss, worker lanes,128-operation UNKNOWN and no console errors. Six larger model inputs / twelve HDF5 files passed6,301,798 independent coefficient checks;37 plans and480 annealing samples rechecked. Three manufacturing Python tests and110 site tests/build passed. Added a gated backend runbook. Completed the recovery-centered161.9493-second local video review cut in `output/manufacturing-video-v3/`, with actual captures, disclosed synthetic narration and source-hash receipt. Sampled encoded video frame inspected; no upload or submission. No remote service/QPU, credits, publication or deployment.

## 2026-10-17 — combined direction and QOBLIB assessment

- User emphasized competing for the VeloxQ prize with a workload the solver can
  actually handle well. Added a sponsor-priority pilot ladder to the combined
  direction: known-target full recovery, growing backlogs/windows, strong native
  CP and identical-QUBO controls, feasibility/quality/time/cost/diversity metrics.
  Measured the saved recovery graph as12.22% dense with mean degree305.22;
  sparse storage alone is not the sparse-topology promise of published tests.
  Local tiny-budget annealing failures motivate testing, not a performance claim.
  The existing remote-use hold remains; no VeloxQ call was made.

- User authorized combining iwos, kari and iwow, then asked for ongoing
  documentation. Added `docs/STAGE2_COMBINED_DIRECTION.md`; the other active
  instance continues to own manufacturing implementation and visualization.
- Centered the synthesis on saved recovery-v2 evidence: complete native CP
  weighted tardiness 45→0 with replacement heat capacity, while this restricted
  candidate pool remains at45. Freshly replayed the four raw/pool schedules with
  the source-matched checker and verified objectives/input hashes. The audit is
  `output/combined-direction-20261017/evidence.json`; no new optimizer ran.
- Kept older study-v1 due dates distinct, small QAOA separate from full-recipe
  results, and proposed economic sensitivity separate from calibrated ROI.
- Read QOBLIB's official site, participation guidance and MIS family. Recommend
  its reporting discipline now and optional predeclared external solver controls
  after the main manufacturing evidence is secure. Its current ten-family list
  has no manufacturing job-shop family. No benchmark run or external submission
  was performed; remote-backend and publication holds remain.

## 2026-10-17 — manufacturing entry refinement and complete assignment mixer

- Closeout: five new assignment/circuit tests and twenty existing window-model
  regression tests pass. The site build passes all107 browser-model tests;
  syntax checks now include the new entry app. The final retained claim audit
  is `output/stage2-entry-claim-audit-v3.json`. Independent coefficient equality
  checks274,653 values across the nine final SDK files, covering every state.
- The supplied mentor reply is personal preference pending further jury
  consultation; it reinforces staying in manufacturing and is not quoted as
  a formal ban. No message was sent to the mentor/private channel.
- Credential wording correction: earlier receipts counted only the preparer's
  explicit token lookups, overlooking the SDK's import-time environment lookup.
  No credential was displayed or used in a request. The final v4 preparer forces
  an empty process-local token before import without reading its previous value.
  Parent environment/configuration is unchanged. Earlier receipts are retained
  with that narrower interpretation; no service request or credit use occurred.
- A local173.217366-second H.264/AAC review draft is prepared in
  `output/stage2-entry-video-v6/`, using real UI captures plus timestamped
  before/after frames of an actual fresh button action. Synthetic Daniel
  narration and editing are disclosed; this is not a continuous recording of
  the entire presentation. A transcript and hashes accompany it. Human review,
  upload and actual live delivery remain separate.

- User resumed Stage 2 implementation after the explanation pause and reported
  organizer advice to remain in manufacturing. Kept the pump domain. Replaced
  catering as the active direction; its proposal remains historical research.
- The existing full-factory study stays frozen. Built an explicitly synthetic,
  complete residual cell: final housing/rotor machining, assembly join, pump QA
  and an urgent QA order, with shared people, alternative machines, a calendar
  outage and due-date priorities. It is not a trace-extracted factory state.
- Implemented W preparation and ordered XY mixing for every operation assignment
  group and makespan group. This removes the earlier proposal-pool restriction
  within the declared cell. It does not preserve all resource constraints or
  encode the rich factory losslessly. Simulation enumerates the one-hot sector
  classically and retains the full logical-qubit register.
- Saved protocol/source snapshots before TRAIN/TEST. TRAIN seeds 7/13/29 select
  p=2/CVaR .25; ten TEST seeds per six cases test fresh optimizer/sampling
  randomness on those same instances. QAOA: 60/60 valid optimal actual schedules,
  57/60 exact encoded minima. Three makespan registers are 30 too large;
  operation plans are unchanged. SA: 60/60 of both. Uniform: 59/60 optimal plans,
  52/60 minima. Unequal evaluation budgets and all classical costs are disclosed.
- `output/stage2-entry-v1/` retains a duplicate-keyword reporting failure; v2
  fixes reporting without retuning the algorithm. Completed v2 campaign takes
  11.980 wall / 11.838 CPU seconds on this host. No hardware timing claim.
- Qiskit independently replays the emitted 18-qubit circuit: maximum probability
  error 1.0062e-15. Larger circuits are parsed/transpiled only. The 34-qubit
  circuit has 852 logical CX and depth 322, including preparation; no routing.
- Capacity ablations change the reference objective 120→11,010. Without a spare
  during outage, the pump is 30 minutes late. Without cross-training, the
  selected optimum instead delays urgent inspection by 60. This is a synthetic
  scheduling counterfactual, not measured purchase ROI.
- Prepared nine actual SDK-format VeloxQ files without a token or network call.
  The first packet attempt found missing OR-Tools in the SDK environment;
  references now run separately with problem hashes checked. The next attempt
  caught an actual float32 serialization energy mismatch. Exact ×4 integer
  Hamiltonian scaling preserves quarter-integral coefficients and all 576 final
  round-trip checks pass. Failed directories are retained. SDK 1.0.0 backend
  acceptance/internal precision remain unverified. Largest packet: 1,602
  variables / 118,889 couplers; its native CP reference is separately optimal.
- Built the local jury view `/entry/` and a loopback Python action that actually
  recomputes QAOA and a native CP reference. Browser verification confirms a new
  timestamped result/QASM/manifest and the no-spare ablation. Saved evidence is
  labeled separately. The static build includes no Python service.
- Added the authoritative `docs/STAGE2_ENTRY.md`, root Design/README links and
  `scripts/verify-stage2-entry.py`. The audit checks 386 file hashes, independently
  redecodes all 180 TEST outputs, confirms winners were actually sampled and
  checks display totals against the retained source. An old guide hash correctly
  failed after README changed; its generated reference is refreshed, rather
  than removing the check. No frozen factory export is rewritten.
- VeloxQ service calls, token reads, uploads, credit use and physical QPU calls
  remain zero. Stage 2 commit/push/deploy/publication hold remains in force.
  Video review/upload, public MIT release, team declaration, form submission and
  human live rehearsal are separate completion duties, not inferred from tests.

## 2026-10-17 — Stage 2 implementation and ongoing research

- Implemented the full minute-resolution two-hall factory and independent
  physical replay under `stage2/`, preserving the original Stage 1 artifacts.
- Added matched classical and quantum-simulator dispatch experiments, learning
  and scenario-lookahead controls, physical flow heuristics and scoped exact
  deterministic references. Failures and restrictions are retained explicitly.
- The separate Stage 2 viewer imports checked traces and labeled research
  cohorts. Development selection does not imply final reliability or a global
  factory optimum. Unfinished-order cutoff debt is separate from delivered-only
  tardiness.
- Actual evidence, immutable sources and resource accounting are in
  `output/stage2-search/`; the detailed live record is
  `docs/STAGE2_EXPERIMENT_LOG.md`. The current implementation entry point is
  `stage2/README.md`. Earlier entries below describe the state at their time.
- The user stopped ODRA/VPN work; bounded CPU experiments and local quantum
  simulation continue. No VeloxQ calls, physical quantum runs or new publication
  are claimed. Reserved final tapes have not yet been executed.

## 2026-10-16 — requirements and access

- Captured the organizer's opening slides and checked the transcription. The user emphasized that both baseline solutions must be demonstrated for eligibility.
- Connected/verified the existing GitHub remote and pushed the initial shared context snapshot as `1123ff4`, following the user's explicit instruction. Subsequent work is local until published.
- Verified WCSS SSH authentication and Axion quantum Unix group membership. Slurm did not list a corresponding allocation; a test-only request using the group name as an account was rejected. No compute job was submitted and no account default was changed.
- Read both supplied PDFs in full, visually checked the instance tables and extension requirements, and reconciled the context. Important clarification: Instance A requires a QUBO solved using a quantum algorithm; baseline output times are integer hours.

## 2026-10-16 — presentation environment

- User requested visually engaging results and specified a clear Factorio/Stardew Valley-inspired scene. Chose original SVG pixel art with machine mechanisms, a conveyor, parts, and a small landscape; kept analysis and controls readable outside the scene.
- Built a local-only, buildless browser application with Node's standard library server. This avoids a framework/dependency setup for a presentation shell and keeps it easy to run and record offline.
- Added 3×3/2×2 illustrations, time replay, selection, linked Gantt chart, evidence view, playback speed, presentation layout, and JSON import/export. The 9-hour alternative was manually authored for comparison, not obtained through a solver experiment.
- Kept illustrations separate from actual result claims. No completed baseline JSON outputs or solver-run evidence have been fabricated.
- Implemented independent checks against operation requirements: coverage, duration, machine capacity, and precedence. The official-output adapter also checks the declared makespan and requires integer hours.
- Added the exact official input JSON files. Tests compare fixture operation data to these inputs.
- Caught and corrected a visual bug during browser review: an SVG tile path had an implicit black fill, obscuring the factory floor. Explicitly removed the fill.
- Verified timeline selection seeks to the operation's start and updates the selected part route and completion count. Checked the evidence view's feasibility/source labels.
- Browser checks also confirmed 2×2/3×3 switching, 2×2 replay completion at 4 hours, and import of a temporary official-format illustration with unverified method provenance. The test fixture remained in ignored `tmp/`, not among final baseline outputs.
- Ten automated tests passed, as did JavaScript syntax checks. These verify the presentation/checker, not quantum execution.
- Tests and syntax checks are recorded in the task's final report after the final changes; they establish display/checker behavior, not quantum solver success.

## Decisions and rejected directions

- Rejected presenting an SDK call alone as satisfying both instances: the 2×2 needs a genuine quantum algorithm run.
- Rejected replacing failed solver output with a classical answer while calling it a solver success. Classical reference results and solver-produced schedules will have separate provenance.
- Kept transport cosmetic because the official baseline has no travel-time constraint.
- Chose a shared display contract plus an official-JSON adapter instead of coupling the frontend to VeloxQ credentials or SDK objects. API tokens must stay outside the browser and repository.
- Deferred extended-model UI claims until the chosen constraints are actually modeled and solved. Rich visuals cannot substitute for Stage 2 substance.

## Current status

Visual cleanup passes on 2026-10-16: removed the introductory slogans, stage eyebrow, repeated instructions, redundant passing-check descriptions, and footer tagline. Replaced the temporary asterisk with the unchanged Axion logo from the user's `axion2.0` site, bundled its typefaces/licenses locally, and revised the Gantt to neutral bars with semantic job markers and a legible dark selection. Factory, selected-chart, and Validation states were inspected in the browser. No scheduling algorithm or data was changed by these passes.

The presentation environment and both local required-method baseline runs are implemented and checked: quantum QAOA simulation for A, classical QUBO annealing for B. Actual root schedule outputs have makespans 4 h and 8 h, independently verified optimal. VeloxQ service use is explicitly on hold at the user's direction; no remote VeloxQ or physical ODRA5 result is claimed. Stage 2 has the working proposal recorded below, rather than an implemented model.

## 2026-10-16 — offline Stage 1 preparation without VeloxQ access

- User asked whether implementation could start without the API. Built a standard-library Python preparation pipeline; it performs no service calls and needs no new packages.
- Implemented integer start windows, exactly-one/capacity/precedence QUBO penalties, coefficient export, sample decoding, and an independent interval checker. All weights are one for fixed-horizon feasibility; zero energy means feasibility. Minimizing makespan remains an outer search.
- Reproduced 39 variables at H=8 for B, using ordinary window pruning. A has 8 at H=4. These are not novel/minimal encoding claims.
- Independently enumerated all machine orders (including non-permutation combinations): optima are 4 h and 8 h. Both references round-trip through their QUBOs with zero energy. Wrote clearly labeled reference artifacts rather than final required-method submission files.
- Verified every bitstring of the 2×2 QUBO at H=3 and H=4 against independent schedule feasibility. Added 1,000 deterministic 3×3 one-start-per-operation samples comparing QUBO energy with direct constraint-violation counts, reference checks, and corrupt-schedule rejection.
- Prepared a lazy optional dimod BINARY BQM conversion for the SDK boundary. Conversion and remote integration remain untested here. The official SDK README confirms token-based remote sampling; backend behavior still needs real service verification.
- AI assistance included the offline formulation implementation, reference enumerator, tests and explanatory notes. Team review and understanding remain required. No QAOA/VeloxQ result is claimed.

## 2026-10-16 — baseline/methods literature review and tutorial

- Ran a targeted literature sweep (OpenAlex keyword/title queries plus one backward/forward citation step from seven seed papers) focused on the Stage 1 formulation and the methods we might use. Result: `literature/BASELINE_METHODS_REVIEW.md` (52 DOI-resolved references) and `literature/reading_list.csv`, complementing the existing Stage 2 guide.
- Main conclusions recorded there: our time-indexed QUBO with window pruning and an outer horizon search is the standard Venturelli et al. (2015) formulation, ported to QAOA by Kurowski et al. (2023); differentiation must come from encoding size, constraint-aware QAOA, and a hybrid (LNS-style) extension where VeloxQ solves residual QUBOs. VeloxQ is a classical, quantum-inspired solver and must be described that way.
- Extended `literature/sources.json` with a `baseline-methods` collection and generalised the README generator in `fetch_papers.py`; 19 new open PDFs (arXiv versions) were added. Publisher-hosted PDFs outside arXiv could not be fetched from that environment and remain link-only; Stage 2 manifest records keep their original retrieval data.
- Added `docs/METHODS_TUTORIAL.html`. Its numbers come from `solver/stage1.py` models and a small exact statevector QAOA simulation (COBYLA, 20 restarts): at H=4 exactly 1 of 256 one-hot bitstrings has zero energy; at p=3 the domain-wall model reaches P(optimal)=0.886, matching the committed QAOA run's 0.888 feasible-shot rate; one-hot with an X mixer reaches only 0.113, while an XY mixer recovers the domain-wall result. Also documented a lower-bound proof that 8 h is optimal for Instance B (T load 5 h + min(F+S) 3 h).
- AI assistance: the literature search, synthesis, simulations and tutorial were prepared with an AI research assistant. Claims summarise abstracts; team members should read the key PDFs before the defense.

## 2026-10-16 — ambitious Stage 2 environment ideation

- User directed us to start with the most complex coherent/explainable factory we can formulate and consider simplification only after actual difficulties. Preserved that mandate; small audit cases are for correctness, not a reduced target.
- Re-read the full ERP challenge text and visually checked its Stage 2 requirements page. Reviewed the existing display model and its two/three-machine, common-route limitations.
- Developed eight design/critique iterations in `docs/STAGE2_IDEATION.md`: compared flexible-shop, recovery, energy, supply-network, investment and adversarial ideas, then integrated the strongest interactions into a two-hall pump factory.
- Wrote `docs/STAGE2_ENVIRONMENT.md`: BOM joins, batches, alternative machines/modes, family setups, physical AGV movement, finite buffers/blocking, people/tooling/wear, energy/batteries, quality/rework, hidden observations, WIP replanning, investment counterfactuals, objective priorities, evidence and a staged research program.
- Identified correctness traps: setup depends on immediate predecessor; quality revelations occur at decision-dependent inspection completion; per-scenario perfect foresight is not an executable policy; free optional capacity cannot worsen the true optimum; physical feasibility and order fulfillment are separate outcomes.
- Proposed conceptual exact finite-state flow and practical restricted recovery QUBOs. Did not claim compactness, full-model equivalence, solver advantage or a completed formulation. Neighborhood resource/state closure and full trace replay remain required work.
- Added synthetic blueprint parameters and a standard-library expansion/audit script. Generated `output/stage2-design/expanded-design.json` and `audit.json`: 24 known orders, 72 component lots, 384 nominal operations, 15 machines, 10 workers, 4 AGVs, 8 exogenous leaves with exact probability sum 1, and 1,752 nominal machine/mode alternatives.
- Counted 665,760 manufacturing-start choices after only duration-window trimming (672,768 all-tick ceiling). This partial count excludes joint batches, logistics, setups, rework, scenario copies, slack and other state; it is not a complete QUBO/qubit count.
- Kept missing tables and reachable-snapshot generation explicit. The blueprint audits structure only and provides no dynamic feasibility, fulfillment, solver result or new browser implementation.
- Validation: blueprint expansion succeeded; the ten existing viewer tests and JavaScript syntax checks passed. Independent checks confirmed per-order three-component assembly joins, operation totals, all eight scenario histories, repeatable expansion and stored-artifact agreement. Seven deliberate corruptions were rejected: bad probability mass, duplicate machine, missing capability, negative duration, event before reveal, terminal battery depletion and unknown outage machine. These establish structural behavior only, not physical feasibility.

## 2026-10-16 — Stage 1 executions, iteration and hardware preparation

- Built pinned, separate solver and IQM environments. The verified simulator uses Qiskit 2.5.2; IQM client 35.0.3 resolves Qiskit 2.1.2, so it stays separate. Full dependency lockfiles are included.
- Ran genuine four-qubit QAOA circuits and Aer measurement sampling for A, optimizing mean QUBO energy without using the classical reference to choose an answer. Compared p=3/p=5, longer COBYLA runs and BFGS. Seed-2026 measured feasibility progressed from 88.77% (p=3 COBYLA) to 91.24% (more COBYLA), 95.41% (p=5 COBYLA), 95.65% (p=3 BFGS), and 99.61% (p=5 BFGS). The final selected run has 4,080 feasible shots out of 4,096 and makespan 4 h. Two further p=5/BFGS seeds yielded about 98.12% and 98.54%; the best single run is not a universal rate.
- Solved the actual 39-variable B QUBO by local simulated annealing with random initialization, not a reference warm start. The selected run gives makespan 8 h and 491/512 feasible samples. Both accepted schedules match independent exact optima. Root official-format schedules are exported; circuit, raw counts, samples, model coefficients, settings, hashes, versions and replays are retained under output/stage1-ready/.
- Added a domain-wall option: A shrinks from 8 to 4 variables and B from 39 to 30, preserving every start assignment at the horizon. Review caught an invalid-wall algebra pitfall: substituting a binary-simplified exactly-one polynomial permits indicators -1 where x²=x fails. Removed that polynomial before substitution and added an incident-degree penalty proof. For B the safe wall weight is 10. Added exhaustive invalid-wall checks for small instances with multiple internal walls. Earlier experimental compact packets are explicitly superseded.
- Exhausted all 512,000 one-start-per-operation assignments for B at H=8. The one-hot model, corrected compact model and direct interval constraints agree on energy throughout; 13 assignments are feasible. This is not enumeration of every arbitrary 30/39-bit state.
- After the correction, ten annealing seeds at H=8 each found an optimum for both encodings. Mean feasible-sample rates were 95.08% (39-variable one-hot) and 91.88% (30-variable domain-wall), at 256 reads × 2,000 sweeps per seed. One-hot remains the initial VeloxQ candidate; local timings/rates are not remote performance claims. H=7 produced no feasible sample, consistent with the separate exact reference proof, not itself a proof of infeasibility.
- Tested actual SDK HDF5 serialization and result parsing without service calls. Review caught dimod's bulk-constructor variable ordering; adding variables before edges now fixes canonical wire order. Tests cover shuffled string labels, spin/binary conversion, full and constant-omitted energies, failures/timeouts and default CLI network isolation. The remote runner records a job id immediately and resumes retrieval without repeating submission.
- Added the complete local preparation command, fail-closed evidence verification/export, source hashes and independent browser validation of the actual artifacts. Eighteen Python tests pass in the IQM environment; twelve Node tests and the viewer build pass. Upstream SDK Pydantic deprecation notices remain non-failing.
- User requested physical ODRA5 execution and authorized the existing Axion e-science/SSH/VPN route plus personal token generation if needed. Verified the SSH login, active Axion quantum service and actual Axion CPU association hpc-iwowoj-1781179048. A short interactive CPU network check reached the real ODRA5 service from r31c03b03 and received HTTP 401; the login host instead redirects to e-science. The network-check allocation ended cleanly and no QPU job was submitted.
- WCSS's current manual requires IQM client 35.0.3 and a personal API token even from SSH. No token was configured in either checked environment. The user's e-science browser sign-in succeeded, while the ODRA5 dashboard still redirected from the local browser. Token creation/access remains unresolved; do not claim SSH authentication alone grants IQM API access.
- Prepared native IQM star compilation with classical-measurement probability checks and physical-ancilla marginalization. Circuit copying can reorder Qiskit's qubit list; the verification now resolves retained qubit objects after removing measurements. Proxy p=1 uses 11 CZ/depth 22; p=5 uses 67 CZ/depth 123. Local Adonis-noise rates around 19.8% and 19.1% at 1,024 shots are illustrative proxy results, not real ODRA5 calibration or performance. A shallow first hardware batch is appropriate once authenticated.
- User received VeloxQ onboarding and reports exporting VELOX_TOKEN, but explicitly says DO NOT use it yet. No quick test, connectivity request, upload or remote job has been made. Keep the key private and outside code/logs/commits; wait for explicit authorization before any service use.
- Completed the additional p=3 native/noise proxy: 39 CZ gates, depth 73, 317/1,024 feasible measurements (30.96%). It is a better proxy compromise than the tested p=1/p=5 candidates; real device calibration may change that conclusion. Retained all proxy runs separately.
- Copied a token-free p=3 client bundle to ~/qhackathon26-stage1 on WCSS and installed/verified its dedicated Python 3.12.13, IQM 35.0.3 environment in an Axion CPU session. The uploaded source QAOA evidence passed verification there. Both short client/network-check allocations ended; there is no queued hardware job or lingering allocation from this work.
- User authorized personal IQM token creation if no existing token can be found. Creation could not yet be reached: the ODRA5 dashboard redirects to e-science on the local browser even after successful e-science sign-in. Requested a working VPN-KDM dashboard route; no credential was invented, printed or committed. The SSH client itself is ready.

## 2026-10-16 — Offline Stage 1 refinement; both remote backends on hold

User stopped ODRA5 work and retained the VeloxQ hold. Screened eighteen configurations (three seeds each), then validated selected QAOA/annealing settings on ten new seeds each, with network connections blocked inside experiment workers. Independent-X QAOA p=3 achieved 40,960/40,960 valid measured shots, using 12 RZZ cost gates instead of 20 in the prior p=5 circuit. Linear classical QUBO annealing at 32,000 sweeps achieved 5,110/5,120 valid samples. All runs returned optimal 4 h / 8 h schedules. No quantum advantage, unseen-instance generalization or physical-device claim is made.

Fresh seed-2026 exports and selection manifest point to output/stage1-local-ready/. Earlier evidence is preserved. Added reconstruction of saved quantum expectations and raw-count consistency to the verifier; tampering is rejected. Default preparation excludes both remote adapters and SDK packets. Full evidence, tradeoffs, settings and reproduction are in docs/STAGE1_REFINEMENT.md. Optimizer traces in the experiment archive are losslessly compressed. No commit, push, submission or external solver call was made.

## 2026-10-16 — Factory world, Stage 1 field manual and release preparation

- Converted the viewport into the factory world, with wooden HUD controls and parchment Timeline/Validation menus. Preserved replay synchronization, selection, imports and explicit illustration provenance.
- Added `/problem-explanation`: six chapters covering official inputs/rules, interactive schedule calculation, optimum proofs, fixed-horizon QUBO, encodings, actual solvers and complexity. Checked the compact four-bit energy against every assignment and independently validated each illustrated permutation schedule.
- Initially placed the guide in the footer; user found it hard to discover. Added it to the primary navigation beside Factory world and Control desk. Verified navigation on desktop and a 390-pixel phone viewport.
- Updated the guide from the old p=5/2,000-sweep evidence to the selected independent-X p=3 and 32,000-sweep runs. Added a public evidence summary and a test against the current selection manifest to detect drift.
- Reviewed README, Project Design, presentation design, readiness/compliance notes, changelog and context before committing, following the user’s standing request to update docs before every commit and push. Historical experiment entries above describe the state at their original dates; the selection manifest identifies the current outputs.
- Release checks: 16 Node tests/build, 19 core Python tests, and 2 optional IQM compilation tests in the dedicated environment. Both selected schedules pass reconstruction/independent verification. Credential scan found no secrets in candidate files or their compressed archives. Both external solver holds remain unchanged.
- Preserved the two newer literature/tutorial commits from GitHub main while resolving README and Development Log append conflicts; both sets of documentation remain in the release. The web deployment contains only presentation assets, while source, solver evidence and documentation are published in the repository.

- After integration, updated the imported methods tutorial and baseline literature review to distinguish their historical shared-X/XY experiments from the currently selected independent-X run. Preserved the original comparison results and linked the current selection/refinement evidence.

## 2026-10-16 — Preserve the concurrent tutorial update before publishing

A further GitHub tutorial commit arrived after release preparation. Integrated its expanded from-scratch QUBO derivation while retaining the release’s current-evidence note and updated source pointers. Built and checked an isolated committed checkout so the concurrently edited visual variants are excluded, as the user explicitly requested. Documentation remains updated before the integration commit and push.

## 2026-10-16 — Ten pixel-game visual variants

Added ten reversible art directions to the live factory, with distinct palettes,
landmarks, UI materials and desktop HUD arrangements. Kept the original as a
reference and shared the schedule/selection/clock between directions. Added a
movable, keyboard-positionable, collapsible picker; an all-ten overview; larger
previews; a favorite comparison; browser-local saved selection/favorite/position;
and URL selection. Preview frames stop on close and do not run replay frame loops.

Checked all ten rendered directions, the overview and two-way comparison, favorite
selection/removal, original restoration, picker dragging and keyboard movement,
rebuilding the two-machine scene, preserved time after theme changes, the Timeline
and Validation desk, and the 390-pixel phone layout. Corrected inherited theme
variables, improved machine shade detail and dark desk contrast, and made the phone
picker start collapsed. The 1280×720 overview fits all ten choices without internal
scrolling. The existing 16 Node tests and expanded syntax checks pass. This is local
viewer work; no deployment, commit, push or external solver call was performed.

## 2026-10-16 — Explain where the QUBO matrix comes from

User asked how we obtain the matrix. Expanded chapter 03 of the Stage 1 guide with the path from processing durations to start variables, penalty expansion, coefficient collection and matrix storage. Added the actual 8-by-8 A model, staged exactly-once/capacity/precedence accumulation, inspectable coefficient provenance, the separate constant and triangular/symmetric conventions. Showed the compact 4-by-4 substitution and distinguished Q from the quantum cost operator.

The teaching builder computes entries from the official durations and interval conflicts; tests match all coefficients and all 256 energies against the actual Python-generated model, including symmetric half-coefficients. The 18 Node tests and static build pass. Relevant README, changelog, presentation design and formulation notes were updated. This addition is local; no commit, push, deployment or external solver call was made.

## 2026-10-16 — Refine Lunar, Frostline and Blueprint; archive other directions

The user selected Lunar Assembly, Frostline Works and Blueprint Bureau for further
iteration and asked to remove the other seven from comparison. Preserved the first
variant definitions and styling in docs/design-archive/2026-10-16-first-variants/.
That directory is outside the shipped presentation. The runtime registry, selector,
keyboard cycle and gallery now contain exactly three options; retired URLs fall
back to Lunar and retired favorites are cleared.

Refined Lunar's ceramic HUD, deck materials, craters and outpost equipment. Gave
Frostline a snow-covered conifer perimeter, warm lamps/active-work accents and a
subtly warmer interior floor. Replaced Blueprint's universal wireframe treatment
and crossed placeholder scenery with solid shaded machines, a quiet ink grid and
sparse floor dimensions. Kept job colors/identifiers stable, refined navigation,
control-desk contrast and invalid-state treatments, and preserved replay semantics.
The art picker now remembers separate factory/desk and desktop/phone positions so
a saved position does not cover the desk header. The hosting frame policy allows
same-origin comparison previews while continuing to block embedding by other origins.

Visual checks covered all three full-size factory views, the three-way gallery,
favorite comparison, Lunar Timeline/Validation, Frostline's 390-pixel phone view
and the phone gallery. Interaction checks covered state preservation at 2.0 h with
Z1 selected after a two-machine replay rebuild, the three-option selector, retired
URL fallback, favorite selection/removal, and separate desk placement. Corrected a
selector-specificity issue in active-navigation colors and a thumbnail aspect-ratio
issue discovered in the phone pass. Existing model/manual checks and syntax checks
pass. No deployment, commit, push, Stage 2 simulation or external solver call.

## 2026-10-16 — Distinguish QUBO and quantum-operator dimensions

User asked whether a 2^n-by-2^n matrix appears. Checked `solver/quantum.py`: it constructs a 2^B-entry cost diagonal, computes statevector probabilities from local gates, and takes their dot product. It does not explicitly construct the dense whole-register operator. Added dimensions for x, Q, cost/unitary operators, state/probability/cost vectors and local gates, plus each actual Stage 1 encoding. Explained O(4^B) dense-operator storage versus O(2^B) statevector storage, the local B<=12 guard, and that B's classical annealer uses no quantum state. Updated the formulation notes alongside the local guide.

## 2026-10-16 — Lock Lunar and publish the completed viewer/guide

User selected direction 1 / Lunar Assembly and requested a docs-first commit/push.
Archived refined Frostline/Blueprint source, integration and preview references
under docs/design-archive/2026-10-16-refined-shortlist/. Removed live comparison,
favorites and style switching. Shared fixed lunar.js/lunar.css now cover factory,
control desk, guide and error page; old comparison URL parameters are removed.
The guide's actual 8×8 matrix, coefficient stages, conventions, compact example
and dimension explanations remain functional. Fixed low-contrast guide labels
found by the accessibility audit. Restored frame-ancestors 'none' after removing
comparison iframes. Version stays 0.1.0 for the existing same-day private web app.

The user clarified: push completed Lunar + guide now, keep new Stage 2 work local.
The release uses an isolated checkout from origin/main, preserving eight newer
methods-tutorial commits through 0c5fe1e. Concurrent Stage 2 source/tests are not
copied, edited or staged. The pre-existing hardware-access artifact update is
retained as recorded evidence; no new remote-compute verification is claimed.

Checks: 18 Node tests and syntax/build checks; 8 formulation plus 11 solver-boundary
Python tests; 2 optional IQM compilation tests. Local Lighthouse: factory 94
performance / 100 accessibility; guide 90 performance / 100 accessibility after
contrast fixes. Browser checks cover Lunar factory, legacy URL normalization,
manual scene and matrix stage/cell inspection. Secret scanning and the isolated
candidate build precede the commit. Both remote solver holds remain in force.

Release candidate: isolated production build, staged gitleaks scan (no leaks) and
whitespace checks passed. Publish the approved snapshot through the existing main
Git integration; verify the resulting commit and deployment after the push.

## 2026-10-17 — Strengthen Stage 1 and certify the compact representation

User requested sustained iteration against the challenge conditions. Re-read the supplied challenge and visually checked the mandatory-method page. The previous 4/8 h schedules were already globally optimal; improvements target representation, quantum coverage and reproducible evidence. Kept ODRA5 and VeloxQ on hold.

Implemented an exact pairwise-order QUBO for two/three jobs. All common-order makespans are calculated, two cyclic-state costs are set above all valid costs, and integer Boolean interpolation cancels the cubic term. A uses one bit, B three: the information minima for distinct states for all 2/6 common orders. Unlike the previous horizon-feasibility models, valid-state energy equals makespan. Full independent machine-order enumeration checks that neither official optimum is lost. The builder tabulates all permutations and already reveals their optimum; no quantum speedup, general scalable encoding or broader schedule-space equivalence is claimed.

Screened eleven configurations on seeds 0–2; retained all failed/non-improving samples. One-layer B reached only ~80.58% or ~95.21% optimal samples with shared/independent mixers; p=2 independent mixers reached 100%. Confirmed seven settings on twenty fresh seeds 200–219. Selected A p=1/shared-X/one restart and B p=2/independent-X/eight restarts each returned 81,920/81,920 optimal measurements. Four restarts matched eight in this validation; eight remains a conservative training budget. Three layers offered no observed improvement over two. The same three-bit classical B QUBO also reached 10,240/10,240 optimal samples, emphasizing how easy these fixed cases are classically.

Fresh seed-2026 quantum runs exported both official JSONs with 4,096/4,096 optimal shots each. Added full truth-table/reference certificates, actual source snapshots, QASM, angles, raw counts, compressed optimizer histories and reproducible search/validation commands. Strengthened the verifier to rebuild models from official inputs and check compact QASM plus ideal ground-state probability. Tests exercise all bitstrings, cyclic penalties, 40 additional duration tables, nonoptimal-but-feasible samples, full cost phases and tampering. Updated default preparation, selection, guide evidence, formula/dimension explanations, README, design and current/historical status boundaries. Full report: `docs/STAGE1_COMPACT.md`.

No service call, physical QPU job, team message, commit, push or deployment. Stage 2 and wider submission deliverables remain separate work.

Final verification (17 October): all 179 retained compact run bundles pass the strengthened verifier and every run returns an exact optimum. Full preparation reproduces both required quantum schedules and the 512,000-assignment legacy audit. All 26 core Python tests pass (2 optional IQM tests skipped), all 52 Node tests and the static build pass, and the local browser renders the selected quantum panels and compact formulas correctly. Automatic guide evidence regeneration matches the checked public summary exactly.

## 2026-10-17 — Stage2 source freeze and untouched comparison

Implemented and independently checked the complete synthetic manufacturing extension under `stage2/`, separate from the mandatory baseline outputs. The one-minute factory includes BOM joins, qualified workers/calendars, transport, finite buffers, portable tools/service/rental, wear, energy, quality/replacement and revealed disruptions. Extensive development compares static controls, actual CPU-simulated local QAOA against exact/SA/uniform, PPO, learned CEM time schedules and independently sampled MPC. Incorrect batch-reward preferences, maintenance/outage overlaps, failed packaging, policy regressions and validation reversals are retained rather than discarded.

Before reserved outcomes, sealed the complete policy/source/checkpoint/protocol bundle and launched ten256-tape final cohorts. The official preselected cheap controls remain fixed even when a different frozen candidate performs better on final tapes. Paired environment-cluster statistics retain actors as nested replicas; only the two specified12-order quantum mean contrasts receive the declared family adjustment. Neither demonstrates quantum advantage. A separate quality/material relaxation gives primary-only certificates on fixed realized tapes; positive remaining gaps are bounds, not exact optimality gaps. One separately declared audit replay supplies a complete nontrivial final witness with an unavoidable final-pump loss.

The current final campaign is still finishing. Detailed source/result/cost provenance and honest uncertainty are in `docs/STAGE2_EXPERIMENT_LOG.md`, `docs/STAGE2_FINAL_EVALUATION.md`, `docs/STAGE2_METHOD_SELECTION.md` and `output/stage2-search/`. A bounded TRAIN-only offline schedule-neighborhood audit investigates controller headroom without changing the selected final policies. Current software checks:378 Stage2 tests before the final freeze, additional reporting/activity corruption tests, and71 frontend tests. Actual selected-model replays and small QAOA run from a portable source package in a minimal environment; no GPU/QPU is required for those demos.

Stage2 remains on its separate local publication hold. Read-only repository metadata verifies current private visibility; the public-source, video and submission obligations must not be marked complete. No Stage2 commit, push, deployment, VeloxQ or physical ODRA call was made.

###17October2026,01:23UTC — complete Stage2 final evaluation

All ten globally frozen final cohorts completed with23,552valid executions across74method/context groups. Complete aggregation computes all41declared paired contrasts; independent audits verify592original retained traces and every row's fresh numerical anchor. Original policies/source archives remain unchanged; historical partial reports remain. Full result/limits: `docs/STAGE2_RESULTS.md`, `output/stage2-search/final-complete-report/`. The two named n12quantum mean-missing intervals both crosszero. No advantage, post-final policy switching or complete factory secondary gap is claimed. MPC16 improves fulfillment against the selected cheap policy, whereas MPC24regresses against its selected CEM, preserving the negative result.

One fixed TRAIN-only finite-neighborhood audit completed12184grid+24oracle-witness runs; auditing is separate from policy deployment/generalization. A bounded two-hour16CPU exact-reference follow-up reuses the unchanged four-pump fixture and checked1567hint; pending results do not revise its[1480,1567]interval. Final campaign allocation70.42CPUh and measured episode processCPU68.58h are separately reconciled and included in the overall research ledger. No GPUtraining, physicalQPU, publication, submission or deployment performed.


### Stage2 technical research closeout — 2026-10-17 03:29:54 UTC

All tracked research cluster jobs are finished; the requested monitoring and handoff window remains active. The immutable 03:16 ledger records 431.9967 allocated CPU-hours including failed jobs, zero recorded GPU-hours and zero physical-QPU/VeloxQ calls. Final evaluation used 70.4178 allocated CPU-hours within that total. Local setup, audits and agent inference are not a complete host-wide meter. ODRA/VPN troubleshooting remains stopped under the user hold. No autoresearch, Stage2 commit, push, deployment or submission was performed.

The unchanged final benchmark has 74 groups, 23,552 valid executions and 41 contrasts. Independent audits freshly check 592 original retained traces and rebuild every row's numerical anchor. Preselected classical fulfillment is 94.9844% at 12 initial orders/96 hours and 91.0156% at 32 initial orders/240 hours, with substantial lateness in the latter. This is the tested-controller frontier; failures at 16/24 do not prove physical infeasibility. MPC improves 16 but worsens 24 against the selected CEM. Useful adaptive-RL and quantum advantage remain unestablished. Actual QAOA uses at most five total bits, including slack, in restricted local decisions with recorded classical fallback.

Exact reference job 6117555 reports FEASIBLE 1541 and CP lower bound 1524 on the identical four-pump fixture: interval [1524,1541]. Raw CP/hint identity rejections for reservations before pump birth remain preserved. A separate derived witness changes only move74.start from 1382 to 1420, preserving physical actions, timings and recomputed metrics; both unchanged general checkers pass. Six mutation/scope tests and a second independent review pass. Auditing and normalization run no new factory or solver, change no frozen checker and add no final sample. Evidence: final-independent-audit/reference-2h-6117555/ and reference-2h-methodology-review/. This does not bound the rich stochastic factory's global gap.

Portable v2 is 10,097,277 bytes, SHA 8a54050496537a794e17bdf73c7d47ed323798f0ae7e67e8152f6d49e3c0aaa1. Its 2,436 indexed files, 24 predeclared replays and 29 separate supplements verify in 10.84 seconds in isolated Python 3.14.6 with only NumPy 2.5.4 and pip installed. Supplemental records are hashed; their entire analyses are not rerun by this compact verifier. Portable v1 and the full 116.8 MB v2 archive remain byte-stable; the full archive independently reproduces all 41 contrasts and 592 retained replays. Read docs/STAGE2_RESULTS.md and output/stage2-search/stage2-portable-final-v2-closeout-receipt.json.

The local 4187 research view shows the final frontier, TRAIN neighborhood, conditional leaves, posthoc proof and current reference interval with qualifications. Frozen final-export SHA 6a66d36b2ea032b773a2b550d8773c13a0c4ea3f1fab0ef3565894853746fd60 remains unchanged. GitHub rechecked at 03:26 UTC is still private: the public-MIT requirement is unmet; completed video, team and form receipt remain unverified. Preserve the other chat's Stage1/root presentation changes and the publication hold.


Stage2 authorized eight-hour research window completed at 2026-10-17T04:14:35.500900+00:00. Technical evidence and local handoff are complete; all tracked research jobs are finished. See output/stage2-search/research-closeout.json and docs/STAGE2_RESULTS.md. Publication hold remains; repository private at the04:11UTC live recheck, with video/team/form receipt unverified. No further experiments or policy changes are scheduled.

## 2026-10-17 — Later solution-quality scoring supplement

The user requested stronger evidence for the five-point solution-quality criterion
and authorized local Mac compute. Stage 1 was already optimal and needed no new
search. No VeloxQ, physical QPU or remote compute was used.

Added `stage2/quality_gap_audit.py`: rebuild all 2,048 distinct configuration/tapes
and audit the 23,552 original frozen outcome rows across all 74 groups. The
original source-bound quality/material lower bound and best valid same-tape
retained witness bracket the realized primary optimum; exact actor-within-tape
weighting gives absolute excess-missing intervals. Hindsight witness selection is
an offline bound, not a deployable policy. Invalid/mismatched rows, incomplete
actors, duplicate actors and incorrect weights are rejected. No final policy,
factory source, outcome, held-out sample or previous report is changed.

Added a stronger independent `quality_compound_bound.py` supplement: the engine's
`1-(1-r)(1-p)` recurrence gives the necessary floor
`1-product(1-min_legal_mode_risk)` across mandatory steps, with zero wear granted,
exact fractions and a conservative rounding margin. Original source/domain guards
remain mandatory. Inspection draws enter offline proof only. On the unchanged
32-order/240-hour final sample, primary-optimum certification rises from 93.44%
to 95.28%, and mean excess above the realized primary optimum is at most 0.04719
missing orders. The 12-order selected controller's weighted certificate rate is
95.61%, with excess interval [0.06469,0.06875]. Secondary optimality and quantum
advantage remain unestablished; the weak 24-order results remain visible.

Tested a supplemental equivalent deterministic CP formulation in
`reference_polish.py`, preserving the original reference solver and all frozen
physics/checkers. It replaces worker-path bits with chronological hall-order
constraints, adds AGV occupation intervals and prunes precedence-impossible arcs.
The original 1541-minute witness fits every new constraint; both formulations
agree on a proved small optimum. A five-minute/eight-worker search retained1541
and reported1457, below the earlier1524 lower bound. Three worker-order
neighborhood searches also retained1541 and proved only their restricted local
optima. Their lower bounds are explicitly excluded from global claims. Thus the
combined best four-pump interval remains [1524,1541], at most1.116% excess.
Fresh unchanged physical/identity checks also validate the existing863/1191
two/three-pump exact witnesses.

Measured local reference searches used2374.76 process CPU seconds (0.660CPUh),
separate from the immutable earlier432CPUh ledger. Tests/audits are excluded from
that process-CPU subtotal. All local searches ended. The closeout, source
snapshots, negative searches and audit tables are in
`output/solution-quality-20261017/`. The evidence is summarized in
`docs/SOLUTION_QUALITY.md`, linked from README/results/judge notes. The Project
Design now describes the actual QAOA baseline and unused remote adapters.

Validation:18 quality tests,7 supplemental-reference tests,6 original multi-pump
reference tests and87 frontend tests passed. Hash checks match the original input
rows and current compound-audit snapshots. Jury points cannot be guaranteed.


## 2026-10-17 — renewed Stage 2 planning-core research (active)

The user renewed the goal of the strongest feasible Stage2 contender after the
original8h campaign. New local-only work is separate from its immutable final
tapes. Complete deterministic32/48/64-operation pump/BOM scheduling-window
QUBOs now have raw interval CP references, exact support pruning, independently
checked conditional energies, affine dual-rail reductions and optional exact
machine-only metric-family changeovers with zero added bits. The32-operation
minute-grid/setup raw CP optimum787555 is proved in9.71s; coarser grids have
measured loss and are never called exact reductions. Fine-grid raw CP did not
construct the115878-candidate time-indexed QUBO.

Restricted complete-trajectory masters fit5/8bits but explicitly discard raw
schedules; their nonzero full-model gaps and failed4-pump parent generation
remain visible. W-state/XY makespan-preserving circuits improve the8bit pool's
mean p2 single-shot optimum probability to13.42% vs0.48% X QAOA and2.5% strong
one-hot-uniform control. Logical CX64->48 includes preparation; depth worsens
67->81-83. This is not a classical runtime/quantum advantage result.36 emitted
X/XY circuits and48 earlier block circuits independently match Qiskit;144 generic
noise experiments are proxy sensitivity only, not hardware calibration.

Both full-factory advisory integrations are rejected. The softer rule's16 fresh
seeds50000000..15 produce48 physically valid traces but mean missing orders
worsen1.4375->2.125; constructive and QAOA outcomes are identical. Keep the
previous strong controller. Do not add these tapes to frozen final estimates.

24 targeted tests pass, including30 randomized exhaustive raw/CP/pruning checks.
New primary campaigns copy sources before running and retain source-stable
manifests and failures. Initial two prototypes have hashes but no copied sources.
The local checkpoint meters813.58 process CPU seconds across14 distinct reports
(excluding unmetered tests/diagnostics), max recorded process RSS6.60GB; GPU/QPU0.
This is separate from both the original frozen ledger and the other chat's
solution-quality searches. Research remains active, next on broader component
trajectory masters rather than merely reducing already-tiny recombination pools.

See docs/STAGE2_PLANNING_CORE.md and
output/stage2-search/planning-core-checkpoint-v1/report.json. Visualization
subagent built the optional /stage2/planning.html with saved BOM/machine/worker
schedules, losses, mixer controls, logical costs and negative validation; frozen
final export unchanged. No Stage2 commit/push/deploy, autoresearch, ODRA/VPN or
remote compute.

### 2026-10-17 — Mac-only planning-core scaling and verified circuit compilation

The user authorized the full48GiB Mac memory, with external compute held until
a concrete need is explained. All renewed work stays local. Larger rigid
component pools, time-shift pools and machine/worker-flexible suffix pools are
retained, including negative results: most cannot beat an existing parent even
when the finite pool is solved to proven optimality. Larger bit counts alone do
not establish useful search complexity.

Finer operation-level pools retain cross-operation BOM, machine/crew/calendar,
travel and machine-only metric setup constraints. The128-operation pool has
6,046bits/491,109couplers; native same-pool CP proves19,580,896 versus its
21,525,346 heuristic parent. Its32-operation pool retains the proven grid15
raw optimum908,670 using1,489bits/112,060couplers. This is measured optimum
retention for that instance, not lossless compression of every feasible plan.
The specialized compiler matches every saved128-operation coefficient and
reduces measured construction244.62s→6.52s; no quantum speedup is claimed.

The original128-operation table reference returns UNKNOWN in120s. Analytic
calendar domains and shared exact earliest-walk completion functions make a
stronger independent native reference practical. Forty small exhaustive cases
cross-check domains and optima; walking boundaries are independently checked.
Complete raw grid15 references prove32/48/64-operation optima908,670 /
1,297,680 /1,945,958. A600s128-operation local continuation finds13,941,691,
with solver lower bound8,071,630, independently checked raw schedule and
42.10% remaining interval gap. Its peak process RSS is1.322GB. The operation
pool's optimum is40.45% above this better raw feasible incumbent. These cells
exclude physical shipping, AGV capacity, finite buffers, tools/service, energy,
human setup crews and stochastic quality; they are not whole-factory bounds.

Conditional circuits now use exact affine choice substitution and a W/XY
makespan mixer. An exact invariant-sector simulator stores k*2^n amplitudes
for n binary choices plus k makespan qubits without reducing logical qubits.
The256-block, three-seed controls reach21 logical qubits and a small scheduling
improvement, but the plain classical proposal and uniform controls match QAOA.
No quantum advantage is established; the best new physical-factory controller
remains the earlier incumbent after both advisory integrations were rejected.

All768 longer-run raw QASM circuits match Qiskit's full-state simulation.
Three aggressive level3 compilations fail the1e-10 probability check, maximum
3.93e-6; the failed audit is retained. Diagnostics isolate identity-removal and
commuting-cancellation passes. Verified level1 fallbacks for those three cases
preserve all768 compiled circuits within2.06e-14, with unchanged tolerance and
actual selected compiled QASM exported. Resource counts from rejected
compilations are not promoted. Earlier48-local/36-trajectory/48-sector audits
remain separate; overlapping audit cases are not distinct-circuit counts.

37 targeted backend tests pass, including the earlier30 and additional40
randomized exhaustive instances. The optional scaling visualization passes45
targeted viewer checks and shows the newest128-operation Gantt/BOM, bounded
quality and all prior references. Frozen final export SHA6a66d36b… remains
unchanged. Latest scaling export SHA88fba547… is an optional development view.

`output/stage2-search/planning-core-checkpoint-v2/report.json` seals36 distinct
top-level reports and combines the same-model raw128 interval. It meters
5,678.26 process CPU seconds, including failures, and maximum recorded process
RSS6.741GB. This is a lower bound excluding unmetered tests/diagnostics, separate
from the original431.9967 allocated-CPU-hour frozen ledger. New GPU/QPU/remote
jobs0. No autoresearch, ODRA/VPN, VeloxQ, publication, submission, Stage2 commit,
push or deployment occurred. See `docs/STAGE2_PLANNING_CORE.md` and
`http://127.0.0.1:4187/stage2/planning.html?scaling=1`.

This bounded planning-core batch is complete. Its formulation, same-model
references, costs, circuit verification and integration tests are reviewable.
The failed integrations and absent quantum advantage remain findings; completion
of this batch does not certify competition acceptance or a winning submission.

## 2026-10-17 — user pause and complete owner explanation

The user explicitly stopped further optimization to understand the current
problem and results. The latest larger native-CP probes had already completed
when the stop was processed. No optimization processes remain running; no new
search, training, factory episode or hardware job was launched for this task.
The pause receipt is retained at
`output/stage2-search/pause-explanation-20261017/pause-receipt.json`.

Completed larger probes cover 512 operations over 96/120 hours and 384 operations
over 96 hours. All short CP runs returned UNKNOWN without a complete plan.
A separate optimistic QA-worker packing certificate proves the declared
512-operation/96-hour cell infeasible: 6,496 required attendance minutes exceed
5,979 available packed minutes. The other two certificates are inconclusive.
These are simplified planning-cell statements, not full-factory limits.
The three probes add 1,364.66 process CPU seconds; together with checkpoint v2,
the renewed metered local work is approximately 1.96 process CPU-hours. This is
not directly additive to earlier allocated cluster CPU-hours.

`docs/STAGE2_CURRENT_EXPLAINED.md` now explains Stage 1, every implemented
factory condition, the controller hierarchy, measured performance, separate
physical references and planning cells, complete/restricted/conditional QUBO
scope, classical/quantum viability, capacity and proof meanings. README and
CONTEXT link it and state the pause. It explicitly separates the 21-qubit
32-operation experiment from the 128-operation pilot and from factory results.

The read-only visual guide at `/stage2/start.html` adds four chapters: distinct
models, one pump and its conditions, solver/QUBO behavior, and measured evidence.
Factory/research/planning navigation links it. Its small hash-anchored export
uses retained files only; frozen final/base-planning exports remain unchanged.
The visualization work passed 51 targeted tests and browser review. No new
commit, push, deployment, publication or submission is implied.

## 2026-10-17 — written factory definition and encoding clarification

The owner requested an actual readable document comparable to the existing
learning-methods course, with the complete factory definition and a direct
answer about domain-wall encoding. The supplied challenge §5/§11 was reread;
its integrated quantum/QUBO emphasis is stronger than the previous general
explanation conveyed. Decomposition is permitted, but the physical/quantum
scope gap remains a submission weakness, not solved by interface complexity.

`docs/STAGE2_PROBLEM_WALKTHROUGH.md` provides 22 connected chapters explaining
input quantities and orders, each recipe/machine, workers/setups/tools, finite
buffers, stock, actual lane times, robot chargers, the separate stationary
battery, solar/grid/tariff arithmetic, failures, objectives and controller scope.
Its encoding chapters trace the actual builders: earlier Stage1 domain-wall,
selected Stage1 pairwise order, Stage2 local action/bounded-binary slack, planning
one-hot groups and conditional binary choices with a one-hot makespan register.
Worked examples distinguish choices, penalties, domain-wall thresholds and
logical-qubit counts. The HTML edition is generated under `docs/stage2-problem/`
without touching the other chat's learning-methods files. Research remains paused.

## 2026-10-17 — final combined merit integration and adversarial passes

The user authorized multiple independent subagent review passes, relevant fixes
and completion of the non-VeloxQ merit implementation. The resulting centerpiece
is the same complete32-operation furnace-recovery input, rather than a separate
small fixture. Earlier pauses and failed attempts above remain historical.

The certified full-model45→0weighted-lateness recovery is lost by the original
781-bit pool and restored by deterministic nested enrichment at2078bits. Complete
optimization uses2499bits/381371couplers. A distinct exact hard-deadline query
uses818bits/33817couplers and has an independently checked zero-energy witness.
The outage query is infeasible; sampling a nonzero state is not its certificate.
Forty cold binary/one-hot annealing runs retain640samples; an independent report
audit confirms0encoded-valid,0raw-valid,0target-satisfying samples at those
budgets. Native query CP is fast; these failures do not imply intrinsic hardness.

The completed trajectory bridge uses all eight components and every original
operation, preserving first and best constructive parents before adding choices.
Nested caps2/3/4 give18/28/36logical qubits and512/26244/262144sector states.
Across two known inputs and three sampling seeds, QAOA and sectorSA each return
18/18valid encoded optima; uniform returns6/18. The constructor already finds the
optimal recovery plan, and sector energies are enumerated classically. There is
no quantum advantage claim. A final review caught invalid uniform winners being
counted by raw objective alone; exporter regression tests now require validity,
raw objective and literal energy. All54records and observed counts were audited.
Six18-qubit circuits pass independent full-Hilbert before/after-transpilation
checks; all18circuits receive logical resource audits. Failed first-two-parent
and fixed-boundary attempts remain preserved with their original outputs.

Six fixed-grid/horizon ablations quantify feature effects, with all native and
pool optima certified. Continuous-calendar dense counts are supplemented by an
exact blockwise audit instead of allocating its3,785,787-coupler support matrix.
The larger64/128native references remain UNKNOWN, with checked incumbents/bounds.
Four current cold SDK files cover818deadline,2078enriched at two penalty settings
and2499complete;815121literal coefficient/constant checks establish exact integer
serialization. These are offline preparation, with no token access or service call.

`capacity-economics-v2` values four checked saved schedules under an explicit
synthetic PLN profile, using exact rational arithmetic and135sensitivities. An
independent minute-by-minute ledger recomputes36cost lines. The example event-fee
threshold is11389/24PLN=474.5416667; the assumed repeated-exposure purchase-price
threshold is19923.63PLN. These value deadline-priority schedules; they are not
minimum-money optimization, calibrated industrial ROI or a measured failure law.

The manufacturing studio now integrates the representation frontier, same-model
whole-recipe QAOA, adjustable economic assumptions and feature table. Its local
fresh action actually generated and simulated a28-qubit run with0weighted late
minutes and855-minute completion in0.84s, retaining a timestamped protocol,
counts, QASM, sources and manifest. The constructor is shown alongside it.
README, design, combined plan, current live script and submission preparation
are reconciled around these scopes. The older manufacturing-v3video remains
explicitly a review draft predating these additions; final recording, human
rehearsal, publication and submission are separate release duties. VeloxQ and
physical QPU use, external compute, commits, pushes and deployment remain held.

Final acceptance uses `scripts/verify-stage2-merit.py`, independent document/UI
consistency and command/source-hash receipts. Its generated acceptance document
records actual pass/pending status; this log entry does not predeclare a pass.
## 2026-10-17 — accepted integrated strategy for both awards

The user approved prioritizing the hackathon rubric over a quantum-advantage
requirement and targeting the overall award plus best use of VeloxQ through
one catering-production extension. Keep the complete-meal/shared-batch model,
compact correct QUBO, meaningful quantum solver outputs, matched references,
scaling measurements and polished trace-backed demo. A standalone SAT pivot
and speculative cluster expansion are parked. QAOA/VQE remain method variants
on shared inputs; actual checked results should decide the featured method.

VeloxQ's intended role is larger/broader same-model production optimization,
with small shared-QUBO comparisons and independent schedule validation. Measure
raw feasibility, quality/reference gaps, build/service/full timings and repeat
variability rather than claiming superiority from an SDK call or paper capacity.
The challenge PDF Section15lists2000PLNoverall and1000PLNbestVeloxQ; it states
no mutual exclusion but does not explicitly confirm simultaneous receipt by
one team. No organizer or teammate message was sent. Existing service/QPU
execution and VeloxQ credit holds remain. This entry records a decision, not
new solver results, service integration, push, deployment or submission.


### 17 October — a concrete larger workload for the VeloxQ owner

Prepared the same paired-meal S3 input at 12 customers and nested 512/1024/2048
variables, including all 26 anchor blocks. Measured 37,008/156,129/636,882 couplers;
these are approximately 28–30% dense, not a claimed sparse backend showcase.
Generated local domain: 18,182 programs. Five-second one-worker CP references:
FEASIBLE (7,2,10,10), FEASIBLE (8,8,10,10), UNKNOWN; independent raw CP FEASIBLE
(8,1,7,7). Checked idle witnesses retained. These are limited references, not
hardness or advantage evidence. Added optional feasible anchor bounds to avoid
unnecessary coefficient inflation while preserving lexicographic priorities;
existing frozen inputs are unchanged. The service owner still needs a capped
pilot manifest and explicit user authorization. Zero VeloxQ/IBM calls.


### 17 October — game viewer follows the actual paired-meal evidence

Replaced the stale V1 replay export with five V3 cases / 16 independently checked
views. Preserved the pixel kitchen/art and expanded it from one selected batch to
multiple programs and idle data bits. Complete handovers now require both courses;
orphans contribute to component waste. Included the separate mandatory recovery
operations in equipment, attendance, props and inspector timelines. Source selector
switches real QAOA, control, offered-domain exact and independent raw-reference
plans; sample frequency/hash and scope remain explicit. Added a readable model/results
dialog with objective/penalty equations and all eight larger pilot outcomes. Existing
uncommitted UI was backed up before integration; cleanup remains deferred. No live
solver calls, credits, hardware or deployment verification are implied by this work.


V3 viewer verification: npm run build passes134site tests;45Python catering tests
pass with one optional SDK skip in the lightweight environment, and the Qiskit
circuit-equivalence test passes separately. Independent replay checks cover16views
and48manual interventions. Desktop and390×844portrait browser checks verify the
actual recovery clean, raw S3completion, skip-side material outcome, model equations
and retained results. Evidence and screenshots: output/catering-ui-v3-qa/. This
is local verification; production deployment and final video remain separate.


### 17 October — stronger local classical comparisons for the service owner

Frozen a separate30second,one-worker reference campaign on the existing scale
bundles, plus2second seeded cold raw-bit SA controls. Raw CP improved toFEASIBLE
(5,1,11,11); offered-domain incumbents at512/1024/2048 became(6,1,10,10),
(7,2,11,11),(8,3,8,8), allFEASIBLE. The original five-second references remain.
SA has valid weak returns on the two smaller tiers and no valid return at2048.
All raw responses/statuses/bounds, load and call times and source snapshots
are retained. No hardship/speedup claim from finite budgets or failed SA;
no reference plan teaches the quantum search. No credits or QPU calls.


### 17 October — make the production sequence explicit

The user asked how production order and overlap are chosen, then requested the
explanation in the demo. Added read-only production-sequence projections of the
retained plan: cook-start order, per-order packing queue, component waiting and
ready states, and event stepping. The batch timeline now opens by default,
with a separate equipment view, cleaning on a second lane and departure markers.
The default sample explicitly shows B prepped first but C cooked first; one
shared C batch supplies both orders. Existing result hashes/physics/encoding stay
unchanged. Replay ends at the last action/departure and holds the outcome before
looping, without changing the physical planning horizon. No VQE/QAOA training,
classical optimization, account access, QPU or VeloxQ call was performed.

Verification: all138site tests and the static build pass. Browser checks confirm
waiting after prep, exact packing→order links, concurrent clean/pack/cook at11:40,
separate repair/wait/clean windows, mobile clipboard access, final20/20handovers,
and preserving that result when paused before the loop. Only local rendering,
source reads and deterministic projection checks were used; no training or solver
run accompanied this UI pass.

### 17 October — plan the catering talk and demo around the actual decision

Added docs/CATERING_PRESENTATION.md with a timed three-minute script, a
five-minute recording storyboard, exact kitchen actions, a current claim sheet,
Q&A and owner tasks. The shared side batch supplies the opening: two orders
need both courses; skipping the side changes twenty complete meals to zero.
Kept the game visual direction and separated local validation of a retained
sample from a future fresh optimizer launch. No new training was requested.

Reviewed the official launch/result, design, development-log and scoring
requirements. Marked the old factory submission package as historical and
pointed the current project design and entry docs to catering. Incorporated
the service owner's already committed first cold VeloxQ runs into current
status text; this chat made no service call. The prize plan prioritizes a
budgeted, mathematically checked feasibility improvement and comparable
quality/runtime measurements before recording a performance headline.

Presentation-plan verification: the documented local evaluation command runs
successfully and reports the retained best tuple (0,0,2,2), without repair.
The spoken draft is 345 words. Entry-document links and git whitespace checks
pass; npm run build passes all 138 site tests and produces the static site.
This prepares the plan and checker demonstration; recording, fresh optimizer
launch rehearsal and later VeloxQ improvement experiments remain open.

### 17 October — audit all submission points and preserve release privacy

Mapped all eight official scoring categories (30 points), every required
deliverable and the separate unweighted VeloxQ criteria to current evidence
and remaining gates in docs/STAGE2_SUBMISSION.md. QAOA plus VeloxQ is the
current presentation default; a VQE result must pass the common checks and
justify inclusion before the freeze. More method names are not rubric points.
The major technical gaps are larger-instance quantum quality and VeloxQ
feasibility/quality. Half the points concern documentation, video, defense
and consistency, so those have explicit acceptance work too.

Read the official requirements, current result receipts, root schedules and
MIT file; checked the actual GitHub visibility as private and fetched main
for delivered method work. Added the current catering AI-use disclosure and
corrected the presentation measurement plan: final-only service samples do
not expose time to first feasible solution. The user explicitly wants GitHub
private until the final submission step. Preparation targets preserve that
preference while leaving access-check/submission time before the deadline.
No repo visibility change, deletion, cleanup, service call or training occurred.

Checklist verification: all eight rubric rows total30points; changed Markdown
links resolve locally; root schedules report4h/8h; the cited complete-cell
report contains all six trials with the stated reference tuple. Whitespace
checks pass. These documentation checks do not constitute a final release run.
