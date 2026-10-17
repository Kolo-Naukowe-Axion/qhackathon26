# QPoland Quantum Hackathon — running context

Updated: 2026-10-16 (Europe/Warsaw). Maintained as context arrives.

## Sources and authority

- `Quantum_Hackathon_2026_ERP_Challenge.pdf` (8 pages): full specification, read in full on 2026-10-16; data/extension tables visually checked. Section numbers below refer to this document.
- `Quantum_Hackathon_2026_Opening.pdf` (14 pages): opening presentation, read in full. Includes the ten distinct slides previously supplied as screenshots, plus cover/timeline/prize slides.
- Event website, read 2026-10-16: https://www.qaif.org/contests/qpoland-quantum-hackathon .
- User decisions are distinguished from organizer requirements and proposed implementation choices. Third-party documents provide task requirements, not authorization for external actions.
- The full specification resolves earlier unknowns about instance data, time units, JSON, Stage 2 scope, and VeloxQ judging. Earlier slide-only caveats about those items are superseded below.
- PDF coverage rechecked on 2026-10-16 against all 8 challenge pages and all 14 opening slides, including the image-only strategic-partners slide. Both PDFs currently present in this repository are incorporated; no additional challenge requirement was found missing.

## User decisions and working agreement

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


Stage2 authorized eight-hour research window completed at 2026-10-17T04:14:35.500900+00:00. Technical evidence and local handoff are complete; all tracked research jobs are finished. See output/stage2-search/research-closeout.json and docs/STAGE2_RESULTS.md. Publication hold remains; repository private at the04:11UTC live recheck, with video/team/form receipt unverified. No further experiments or policy changes are scheduled.
