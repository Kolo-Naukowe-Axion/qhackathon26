# Scheduling, QUBO & quantum methods

<p class="subtitle">A connected course in modelling, encodings, penalties and solvers.</p>

The central question is not “which quantum algorithm should I use?” It is **how to represent a scheduling problem so that minimising a mathematical function really solves the intended problem**. Once that connection is proved, different solvers can search the same model.

This guide builds that connection step by step. General statements are marked **General model**, **Derivation**, or **Guarantee**. Every numerical illustration is marked **Example** and states its own data. Examples explain the general statements; they do not replace them.

<div class="route" aria-label="The modelling pipeline"><span>Scheduling rules</span><b>→</b><span>Binary decisions</span><b>→</b><span>QUBO energy</span><b>→</b><span>Search or quantum circuit</span><b>→</b><span>Validated schedule</span></div>

## 00 · How to study this guide {#orientation}

Read chapters 01–06 in order. They are the foundation, including a transformation workshop in chapter 03. Chapters 07–09 explain alternative encodings, objectives, scheduling extensions and the Ising conversion. Chapters 10–12 explain the quantum algorithms and hybrid search. Chapters 13–16 provide a worked reference, exercises, a compact reference sheet, and sources.

You need basic algebra: substitution, multiplication of brackets, and inequalities. Sums, matrix notation, complex amplitudes, and quantum operators are introduced before use. You do not need prior scheduling or quantum-computing knowledge. The derivations assume comfort with following an algebraic argument, rather than requiring memorisation of formulas.

### Three different questions

| Question | Meaning | What establishes it? |
|---|---|---|
| Is this an **encoding-valid** bitstring? | Each operation has exactly one represented start. | Check the encoding. |
| Is this a **feasible** schedule? | The represented starts satisfy all scheduling rules. | Decode and validate the original rules. |
| Is this schedule **optimal**? | No feasible schedule has a smaller objective. | A matching lower bound or an exact optimality certificate. |

For example, every operation can have one start and still collide with another operation. Encoding validity is necessary for feasibility, but it is not sufficient. Likewise, feasibility does not establish optimality.

### Our notation contract

A subscript identifies an object; it does not imply multiplication. Thus $p_o$ means “the processing time of operation $o$.” A sum $\sum_{o\in\mathcal O}p_o$ means “add $p_o$ for each operation in the set $\mathcal O$.” The symbol $\in$ means “belongs to”; $\forall$ means “for every”; $\Leftrightarrow$ means “if and only if.” An empty sum is zero.

A product sign $\prod$ means multiply the listed factors. The logarithm $\log_2 K$ is the exponent needed to obtain $K$ from 2, and $\lceil a\rceil$ means round $a$ up to the next integer, keeping integers unchanged. For example, $\lceil\log_2 5\rceil=3$ because two bits give only 4 patterns, while three give 8. A set lists distinct objects; a graph consists of objects called vertices and links called edges. A directed edge has a specified direction. A directed acyclic graph has no directed loop. A longest-path processing-time bound adds durations along the longest directed chain of dependencies.

| Symbol | One meaning throughout |
|---|---|
| $\mathcal O$, $o$, $v$ | Set of operations; two operation labels. |
| $\mathcal M$, $\mu(o)$ | Set of machines; machine required by operation $o$. |
| $\mathcal A$ | Set of directed precedence pairs $(o,v)$: $o$ must finish before $v$ starts. |
| $p_o$, $S_o$ | Fixed processing time; chosen start time of operation $o$. |
| $H$, $C_{\max}$ | Tested completion deadline; actual makespan. |
| $T_o$, $K_o$ | Allowed start-time set; its size. |
| $x_{o,t}$ | One-hot bit: operation $o$ starts at time $t$. |
| $N$, $x_i$, $\phi(o,t)$ | Total bits; flattened bit; index of $(o,t)$ in a fixed ordering. |
| $a_i$, $w_{ij}$, $c_0$ | Linear coefficient, pair coefficient, constant offset of a QUBO. |
| $Q$ | **Upper-triangular** QUBO matrix. Each pair coefficient appears once. |
| $y_{o,r}$, $u_{o,r}$ | Domain-wall bit; binary positional bit. |
| $z_i$, $Z_i$, $X_i$, $Y_i$ | Classical spin; quantum Pauli operators. |
| $L$, $\gamma_\ell$, $\beta_\ell$ | QAOA layer count; cost and mixer angles in layer $\ell$. |
| $\lambda_{\mathrm{once}}$, $\lambda_{\mathrm{cap}}$, $\lambda_{\mathrm{prec}}$ | Positive weights of the three scheduling penalties. |
| $\eta$, $\rho$ | Domain-wall validity weight; objective-versus-constraints weight. |

In particular, **$p_o$ always means a processing time, never QAOA depth**. **$H$ always means a time horizon**; quantum Hamiltonians carry a hat, such as $\widehat H_C$. The letter $c_0$ always means a constant, never a coupling.

<aside class="takeaway">The model defines what a solution means. The solver only searches the model. A better solver cannot correct a model that rewards the wrong answers.</aside>

## 01 · Define the scheduling problem before encoding it {#scheduling}

### General model · Fixed-route, non-preemptive scheduling

An **operation** is one indivisible processing step. A job is an ordered chain of operations. We consider a finite, nonempty operation set $\mathcal O$. Each operation $o\in\mathcal O$ requires a particular machine $\mu(o)\in\mathcal M$ for a known duration $p_o>0$. Choosing its start $S_o$ determines its finish $S_o+p_o$.

We assume machines are available from time zero, have capacity one, and do not break down. Every job is available at time zero. Processing cannot be interrupted (**non-preemption**). A job may wait between operations. There are no sequence-dependent setups, transport delays, deadlines, or alternative machine assignments in this baseline model. Those require explicit additional modelling.

A machine is occupied during the **half-open interval** $[S_o,S_o+p_o)$. The endpoint is excluded so another operation may start at exactly the finishing time.

The three baseline requirements are:

1. **Start:** every operation receives exactly one nonnegative start.
2. **Precedence:** for every $(o,v)\in\mathcal A$, require $S_v\ge S_o+p_o$.
3. **Machine capacity:** if distinct operations require the same machine, their occupied intervals must not overlap.

The capacity requirement can be written as an “either/or”:

$$
S_o+p_o\le S_v\quad\text{or}\quad S_v+p_v\le S_o.
$$

The objective in the baseline is the **makespan**, the final completion time:

$$
C_{\max}(S)=\max_{o\in\mathcal O}(S_o+p_o),\qquad
\min_{S\text{ feasible}}C_{\max}(S).
$$

The maximum takes the latest finish among all operations. Minimising this maximum means finishing the whole workload as early as possible.

### Flow shop is a special case

In a flow shop, all jobs visit the same machines in the same order. A job shop allows different job routes. The operation-based notation above covers both. It does **not** force all machines to process jobs in the same job order; imposing one shared permutation would be an extra restriction.

### Why time is discrete here

We measure time in a fixed unit and assume every $p_o$ and the tested $H$ is an integer. Allowed starts are integers. If durations are rational, a sufficiently fine common unit can represent them exactly, at the cost of a larger horizon. Rounding arbitrary real durations changes the problem and needs an approximation statement.

For the baseline assumptions above, integer durations do not sacrifice an optimum even if continuous starts were initially allowed. Take a feasible schedule, preserve its processing order on every machine, and combine those orders with job precedences. Positive durations rule out a directed cycle in this graph. Starting every operation as early as its predecessors allow gives integer longest-path start times, no later finishes, and the same valid machine orders. This argument relies on the stated baseline assumptions; it should not be carried unexamined into models with extra temporal constraints.

### Example A · The supplied two-job instance

This is data from the supplied tutorial and repository, not a general assumption. Both jobs visit machine T and then machine F.

| Job | Duration on T | Duration on F |
|---|---:|---:|
| Z1 | 2 | 1 |
| Z2 | 1 | 2 |

One feasible schedule is Z2·T at 0, Z1·T at 1, Z2·F at 1, Z1·F at 3. Its makespan is 4. The fact that this is optimal will be proved in chapter 13. Nothing in the general formulation depends on these particular durations or on having only two machines.

<details class="check"><summary>Check your understanding · Can an operation finish at 3 and another start at 3 on the same machine?</summary><p>Yes. Their half-open intervals can touch without overlapping. For example, [1,3) and [3,5) have no common occupied time. Replacing a strict overlap test with a non-strict one would incorrectly forbid this.</p></details>

## 02 · What a QUBO represents {#qubo}

### General form

A binary variable, or **bit**, is a variable $x_i\in\{0,1\}$. A vector $x=(x_1,\ldots,x_N)$ is one candidate assignment of all $N$ decisions. There are $2^N$ such assignments.

A **quadratic unconstrained binary optimisation** problem chooses the bits to minimise

$$
E(x)=c_0+\sum_{i=1}^{N}a_i x_i+\sum_{1\le i<j\le N}w_{ij}x_i x_j.
$$

Here $a_i$, $w_{ij}$, and $c_0$ are fixed real coefficients chosen by the modeller. The solver chooses $x$, not the coefficients. The index condition $i<j$ means every unordered pair appears once. A missing pair has coefficient zero.

The product $x_i x_j$ is one exactly when **both** decisions are one. This is how a quadratic term can detect two incompatible choices being selected together. “Quadratic” means degree at most two: constants, individual bits, and products of two bits are allowed; products of three distinct bits are not.

“Unconstrained” means all $2^N$ bitstrings are legal inputs to $E$. It does not mean the original scheduling rules have disappeared. We must encode those rules in the energy, usually as penalties.

### Binary algebra: the simplification that matters

Since $0^2=0$ and $1^2=1$, every bit satisfies $x_i^2=x_i$. Thus a squared bit is linear. For example, $(x_i+x_j)^2=x_i+x_j+2x_ix_j$. This identity is valid only for binary inputs; it cannot be applied to a quantity that might equal $-1$.

### Example · A deliberately invented two-bit energy

This algebra example is not a scheduling instance. Let

$$
E(x_1,x_2)=1+3x_1-2x_2+4x_1x_2.
$$

| $(x_1,x_2)$ | Constant | Linear contribution | Pair contribution | Total |
|---|---:|---:|---:|---:|
| $(0,0)$ | 1 | 0 | 0 | 1 |
| $(0,1)$ | 1 | −2 | 0 | −1 |
| $(1,0)$ | 1 | 3 | 0 | 4 |
| $(1,1)$ | 1 | 1 | 4 | 6 |

The minimum is $-1$ at $(0,1)$. Negative energy is perfectly valid for a general QUBO. Later, our special feasibility construction will have nonnegative energy because we deliberately build it as a sum of nonnegative penalties.

### The constant shifts values, not decisions

Adding $c_0$ changes every energy by the same amount, so it does not change which bitstrings minimise the energy. But the offset matters when interpreting a numerical value. If you drop the offset from a feasibility model, a feasible schedule may no longer have energy zero. Never mix “zero in the complete energy” with “zero in the matrix part.”

<aside class="takeaway">A QUBO is a function on bitstrings. The meaning of its bits and its minimum must come from an explicit encoding and a correctness argument.</aside>

## 03 · Translate requirements into penalties {#penalties}

### General construction

A penalty for a condition is a function that is zero when that condition holds and strictly positive when it fails. If all penalties have this property and all their weights are positive, their sum is zero exactly when all conditions hold. This is the foundation of a feasibility QUBO.

#### Exactly one of $K$ choices

Let $x_1,\ldots,x_K$ represent mutually exclusive alternatives. Exactly one should be selected, so $\sum_{i=1}^Kx_i=1$. Define

$$
P_{\mathrm{once}}(x)=\left(\sum_{i=1}^Kx_i-1\right)^2.
$$

**Derivation.** Expand the square and use binary idempotence:

$$
\begin{aligned}
\left(\sum_i x_i-1\right)^2
&=\left(\sum_i x_i\right)^2-2\sum_i x_i+1\\
&=\sum_i x_i^2+2\sum_{i<j}x_ix_j-2\sum_i x_i+1\\
&=1-\sum_i x_i+2\sum_{i<j}x_ix_j.
\end{aligned}
$$

The coefficient $2$ appears because the expansion contains both $x_ix_j$ and $x_jx_i$. This factor belongs to the algebra, independently of how we later store the matrix.

If $n_{\mathrm{sel}}$ bits are selected, the penalty equals $(n_{\mathrm{sel}}-1)^2$: no selection costs 1; one selection costs 0; two selections cost 1; three cost 4. Thus **this penalty does not literally count the number of violated rules**. It measures a squared violation.

For $K=0$, the sum is empty and the penalty is 1. An operation with no allowed starts makes the horizon infeasible. For $K=1$, the penalty is $1-x_1$; a preprocessing step could fix $x_1=1$ and remove that bit.

#### Forbid one simultaneous pair

If decisions $x_i=1$ and $x_j=1$ may not occur together, use

$$
P_{\mathrm{pair}}(x_i,x_j)=x_ix_j.
$$

It is zero at 00, 01 and 10, and one at 11. This enforces **at most one of this pair**, not exactly one: 00 remains allowed. Exactly-once penalties will separately ensure that operations actually happen.

#### A more general equality

For real coefficients $d_i$ and a target $b$, a linear equality $\sum_i d_i x_i=b$ can be penalised by

$$
\left(\sum_i d_i x_i-b\right)^2
=b^2+\sum_i(d_i^2-2bd_i)x_i
+2\sum_{i<j}d_id_jx_ix_j.
$$

It remains quadratic because the expression inside the square is linear. Squaring a quadratic constraint would generally produce degree-four terms. Not every constraint becomes a QUBO merely by squaring it.

### Transformation workshop · What can actually become linear or quadratic?

First distinguish **three different operations** that are often loosely called “linearising.”

| Operation | What changes? | What must stay equivalent? |
|---|---|---|
| Binary simplification | Replace repeated powers using $x_i^r=x_i$. No new variables. | The value at every original binary assignment. |
| Quadratization | Replace degree-three-or-higher terms by quadratic terms, often with auxiliary bits and penalties. | Minimising over auxiliaries recovers the intended original energy or at least its minimisers, as explicitly specified. |
| Constrained linearisation | Replace a product by an auxiliary variable and linear constraints, producing a MILP-type formulation. | Feasible extended solutions project to exactly the original product relation. |

These operations have different outputs. A linear objective with constraints is not an unconstrained linear problem, and a quadratized function is not necessarily equal to the old polynomial on inconsistent auxiliary assignments.

#### Step A · Expand and remove repeated powers

The **degree** of a monomial is the number of variable factors, after binary powers are reduced. For example, $x_1^3x_2^2=x_1x_2$ is quadratic, whereas $x_1x_2x_3$ is cubic. A polynomial's degree is the largest degree of its nonzero terms after collecting cancellations. Expand complements such as $(1-x_i)$, combine equal monomials, and then inspect the result. A factored expression that looks complicated may simplify, but distinct-bit interactions generally remain.

For example, $x_1x_2+x_1(1-x_2)=x_1$ is linear because the pair terms cancel. In contrast, $x_1x_2$ alone cannot be represented by any affine expression $a+bx_1+cx_2$ on all four assignments: values at 00, 10, 01 force $a=b=c=0$, contradicting its value 1 at 11. There is no general identity that removes genuine interactions without changing the representation.

#### Step B · Use the structure before adding auxiliaries

A time-indexed model turns many apparently nonlinear start-time costs into linear sums. If $f_o(t)$ is any fixed cost of starting operation $o$ at time $t$, then on valid encodings the cost is $\sum_{t\in T_o}f_o(t)x_{o,t}$. The function $f_o$ may contain an absolute value, a maximum, or a square; it is evaluated on fixed candidate times before building the QUBO. This is exact because only one candidate is selected. Its price is potentially many time-indexed bits.

A cost depending on two chosen starts similarly becomes $\sum_{t\in T_o}\sum_{u\in T_v}f_{ov}(t,u)x_{o,t}x_{v,u}$, which is quadratic. A genuinely three-operation cost may require products of three indicators. Polynomial degree depends on both the original function **and the chosen representation**.

#### Step C · Quadratize a higher-order binary interaction

For a cubic term $c x_1x_2x_3$, introduce a binary auxiliary $q$ intended to equal $x_1x_2$. Replace the term by

$$
cqx_3+M\left(x_1x_2-2x_1q-2x_2q+3q\right).
$$

The consistency penalty in parentheses has this complete truth table:

| $(x_1,x_2)$ | Penalty at $q=0$ | Penalty at $q=1$ | Required $q$ |
|---|---:|---:|---:|
| $(0,0)$ | 0 | 3 | 0 |
| $(0,1)$ | 0 | 1 | 0 |
| $(1,0)$ | 0 | 1 | 0 |
| $(1,1)$ | 1 | 0 | 1 |

For each fixed original assignment, an inconsistent $q$ costs at least $M$ and can improve $cqx_3$ by at most $|c|$. Thus $M>|c|$ ensures the minimum over $q$ uses the correct product and recovers the original cubic value. If $q$ participates in several substituted terms, bound their **combined** possible benefit instead. Repeated product substitutions reduce arbitrary finite binary polynomials to quadratic form, at the cost of auxiliary variables and potentially large weights. This generic construction is exact with sufficient bounds; it need not be the most efficient quadratization.

#### Step D · Linearise a product when keeping explicit constraints

For binary $u,v$, introduce $q$ and impose

$$
0\le q,\qquad q\le u,\qquad q\le v,\qquad q\ge u+v-1.
$$

When $(u,v)$ is 00, 01 or 10, an upper bound forces $q=0$. When it is 11, the lower bound forces $q=1$. These linear constraints therefore enforce $q=uv$ exactly. A quadratic objective term $wuv$ becomes linear $wq$, but the formulation is now **constrained**. Keeping all original bits integral yields a mixed-integer linear model; relaxing them to fractions changes the problem. Feeding only the linear objective to an unconstrained solver and dropping the linking constraints is incorrect. To return to QUBO, those constraints must be encoded again, for example by the product-consistency penalty above.

#### Step E · Do not square the wrong relation

The equation $q=uv$ suggests $(q-uv)^2$, but binary simplification gives $q+uv-2quv$, which is cubic. The specially constructed penalty above is quadratic and has the same zero set. A useful penalty does not have to be the square of the most obvious residual.

More generally, every function of finitely many bits can be written as a multilinear polynomial by summing a coefficient times an assignment indicator over all input assignments. That establishes representability, not efficiency: the direct expression can be exponential in the number of bits and need many auxiliaries. “Can be expressed as QUBO” and “has a useful small QUBO” are different claims.

<details class="check"><summary>Check your understanding · Why not penalise exactly-once by the unsquared expression?</summary><p>The residual can be negative. Selecting no alternatives makes “sum minus one” equal −1, which a minimiser would reward. Squaring makes both under-selection and over-selection nonnegative while preserving zero at exactly one.</p></details>

## 04 · Build the general time-indexed scheduling QUBO {#formulation}

### Step 1 · Choose a horizon and safe start windows

We temporarily ask a decision question: **does a feasible schedule finish by $H$?** The objective of minimising makespan will return in chapter 06.

For an operation $o$ in a job chain, let $h_o$ be the sum of processing times **before** $o$ in that job, and let $\tau_o$ be the sum **after** $o$. Neither includes $p_o$. Every schedule finishing by $H$ must satisfy

$$
h_o\le S_o\le H-p_o-\tau_o.
$$

The left bound leaves time for predecessors. The right bound leaves time for this operation and its successors. Define

$$
T_o=\{t\in\mathbb Z:h_o\le t\le H-p_o-\tau_o\},\qquad K_o=|T_o|.
$$

Here $\mathbb Z$ denotes integers and $|T_o|$ the number of allowed starts. If the upper bound is below the lower bound, $T_o$ is empty. These bounds are **necessary, not sufficient**: machine competition and the actual selected predecessor start can make an allowed time unusable.

For a general acyclic precedence graph, replace chain sums by a longest-path processing-time bound before and after $o$. The remainder of the QUBO construction is unchanged. The simple bit-count formula below specifically uses job chains.

**Derivation of the count.** Let job $j$ contain $q_j$ operations and have total duration $P_j$. Since $h_o+p_o+\tau_o=P_j$ for each of its operations,

$$
K_o=\max\{0,H-P_j+1\},\qquad
N=\sum_{o\in\mathcal O}K_o=\sum_jq_j\max\{0,H-P_j+1\}.
$$

The $+1$ counts both endpoints of an integer interval. In an $n$-job, $m$-machine flow shop with one visit to each machine, $q_j=m$. If every $P_j\le H$, this simplifies to $N=m\sum_j(H-P_j+1)$. These are counts for this one-hot formulation before fixing singleton bits, not claims of the smallest possible formulation.

### Step 2 · Assign a precise meaning to every bit

For each operation and each surviving start time, introduce

$$
x_{o,t}=\begin{cases}1&\text{operation }o\text{ starts at }t,\\0&\text{it does not.}\end{cases}
$$

There is no bit for a pruned time. We are not setting such a bit to zero later; it is absent from the model. The bits of one operation form its **one-hot group**.

### Step 3 · Require exactly one start per operation

$$
P_{\mathrm{once}}(x)=\sum_{o\in\mathcal O}\left(\sum_{t\in T_o}x_{o,t}-1\right)^2.
$$

This also detects an operation with an empty domain, because its summand is 1.

### Step 4 · Enumerate machine conflicts

Two candidate occupied intervals $[t,t+p_o)$ and $[u,u+p_v)$ overlap exactly when

$$
t<u+p_v\quad\text{and}\quad u<t+p_o.
$$

Both inequalities are strict. The first prevents the second operation finishing before the first starts; the second prevents the reverse ordering.

Fix any ordering of operation labels and write $o<v$ to enumerate each pair once. Let $\mathcal C$ contain every pair of candidate starts $((o,t),(v,u))$ with $o<v$, $\mu(o)=\mu(v)$, and the overlap condition above. Then

$$
P_{\mathrm{cap}}(x)=\sum_{((o,t),(v,u))\in\mathcal C}x_{o,t}x_{v,u}.
$$

This detects capacity violations between distinct operations. Within an operation, exactly-once already handles multiple selected starts. In a general job shop, two operations of the same job may revisit one machine; use operation identities, rather than assuming “same machine” always means “different jobs.”

### Step 5 · Enumerate precedence conflicts

For each arc $(o,v)\in\mathcal A$, selected starts $t,u$ violate precedence precisely when $u<t+p_o$. Let $\mathcal D$ contain these directed conflicting candidate-start pairs. Define

$$
P_{\mathrm{prec}}(x)=\sum_{((o,t),(v,u))\in\mathcal D}x_{o,t}x_{v,u}.
$$

Only adjacent job-chain arcs are needed: satisfying every adjacent precedence implies every transitive one. Adding redundant transitive arcs can change nonzero energies and couplings without changing the feasible schedules.

### Step 6 · Combine the penalties

For any strictly positive weights,

$$
E_H(x)=\lambda_{\mathrm{once}}P_{\mathrm{once}}(x)
+\lambda_{\mathrm{cap}}P_{\mathrm{cap}}(x)
+\lambda_{\mathrm{prec}}P_{\mathrm{prec}}(x).
$$

It is a QUBO: exactly-once squares expand to degree two, and the other terms are already products of bits. For pure feasibility all three weights may equal 1. Their relative values affect heuristic search, but not which states have zero complete energy.

### Guarantee · Zero energy if and only if feasibility within $H$

**Forward direction.** If $E_H(x)=0$, every nonnegative penalty must be zero. Exactly-once gives one selected $t\in T_o$ for every operation. Set $S_o=t$. No selected pair lies in $\mathcal C$, so machines do not overlap. No selected pair lies in $\mathcal D$, so all precedences hold. The windows ensure nonnegative starts and completion by $H$.

**Reverse direction.** Given any feasible integer schedule finishing by $H$, its starts lie in the safe windows. Select exactly those starts. Every exactly-once penalty is zero. Feasibility prevents every selected machine or precedence conflict. Hence the resulting bitstring has energy zero.

Both directions matter: the first excludes false solutions (**soundness**); the second ensures we did not accidentally remove real solutions (**completeness**).

<aside class="takeaway">Safe pruning reduces the number of choices. Conflict penalties enforce compatibility between the choices that remain. Those are different jobs.</aside>

## 05 · Convert the energy into a matrix without factor errors {#matrix}

### One indexing map connects scheduling to linear algebra

List all surviving pairs $(o,t)$ in a fixed order and let $i=\phi(o,t)\in\{1,\ldots,N\}$. Write $x_i=x_{o,t}$. This is a relabelling of the same decisions, not another encoding. Store this mapping next to the coefficients so a returned vector can be decoded.

An $N\times N$ matrix $Q$ has an entry $Q_{ij}$ in row $i$, column $j$. Regard $x$ as a column vector and $x^\mathsf T$ as its transpose, a row vector. Matrix multiplication gives the scalar

$$
x^\mathsf TQx=\sum_{i=1}^N\sum_{j=1}^NQ_{ij}x_ix_j
=\sum_iQ_{ii}x_i+\sum_{i<j}(Q_{ij}+Q_{ji})x_ix_j.
$$

The second equality uses $x_i^2=x_i$ on the diagonal and combines the two orders of each off-diagonal pair. It explains all factor-of-two conventions.

### Our convention · Upper triangular

For the polynomial $E=c_0+\sum_i a_ix_i+\sum_{i<j}w_{ij}x_ix_j$, use

$$
Q_{ii}=a_i,\qquad Q_{ij}=w_{ij}\ (i<j),\qquad Q_{ij}=0\ (i>j).
$$

Then $E=x^\mathsf TQx+c_0$. A symmetric convention is also possible: put $w_{ij}/2$ in both mirror cells. Do not put the full $w_{ij}$ in both cells: that doubles the interaction.

### General coefficient recipe for chapter 04

Start every linear coefficient and pair coefficient at zero. Each exactly-once group contributes $-\lambda_{\mathrm{once}}$ to every member's linear coefficient, $2\lambda_{\mathrm{once}}$ to every pair inside that group, and $\lambda_{\mathrm{once}}$ to the offset. Each machine conflict adds $\lambda_{\mathrm{cap}}$ to its pair; each precedence conflict adds $\lambda_{\mathrm{prec}}$.

**Add contributions; do not overwrite them.** If two rules affect the same pair, both contributions belong in the energy. For the supplied flow shop, the same-operation, machine-conflict, and precedence-conflict pair classes are disjoint. That disjointness is a feature of that baseline, not a universal property.

### Example · Matrix for the invented energy from chapter 02

$$
Q=\begin{pmatrix}3&4\\0&-2\end{pmatrix},\quad c_0=1.
$$

Multiplying gives $x^\mathsf TQx=3x_1^2+4x_1x_2-2x_2^2=3x_1+4x_1x_2-2x_2$. For $x=(1,1)$, add the four matrix entries and the offset: $3+4+0-2+1=6$.

If matrix multiplication is new, the intermediate step is $Qx=(3x_1+4x_2,-2x_2)^\mathsf T$: multiply each matrix row by the column, matching positions, then add. Multiplying that result by the row $x^\mathsf T$ gives $x_1(3x_1+4x_2)+x_2(-2x_2)$. Thus the compact matrix notation is just bookkeeping for the same polynomial, not another objective.

### How to evaluate and store it

Only entries whose row bit **and** column bit are 1 contribute. Equivalently, select the rows and columns indexed by the active bits, sum their intersections, and add $c_0$. This is just $x_ix_j$ written visually.

Sparse storage usually keeps the list $(a_1,\ldots,a_N)$, nonzero triples $(i,j,w_{ij})$ with $i<j$, and the offset $c_0$. A program may number from zero. An index conversion must change labels consistently, not the mathematics.

<details class="check"><summary>Check your understanding · What is the symmetric matrix for this two-bit example?</summary><p>The diagonal stays (3, −2), and both off-diagonal cells become 2. Then their sum is 4, the required pair coefficient. The offset remains 1.</p></details>

## 06 · Recover makespan minimisation from feasibility tests {#horizon}

At one fixed $H$, every feasible schedule has $E_H=0$. The energy does **not** rank these schedules by makespan. A schedule finishing earlier and another finishing exactly at $H$ may both have zero energy.

### General principle · Feasibility is monotone in the deadline

If a schedule finishes by $H$, the same schedule also finishes by any larger horizon. With safe complete domains, “a feasible schedule exists” changes only from false to true as $H$ increases. Thus

$$
C_{\max}^*=\min\{H\in\mathbb Z_{\ge0}:\min_xE_H(x)=0\}.
$$

The star denotes the optimal makespan. This equality is a mathematical statement about exact minima. A heuristic search is not an exact decision oracle.

### Obtain lower and upper bounds

Under the baseline assumptions, every schedule must satisfy

$$
C_{\max}^*\ge
\max\left\{\max_jP_j,\ \max_{k\in\mathcal M}\sum_{o:\mu(o)=k}p_o\right\}.
$$

The first bound is the longest job's own sequential work. The second is the busiest machine's workload. Neither includes every possible bottleneck, so stronger bounds may be available. Scheduling all operations serially, respecting job order, gives the simple feasible upper bound $\sum_op_o$. A constructed schedule gives a potentially much tighter upper bound.

Search integer horizons between a valid lower bound and a feasible upper bound. Linear search, descending search, or binary search with an **exact** feasibility solver are all possible.

### Treat a heuristic result as three-valued

| Result at $H$ | Valid conclusion | Next step |
|---|---|---|
| A decoded schedule independently passes validation | Feasible at $H$ | Tighten the upper bound. |
| Exact proof that no feasible schedule exists | Infeasible at $H$ | Raise the lower bound. |
| No feasible sample found within the budget | Unknown | Increase search, change method, or retain the unresolved gap. |

A positive best sampled energy is the third case. Treating it as a proof of infeasibility can incorrectly discard the true optimum. An exact QUBO minimum above zero does prove infeasibility, provided the formulation and offset are correct.

<aside class="takeaway">A validated schedule proves an upper bound. A lower-bound argument or exact certificate proves a lower bound. Optimality follows when the two meet.</aside>

## 07 · Understand encoding trade-offs for arbitrary numbers of choices {#encodings}

### General decision: choose one of $K$ alternatives

Fix an operation with $K\ge1$ allowed starts, sorted as $t_0<\cdots<t_{K-1}$. Use $r\in\{0,\ldots,K-1\}$ for the **rank of the choice**, not its time. Rank $r$ means start at $t_r$. They coincide only if the first start is zero and the grid step is one.

For this chapter, $\chi_r$ denotes the indicator “choice $r$ is selected.” In one-hot it is $x_{o,t_r}$ itself. Other encodings express it as a function of different bits. The scheduling conflicts still use products $\chi_r\chi_s$ belonging to two operations.

An encoding uses $b$ bits to give each of the $K$ alternatives a distinct **codeword**. Unused bitstrings need special handling. Every injective encoding needs $2^b\ge K$, hence $b\ge\lceil\log_2K\rceil$. Meeting this information bound does not ensure the encoded energy is quadratic.

### One-hot · Direct indicators

Use $K$ bits, with one bit per alternative. Set $\chi_r=x_{o,t_r}$ and enforce exactly one by chapter 03. Indicators are linear, so pairwise scheduling conflicts remain quadratic.

For the **invented encoding illustration $K=4$**, the codewords in rank order are 1000, 0100, 0010, 0001. Four of sixteen bitstrings are encoding-valid. This example is purely a four-choice variable, not a new scheduling instance.

### Domain wall · Threshold indicators

Use $K-1$ bits $y_{o,1},\ldots,y_{o,K-1}$, with the meaning

$$
y_{o,s}=1\quad\Leftrightarrow\quad r\ge s.
$$

A valid word is a prefix of ones followed by zeros. Rank $r$ has exactly $r$ initial ones. In the $K=4$ illustration, ranks 0,1,2,3 are 000, 100, 110, 111.

Add fixed boundary values $y_{o,0}=1$, $y_{o,K}=0$. Then every indicator is affine (a constant plus linear terms):

$$
\chi_r=y_{o,r}-y_{o,r+1},\qquad r=0,\ldots,K-1.
$$

For a monotone valid word, there is one transition from 1 to 0, so exactly one indicator is 1. The sum telescopes:

$$
\sum_{r=0}^{K-1}\chi_r=y_{o,0}-y_{o,K}=1.
$$

But the sum is also 1 on **invalid** words. For $K=4$, word 010 gives $(\chi_0,\chi_1,\chi_2,\chi_3)=(1,-1,1,0)$. It does not represent a valid choice. A sum of one is insufficient when indicators can be negative.

Enforce monotonicity with

$$
P_{\mathrm{wall}}(y)=\sum_o\sum_{s=1}^{K_o-2}(1-y_{o,s})y_{o,s+1}.
$$

Each summand detects an upward transition 0→1. The sum is zero exactly for valid domain-wall words. For $K=1$ no bits are needed: the unique indicator is the constant 1. For $K=2$ there is one bit, both bitstrings are valid, and there is no wall term. Handle empty domains separately as an infeasible horizon.

### Why substituting domain-wall indicators preserves degree

Each $\chi_r$ is affine, so a product of two indicators has degree at most two. Therefore the **conflict part** of the scheduling energy remains quadratic after substitution. Replace exactly-once constraints by the wall constraint; do not blindly substitute into an already simplified one-hot square. That simplification used $\chi_r^2=\chi_r$, which is false for an invalid indicator equal to $-1$.

For a domain-wall feasibility model, use

$$
E_H^{\mathrm{DW}}(y)=C(y)+\eta P_{\mathrm{wall}}(y),
$$

where $C(y)$ is the substituted weighted capacity and precedence conflict sum. On valid words, $C$ equals the original conflict sum. On invalid words, it may be negative. Consequently **an arbitrary positive wall weight is not enough**.

### Guarantee · A sufficient wall weight

Write the original conflict sum as a sum of nonnegative weighted products $\kappa_{ab}\chi_a\chi_b$ over different operations. Here $a,b$ label candidate starts, not bits in the new encoding. Define the weighted incident degree

$$
d_a=\sum_{b:\{a,b\}\text{ is a conflict}}\kappa_{ab},\qquad d_{\max}=\max_a d_a.
$$

Choose $\eta>d_{\max}$. To see why, let $V=P_{\mathrm{wall}}(y)$. Each upward transition creates exactly one negative indicator, so there are $V$ negative indicators. Every indicator is in $\{-1,0,1\}$. A negative conflict term must touch a negative indicator; charging it to that endpoint bounds total negative conflict energy by $d_{\max}V$. All remaining terms are nonnegative. Hence

$$
E_H^{\mathrm{DW}}(y)\ge(\eta-d_{\max})V>0\quad\text{if }V>0.
$$

If $V=0$, the indicators are valid and the original feasibility proof applies. Thus zero energy again means exactly feasible. With integral conflict weights, $\eta=d_{\max}+1$ is convenient. This proof assumes only those nonnegative pairwise conflicts; additional signed objectives require a new bound.

<details class="derivation"><summary>Example · Why a weak wall penalty can create false zero energy</summary><p>This is an invented three-choice variable A and a fixed-choice variable B. Let the only conflict cost be χ<sub>A,1</sub>χ<sub>B,0</sub>, with χ<sub>B,0</sub>=1. Valid A ranks have costs 0, 1, 0. The invalid A word 01 has indicators (1, −1, 1), so its conflict cost is −1. A wall weight η=1 adds 1 and creates false total energy 0. Here d<sub>max</sub>=1; choosing η&gt;1 excludes that state. The example demonstrates the need for a strict bound, not a universal optimal choice of penalty.</p></details>

### Binary positional encoding · Fewer decision bits, potentially higher degree

Let $b=\lceil\log_2K\rceil$ and represent the rank as

$$
r=\sum_{s=0}^{b-1}2^s u_{o,s}.
$$

Codes with $r\ge K$ are unused. If the binary digits of a particular rank $r$ are $r_s$, its indicator is

$$
\chi_r(u)=\prod_{s=0}^{b-1}\begin{cases}u_{o,s}&r_s=1,\\1-u_{o,s}&r_s=0.\end{cases}
$$

The indicator generally has degree $b$. A conflict between two operations can have degree up to the sum of their bit counts. In the $K=4$ illustration, a rank-zero conflict becomes $(1-u_{o,0})(1-u_{o,1})(1-u_{v,0})(1-u_{v,1})$, which contains a degree-four term. All four codes are valid here; avoiding unused codes does **not** avoid the higher degree.

One can sometimes simplify these expressions, redesign the formulation, or reduce higher-order terms with auxiliary bits. The resulting total bits and penalty guarantees must include those auxiliaries. A logarithmic encoding count alone is not the size of a completed QUBO.

The transformation workshop in chapter 03 derives a product auxiliary, its complete consistency table, and a sufficient penalty bound. That construction is one route from these binary-encoded higher-order interactions back to a QUBO; it does not make the auxiliary-bit cost disappear.

### Compare what each encoding actually buys

| Encoding | Bits for one $K$-choice variable | Valid words | Degree of its indicators | Extra issue |
|---|---:|---:|---:|---|
| One-hot | $K$ | $K$ | 1 | Exactly-once penalty or a preserving mixer. |
| Domain wall | $K-1$ | $K$ | 1 (affine) | Monotonicity and a sufficient wall weight. |
| Binary positional | $\lceil\log_2K\rceil$ | $K$ | Up to $\lceil\log_2K\rceil$ | Unused codes and possible degree reduction. |

The table concerns $K\ge1$. Fixed single-choice variables may be removed in every encoding. Better qubit count alone does not imply better runtime: coupling density, coefficient range, graph embedding, circuit routing, and search difficulty also matter.

### Encoding-valid probability is not feasibility probability

If a circuit samples uniformly from all $2^N$ basis bitstrings and the encoding gives one codeword per choice, then

$$
\Pr(\text{encoding-valid})=\frac{\prod_o K_o}{2^N}.
$$

The numerator counts all combinations of one choice per operation. Many combinations can still violate scheduling constraints. This formula applies to a uniform distribution, such as the initial all-plus state of standard QAOA. It does not describe the distribution after arbitrary trained layers, nor a custom initial state.

<div id="encoding-lab" class="lab" aria-label="Interactive encoding comparison"><p>The encoding laboratory requires JavaScript. The general formulas and worked examples above remain readable without it.</p></div>

## 08 · Add an objective without rewarding infeasibility {#objectives}

### General distinction

A feasibility energy has the same value on all feasible schedules. To prefer feasible schedules with lower cost, add an objective $F(x)$. Examples include total weighted completion time, tardiness, or changes relative to an old schedule. Decide first whether each new requirement is **hard** (must hold) or **soft** (may be traded against cost).

Let $P(x)\ge0$ be a complete penalty function with $P(x)=0$ exactly on feasible encodings. Consider

$$
E(x)=\rho P(x)+F(x),\qquad\rho>0.
$$

The objective must be defined on **every** bitstring, including invalid ones, because the solver can visit them. A formula that makes sense only after successful decoding is not yet a complete QUBO objective.

### Guarantee · A conservative global penalty bound

Assume at least one feasible encoding exists. Suppose every infeasible bitstring has $P(x)\ge\delta>0$, and bounds $F_{\min}\le F(x)\le F_{\max}$ hold for **all** bitstrings. Then

$$
\rho\delta>F_{\max}-F_{\min}
$$

ensures every global minimum is feasible. Indeed, an infeasible energy is at least $\rho\delta+F_{\min}>F_{\max}$, while any feasible energy is at most $F_{\max}$. Among feasible states the penalty vanishes, so minimising the energy minimises $F$.

For an unweighted integral feasibility penalty from chapter 04, $\delta=1$ is safe. A tighter bound can use one known feasible solution with objective $U$: it is sufficient that $\rho\delta+F_{\min}>U$. Strict inequality prevents an infeasible state tying a feasible minimum.

This is a sufficient guarantee, not the smallest practical penalty. Excessively large weights can worsen numerical resolution and search behaviour after rescaling. A vague “make the penalty bigger than one violation's gain” is inadequate unless that gain and the way multiple violations interact have actually been bounded.

### Example · Invented penalty-versus-reward trade-off

Let a single bit be required to equal 1. Use $P(x)=(x-1)^2$ and a soft cost $F(x)=5x$. Then the feasible state has energy 5; the infeasible state has energy $\rho$. A weight below 5 rewards infeasibility, a weight equal to 5 creates a tie, and a weight above 5 makes the feasible state strictly better.

### Some objectives are directly linear in start indicators

If job $j$ ends with operation $o_j$, its completion time on a valid one-hot encoding is $\sum_{t\in T_{o_j}}(t+p_{o_j})x_{o_j,t}$. Weighted completion time is therefore linear in those bits.

For due date $d_j$ and weight $v_j\ge0$, soft tardiness can also be precomputed:

$$
F_{\mathrm{tardy}}(x)=\sum_j\sum_{t\in T_{o_j}}
v_j\max\{0,t+p_{o_j}-d_j\}\,x_{o_j,t}.
$$

Each maximum is calculated from fixed data before optimisation, so this is linear in $x$. A **hard** completion deadline can instead remove all final-operation starts that miss it, followed by safe propagation. These particular inequalities do not inherently require slack bits.

### Other inequalities may use slack

For an integer linear constraint $g(x)\le b$, introduce a nonnegative integer slack $s=b-g(x)$ with enough representable range, then penalise $(g(x)+s-b)^2$. Encoding $s$ with bits keeps this quadratic when $g$ and $s$ are linear in the bits. Choose a range that includes the slack needed by every permitted $x$; an insufficient range removes real solutions. Alternative asymmetric penalties can save auxiliaries, but require their own ground-state guarantee or explicit acknowledgement of approximation.

**Example · Invented slack construction.** To enforce $2x_1+3x_2\le3$, the required nonnegative slack ranges from 0 to 3 on feasible assignments. Two new binary slack digits $\sigma_0,\sigma_1$ encode $s=\sigma_0+2\sigma_1$. The penalty is $(2x_1+3x_2+\sigma_0+2\sigma_1-3)^2$. Applying chapter 03's general equality expansion gives offset 9; linear coefficients $(-8,-9,-5,-8)$ in the order $(x_1,x_2,\sigma_0,\sigma_1)$; and pair coefficients $(12,4,8,6,12,4)$ in the order $(12,13,14,23,24,34)$. It is a four-bit QUBO. At $(x_1,x_2)=(1,0)$, choose slack 1 to get zero. At $(1,1)$, the load is 5 and even zero slack leaves penalty 4; a nonnegative slack cannot undo an overload.

For a general integer inequality with known lower bound $g_{\min}$, a safe slack upper bound is $b-g_{\min}$ when this is nonnegative. Ordinary binary encoding with $\lceil\log_2(b-g_{\min}+1)\rceil$ digits covers that range. Extra encoded slack values beyond the required maximum cannot make the equality hold for an invalid overload, because the slack remains nonnegative. If $g_{\min}>b$, the inequality is already impossible. Tightening bounds can reduce auxiliary bits before any solver is called.

### Why an asymmetric penalty is a different contract

[Unbalanced penalization](https://arxiv.org/abs/2211.13914) avoids slack variables by giving the two sides of an inequality different energy treatment. It must not inherit the proof for a nonnegative penalty that vanishes on **every** feasible state.

To see the issue independently, take residual $r(x)=g(x)-b$, so feasibility means $r\le0$. An illustrative asymmetric quadratic is $A r+B r^2$ with positive constants $A,B$. If $g$ is linear, this stays quadratic without auxiliaries. But its minimum as a function of the residual is at $r=-A/(2B)$, inside the feasible side. Thus it generally assigns different energies to different feasible solutions and can change the objective ordering. This illustrative algebra explains the trade-off; it is not a claim about one paper's recommended coefficients. Reducing bit count may sacrifice an exact original-objective correspondence unless a separate argument restores it. Always check the original objective and feasibility, not just proximity to the encoded ground energy.

<aside class="takeaway">A hard constraint needs a correctness guarantee. A soft objective needs an explicit trade-off. Calling both “costs” does not make them interchangeable.</aside>

### Makespan, maxima and absolute values

The makespan is the **maximum** completion time, not the sum. Replacing it by total completion time changes the objective. Horizon search avoids this issue by solving a sequence of feasibility problems.

For a direct constrained formulation, introduce a variable $C$ and enforce $C\ge S_o+p_o$ for every operation. Minimising $C$ then makes it the maximum finish. This is an **epigraph** formulation: an upper-bounding variable becomes tight when minimised. In a binary QUBO, $C$ must itself be encoded over an adequate range, the inequalities must be enforced, any slack must be encoded, and the penalty-versus-objective bound must include all these bits. The symbol “max” has not vanished for free; its meaning moved into variables and constraints.

Similarly, in a constrained minimisation with positive weight, $d\ge S_o-\bar S_o$, $d\ge\bar S_o-S_o$ and $d\ge0$ let $d$ represent $|S_o-\bar S_o|$ at an optimum. Here $\bar S_o$ is a fixed old start. In the time-indexed formulation, a simpler exact alternative is to precompute $|t-\bar S_o|$ for each candidate start and use $\sum_t|t-\bar S_o|x_{o,t}$. A penalty for “changed at all” uses coefficients $\mathbf1[t\ne\bar S_o]$, where $\mathbf1[\cdot]$ is 1 when its condition holds and 0 otherwise. These are different notions of schedule churn and should not be mixed.

### Extension workshop · Know which part of the model changes

| Added feature | Exact modelling route in this representation | What needs care |
|---|---|---|
| Release time $r_o$ | Remove starts below $r_o$ and propagate precedence bounds. | Release dates can make the earlier baseline integer-time argument require corresponding integer data. |
| Fixed machine outage $[a,b)$ | Remove candidate starts whose processing intervals overlap the outage. | Use interval overlap, not just “start lies in outage.” |
| Minimum precedence lag $\ell_{ov}$ | Forbid $u<t+p_o+\ell_{ov}$ on arc $(o,v)$. | Recompute safe head/tail bounds; do not retain a pruning proof for different lags. |
| No-wait link | Permit only $u=t+p_o$ for the linked pair. | An equality is stronger than the usual minimum-lag condition. |
| Soft due dates | Precompute tardiness coefficients on final-operation starts. | They are costs, not hard feasibility restrictions. |
| Fixed resource capacity greater than one | Constrain the sum of active resource demand in every time slot. | Pairwise incompatibility is insufficient for higher capacities. |
| Alternative machines | Use choices indexed by both machine and start. | One operation still chooses exactly one alternative; durations may depend on the chosen machine. |
| Sequence-dependent setup | Introduce explicit immediate-predecessor information, or an equivalent complete sequence model. | A setup depends on adjacency, not merely on two jobs sharing a machine. |
| Transport or AGVs | Add transport operations/resources if transport competes for vehicles. | A fixed lag alone cannot represent a shared vehicle bottleneck. |

For capacity $B_k$ on resource $k$ in integer slot $\theta$, let $d_{ok}$ be operation $o$'s fixed demand on that resource. The active load is linear in the start indicators:

$$
L_{k,\theta}(x)=\sum_o\sum_{t\in T_o:\ t\le\theta<t+p_o}d_{ok}x_{o,t}.
$$

Enforce $L_{k,\theta}(x)\le B_k$ for each relevant slot. With integer demands, slack makes this a squared linear equality and hence a QUBO, using enough slack bits. For capacity two with unit demands, three simultaneous operations violate capacity even though every pair fits; a list of forbidden pairs alone cannot express this threshold. This explains exactly where the simple capacity-one construction stops applying.

For alternative-machine choices, candidate $(o,k,t)$ has its own indicator and duration $p_{o,k}$. Conflict tests must use the selected alternatives' durations and resource assignments. There may now be more than one alternative at the same time, so a rank must enumerate alternatives, not be mistaken for elapsed time.

For a fixed-order two-machine flow shop, a permutation representation can use $n^2$ position bits, with one job per position and one position per job. Given a common job sequence $\pi$, its earliest completion times satisfy the max-plus recurrence

$$
C_{r,k}=\max\{C_{r-1,k},C_{r,k-1}\}+p_{\pi(r),k},
$$

with zero boundary values. This is an exact classical **decoder** for that permutation schedule. It does not establish that makespan is quadratic in the position bits. A formulation must encode the recurrence, derive another exact objective, or explicitly use classical decoded-objective search. Moreover, imposing one common permutation can restrict a general flow-shop problem; it is not a general job-shop encoding. Small permutation bit counts should not be compared with complete time-indexed QUBO counts without accounting for these differences.

## 09 · Convert QUBO to Ising, coefficient by coefficient {#ising}

An Ising model uses classical spins $z_i\in\{-1,+1\}$ instead of bits. We fix the convention

$$
x_i=\frac{1-z_i}{2},\qquad x_i=0\Leftrightarrow z_i=+1,\quad x_i=1\Leftrightarrow z_i=-1.
$$

This bijection changes representation, not the underlying optimisation. Other libraries may choose the opposite sign; changing convention requires changing coefficients consistently.

### Derivation · Expand a generic linear and pair term

$$
a_ix_i=\frac{a_i}{2}-\frac{a_i}{2}z_i,
$$

$$
w_{ij}x_ix_j=\frac{w_{ij}}4\left(1-z_i-z_j+z_iz_j\right).
$$

Each pair contributes to a constant, to **both** local spin fields, and to one spin-spin coupling. Collecting everything gives

$$
E(z)=c_I+\sum_i h_i z_i+\sum_{i<j}J_{ij}z_i z_j,
$$

$$
J_{ij}=\frac{w_{ij}}4,\qquad
h_i=-\frac{a_i}{2}-\frac14\left(\sum_{j<i}w_{ji}+\sum_{j>i}w_{ij}\right),
$$

$$
c_I=c_0+\frac12\sum_i a_i+\frac14\sum_{i<j}w_{ij}.
$$

The coefficients here come from our polynomial with each pair counted once. They must not be applied unmodified to a symmetric matrix whose off-diagonal entries are half-pair coefficients.

### Example · Reuse the invented two-bit polynomial

For $c_0=1$, $a_1=3$, $a_2=-2$, $w_{12}=4$, the transformed coefficients are $c_I=5/2$, $h_1=-5/2$, $h_2=0$, $J_{12}=1$. Therefore

$$
E(z)=\frac52-\frac52z_1+z_1z_2.
$$

The bit optimum $(0,1)$ corresponds to spins $(+1,-1)$, giving $5/2-5/2-1=-1$, the same energy. Checking every bitstring under $z_i=1-2x_i$ is a useful automatic conversion audit.

### From classical spins to a quantum operator

Let $|x\rangle$ denote the computational basis state labelled by bitstring $x$. A quantum Pauli operator $Z_i$ has eigenvalue $+1$ on a zero in position $i$ and $-1$ on a one. Replace each classical $z_i$ by $Z_i$:

$$
\widehat H_C=c_I I+\sum_i h_iZ_i+\sum_{i<j}J_{ij}Z_iZ_j.
$$

The identity operator $I$ leaves every state unchanged. This **cost Hamiltonian** is diagonal in the computational basis and satisfies

$$
\widehat H_C|x\rangle=E(x)|x\rangle.
$$

Thus its eigenvalues are the classical bitstring energies. A ground state is any state with minimum energy. There may be several optimal basis bitstrings; superpositions within their span are also ground states. For the fixed-horizon feasibility QUBO, a zero-energy ground state corresponds to feasible schedules only when that horizon is feasible. At an infeasible horizon, every basis state violates something, including the ground states.

An **eigenvector** of an operator is a nonzero vector whose direction is unchanged by the operator: it is multiplied by a scalar, its **eigenvalue**. Here that vector is $|x\rangle$ and the scalar is $E(x)$. “Diagonal” means the operator changes the coefficient of each basis vector without mixing it with other basis vectors. A **span** is the set of linear combinations of specified vectors.

## 10 · The quantum ideas needed to understand QAOA {#quantum}

### A quantum state is a vector of amplitudes

One qubit is a quantum system with two basis states. We represent them as $|0\rangle=(1,0)^\mathsf T$ and $|1\rangle=(0,1)^\mathsf T$. The brackets are **ket notation** for vectors. A general pure state is

$$
|\psi\rangle=\alpha_0|0\rangle+\alpha_1|1\rangle,
\qquad |\alpha_0|^2+|\alpha_1|^2=1.
$$

The amplitudes $\alpha_0,\alpha_1$ are complex numbers. A complex number has the form $a+\mathrm i b$, where $\mathrm i^2=-1$, and squared magnitude $|a+\mathrm i b|^2=a^2+b^2$. The upright $\mathrm i$ here is the imaginary unit, not a bit index.

The complex conjugate of $a+\mathrm i b$ is $a-\mathrm i b$. A conjugate transpose turns a column into a row and conjugates its entries. “Pure state” means a state described by one such normalised vector; a statistical mixture of states is a more general description that is not needed for the ideal circuits derived here.

Measuring in this basis returns 0 with probability $|\alpha_0|^2$ and 1 with probability $|\alpha_1|^2$. It returns one outcome, not the full vector of amplitudes.

For $N$ qubits there is one basis vector per bitstring:

$$
|\psi\rangle=\sum_{x\in\{0,1\}^N}\alpha_x|x\rangle,
\qquad\sum_x|\alpha_x|^2=1.
$$

The statevector has $2^N$ complex entries. A classical exact statevector simulator explicitly stores these entries; quantum hardware does not hand us a readable list of all of them. Exponential state dimension by itself is not a proof of useful computational speedup.

### The tensor product combines qubits

The symbol $\otimes$ combines systems. For example, $|0\rangle\otimes|1\rangle=|01\rangle$. The one-qubit plus state and the all-plus product state are

$$
|+\rangle=\frac{|0\rangle+|1\rangle}{\sqrt2},\qquad
|+\rangle^{\otimes N}=\frac1{\sqrt{2^N}}\sum_x|x\rangle.
$$

Measuring the all-plus state samples every bitstring equally. A superposition is not just a classical random choice: its amplitudes have relative phases that can affect later outcomes.

### Phase matters only through later interference

A factor $e^{\mathrm i\theta}=\cos\theta+\mathrm i\sin\theta$ has magnitude one. Multiplying one amplitude by it changes its **phase** while preserving its probability at that instant. Multiplying every amplitude by the same phase is a global phase with no observable effect.

Relative phases can change probabilities after an operation combines amplitudes. For a small algebra illustration, $|+\rangle$ and $(|0\rangle-|1\rangle)/\sqrt2$ give the same 50/50 outcomes when measured immediately, but a Hadamard transform maps them to $|0\rangle$ and $|1\rangle$, respectively. The Hadamard matrix is $2^{-1/2}\begin{pmatrix}1&1\\1&-1\end{pmatrix}$; ordinary matrix multiplication verifies both claims. The sum or cancellation of amplitudes is **interference**.

### Operators and the Pauli matrices

A quantum operator is a linear transformation on statevectors. The Pauli matrices used here are

$$
X=\begin{pmatrix}0&1\\1&0\end{pmatrix},\quad
Y=\begin{pmatrix}0&-\mathrm i\\\mathrm i&0\end{pmatrix},\quad
Z=\begin{pmatrix}1&0\\0&-1\end{pmatrix}.
$$

$X$ swaps the two basis states. $Z$ changes the sign of $|1\rangle$. $Y$ swaps the states with phases. A subscript, such as $X_i$, means this operator acts on qubit $i$ and as identity on the others. The product $Z_iZ_j$ has eigenvalue $z_iz_j$ on $|x\rangle$.

A physically valid ideal gate is **unitary**: it preserves total squared amplitude, hence total probability. A Hermitian operator equals its conjugate transpose; its eigenvalues are real. Hamiltonians are Hermitian, and $e^{-\mathrm i\theta\widehat H}$ is unitary for real $\theta$. For the diagonal cost Hamiltonian, the exponential simply multiplies each basis amplitude by $e^{-\mathrm i\theta E(x)}$. No general matrix-exponential calculation is needed to understand this action.

### Expected energy is an average over outcomes

The bra $\langle\psi|$ is the conjugate transpose of $|\psi\rangle$. Because $\widehat H_C$ is diagonal,

$$
\langle\psi|\widehat H_C|\psi\rangle=\sum_x|\alpha_x|^2E(x).
$$

This is the probability-weighted mean energy. It is not necessarily the energy of the best sample or the probability of measuring an optimum. If the distribution includes many mediocre states and one rare excellent state, those statistics tell different stories.

<aside class="takeaway">The cost operator writes energy into phases. A mixer combines amplitudes so those phases can influence measurement probabilities. Neither step alone is a “choose the minimum” operation.</aside>

## 11 · QAOA as a complete algorithm {#qaoa}

The **quantum approximate optimisation algorithm** alternates a problem-dependent phase operation and a mixing operation, and uses a classical optimiser to choose their angles. Its original formulation is due to [Farhi, Goldstone and Gutmann](https://arxiv.org/abs/1411.4028). Here we use a minimisation convention throughout.

### General circuit · Initial state, cost, mixer

Standard unconstrained QAOA starts with $|\psi_0\rangle=|+\rangle^{\otimes N}$. Define

$$
U_C(\gamma_\ell)=e^{-\mathrm i\gamma_\ell\widehat H_C},\qquad
\widehat H_M=\sum_{i=1}^N X_i,\qquad
U_M(\beta_\ell)=e^{-\mathrm i\beta_\ell\widehat H_M}.
$$

The layer recursion avoids ambiguity about operator order:

$$
|\psi_\ell\rangle=U_M(\beta_\ell)U_C(\gamma_\ell)|\psi_{\ell-1}\rangle,
\qquad\ell=1,\ldots,L.
$$

Operators on the right act first: **cost, then mixer** in each layer. The two angles per layer give $2L$ trainable real parameters. They are algorithmic parameters; processing times and QUBO coefficients remain fixed.

### What the cost step actually does

If $|\psi\rangle=\sum_x\alpha_x|x\rangle$, then

$$
U_C(\gamma)|\psi\rangle=\sum_x\alpha_xe^{-\mathrm i\gamma E(x)}|x\rangle.
$$

The probabilities $|\alpha_x|^2$ are unchanged by this step. Low-energy states do not automatically receive larger probabilities. The energy-dependent relative phases become useful only when subsequent operations mix amplitudes.

### What the X mixer actually does

The $X_i$ operators commute because they act on different qubits: applying them in either order gives the same result, $X_iX_j=X_jX_i$. Thus the mixer factors into one-qubit operations, and since $X^2=I$,

$$
U_M(\beta)=\prod_i e^{-\mathrm i\beta X_i},\qquad
e^{-\mathrm i\beta X}=\cos\beta\,I-\mathrm i\sin\beta\,X.
$$

For a single application of this factor, each output amplitude combines the old amplitude at that bitstring with the amplitude at the bitstring whose chosen bit is flipped. That is the local source of interference. Repeated layers can create structured, correlated distributions. The direction of the improvement depends on the angles and on the whole energy landscape; it is not guaranteed by the mixer alone.

### Example · A one-bit mechanism demonstration, not a scheduling benchmark

Let $E(x)=x$, whose minimum is at $x=0$. Starting from $|+\rangle$, one cost step gives $(|0\rangle+e^{-\mathrm i\gamma}|1\rangle)/\sqrt2$. After one X mixer, the zero-state amplitude is $(\cos\beta-\mathrm i\sin\beta e^{-\mathrm i\gamma})/\sqrt2$. Consequently

$$
\Pr(x=0)=\frac{1-\sin(2\beta)\sin\gamma}{2}.
$$

For $\gamma=\pi/2$, $\beta=-\pi/4$, the probability is 1. Reversing the sign of that $\beta$ gives probability 0. This intentionally simple calculation isolates phase-to-probability conversion. It does not establish that angles for interacting scheduling models are easy to find.

<div id="phase-lab" class="lab" aria-label="Interactive phase and mixer demonstration"><p>The phase-and-mixer laboratory requires JavaScript. The exact probability formula and its derivation are given above.</p></div>

### Turn the circuit family into a search procedure

1. Build and audit the encoding, energy, and Ising coefficients.
2. Choose $L$, an initial parameter vector, an optimiser, and a total budget.
3. For each parameter proposal, prepare the circuit and estimate its objective. A statevector simulator can compute the ideal expectation exactly; hardware usually estimates it from samples.
4. Give that scalar estimate to the classical optimiser, which proposes new angles. Use multiple starts if the landscape warrants them, and count that work in the budget.
5. At the selected angles, collect a final batch of bitstrings. Decode each one and validate it against the original scheduling model.
6. Report raw sample statistics, best validated objective, training cost, final sampling cost, and whether noise or hardware was involved.

The circuit evaluates a distribution; the optimiser searches parameters. Neither part automatically certifies a global minimum. For the ideal circuit family, adding a layer cannot worsen the globally best attainable expectation, because its angles may be zero. A finite optimiser or noisy device can nevertheless perform worse at larger depth.

### Gate-level connection to the Ising coefficients

All terms in $\widehat H_C$ commute. With gate conventions $R_Z(\theta)=e^{-\mathrm i\theta Z/2}$ and $R_{ZZ}(\theta)=e^{-\mathrm i\theta Z_iZ_j/2}$, a cost layer uses

$$
R_Z(2\gamma_\ell h_i)\quad\text{and}\quad
R_{ZZ}(2\gamma_\ell J_{ij}).
$$

The term $c_I I$ gives only a global phase and can be omitted from the circuit. Retain the offset for reported energies. An X mixer uses $R_X(2\beta_\ell)$ on each qubit under the analogous rotation convention. Nonzero couplings determine logical two-qubit rotations, but device connectivity, parallel scheduling and gate decomposition determine physical circuit depth.

Scaling every energy coefficient by the same positive factor preserves minimisers and can be absorbed into cost angles. Changing only penalty weights changes the landscape and generally changes the optimisation problem away from its feasible subset.

### Encoding-preserving mixers

The plain X mixer can flip a one-hot 1 to 0 or create an extra 1, leaving the valid encoding subspace. A different mixer can preserve one selected alternative per operation. For two bits $a,b$ within one group, define

$$
\widehat H_{ab}^{XY}=\frac12(X_aX_b+Y_aY_b).
$$

It maps $|10\rangle$ to $|01\rangle$ and vice versa, and annihilates $|00\rangle$ and $|11\rangle$. Thus its evolution preserves the number of ones. Coupling choices along a connected graph within each group allows movement among that group's one-hot alternatives. A suitable initial state, such as one known one-hot codeword or a uniform one-excitation state per group, is required: a preserving mixer does not remove invalid weight already present.

Preserving one-hot validity does **not** preserve machine or precedence feasibility. Those constraints still need penalties or a stronger custom mixer. If the circuit is rigorously confined to one-hot words, the exactly-once penalty is identically zero on the reachable subspace and may be omitted there. The pairwise feasibility conflicts remain.

For **exactly two alternatives per operation**, mapping $|10\rangle\mapsto|0\rangle$ and $|01\rangle\mapsto|1\rangle$ makes this XY mixer act like a single-qubit X mixer. That explains a special equivalence between one-hot XY and one-bit domain-wall QAOA, provided initial states, energies, angles and normalisations match. It is not an equivalence of the encodings for arbitrary $K$. See [Hadfield et al.](https://arxiv.org/abs/1709.03489) for the broader alternating-operator framework.

### Independent angles, CVaR and warm starts change different parts

**Independent mixer angles** replace one shared $\beta_\ell$ by $N$ values $\beta_{\ell,i}$. With one shared cost angle per layer, this has $L(N+1)$ parameters, not $2L$. More flexibility can increase training work; it does not reduce the number of bits.

**CVaR** changes the objective used to tune a circuit. For minimisation, choose $\alpha\in(0,1]$ and average the lowest-energy $\alpha$ fraction of the output distribution. For $R$ equally weighted samples sorted as $e_{(1)}\le\cdots\le e_{(R)}$ and $k=\alpha R$ an integer, the estimate is $k^{-1}\sum_{r=1}^k e_{(r)}$. A non-integer cutoff uses a fractional weight on the boundary sample. $\alpha=1$ is the ordinary sample mean. Smaller $\alpha$ focuses on the good tail and uses fewer effective samples. It can prefer a distribution with a better good tail and a worse overall mean. This is the aggregation proposed by [Barkoutsos et al.](https://quantum-journal.org/papers/q-2020-04-20-256/); it is not a universal improvement guarantee.

**Warm starts** change the initial state, parameters, or search seed using classical information. Specify which information is used and count the work that produced it. A warm-start state and a preserving mixer must be compatible. A solution supplied as initial data cannot simultaneously be claimed as discovered from scratch by the quantum part.

## 12 · Compare solvers and build a correct hybrid {#solvers}

### The same QUBO does not imply the same search mechanism

| Method | Input and mechanism | What a run can establish |
|---|---|---|
| Exhaustive enumeration | Evaluate all $2^N$ bitstrings. | An exact minimum, if the full space was checked. Exponential work. |
| CP-SAT or MILP | Use the original constraints or a linearised model; combine propagation, relaxations and search. | A feasible solution and bounds; optimality only when certified by status and matching bounds. |
| Simulated annealing | Stochastic classical bit flips, accepting some uphill moves according to temperature. | Candidate bitstrings; a finite run is generally not a certificate. |
| Quantum annealing | Physical evolution from a mixing Hamiltonian towards a cost Hamiltonian. | Measured candidates; finite-time, noisy runs need validation. |
| QAOA | Train an alternating parameterised circuit, then sample it. | A trained distribution and samples; no general finite-run certificate. |
| VQE / filtering variants | Train a chosen circuit family against an energy or filtering-related objective. | Performance depends on the ansatz, initialisation, measurements and optimisation. |
| VeloxQ | A classical physics-inspired QUBO solver operating on conventional computing infrastructure. | Solver samples and measured runtime/quality on the tested instances. |

An **ansatz** is a chosen parameterised family of states or circuits. QAOA uses a particular ansatz; VQE is a broader variational energy-minimisation framework. Filtering methods aim to suppress high-energy contributions through a filter-related procedure; calling something filtering VQE does not specify its implementation, measurement cost, or guarantees.

### What CP-SAT and MILP do with a schedule

In **constraint programming**, a variable has a domain of possible values. Propagation removes values that cannot coexist with current constraints: for example, a fixed predecessor's finish raises its successor's earliest start. Global constraints such as “these machine intervals do not overlap” can propagate more information than separately examining a single pair. Search branches on unresolved choices, propagates again, and uses bounds to discard branches that cannot improve the incumbent, meaning the best feasible solution found so far. CP-SAT combines integer modelling, constraint reasoning, Boolean search and additional optimisation machinery; its time-limited feasible result and its proved optimal result are different statuses.

In **mixed-integer linear programming**, the objective and constraints are linear, while some variables must be integral. Chapter 03's product linearisation is one way to build such a model. Replacing integrality by continuous ranges gives a **relaxation** whose minimum is a lower bound for minimisation, because it permits at least all original feasible points. Branch-and-bound divides unresolved integer choices into subproblems, obtains lower bounds and feasible upper bounds, and discards subproblems whose lower bounds cannot beat the incumbent. Exact solvers can certify a closed gap, but time or memory limits may stop them before that happens. Their performance depends on the formulation; “classical exact solver” is not the same as “instant solution.”

### VQE and filtering: which part changes?

In **VQE**, choose a circuit family $|\psi(\theta)\rangle$ with parameter vector $\theta$, then minimise $\langle\psi(\theta)|\widehat H_C|\psi(\theta)\rangle$ with a classical optimiser. A normalised state's expected energy is a weighted average of eigenvalues, so it cannot lie below the true ground energy. That lower limit is the variational principle. The chosen circuit family may be unable to represent the ground state, and a finite optimiser may fail to find even the best state in the family. The word VQE by itself supplies neither a circuit design nor a success guarantee. For a diagonal scheduling cost, computational-basis samples suffice to estimate its energy.

To understand **filtering**, imagine weighting each basis amplitude by $f(E(x))$, where $f$ is larger at lower energy, then renormalising. Formally,

$$
|\psi_{\mathrm{filtered}}\rangle=
\frac{f(\widehat H_C)|\psi\rangle}
{\sqrt{\sum_x|\alpha_x|^2|f(E(x))|^2}}.
$$

For example, the positive filter $f(E)=e^{-\kappa E}$ with $\kappa>0$ relatively suppresses higher energies. Its output probabilities are proportional to $|\alpha_x|^2e^{-2\kappa E(x)}$. Unlike a phase factor, this changes magnitudes. But the transformation is generally nonunitary, so it is **not** an ordinary deterministic cost gate; directly writing the formula does not implement it for free. Filtering variational algorithms use specific measurable objectives and variational updates or probabilistic constructions to approximate such concentration. State the chosen filter, approximation, measurement overhead and procedure. If an energy component has exactly zero initial amplitude, multiplying by a diagonal filter cannot create it. This explains both the motivation and a basic limitation without implying that all filtering variants use one identical protocol.

The [VeloxQ paper](https://arxiv.org/abs/2501.19221) describes and benchmarks a classical solver. “Quantum-inspired” does not mean a circuit ran on a quantum processor. No remote solver run is needed to understand or use this learning guide.

### An exact special case: Johnson's rule

For the ordinary **two-machine flow shop** under the baseline assumptions, [Johnson's rule](https://doi.org/10.1002/nav.3800010110) constructs an optimal common job order. Put jobs with first-machine duration at most their second-machine duration in an early group, sorted by increasing first-machine duration. Put the remaining jobs in a late group, sorted by decreasing second-machine duration. Concatenate the groups and schedule each operation as early as its job predecessor and its machine allow. Ties may be broken consistently in either order within tied entries.

The intuition is to bring short first-machine tasks forward so they release work downstream quickly, and put short second-machine tasks late so they do not create a long ending tail. The optimality theorem is specific to this two-machine setting. The same sorting recipe is not a general job-shop algorithm, nor a general optimal three-machine rule. Example A satisfies its conditions and yields Z2→Z1. Chapter 13 independently proves that example's optimum by matching a lower bound, without relying on the theorem.

### Simulated annealing, one step at a time

At a current bitstring $x$, propose a nearby bitstring $x'$—often one bit flip. Compute $\Delta E=E(x')-E(x)$. Accept an improving move; otherwise accept it with probability $e^{-\Delta E/T}$ at temperature $T>0$. Equivalently, acceptance is $\min\{1,e^{-\Delta E/T}\}$. Temperature is a search parameter measured on the energy scale, not necessarily a physical temperature.

At high $T$, uphill moves are common; at low $T$, they are rarer. A cooling schedule decreases $T$ over time. For our polynomial, flipping bit $i$ changes energy by

$$
\Delta E=(1-2x_i)\left(a_i+\sum_{j<i}w_{ji}x_j+\sum_{j>i}w_{ij}x_j\right).
$$

Only the bit's incident coefficients are needed. This explains why sparsity matters computationally. Finite cooling can get trapped in local minima; a favourable energy landscape is not guaranteed by correctness of the encoding.

### Quantum annealing and embedding

A typical idealised anneal uses $\widehat H(s)=-A(s)\sum_iX_i+B(s)\widehat H_C$ for $s\in[0,1]$, moving from a strong mixing term to a strong cost term. The minus sign makes the all-plus state a ground state of the initial mixing Hamiltonian. Staying near an instantaneous ground state requires conditions involving the spectral gap and evolution rate. Practical time, noise and control limits mean “slowly reduce the transverse field” is not an unconditional guarantee of the optimum.

If a hardware connectivity graph lacks a required logical coupling, **minor embedding** may represent one logical bit by a chain of physical qubits tied together. Chain strength, broken chains and decoding matter. Therefore one logical QUBO bit is not necessarily one physical annealer qubit. Gate-model routing can also require extra operations. State the level at which a qubit count is measured.

### General hybrid · Large-neighbourhood search

A hybrid scheduler can use a QUBO solver to improve part of a feasible schedule. Let some decisions remain fixed while a selected **neighbourhood** is reoptimised. This can make each subproblem small enough for the chosen backend. It also restricts the moves available, so global improvements may be missed.

```text
start from a schedule validated against the complete scheduling model
repeat until the total budget is exhausted:
    choose which operations or decisions may change
    preserve commitments such as already executed operations
    build the subproblem, including interactions with everything fixed
    obtain candidate bitstrings from the chosen QUBO solver
    decode each candidate into a complete schedule
    validate against all original constraints
    accept a feasible improvement according to the chosen objective
    log construction time, solve time, validation time and objective
```

### Derivation · Fixing variables is not deleting their interactions

Let $\mathcal I_{\mathrm{free}}$ be the set of free bit indices and $\mathcal I_{\mathrm{fixed}}$ the fixed indices, with $x_j=\bar x_j$ for each fixed index. A pair between a free and fixed bit becomes a linear term in the free bit. Its new coefficient is

$$
a_i'=a_i+\sum_{j\in\mathcal I_{\mathrm{fixed}}}w_{\min\{i,j\},\max\{i,j\}}\bar x_j,
\quad i\in\mathcal I_{\mathrm{free}}.
$$

Pairs entirely inside the fixed set and fixed linear terms become part of the new offset. Pairs entirely inside the free set stay quadratic. Simply deleting fixed rows and columns loses boundary effects and can permit collisions with frozen operations. Alternatively, construct start windows and conflicts directly against the fixed schedule, with an equivalent completeness argument.

### Restriction gap versus solver gap

Let $f^*$ be the certified optimum of the full problem and $f_R^*$ the certified optimum under the chosen fixed decisions. When the restricted feasible set is a subset of the full feasible set and objectives agree, $f_R^*-f^*\ge0$ is the **restriction gap**. It measures the cost of freezing decisions.

If a heuristic returns objective $f_{\mathrm{found}}$ in that neighbourhood, then $f_{\mathrm{found}}-f_R^*$ is a separate **solver gap**. Comparing two heuristic outputs does not isolate these gaps. An apparent negative restriction gap signals unequal models, incomparable bounds, or uncertified reference values.

[Zhang, Lo Bianco and Beck](https://ojs.aaai.org/index.php/ICAPS/article/view/19826) provide a concrete QUBO–constraint-programming hybrid LNS study. Its empirical results motivate testing this architecture; they do not establish that hybrid QUBO solvers are universally best on all scheduling problems.

## 13 · A complete reference example, checked against the source {#worked}

This chapter applies the general construction to **Example A**, the supplied instance from chapter 01, at $H=4$. It is a consistency check and a worked translation, not a claim about realistic-scale performance.

### Windows and index map

Both jobs have total duration 3, so each operation has $K_o=4-3+1=2$ starts. We use the following one-based ordering in both the mathematics and the interactive explorer.

| Bit | Operation | $p_o$ | $h_o$ | $\tau_o$ | Allowed start represented |
|---|---|---:|---:|---:|---:|
| $x_1$ | Z1·T | 2 | 0 | 1 | 0 |
| $x_2$ | Z1·T | 2 | 0 | 1 | 1 |
| $x_3$ | Z1·F | 1 | 2 | 0 | 2 |
| $x_4$ | Z1·F | 1 | 2 | 0 | 3 |
| $x_5$ | Z2·T | 1 | 0 | 2 | 0 |
| $x_6$ | Z2·T | 1 | 0 | 2 | 1 |
| $x_7$ | Z2·F | 2 | 1 | 0 | 1 |
| $x_8$ | Z2·F | 2 | 1 | 0 | 2 |

Use unit penalty weights. Exactly-once groups are $(x_1,x_2)$, $(x_3,x_4)$, $(x_5,x_6)$, $(x_7,x_8)$. The strict interval-overlap test gives machine-conflict pairs $(1,5),(1,6),(2,6),(3,7),(3,8),(4,8)$. Precedence gives pairs $(2,3),(6,7)$.

For example, $x_1x_6$ is forbidden because Z1·T at 0 occupies $[0,2)$ and Z2·T at 1 occupies $[1,2)$. In contrast, $x_2x_5$ is allowed: $[1,3)$ and $[0,1)$ only touch. Pair $x_2x_3$ violates precedence because Z1·T would finish at 3 while Z1·F would start at 2.

### The energy before and after expansion

$$
\begin{aligned}
E_4(x)={}&(x_1+x_2-1)^2+(x_3+x_4-1)^2\\
&+(x_5+x_6-1)^2+(x_7+x_8-1)^2\\
&+x_1x_5+x_1x_6+x_2x_6+x_3x_7+x_3x_8+x_4x_8\\
&+x_2x_3+x_6x_7.
\end{aligned}
$$

Its linear coefficients are all $-1$, its constant is 4, its same-operation pair coefficients are 2, and its eight conflict pair coefficients are 1. The complete upper-triangular matrix is

$$
Q=\begin{pmatrix}
-1&2&0&0&1&1&0&0\\
0&-1&1&0&0&1&0&0\\
0&0&-1&2&0&0&1&1\\
0&0&0&-1&0&0&0&1\\
0&0&0&0&-1&2&0&0\\
0&0&0&0&0&-1&1&0\\
0&0&0&0&0&0&-1&2\\
0&0&0&0&0&0&0&-1
\end{pmatrix},\qquad c_0=4.
$$

The feasible bitstring $x=(0,1,0,1,1,0,1,0)$ selects $x_2,x_4,x_5,x_7$. Its four linear terms sum to $-4$ and every selected pair coefficient is zero, so $E_4=-4+4=0$.

The encoding-valid bitstring $(1,0,1,0,1,0,1,0)$ has two machine conflicts, $x_1x_5$ and $x_3x_7$, and energy 2. In contrast, the all-ones bitstring has four exactly-once penalties of 1 and eight conflicts, for energy 12. Squared exactly-once violations for larger groups need not equal a simple count.

<div id="schedule-lab" class="lab" aria-label="Interactive scheduling and QUBO explorer"><p>The scheduling laboratory requires JavaScript. The complete matrix, penalties and checked schedules are given in this chapter.</p></div>

### Domain-wall conversion of this particular instance

Every operation has two choices, so four domain-wall bits suffice, one per operation in the same group order. Substitute

$$
(x_1,x_2)=(1-y_1,y_1),\quad(x_3,x_4)=(1-y_2,y_2),
$$

$$
(x_5,x_6)=(1-y_3,y_3),\quad(x_7,x_8)=(1-y_4,y_4).
$$

All sixteen $y$ words are encoding-valid because each group has only one threshold bit. Substitute into the eight conflict terms, remove the exactly-once penalties, and collect:

$$
E_4^{\mathrm{DW}}(y)=2-y_2+y_3-y_1y_2+y_1y_3+y_2y_4-y_3y_4.
$$

The feasible choice $y=(1,1,0,0)$ gives $2-1+0-1+0+0-0=0$. Encoding validity is automatic here, but scheduling feasibility is not: only one of these sixteen bitstrings has zero energy. This special $K=2$ case is why an example at only this horizon cannot teach general domain-wall validity constraints.

### Prove the optimum, rather than trusting the solver

For Example A, machine T has 3 units of work. Its last-finishing job still requires at least 1 unit on F, so every feasible schedule has $C_{\max}\ge4$. The displayed schedule finishes at 4; therefore 4 is optimal. An exhaustive QUBO check at $H=3$ independently finds minimum energy 2, and at $H=4$ finds one zero-energy bitstring.

For **Example B**, the supplied three-job, three-machine instance, the duration rows are Z1 $(2,1,2)$, Z2 $(1,2,1)$, and Z3 $(2,2,1)$ on T→F→S. Machine T has workload 5. Its last job still needs at least $\min_j(p_{j,F}+p_{j,S})=3$ afterwards, so the makespan is at least 8. Processing jobs in order Z2→Z1→Z3 on each machine yields intervals:

| Job | T | F | S |
|---|---|---|---|
| Z2 | [0,1) | [1,3) | [3,4) |
| Z1 | [1,3) | [3,4) | [4,6) |
| Z3 | [3,5) | [5,7) | [7,8) |

This schedule meets the bound, proving optimum 8. The total job durations are $(5,4,5)$, so at $H=8$ the one-hot count is $3(4+5+4)=39$, the domain-wall count is $3(3+4+3)=30$, and binary positional decision bits total $3(2+3+2)=21$ **before any auxiliary bits**. These are formulation counts, not measured speedups or physical-device resource counts.

### What has actually been checked for this guide

The accompanying `audit.py` recomputes the source-instance counts, evaluates the worked matrices, checks the Ising conversion on all bitstrings of the algebra example, compares independent scheduling constraints with QUBO energies on small instances, checks domain-wall mappings beyond two choices, and verifies the one-qubit QAOA identity numerically. Its report is included in the guide's folder. The general proofs above explain why the method works beyond those finite checks.

The source tutorial also included historical solver percentages. They are deliberately not used as explanatory evidence here: understanding a mechanism does not require reproducing one run's percentages. For repository experiment details, consult the original run files and refinement report; those are a separate, dated evidence layer.

## 14 · Exercises with worked solutions {#exercises}

Try each question before opening its solution. The questions move from local algebra to model diagnosis and general reasoning. Each numerical case here is invented unless it explicitly refers to Example A.

### 1 · Expand a weighted exactly-once rule

Three bits must select one alternative. Expand $3(x_1+x_2+x_3-1)^2$ and state every upper-triangular matrix entry and the offset.

<details class="solution"><summary>Worked solution</summary>

The expansion is $3-3x_1-3x_2-3x_3+6x_1x_2+6x_1x_3+6x_2x_3$. Thus all three diagonal entries are −3, every upper off-diagonal entry is 6, every lower entry is 0, and $c_0=3$. At three selected bits the penalty is $3(3-1)^2=12$.

</details>

### 2 · Distinguish squaring a bit from reducing an interaction

Simplify $2x_1^2x_2-3x_1x_2+4x_2^3$. Is the result linear or quadratic? Can $x_1x_2$ be replaced by either one of its factors?

<details class="solution"><summary>Worked solution</summary>

Binary powers reduce, giving $-x_1x_2+4x_2$, which is quadratic. Distinct bits cannot be collapsed: at $(x_1,x_2)=(0,1)$ their product is 0 but $x_2=1$, while at $(1,0)$ their product is 0 but $x_1=1$. Removing a genuine pair interaction needs an equivalent reformulation with extra conditions, not the identity $x_i^2=x_i$.

</details>

### 3 · Derive windows for an arbitrary chain

A job has durations $(2,3,1)$ and horizon 9. Find the allowed starts for each operation. How many one-hot and domain-wall bits does this job use before fixing variables?

<details class="solution"><summary>Worked solution</summary>

The job duration is 6. The windows are {0,1,2,3}, {2,3,4,5}, {5,6,7,8}. Each has $9-6+1=4$ starts. There are $3\cdot4=12$ one-hot bits or $3\cdot3=9$ domain-wall bits. Starts in these windows may still conflict with other jobs; pruning has not solved scheduling.

</details>

### 4 · Audit an overlap boundary

Two operations on one machine have durations 3 and 2. The first starts at 1. Which integer starts $u\ge0$ for the second overlap it?

<details class="solution"><summary>Worked solution</summary>

The intervals are [1,4) and [u,u+2). Overlap requires $1<u+2$ and $u<4$, so the nonnegative integer possibilities are $u=0,1,2,3$. Start 4 is allowed because it touches the first operation's finish. Start 0 still overlaps during [1,2).

</details>

### 5 · Collect two contributions to one pair

An invented formulation contains $2x_1x_2$ from one rule and $5x_1x_2$ from another. What goes into an upper-triangular matrix? What goes into a symmetric one?

<details class="solution"><summary>Worked solution</summary>

The total pair coefficient is 7. Put 7 in $Q_{12}$ and 0 in $Q_{21}$ for upper-triangular storage, or 3.5 in both cells for symmetric storage. Writing 2 and then overwriting it with 5 loses a constraint contribution.

</details>

### 6 · Detect a nonquadratic encoding

Two operations each have eight candidate starts. Binary positional encoding needs three bits per operation. What degree can a rank-specific conflict have? Why is “six bits in total” not necessarily the size of a QUBO for the two operations?

<details class="solution"><summary>Worked solution</summary>

Each indicator is a product of three literals, where a literal is a bit or its complement. A product of two such indicators can have degree six. It is a binary polynomial but not yet a QUBO. An exact degree reduction may introduce auxiliary bits and penalty terms. Some particular expressions simplify; no such simplification follows just from the encoding count.

</details>

### 7 · Diagnose a domain-wall word

For $K=5$, decode the threshold word 1100. Then compute all five indicators for 1010 and explain why a telescoping sum of one does not validate it.

<details class="solution"><summary>Worked solution</summary>

Word 1100 represents rank 2, meaning the third allowed start $t_2$. With fixed boundaries, 1010 gives indicators $(0,1,-1,1,0)$. They sum to 1, but the negative entry invalidates the meaning “selected or not selected.” There is one upward transition 0→1, so $P_{\mathrm{wall}}=1$.

</details>

### 8 · Choose a sufficient objective penalty

Suppose a complete feasibility penalty is zero on feasible states and at least 2 on every infeasible state. The objective lies between −7 and 11 on all bitstrings. Give a sufficient $\rho$ and explain what happens at equality in the conservative bound.

<details class="solution"><summary>Worked solution</summary>

Use $2\rho>11-(-7)=18$, hence $\rho>9$. For example, 10 is sufficient if a feasible state exists. At $\rho=9$, the bound allows an infeasible state to tie a feasible state: $2\cdot9-7=11$. Equality therefore cannot guarantee that every minimiser is feasible.

</details>

### 9 · Convert a QUBO to Ising

Convert $E=2-x_1+3x_2-2x_1x_2$ using our convention and check one bitstring.

<details class="solution"><summary>Worked solution</summary>

$J_{12}=-1/2$, $h_1=1/2+1/2=1$, $h_2=-3/2+1/2=-1$, and $c_I=2+(-1+3)/2-2/4=5/2$. Thus $E=5/2+z_1-z_2-z_1z_2/2$. At $x=(1,0)$, the original energy is 1. Spins $(-1,+1)$ give $5/2-1-1+1/2=1$.

</details>

### 10 · Explain why the phase layer is insufficient

A circuit starts uniform over eight bitstrings. One cost layer assigns a different phase to each. What is the immediate measurement probability of each bitstring? What additional mechanism is needed to change those probabilities?

<details class="solution"><summary>Worked solution</summary>

Every probability remains 1/8 because every phase factor has magnitude one. A subsequent non-diagonal operation, such as the mixer, must combine amplitudes so their relative phases can cause constructive or destructive interference.

</details>

### 11 · Separate a sample from a proof

A heuristic finds a feasible schedule at $H=12$ but finds no zero-energy sample at $H=11$. The valid lower bound is 9. What can you report?

<details class="solution"><summary>Worked solution</summary>

The optimum lies between 9 and 12, inclusive. The horizon 11 is unresolved, not proved impossible. Report the validated 12 schedule, the lower bound 9 and the search budget/failure at 11. You cannot report an optimum of 12 from this evidence.

</details>

### 12 · Construct a residual energy correctly

For $E=c_0+a_1x_1+a_2x_2+a_3x_3+w_{12}x_1x_2+w_{13}x_1x_3+w_{23}x_2x_3$, fix $x_3=1$ and retain $x_1,x_2$.

<details class="solution"><summary>Worked solution</summary>

The residual energy is $(c_0+a_3)+(a_1+w_{13})x_1+(a_2+w_{23})x_2+w_{12}x_1x_2$. The fixed variable changes the offset and the free variables' linear coefficients. Deleting it without these adjustments would change the subproblem.

</details>

### 13 · Test a proposed full model

You are handed a new scheduling QUBO and told “the solver returned low energy.” Describe the evidence you would require before calling that a solution to the original problem.

<details class="solution"><summary>Worked solution</summary>

Require the original assumptions and objective; every variable's meaning; the full offset and coefficient convention; a soundness/completeness argument; safe pruning; sufficient penalty bounds if objectives or domain-wall validity are involved; and an independent decoder/validator. Validate operation coverage, durations, precedence, resource capacity and every extension. Report the actual schedule and objective. To call it optimal, also require a matching lower bound or certificate. A low number without this chain of meaning is not enough.

</details>

### 14 · Quadratize a signed cubic term

Give an exact QUBO reduction of $-4x_1x_2x_3$ using one auxiliary $q$. Choose a sufficient weight. Explain why replacing it only by $-4qx_3$ is incorrect.

<details class="solution"><summary>Worked solution</summary>

Choose $q=x_1x_2$ and use $-4qx_3+5(x_1x_2-2x_1q-2x_2q+3q)$. The consistency weight 5 exceeds the maximum improvement 4 obtainable by changing $q$ in the substituted cubic. Therefore minimising over $q$ recovers the original energy for every fixed $(x_1,x_2,x_3)$. Without the linking penalty, at $(x_1,x_2,x_3)=(0,0,1)$ the original cost is 0, but a solver could choose $q=1$ and obtain −4. The auxiliary must be a checked relation, not a free shortcut.

</details>

### 15 · Size a slack encoding

An integer linear expression satisfies $-2\le g(x)\le7$ on all bitstrings. The required constraint is $g(x)\le4$. What slack range is sufficient, how many ordinary binary slack digits cover it, and why does allowing the unused largest code not create a false feasible overload?

<details class="solution"><summary>Worked solution</summary>

Use $s=4-g(x)$, which ranges from 0 to 6 on feasible states, so three bits covering 0 through 7 suffice. The value 7 is unnecessary but harmless to zero-energy correctness: $g+s=4$ would then require $g=-3$, excluded by the bound. Any overload $g>4$ would require negative slack, impossible for the encoded nonnegative $s$. A two-bit encoding covers only 0 through 3 and could remove feasible assignments needing larger slack.

</details>

### 16 · Find the missing resource constraint

Three unit-demand operations overlap during one time slot on a resource of capacity two. A proposed model forbids only pairs whose combined demand exceeds capacity. Does it detect the violation? How would you formulate the capacity correctly?

<details class="solution"><summary>Worked solution</summary>

No pair exceeds capacity: every pair has demand two, so no forbidden-pair term is added. Yet the three-operation load is three. Build the linear active load for each slot and enforce $L_{k,\theta}\le2$, using an appropriate slack equality or another exact capacity formulation. Degree reduction and penalties then depend on that chosen formulation. Capacity-one conflict graphs cannot simply be reused for arbitrary resource capacities.

</details>

## 15 · Reference sheet and modelling checklist {#reference}

### The transformations in one place

| Task | Transformation | Condition to check |
|---|---|---|
| Remove powers of one bit | $x_i^r=x_i$ for integer $r\ge1$ | The same variable is binary. Distinct variables do not merge. |
| Exactly one | $(\sum_i x_i-1)^2$ | Expand with every pair once and coefficient 2. |
| Forbid a pair | $x_ix_j$ | A separate rule ensures required choices are made. |
| Polynomial to matrix | $Q_{ii}=a_i$, $Q_{ij}=w_{ij}$ for $i<j$ | Lower triangle zero; offset external. |
| QUBO to spin | $x_i=(1-z_i)/2$ | Include pair contributions to fields and offset. |
| Domain wall | $\chi_r=y_r-y_{r+1}$ | Enforce monotonicity; bound negative conflict energy. |
| Hard linear inequality | Add adequate nonnegative slack and square the equality | All required slack values representable. |
| Objective with constraints | $\rho P+F$ | Bound objective gain over all invalid bitstrings. |
| Fixed variables | Substitute values and recollect terms | Preserve boundary interactions and the offset. |
| Higher-order polynomial | Introduce products as auxiliaries with consistency penalties | Count new bits and prove penalty sufficiency. |

### Questions to ask in every new formulation

1. **Meaning:** What does each variable mean, including auxiliaries? Are data, choices, and algorithm parameters separate?
2. **Scope:** Which assumptions make the equations valid? Does the time grid represent the original problem exactly?
3. **Representation:** Can every feasible solution be encoded? Are all invalid codes excluded from optimal solutions?
4. **Degree:** After expansion and binary simplification, is every term degree at most two? If not, what exact reformulation is used?
5. **Coefficients:** Are duplicate contributions added? Is the matrix convention explicit? Is the offset retained?
6. **Weights:** Is this pure feasibility or constrained optimisation? What prevents objective rewards or negative substituted terms from defeating constraints?
7. **Search:** Does the backend certify a bound or just generate candidates? What is the unresolved optimality gap?
8. **Validation:** Does an independent checker test the original scheduling rules, rather than repeating the same energy calculation?
9. **Comparison:** Do compared methods solve the same problem, with the same restrictions, budgets, preprocessing and stopping criterion?

### Measurements that answer distinct questions

Report encoding-valid fraction, feasible fraction, best feasible objective, best known lower bound, objective gap, and end-to-end time. Include model-construction, embedding or circuit compilation, optimiser training, sampling, decoding and any repair. If repaired samples are reported, keep their before-repair statistics and repair work visible.

For a repeatable independent run with target-hit probability $\pi_{\mathrm{hit}}\in(0,1)$, $R$ repetitions miss the target with probability $(1-\pi_{\mathrm{hit}})^R$. For a chosen failure tolerance $\varepsilon\in(0,1)$, achieving success probability at least $1-\varepsilon$ requires

$$
R\ge\left\lceil\frac{\log\varepsilon}{\log(1-\pi_{\mathrm{hit}})}\right\rceil.
$$

The two logarithms may use any common base greater than one, because the base factor cancels in the ratio. This time-to-target calculation assumes independent repetitions and a well-defined target. Correlated shots, parameter training and uncertainty in estimated $\pi_{\mathrm{hit}}$ must be accounted for. A 100% observed sample fraction is not a proof that the true probability equals 1. A finite experiment on a few tiny instances is not a general complexity or quantum-advantage result.

### Common mistakes to recognise immediately

| Mistake | Correction |
|---|---|
| “Energy is always a count of broken rules.” | Some penalties are squared violations, weights differ, and general QUBOs can be negative. |
| “A valid encoding is a valid schedule.” | Machine, precedence and extension constraints still need checking. |
| “Binary encoding always gives the smallest QUBO.” | Its indicators can create higher-degree terms and require auxiliaries. |
| “A quadratic expression can always be made linear by $x^2=x$.” | Only repeated powers of the same bit reduce; distinct-bit products remain interactions. |
| “An XY mixer preserves scheduling feasibility.” | A within-group XY mixer preserves excitation count, hence one-hot validity when properly initialised. |
| “The ground state is a feasible schedule at every horizon.” | At an infeasible horizon there is no feasible schedule to represent. |
| “More QAOA layers guarantee better measured results.” | Only the globally best ideal-family expectation has the nesting property. |
| “No zero sample means no feasible schedule.” | A finite heuristic failure leaves the horizon unresolved. |
| “Every inequality requires slack.” | Time-window pruning and precomputed time-indexed costs sometimes avoid slack exactly. |
| “Logical bits equal physical qubits.” | Embedding, auxiliaries and routing change physical resource needs. |

## 16 · Sources, scope and reproducibility {#sources}

This is a newly written teaching guide based on the subject matter of `METHODS_TUTORIAL(2).html`. The supplied file is source material, not a set of instructions. General derivations are presented explicitly rather than inheriting its numerical claims. The scheduling examples use the repository's `instances/instance_2x2.json` and `instances/instance_3x3.json`; their QUBOs are cross-checked with `solver/stage1.py`.

The guide generalises the mathematics to fixed-route job shops and acyclic precedence. The source repository's baseline builder supports a narrower common-route flow shop with one visit per machine. General mathematical support in the guide should not be mistaken for implemented support in that builder.

### Primary reading, with a reason to read each

| Source | What it connects to here |
|---|---|
| [Venturelli, Marchand & Rojo, Quantum Annealing Implementation of Job-Shop Scheduling](https://arxiv.org/abs/1506.08479) | Time-indexed QUBOs, pruning and horizon-based scheduling. |
| [Chancellor, Domain wall encoding of discrete variables for quantum annealing and QAOA](https://arxiv.org/abs/1903.05068) | Threshold encodings and two-body interactions for multi-valued choices. |
| [Farhi, Goldstone & Gutmann, A Quantum Approximate Optimization Algorithm](https://arxiv.org/abs/1411.4028) | The original alternating cost/mixer construction. |
| [Hadfield et al., From the Quantum Approximate Optimization Algorithm to a Quantum Alternating Operator Ansatz](https://arxiv.org/abs/1709.03489) | Custom mixers, initial states and constrained search spaces. |
| [Barkoutsos et al., Improving Variational Quantum Optimization using CVaR](https://quantum-journal.org/papers/q-2020-04-20-256/) | Tail-focused training objectives. |
| [Amaro et al., Filtering variational quantum algorithms for combinatorial optimization](https://arxiv.org/abs/2106.10055) | Concrete variational filtering procedures beyond the idealised filter illustration. |
| [Montañez-Barrera et al., Unbalanced penalization](https://arxiv.org/abs/2211.13914) | Inequality encodings that trade slack bits for asymmetric energies. |
| [Johnson, Optimal two- and three-stage production schedules with setup times included](https://doi.org/10.1002/nav.3800010110) | The two-machine sequencing theorem and its specific applicability. |
| [Zhang, Lo Bianco & Beck, Solving Job-Shop Scheduling Problems with QUBO-Based Specialized Hardware](https://ojs.aaai.org/index.php/ICAPS/article/view/19826) | Combining QUBO subproblems with classical constraint programming. |
| [Pawłowski et al., VeloxQ: A Fast and Efficient QUBO Solver](https://arxiv.org/abs/2501.19221) | A classical QUBO backend and its reported benchmark scope. |

These references identify the method families; the finite examples and algebra in this guide are independently recomputed. The guide makes no claim that one solver family universally outperforms another. The general proofs apply under their stated assumptions. Finite audits check implementations and examples, not every possible future extension.

### Files that travel with this guide

`index.html` is the self-contained reading edition, with embedded styles, native MathML equations and interactive JavaScript. It needs no internet connection, packages, account or remote solver. Browser Find searches the visible chapter text. Browser Print uses a dedicated print layout; worked solutions are expanded when printing. The complete explanations remain readable with JavaScript disabled; the interactive laboratories require JavaScript.

`guide.md` is the editable source. `build.py` rebuilds the reading edition using Python packages `markdown` and `latex2mathml`; runtime dependencies are not needed to read the HTML. `audit.py` runs local mathematical checks with Python's standard library and the repository's baseline builder. `audit-report.json` records the executed checks. `QUALITY.md` records the revision and validation passes for this edition.
