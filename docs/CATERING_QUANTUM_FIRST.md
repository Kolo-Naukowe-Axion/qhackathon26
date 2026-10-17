# Catering: quantum-first method and current evidence

**Accepted direction — 17 October 2026:** the user approved optimizing for the
hackathon's judging criteria and targeting both the overall prize and best use
of VeloxQ through one integrated catering-production project. Demonstrating
quantum advantage is no longer an acceptance requirement. Keep a substantive
quantum method, the paired-meal mathematical contribution, rigorous references,
measured scaling and a polished evidence-backed demo. Standalone SAT/exact-cover
advantage research and unmotivated cluster expansion are parked. This overrides
the earlier advantage-seeking discussion below; that discussion is retained as
decision history, not the current roadmap.

The supplied challenge PDF Section15 lists2000PLNoverall and1000PLNbestVeloxQ;
it contains no stated mutual exclusion, but does not explicitly confirm that
one team may receive both. Target both criteria; simultaneous receipt remains
an organizer-policy question. No message was sent and no award eligibility is
guaranteed by this interpretation.

VeloxQ's role is to solve broader/larger instances or portfolios from the same
versioned production model, with the common decoder and physical checker.
Small overlapping cases permit direct same-QUBO comparisons with QAOA/VQE and
classical controls; larger scale cases expose quality/runtime/representation
tradeoffs. Record all cases, seeds or service replicates, raw feasibility,
objective tuples, reference bounds/gaps and end-to-end timings. A sponsor call
alone or a different problem disguised as a scale comparison is insufficient.
Budget-aware offline preparation may continue; the existing hold on calls,
uploads, token use and credit spending remains until separately lifted.

17 October 2026. The user clarified that the quantum method is the main project;
classical optimization provides validation and reference values. This supersedes
a classical-planner-first interpretation of the work split.

## Current runnable evidence and next gates

The local foundation is now implemented and frozen, with source snapshots:

| Evidence | What it establishes |
|---|---|
| output/catering-complete-cell-v3/ | All32legal programs of a small declared production cell,35data qubits (32choices+3idle),520couplers,1045one-hot states,59physically feasible states. Raw CP, offered-domain CP, independent raw subset audit and sector enumeration agree on U0,W0,B2,R2. |
| output/catering-foundation-v3/ | Four6customer event cases; fixed33/35/31/35qubit portfolios and nested128/256bit scale pools, with raw references, literal SA and exact/limited offered-domain CP. All4raw release references are certified optimal. |
| output/catering-paired-pilot-v1/ | Eight predeclared QAOA runs:4paired cases,2seeds,8portfolio updates,16parameter evaluations/update,2048shots/update. Quantum samples construct valid improving plans, but all8final plans remain worse than raw CP. |
| output/catering-v3-verification.json | Separate manifest, raw sample energy/validity, frequency, controller-update and final-plan rechecks. |
| output/catering-paired-circuit-audit-v1/ | One35qubit pilot circuit:272CXall-to-all,925CXon a synthetic57node heavy-hex topology. |
| output/catering-complete-cell-circuit-v3/ | Complete-cell p1circuit:702CXall-to-all,1914CXon the same synthetic topology. |

In the complete cell, all6predeclared runs (p1/p2, seeds2026/2027/2028,
64parameter evaluations and4096shots each) recover the certified optimum.
Initializer and mixer-only controls recover it too. These are exact-sector
simulator experiments and a correctness demonstration, not quantum superiority
or an IBM result. All sources, failed/invalid samples and control outcomes are
retained. The cell has explicit narrow preparation/attendance calendars and a
fixed-yield main recipe; it is not a cap hiding choices in the6customer study.

The larger pilot's final missed-meal counts for the two seeds are S0:3/4,
S1:5/5,S2:4/4,S3:5/5 versus certified raw minima2/3/2/3. Its initial fixed
quantum portfolios also lose opportunities even under exact optimization:
U5/7/5/6. This separates restriction loss from within-portfolio search loss.
The256bit scale pools match full raw tuples inS0/S2; S1retains an extra batch
and S3still misses one extra meal in its certified offered-domain optimum.
Different portfolio weights mean raw QUBO energies cannot be compared across
widths. Matched operational quality, not variable count, remains the gate.

The current V3contract and quick start describe additional quadratic objective
terms, one-hot idle data qubits, whole-meal service and per-batch disposal.
V2 remains immutable regression evidence; method owners opt into V3 explicitly.
The existing untracked catering viewer still exports foundation-v1 data. Its
green animation tests do not validate V3semantics or the mandatory-clean fix.
It must be ported before presentation. A backend demo receipt containing an
actual p1/seed2026QAOA sample is output/catering-complete-cell-demo-v3.json;
this is ready for UI integration, not a claim that the browser now uses it.
In the current V3fixtures previous_unstarted is empty, so R=B; the fourth
priority does not create an independent stability tradeoff in these inputs.
Next gates are VQE/standard-QAOA results on shared bundles, better large-kitchen
quantum quality, actual calibrated IBM compilation before spending, a bounded
authorized VeloxQ campaign, and the synchronized demo/video/public submission.
No service result or quantum advantage is claimed. Generic matrix-product-state
runtime probes are separate from these more connected QAOA circuits.

## Recommendation for winning the event

After rechecking the actual challenge PDF Section11 and the user's reported
mentor guidance, prioritize one finished, mathematically justified catering
extension rather than pivoting to a standalone SAT/quantum-advantage project.
The rubric assigns15of30points to formulation, solution quality and extension;
the remaining15cover development log, project design, video, live presentation
and consistency. Quantum advantage is not an explicit eligibility/scoring gate.
This is a strategy recommendation, not a prediction of jury scores.

Center the story on complete meals, shared batches, freshness, competing
resources and checked recovery, with a precise paired-course quadratic model.
Demonstrate the variable/auxiliary/coupler tradeoff and independent correctness.
Use actual QAOA/VQE outputs on a frozen shared workload to select the strongest
quantum method; QAOA is the current implementation default, not a required
winner. A new exact-cover study remains a research candidate, not a priority
pivot or evidence of near-term hardware superiority. Generic30qubit clustering
alone is not a scientific contribution or proof of quantum benefit.

Finish a repeatable experiment on the integrated extension: checked quality,
feasibility, matched references, restriction gaps, seed variability and scaling.
Include unsuccessful cases. A bounded actual IBM demonstration can strengthen
evidence if compilation and allowance support it; unexecuted projections must
remain labeled. VeloxQ should tackle larger instances of the same decision
model, with measured quality/runtime and a clear role in the workflow, subject
to the existing execution hold. Finish the game-style demo around retained
solver traces, rigorous docs and a rehearsed explanation. The event PDF requires
a video of at most5minutes and a3minute live presentation; polished graphics
must not substitute for experimental substance. No new hardware/service use,
submission or human messaging is authorized by this recommendation.

## Historical research discussion: quantum benefit (parked)

The user clarified that the aim is to identify a formulation where the quantum
optimizer could outperform strong classical methods, not merely demonstrate
QAOA/VQE on a difficult large problem. No current result establishes that.
Increasing the number of30qubit clusters does not by itself favor quantum
optimization: classical methods can use the same decomposition, and a readily
simulated quantum cluster routine remains reproducible classically. Hardware
could still differ in speed, but that needs an end-to-end comparison with direct
classical optimization, not only quantum-circuit simulation.

A research candidate to evaluate before any pivot is exact-one batch/service
selection (exact cover / positive one-in-three SAT): each requirement has three
candidate choices and exactly one must be selected. The penalty
sum_clauses(x_i+x_j+x_k-1)^2 is already quadratic, with no product auxiliaries.
Only interpret this as a kitchen model when the actual local programs and
requirements support those semantics; arbitrary SAT triples are a benchmark,
not an independently validated manufacturing instance. Current paired-meal
semantics do not automatically become exact cover by changing the solver name.

A [2026 one-in-three SAT study](https://www.nature.com/articles/s43588-026-01007-8)
reports improved ideal numerical scaling with parity-informed reduction and
structured quantum solvers. Its scaling comparison uses inverse success
probabilities versus classical work counters, rather than end-to-end wall time;
its hardware demonstrations are small feasibility tests. This is a candidate
research mechanism, not evidence our IBM allowance or generic clustered VQE
will beat CP-SAT. Give classical controls the same algebraic reductions.

An evaluation gate would require multiple predeclared sizes/seeds, strong SAT/
exact-cover/CP and heuristic controls, matched solution-quality targets, actual
compiled hardware cost and all training/preprocessing/coordination overheads.
If pursuing the candidate, investigate problem-informed coherent search rather
than assuming more independent clusters creates advantage. No new SAT/kitchen
profile, solver adapter or physical experiment has been implemented by this
note; the existing shared problem and human work split remain intact.

## Current direction: coupled complete meals and bounded quantum neighborhoods

17 October update. Code in `paired_meals.py`, `meal_blocks.py`,
`meal_search.py` and `meal_circuit.py` implements the next experimental profile,
`paired-course-contiguous.v3`. The frozen V3release and complete-cell evidence
above supersede the earlier unbuilt-handoff status.
The older unit-demand independent-set prototype documented below is historical;
its rejected capped pools are not the main workload.

A delivered meal now requires both its main course and side. If M_d and S_d
are 0/1 component-coverage expressions, completion is M_d*S_d. Missing-meal
cost is priority_d*(1-M_d*S_d); unmatched components contribute
M_d+S_d-2*M_d*S_d to disposal. Under the declared unit-component model these
expand directly to quadratic program-selection terms with no product-auxiliary
qubits. Shared batches, yields, freshness, departure times, workers/equipment,
committed work and mandatory repair cleaning still constrain the decision.
This is a mathematical modeling contribution to test, not a claim that classical
solvers find multiplication difficult. Aggregate stock/holding/power and
interrupted-batch recovery remain disabled in this profile.

Program choices are grouped by a common covered demand anchor, with an idle
data qubit per block. Local XY gates preserve exactly one choice per block;
cross-block resource/double-service conflicts still use penalties and an
independent physical check. This removes the previous large multi-controlled
mixers. The search varies bounded portfolios while retaining its quantum-sampled
incumbent. Local compatible main/side proposals and independent retiming support
are explicit classical preprocessing; no CP solution or complete-plan repair
supplies the answer. Exact sector values and raw CP are evaluation references.
Incumbent retention does not guarantee convergence or eliminate restriction loss.

The quantum question is whether this structure-aware, trained multi-angle QAOA
produces more useful complete-meal schedules than ordinary penalized X-mixer
QAOA at comparable routed gate/shot budgets. One-hot preservation alone does
not establish a better optimizer. Compare the initializer and mixer-only
controls, same-QUBO classical search, and whole-model native references. Existing
larger paired-meal pilots remain worse than their raw CP reference; this
direction has not established a performance advantage.

## SamplingVQE and clustering: independent choices

17 October clarification prompted by the user's question: QAOA is a structured
variational ansatz, not the only admissible quantum optimizer. SamplingVQE is
an appropriate alternative for our same diagonal cost Hamiltonian; Qiskit's
[QAOA implementation](https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.minimum_eigensolvers.QAOA.html)
itself subclasses SamplingVQE. Switching methods changes neither the problem
nor the direct-encoding qubit count. A shallow custom ansatz may reduce routed
cost, but neither quality nor training overhead is predictable from its name.
For this application, score actual bitstrings and consider CVaR; see
[SamplingVQE](https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.minimum_eigensolvers.SamplingVQE.html).

Problem partitioning/overlapping neighborhoods can use either QAOA or VQE.
Ignoring interactions between independently solved clusters changes the
optimization problem. Conditioning on the current outside decisions retains
all crossing QUBO terms exactly as local linear biases, but repeated cluster
updates are a heuristic and may stall. For example E(a,b)=a+b-3ab has a global
minimum at11 with energy-1; from00, either one-bit conditional minimization
stays at00 with energy0. Joint/overlapping updates can address this particular
trap, without guaranteeing global convergence. This maps naturally to the
main-and-side complementarity motivating our paired-meal profile.

An important distinction from molecular VQE: our Hamiltonian is diagonal.
At least one optimal state is a computational-basis bitstring, which is a
product state. Provided each cluster ansatz can represent its component basis
states, a product-of-clusters family still contains a global optimum. There
is therefore no unavoidable optimal-energy loss solely from the absence of
cross-cluster entanglement. Finding the coordinated optimum can remain hard;
this observation supplies neither an efficient algorithm nor quantum advantage.

Exact circuit cutting is different from conditional optimization or a product-
cluster ansatz. Reconstructing a full circuit's behavior can require sampling
overhead exponential in the number/type of cuts; do not describe many small
circuits as an equivalent affordable large circuit. See
[IBM cutting documentation](https://qiskit.github.io/qiskit-addon-cutting/).
The named [ClusterVQE paper](https://arxiv.org/abs/2106.07619) uses dressed
Hamiltonians for electronic structure; its methodology and resource behavior
are not automatically the same as partitioning our diagonal QUBO.

If evaluating a VQE-centered candidate, retain whole one-hot blocks, use a
block-preserving ansatz where useful, and compare overlapping cluster updates
against QAOA and a classical cluster solver under the same schedule and budget.
An arbitrary rotation/CNOT ansatz may leave our one-hot sector and invalidate
the small-sector simulator even though the encoded problem is unchanged.
Keep crossing constraints/rewards in every conditioned solve, report global
physical checks, and label the result a cluster heuristic rather than a full
entangled solve. This clarification is a proposed comparison, not an implemented
VQE adapter, a numerical loss estimate or a replacement of the human work split.

### Concrete example: ten 30-qubit clusters

For disjoint direct-encoded clusters this represents300binary variables, while
each execution needs30data qubits (plus any circuit workspace). Overlapping
clusters represent fewer than300distinct variables. A full dense30qubit vector
has2^30amplitudes:16GiBcomplex128 or8GiBcomplex64. Sequential cluster simulation
reuses this memory; ten simultaneous double-precision vectors need160GiBbefore
workspace. This does not simulate a general entangled300qubit state. Hardware
can reuse the same30qubits, but circuit evaluations, shots and cluster-update
passes accumulate. For example10clusters*100evaluations*1024shots*5passes is
5,120,000executions, before any gradient/mitigation expansion; this is arithmetic,
not a proposed job or device-time estimate.

Qubit count is an encoding resource, not a hardness certificate. A classical
optimizer need not store any quantum amplitudes or inspect every bitstring.
The same300variables could be ten truly independent problems, a special easy
graph, or a tightly coupled problem with difficult competing choices. Relevant
factors include independent decisions after presolve, graph/constraint structure,
how many decisions a separator must coordinate, symmetries, objective tolerance,
and the quality of formulation/solver/hints. A proof of optimality may be much
harder than finding an equally useful plan. More edges or more penalties do not
monotonically imply greater useful difficulty.

Exact decomposition exploits existing independence and helps classical methods
too. Conditional/approximate clustering trades small local solves for repeated
coordination; it does not remove the global problem's difficulty, and dropping
crossing terms solves a different problem. If exact coordination must enumerate
many boundary assignments, its cost may grow exponentially in boundary size.

The relevant quantum-benefit test has two levels: whether the quantum cluster
solver produces better checked samples than competent classical cluster search
at matched total budgets, and whether replacing that solver improves the full
controller's solution quality/time after training, calls and coordination.
Difficulty of full-statevector simulation alone answers neither question.
At30qubits a direct classical cluster solver is a strong expected baseline;
current VQE hardware/noise/training does not establish a practical crossover.
Future/larger useful clusters are a research path, not an automatic advantage
from increasing problem size or multiplying the number of clusters.

## Hardness and hardware selection gate

### User's scale-consistency requirement

The user further clarified that the small demonstration may be classically
easy, provided it is the same meaningful optimization family at larger sizes.
Use this as an acceptance criterion: retain the service semantics, objective,
encoding/compiler and quantum ansatz while increasing interacting orders,
resource competition and offered programs. Ten disconnected copies of an easy
case do not meet it. The scale axis must report order count, program count,
physical qubits, couplers, connected components, sector size and routed depth
separately. Ten times the customers need not mean ten times the qubits.

Recommended mathematical core: multi-resource batch-program selection, a
weighted set-packing/conflict-selection problem, extended by complete-meal
pair rewards. It is naturally quadratic. For the simpler additive-reward
reference core, E=-sum_i w_i*x_i+P*sum_conflicts x_i*x_j, with positive w_i and
P>max_i w_i, exactly optimizes weighted independent set. The paired-meal
extension needs its existing wider objective-span penalty bound instead.
General independent set is NP-hard; this does not prove the particular
physically generated kitchen graph family is hard. Avoid claiming hardness
from a graph label or from one CP timeout. Special resource/graph structure can
make a subclass easy. QOBLIB's
[independent-set benchmark](https://zib-aopt.github.io/QOBLIB/problem/07/)
provides independent graph controls, not substitute kitchen evidence.

Proposed same-family program-count ladder:24/32for local method validation,
64/96/128as conditional hardware compilation targets,256/512/1024for large
classical/VeloxQ scaling studies. These are experiment sizes, not measured
hardness thresholds, approved service jobs or commitments that the current
whole-kitchen generator fits each number exactly. With one-hot block encoding,
physical width is program choices plus idle bits;128programs can exceed a
156-qubit device once all blocks/workspace are counted. Changing to lossy
portfolios must keep the restriction label and broader reference gap.

At fixed depth p, an ordinary QAOA cost/mixer circuit for a graph has
O(p*(|V|+|E|)) logical gates before routing. That describes circuit construction,
not the depth/shots/training needed for a target solution quality. No favorable
quantum runtime scaling follows solely from general classical NP-hardness.
Test both quantum quality and classical time-to-matched-quality across sizes;
large runs that cannot be simulated or executed remain projections. Parameter
transfer is a research option to test, not an assumed preservation of quality;
see [MIS parameter-transfer study](https://arxiv.org/abs/2504.21135).

The defensible eventual statement is that a small verified demonstration and
larger measured difficult cases share one formulation and scaling rule. Only
make the latter statement after observing it across representative seeds and
competent classical controls. Do not promise that10xsize guarantees classical
failure or that QAOA remains effective beyond the measured range.

The user reports access to a 156-qubit IBM processor, a 48 GB Mac and a 90+ GB
H100. Device width is a ceiling; the specific target/coupling map, calibration,
routed depth, account budget and useful sampled quality still determine a
hardware workload. Do not pad a circuit to 156 qubits or infer optimization
difficulty from an inability to store its dense quantum state.

In particular, a 35-data-qubit layout with seven size-3 and seven size-2 one-hot
blocks has just 279,936 sector states. It is classically enumerable; exact
sector simulation also lets us obtain its optimum. It supports a method/circuit
experiment, not a claim of a classically hard 35-qubit optimization problem.
The much larger whole-kitchen domain can still be nontrivial while a quantum
neighborhood remains tractable. The neighborhood's contribution must be
measured against replacing it with a classical solver under the same controller.

Fresh serial Mac screen: S3, paired-course v3, predeclared customer counts
4/8/12, five-second end-to-end CP-SAT budget per case, four workers, seed2026.
Raw inputs, checked results, source/artifact hashes and limitations are retained
in `output/catering-paired-classical-screen-v1/`.

| Customers | Result | Total seconds | Best U,W,B,R |
|---:|---|---:|---|
| 4 | OPTIMAL | 0.492 | 3,1,4,4 |
| 8 | FEASIBLE; full lexicographic optimum unproved | 5.002 | 4,1,7,7 |
| 12 | FEASIBLE; optimum unproved | 5.005 | 5,1,11,11 |

For eight customers the scalar bound already certifies that four missed meals
is minimal: bound64,126 exceeds every U<=3 score, whose maximum is63,999.
Its remaining uncertainty concerns lower-priority costs. For twelve customers
the bound only implies U>=3 while the incumbent has U=5. These are bounds for
one formulation/configuration, not intrinsic-hardness evidence. A proof timeout
is not evidence that finding a good plan is difficult. Multiple seeds and a
competent independent heuristic remain necessary before claiming a difficult
benchmark or solver benefit.

Recommended progression: retain tiny exhaustive correctness cases; study
roughly24–35-qubit quantum neighborhoods on the Mac/H100; compile the actual
target before physical execution; enlarge hardware neighborhoods only if
sample quality and routing justify it. Measure larger whole-kitchen cases with
native references and the integrated VeloxQ method, without claiming that a
small easy quantum subproblem solves the full domain or outperforms classical
search. The next acceptance gate is repeatable operational improvement and a
fair method comparison, not a promised quantum advantage. This follows the
[robust benchmarking guidance](https://arxiv.org/abs/2405.07624). IBM and VeloxQ
execution holds remain; the screen consumed neither service.

## The operational decision

Choose which legal local batch programs to execute. A program specifies menu,
yield, customer allocation, cooker, qualified workers and prep/cook/pack/clean
times. Several customers can share one batch. It is not a pre-solved complete
kitchen schedule. The selected programs directly decode into the full kitchen
plan; no classical optimizer completes or repairs a quantum answer.

The score remains lexicographic (U,W,B,R): weighted missed demand, discarded
lots, new batches and symmetric difference from the prior unstarted programs.
Hard constraints remain hard even when some demand cannot be fulfilled.

## A quantum-oriented representation

The implemented prototype, catering/quantum_first.py, uses unit residual demand
groups: each represents one lot, not necessarily one individual meal. For the
current fixtures a lot is ten meals. This representation rejects residual
quantities above one rather than silently changing their meaning.

Let x_b select a legal batch program and a_db be its 0/1 coverage of group d.
Connect two programs whenever they double-book any equipment/worker interval
or serve the same unit demand. A feasible selection is an independent set of
this conflict graph. Individual program validity and global pair compatibility
are sufficient only for the declared profile: aggregate ingredients, holding
and power are disabled. Adding those constraints requires a new proof/mixer.

On feasible selections:

    U = sum_d priority_d * (1 - sum_b a_db x_b)
    W = fixed_waste + sum_b (yield_b - served_b) x_b
    B = sum_b x_b
    R = |previous| + sum_b (1 - 2*[b in previous]) x_b

Thus the objective C=C0+sum_b c_b x_b is linear, with no missed-demand register.
The equivalent unconstrained QUBO is:

    E(x) = C(x) + P sum_{(b,c) in conflicts} x_b x_c.

Coverage rewards can make C negative on invalid selections. The old penalty
bound for a nonnegative objective is insufficient here. The implementation uses
P=1+sum_b |c_b|, exceeding the entire bit-domain objective range. If any conflict
is selected, E is greater than the maximum possible C; all-zero is a feasible
witness. Every global minimizer is therefore feasible and optimizes C in the
declared option domain. Every zero-penalty selection is checked independently
against raw operations, meal allocations and material disposal.

The loader, literal energy, Ising conversion, decoder and generic sampling
contract remain usable. The old catering.native.solve_program_master explicitly
rejects this representation: it separately adds missed-variable costs, which
would double-count them. Use literal exact enumeration/independent selection
audits or catering.native_slots for the complete raw reference.

## Algorithm: alternate cost phases and feasible mixing

For program b, rotate its data qubit only when every conflicting neighbor is
zero. A sequential layer of these neighbor-controlled RX(2 beta) gates preserves
independent-set support. Start from all-zero, which retains committed work and
mandatory recovery cleaning while explicitly missing the remaining meal demand.
Any independent set can be reached through valid single-bit additions/removals;
this connectivity statement does not guarantee useful amplitudes at shallow depth.

On this invariant feasible subspace, penalty phases are identities. The cost
phase can therefore use only the linear service/waste/batch/change terms.
Ordinary X-mixer QAOA instead uses the full penalized QUBO. Compare both methods
on identical offered programs and physical objectives, recording their different
gate costs and state preparations explicitly.

Controlled independent-set/set-packing mixers are established methods, not our
invention: see Hadfield et al., Sections 4.2 and A.2.4,
[Quantum Alternating Operator Ansatz](https://arxiv.org/abs/1709.03489).
Our proposed contribution is the catering mapping, its precise correctness and
scope, and the measured feasibility/quality/resource tradeoff.

The central experiment is whether constraint-preserving mixing gives better
checked schedules per shot and per routed gate budget than ordinary QAOA.
VQE and VeloxQ consume the same literal QUBO for their comparisons; they need
not use the QAOA mixer. Classical solving supplies optima/bounds and sanity checks.

## What has actually been tested

Run:

    .venv-stage2/bin/python -m unittest discover -s tests/catering -v
    .venv-stage2/bin/python -m catering.build_quantum_first --output output/NEW-DIRECTORY

The retained prototype is output/catering-quantum-first-v2/. Its raw fixture has
two residual menus, four ten-meal demand groups, variable batch yields,
freshness/departures, shared crews and committed Menu A work. Its complete
program encoding has 359 data bits and 55,426 couplers. Caps 8/12/16/20 are
explicit restrictions with distinct hashes.

Tests verify the literal QUBO against independent raw enumeration, the full
objective-range penalty bound, mixer unitarity, feasible-support preservation
and exact Ising energies. Fixed-angle, two-layer full-statevector probes are
logical circuit audits, not trained QAOA performance measurements.

| Cap/data qubits | Feasible basis states | Exact restricted U,W,B,R | Full raw optimum |
|---:|---:|---|---|
| 8 | 25 | 1,0,2,2 | 0,0,2,2 |
| 12 | 49 | 1,0,2,2 | 0,0,2,2 |
| 16 | 96 | 1,0,2,2 | 0,0,2,2 |
| 20 | 189 | 1,0,2,2 | 0,0,2,2 |

**These capped pools fail the main-workload gate:** they lose one demand lot
relative to the complete model. Do not present an exact optimum of these pools
as solving the complete kitchen. The first pool policy in retained v1 was even
weaker: every offered pair conflicted, so at most one program could be selected.
It is rejected as a main workload. V2 admits compatible multi-batch selections
but still loses the complete optimum. Preserve both negative diagnostics.

The v2 20-qubit logical probe retains feasible probability 1 within numerical
precision, versus about 0.017 for ordinary X mixing with the same fixed angles
and all-zero initialization. This validates the invariant, not an optimized,
hardware, equal-gate-budget or quantum-versus-classical advantage. Its largest
rotation has 11 neighbor controls. Routed depth, ancillas and native gate counts
are unknown; logical data width alone is not a hardware feasibility claim.

## Acceptance gates before calling this the main result

1. Retain meaningful competing multi-batch plans; report components, density,
   feasible states and operational gaps, not just qubit count.
2. Improve/version the restriction or use a small complete domain that preserves
   the decision we intend to demonstrate. Do not inject a classical optimum
   into the choices. Exact reductions need proofs; heuristic caps need gaps.
3. Train QAOA locally, with declared train/test cases, seeds and evaluation
   budgets. The method owner retains unsuccessful runs and initializers.
4. Compile both mixers for the same actual IBM target. Judge the benefit against
   the added controls/routing/depth; change the mixer if the cost is impractical.
5. Use checked raw returns directly. Keep CP/exact/SA as reference evidence;
   tiny correctness cases are not the project centerpiece or a hardness claim.
6. Freeze a bounded campaign before any IBM/VeloxQ use. Both remain held.

Alternative-menu, ingredient-stock and stochastic extensions remain proposals.
They must not silently invalidate this pair-conflict feasible-subspace proof.

## Mandatory post-repair clean: corrected physical core

The current core profile is core-contiguous-repair-clean.v2. Every outage case
includes a ten-minute recovery clean, even if C2 was idle and is never used again.
The conservative core fixes its time/worker by the declared earliest grid slot
compatible with committed operations. In this fixture W2 cleans A during 60–70;
C2's recovery clean is therefore W2/C2 during 70–80. Cooking on C2 cannot restart
until minute 80. The task is in raw plans and consumes both equipment and labor.

This is a fixed recovery-policy restriction, costing zero decision bits. It is
not the ambitious model's optimized choice of cleanup time/worker, phase-aware
failure or material-loss recovery. A quantum model with movable mandatory tasks
needs exactly-one continuation groups and an appropriate feasible mixer; the
independent-set-only proof cannot be reused unchanged.

Corrected exact tuples: S0=(0,0,1,0), S1=(0,0,1,2), S2=(1,0,0,1),
S3=(1,0,1,2). S2 misses the nominal B order. S3 serves only the urgent B order on
C1. output/catering-foundation-v2/ is the current common-method release.
The v1 outage results omitted this mandatory task and are superseded.
