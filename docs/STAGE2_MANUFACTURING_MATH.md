# Mathematics of the complete-recipe manufacturing model

Authoritative formulation guide, 17 October 2026. This describes the implemented
finite-window model and its explicitly restricted variants. The owning source
files and frozen numerical artifacts are linked below. No new experiment is
needed to establish the statements in this guide.

The main recovery fixture has two pumps, 16 mandatory operations per pump,
horizon $H=1440$ minutes and 30-minute **start** grid. Actual integer durations
are retained: a start at 810 and a 45-minute duration ends at 855, without rounding
that end to the start grid. Heat capacity is withdrawn before planning; the
replacement scenario adds a resource whose processing cannot begin before 360.
The terminal due dates are 900. These are synthetic, known planning conditions,
not a simulated surprise during an already running operation.

## 1. Raw data and legal individual assignments

Let $O$ be the mandatory operations, $M$ the machines and $W$ the workers.
Each operation $o$ has predecessors $\operatorname{pred}(o)$, release $r_o$,
integer due date $d_o$, integer weight $w_o\ge1$, required skill, eligible
machines and positive integer processing durations $p_{om}$. The precedence
graph is acyclic. Due dates enter the objective only for terminal operations

$$
O_T=O\setminus\{p:p\in\operatorname{pred}(o),\ o\in O\}.
$$

A raw assignment is $a=(o,m,w,s)$, with machine hall $h_a$, start

$$
s\in\{0,g,2g,\ldots\}\cap[0,H],\qquad e_a=s+p_{om}\le H.
$$

The worker's attended end $u_a$ is $e_a$ for full attendance and

$$
u_a=s+\min(p_{om},\ell_o)
$$

for start-only attendance of declared length $\ell_o\ge1$. The machine is
occupied on $[s,e_a)$; the worker is occupied on $[s,u_a)$. Endpoints are
half-open: one operation may begin at the instant another releases a resource.

The unary domain $D_o$ contains exactly the assignments satisfying:

- eligible machine and qualified worker;
- $s\ge\max(r_o,r_{om},r_w,\sigma(f^0_m,f_o))$, using zero for an absent
  machine release or absent initial setup family;
- machine interval $[s,e_a)$ lies in one declared machine availability window;
- worker attendance $[s,u_a)$ lies in one worker availability window;
- if the worker's initial hall differs from $h_a$, one complete walk of
  duration $\tau$ fits between worker-ready time $r_w$ and $s$, entirely
  inside a worker availability window.

For a worker with availability intervals $[L_k,U_k)$, the last condition is

$$
\operatorname{walk}(w,t_0,t_1,\tau)
\iff \tau=0\ \lor\ \exists k:
\max(t_0,L_k)+\tau\le\min(t_1,U_k).
$$

Processing is nonpreemptive and cannot straddle a machine calendar break.
Worker start-only attendance may finish before the machine processing does.
Calendar gaps cannot be used as working-time walks. Every operation is selected
once; unfinished or inconvenient operations cannot be silently dropped.

Owning code: [`assignments`, `validate`, `can_walk`](../stage2/window_qubo.py).
Raw inputs: [replacement problem](../output/manufacturing-recovery-v2/heat-lease-32/problem.json).

## 2. Pairwise compatibility and its assumptions

Two assignments of different operations are incompatible if any of the
following conditions fails.

**Machines.** Intervals on the same machine cannot overlap. If assignment $a$
precedes $b$ on that machine, machine-only family setup requires

$$
e_a+\sigma(f_a,f_b)\le s_b.
$$

The compiler enforces this for **every time-ordered pair**, not only adjacent
operations. This is exact for the supported setup model because setup durations
are nonnegative, diagonal entries are zero, and the directed triangle inequality

$$
\sigma(f_i,f_k)\le\sigma(f_i,f_j)+\sigma(f_j,f_k)
$$

holds. Adjacent pairs enforce the actual transitions. Summing the adjacent
transitions, with intervening nonnegative processing and idle time, implies
every nonadjacent direct setup inequality. The same argument justifies the
initial-family unary bound. `validate` rejects nonmetric setup matrices and,
when setups are enabled, machines whose availability is not exactly $[0,H)$.
Machine-specific processing-release times are still permitted. There is no
setup crew, setup interruption or human attendance during setup in this model.

**Workers.** Assignments using the same worker cannot have overlapping attendance.
For $s_a\le s_b$, require $u_a\le s_b$. If halls differ, also require
$\operatorname{walk}(w,u_a,s_b,\tau)$. The fixed travel duration is the declared
hall-change duration, not a capacitated vehicle route. Enforcing every pair is
consistent with the raw adjacent worker path: between different-hall endpoints
an actual valid path contains at least one complete walk inside their time gap.

**Precedence and transfer.** For each direct predecessor $o\to v$, assignments

$$
a\in D_o,\ b\in D_v
\quad\text{must satisfy}\quad
e_a+L_{m_a,m_b}\le s_b,
$$

where $L$ is the declared nonnegative integer machine-to-machine transfer lag.
All parents of an assembly join must satisfy this inequality. Transfer lag is
uncapacitated: no AGV queue, empty journey, shared buffer or transport-worker
occupation is introduced.

Let $n_{ab}$ be the number of failed reasons returned by `conflict_reasons`.
A pair may fail more than one reason. The complete assignment compiler uses
that integer multiplicity; it does not replace it with a Boolean flag.

Owning code: [`conflict_reasons` and raw `check_plan`](../stage2/window_qubo.py).
The checker reconstructs raw resource and predecessor sequences without reading
the QUBO coefficients. Its independence is architectural, not a claim of a
formally verified implementation.

## 3. Assignment optimization QUBO, including the completion register

Introduce one binary variable $x_a$ for every retained assignment
$a\in D_o$. The complete compiler's completion values are

$$
\mathcal C=\{e_a:a\in\bigcup_o D_o\}.
$$

Introduce $y_c\in\{0,1\}$ for $c\in\mathcal C$. The selected completion
value is an upper bound on every selected operation end. Let $z=(x,y)$ and
let $\mathcal G$ contain every operation assignment group and the one
completion-register group.

The literal implemented objective-and-penalty polynomial is

$$
\begin{aligned}
E_P(x,y)={}&
(H+1)\sum_{o\in O_T}\sum_{a\in D_o}
 w_o[e_a-d_o]_+x_a
+\sum_{c\in\mathcal C}c\,y_c\\
&+P\sum_{G\in\mathcal G}\left(\sum_{i\in G}z_i-1\right)^2\\
&+P\sum_{\substack{a<b\\o_a\ne o_b}}n_{ab}x_ax_b
+P\sum_{\substack{a,c\\e_a>c}}x_ay_c.
\end{aligned}
$$

Here $[t]_+=\max(0,t)$, and the arbitrary index ordering $a<b$ counts each
assignment pair once. Zero entries need not be stored. Every selected assignment
must be compatible, each mandatory group must select exactly one option, and
the completion register must not understate the actual makespan.

For a feasible selected schedule define

$$
T=\sum_{o\in O_T}w_o[e_o-d_o]_+,\qquad C=\max_o e_o.
$$

Choosing its minimum valid completion-register value gives

$$
J=(H+1)T+C.
$$

All times and weights are integers, so $T$ is an integer. Since $0\le C\le H$,
improving $T$ by at least one outweighs any change in $C$. Thus $J$
lexicographically minimizes weighted terminal tardiness, then makespan. This
argument would need a new dominance coefficient if fractional tardiness units
or fractional weights were introduced. It is **not** a calibrated money objective.

A nonoptimal bitstring can select a valid completion upper bound larger than
the real makespan. Its literal energy and its decoded actual objective then
differ. Both must be retained; reporting raw objective alone does not certify an
encoded optimum.

### Stored coefficients and counting

`WindowQUBO.energy` uses

$$
E=E_0+\sum_i h_i z_i+\sum_{i<j}Q_{ij}z_i z_j.
$$

There is one stored upper-triangular coefficient per unordered pair; no factor
of two is applied when evaluating it. Binary squaring gives

$$
P\left(\sum_{i\in G}z_i-1\right)^2
=P-P\sum_{i\in G}z_i+2P\sum_{i<j\in G}z_i z_j.
$$

Hence the offset is $P|\mathcal G|$, each group member's linear coefficient
receives $-P$, same-group pairs receive $2P$, a different-operation conflict
pair receives $Pn_{ab}$, and an illegal assignment/register link receives
$P$. Original nonnegative objective coefficients are added to the appropriate
linear terms. Coupler counts mean nonzero stored unordered pairs, not the sum
of reason multiplicities and not the number of hardware gates.

Owning code: [`compile_qubo`](../stage2/window_qubo.py) and
[`manufacturing_full.py`](../stage2/manufacturing_full.py).

## 4. Why the penalty guarantees a correct ground state

Write the unexpanded expression as $E_P=F+PV$, where $F$ is the nonnegative
linear objective on **every** binary state and $V$ is a nonnegative integer
sum of squares and conflict products. An invalid encoding has $V\ge1$.

The compiler computes

$$
B=\sum_{o\in O}\max_{a\in D_o}
\bigl((H+1)\mathbf{1}_{o\in O_T}w_o[e_a-d_o]_+\bigr)
+\max\mathcal C.
$$

Every feasible encoding has $F\le B$. With $P=B+1$, every invalid state has
$E_P\ge P>B$. **If the domain contains a feasible schedule**, every global
minimum is therefore feasible and objective-optimal. The argument does not say
that a heuristic solver will find a ground state, or that an infeasible instance
must have a zero-energy state.

### Checked-witness penalty

For the same compiler structure, suppose a checked representable feasible
schedule, with its minimum completion register, has objective $U$. Then
$P=U+1$ is sufficient: an invalid state costs at least $U+1$, while that
feasible witness costs $U$. Feasible energies remain unchanged, and the global
feasible optimum cannot change. Invalid-state energies deliberately change.

This theorem requires the objective to remain nonnegative on every binary
state, and the penalty polynomial to retain the stated integer structure.
`manufacturing_penalty.tighten` is specialized to these assignment/column
compilers; it is not a generic theorem for arbitrary QUBOs, negative rewards or
quadratic monetary objectives. Its witness must exist inside the supplied
domain; a valid raw plan excluded by a restricted pool is insufficient.

After witness tightening, **energy below $P$ is sufficient but not necessary
for feasibility**. A feasible expensive plan can exceed $U+1$. Decode/check
samples directly when reporting feasibility; do not reuse an energy-threshold
classifier without checking its penalty assumptions.

Owning code: [`tighten`](../stage2/manufacturing_penalty.py).
Tests: [exhaustive penalty preservation](../tests/stage2/test_manufacturing.py).
The saved CPU pilot even finds worse feasibility with the smaller penalty;
a correctness bound is not a performance guarantee.

## 5. Exact reductions, changed models and deliberately restricted pools

**Unary pruning** removes individually illegal assignments by the raw rules.
**Binary support pruning** removes an assignment only if some other mandatory
operation has no compatible remaining assignment. A complete feasible schedule
supplies a supporting assignment in every other group. By induction none of its
assignments is removed. Repeating to a fixed point preserves every feasible
schedule. Nonempty surviving domains do not certify joint feasibility.

**Start-grid coarsening** changes the raw allowed starts. It can remove optimal
schedules and is not an exact reduction of a finer-grid model. Horizon changes,
due-date changes and feature ablations also change the problem; their input
identities and reference objectives must remain distinct.

**Operation pools** retain selected machine/worker/start rows and all operations,
but omit other individually legal assignments. The optimizer is exact only
inside that selected pool. Nested enrichment preserves the previous choices;
replacing capped choices need not preserve a previous optimum. The specialized
operation/column compilers penalize a conflicting pair **once** instead of using
the complete compiler's multiplicity. They preserve the same feasible
interpretation on their domain, but their invalid-state energies differ.

Measured examples: the original 781-bit replacement pool stays 45 minutes late;
the deterministic nested 2,078-bit pool retains the complete-model0/855 optimum.
The complete support-pruned assignment QUBO has 2,499 bits and 381,371 couplers.
The counts use different domain/register constructions; these are measured
quality/representation tradeoffs, not a minimum-qubit theorem.

Owning code: [`arc_prune`](../stage2/window_reduction.py),
[`operation_columns.py`](../stage2/operation_columns.py),
[`operation_qubo.py`](../stage2/operation_qubo.py),
[`capacity_frontier.py`](../stage2/capacity_frontier.py).
Evidence: [complete-domain recovery](../output/manufacturing-full-recovery-v1/report.json),
[nested frontier](../output/capacity-frontier-review-v1/report.json).

## 6. The unit-penalty hard-deadline query

This is a distinct question: **does any schedule meet all terminal deadlines and
finish by a declared cap $K\le H$?** Retain the original horizon, calendars,
durations, start grid and resource rules. Remove assignments with $e_a>K$,
and terminal assignments with $e_a>d_o$, then apply exact support pruning.
There is no completion register and no soft objective.

On the resulting domain $D^K$, let $I_K$ be unordered different-operation
pairs with at least one incompatibility. Use

$$
E_{\mathrm{deadline}}(x)
=\sum_{o\in O}\left(\sum_{a\in D_o^K}x_a-1\right)^2
+\sum_{\{a,b\}\in I_K}x_ax_b.
$$

Every term is nonnegative. Therefore energy is zero **if and only if** exactly
one query-legal assignment is selected for every operation and no selected pair
conflicts. This is precisely a feasible raw schedule meeting the hard query.
No objective competes with the penalties, so unit weights suffice. Stored
coefficients are $-1$ linearly, 2 within groups, 1 for incompatible pairs, and
offset $|O|$. Multiple reasons are collapsed to one Boolean conflict here.

The checked replacement query at $K=900$ has **818 variables and 33,817
couplers**. The cap855 query has the same retained domain, and is feasible.
Cap854 retains 632 variables and 21,152 couplers but is globally infeasible.
The outage cap900 query retains 796 variables and 32,760 couplers yet is also
infeasible. These examples show why surviving pairwise supports do not prove a
full schedule exists. Independent native CP certifies the yes/no outcomes.

A nonzero heuristic sample proves only that this returned state fails the
query. It does not prove infeasibility. An exact empty-domain propagation
certificate is different from a construction memory guard, failed optimizer or
UNKNOWN native result. Query identity hashes include the original problem,
completion cap and terminal deadlines. A feasible query witness need not
minimize makespan or monetary cost.

Owning code: [`deadline_qubo.py`](../stage2/deadline_qubo.py),
independent [`deadline_reference.py`](../stage2/deadline_reference.py).
Evidence: [four frozen decision queries](../output/deadline-decision-review-v1/report.json).
Tests: [literal zero-set and pruning tests](../tests/stage2/test_deadline_qubo.py),
[native calendar/travel/setup and status tests](../tests/stage2/test_deadline_reference.py).

## 7. The actual whole-recipe quantum bridge

The bridge partitions all 32 operations into eight disjoint complete component
trajectories. Every choice in group $g$ supplies concrete assignments for
exactly that group's operations. A binary $z_{gk}$ selects trajectory $k$.
Each supplied trajectory is internally checked. Pair penalties enforce all
cross-component resources, worker paths, setups and BOM dependencies; a
completion register preserves the same priority objective $J$.

Unlike the complete assignment compiler, the column compiler only needs
completion values taken from **terminal** operation ends. In a feasible finite
DAG, every operation reaches a terminal successor and all transfer lags are
nonnegative, so the actual maximum end is attained at a terminal. The compiler
also removes register values below an explicit minimum possible terminal
completion. This preserves all feasible trajectory combinations with their
minimum valid register; it does not preserve every redundant encoding state.

The first and best of 64 independently constructed raw schedules are preserved
as trajectory anchors; additional choices give nested caps 2/3/4. No native
reference plan generates candidates. The classical constructor already finds
the 0/855 recovery plan and its cost is reported. QAOA searches a restricted
recombination domain; it is not credited for discovering that source plan.

`AssignmentSector` keeps every trajectory and register bit as a logical qubit.
W-state initialization and XY exchange mixers preserve one excitation per
group. This permits omitting the one-hot penalty **inside the invariant sector**
because it is identically zero there; conflicts and objective terms remain.
Storing only $\prod_g|D_g|$ amplitudes is a classical simulation optimization,
not a reduction in circuit qubits or an oracle for feasible schedules. Preparing
the exact sector energy table enumerates its optimum classically; all such
preprocessing is disclosed.

The actual 18–36-qubit bridge retains the whole 32-operation model within its
restricted trajectory domain. QAOA and SA each return 18/18 valid encoded pool
minima; uniform returns 6/18. Encoded minima require both valid decoding and
literal energy equal to the reference. No quantum speedup is established:
native restricted CP and the constructive source already solve these domains.

Owning code: [`column_qubo.py`](../stage2/column_qubo.py),
[`recipe_bridge.py`](../stage2/recipe_bridge.py),
[`assignment_qaoa.py`](../stage2/assignment_qaoa.py).
Details and limits: [whole-recipe bridge](STAGE2_RECIPE_BRIDGE.md).
Evidence: [actual circuit/sample campaign](../output/recipe-bridge-review-v2/report.json),
[independent circuit audit](../output/recipe-bridge-circuit-audit-v1/report.json),
[all-return/count audit](../output/recipe-bridge-reporting-audit-v1.json).

## 8. Verification boundary and mathematical risks

The proof is conditional on the stated raw semantics, integer data, metric
machine-only setups, compatible calendars and correct implementation of the
enumerated domains. It does not cover the separate rich simulator's capacitated
AGVs, finite buffers, physical tools, stochastic quality/rework, setup crews,
energy management, shipments or an online unknown-breakdown policy. The cost
ledger values declared schedules under synthetic assumptions; its monetary
numbers are not this QUBO's optimization objective.

The same raw input is checked through native CP, direct schedule checking,
literal QUBO energies and exact small-sector/enumeration tests. These are
complementary implementation checks, not a machine-checked proof of the whole
codebase. Saved OPTIMAL statuses apply only to their original input/domain.
Restricted optimality is not whole-model optimality unless matched with a
complete-model certificate. UNKNOWN is unresolved, and physical quantum
execution remains distinct from simulator results and logical compilation.

Relevant executable checks:

- [assignment constraints and ground states](../tests/stage2/test_window_qubo.py);
- [all-feasible-schedule support preservation](../tests/stage2/test_window_reduction.py);
- [witness penalties and actual manufacturing scope](../tests/stage2/test_manufacturing.py);
- [cross-component precedence and ground-state validity](../tests/stage2/test_column_qubo.py);
- [sector energy, mixer and raw-reference agreement](../tests/stage2/test_assignment_qaoa.py);
- [encoded-optimum reporting regression](../tests/stage2/test_bridge_reporting.py).

No new solver run was performed to write this guide. Historical artifacts keep
their original source snapshots and hashes; this document explains those exact
boundaries rather than upgrading a result by changing its description.
