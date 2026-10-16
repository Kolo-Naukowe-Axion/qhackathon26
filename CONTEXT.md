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
