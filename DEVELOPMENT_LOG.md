# Development log

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
