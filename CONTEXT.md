# Current working context

Updated 17 October 2026. Active project: **Axion Kitchen**, the catering Stage 2
extension. Start with [README.md](README.md) and the [documentation index](docs/README.md).
The prior running transcript is retained [in the archive](docs/archive/2026-10-17/CONTEXT_BEFORE_CLEANUP.md).
Dated work belongs in [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md).

## Scope and ownership

One project targets the main award and integrated VeloxQ prize. Quantum methods
remain central, with classical references on declared domains. This chat owns
foundation/classical integration and presentation; other people own QAOA, VQE
and VeloxQ experiments. The user has now asked this chat to improve the VeloxQ track too; see docs/CATERING_VELOXQ_TUNING.md. Do not run QAOA/VQE training or QPU jobs.
Do not message their chats without direct authorization.

Keep objectives, coefficients, encoding, variable order, frozen workloads and
result hashes unchanged while other owners run. Additional solver-side conditioning uses separately hashed inputs and preserves existing runs. If a necessary model change
would require reruns, tell the user before changing that contract.

## Current evidence

- Stage 1 actual simulator schedules: A=4h, B=8h; root schedule JSONs match the
  selected retained solver outputs.
- Catering cell: 32 legal programs, 3 idle bits, 35 data qubits, 1,045 sector
  states and 59 physically feasible states. Independent references agree on
  (U,W,B,R)=(0,0,2,2). All six QAOA trials and both simple controls find it.
- Eight larger final pilot plans: six attain their final offered-pool optimum;
  all trail raw-grid CP. Final-step controls tie. No quantum advantage follows.
- Actual initial VeloxQ service jobs exist at 512/1,024/2,048 variables; see
  [the owner report](docs/catering-methods/VELOXQ.md). The representation comparison is
  integrated in the studio and benchmark browser. This chat added seven service jobs (36,640 quota units, reported USD0).
  Idle elimination returns 512/512 valid at actual widths 486/998/2022; CP/SA
  still produce better schedules. The reconciled shared ledger has 61 attempts.
- Karina QAOA campaign is merged: 400 runs independently checked. Frozen p3
  multi-angle XY reaches each held-out offered-pool optimum in 10/10 seeds at
  both budgets; exact simulator training, with a full-kitchen restriction gap.
- VQE primary held-out CSV medians are about 12.4%/12.8% optimum probability
  with 10/10 and 9/10 sampled hits. Five exported cell/S0–S3 plans are independently
  checked. QAOA/VQE budgets and shots differ; no matched-budget winner is claimed.
- No catering physical-QPU result.

Use [PROJECT_DESIGN.md](PROJECT_DESIGN.md) for the mathematics and
[CATERING_QUALITY.md](docs/CATERING_QUALITY.md) for exact statuses and limits.
The current fixtures have empty previous plans, so R=B. Monetary costs,
ingredient/holding/power capacities and interrupted cooking are disabled.

## Presentation

Keep the pixel kitchen style and concrete scheduling language. Avoid slogans,
vanity qubit counts and invented results. The audience should understand the
orders, choices, constraints and score before hearing solver names.

- Viewer: `PORT=4192 npm run dev`, then `/catering/`. It holds at the final
  service outcome by default; looping is opt-in. The clipboard can jump to
  the outcome, and evidence-download failures have a retry action.
- Private studio: `.venv-stage2/bin/python scripts/serve-catering-showcase.py --port 4193`.
- Video script: [CATERING_VOICEOVER.md](docs/CATERING_VOICEOVER.md).
- Live script/operator cues: [CATERING_LIVE.md](docs/CATERING_LIVE.md).
- Questions: [CATERING_QA.md](docs/CATERING_QA.md).
- Benchmarks: `/catering/benchmarks/` exposes all 400 QAOA runs, 61 service
  attempts, VQE grids, checked exports and source hashes. No optimizer runs there.
- Current v3 stills: ignored `output/playwright/catering-showcase-v3/`. Existing
  silent v2 cut predates these results and scaling; record a new final cut.

The opening screen states full implemented scope, then introduces the small
example. Results compare both quantum methods with their budgets; scaling
distinguishes portfolio limits from service width. Fresh local execution reuses
the selected trained p3 angles, samples the exact one-hot sector and
checks raw bitstrings. It is neither retraining nor a generic dense 35-qubit
statevector. Retained replay, fresh sampling and manual interventions keep
separate labels. Chapter holds pause animation, not the speaker's allotted time. R starts an
independent rehearsal clock. Both speaker docs are generated from story.json;
run npm run docs:write after edits.
Method emphasis is fixed: trained QAOA live, VQE as an unequal-budget ansatz
comparison, and the VeloxQ equivalent-representation study. The v4 recording
sheet and safe still-only capture route are prepared; no new video is recorded.
The portable release checker covers archives, math, exports and three fixed-seed
local sampling executions. Actual human voiceover/rehearsal, upload and final
authorized publication/submission remain open.

## Repository and release

The user authorizes ordinary private-main pushes. Fetch before pushing and
preserve teammate work. Keep GitHub private until the final release step.
The user explicitly requested deployment and push to origin/main. Production
now routes the root to /catering/ and preserves the Stage 1 viewer at /baseline/.
A main push triggers the configured static deployment, which copies only
`presentation/`; draft studio assets live under `scripts/`.

Cleanup has started: short active README/context/presentation plan, documentation
index and archived snapshots. Both speaker scripts have one chapter source,
and a read-only demo preflight checks frozen inputs. Continue consolidating
navigation and superseded presentation instructions first. Preserve frozen JSONs, manifests, historical experiments,
root required deliverables and untracked `output/catering-graphics/`. Do not
rewrite history or delete evidence. Refresh docs and run relevant checks.

Official deadline: 18 October 15:00 UTC+2; live presentations start 18:00, with
the assigned slot still to confirm. Video ≤5min; live ≤3min plus about 2min Q&A.
Use [the submission checklist](docs/STAGE2_SUBMISSION.md) for all 30 points and
release gates. Public access, the video URL and actual submission need separate
verification; a local build is not a submission.
