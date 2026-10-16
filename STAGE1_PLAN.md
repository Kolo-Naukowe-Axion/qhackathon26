# Stage 1 plan — solve, verify, explain

Status: planning and presentation preparation, 2026-10-16. Both official PDFs have now been read and the exact datasets/JSON schema are known. The user authorizes environment work first, followed by the VeloxQ formulation and integration. Neither baseline solver run is complete.

Offline preparation is now implemented in `solver/stage1.py`: pruned fixed-horizon QUBOs, sample decoding/independent checking, exact classical references and coefficient exports. See [implementation details](docs/STAGE1_OFFLINE.md). Neither required-method run is complete; SDK handoff conversion remains untested in this repository environment.

## Proposed approach

Build a small, inspectable scheduling demonstration that shows how a binary solver result becomes a valid factory schedule. Use VeloxQ substantively for the 3×3 baseline and a separately demonstrated quantum algorithm for the 2×2 baseline.

1. Load the official instance data into one scheduling model. Express each operation, duration, machine, and predecessor explicitly.
2. Derive an encoding for each required method after checking the full specification. Preserve the allowed schedule space; do not assume permutation scheduling or discrete time without support. Reduce variables using valid bounds and proven redundant-variable elimination where helpful.
3. Solve the 2×2 QUBO using a compact QAOA circuit on a local simulator, subject to the official algorithm requirements. Save circuit settings, optimization history, sampled bitstrings, and the selected feasible sample. The full document explicitly requires a QUBO for this instance.
4. Formulate the 3×3 QUBO and solve it through the VeloxQ SDK. Save the submitted model, actual solver/backend settings, job identifier, raw returned samples, and decoded schedule. Use a small number of additional runs to check stability if needed.
5. Validate both schedules using an independent checker operating on decoded operations: all required operations appear once, durations are correct, machine intervals do not overlap, precedence holds, and reported makespan matches completion times. Validate the official JSON schema too.
6. For these tiny instances, independently determine the optimum with an exact classical method over the full allowed schedule space. Use this as a reference for quality and correctness, while preserving which schedules actually came from QAOA and VeloxQ. Do not replace a failed solver result with the reference and describe it as solver success.

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
- User authorizes WCSS work under the Axion quantum group. SSH login was verified, but the corresponding Slurm allocation has not been identified/validated; do not substitute unrelated allocations.
- Remote GPU work is contingent on an actual workload need and verified allocation. No solver execution or compute job submission has started.

The visual environment uses original Factorio/Stardew Valley-inspired pixel art, with linked replay, Gantt and validation/provenance views. The official document requires a strong, verified Stage 2 extension; the presentation is supporting evidence rather than a substitute.

Sources: organizer slides summarized in [CONTEXT.md](CONTEXT.md); [VeloxQ SDK](https://github.com/quantumz-io/veloxq_sdk) and [solver/backend documentation](https://github.com/quantumz-io/veloxq_sdk/wiki/solvers-and-backends), inspected 2026-10-16.
