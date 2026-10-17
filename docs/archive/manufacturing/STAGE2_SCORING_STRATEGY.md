# Stage 2 scoring strategy

**Historical strategy; implementation now exists.** The user subsequently
authorized manufacturing entry refinement. Read [STAGE2_ENTRY.md](STAGE2_ENTRY.md)
for the current definition, measured 18–34-qubit study, exact counts, offline
precision-safe SDK files and submission evidence. The proposal below records
the earlier decision process; it is not the current work-status checklist.

Research and recommendation, 17 October 2026. This is a proposed next-work plan,
not a new experiment, performance result, release decision or claimed jury score.

## Decision

Make the current extended scheduling core the scientific centerpiece. Improve
its measured solution quality and explain the exact cost of restricting its
search space. Use the large synthetic factory as the application demonstration.
Add an industrial-data case only after the integrated core and submission
deliverables are secure.

The central question is: how much scheduling realism can we retain in a compact
QUBO, and what solution quality does each reduction and solver actually deliver?
The practical story can be recovering production commitments under changing
conditions. Recovery integration is a further result to establish: the saved
short-window advice currently worsens full-factory outcomes.

## Authority and scoring

The local organizer document, `Quantum_Hackathon_2026_ERP_Challenge.pdf`, sections
3, 5 and 11, is the source of the scoring below. Both PDFs were read; the Stage 2
requirements on challenge page 3 were also visually inspected. The organizer's
[live event page](https://www.qaif.org/contests/qpoland-quantum-hackathon)
currently agrees on submission by **18 October, 15:00 Warsaw time**.

Stage 1 is an eligibility gate. Its selected schedules are optimal on the two
official instances, but that alone does not establish maximum marks for the
extension. Quantum advantage, physical-QPU execution, industrial data and use of
every suggested extension are not stated requirements. Section 5 expects the
extended model, formulation, solver comparisons and scaling to form one integrated
result. Decomposition is explicitly among the suggested approaches.

| Criterion | Maximum | Next concrete evidence |
|---|---:|---|
| QUBO formulation correctness for quantum implementation | 5 | One extended model, exact polynomial, constraint/penalty proof, independent decoding checks, and precise reduction scope |
| Solution quality against reference/classical baseline | 5 | Same-instance comparisons for the actual quantum/hybrid output, plus feasibility, reference bound, gap and full runtime |
| Creativity and complexity of extension | 5 | Explain coupled assembly, machine choices, skills/calendars, setups and due dates through one operational example |
| Development log | 3 | Curated dated decision trail, including rejected methods and what was learned |
| Project Design | 3 | Reproducible model specification, variables, objective, assumptions, methods and interfaces |
| Demo video | 3 | At most five minutes; fresh launch/result, code explanation, decisions and limitations |
| Live presentation and answers | 3 | Three-minute demonstration plus prepared answers for roughly two minutes of questions |
| Consistency of log, code and presentation | 3 | One manifest linking claims, input/source hashes, actual runs, charts, commands and scripts |
| **Total** | **30** | **15 technical/application points and 15 documentation/defense points** |

These are maxima available, not points already awarded or a prediction of the
jury's assessment.

## Bit 1: formulation correctness, 5 points

Use the deterministic pump scheduling cell already in `window_qubo.py` and the
operation-pool compiler. Its declared core has alternative machines, qualified
workers, calendars, worker travel, component precedence and assembly joins,
transport minimum lags, metric machine-family setups and terminal due dates.
Its integer objective is `(H+1)*weighted_terminal_tardiness + makespan`.

Prepare one worked operation-choice example and one two-choice conflict. Explain
exactly which bits select machine/worker/start, why exactly one assignment must be
chosen, and why the nonnegative objective bound B permits penalty P=B+1. Check
literal QUBO energy against decoded scheduling objective and an independent raw
CP model. Use exhaustive tiny cases to support the general construction.

Separate four different operations: exact unary/support pruning, lossy time-grid
coarsening, lossy candidate-pool restriction, and exact conditional substitution
inside that retained pool. The existing raw compiler requires metric setup times
and uninterrupted machine availability when setup modeling is enabled; it cannot
be presented as supporting arbitrary changeovers and outages together.

For each feature report variables AND couplers, plus preprocessing and circuit
depth where relevant. A feature costing zero extra bits can still add many
interactions. Never call the full 1,489-bit master a 21-qubit global solution:
21 is the maximum observed local circuit register in the longer search.

## Bit 2: solution quality, 5 points

This is the main technical improvement opportunity. A CP reference can prove
what is achievable, but its best plan is not automatically the quantum method's
solution. Report them in different rows on the identical model.

Saved 32-operation/grid15 example, checked from the retained run summaries:

| Quantity | Value |
|---|---:|
| Raw-model CP optimum and restricted-pool CP optimum | 908,670 |
| QAOA final objective, seeds 7/13/29 | 1,103,205 |
| QAOA excess over that objective optimum | 21.41% |
| CP reference / QAOA makespan | 840 / 840 minutes |
| CP reference / QAOA weighted terminal tardiness | 630 / 765 |

Matching the reference's makespan does not establish optimality for the combined
objective. The reference prioritizes tardiness, so its makespan also must not be
called an independently proved minimum-makespan solution without a separate proof.
The direct classical proposal and uniform controls reach the same QAOA objective.
The known candidate pool contains the optimum here: search is the remaining loss
at this grid. Existing 256-block conflict-closure search has already been tried;
simply running that unchanged method longer is not the proposed next experiment.

First test candidate neighborhoods with an exact conditional optimizer. Consider
coordinated critical-chain/assembly changes and multiple choices per operation,
with boundary resource occupation retained. If exact optimization of those
neighborhoods cannot improve the incumbent, redesign their construction before
tuning QAOA. If it can, compare QAOA with X versus one-hot-preserving XY mixers,
SA, uniform sampling, proposal-only and exact conditional controls on the same
saved subproblems. Use a small fixed development budget; reserve fresh instances
and seeds for evaluation after selection. Count angle optimization and classical
proposal costs, not just final shots.

The existing XY/W experiment is useful: mean pool-optimum probability is 13.42%
versus 2.5% for uniform sampling within the same one-hot domain, on one eight-qubit
case across three seeds. It is an exploratory concentration result, with a
restricted-pool loss and classical training costs; it is not a runtime advantage
over classical scheduling.

Show makespan and tardiness separately alongside objective gaps. Grid15 already
costs 15.38% relative to the minute-grid optimum on the saved two-pump model;
compression loss and solver loss must not be merged or hidden.

Evidence: `docs/STAGE2_PLANNING_CORE.md`,
`output/stage2-search/operation-sector-blocks32-long-mac-v1/summary.json`,
`output/stage2-search/operation-sector-blocks32-long-mac-v1/qaoa_xy-7.json`,
`docs/STAGE2_RESULTS.md`, and `docs/SOLUTION_QUALITY.md`. This research inspected
saved evidence and source; it did not rerun the campaigns.

## Bit 3: creativity and complexity, 5 points

The current work already has enough breadth to support this criterion. Explain
one coupled scheduling problem: an apparently attractive machining decision can
delay a matching component, occupy a needed worker or force a costly setup, then
delay assembly and a customer deadline. Demonstrate the interaction through
checked schedules and an ablation, rather than counting simulator features.

The full factory is synthetic. A real manufacturing problem and real industrial
data are different claims. A real-data case can strengthen practical relevance,
but a full company deployment or partner is not required by the rubric.

Best candidate found: Deliktas et al.'s
[cell-scheduling dataset article](https://pmc.ncbi.nlm.nih.gov/articles/PMC10751839/)
describes 43 instances. Its industrial-derived instance #43 has 58 jobs, 269
operations, 41 physical machines and four cells, including family setups,
intercell transport, due dates and reentrant routes. Other instances include
generated/adapted information; do not describe all 43 as factory measurements.
The [dataset](https://data.mendeley.com/datasets/rtzby7pv7m/1) is labeled CC BY 4.0.

Begin with a documented bounded subset or a scheduling window. Preserve each
selected job's full route and relevant alternatives, or explicitly freeze and
document the outside work. Keep the same data and objective in CP and QUBO paths.
Validate decimal time units, repeated machine visits, parallel-machine expansion
and setup semantics. Report invented downtime events separately from source data.
This is a proposed adapter; no dataset files or complete import were validated
in this research.

Alternative: [flexible-packaging scheduling data](https://data.mendeley.com/datasets/h66hb89k6z/1),
published as six XLSX files with machine, routing, material, product and dynamic
order information, also labeled CC BY 4.0. Its record is promising but does not
by itself verify calibration, historical breakdown coverage or a ready solver
adapter. The metal-manufacturing case is the closer match to the current entry.

## Bits 4–8: documentation and defense, 15 points

For the development log, lead with a readable chain of decisions: baseline,
extended model, encoding, observed failures, redesign, selected results. Link the
bulk experiment archive. Record why large classical factory results cannot be
attributed to the small quantum circuits.

For Project Design, specify one authoritative problem, objective hierarchy, units,
constraints, variables and solver flow. Show a complete input-to-schedule example.
Distinguish the deterministic planning model from the physical simulator and the
restricted candidate pool. Make the mathematical explanation consistent with the
actual implementation and penalty conventions.

For the five-minute video, aim for: 30 seconds operational problem; 60 seconds
fresh run; 90 seconds variables/QUBO/code; 60 seconds reference and reduction
results; 60 seconds decisions, negative results and limits. Show a new local
execution clearly separately from saved factory replay.

For the three-minute live slot, use: 20 seconds problem; 40 seconds fresh launch
and result; 50 seconds formulation/reduction; 45 seconds same-model comparison;
25 seconds findings. Rehearse to the actual timing. Prepare answers about penalty
choice, preprocessing, candidate-pool loss, quantum contribution, simulation versus
hardware, and what happens as the problem grows.

For consistency, choose a small claims table with exact artifact pointers and
model scopes. Audit every number in the presentation against it. In particular:
full factory controller versus quantum selector; grid15 versus minute-grid;
full-domain versus pool optimum; global master bits versus local qubits;
classical cost versus quantum sampling; 32 orders/240 hours versus 96 hours.

## Research basis for method choice

Do not choose a supposedly universal best quantum optimizer first and then search
for an application. Select the operational decision and evaluation model, then
compare formulations and solvers under that model.

Established relevant methods include
[time-indexed scheduling and pruning](https://arxiv.org/abs/1506.08479),
[warm-start QAOA](https://quantum-journal.org/papers/q-2021-06-17-479/), and
[graph-controlled feasible scheduling mixers](https://arxiv.org/abs/2311.04100).
They motivate experiments; their results do not establish performance on our model.
The current XY mixer preserves the makespan one-hot sector, not every scheduling
resource constraint. A richer fully feasible mixer would require its own
correctness/connectivity argument and circuit-cost measurement.

VeloxQ offers a separate award and a natural larger-master backend. Its
[primary paper](https://arxiv.org/abs/2501.19221) describes conventional-compute
deployment; using it is not physical quantum execution. It would be useful to
compare the same medium/large scheduling QUBOs against SA and raw CP, including
network and decoding costs. Existing remote-backend holds remain in effect;
no service run was part of this research.

## Work order until submission

1. Fix the centerpiece and its claims table. Stop expanding factory mechanisms.
2. Spend a bounded block on the quality bottleneck: exact-neighborhood diagnostic,
   then a small quantum/classical comparison only if the neighborhood offers value.
3. Add the industrial-data adapter only if it fits without displacing validation
   or submission work. A checked subset is a valid result with a declared scope.
4. Produce a same-model result table and the variable/coupler/accuracy frontier.
5. Curate Design and Development Log around those results.
6. Reserve the final six hours before the deadline for clean reproduction, claim
   audit, recording and rehearsal, repository/submission checks and upload margin.

If no better quantum outcome emerges in the bounded research block, preserve the
negative comparison and present the verified integrated extension honestly.
Do not let uncertain extra performance consume guaranteed deliverable work.

The required public MIT repository, both baseline JSON files, README with AI-use
disclosure, Development Log, Project Design, video link, team declaration and form
submission need a final live check. Existing local notes are not proof that those
external submission duties are complete.
