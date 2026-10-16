# Stage 1 plan — solve, verify, explain

Status: both mandatory baseline methods have run locally, 2026-10-16. A was solved by a genuine four-qubit QAOA simulator circuit (4 h); B by classical QUBO simulated annealing (8 h). Both exported schedules pass independent checks and match exact optima. **User hold: do not use ODRA5 or VeloxQ for now; iterate locally.**

Current selected evidence is in `output/stage1-selected.json`, pointing to `output/stage1-local-ready/`; required root schedule JSONs are exported. Reproduce with `.venv/bin/python scripts/prepare-stage1.py --output output/new-stage1`. The refined p=3 quantum circuit passed all 40,960 validation measurements; the classical solver passed 5,110/5,120. See [refinement evidence](docs/STAGE1_REFINEMENT.md) and [implementation details](docs/STAGE1_OFFLINE.md). Service behavior remains unverified.

## Proposed approach

Build a small, inspectable scheduling demonstration that shows how a binary solver result becomes a valid factory schedule. The completed baseline uses local classical QUBO annealing for B and simulator QAOA for A. Substantive VeloxQ integration remains an intended later upgrade, after the user lifts the service hold.

1. Load the official instance data into one scheduling model. Express each operation, duration, machine, and predecessor explicitly.
2. Derive an encoding for each required method after checking the full specification. Preserve the allowed schedule space; do not assume permutation scheduling or discrete time without support. Reduce variables using valid bounds and proven redundant-variable elimination where helpful.
3. Solve the 2×2 QUBO using a compact QAOA circuit on a local simulator, subject to the official algorithm requirements. Save circuit settings, optimization history, sampled bitstrings, and the selected feasible sample. The full document explicitly requires a QUBO for this instance.
4. Formulate the 3×3 QUBO and solve it locally while VeloxQ is on hold. After the user lifts the hold, the intended SDK integration must save the submitted model, actual solver/backend settings, job identifier, raw returned samples, and decoded schedule.
5. Validate both schedules using an independent checker operating on decoded operations: all required operations appear once, durations are correct, machine intervals do not overlap, precedence holds, and reported makespan matches completion times. Validate the official JSON schema too.
6. For these tiny instances, independently determine the optimum with an exact classical method over the full allowed schedule space. Use this as a reference for quality and correctness, while preserving which schedules actually came from QAOA and classical annealing (or a future explicitly authorized VeloxQ run). Do not replace a failed solver result with the reference and describe it as solver success.

## Interesting, functional demonstration

Produce a compact report connecting each result across three views:

- Solver output: selected bitstring, energy, and method provenance.
- Factory schedule: a readable Gantt chart and calculated makespan.
- Verification: a checklist of constraints, comparison to the exact optimum, and any constraint violations in rejected samples.

Show a deliberately conflicting schedule separately so viewers can see what the independent checker catches. Label it as a demonstration fixture, not solver output. If an encoding reduction is used, show the variable/qubit count before and after and explain why it preserves correctness.

This makes the baseline understandable and convincing without expanding it into a second research project. The same model/checker can support Stage 2 if useful, but the extension need not reuse the baseline implementation.

## Required completion evidence

- Actual required-method runs for both instances.
- `schedule_2x2.json` and `schedule_3x3.json` in the official format.
- Independent feasibility checks and reference makespans.
- Reproduction commands and dependency versions.
- Dated development notes, formulation explanation, and AI-use disclosure.

Do not mark Stage 1 complete before both method-specific runs and both schedule validations succeed. Feasibility is the slide's explicit acceptance requirement; optimality is a quality target to verify, not an assumption.

## Compute and dependencies

- Prefer the local machine for tiny baseline work; choose the encoding to keep simulation practical.
- VeloxQ SDK access requires the platform API token; local H100 access is separate from access to the VeloxQ service.
- User authorizes WCSS work under the Axion quantum group. SSH and CPU association `hpc-iwowoj-1781179048` are now verified, including a successful short interactive network check. GPU allocation/quota is not established; do not substitute unrelated allocations.
- Local solver execution is complete for both baselines. No GPU is needed for them. Physical ODRA5 work is an optional hardware upgrade to the simulator result and uses separate IQM authentication; both remote backends remain on user hold; reported VeloxQ access has not been exercised.

The visual environment uses original Factorio/Stardew Valley-inspired pixel art, with linked replay, Gantt and validation/provenance views. The official document requires a strong, verified Stage 2 extension; the presentation is supporting evidence rather than a substitute.

Sources: organizer slides summarized in [CONTEXT.md](CONTEXT.md); [VeloxQ SDK](https://github.com/quantumz-io/veloxq_sdk) and [solver/backend documentation](https://github.com/quantumz-io/veloxq_sdk/wiki/solvers-and-backends), inspected 2026-10-16.
