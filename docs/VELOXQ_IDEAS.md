# VeloxQ: initial formulation and presentation ideas

Status: proposed experiments, not measured solver results. Updated 2026-10-16 after reading the official specification.

## Stage 1: a visible path from QUBO to factory

Use VeloxQ to solve the 3×3 scheduling QUBO, with a real job record and independently checked schedule. Run the 2×2 QUBO with an actual quantum algorithm separately. Make the role of each method clear in the replay instead of attaching a solver logo to an illustrative answer.

Start with a time-indexed feasibility formulation at candidate makespan H:

- Binary variable x(job,machine,start) selects an operation start time.
- Exactly-one penalty per operation: `(sum(x) - 1)^2`.
- Capacity penalties couple starts that overlap on a machine.
- Precedence penalties couple starts that put a successor before its predecessor completes.
- Positive penalties make energy zero equivalent to feasibility inside H, provided the encoding/domain construction is correct.

Prune each operation's domain using earliest completion of its predecessors and the remaining processing chain. At H=8 the organizer gives 72 raw variables and 39 after this simple pruning. Reproduce and verify that count; do not call ordinary window pruning a novel reduction.

Search H systematically to minimize makespan. A heuristic solver's failure to return energy zero does not prove a horizon infeasible. Use exact classical reference schedules to establish the tiny instances' optimum and report solver outcomes honestly.

## The creative presentation layer

Once genuine run artifacts exist, add a formulation view that connects:

1. **Start windows → factory:** select an operation and show which starts were removed and why (predecessors or remaining work).
2. **Constraint → schedule:** select a violated QUBO term and highlight the corresponding machine conflict or precedence violation. Keep this separate from accepted feasible output.
3. **Sample → outcome:** select an actually returned bitstring and show decoded schedule, energy components, feasibility, and makespan. A low-energy infeasible sample remains visibly infeasible.
4. **Run → evidence:** show actual model size, SDK/backend settings, remote job id, repetitions, timing boundaries, and the classical reference gap.

This makes the integration inspectable. These overlays are planned; the initial factory/Gantt/evidence environment is the foundation, not an implementation of this entire list.

## Experiment discipline

- Compare raw and pruned encodings on exactly the same instance/objective and constraints.
- Compare feasibility rate, actual best feasible makespan, and model size; keep energy comparisons within a compatible formulation.
- Record wall time including upload/queue/result retrieval separately from solver-reported compute time, if available.
- Preserve the actual SDK parameters. Do not invent a seed control or reproducibility guarantee unsupported by the backend.
- Do not call an exact reference schedule a VeloxQ result. Do not infer quantum advantage from a tiny instance, GPU execution, or a single timing.
- Keep confidential tokens in the backend environment, never the viewer or committed run metadata.

## Stage 2 candidate to investigate next

Update, 2026-10-16: the user's ambition mandate led to the much richer working
proposal in `STAGE2_ENVIRONMENT.md` and the design iterations in
`STAGE2_IDEATION.md`. The single-disruption idea below is historical context;
the target now includes physical logistics, BOM assembly, energy, tooling,
quality and causal recovery. Investigate a closed recovery QUBO within that
environment, preserving explicit boundary state and reporting restricted-pool
gaps. This remains proposed solver work, not an executed integration.

One coherent direction is **replanning after a machine disruption while preserving work already done**: freeze completed/in-progress operations, solve the remaining schedule, and compare against a classical reference under the same outage/partial-state model. The factory can show the actual disruption and recovery schedules side by side.

Evaluate whether a compact residual QUBO gives VeloxQ a useful role relative to solving the full extended model. Measure quality, variable savings, repeated-run variability, and runtime across larger instances. This is a candidate, not a selected extension; formulation correctness and a realistic comparison take priority over adding more UI.

The official scoring requires the reduction/scaling experiments to apply to the extended model too. Also retain a smallest-correct-QUBO comparison for the baseline 3×3. Presentation polish cannot substitute for this substantive work.

Sources: `Quantum_Hackathon_2026_ERP_Challenge.pdf` §§4–5,11,15 and the [VeloxQ SDK](https://github.com/quantumz-io/veloxq_sdk). No remote VeloxQ jobs have been run for this plan.
