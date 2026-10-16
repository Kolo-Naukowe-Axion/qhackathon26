# Literature for the Stage 2 QUBO solver

Researched 16 October 2026. Ranked for the proposed MetalTech environment in
[Stage 2 environment](../docs/STAGE2_ENVIRONMENT.md): flexible manufacturing, physical transport, finite
buffers, workers/tools, energy and causal disruption recovery. This is a targeted
reading guide, not a systematic review or a claim that these methods solve our
full model. The environment is still a blueprint.

## Main finding

The closest architectural precedent is **QUBO plus constraint programming in
large-neighborhood search**. The closest modeling precedents cover flexible
machines, AGVs and rescheduling. Compact constraint transformations and penalty
design are equally relevant to making the resulting QUBOs solvable.

Our recommendation is to investigate both a direct formulation and structured
recovery subproblems while retaining the full factory rules in the environment.
Decomposing the solver does not require deleting mechanisms from the factory.
No located source establishes an exact, scalable QUBO for our entire combination
of BOM joins, blocking, batteries, individual resources, rework and observation-
dependent decisions.

## Read these first

| Priority | Reference | Main use here |
| --- | --- | --- |
| 1 | Zhang, Lo Bianco & Beck (2022) | Architecture: QUBO-guided large-neighborhood search with CP |
| 2 | Pichugina, Tan & Beck (2024) | Smaller correct QUBOs through constraint transformation |
| 3 | Geitz et al. (2021 preprint) | Joint production/AGV formulation and classical comparison |
| 4 | Schworm et al. (2024), multi-objective rescheduling | Recovery after failures/urgent jobs; schedule stability |
| 5 | Deleplanque, Pérez Armas & Aggoune (2026) | Machine availability, tighter horizons, warm starts |
| 6 | Pawłowski et al. (2025; revised May 2026) | VeloxQ benchmark regimes and timing conventions |
| 7 | Verma & Lewis (2020 online; 2022 issue) | Penalty magnitude and partitioned slack ranges |
| 8 | Venturelli, Marchand & Rojo (2015 preprint) | Foundational scheduling QUBO and pruning |

### 1. Solving Job-Shop Scheduling Problems with QUBO-Based Specialized Hardware

Jiachen Zhang, Giovanni Lo Bianco and J. Christopher Beck. **ICAPS 2022,
404–412**, peer-reviewed. [Publisher and abstract](https://ojs.aaai.org/index.php/ICAPS/article/view/19826),
[DOI](https://doi.org/10.1609/icaps.v32i1.19826),
[full PDF](https://cdn.aaai.org/ojs/19826/19826-40-23839-1-2-20220613.pdf).

Studies direct formulations and a hybrid LNS method. Its specific division of
labor matters: **single-machine rank QUBOs guide neighborhoods; CP solves the
multi-machine scheduling problem**. It reports competitive results on larger
JSPs with a Digital Annealer in the loop.

**Use:** compare QUBO-guided neighborhood generation with our proposed executable-
bundle selection. **Limit:** these are different architectures, and neither the
paper's empirical results nor its ordinary JSP model certify our full factory.
QUBO/CP hybridization itself is established prior work.

Evidence inspected: publisher abstract and indexed primary PDF text; this entry
is not a complete reproduction of the algorithm or experiments.

### 2. Deriving Compact QUBO Models via Multilevel Constraint Transformation

Oksana Pichugina, Yingcong Tan and J. Christopher Beck. **2024 preprint**.
[Paper](https://arxiv.org/abs/2404.03610),
[full text](https://arxiv.org/html/2404.03610v1).

MLCTS derives penalties with fewer ancillary variables and gives sufficient
conditions for compact formulations. The useful distinction is between valid
penalties and generic conversion through binary slack. Read Sections 2.3–2.5,
3 and 4 for construction rules.

**Use:** inspect buffer, energy, budget, assignment and ordering constraints
individually before introducing slack bits. **Limit:** its conditions do not
make arbitrary inequalities quadratic without auxiliaries. Savings must be
demonstrated for our actual rows; its numerical examples are not scheduling
experiments.

Evidence inspected: primary full-text definitions and construction discussion.

### 3. Solving the Extended Job Shop Scheduling Problem with AGVs — Classical and Quantum Approaches

Marc Geitz, Cristian Grozea, Wolfgang Steigerwald, Robin Stöhr and Armin Wolf.
**2021 preprint**. [Paper](https://arxiv.org/abs/2109.04830),
[full PDF](https://arxiv.org/pdf/2109.04830).

Formulates production and AGV transport using CP and QUBO, including empty
vehicle repositioning between consecutive transport tasks. This is unusually
close to our physical-logistics requirement. Its Set6 comparison favors CP:
the reported CP solution has makespan 39, versus 57 from the D-Wave hybrid
configuration and 53 from the Digital Annealer configuration under their
different reported budgets.

**Use:** transport alternatives, vehicle continuity and an independent CP model.
**Limit:** a transport-time model does not automatically enforce our bridge
collisions, buffer reservations, charging or blocking semantics. The results
also illustrate why an impressive QUBO size is not sufficient evidence of a
useful solver.

Evidence inspected: primary PDF modeling passages and experimental table.

### 4. Multi-objective rescheduling of job shop scheduling problems in manufacturing using Quantum Annealing

Philipp Schworm, Xiangqian Wu, Matthias Klar and Jan C. Aurich.
**Manufacturing Letters 42 (2024), 5–10**, peer-reviewed.
[Article](https://www.sciencedirect.com/science/article/pii/S2213846324001287),
[DOI](https://doi.org/10.1016/j.mfglet.2024.09.066).

Uses a binary quadratic rescheduling model after urgent arrivals or machine
failures. Penalizes changes to planned start times and machine assignments
alongside production performance.

**Use:** define and measure plan churn against the pre-disruption schedule.
**Limit:** its description of encouraging earlier starts should be checked
against the precise makespan objective we implement; early-start surrogates
are not generally identical to minimizing maximum completion time. Its
comparisons do not establish an advantage over our matched full-model CP
reference, and deterministic rescheduling is not a nonanticipative stochastic
policy.

Evidence inspected: primary article framework, application scenario and conclusion.

### 5. Quantum annealing heuristics for the job shop scheduling problem with availability constraints

Samuel Deleplanque, Luis Fernando Pérez Armas and Riad Aggoune.
**Journal of Heuristics 32, article 19 (2026)**, published 4 May 2026,
peer-reviewed. [Publisher](https://link.springer.com/article/10.1007/s10732-026-09594-5).

Combines machine unavailability modeling with constructive heuristics, tighter
horizon bounds and reverse-annealing warm starts. The abstract reports a 29.9%
variable reduction and 46.4% fewer quadratic terms from the tighter horizon.

**Use:** quantify how valid incumbents and availability-aware bounds reduce
our recovery domain before changing the encoding. **Limit:** reverse annealing
is backend-specific, and known unavailability intervals do not model hidden
future failures. Respect preemptive versus nonpreemptive variants when choosing
references.

Evidence inspected: publisher abstract and public notes; full publisher article
is subscription content. Reported percentages have not been independently
reproduced.

### 6. VeloxQ: A Fast and Efficient QUBO Solver

J. Pawłowski et al. **2025 white paper, v2 dated 4 May 2026**.
[Version 2](https://arxiv.org/html/2501.19221v2),
[benchmark repository](https://github.com/quantumz-io/velox-data).

The revised paper explicitly identifies itself as a technical white paper,
describes VeloxQ as a conventional-hardware physics-inspired solver, and
distinguishes reference gaps from certified optimality gaps. Sections IV and
X are particularly useful for methodology. Largest-size results concern sparse
instances, and the solver is proprietary.

**Use:** reproduce timing boundaries, report AutoTune versus custom settings,
and benchmark our own scheduling-generated instances. **Limit:** its sparse
scale and energy results do not imply equivalent performance on dense,
penalty-heavy scheduling models. Returned solutions are not certified optima.

Evidence inspected: revised primary full text, including methodology. Prefer
v2 over search snippets quoting the earlier version's larger headline count.

### 7. Penalty and partitioning techniques to improve performance of QUBO solvers

Amit Verma and Mark Lewis. **Discrete Optimization 44, Part 2 (2022), 100594**;
online publication in 2020.
[Publisher](https://www.sciencedirect.com/science/article/abs/pii/S1572528620300281),
[DOI](https://doi.org/10.1016/j.disopt.2020.100594).

Examines penalty magnitude and partitions an inequality's slack range into
smaller problems, reducing auxiliary variables within each partition.

**Use:** investigate tight penalty bounds and range partitioning for cumulative
resource constraints. **Limit:** partitioning introduces multiple solves;
cover the full admissible range if preserving equivalence. A per-partition
variable reduction need not reduce total work. Do not treat a local
penalty estimate as a universal correctness proof.

Evidence inspected: primary publisher metadata, indexed article discussion
and examples. The issue year differs from the year often used for its online
publication.

### 8. Quantum Annealing Implementation of Job-Shop Scheduling

Davide Venturelli, Dominic J. J. Marchand and Galo Rojo. **2015 preprint**.
[Paper](https://arxiv.org/abs/1506.08479).

Foundational time-indexed scheduling QUBO with preprocessing, embedding,
variable pruning and horizon-search strategies, tested on small hardware
instances.

**Use:** establish a transparent direct formulation and explain start-window
pruning and makespan-feasibility search. **Limit:** its base JSP does not
contain our logistics, resource state or stochastic recourse. A heuristic's
failure to find a zero-penalty sample cannot certify horizon infeasibility.

Evidence inspected: primary abstract; detailed adaptation requires reading
the formulation and validating it on our own small cases.

## Solver methods and further modeling references

### 9. Iterated Tabu Search for the Unconstrained Binary Quadratic Optimization Problem

Gintaras Palubeckis. **Informatica 17(2) (2006), 279–296**, peer-reviewed.
[Publisher](https://www.informatica.vu.lt/journal/INFORMATICA/article/441/info),
[PDF](https://www.informatica.vu.lt/journal/INFORMATICA/article/441/file/pdf).

Provides a concrete classical QUBO search method, with experiments up to 7,000
variables. **Use:** a substantive tabu-search baseline with restarts and
incremental objective changes. **Limit:** this is a historical algorithmic
reference, not a claim of current state-of-the-art performance. It should be
benchmarked alongside SA and VeloxQ on the identical coefficients.

Evidence inspected: publisher metadata and primary PDF abstract.

### 10. High-performance combinatorial optimization based on classical mechanics

Hayato Goto et al. **Science Advances 7 (2021), eabe7953**, peer-reviewed.
[Article](https://doi.org/10.1126/sciadv.abe7953).

Develops ballistic and discrete simulated bifurcation, with numerical update
rules for classical dynamics. **Use:** a GPU-friendly physics-inspired
comparison method. **Limit:** performance on Ising/Max-Cut benchmarks does not
establish physical feasibility or schedule quality on our penalized model;
field terms, scaling and tuning must be handled consistently.

Evidence inspected: primary methods and limitations discussion.

### 11. Tabu-Enhanced Simulated Bifurcation for combinatorial optimization

Xian-Zhe Tao et al. **Communications Physics 9, article 100 (2026)**,
published 10 February 2026, peer-reviewed.
[Article](https://www.nature.com/articles/s42005-026-02538-2),
[authors' implementation](https://github.com/Tao-qubit/Tabu-Enhanced-Simulated-Bifurcation).

Adds search-history-based escape behavior to simulated bifurcation. **Use:**
a recent open implementation candidate if standard SB stagnates. **Limit:**
reported gains concern Max-Cut and particle tracking, not our scheduling
constraints; include tuning effort in comparisons.

Evidence inspected: primary abstract, methods and code-availability statement.
The linked implementation has not been installed or tested here.

### 12. Preprocessing of Unconstrained Quadratic Binary Optimization

Endre Boros, Peter L. Hammer and Gabriel Tavares. **RUTCOR report 10–2006**.
[Author research report](https://users.cecs.anu.edu.au/~pcarr/qpbo/BorosRRR102006.pdf).

Studies implications, roof duality, probing and related preprocessing that can
produce bounds, variable fixings and decomposition. **Use:** test exact
reduction after compiling the QUBO, in addition to scheduling-domain pruning.
**Limit:** distinguish weak from strong persistency; simultaneous fixings need
a jointly valid guarantee, and reductions preserving some optimum need not
preserve all optimal schedules.

Evidence inspected: primary report metadata and abstract-level description.

### 13. A Multilevel Approach For Solving Large-Scale QUBO Problems With Noisy Hybrid Quantum Approximate Optimization

Filip B. Maciejewski et al. **2024 preprint**.
[Paper](https://arxiv.org/abs/2408.07793).

Uses quantum-assisted subsolvers inside a multilevel optimization framework.
The reported global instances reach approximately 27,000 variables, with
individual QPU problems at most 82 qubits. **Use:** an alternative decomposition
direction and a small genuine quantum subroutine within a larger solver.
**Limit:** the global variable count is not the QPU size, and graph coarsening
does not automatically preserve our resource/transition semantics.

Evidence inspected: primary abstract; not a full algorithm audit.

### 14. Solving flexible job shop scheduling problems in manufacturing with Quantum Annealing

Philipp Schworm, Xiangqian Wu, Moritz Glatt and Jan C. Aurich.
**Production Engineering 17 (2023), 105–115**, online July 2022,
peer-reviewed.
[Article](https://link.springer.com/article/10.1007/s11740-022-01145-8).

Useful formulation comparison across binary, discrete and constrained quadratic
models and hybrid approaches. **Use:** machine alternatives and the cost of
forcing constraints into a BQM. **Limit:** CQM/DQM hybrid results are not
interchangeable with an explicit QUBO backend result, and hybrid runtime must
not be attributed entirely to a QPU.

Evidence inspected: primary formulation/framework and conclusion passages.

### 15. Evaluation of Quantum Annealing-based algorithms for flexible job shop scheduling

Philipp Schworm, Xiangqian Wu, Matthias Klar and Jan C. Aurich.
**2024 preprint**, marked accepted for the 18th CIRP ICME conference.
[Paper](https://arxiv.org/abs/2408.15671),
[PDF](https://arxiv.org/pdf/2408.15671).

Focuses on when larger FJSSPs require hybrid solving and the distribution of
computation between solver components. **Use:** report what the QUBO backend
actually contributes to end-to-end recovery. **Limit:** avoid inferring a
general hardware crossover from one solver configuration or instance family.

Evidence inspected: primary abstract and PDF access; detailed numerical
thresholds have not been audited here.

### 16. Unbalanced penalization: A new approach to encode inequality constraints of combinatorial problems for quantum optimization algorithms

Alejandro Montanez-Barrera, Dennis Willsch, Alberto Maldonado-Romo and Kristel
Michielsen. **2022 preprint**.
[Paper](https://arxiv.org/abs/2211.13914),
[follow-up hardware study](https://arxiv.org/abs/2305.18757).

Avoids slack bits through asymmetric penalties. **Use:** an explicitly
heuristic encoding ablation when auxiliary variables dominate. **Limit:**
the original constrained optimum is not generally guaranteed to be the QUBO
ground state. Keep an exact-slack reference and independently check feasibility
and objective changes; fewer bits alone is not an exact reduction.

Evidence inspected: primary abstracts, including the follow-up's explicit
ground-state versus near-ground-state distinction.

### 17. From the Quantum Approximate Optimization Algorithm to a Quantum Alternating Operator Ansatz

Stuart Hadfield et al. **Algorithms 12(2) (2019), 34**, peer-reviewed;
2017 preprint. [Article](https://www.mdpi.com/1999-4893/12/2/34),
[preprint](https://arxiv.org/abs/1709.03489).

Designs mixers that preserve chosen feasible subspaces. **Use:** a small
quantum experiment preserving exactly-one bundle choices or selected ordering
constraints. **Limit:** an XY mixer preserving one-hot cardinality does not
also enforce transport, power, buffers and precedence. Establish feasible-state
connectivity and circuit cost for the constraints actually preserved.

Evidence inspected: primary design-criteria and hard-constraint discussion.

### 18. Scenarios and Policy Aggregation in Optimization Under Uncertainty

R. T. Rockafellar and Roger J.-B. Wets. **Mathematics of Operations Research
16(1) (1991), 119–147**, peer-reviewed.
[Article](https://pubsonline.informs.org/doi/abs/10.1287/moor.16.1.119).

Foundational progressive-hedging/scenario-aggregation reference connecting
decisions through information availability. **Use:** understand why our
scenario-specific plans need nonanticipativity. **Limit:** classical convergence
results cannot simply be carried over to binary scheduling with heuristic
QUBO subsolves. Quality revealed at decision-dependent QA completion also
requires an observation-history model beyond a fixed exogenous tree.

Evidence inspected: publisher abstract and metadata; the proposed QUBO use
is our inference.

### 19. Quantum algorithms for scheduling problems: a survey

Tino Werner and Freyja Ullinger. **EPJ Quantum Technology 13, article 31
(2026)**, published 19 March 2026, peer-reviewed review.
[Survey](https://link.springer.com/article/10.1140/epjqt/s40507-026-00494-y).

Maps scheduling variants, encodings, solver types, tested sizes and comparison
metrics. **Use:** discover adjacent primary papers and check evaluation
conventions. **Limit:** consult original papers for formulation correctness
and exact experimental details; this review does not verify our model.

Evidence inspected: primary survey introduction, formulation discussion and
scheduling entries. Method claims above cite the original research sources.

## What this suggests for our implementation

These are project recommendations inferred from the literature and our design,
not results reported by the papers.

1. **Keep a direct reference encoding.** Derive valid start domains for machine,
   mode and time choices, then measure their actual variable count, couplings
   and coefficient range. Existing 665,760 start choices are a partial blueprint
   count, not a complete QUBO. Tighten horizons only with bounds valid for the
   same objective and model; a makespan incumbent is not automatically a valid
   restriction for a tardiness/energy/risk objective.
2. **Investigate two hybrid architectures.** One uses rank QUBOs to guide a CP
   neighborhood, following Zhang et al. The other selects executable recovery
   bundles through QUBO, as proposed in our design. Compare them rather than
   treating them as the same published method.
3. **Close every neighborhood physically.** Fix entry state and account for exit
   stock, buffer reservations, AGV locations/SOC, worker/tool positions, setup
   family and wear. Merge or link alternatives whose interactions are not
   additive. Pairwise conflict edges alone cannot express every cumulative
   resource constraint or predecessor-dependent setup.
4. **Improve formulation before enlarging solves.** Apply domain pruning,
   justified compact penalties, exact QUBO preprocessing and bounded slack.
   Measure nonzero couplings and degree as well as binary count: squaring a
   capacity row or exactly-one group can introduce a clique among its variables.
5. **Derive penalty margins.** If the unpenalized objective lies in [L,U] over
   the entire encoded domain and every infeasible assignment has total penalty
   at least delta > 0, a multiplier greater than (U-L)/delta suffices, provided
   a feasible assignment exists and feasible assignments have zero penalty.
   This is a sufficient bound, not necessarily a practical numerical choice.
   Bounds only over feasible schedules are insufficient for this argument.
6. **Separate three comparisons.** Verify the encoding against exact tiny
   cases; compare VeloxQ/tabu/SA (and SB if practical) on identical QUBOs;
   compare complete causal recovery policies under equal planning budgets.
   Include generation, compilation, backend communication, repairs and checking.
   Report raw feasibility separately from repaired feasibility.
7. **Measure restricted-domain loss.** Solving a candidate pool exactly proves
   only its restricted optimum. Where possible compare it with an unrestricted
   reference for the same small full-rule environment. On larger cases retain
   incumbents/bounds and unsolved results. Do not silently replace missing
   logistics or stochastic rules with easier benchmarks.

Suggested reading sequence for immediate work: **1 → 2 → 3 → 4 → 6 → 7**.
Read **8 and 5** alongside direct horizon/pruning experiments, **9–11** for
classical solver comparisons, and **18** before scenario decomposition.

## Scope and open gaps

The search emphasized primary publisher pages, arXiv manuscripts and author
repositories available by the research date. Some entries were assessed at
abstract or selected-passage level, explicitly indicated above; no benchmark
was reproduced and no solver was installed or run for this review.

The most important remaining literature gap is an efficient exact treatment of
our **combined** batch/BOM/blocking/stateful-resource model with causal quality
recourse. The located papers are components and architectural precedents,
not evidence that an off-the-shelf formulation already handles that combination.
Further mechanism-specific research should follow the actual encoding obstacles.
