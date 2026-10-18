# Development log

Axion Kitchen — QPoland Quantum Hackathon 2026. This log records the decisions,
failures and checks that shaped the submitted model. The [complete working
history](docs/archive/2026-10-17/DEVELOPMENT_LOG_FULL.md) preserves the earlier
experiments and abandoned directions. Raw results retain their original hashes.

## 16 October — establish the baseline and independent checks

We started from the official two- and three-job factory instances. The first
formulation indexed operation starts in time, with one-hot, precedence and
machine-conflict penalties. Classical references and a schedule checker gave
an independent way to distinguish a valid schedule from an optimal one.

## 17 October — reduce the baseline register

The baseline was reduced to common job-order bits and an earliest-start
decoder. For three jobs this represents all six common permutations with three
bits, rather than all feasible timed schedules. We tabulate those permutation
costs classically; that factorial preprocessing makes this a small-instance
encoding, not a scalable quantum-advantage claim. The selected measured QAOA
simulator results give makespans 4h and 8h. Both required root JSONs match actual
retained samples. [Formulation and evidence](docs/STAGE1_COMPACT.md).

## 17 October — choose an extension that changes the decisions

We explored manufacturing recovery and capacity planning before choosing
catering batch production. The extension adds shared batch yields and paired
main/side service: cooking an isolated component does not complete an order.
The earlier factory studies remain [archived](docs/archive/README.md).

We kept a finite-grid, contiguous-packing profile so every method could use
one agreed problem. Ingredients, monetary prices, aggregate power and
interrupted-cooking recovery were excluded from the implemented profile.
This prevented the broader proposal from being mistaken for delivered features.

## 17 October — correct the outage semantics before comparing methods

The first catering build omitted the ten-minute clean required after cooker
repair, including when that cooker had been idle. This let production resume
too early and incorrectly erased the disruption's effect. We corrected the
boundary policy and added regression checks. V1 outage answers remain historical;
they are not presented as valid results for the corrected specification.

Started work stays fixed. Recovery cleaning occupies both the cooker and a
qualified worker. The raw checker reconstructs those intervals independently.
The implemented recovery time is a declared earliest-compatible policy, rather
than another optimized maintenance decision.

## 17 October — model complete service and waste quadratically

We moved from component-demand scoring to the paired-meal profile. For binary
main and side coverage M,S, complete service is MS and unpaired waste is
M+S−2MS. Coverage is linear in selected batch programs, so these expressions
remain quadratic without product-register bits. Surplus and unpaired disposal
are separate terms in the physical material balance.

The objective orders priority-weighted missed meal lots, discarded component
lots, batches and changes to the unstarted plan. Bounds prove the scalar
weights preserve that priority. In the published fixtures the previous
unstarted plan is empty, so R=B; they do not isolate a stability benefit.
[Full model and proofs](PROJECT_DESIGN.md).

## 17 October — distinguish missing choices from solver error

A bit selects one locally valid batch program, including its quantity,
allocations, resources and phase times. Anchor blocks contain those choices
and idle. Cross-block penalties prevent resource clashes and duplicate use of
demand. The complete small cell contains 32 program bits plus 3 idle bits; its
one-hot sector has 1,045 states, 59 physically feasible. Independent raw and encoded
references agree on the optimum (0,0,2,2): 20 meals, no waste, two new batches.

Larger quantum portfolios deliberately restrict the choices. We kept both the
same-portfolio optimum and the independent full-grid reference. All eight
changing-portfolio pilot outcomes trail the full-grid optimum, even though six
attain their final offered-pool optimum. Initializer/mixer controls tie those
final best outcomes. We therefore use that pilot to study representation loss,
not as evidence that quantum phases beat the controls.

## 17 October — select and audit the quantum methods

The main QAOA configuration was selected on the cell/S0/S1, then frozen before
S2/S3. It uses depth three, separate objective/conflict angles, blockwise XY
mixing and layerwise COBYLA with exact CVaR 0.1. Angles are optimized per instance;
the held-out test concerns configuration selection. The 400-run campaign finds
the offered-pool optimum in 10/10 seeds on both held-out cases at both budgets.
All 1,638,400 retained shot counts were independently rechecked.

VQE compares product, block-local and coupled ansatzes. The selected coupled
Givens L2 method uses exact CVaR and simulator adjoint gradients. Its primary
held-out CSV reports 10/10 and 9/10 optimum hits, with higher per-shot optimum
probability than QAOA but different training work and final shots. Five exported
plans pass the raw checker. Historical per-seed E5 angles and raw samples are
absent, so we keep that limitation explicit rather than declaring an equal-work
method win.

Integration exposed export problems: VQE used the wrong count field and lost
one cell export through a filename collision; QAOA embedded a stale self-hash.
We retained the original receipts, supplied checked exports, fixed future
packaging, and preserved frozen source versions. Future VQE runs retain angles,
actual convergence status and source identity captured at worker import.
[QAOA](docs/catering-methods/QAOA.md), [VQE](docs/catering-methods/VQE.md).

## 17 October — improve the VeloxQ representation

The initial cold scale jobs produced few valid schedules. The conservative
penalty dominated the objective, and idle choices introduced redundant bits.
We derived a tighter deletion-loss penalty bound and proved that removing idle
bits preserves the feasible objectives and optimal schedules. This creates new
sampling matrices; it does not change anyone's existing frozen quantum input.

At equal 20,000 steps and 512 replicas on the 512-source-bit tier, the new
representation improves valid returns 17→512/512 and best delivered service
10→50 of 140 meals. Most valid returns are empty plans: only 143/512 select any
batch (102/512 and 62/512 at the larger widths). Waste rises 30→60 component portions; the declared policy
prioritizes complete service. Raw handovers were independently rechecked.
These are exploratory single-job comparisons, and CP/SA still find better plans.

Actual solver widths are 486/998/2022 after idle elimination. The complete ledger
retained 61 attempts at that point, including failed downloads and recovered jobs. We report
backend and whole-call time separately. [Study and proof](docs/CATERING_VELOXQ_TUNING.md).

## 17 October — prepare the demonstration and submission checks

The live demonstration separates a saved schedule, a manual side-batch removal
and a fresh execution with frozen trained angles. The fresh launch independently
checks returned schedules; a failed launch opens an explicitly labeled saved
fallback. No remote backend is needed during the presentation.

We prepared a 4:20 video script, a 2:45 live route, a timed recording sheet and Q&A
notes. The final review added an actual development-log summary, explained the
shown compiler lines and shortened rushed passages. No final video was recorded.

A clean export passed the archive, mathematical, baseline and physical-sample
checks recorded in [the release-preparation receipt](output/catering-release-prep-v1/verification.json).
The final editorial pass adds an explicit baseline stage and the requested
price-of-realism ledger. Frozen inputs and measured results are unchanged.
Historical notes are archived, not presented as current deliverables. The current
log is a curated account of decisions; the full working history remains linked.
The selected baseline verifier now has adversarial tests for forged exports,
measured-count changes and changed model coefficients. The historical factory
guide's display-source list was refreshed for the archived documentation paths;
its numerical evidence exports were not changed. A final UI correction enlarged
the cooks, placed their working positions closer to the benches and attached
the chopping tool to the moving hand instead of animating it independently on
the worktop. Replay time still drives movement; physical schedules are unchanged.

The clean export of `3653fd7d` passed all 13 release stages: 152 site
tests, 43 core checks, three adversarial baseline checks, the full 400-run QAOA
archive audit, VQE/VeloxQ checks and three fixed-angle local launches. Each
launch returned 20 meals and zero waste. The [final review receipt](output/catering-submission-review-v1/verification.json)
records the tested source and raw checks. No new training campaign, service
job, QPU call or video recording was performed.

After the numerical audit, the UI follow-up restored the supplied Axion logo
in the kitchen, benchmark browser and presentation studio. The local server
and static build now both open catering at the root, with the original factory
kept under Stage 1. Earlier factory studies were removed from the active
navigation. These changes affect branding and navigation only; the final site
build and browser checks cover them separately from the model audit above.

The default web replay now opens the larger combined outage/urgent-order case.
Its source is labeled dynamic-portfolio QAOA, distinct from the later fixed-pool
campaign in Benchmarks. VeloxQ has a direct results link; the studio still opens
the small complete cell explicitly. The review also clarified the Python minimum
and case-specific sector sizes in the setup and Q&A notes.

The final animation review aligned tools with the active pot or counter while
retaining the larger cooks. Cleaner placement and its return lane avoid pot
occlusion and collisions. All 153 build tests pass, including a geometric reach
check across all 16 method views. Six visual checks covered prep, both cookers,
packing, cleaning and recovery cleaning, including pause/seek consistency.
No model, schedule, training result or service allowance changed.

## AI use and remaining steps

Codex assisted with formulation, implementation, experiments, tests and
presentation under the team's direction. The team supplied the problem choices
and corrections and is responsible for explaining and defending the result.
We record measured outcomes separately from generated explanations.

Human timed rehearsal, final recording/voiceover, playable video upload,
authorized public-source release and actual organizer submission remain open.
The prepared scripts and checklists are not evidence those steps have occurred.


## 18 October — make the scheduling and correctness arguments visible

The presentation now maps kitchen resources to machines, setup-like cleaning
and due dates. A real frozen-cell conflict (x1/x3 on C2) explains why locally
legal programs must be selected jointly; the retained plan uses x11 on C1.
The loss chapter shows the full-bit-domain range bound and P=S+1 inequality,
while the scale chapter separates the 1,045-state correctness cell from the
18,182-program generated domain and the nested offered QUBOs.

Presentation claims are derived from retained source files and checked by the
local preflight, including the actual conflict, penalty constants and scale
counts. Video/live scripts remain 4:20/2:45 and within their speaking-rate
limits. This is an explanation/evidence pass: no compiler, objective, frozen
model, solver results, training or service use changed. Human rehearsal and
final recording remain separate.

The visual follow-up moved replay captions into the stage footer so they cannot
cover the embedded Axion masthead. Captions follow replay/code visibility and
remain distinct from the fresh-run receipt. The objective screen now defines
main/side coverage, meal priority and the 10-portion lot units alongside its
truth table. These are presentation-only clarifications of the frozen model.


## 18 October — presentation state and interaction review

Reviewed 24 video states and 16 live states, including reveal boundaries and
final holds, plus notes across every live chapter. The encoding strip now
shows source-checked x3 operations with parallel packing/cleaning and partial
cooking attendance. The opening uses kitchen art without viewer controls;
charts state their scales and VeloxQ tables include best objective tuples.

The review caught two playback faults: Play stopped immediately at the video
end and could not replay a held live chapter. Both now restart correctly, with
a regression test. Failure/retry wording no longer describes an absent sample
as checked, and the fallback opens the same complete cell. A deliberate local
503 fixture verified blank failed values and retry; it started no sampler and
was stopped afterward. Two ordinary frozen-angle local launches each returned
20 meals, zero waste and 2,173/4,096 valid shots. No training, backend allowance,
QPU use, frozen model or retained solver campaign changed. The timed routes
remain 4:20 and 2:45; final human rehearsal and recording remain open.


## 18 October — VeloxQ as part of a classical workflow

Review found the 512/512-valid headline mostly counted empty plans, so we asked
whether VeloxQ can improve a classical plan instead. Five capped service jobs
(ledger 61→66; cap 70 authorized by the VeloxQ owner) tested two ideas.

Rejected: warm-starting the whole matrix from the CP plan. The start is
accepted, but VeloxQ leaves it within 10 steps and returns mostly empty plans.

Kept: a large-neighbourhood step. The CP plan stays fixed except two freed
blocks; VeloxQ solves only that exact sub-QUBO (162–207 bits) and the merged
plan is rechecked. At width 2,022 one step improved missed meal lots 8→7; the
next step stayed at 7 even with 100,000 steps, while exact enumeration shows 6
is reachable. Longer CP (240 s) still reaches 5–6. Details and limits:
[VeloxQ study](docs/CATERING_VELOXQ_TUNING.md#hybrid-follow-up-18-october-veloxq-on-a-classical-plan).

The release check was repeated on a fresh clone of `44bd2706`, which included
the hybrid study, stale-claim corrections and benchmark update: all 13 stages
pass (154 site tests, 43 core checks, three adversarial baseline checks, the
400-run QAOA archive audit, VQE/VeloxQ checks and three fixed-angle launches
returning 20 meals and zero waste). The
[review receipt](output/catering-submission-review-v1/verification.json) now
records that commit; the check made no service call.


## 18 October — remote hybrid review, Stage 1 frame and formal explanation

Pulled main through c1787393 and reviewed the new five-job VeloxQ hybrid study.
Fresh offline decoding of each reported best source-plan witness agrees with
its recorded metrics; 51 conditioning/LNS tests pass. No service call or training
was started for this review. Corrected one documentation unit: the step-1 gap
to its exact neighborhood optimum is one component lot, or ten portions.

Both presentation routes now show the actual Stage 1 A/B Gantts from 0:04 to
0:09, between the title and extension problem frame. The preflight validates
the displayed schedules against official instances and an exact classical
reference. The compact-order classical tabulation scope remains explicit.
The VeloxQ frame also shows the separately labeled 162-bit hybrid improvement,
including the offline neighborhood-selection caveat. Routes remain 4:20/2:45.

Added docs/CATERING_PROBLEM.md as a self-contained explanation of final physical
semantics, lexicographic loss, anchor encoding, penalty proofs, no-idle equivalence,
Ising conversion, hybrid restriction and experiment domains. It is linked from
the README, documentation index and design. It changes no shared problem input,
solver formulation or frozen method campaign.


## 18 October — VeloxQ-driven LNS loop

With the VeloxQ owner raising the cap to 150, we turned the single LNS step
into a loop. Random block pairing was rejected after the free exact control
showed it misses the few pairs that matter; sweeping all 325 pairs with 40-bit
pair sub-QUBOs reached U=7/6/7 from VeloxQ's own U=9/11/13 plans. VeloxQ then
ran the same loop: 2,000 steps stalled at 2,022 bits, 20,000 steps converged.
Final U=7/6/7 at 486/998/2,022 bits, one meal lot better than 30-second CP at
998 and 2,022, equal to the exact control, still behind 240-second CP. Five of
71 submissions failed on connection errors; we kept their pairs unchanged and
added a pause between submissions. Ledger 66→137.
[Study](docs/CATERING_VELOXQ_TUNING.md#veloxq-lns-loop-18-october-a-veloxq-driven-pipeline).

After the loop, the release check passed all 13 stages again on a fresh clone
of `aa658aad`; the [review receipt](output/catering-submission-review-v1/verification.json)
now records that commit. The check made no service call.


## 18 October — Investment what-if

To use the model as a decision tool, we changed one resource at a time in the
12-customer S3 lunch and reran the raw-input CP reference (240 s, two seeds,
identical results). Repairing C2 or adding a third cooker only removes one
discarded portion (U stays 5); a second prep station or a cook-only worker
changes nothing; one flexible worker for prepare, cook and pack cuts missed
lots 5→3, i.e. 20 more meals. A second packing line is outside the core
profile and is reported as unsupported. We deliberately did not retrain QAOA
or VQE for these variants: the flexible worker grows the program register
8.3× (18,182→150,080), so the answer comes from the classical reference.
[Study](docs/CATERING_INVESTMENT.md).
