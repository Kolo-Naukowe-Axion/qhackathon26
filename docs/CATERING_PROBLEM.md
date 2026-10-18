# Axion Kitchen: the implemented optimization problem

This is a self-contained mathematical explanation of the problem we actually
implemented, rather than the earlier proposed catering feature set. It describes
profile `paired-course-contiguous.v3`, the frozen anchor-one-hot encoding, and
the equivalent no-idle representation used by VeloxQ. The implementation and
extended proofs are in [PROJECT_DESIGN.md](../PROJECT_DESIGN.md).

## 1. What is being optimized?

At an observed kitchen state, choose the remaining production plan. Each order
needs a main and a side before its departure. A batch can produce enough portions
for several orders, and those portions can be shared across them. The plan must
respect equipment, workers, recipes, calendars, freshness, cleaning and work
already started.

We minimize the following tuple **lexicographically**:

$$
\min (U,W,B,R).
$$

| Symbol | Meaning | Units |
|---|---|---|
| $U$ | Priority-weighted missed complete-meal demand | Weighted meal lots |
| $W$ | Discarded surplus and unpaired food | Component lots |
| $B$ | Number of newly selected batches | Batches |
| $R$ | Changes to the previous unstarted batch-program set | Added/removed programs |

One lot is **ten portions** in the current fixtures. A complete meal lot consumes
one main-component lot and one side-component lot. Consequently, serving one
more meal lot takes priority over any possible improvement in waste, batch count
or changes. These are not prices or monetary costs.

The problem belongs to the manufacturing scheduling family: cookers are machines,
recipes are operation chains, cleaning is setup-like work, and departures are due
dates. Shared batch yields and the requirement to complete two component streams
extend the fixed-job factory problem.

## 2. Inputs and notation

Time is measured in integer minutes on the declared ten-minute grid. Occupancy
intervals are half-open: $[a,b)$ and $[b,c)$ do not overlap.

The input contains:

- Menus, allowed batch yields, phase durations, freshness limits and cooking
  attendance requirements. The implemented recipes have preparation, cooking,
  packing and immediate cooker cleaning.
- Equipment with availability calendars, and individually identified workers
  with qualifications and calendars. Each equipment item and worker has unit
  capacity.
- Active meal lots $d\in D$. Each has a main demand group $q_M(d)$, a side demand
  group $q_S(d)$, reveal time, departure $D_d$, and positive integer priority $p_d$.
  Every component-demand group belongs to exactly one meal and has unit demand.
- A snapshot time $t_0$, whole committed batches $F$, observed outages, required
  recovery operations, and the previous unstarted program-ID set $T$.
- A finite scheduling horizon and declared grid of permitted starts.

New work starts no earlier than $t_0$. Demand must be revealed in the observed
snapshot before it can be planned. Current S0/S1/S2/S3 cases are deterministic
normal/urgent/outage/combined scenarios, each solved with its own observed state.
We do not optimize one policy over a probability distribution of future events.

## 3. What is a batch program?

A local batch program $i$ fixes all the decisions for **one batch**:

$$
i=(m_i,y_i,A_i,a_i,b_i,c_i,\text{equipment}_i,\text{crew}_i).
$$

Here $m_i$ is its menu, $y_i$ its yield in lots, $A_i$ its ordered list of allocated
component-demand groups, and $a_i,b_i,c_i$ its preparation, cooking and packing
starts. Write $r_i=|A_i|$, with $1\le r_i\le y_i$. Packing uses one contiguous
sequence on the packing line, one operation per allocated lot.

For preparation duration $p_m$, cooking duration $d_m(y)$, packing time $k_m$
per lot, and cleaning duration $\ell_m$:

$$
a_i+p_{m_i}\le b_i,
\qquad
b_i+d_{m_i}(y_i)\le c_i.
$$

$$
\operatorname{clean}(i)=
[b_i+d_{m_i}(y_i),\ b_i+d_{m_i}(y_i)+\ell_{m_i}).
$$

Allocated lot $j=0,\ldots,r_i-1$ is packed during

$$
[c_i+jk_{m_i},\ c_i+(j+1)k_{m_i}).
$$

Its packing interval must respect reveal and departure. For every allocated
group belonging to meal $d$, freshness is measured from cooking completion:

$$
0\le D_d-\bigl(b_i+d_{m_i}(y_i)\bigr)
\le \operatorname{maxAge}(m_i).
$$

Cooking occupies the cooker for its full duration, but its worker is reserved
only for the specified initial attendance interval. Preparation, cleaning and
packing require full attendance. Cleaning and packing can therefore overlap
when they use different equipment and workers.

Each program is checked against calendars, qualifications, outages, committed
work, recovery operations and its own phase interactions **before** it is offered
to an optimizer. This enumerates locally legal possibilities; it does not find
a compatible plan for the whole kitchen.

Surplus $y_i-r_i$ is discarded at cooking completion. An allocated component
without its partner is discarded at departure. All phases of a started batch
remain fixed, including phases that have not happened yet.

### Outage boundary

The supported outage withdraws idle cooker capacity; it does not interrupt a
committed cook. A qualified worker must perform a ten-minute post-repair clean,
even if that cooker is not subsequently used. Preprocessing fixes the earliest
clean compatible with committed work. That clean reserves both worker and
cooker and is not a new optimization variable. In current S2/S3, repair ends at
minute 60, cleaning occupies minutes 70–80, and new cooking cannot start before
minute 80. The viewer adds 10:30 to these minute offsets.

This fixed recovery policy is part of the declared problem. A model that also
optimized recovery timing would have a broader decision domain.

## 4. Global feasibility

Let $P$ denote the explicitly offered program set. Choose a subset $S\subseteq P$
to execute together with fixed work. It is feasible exactly when:

1. Every selected local program satisfies the conditions above.
2. No component-demand group is allocated twice, including fixed allocations.
3. No two selected programs overlap on equipment or attended-worker intervals.
4. Selected programs do not conflict with the committed/recovery boundary.

The compiler constructs a conflict set $\mathcal F$ for duplicate allocations
and equipment/attendance overlaps. Pairwise conflicts suffice for this profile
because resources have unit capacity and the disabled mechanisms introduce no
additional aggregate constraints. Missing a meal is permitted; it increases $U$.

The output records selected batches, operations, attendance, allocations,
handovers and disposals. An independent physical checker reconstructs validity
and outcomes from those records rather than trusting QUBO energy alone.

## 5. Why the objective is quadratic

Introduce $x_i\in\{0,1\}$ for every $i\in P$. Let $f_q\in\{0,1\}$ be fixed
coverage of component group $q$. Define planned coverage

$$
C_q(x)=f_q+\sum_{i:\ q\in A_i}x_i,
\qquad
M_d=C_{q_M(d)}(x),\quad S_d=C_{q_S(d)}(x).
$$

On feasible selections, $M_d,S_d\in\{0,1\}$. Coverage denotes a planned compliant
allocation, not food already handed over at the current replay time. A meal
handover occurs at its departure only when both components are ready.

The exact objective components are

$$
U(x)=\sum_{d\in D}p_d(1-M_dS_d),
$$

$$
W(x)=\sum_{b\in F}(y_b-r_b)
     +\sum_{i\in P}(y_i-r_i)x_i
     +\sum_{d\in D}(M_d+S_d-2M_dS_d),
$$

$$
B(x)=\sum_{i\in P}x_i,
\qquad
R(x)=|T|+\sum_{i\in P}
       \bigl(1-2\mathbf 1_{i\in T}\bigr)x_i.
$$

$R$ equals the symmetric-difference size $|S\mathbin{\triangle}T|$, including
removal of an old program that is not offered now. In the current fixtures
$T=\varnothing$, so **$R=B$**. They do not demonstrate a distinct stability gain.

| Main $M_d$ | Side $S_d$ | Complete meal $M_dS_d$ | Unpaired components |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 |
| 1 | 0 | 0 | 1 |
| 0 | 1 | 0 | 1 |
| 1 | 1 | 1 | 0 |

Coverage is linear in the program bits, so multiplying main and side coverage
produces terms of degree at most two. Diagonal products use $x_i^2=x_i$.
**No product-register qubits are introduced.** On feasible plans, an equivalent
material balance is

$$
W=\text{total produced component lots}
  -2\,\text{complete meal lots}.
$$

On invalid bitstrings, coverage can exceed one and these polynomial expressions
need not be physical waste counts. The hard-penalty proof below explicitly
includes those bitstrings.

## 6. Exact priority weights

Choose valid nonnegative integer bounds $K_U,K_W,K_B,K_R$ on feasible costs.
Safe bounds are total active priority, total fixed-plus-offered yield, $|P|$,
and $|P|+|T|$, respectively. Tighter proved bounds can also be used.

For priorities ordered $(U,W,B,R)$, define weights from lowest to highest:

$$
w_R=1,\qquad
w_k=1+\sum_{j\text{ lower priority than }k}w_jK_j.
$$

Then minimize

$$
C(x)=w_UU(x)+w_WW(x)+w_BB(x)+w_RR(x).
$$

An improvement of one unit at priority $k$ saves at least $w_k$. All lower costs
together can worsen by at most $\sum_j w_jK_j<w_k$. Therefore this scalar cost
orders feasible plans exactly as the lexicographic tuple; it is not a weighted
compromise that can sacrifice a complete meal to save food.

For the complete cell, the bounds are $(2,47,32,32)$, weights are
$(52{,}272,1{,}089,33,1)$, and the optimum $(0,0,2,2)$ has scalar cost $68$.
Different domains can use different weights, so operational tuples are the
appropriate cross-domain comparison.

## 7. Anchor blocks and the complete QUBO

Define a program's anchor as the lexicographically smallest component-group ID
it allocates. Let $P_g$ contain programs with the same anchor $g$. Two such
programs allocate the same unit demand, so no feasible plan can select both.

Add one idle bit $u_g$ per nonempty block and impose

$$
u_g+\sum_{i\in P_g}x_i=1.
$$

Every compatible offered subset has a unique completion: set $u_g=1$ precisely
in unused blocks. Grouping preserves all compatible subsets of $P$; choosing a
restricted $P$ can exclude schedules.

Let $\xi=(x,u)$ contain all bits. Cross-block conflicts remain in $\mathcal F$;
same-block incompatibility is already enforced by one-hot selection. The QUBO is

$$
E(\xi)=C(x)
 +P_{\mathrm{hard}}\sum_g
       \left(u_g+\sum_{i\in P_g}x_i-1\right)^2
 +P_{\mathrm{hard}}\sum_{(i,j)\in\mathcal F}x_ix_j.
$$

The register size is

$$
N=|P|+\text{number of nonempty anchor blocks}.
$$

Idle bits are data choices, not circuit work ancillas. The complete cell has
32 program bits and three idle bits, hence **35 data qubits**.

### Ground-state guarantee

Expand the objective as

$$
C(x)=c_0+\sum_i a_ix_i+\sum_{i<j}b_{ij}x_ix_j,
\qquad
A=\sum_i|a_i|+\sum_{i<j}|b_{ij}|.
$$

For any binary $x,y$, $|C(x)-C(y)|\le A$: each monomial changes by at most one.
Set $P_{\mathrm{hard}}=A+1$. Every invalid full register pays at least one integer
hard violation. For any feasible $\eta=(y,v)$ and invalid $\xi$,

$$
E(\xi)\ge C(x)+P_{\mathrm{hard}}
       \ge C(y)+1=E(\eta)+1.
$$

The validated boundary plus choosing every block's idle option supplies a
feasible witness. Thus every global ground state is feasible and optimal over
the offered domain. A heuristic is not guaranteed to find that ground state.
For the complete cell, $A=11{,}141{,}286$ and $P_{\mathrm{hard}}=11{,}141{,}287$.

## 8. The no-idle formulation used by VeloxQ

Remove $u_g$ and enforce at-most-one using pair exclusions. Let $\mathcal F^+$
contain the cross-block conflicts plus every pair of distinct programs in the
same anchor block. The transformed energy is

$$
\widetilde E(x)=C(x)+P_{\mathrm{del}}
                   \sum_{(i,j)\in\mathcal F^+}x_ix_j.
$$

For each program define a bound on objective increase when deleting it:

$$
D_i=\max(0,-a_i)+\sum_{j\ne i}\max(0,-b_{ij}),
\qquad
P_{\mathrm{del}}=1+\max_iD_i.
$$

From any invalid assignment, delete one endpoint of a selected exclusion edge.
This reduces its penalty by at least $P_{\mathrm{del}}$, while increasing its
objective by at most $D_i$. Total energy strictly decreases. Therefore no
invalid assignment is a global minimizer.

Feasible program selections and their objective values are preserved exactly;
unused blocks restore their unique idle bits. Invalid-state energies and the
search landscape change. This is an equivalent optimization over feasible
plans, **not the same sampling matrix**. It receives a separate bundle identity.
Mapping returns back preserves program decisions, including invalid ones; it
does not repair a schedule.

## 9. Ising and quantum optimization

For the fully expanded QUBO, use the convention

$$
E(\xi)=c+\sum_iq_i\xi_i+\sum_{i<j}Q_{ij}\xi_i\xi_j.
$$

Each pair coefficient appears once; incident-pair sums use the symmetric extension of $Q_{ij}$. Substituting $\xi_i=(1-Z_i)/2$ gives

$$
H_E=c'I+\sum_i h_iZ_i+\sum_{i<j}J_{ij}Z_iZ_j,
$$

$$
c'=c+\tfrac12\sum_iq_i+\tfrac14\sum_{i<j}Q_{ij},\quad
h_i=-\tfrac12q_i-\tfrac14\sum_{j\ne i}Q_{ij},\quad
J_{ij}=\tfrac14Q_{ij}.
$$

Multiplying by four gives integer coefficients. The VeloxQ adapter checks its
opposite spin convention $s_i=2\xi_i-1$ separately.

QAOA initializes one excitation in each block. Its blockwise XY mixing
preserves that excitation count, while objective/conflict phases couple the
choices. VQE uses a different one-hot-preserving Givens ansatz with controlled
couplings. Both optimize an exact simulated low-energy CVaR objective; at
$\alpha=0.1$, CVaR averages the lowest-energy ten percent of the distribution,
including a fractional boundary probability when necessary. Final samples are
decoded and checked independently.

The complete cell's block sizes are $5,11,19$, so the invariant sector contains
$5\cdot11\cdot19=1{,}045$ states, of which 59 are physically feasible. We simulate
this sector, not all $2^{35}$ basis states. It is a classically easy correctness
example. Current catering results are simulations and VeloxQ service results,
not physical-QPU results or evidence of quantum advantage.

## 10. The hybrid VeloxQ neighborhood step

The new follow-up fixes a checked classical incumbent outside a few freed
blocks. Partition no-idle program variables into free $F'$ and fixed $K$, with
fixed values $\bar x_K$. Substitution gives an exact sub-QUBO:

$$
E_{\mathrm{sub}}(y)=\widetilde E(x_{F'}=y,x_K=\bar x_K).
$$

Free/free pair terms remain quadratic; free/fixed terms become linear; fixed
terms become constants. Every sub-assignment therefore has exactly the same
energy as the corresponding full assignment. Returned choices are merged and
the full source plan is independently checked.

One retained 162-bit subproblem inside the 2,022-program-bit model improves
$(U,W,B,R)$ from $(8,3,8,8)$ to $(7,4,9,9)$. The exact neighborhood optimum is
$(7,3,9,9)$, which that run does not reach. Neighborhoods were selected offline
using exact enumeration; longer classical runs still find better plans. This
is a checked exploratory hybrid improvement, not a measured end-to-end solver
advantage. [Actual study and receipts](CATERING_VELOXQ_TUNING.md#hybrid-follow-up-18-october-veloxq-on-a-classical-plan).

## 11. Which domain did each experiment solve?

| Experiment | Offered decision domain |
|---|---|
| Complete cell | All 32 legal programs on its narrow declared grid; 35 bits with idle choices |
| Frozen QAOA/VQE S0–S3 portfolios | Restricted domains using 33/35/31/35 data bits |
| Larger VeloxQ tiers | Nested subsets of a 12-customer input generating 18,182 legal local programs; 512/1,024/2,048 source bits |
| No-idle VeloxQ tiers | Same offered feasible selections at 486/998/2,022 program bits |
| Hybrid neighborhood | Only selected blocks of that larger domain are free; all others retain their incumbent values |

Let $D_{\mathrm{raw}}$ be every schedule permitted by the declared physical
profile, grid, horizon and fixed recovery policy. Let $D_P\subseteq D_{\mathrm{raw}}$
be schedules expressible with the offered programs. For any checked returned
plan $z\in D_P$, lexicographic optima satisfy

$$
J^*_{\mathrm{raw}}\le_{\mathrm{lex}}J^*_P
                    \le_{\mathrm{lex}}J(z).
$$

The first gap is **representation loss**; the second is **search loss**.
The raw CP reference chooses scheduling decisions directly without the program
conflict graph. Same-domain CP and exact enumeration measure $J^*_P$ when they
certify optimality. A timeout with a feasible incumbent is not an optimum proof.

The model currently excludes aggregate ingredient and holding capacities,
monetary/energy costs, travel-time constraints, stochastic robustness and
interruption of already cooking batches. The game's walking animation does not
introduce transport constraints. Variable count alone does not establish
classical difficulty, and locally enumerating programs has a classical cost.

## 12. Relationship to Stage 1

Stage 1 is a separate required baseline: fixed job chains on factory machines,
minimizing makespan $C_{\max}=\max_o\operatorname{end}(o)$. Submitted instance A
has makespan 4 hours and B has 8 hours, both independently checked optimal.
The selected compact QAOA encodings use classically tabulated permutation
costs; that factorial preprocessing already reveals their best represented
order. We do not describe them as a general scheduling compression or speedup.

Stage 2 changes the decision set from fixed jobs to selectable/shared batches,
and changes the objective from makespan to complete-service/waste priorities.
Its source problem, QUBO and experiments are those specified above.

## Source map

| Responsibility | Implementation / evidence |
|---|---|
| Physical programs and local enumeration | [domain.py](../catering/domain.py), [options.py](../catering/options.py) |
| Paired service and waste | [paired_meals.py](../catering/paired_meals.py) |
| Anchor blocks, objective and hard penalties | [meal_blocks.py](../catering/meal_blocks.py) |
| QUBO/Ising conventions | [qubo.py](../catering/qubo.py) |
| Independent reconstruction | [check.py](../catering/check.py), [decode.py](../catering/decode.py) |
| Idle elimination | [conditioning.py](../catering/conditioning.py) |
| Exact fixed-boundary sub-QUBO | [velox_lns.py](../catering/velox_lns.py) |
| Counts, proofs and documented limits | [Project design](../PROJECT_DESIGN.md), [quality audit](CATERING_QUALITY.md) |
| Reproduction and frozen method inputs | [Catering guide](../catering/README.md) |
