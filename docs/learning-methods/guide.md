# Scheduling, QUBO & quantum methods

<p class="subtitle">A connected course in modelling, encodings, penalties and solvers.</p>

The central question is not “which quantum algorithm should I use?” It is **how to represent a scheduling problem so that minimising a mathematical function really solves the intended problem**. Once that connection is proved, different solvers can search the same model.

This guide builds that connection step by step. General statements are marked **General model**, **Derivation**, or **Guarantee**. Every numerical illustration is marked **Example** and states its own data. Examples explain the general statements; they do not replace them.

<div class="route" aria-label="The modelling pipeline"><span>Scheduling rules</span><b>→</b><span>Binary decisions</span><b>→</b><span>QUBO energy</span><b>→</b><span>Search or quantum circuit</span><b>→</b><span>Validated schedule</span></div>

## 00 · How to study this guide {#orientation}

Read chapters 01–06 in order. Chapter 02 first explains what each bit means and how to encode and decode a schedule. Chapter 03 builds penalties and works through their algebra. Its expandable transformation workshop is optional on the first pass; return to it after chapter 04. Chapters 07–09 explain alternative encodings, objectives, scheduling extensions and the Ising conversion. Chapters 10–12 explain the quantum algorithms and hybrid search. Chapters 13–16 provide a worked reference, exercises, a compact reference sheet, and sources.

You do not need prior scheduling, QUBO or quantum-computing knowledge. The calculations use addition, multiplication, substitution and inequalities; the derivations explain how those operations apply to the new symbols. Sums, matrix notation, complex amplitudes and quantum operators are introduced where needed. Read one step at a time. If a transition is unclear, the missing step needs explaining; you do not need to memorise a formula to move past it.

### How to tell a starting rule from a step you should understand

The quantum chapters distinguish the following kinds of statement. A starting rule is not a hidden exercise: when a physical law or a mathematical result is used without a full proof, its name and the boundary of the explanation are stated. “Given here” means the rule is supplied for you to use, not that you were expected to know it already. A postulate is a starting point of this physical formulation, not an arbitrary unsupported claim.

| Label | What the statement is doing | What you should understand here |
|---|---|---|
| **Physical postulate — given here** | A starting rule of the quantum model, supported by experiment. It is not deduced from scheduling. | Its meaning, when it applies, and how we use it. A deeper justification from another formulation of physics is outside this guide. |
| **Definition / convention** | We introduce a name, coordinate order, unit or particular gate. | What was chosen and how to use it consistently. A definition needs no physical proof. |
| **Model assumption** | We restrict the problem or device, such as fixed machine assignments or ideal noiseless gates. | Which conclusions rely on that restriction. |
| **Derivation** | We obtain a conclusion from rules already stated. | Follow the intermediate steps. A missing transition here needs explaining. |
| **Mathematical result used** | We import a named mathematical identity or theorem rather than prove the entire underlying subject. | Its relevant conditions and what it lets us do; the text identifies any omitted proof. |
| **Algorithm choice** | A designer chooses how to search: an initial state, mixer, objective or optimiser. | Why the choice is useful and what it does. It is not a law guaranteeing success. |

A useful question at any line is: **what changed, why did we change it, and what rule permits that step?** The quantum walkthrough and QAOA steps answer these separately. You do not need to derive the laws of quantum mechanics to follow their consequences, but you should not have to guess which statements are laws.

### Three different questions

| Question | Meaning | What establishes it? |
|---|---|---|
| Is this an **encoding-valid** bitstring? | Each operation has exactly one represented start. | Check the encoding. |
| Is this a **feasible** schedule? | The represented starts satisfy all scheduling rules. | Decode and validate the original rules. |
| Is this schedule **optimal**? | No feasible schedule has a smaller objective. | A matching lower bound or an exact optimality certificate. |

For example, every operation can have one start and still collide with another operation. Encoding validity is necessary for feasibility, but it is not sufficient. Likewise, feasibility does not establish optimality.

### Our notation contract

A symbol with parentheses names a **function**: a rule that takes an input and returns an output. For example, $\mu(o)$ takes the operation label $o$ and returns its required machine. The parentheses identify the input; they do not mean multiplication. Later, $E(x)$ will take a whole bit vector and return one energy number. Every new function name will be unpacked where its rule is introduced.

A subscript identifies an object; it does not imply multiplication. Thus $p_o$ means “the processing time of operation $o$.” A sum $\sum_{o\in\mathcal O}p_o$ means “add $p_o$ for each operation in the set $\mathcal O$.” The symbol $\in$ means “belongs to”; $\forall$ means “for every”; $\Leftrightarrow$ means “if and only if.” An empty sum is zero.

A product sign $\prod$ means multiply the listed factors. The logarithm $\log_2 K$ is the exponent needed to obtain $K$ from 2, and $\lceil a\rceil$ means round $a$ up to the next integer, keeping integers unchanged. For example, $\lceil\log_2 5\rceil=3$ because two bits give only 4 patterns, while three give 8. A set lists distinct objects; a graph consists of objects called vertices and links called edges. A directed edge has a specified direction. A directed acyclic graph has no directed loop. A longest-path processing-time bound adds durations along the longest directed chain of dependencies.

The first table names the scheduling objects and start decisions. Read it as a reference: the chapters introduce the model in order. Symbols for later transformations and quantum algorithms are in the optional table below.

| Symbol | Meaning |
|---|---|
| $\mathcal O$, $o$, $v$ | Set of operations; two operation labels. |
| $\mathcal M$, $\mu(o)$ | Set of machines; machine required by operation $o$. |
| $\mathcal A$ | Set of directed precedence pairs $(o,v)$: $o$ must finish before $v$ starts. |
| $p_o$, $S_o$ | Fixed processing time; chosen start time of operation $o$. |
| $H$ | A deadline we choose to test: can all operations finish by this time? It is not inherently the best result found so far. See [chapter 06](#horizon). |
| $C_{\max}(S)$ | Finishing time of the last operation in the particular schedule $S$. A schedule meeting the tested deadline has $C_{\max}(S)\le H$. Optimality is a separate question. |
| $T_o$ | Set of allowed candidate start times for operation $o$. The subscript is the letter $o$, not zero. |
| $K_o=|T_o|$ | Number of elements in $T_o$: a nonnegative integer scalar. |
| $x_{o,t}$ | A single bit: 1 if operation $o$ starts at candidate time $t$, otherwise 0. The whole operation group has $K_o$ such bits; a valid one-hot group has exactly one 1. |

<details class="derivation"><summary>Later symbols: where each is explained — these are not prerequisites for starting chapter 01</summary>

| Symbol | Meaning | First developed |
|---|---|---|
| $N$, $x_i$, $\phi(o,t)$ | Join the operation groups into one long vector with $N$ bits. The same bit $x_{o,t}$ is renamed $x_i$, where $i=\phi(o,t)$. The chosen listing order is kept consistent; it does not prescribe processing order. | [02: complete encoding and decoding walkthrough](#qubo), then [05: matrix indexing](#matrix). |
| $a_i$, $w_{ij}$, $c_0$ | Fixed linear coefficient, pair coefficient and constant offset of a QUBO. | [02: QUBO](#qubo). |
| $Q$ | **Upper-triangular** QUBO matrix. Each pair coefficient appears once. | [05: matrix construction](#matrix). |
| $\lambda_{\mathrm{once}}$ | Positive multiplier of the penalty for an operation having zero or multiple selected starts. “Once” means exactly one start per operation. | [03: penalties](#penalties), [04: complete model](#formulation). |
| $\lambda_{\mathrm{cap}}$ | Positive multiplier of the machine-capacity penalty. In this baseline, each machine can process only one operation at a time. “Cap” abbreviates capacity. | [04: machine conflicts](#formulation). |
| $\lambda_{\mathrm{prec}}$ | Positive multiplier of the precedence penalty: a successor must not start before its required predecessor finishes. “Prec” abbreviates precedence. | [04: precedence conflicts](#formulation). |
| $y_{o,r}$, $u_{o,r}$ | Bits in two alternative representations of a start choice: domain wall and binary positional. They are not additional variables required by the one-hot model. | [07: alternative encodings](#encodings). |
| $\eta$ | Domain-wall validity weight. | [07: wall penalty](#encodings). |
| $\rho$ | Multiplier controlling constraint penalties relative to an added objective. | [08: objectives and guarantees](#objectives). |
| $z_i$ | Classical spin, taking values −1 and +1. | [09: Ising conversion](#ising). |
| $Z_i$, $X_i$, $Y_i$ | Quantum Pauli operators, not classical spin values. | [09](#ising)–[10](#quantum). |
| $L$, $\gamma_\ell$, $\beta_\ell$ | QAOA layer count; cost and mixer angles in layer $\ell$. | [11: QAOA](#qaoa). |

The three $\lambda$ values are **fixed numbers chosen by the modeller**. Each multiplies an amount of violation computed from the candidate bits. They are not start times, probabilities, or variables selected by the solver. All three can equal 1 in the pure-feasibility baseline. Chapter 04 derives the penalties they multiply; chapter 08 explains why an added objective makes weight selection more delicate.

</details>

You do not need the later-symbols table to start chapter 01. The chapters below develop the names from their meanings, instead of asking you to memorise the reference table.

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

The objective is to finish the whole workload as early as possible. For one schedule, the time when **all** work is finished, measured from time zero, is called its **makespan**. To calculate it, find the finishing time of each operation and take the latest one. We write that number as $C_{\max}(S)$, where $S$ is the schedule. The letter $C$ refers to completion time; it is not a set of all candidate schedules.

$$
C_{\max}(S)=\max_{o\in\mathcal O}(S_o+p_o),\qquad
\min_{S\text{ feasible}}C_{\max}(S).
$$

Read the two operations separately: **take the maximum finishing time within each schedule; minimise that number across feasible schedules**. The subscript “max” names how the cost of one schedule is calculated. It does not tell the solver to maximise it. For example, in a deliberately invented comparison, finishing times (3,5,8) give makespan 8, while (4,6,7) give makespan 7; the latter whole workload finishes earlier.

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

### First establish what the bits mean

Before writing an energy formula, we must specify what every bit represents. A bit is one yes/no choice. In our current start-time representation,

- $x_{o,t}=1$ says: select the choice “operation $o$ starts at time $t$.”
- $x_{o,t}=0$ says: do not select that particular start time. It does not cancel the operation; another bit in its group must select its start.

Each operation has one group containing $K_o$ bits, one for each time in $T_o$. One bit selects a **start**, not one unit of processing. Its duration $p_o$ is already fixed data: selecting start $t$ occupies $[t,t+p_o)$ without needing additional ones for the occupied time units.

### A complete encoding and decoding example

This is an **invented teaching example**, separate from the supplied Examples A and B. Let the operation set be $\mathcal O=\{a,b\}$, with three available machines. Operation $a$ uses machine 1 for 3 units; $b$ uses machine 3 for 3 units. Machine 2 is unused by these two operations. Suppose $a$ must finish before $b$ starts. Choose deadline $H=6$.

For this walkthrough, keep the broad candidate sets $T_a=T_b=\{0,1,2,3\}$. Each candidate individually allows its operation to finish by 6. Some candidates cannot satisfy precedence; chapter 04 shows how to remove such choices in advance. Keeping them here is deliberate: the indexing and decoding are visible, and a precedence penalty can exclude bad combinations. We are not claiming that all four starts can occur in a feasible full schedule.

The data and rules are fixed before the solver chooses bits:

| Operation | Required machine | Duration | Retained candidate starts |
|---|---|---:|---|
| $a$ | Machine 1 | 3 | 0, 1, 2, 3 |
| $b$ | Machine 3 | 3 | 0, 1, 2, 3 |

**Flattening means choosing a list order and numbering the existing choices.** We choose $a$'s group first, then $b$'s; inside each group, increasing start time. This gives the complete lookup table:

| Position $i$ | Same bit with its descriptive name | Meaning when its value is 1 |
|---|---|---|
| 1 | $x_1=x_{a,0}$ | Start $a$ at 0 on machine 1. |
| 2 | $x_2=x_{a,1}$ | Start $a$ at 1 on machine 1. |
| 3 | $x_3=x_{a,2}$ | Start $a$ at 2 on machine 1. |
| 4 | $x_4=x_{a,3}$ | Start $a$ at 3 on machine 1. |
| 5 | $x_5=x_{b,0}$ | Start $b$ at 0 on machine 3. |
| 6 | $x_6=x_{b,1}$ | Start $b$ at 1 on machine 3. |
| 7 | $x_7=x_{b,2}$ | Start $b$ at 2 on machine 3. |
| 8 | $x_8=x_{b,3}$ | Start $b$ at 3 on machine 3. |

There is no universal meaning attached to the number 8. Here $x_8$ means $x_{b,3}$ because **we placed that candidate eighth**. We retain the lookup when building the model and interpreting returned bits. The list order does not determine which operation runs first.

**Encoding a schedule into bits.** Suppose $a$ starts at 0 and $b$ at 3. Look up those choices: positions 1 and 8. Set those bits to 1 and all other bits to 0:

$$
x=(1,0,0,0,\;0,0,0,1).
$$

This represents $a$ occupying $[0,3)$ and $b$ occupying $[3,6)$. A single selected start determines the whole interval because the processing duration is known.

**Decoding returned bits into a candidate schedule.** Scan each operation's group. Find its selected bit and use the lookup to recover the start. The vector above gives $S_a=0$ and $S_b=3$. Retrieve the machines and durations from the fixed operation data. Check all the original scheduling rules. If a group has zero or multiple selected bits, it fails to specify exactly one start; reject it as an invalid one-hot encoding.

Decoding and checking are separate steps. For example, $x=(0,1,0,0,\;0,0,1,0)$ decodes to $S_a=1$ and $S_b=2$. Each operation has one start, but $a$ finishes at 4, after $b$ has already started. That is an encoding-valid but precedence-infeasible candidate.

### General flattening: any operation count, any group sizes

Choose an operation listing $o_1,\ldots,o_q$, where $q$ is the number of operations. Sort each operation's allowed times as $t_{j,0}<\cdots<t_{j,K_{o_j}-1}$ for operation $o_j$. Here $j$ identifies its group and $r$ will identify a time's zero-based position inside that group. Concatenate the groups. They do not need equal lengths.

The mapping $\phi$ returns the numbered position of a candidate:

$$
\phi(o_j,t_{j,r})=\sum_{\ell=1}^{j-1}K_{o_\ell}+r+1,
\qquad r=0,\ldots,K_{o_j}-1.
$$

Read this as **number of entries in all earlier groups, plus the one-based position within this group**. The extra 1 changes zero-based $r$ into one-based bit numbering. In the example, $b$ is the second group, four entries precede it, and time 3 is its fourth choice. Thus $\phi(b,3)=4+4=8$.

There are $N=\sum_oK_o$ bits altogether. Store both directions of the mapping: $(o,t)$ to bit position for encoding, and position to $(o,t)$ for decoding. The machine follows from $\mu(o)$; precedence follows from the operation labels in $\mathcal A$. We do not try to infer those facts from the numerical bit index. If an operation can choose between machines, that needs extra machine-choice information in the encoding; it is outside the fixed-machine baseline.

### General form

A binary variable, or **bit**, is a variable $x_i\in\{0,1\}$. An **assignment** means choosing a value for every bit. The vector $x=(x_1,\ldots,x_N)$ lists all those values in the stored order; it is one complete candidate. There are $2^N$ assignments because each of the $N$ positions independently has two possible values. Some assignments will violate the intended rules.

A **quadratic unconstrained binary optimisation** problem chooses the bits to minimise an energy function. The name $E(x)$ means “calculate the energy from the candidate bit vector $x$”; its result is one scalar number. The modeller supplies fixed coefficients: $c_0$ is a constant added to every candidate, $a_i$ multiplies one bit, and $w_{ij}$ multiplies a pair of different bits. With those definitions, the general formula is

$$
E(x)=c_0+\sum_{i=1}^{N}a_i x_i+\sum_{1\le i<j\le N}w_{ij}x_i x_j.
$$

Read it in three parts: start with the constant $c_0$; add $a_ix_i$ for every bit; then add $w_{ij}x_ix_j$ for every pair with $i<j$. The solver chooses $x$, not these coefficients. The condition $i<j$ means each pair appears once: include (1,2), but do not also include (2,1). A missing pair has coefficient zero. The formula alone does not identify operations or times; that meaning is retained in the lookup we just constructed.

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

A solver is allowed to try every assignment of zeros and ones. We therefore need a way to make rule-breaking assignments worse than assignments that obey the rules. A **penalty function** takes the candidate bits as input and returns an extra cost: zero when its rule holds, positive when the rule is broken.

The name of a penalty is chosen by the modeller. For example, $P_{\mathrm{once}}(x)$ is read **“P subscript once, evaluated at x.”** Break that down:

| Part of the notation | What it means |
|---|---|
| $P$ | The name of a function that calculates a penalty. |
| The word “once” in the subscript | A label for the rule being checked: exactly one selected start for each operation. It is not a variable or a multiplication. |
| $(x)$ | The input: the whole candidate vector of zeros and ones. |
| $P_{\mathrm{once}}(x)$ as a whole | One computed number, the total penalty for violating that rule. It is not another bit the solver chooses. |

We will build this function below. Other functions will check other rules. Their names tell us which rule they check; their formulas specify how to calculate the cost. If every such cost is nonnegative, adding them gives zero only when each is zero. For instance, two nonnegative costs cannot cancel each other: 0+0 is zero, while adding any positive cost makes the sum positive.

#### Exactly one of $K$ choices

For one operation $o$, there are $K_o$ candidate starts in $T_o$. Exactly one of its start bits should equal 1. We will first count how many are selected, then turn that count into a penalty.

**Step 1: count selected starts.** Adding zeros and ones counts the ones. Write

$$
n_o(x)=\sum_{t\in T_o}x_{o,t}.
$$

Here $n_o(x)$ means “number of selected starts for operation $o$ in this candidate.” It is calculated from the bits, not independently chosen. The sum says: visit each candidate time $t$ in $T_o$ and add its bit. Exactly one start means $n_o(x)=1$.

**Step 2: subtract the desired count, 1.** The expression $n_o(x)-1$ is zero at one selection. It is −1 when nothing is selected, +1 when two starts are selected, and +2 when three are selected. This difference is sometimes called a **residual**, meaning how far the candidate is from satisfying the equation.

**Step 3: square the difference.** We minimise energy, so a negative violation cost would be a reward. Squaring makes both negative and positive differences nonnegative: $(n_o(x)-1)^2$. It is zero precisely at the desired count 1.

For a four-choice operation group, these illustrative assignments give:

| Group bits | Number selected $n_o(x)$ | Subtract 1 | Square it: this operation's penalty |
|---|---:|---:|---:|
| 0000 | 0 | −1 | 1 |
| 1000 | 1 | 0 | 0 |
| 0100 | 1 | 0 | 0 |
| 1100 | 2 | 1 | 1 |
| 1110 | 3 | 2 | 4 |
| 1111 | 4 | 3 | 9 |

The position of the one determines the chosen time; this particular penalty only checks how many starts were selected. Machine and precedence penalties will check whether the selected times are compatible.

**Step 4: add this cost for every operation.** This defines the total function named $P_{\mathrm{once}}$:

$$
P_{\mathrm{once}}(x)=\sum_{o\in\mathcal O}(n_o(x)-1)^2
=\sum_{o\in\mathcal O}\left(\sum_{t\in T_o}x_{o,t}-1\right)^2.
$$

Read the nested version from inside out. For one operation, the inner sum counts its selected starts. Subtract 1. Square. Then the outer sum adds those costs over operations. The inner and outer sums do different jobs; we must not square one count across the whole factory. Selecting two starts for $a$ and none for $b$ would give two selected starts in total, but neither operation would have exactly one.

In our eight-bit teaching example from chapter 02, the total becomes

$$
P_{\mathrm{once}}(x)=(x_1+x_2+x_3+x_4-1)^2
+(x_5+x_6+x_7+x_8-1)^2.
$$

For $x=(1,0,0,0,\;0,0,0,1)$, each bracket is zero, so the total is 0. For $x=(1,1,0,0,\;0,0,0,1)$, operation $a$ has two starts and $b$ has one: the total is $(2-1)^2+(1-1)^2=1$. This arithmetic detects the invalid group without needing to interpret a physical schedule for two starts of the same operation.

#### Why the square becomes a quadratic: every multiplication shown

We now know what the penalty means. The next question is whether its formula can be stored as a QUBO: constants, single bits and products of two bits. Keep the same teaching example. Operation $a$ has bits $x_1,x_2,x_3,x_4$, one for each of its four candidate starts.

The rule is $x_1+x_2+x_3+x_4=1$. Squaring its penalty bracket means multiplying it by an identical bracket:

$$
(x_1+x_2+x_3+x_4-1)^2
=(x_1+x_2+x_3+x_4-1)(x_1+x_2+x_3+x_4-1).
$$

Multiply each of the five terms on the left by every term on the right. That produces five rows of five products, twenty-five products altogether:

$$
\begin{aligned}
(x_1+x_2+x_3+x_4-1)^2={}&x_1^2+x_1x_2+x_1x_3+x_1x_4-x_1\\
&+x_2x_1+x_2^2+x_2x_3+x_2x_4-x_2\\
&+x_3x_1+x_3x_2+x_3^2+x_3x_4-x_3\\
&+x_4x_1+x_4x_2+x_4x_3+x_4^2-x_4\\
&-x_1-x_2-x_3-x_4+1.
\end{aligned}
$$

Read the rows in order. The first is $x_1$ times the whole second bracket, the next is $x_2$ times it, then $x_3$, then $x_4$. The last is $-1$ times the whole bracket; in particular, $(-1)(-1)=+1$ gives the final constant.

Now collect terms with the same variables. Multiplication commutes: $x_1x_2=x_2x_1$, so those two products add to $2x_1x_2$. The same happens for each distinct pair. The six pairs are (1,2), (1,3), (1,4), (2,3), (2,4), (3,4). Each bit also appears twice with a minus sign, making $-2x_i$. Keeping the squared terms for one more line gives

$$
\begin{aligned}
(x_1+x_2+x_3+x_4-1)^2={}&x_1^2+x_2^2+x_3^2+x_4^2\\
&+2x_1x_2+2x_1x_3+2x_1x_4\\
&+2x_2x_3+2x_2x_4+2x_3x_4\\
&-2x_1-2x_2-2x_3-2x_4+1.
\end{aligned}
$$

The variables are bits. A squared bit equals itself because $0^2=0$ and $1^2=1$. Replace $x_i^2$ by $x_i$ for each of the four bits. Each bit's linear contributions now add to $x_i-2x_i=-x_i$:

$$
\begin{aligned}
(x_1+x_2+x_3+x_4-1)^2={}&1-x_1-x_2-x_3-x_4\\
&+2x_1x_2+2x_1x_3+2x_1x_4\\
&+2x_2x_3+2x_2x_4+2x_3x_4.
\end{aligned}
$$

This is the **same function**, written in QUBO form. Its constant is 1; each bit has coefficient −1; each distinct pair has coefficient +2. As a numerical check, set $(x_1,x_2,x_3,x_4)=(1,1,0,0)$. The original form gives $(1+1+0+0-1)^2=1$. In the expansion, the linear part is $1-1-1-0-0=-1$. Of the six pair products, only $x_1x_2$ is nonzero; its weighted contribution is 2. The final value is $-1+2=1$ as well.

**Generalisation to any $K_o$ choices.** The pattern does not depend on three. When a sum is squared, every bit is multiplied by itself once, and every two different bits occur in both multiplication orders. For one operation's group this means

$$
\left(\sum_{t\in T_o}x_{o,t}\right)^2
=\sum_{t\in T_o}x_{o,t}^2
+2\sum_{\substack{t,u\in T_o\\t<u}}x_{o,t}x_{o,u}.
$$

The notation under the last sum says “choose two candidate times from this group, with $t<u$.” This lists each pair once; the factor 2 accounts for both multiplication orders. For the four sorted times in our example, it gives the six pairs just listed. A group of $K_o$ times has $K_o(K_o-1)/2$ distinct pairs: each time has $K_o-1$ different partners, giving $K_o(K_o-1)$ ordered choices; divide by two because exchanging the partners describes the same pair.

Use the ordinary algebra identity $(A-1)^2=A^2-2A+1$, where here $A$ means the sum of this group's bits. Substitute the just-expanded square and replace every squared bit by itself. The result, for an arbitrary operation group, is

$$
\left(\sum_{t\in T_o}x_{o,t}-1\right)^2
=1-\sum_{t\in T_o}x_{o,t}
+2\sum_{\substack{t,u\in T_o\\t<u}}x_{o,t}x_{o,u}.
$$

There are no products of three different bits. Therefore it is quadratic for every group size. Adding these expanded expressions over operations gives the same total $P_{\mathrm{once}}(x)$ defined above.

If a group contains $K_o=0$ candidates, its sum is empty, so its penalty is $(0-1)^2=1$; that operation has no available start. If $K_o=1$, its one bit gives $(x-1)^2=x^2-2x+1=1-x$. A preprocessing step can fix that required bit to 1 and remove it. These edge cases use the same rule. The penalty is a squared count difference, so it does not literally count the number of broken rules when multiple starts are selected.

#### Forbid one simultaneous pair

Suppose selecting $x_i$ alone is allowed and selecting $x_j$ alone is allowed, but selecting both together is forbidden. We name its penalty $P_{\mathrm{pair}}$: “pair” is a word labelling the rule, and its two inputs are the two bits. Define

$$
P_{\mathrm{pair}}(x_i,x_j)=x_ix_j.
$$

The formula follows directly from binary multiplication:

| $x_i$ | $x_j$ | Product $x_ix_j$ | What happens? |
|---|---|---|---|
| 0 | 0 | $0\cdot0=0$ | Neither choice selected; this pair rule is satisfied. |
| 0 | 1 | $0\cdot1=0$ | Only the second selected; this pair rule is satisfied. |
| 1 | 0 | $1\cdot0=0$ | Only the first selected; this pair rule is satisfied. |
| 1 | 1 | $1\cdot1=1$ | Both selected; the penalty detects the forbidden combination. |

This enforces **at most one of this pair**, not exactly one: 00 remains allowed. Exactly-once penalties separately require an operation to have a start. When a particular pair of start choices would overlap on one machine or violate precedence, this product is the building block we add to the energy.

#### A more general equality

For real coefficients $d_i$ and a target $b$, a linear equality $\sum_i d_i x_i=b$ can be penalised by

$$
\left(\sum_i d_i x_i-b\right)^2
=b^2+\sum_i(d_i^2-2bd_i)x_i
+2\sum_{i<j}d_id_jx_ix_j.
$$

It remains quadratic because the expression inside the square is linear. Squaring a quadratic constraint would generally produce degree-four terms. Not every constraint becomes a QUBO merely by squaring it.

Here is where every coefficient in that expansion comes from. Let $A=\sum_i d_i x_i$ just for this calculation. Multiplying $(A-b)(A-b)$ gives $A^2-bA-bA+b^2=A^2-2bA+b^2$. To expand $A^2$, every weighted bit multiplies every other weighted bit. The self-products are $d_i^2x_i^2$; two distinct terms give both $d_id_jx_ix_j$ and $d_jd_ix_jx_i$, adding to $2d_id_jx_ix_j$. Thus

$$
\begin{aligned}
(A-b)^2={}&\sum_i d_i^2x_i^2+2\sum_{i<j}d_id_jx_ix_j\\
&-2b\sum_i d_ix_i+b^2.
\end{aligned}
$$

Replace $x_i^2$ by $x_i$. For each bit $x_i$, add its self-product coefficient $d_i^2$ and its contribution $-2bd_i$ from the subtraction. That gives $(d_i^2-2bd_i)x_i$. The pair terms and constant already have their final forms. The previous displayed equation is exactly this collection, with the constant written first.

<details class="derivation"><summary>Further algebra: degree reduction and constrained linearisation — you can return here after building the complete model in chapter 04</summary>

### Transformation workshop · What can actually become linear or quadratic? {#transformations}

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

</details>

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

To see each counting step, an integer interval from $a$ to $b$ inclusive contains $b-a+1$ entries when $b\ge a$: subtracting counts the gaps, and adding 1 counts the starting entry too. Our endpoints give $(H-p_o-\tau_o)-h_o+1=H-(h_o+p_o+\tau_o)+1=H-P_j+1$. If that is negative, the set is empty and its size is zero, which explains the maximum with zero. Each of job $j$'s $q_j$ operations has that many candidates under these chain-only bounds, so multiply by $q_j$; then add the counts over jobs to obtain $N$. Here $P_j$ is fixed job-duration data, while $P_{\mathrm{once}}(x)$ is a penalty function; their full names distinguish these different quantities.

### Step 2 · Assign a precise meaning to every bit

For each operation and each surviving start time, introduce

$$
x_{o,t}=\begin{cases}1&\text{operation }o\text{ starts at }t,\\0&\text{it does not.}\end{cases}
$$

There is no bit for a pruned time. We are not setting such a bit to zero later; it is absent from the model. The bits of one operation form its **one-hot group**.

Connect this to the teaching example from chapter 02: its two 3-unit operations form a chain $a\to b$ and must finish by 6. For $a$, the head is 0 and the tail is 3, giving window $0\le S_a\le6-3-3=0$. For $b$, the head is 3 and the tail is 0, giving $3\le S_b\le6-3-0=3$. These stronger bounds leave only $a$ at 0 and $b$ at 3. The eight-bit representation in chapter 02 was deliberately before this pruning; after pruning, only two candidate bits remain. Rebuild the lookup for the retained candidates. Bit numbers belong to the particular built model, so changing the horizon or removing candidates requires keeping its numbering, coefficients and decoder consistent.

### Step 3 · Require exactly one start per operation

Use the function constructed in chapter 03. For each operation: add its start bits, subtract 1, square, then add the result to the costs for the other operations. Its name is $P_{\mathrm{once}}(x)$, the total exactly-once penalty:

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

Fix any ordering of operation labels and write $o<v$ to enumerate each pair once. Let $\mathcal C$ contain every pair of candidate starts $((o,t),(v,u))$ with $o<v$, $\mu(o)=\mu(v)$, and the overlap condition above.

Name the total cost $P_{\mathrm{cap}}(x)$, read “machine-capacity penalty evaluated on candidate $x$.” For every forbidden pair in $\mathcal C$, multiply its two bits; add those products. One product is 1 only when both overlapping starts have been selected. That gives

$$
P_{\mathrm{cap}}(x)=\sum_{((o,t),(v,u))\in\mathcal C}x_{o,t}x_{v,u}.
$$

This detects capacity violations between distinct operations. Within an operation, exactly-once already handles multiple selected starts. In a general job shop, two operations of the same job may revisit one machine; use operation identities, rather than assuming “same machine” always means “different jobs.”

### Step 5 · Enumerate precedence conflicts

For each arc $(o,v)\in\mathcal A$, selected starts $t,u$ violate precedence precisely when $u<t+p_o$. Let $\mathcal D$ contain these directed conflicting candidate-start pairs.

Name this total $P_{\mathrm{prec}}(x)$, read “precedence penalty evaluated on candidate $x$.” It uses the same pair-product idea as capacity, but its list of forbidden pairs comes from required operation order. For each such pair, add 1 only when both conflicting starts are selected:

$$
P_{\mathrm{prec}}(x)=\sum_{((o,t),(v,u))\in\mathcal D}x_{o,t}x_{v,u}.
$$

Only adjacent job-chain arcs are needed: satisfying every adjacent precedence implies every transitive one. Adding redundant transitive arcs can change nonzero energies and couplings without changing the feasible schedules.

### Step 6 · Combine the penalties

The three penalty functions above measure different violations. Their weights are fixed positive numbers, chosen by the modeller: $\lambda_{\mathrm{once}}$ multiplies the exactly-once penalty, $\lambda_{\mathrm{cap}}$ the machine-capacity penalty, and $\lambda_{\mathrm{prec}}$ the precedence penalty. The subscripts name the rule; they are not additional variables. A larger weight makes a given violation contribute more to the energy the solver minimises. All three rules remain mandatory in the intended scheduling model.

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

An $N\times N$ matrix $Q$ is a square grid with $N$ rows and $N$ columns. Entry $Q_{ij}$ means row $i$, column $j$. Its row and column indices refer to the numbered bits, so the stored mapping is still essential. Regard $x$ as a column vector and $x^\mathsf T$ as its transpose, the same entries arranged in a row.

First see the multiplication for a general two-bit matrix, with arbitrary entries. This is a demonstration of the operation, not a restriction to a two-bit scheduling problem:

$$
Q=\begin{pmatrix}Q_{11}&Q_{12}\\Q_{21}&Q_{22}\end{pmatrix},\qquad
x=\begin{pmatrix}x_1\\x_2\end{pmatrix}.
$$

**First multiply $Q$ by the column.** In each row, multiply entries in matching positions, then add. The first row gives $Q_{11}x_1+Q_{12}x_2$; the second gives $Q_{21}x_1+Q_{22}x_2$. Therefore

$$
Qx=\begin{pmatrix}Q_{11}x_1+Q_{12}x_2\\Q_{21}x_1+Q_{22}x_2\end{pmatrix}.
$$

**Then multiply the row $x^\mathsf T$ by that result.** Again multiply matching entries and add, obtaining one number:

$$
x^\mathsf TQx=x_1(Q_{11}x_1+Q_{12}x_2)+x_2(Q_{21}x_1+Q_{22}x_2).
$$

Distribute each outside bit over its bracket. This gives $Q_{11}x_1^2+Q_{12}x_1x_2+Q_{21}x_2x_1+Q_{22}x_2^2$. Replace the squared bits by themselves, and combine the two products involving bits 1 and 2, since $x_2x_1=x_1x_2$:

$$
x^\mathsf TQx=Q_{11}x_1+Q_{22}x_2+(Q_{12}+Q_{21})x_1x_2.
$$

For any $N$, exactly the same row-by-column multiplication contributes one term $Q_{ij}x_ix_j$ for every cell in the matrix. Adding all cells is a double sum: for each row $i$, add over all columns $j$, then add the rows. Self-pairs lie on the diagonal, and each distinct pair has two mirror cells. Thus the general formula is

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

“Telescopes” means intermediate terms cancel in pairs. Write the sum out as $(y_{o,0}-y_{o,1})+(y_{o,1}-y_{o,2})+\cdots+(y_{o,K-1}-y_{o,K})$. Every interior bit appears once positively and once negatively, so only the two boundary values remain. They were fixed to 1 and 0, giving 1. For $K=4$, the indicators are explicitly $1-y_{o,1}$, $y_{o,1}-y_{o,2}$, $y_{o,2}-y_{o,3}$, and $y_{o,3}$. Their values for all eight three-bit words are:

| Threshold word $y_{o,1}y_{o,2}y_{o,3}$ | Indicators $(\chi_0,\chi_1,\chi_2,\chi_3)$ | Decoded choice |
|---|---|---|
| 000 | (1,0,0,0) | Rank 0. |
| 001 | (1,0,−1,1) | Invalid: a negative indicator. |
| 010 | (1,−1,1,0) | Invalid: a negative indicator. |
| 011 | (1,−1,0,1) | Invalid: a negative indicator. |
| 100 | (0,1,0,0) | Rank 1. |
| 101 | (0,1,−1,1) | Invalid: a negative indicator. |
| 110 | (0,0,1,0) | Rank 2. |
| 111 | (0,0,0,1) | Rank 3. |

But the sum is also 1 on **invalid** words. For $K=4$, word 010 gives $(\chi_0,\chi_1,\chi_2,\chi_3)=(1,-1,1,0)$. It does not represent a valid choice. A sum of one is insufficient when indicators can be negative.

Define $P_{\mathrm{wall}}(y)$ as the total penalty for invalid 0→1 rises in the threshold words. For a neighbouring pair, $(1-y_{o,s})$ is 1 precisely when the left bit is 0, and $y_{o,s+1}$ is 1 precisely when the right bit is 1. Their product therefore detects exactly that forbidden rise. Add the products across neighbouring internal bits and across operation groups:

$$
P_{\mathrm{wall}}(y)=\sum_o\sum_{s=1}^{K_o-2}(1-y_{o,s})y_{o,s+1}.
$$

Each summand detects an upward transition 0→1. The sum is zero exactly for valid domain-wall words. For $K=1$ no bits are needed: the unique indicator is the constant 1. For $K=2$ there is one bit, both bitstrings are valid, and there is no wall term. Handle empty domains separately as an infeasible horizon.

### Why substituting domain-wall indicators preserves degree

Each $\chi_r$ is affine, so a product of two indicators has degree at most two. Therefore the **conflict part** of the scheduling energy remains quadratic after substitution. Replace exactly-once constraints by the wall constraint; do not blindly substitute into an already simplified one-hot square. That simplification used $\chi_r^2=\chi_r$, which is false for an invalid indicator equal to $-1$.

Name the substituted weighted capacity and precedence sum $E_{\mathrm{conflict}}(y)$. The name means conflict energy calculated from the candidate threshold bits $y$. On valid words it has the same conflict costs as the one-hot model; on invalid words its indicators can be negative. We will add a positive wall weight $\eta$ times the just-defined $P_{\mathrm{wall}}(y)$. Their sum defines the domain-wall feasibility energy:

$$
E_H^{\mathrm{DW}}(y)=E_{\mathrm{conflict}}(y)+\eta P_{\mathrm{wall}}(y),
$$

The superscript DW labels the domain-wall representation. Since invalid words may make $E_{\mathrm{conflict}}(y)$ negative, **an arbitrary positive wall weight is not enough**: it must exceed any negative conflict benefit obtainable from an invalid word.

### Guarantee · A sufficient wall weight

Write the original conflict sum as a sum of nonnegative weighted products $\kappa_{ab}\chi_a\chi_b$ over different operations. Here $a,b$ label candidate starts, not bits in the new encoding. For candidate $a$, add all conflict weights involving that candidate and name the result $d_a$. This is its **weighted incident degree**: “incident” means touching that candidate in the conflict graph. Let $d_{\max}$ be the largest such sum. Written as formulas,

$$
d_a=\sum_{b:\{a,b\}\text{ is a conflict}}\kappa_{ab},\qquad d_{\max}=\max_a d_a.
$$

Choose $\eta>d_{\max}$. Here are the steps establishing why this is sufficient:

1. Write $V=P_{\mathrm{wall}}(y)$ for the number of upward transitions. At a rise, the corresponding indicator is $0-1=-1$. At any other adjacent pattern, its value is 0 or 1. Thus there are exactly $V$ negative indicators.
2. Every indicator is −1, 0 or 1. A conflict product is negative only when one indicator is −1 and the other is +1. Two negative indicators multiply to +1; a zero factor makes the product zero.
3. Associate each negative conflict term with its negative indicator. All weights touching one candidate sum to at most $d_{\max}$, so one negative indicator can contribute no more than $d_{\max}$ in total negative magnitude.
4. There are $V$ negative indicators. Therefore the complete conflict sum cannot be below $-d_{\max}V$; all other contributions are nonnegative.
5. The wall term adds $\eta V$. Consequently the total cannot be below $-d_{\max}V+\eta V=(\eta-d_{\max})V$. For an invalid word $V>0$, and our strict choice $\eta>d_{\max}$ makes this positive.

In formula form, the conclusion is

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

Read the indicator product one digit at a time. For a target digit 1, using $u_{o,s}$ returns 1 exactly when the candidate digit matches it. For a target digit 0, using $1-u_{o,s}$ returns 1 exactly when the candidate digit is 0. Multiply these match tests. If every digit matches, every factor is 1 and the product is 1. If any digit differs, one factor is 0 and the product is 0. For example, the two-digit target code 10 has indicator $u_{o,1}(1-u_{o,0})$: code 10 gives $1(1-0)=1$, while 00, 01 and 11 each give zero. That explains both what the formula computes and why more binary digits can increase its polynomial degree.

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

<details class="derivation"><summary>Calculate every coefficient of that slack example</summary>

Use the general squared-equality rule from chapter 03 with target $b=3$ and input coefficients $(d_1,d_2,d_3,d_4)=(2,3,1,2)$ for $(x_1,x_2,\sigma_0,\sigma_1)$. The offset is $b^2=3^2=9$. A linear coefficient is $d_i^2-2bd_i$, and a pair coefficient is $2d_id_j$. Applying those two rules to every term gives:

| Term | Calculation | Coefficient |
|---|---|---:|
| $x_1$ | $2^2-2\cdot3\cdot2=4-12$ | −8 |
| $x_2$ | $3^2-2\cdot3\cdot3=9-18$ | −9 |
| $\sigma_0$ | $1^2-2\cdot3\cdot1=1-6$ | −5 |
| $\sigma_1$ | $2^2-2\cdot3\cdot2=4-12$ | −8 |
| $x_1x_2$ | $2\cdot2\cdot3$ | 12 |
| $x_1\sigma_0$ | $2\cdot2\cdot1$ | 4 |
| $x_1\sigma_1$ | $2\cdot2\cdot2$ | 8 |
| $x_2\sigma_0$ | $2\cdot3\cdot1$ | 6 |
| $x_2\sigma_1$ | $2\cdot3\cdot2$ | 12 |
| $\sigma_0\sigma_1$ | $2\cdot1\cdot2$ | 4 |

These four linear terms, six pair terms and the offset are the entire expansion. We can now place the linear coefficients on the matrix diagonal and the pair coefficients above it using the already-established ordering.

</details>

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

### Why use +1 and −1 if the quantum computer still outputs 0 and 1?

**The output labels and the values used to express the cost are different things.** The quantum operator called $Z$ naturally assigns eigenvalue +1 to $|0\rangle$ and −1 to $|1\rangle$. Rewriting a bit cost in those values lets us express it using $Z$ operators and implement gates derived from that cost. The bit labels remain 0 and 1 throughout.

| Quantum basis state | Ordinary measured bit $x_i$ | Corresponding spin value $z_i=1-2x_i$ |
|---|---:|---:|
| $|0\rangle$ | 0 | +1 |
| $|1\rangle$ | 1 | −1 |

**Invented one-bit example.** Suppose $E(x)=x$: choosing 0 costs 0 and choosing 1 costs 1. Substitute $x=(1-z)/2$ to get $E(z)=(1-z)/2$. Its quantum cost operator is $(I-Z)/2$, where $I$ leaves a vector unchanged. On $|0\rangle$, its value is $(1-1)/2=0$. On $|1\rangle$, its value is $(1-(-1))/2=1$. Every candidate keeps its original cost. We have changed the mathematical expression used to control the circuit; measurement still returns the candidate's ordinary bit.

Chapter 10 defines these operators and states more fully. Its [Bloch-sphere visual](#bloch-sphere-lab) labels the north pole both “bit 0” and “$Z=+1$,” and the south pole both “bit 1” and “$Z=-1$.” Those are two labels for each same basis state, not four possible outcomes.

### Derivation · Expand a generic linear and pair term

For a single-bit term, replace $x_i$ by $(1-z_i)/2$ and distribute $a_i$ over its two terms:

$$
a_ix_i=\frac{a_i}{2}-\frac{a_i}{2}z_i,
$$

For a pair, make both substitutions. Multiplying the two factors of $1/2$ gives $1/4$. Multiply the remaining brackets term by term: $1\cdot1=1$, $1\cdot(-z_j)=-z_j$, $(-z_i)\cdot1=-z_i$, and $(-z_i)(-z_j)=+z_iz_j$. Therefore

$$
w_{ij}x_ix_j
=\frac{w_{ij}}4(1-z_i)(1-z_j)
=\frac{w_{ij}}4(1-z_i-z_j+z_iz_j).
$$

Distributing $w_{ij}/4$ gives the constant $w_{ij}/4$, the two linear terms $-w_{ij}z_i/4$ and $-w_{ij}z_j/4$, and the pair term $w_{ij}z_iz_j/4$.

Now name the new coefficients. Let $c_I$ be the spin-model constant, $h_i$ the coefficient multiplying spin $z_i$, and $J_{ij}$ the coefficient multiplying $z_iz_j$. Physicists call $h_i$ a field and $J_{ij}$ a coupling; they are fixed coefficients, just as $a_i$ and $w_{ij}$ were. Collecting the transformed terms gives

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

Here is why those totals have those signs and sums. The $z_iz_j$ term appears only in its own transformed pair, giving $J_{ij}=w_{ij}/4$. The single spin $z_i$ gets $-a_i/2$ from its own linear term and $-1/4$ times the weight of every pair touching $i$. A touching pair is stored as $w_{ji}$ if $j<i$, and as $w_{ij}$ if $j>i$, because pairs were always listed smaller index first. These are the two sums in $h_i$. Finally, every transformed linear term adds $a_i/2$ to the constant, every pair adds $w_{ij}/4$, and the original $c_0$ remains; add those to get $c_I$.

The coefficients here come from our polynomial with each pair counted once. They must not be applied unmodified to a symmetric matrix whose off-diagonal entries are half-pair coefficients.

### Example · Reuse the invented two-bit polynomial

For $c_0=1$, $a_1=3$, $a_2=-2$, $w_{12}=4$, compute the four transformed coefficients individually: $J_{12}=4/4=1$; $h_1=-3/2-4/4=-5/2$; $h_2=-(-2)/2-4/4=1-1=0$; and $c_I=1+(3-2)/2+4/4=1+1/2+1=5/2$. Inserting these four numbers gives

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

**Reading scope.** We take a small set of physical postulates as starting rules, then explain the consequences needed for these circuits. Hardware engineering, interpretations of measurement and a derivation of quantum theory from deeper principles are outside scope. The amplitude arithmetic, basis-vector expansion, probabilities and purpose of each algorithmic step are inside scope.

### Why use quantum here? A choice of search mechanism {#why-quantum}

**Algorithm choice.** Scheduling is a classical decision problem. We introduce a quantum processor because it provides a way to prepare and sample distributions of candidate answers using joint quantum states, phase changes and interference. It is a possible computing tool for the search, not a claim that the factory itself needs a quantum model.

Here is the chain of reasoning. First, computing $E(x)$ for one candidate is straightforward once the coefficients are known. Finding a good candidate among many possibilities is the difficult part. Second, a quantum circuit can change amplitudes for the joint register through implementable local gates; we do not first type a list of all $2^N$ amplitudes into the device. Third, gates derived from the cost give the circuit information about which combinations are expensive. Mixing and classical parameter tuning try to turn that information into a useful sampling distribution. This is the motivation for investigating QAOA.

The missing step in that motivation would be a **performance guarantee**: can this method find good feasible schedules with less total work than suitable classical methods? The construction alone does not answer that. A large quantum state space, interference, or an attractive circuit diagram does not establish an advantage. Chapter 12 describes the matched comparisons and costs needed to assess it.

For this guide, the reason to study QAOA is to understand one proposed search method and how it connects to an already-defined optimisation model. Classical exact methods and heuristics remain valid ways to solve that same model. Whether to deploy quantum hardware is a separate, evidence-based decision.

Visual checkpoints in this chapter: [amplitude arrows and probabilities](#amplitude-arrow-lab), [the Bloch sphere and complex amplitudes](#bloch-sphere-lab), [one-qubit gate steps](#quantum-basics-lab), and [basis vectors versus the whole register](#register-explorer-lab). Chapter 11 adds the [two-qubit QAOA and measurement visual](#qaoa-register-lab). Each is an ideal teaching calculation, not a hardware result.

### Before the notation · Why quantum physics is involved at all

A quantum computer is a controlled **physical system**. A qubit can be implemented using two selected states of a physical system, such as two energy levels. We label the readout results 0 and 1. Those labels are chosen for computation; they do not mean an operation's start time or its scheduling cost until we apply our encoding.

Quantum theory describes how preparation and physical operations change the system, and predicts the probabilities of measurement outcomes. Its amplitudes are not invented as scheduling penalties. They belong to the physical theory we use to design the circuit and predict its results.

The intuition for an amplitude is a **directed contribution to an outcome**, pictured as an arrow. The arrow has a length and a direction. Quantum operations can combine contributions: aligned arrows add; opposite arrows cancel. An outcome's probability comes from the squared length of its final amplitude. An amplitude is not a little physical arrow inside the device, a cost, or a probability that may be negative. It is a component of the quantum state's mathematical description whose relative direction has observable consequences through interference.

Why does physics use these rules? Experiments show both discrete detection events and interference in the frequencies of those events. Adding ordinary probabilities alone misses interference; adding complex amplitudes before taking squared magnitudes predicts it. **Physical postulate — Born rule, given here.** For a normalised state, the probability of a standard-basis outcome is the squared magnitude of its amplitude. We use this experimentally supported rule; we do not derive it from scheduling or from the fact that a number can be complex. The wave analogy helps explain addition and cancellation; quantum amplitudes are not literal water-wave heights. See [Feynman's discussion of quantum behaviour](https://www.feynmanlectures.caltech.edu/III_01.html) and [IBM's account of the Born rule](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information).

For a complex amplitude, the probability is **squared magnitude**, $|\alpha|^2$, not the ordinary complex square $\alpha^2$. If $\alpha=a+\mathrm i b$, then $|\alpha|^2=a^2+b^2$. For instance, $\mathrm i^2=-1$, whereas $|\mathrm i|^2=1$. Probabilities cannot be negative. Real amplitudes in our first walkthrough let us see the idea before using general complex numbers.

### Cost and probability answer different questions

Our original cost $E(x)$ answers: **how good is candidate $x$?** The measurement probability $|\alpha_x|^2$ answers: **how likely is this prepared circuit to output candidate $x$?** The subscript $x$ labels the whole candidate here; we will unpack the notation after the one-qubit walkthrough.

We know the rule for computing a candidate's cost, but we do not automatically know which candidate has the lowest cost. The difficulty is searching many candidates. QAOA uses the cost formula to build gates, then tunes a circuit in an attempt to put more measurement probability on useful candidates. A high-cost candidate can still have high probability for a poorly chosen circuit. There is no built-in equality between cost, amplitude and probability.

An ordinary random search also has output probabilities and evaluates candidate costs. The quantum proposal is to use amplitude evolution that preserves relative phase information (called coherent evolution), together with interference, to shape its output distribution. Whether that is competitive must be established by comparison with classical methods on the actual problem. A QUBO does not require a quantum solver, and merely using qubits does not guarantee an improvement.

### Does being more likely mean being more correct?

**No automatic connection.** Probability describes the output frequency of a particular prepared circuit. Correctness describes whether that output satisfies the original problem. The Born rule converts amplitudes into probabilities; it does not check scheduling rules or favour good answers by itself.

**Algorithm goal.** We want to create a connection between the two: use the known cost function to search for a circuit that generates useful answers more often. Initially, standard QAOA gives every bitstring equal probability, including invalid and poor candidates. The cost step writes cost information into phases; the mixer lets phases affect probabilities; the classical optimiser searches angles using cost feedback. This is an attempt to improve the output distribution, not a guarantee that probability will rank candidates by correctness or cost.

We do not need to know the optimum beforehand to provide this feedback. Given a sampled candidate, we can calculate its cost with the formula we already built, even while finding the best candidate remains difficult. The optimiser uses many such evaluations to guide its parameter search.

In the [two-qubit visual in chapter 11](#qaoa-register-lab), the four costs stay fixed at 1, −1, 4 and 6. The low-cost angle preset gives 50% probability to 00 and 50% to the optimum 01. Thus even that better distribution sometimes returns a worse candidate. The high-cost preset gives probability only to 10 and 11, so the optimum never appears in that ideal distribution. The same problem can therefore have useful or useless sampling probabilities depending on the circuit parameters. This is an invented algebra example, not a scheduling feasibility instance.

For scheduling, decode and test every proposed answer against the original rules. In our pure-feasibility model, zero total penalty identifies a feasible candidate; a positive penalty signals a violation. If we also optimise an objective, compare that objective among feasible candidates. Frequent appearance is not a substitute for either check. **The circuit controls how often an answer is proposed; the problem's rules determine whether it is acceptable.**

### Start here · What do we want from the quantum computer?

We already know the classical problem: choose a bitstring $x$, decode its decisions, and evaluate its cost $E(x)$. A low cost is desirable. The quantum part is a way to **generate candidate bitstrings**. It does not change their meaning, replace the scheduling rules, or automatically certify an optimum.

In the logical model used here, one qubit corresponds to each QUBO bit. At the end of a circuit, we **measure** the qubits in the ordinary 0/1 basis: one run produces **one ordinary bitstring**. Decode it with the same lookup table and check the same scheduling rules as before. Amplitudes, introduced below, are not extra start times or another encoding to decode.

A **circuit** is an ordered sequence of quantum operations called **gates**. We prepare the starting state, apply the gates, and measure. Repeating that preparation and circuit gives more samples. Measuring the already-measured state again without preparing it afresh is a different experiment.

**Physical postulate — ideal projective measurement, given here.** After standard-basis measurement yields $x$, the register is in state $|x\rangle$. Immediately repeating the same ideal measurement, without an intervening gate or noise, gives $x$ again. This is why obtaining new circuit samples requires preparing and running the circuit afresh. More general measurement models and interpretations of measurement are outside the present circuit model.

First we will explain one qubit. This is a deliberately small mechanism demonstration, **not a scheduling instance**. We then extend the description to all $N$ bits and connect it to $E(x)$.

### One qubit · The state and the measurement result are different things

A qubit is a quantum system whose standard measurement has two possible results: 0 and 1. We can prepare it so one result is certain, or so each has some probability. Its **quantum state** is the description used to predict those results and how gates will change them.

| Notation | Read it as | Meaning |
|---|---|---|
| $|0\rangle$ | “ket zero” | The state that gives 0 with certainty in this measurement basis. |
| $|1\rangle$ | “ket one” | The state that gives 1 with certainty. |
| $|\psi\rangle$ | “ket psi” | A name for the whole current state. Psi is a Greek letter used as a label. |

The line and angle bracket name a state vector; they are not absolute-value bars or an inequality. In particular, $|0\rangle$ is not the number zero to multiply away.

**Definition / convention.** The ket symbols and the order of vector coordinates are notation choices. The reference states correspond to the readout basis we have chosen; their names are not a new physical law.

### Amplitudes · Numbers used to calculate probabilities

For one qubit, list two numbers in order: the **amplitude for outcome 0**, then the **amplitude for outcome 1**. Name them $\alpha_0$ and $\alpha_1$. Alpha is a Greek letter; its subscript identifies the outcome. This ordered list is the **state vector**. Its entries are amplitudes, not the output bits and not the probabilities themselves.

**Physical postulate — pure-state description, given here.** The ideal state model uses normalised complex vectors and linear quantum evolution. We accept that physical framework rather than deriving why nature uses it. Writing its components and applying stated gates are mathematical steps we do explain. Real amplitudes below are a restricted example inside this general complex model.

Begin with **real** amplitudes, which may be positive, negative or zero. For real amplitudes, the rule is

$$
\Pr(0)=\alpha_0^2,\qquad \Pr(1)=\alpha_1^2.
$$

The symbol $\Pr(0)$ means “probability of measuring 0.” A probability of 1 means 100%; $1/2$ means 50%. General amplitudes can be complex; we will explain the corresponding squared-magnitude rule after this real-number example.

| Amplitudes (for 0, for 1) | Probability of 0 | Probability of 1 |
|---|---|---|
| $(1,0)$ | $1^2=1$: 100% | $0^2=0$: 0% |
| $(0,1)$ | $0^2=0$: 0% | $1^2=1$: 100% |
| $(1/\sqrt2,1/\sqrt2)$ | $(1/\sqrt2)^2=1/2$: 50% | $(1/\sqrt2)^2=1/2$: 50% |
| $(1/\sqrt2,-1/\sqrt2)$ | $(1/\sqrt2)^2=1/2$: 50% | $(-1/\sqrt2)^2=1/2$: 50% |

Why $1/\sqrt2$, rather than $1/2$? Probabilities must add to 1. For two equal amplitudes of magnitude $a$, require $a^2+a^2=1$. Therefore $2a^2=1$, then $a^2=1/2$, so choose $a=1/\sqrt2\approx0.707$. Two amplitudes of $1/2$ would give probabilities $1/4+1/4=1/2$, which does not account for all possible outcomes. A state whose probabilities add to 1 is called **normalised**.

**Derivation.** The Born rule supplies the squared amplitudes as probabilities. The probability axiom that all mutually exclusive, exhaustive outcomes have total probability 1 then gives the normalisation condition. The calculation of $1/\sqrt2$ is a consequence of those rules, not a separate quantum law.

We also write the state as $|\psi\rangle=\alpha_0|0\rangle+\alpha_1|1\rangle$: this assigns an amplitude to each reference state. When both amplitudes are nonzero, we call this a **superposition** of those basis states. One measurement still gives only one outcome.

### Why keep a sign if squaring removes it?

The last two rows give the same immediate measurement probabilities. They are nevertheless different states: a later gate can **add and subtract amplitudes before we calculate probabilities**. Opposite contributions can cancel; contributions with the same sign can add. That is **interference**.

A list of probabilities alone therefore misses information needed to predict later gates. The sign difference here is a **relative phase difference**. A sign reversal is a half-turn of one amplitude's direction. The general idea permits other directions too; that is where complex numbers enter later in this chapter.

### Example · One gate at a time

We use two standard gates. Their names label their transformation rules. This example demonstrates interference; it does not search for a schedule or choose a QUBO optimum.

**Definition / algorithm choice.** We choose the Hadamard and Z gates to make the effect of a sign visible with simple arithmetic. Their specified rules define these particular operations; the laws of physics do not require every circuit to contain them. Why these gates here? The first creates two nonzero amplitudes; Z changes their relative sign; the second lets that sign affect the result. Implementing the gates with physical control pulses is outside scope.

The **Hadamard gate** combines two incoming amplitudes using this rule:

$$
\text{new amplitude for 0}=\frac{\alpha_0+\alpha_1}{\sqrt2},\qquad
\text{new amplitude for 1}=\frac{\alpha_0-\alpha_1}{\sqrt2}.
$$

We write this gate as $H_{\mathrm{Had}}$ in equations. “Had” identifies the gate and distinguishes it from the tested scheduling deadline $H$. Circuit diagrams conventionally label the gate simply H; the visual below explicitly says “Hadamard H.” A gate changes the state; it is not a measurement.

**Step 1: prepare a definite 0.** The amplitudes are $(1,0)$. Measuring now would give 0 with certainty. Instead, we apply gates first.

**Step 2: apply the Hadamard gate.** Substitute the incoming amplitudes into its rule:

$$
\alpha_0'=\frac{1+0}{\sqrt2}=\frac1{\sqrt2},\qquad
\alpha_1'=\frac{1-0}{\sqrt2}=\frac1{\sqrt2}.
$$

A prime, as in $\alpha_0'$, means the updated value after this operation, not a derivative. Measuring here would give 50% for each result. **We do not actually measure between these gates.** At each stage, we calculate what a measurement would produce if we stopped there.

**Step 3: reverse the sign of the amplitude for 1.** The gate called $Z$ leaves the amplitude for 0 unchanged and multiplies the amplitude for 1 by $-1$. The pair becomes $(1/\sqrt2,-1/\sqrt2)$. Both probabilities remain 50%, because squaring removes that sign. The state changed, although these immediate measurement probabilities did not.

**Step 4: apply the same Hadamard gate again.** Its rule remains sum for output 0, difference for output 1, both divided by $\sqrt2$. The amplitude for 0 becomes

$$
\frac{1/\sqrt2+(-1/\sqrt2)}{\sqrt2}
=\frac0{\sqrt2}=0.
$$

The opposite contributions cancel. For outcome 1, subtracting the negative adds the contributions:

$$
\frac{1/\sqrt2-(-1/\sqrt2)}{\sqrt2}
=\frac{2/\sqrt2}{\sqrt2}
=\frac2{\sqrt2\sqrt2}
=\frac22=1.
$$

The final amplitudes are $(0,1)$. Squaring gives probabilities 0 and 1: measurement now gives **1 with certainty** in this ideal example.

**Comparison: omit the sign change.** The second Hadamard then receives $(1/\sqrt2,1/\sqrt2)$. For output 0, its sum gives $(2/\sqrt2)/\sqrt2=1$. For output 1, its difference gives $(1/\sqrt2-1/\sqrt2)/\sqrt2=0$. The final amplitudes are $(1,0)$, so measurement gives **0 with certainty**. Thus two states that looked identical under an immediate 50/50 measurement lead to different later outcomes.

<div id="quantum-basics-lab" class="lab" aria-label="One-qubit amplitude and probability walkthrough"><p>The four stages and all calculations are given above. With JavaScript enabled, step through the same amplitudes and probabilities here. No measurement occurs between the gates.</p></div>

<aside class="takeaway">Gates combine amplitudes. Measurement probabilities come from their squared magnitudes. A phase change can leave probabilities unchanged now and still change what happens after a later gate.</aside>

<details class="solution"><summary>Check your understanding · If the sign-change stage is still 50/50, can we delete it without consequence?</summary>

No. The sign-change stage leaves those immediate measurement probabilities unchanged, but changes an amplitude's sign. The next gate combines amplitudes, so it can distinguish the two states. In this particular ideal example, including the sign change produces final outcome 1 with certainty; omitting it produces final outcome 0 with certainty. Neither path measures in the middle.

</details>

### A quantum state is a vector of amplitudes

We can now state the general form precisely. The two **basis states** are the reference states associated with the measurement outcomes. Their vectors are $|0\rangle=(1,0)^\mathsf T$ and $|1\rangle=(0,1)^\mathsf T$. The superscript $\mathsf T$ means transpose: display these entries as a column. A general pure state is

$$
|\psi\rangle=\alpha_0|0\rangle+\alpha_1|1\rangle,
\qquad |\alpha_0|^2+|\alpha_1|^2=1.
$$

The amplitudes $\alpha_0,\alpha_1$ are complex numbers. A complex number has the form $a+\mathrm i b$, where $\mathrm i^2=-1$, and squared magnitude $|a+\mathrm i b|^2=a^2+b^2$. The upright $\mathrm i$ here is the imaginary unit, not a bit index.

Picture $a+\mathrm i b$ as an arrow in a plane: $a$ is its horizontal component and $b$ its vertical component. Its length is $\sqrt{a^2+b^2}$; the squared length $a^2+b^2$ gives the probability. Its direction is its phase. These arrows represent amplitudes in a mathematical plane, not physical directions of the qubit in the room. For example, $\mathrm i/\sqrt2$ has horizontal component 0 and vertical component $1/\sqrt2$, so its squared length is $0^2+(1/\sqrt2)^2=1/2$, just like $1/\sqrt2$. Relative direction can still matter when arrows are combined.

<div id="amplitude-arrow-lab" class="lab" aria-label="Complex amplitude arrows and measurement probabilities"><p>Visualise two amplitudes as arrows in the complex plane. Changing their relative phase alone preserves their lengths and probabilities. The circle marks length 1; these are mathematical amplitude arrows, not physical directions. The state is chosen for teaching, not a scheduling instance.</p></div>

The complex conjugate of $a+\mathrm i b$ is $a-\mathrm i b$. A conjugate transpose turns a column into a row and conjugates its entries. “Pure state” means a state described by one such normalised vector; a statistical mixture of states is a more general description that is not needed for the ideal circuits derived here.

Measuring in this basis returns 0 with probability $|\alpha_0|^2$ and 1 with probability $|\alpha_1|^2$. It returns one outcome, not the full vector of amplitudes.

### The Bloch sphere · Where do the complex numbers appear? {#bloch-intuition}

**Intuition first.** The two amplitudes describe how the state contributes to two possible outcomes. Their lengths determine immediate 0/1 probabilities. Their relative direction determines how those contributions can add or cancel after further operations. Complex numbers record both pieces of information. A real number is also a complex number with imaginary part zero; our earlier positive/negative examples explored only a restricted slice of this richer picture.

The **Bloch sphere** gives a different view of the *whole single-qubit pure state*. The two small complex planes show its two individual coefficients. One sphere point shows their joint physical state, ignoring a common phase that has no observable effect. The sphere's arrow is neither an individual amplitude nor the qubit's position in physical space.

**Representation and mathematical identity.** After removing any common phase, every normalised pure qubit can be written using two real angles:

$$
|\psi\rangle=\cos(\theta/2)|0\rangle+(\cos\varphi+\mathrm i\sin\varphi)\sin(\theta/2)|1\rangle,
\qquad 0\le\theta\le\pi,\quad 0\le\varphi<2\pi.
$$

Here $\theta$ is the tilt down from the north pole; $\varphi$ goes around the vertical axis. Radians $\pi/2$ and $\pi$ mean 90° and 180°. Why this form? The first amplitude can be chosen real and nonnegative by rotating both amplitudes by the same phase. Its length and the second amplitude's length must have squared sum 1, so write them as $\cos(\theta/2)$ and $\sin(\theta/2)$. A complex number of the second length can point in direction $\varphi$, giving the real component $\cos\varphi$ and imaginary component $\sin\varphi$. The trigonometric identity $\cos^2 u+\sin^2 u=1$ verifies normalisation. The half-angle makes north correspond to definite 0 and south to definite 1.

**Chosen example, with an actual imaginary part.** Set $\theta=90°$ and $\varphi=45°$. Then

$$
\alpha_0=1/\sqrt2,\qquad
\alpha_1=(1/\sqrt2+\mathrm i/\sqrt2)/\sqrt2=(1+\mathrm i)/2.
$$

The second amplitude is $0.5+0.5\mathrm i$. Its squared magnitude is $0.5^2+0.5^2=0.5$, so outcome 1 has probability 50%. The other squared magnitude is also $1/2$. Changing $\varphi$ rotates the point around the sphere at the same height: both immediate 0/1 probabilities stay fixed, while the state can respond differently to later gates.

<div id="bloch-sphere-lab" class="lab" aria-label="Bloch sphere connected to complex amplitudes and measurement settings"><p>The initial example has amplitudes 1/√2 and (1+i)/2, giving 50% each for 0 and 1. The sphere places definite 0 at its north pole and definite 1 at its south pole. The +X state has amplitudes (1,1)/√2; the +Y state has amplitudes (1,i)/√2. Both are 50/50 under ordinary 0/1 readout, but subsequent gates can distinguish their relative phases.</p></div>

### How can a phase become observable? Change the measurement setting

Ordinary 0/1 readout is called **Z measurement**. To test another aspect of the state, first apply chosen gates and then use that same hardware readout. This is a different experiment on a freshly prepared state, not an extra simultaneous result from the first experiment.

For **X measurement**, apply the Hadamard gate before readout. Its output-0 amplitude is $(\alpha_0+\alpha_1)/\sqrt2$, so the probability of that result is $|\alpha_0+\alpha_1|^2/2$. In this setting we label that result +1. The other result is labelled −1. For **Y measurement**, first multiply only the amplitude for 1 by $-\mathrm i$, then apply Hadamard. Substitute the updated amplitude $-\mathrm i\alpha_1$ into the same sum rule: the +1 probability is $|\alpha_0-\mathrm i\alpha_1|^2/2$. These gate sequences define the measurement settings used in the visual.

**Compare two chosen states.** For $(|0\rangle+|1\rangle)/\sqrt2$, the X-setting sum gives $(1/\sqrt2+1/\sqrt2)/\sqrt2=1$, hence +1 with certainty. For $(|0\rangle+\mathrm i|1\rangle)/\sqrt2$, the X-setting amplitude is $(1+\mathrm i)/2$, whose squared magnitude is $1/4+1/4=1/2$. Both were 50/50 under Z readout, yet the X experiment distinguishes them statistically. This is why phase records usable information beyond ordinary 0/1 probabilities.

For a pure qubit the sphere coordinates are

$$
(r_X,r_Y,r_Z)=(\sin\theta\cos\varphi,\sin\theta\sin\varphi,\cos\theta).
$$

Each coordinate is the difference between the probabilities of +1 and −1 for that axis's measurement. For example, $r_Z=P(0)-P(1)$. Since those probabilities add to 1, solving their sum and difference gives $P(0)=(1+r_Z)/2$. Thus height determines the ordinary readout probability. $r_Z$ can be anywhere between −1 and +1; it is an **average**, whereas each individual Z result is +1 or −1. The coordinate identity follows by substituting the amplitudes above into the three measurement rules. The sphere does not replace the original amplitudes with three classical bits.

**What is given, and what is explained here?** The pure-state model and Born rule are physical starting postulates; the sphere is a mathematical representation of them, not a derivation of why nature obeys quantum mechanics. Removing global phase is valid because multiplying every amplitude by the same unit-magnitude number leaves all measurement predictions unchanged, including after later linear gates. Try multiplying both amplitudes by $\mathrm i$ in the visual: both complex arrows rotate, but the sphere point stays fixed. At a pole only one amplitude is nonzero, so the other phase direction has no physical significance. One sphere cannot represent a general entangled multi-qubit state; the joint-register representation comes next. [IBM's Bloch-sphere treatment](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/bloch-sphere) develops the same geometry and its extension to mixed states.

### Why several qubits? We need a complete proposed answer

One scheduling bit answers one yes/no question. If the model has $N$ bits, one proposed answer is the whole string $x=(x_1,\ldots,x_N)$. We therefore use a register of $N$ logical qubits and measure the full register to obtain an $N$-bit candidate. A **register** just means the group of qubits we treat as one computing system.

“Combining qubits” first means describing that joint system. It does not mean adding their 0/1 results together, replacing many qubits by one, or automatically entangling them. The joint description is necessary because constraints and costs can depend on which choices occur **together**. For example, the QUBO product $x_i x_j$ distinguishes both bits being 1 from other joint assignments.

### Two qubits · What does a basis vector actually look like?

Two measured bits have four possible complete outcomes: 00, 01, 10 and 11. In quantum notation, $|01\rangle$ names the joint reference state with first qubit 0 and second qubit 1. The contents of the ket now specify **both qubits**, rather than just one. There is no new measurement rule; the outcome label is simply longer.

### A bit value is not an amplitude coordinate {#outcome-labels-and-coordinates}

This distinction is easy to miss because both are written using numbers. In the classical record $(0,0)$, the two entries say **what the two bits are**. In a quantum state vector, entries say **the amplitudes for the possible complete outcomes**. They answer a different question.

| Object | What its entries mean | Number of entries |
|---|---|---:|
| Classical two-bit result $(0,0)$ | First bit is 0; second bit is 0. | 2 bit values |
| One-qubit amplitude vector $(\alpha_0,\alpha_1)^\mathsf T$ | Amplitude for outcome 0; amplitude for outcome 1. | 2 complex coefficients |
| Two-qubit amplitude vector $(\alpha_{00},\alpha_{01},\alpha_{10},\alpha_{11})^\mathsf T$ | Amplitudes for the four complete outcomes 00, 01, 10, 11. | 4 complex coefficients |

For one qubit, $|0\rangle=(1,0)^\mathsf T$ already uses this rule: the 1 is in the slot **labelled 0**. It means that outcome has probability $|1|^2=1$. It does not say that the bit equals 1. For two qubits, definite outcome 00 likewise has amplitude 1 in the **00 slot**, and zero in the other three slots.

**Yes: these vector entries are the amplitudes.** They remain complex numbers even when written as 0 or 1: $0=0+0\mathrm i$ and $1=1+0\mathrm i$. A complex number does not need a nonzero imaginary part. In a general state, those same slots can instead contain values such as $(1+\mathrm i)/2$; its probability is its squared magnitude, $1/4+1/4=1/2$. All slots' squared magnitudes must sum to 1.

We can absolutely write $(0,0)$ as the classical result of measuring two qubits. We cannot use that same pair as their quantum amplitude vector: it has too few entries for the general joint state. Even as a *one*-qubit amplitude vector, $(0,0)^\mathsf T$ is invalid because its outcome probabilities would sum to zero. The all-zero amplitude vector is not the definite-zero state.

**What is convention, and what is a physical starting rule?** We choose the coordinate order and names. The rule that a composite quantum system uses a tensor-product state space is a physical postulate of the model. Two two-dimensional qubit spaces combine into a four-dimensional space. This also allows four mutually orthogonal states corresponding to four perfectly distinguishable complete outcomes. The four dimensions are not an arbitrary extra convenience introduced by this guide. The tensor-product rule is developed more fully below.

### Build the four entries from the familiar two-entry vectors

For separate pure qubits with amplitudes $(a,b)^\mathsf T$ and $(c,d)^\mathsf T$, the tensor product, written $\otimes$, forms all four pair combinations:

$$
\begin{pmatrix}a\\b\end{pmatrix}\otimes\begin{pmatrix}c\\d\end{pmatrix}
=\begin{pmatrix}ac\\ad\\bc\\bd\end{pmatrix}.
$$

The slots are 00, 01, 10, 11: first choose each qubit's 0 coefficient, then first-0/second-1, then first-1/second-0, then both 1 coefficients. For two definite zeros, substitute the familiar $|0\rangle=(1,0)^\mathsf T$ for **each** qubit:

$$
|00\rangle=|0\rangle\otimes|0\rangle
=\begin{pmatrix}1\cdot1\\1\cdot0\\0\cdot1\\0\cdot0\end{pmatrix}
=\begin{pmatrix}1\\0\\0\\0\end{pmatrix}.
$$

Thus we are using exactly the one-qubit vectors you already know, and **combining** them. We are not concatenating their entries: concatenation would give $(1,0,1,0)^\mathsf T$, whose squared amplitudes sum to 2 and which is not this state. For $|01\rangle$, substitute $(c,d)=(0,1)$ instead: the four products are $1\cdot0$, $1\cdot1$, $0\cdot0$, $0\cdot1$, giving $(0,1,0,0)^\mathsf T$.

This product construction describes separate pure qubit states. A general joint state may be **entangled** and may not factor into two separate two-entry vectors; that is why keeping only one amplitude pair per qubit is insufficient in general. We return to a concrete example after building the joint vector.

Choose the bookkeeping order 00, 01, 10, 11. Each outcome has one coordinate slot. The corresponding **basis vectors** are

$$
|00\rangle=\begin{pmatrix}1\\0\\0\\0\end{pmatrix},\quad
|01\rangle=\begin{pmatrix}0\\1\\0\\0\end{pmatrix},\quad
|10\rangle=\begin{pmatrix}0\\0\\1\\0\end{pmatrix},\quad
|11\rangle=\begin{pmatrix}0\\0\\0\\1\end{pmatrix}.
$$

The single 1 marks which coordinate names that outcome. **Definition / convention:** these are unit coordinate vectors. Their shapes follow from the selected coordinate order, rather than from four new physical assumptions. These four-entry vectors describe **two physical qubits**; they do not require four qubits. The vector $|01\rangle$, for example, has amplitude 1 for the complete outcome 01 and amplitude 0 for the other outcomes. Measurement therefore gives 01 with certainty.

A general joint pure state is a **weighted sum** of those basis vectors:

$$
|\psi\rangle=
\alpha_{00}|00\rangle+\alpha_{01}|01\rangle+
\alpha_{10}|10\rangle+\alpha_{11}|11\rangle
=\begin{pmatrix}\alpha_{00}\\\alpha_{01}\\\alpha_{10}\\\alpha_{11}\end{pmatrix}.
$$

Read a term such as $\alpha_{01}|01\rangle$ literally as scalar multiplication of a vector:

$$
\alpha_{01}\begin{pmatrix}0\\1\\0\\0\end{pmatrix}
=\begin{pmatrix}0\\\alpha_{01}\\0\\0\end{pmatrix}.
$$

Adding the four terms places each amplitude in its labelled slot. The basis vector identifies the outcome; its coefficient supplies the amplitude. The ket itself is not a probability.

The coefficients are **not all assumed equal**, and some may be zero. The state $|\psi\rangle$ is one particular weighted combination, determined by preparation and the gates applied so far. The collection of all such normalised combinations is the collection of possible pure states; one $|\psi\rangle$ does not mean all those different states at once.

### Example · A state with only two nonzero amplitudes

This is an invented two-qubit state for teaching the notation, not a scheduling instance:

$$
|\psi\rangle=\frac{\sqrt3}{2}|01\rangle+\frac12|10\rangle
=\begin{pmatrix}0\\\sqrt3/2\\1/2\\0\end{pmatrix}.
$$

The omitted 00 and 11 terms have coefficient zero. The four measurement probabilities are

| Complete outcome | Amplitude | Squared magnitude: probability |
|---|---|---|
| 00 | $0$ | $0$: 0% |
| 01 | $\sqrt3/2$ | $(\sqrt3/2)^2=3/4$: 75% |
| 10 | $1/2$ | $(1/2)^2=1/4$: 25% |
| 11 | $0$ | $0$: 0% |

They add to $0+3/4+1/4+0=1$. One measurement produces either 01 or 10, with those probabilities. It does not return the four amplitudes or both answers.

The order 00, 01, 10, 11 is a coordinate convention. We could use another order if we changed every vector and gate matrix consistently. Physical predictions do not depend on which coordinate we write first. As with flattening the scheduling variables, a consistent lookup prevents us from attaching a number to the wrong label.

<div id="register-explorer-lab" class="lab" aria-label="Joint quantum register and basis-vector explorer"><p>The outcome order labels the coordinates. A selected basis vector has one amplitude 1; a general state has one amplitude per complete outcome. The preceding explicit two-qubit vectors and probability table remain the noninteractive explanation.</p></div>

### General case · Unpack the compact sum

For $N$ qubits there are $N$ measured positions, each with two possible values. Counting complete strings gives $2\times2\times\cdots\times2=2^N$ possibilities. There are 2 possibilities for one qubit, 4 for two, 8 for three, and so on.

The mathematical description assigns **one complex amplitude per complete outcome**, so the pure-state vector has $2^N$ complex entries. This does not say that every possible state needs a different vector slot: there are infinitely many normalised state vectors. The $2^N$ slots label the basis outcomes we use to describe any one of them. Nor does it mean that the hardware contains $2^N$ qubits or lets us read out $2^N$ answers. A classical exact statevector simulator stores those amplitudes explicitly; measurement of the quantum register gives one string.

Now write the same weighted-sum idea compactly:

$$
|\psi\rangle=\sum_{x\in\{0,1\}^N}\alpha_x|x\rangle,
\qquad\sum_x|\alpha_x|^2=1.
$$

| Part | Meaning |
|---|---|
| $x$ | One complete $N$-bit string, such as 010. It is not one bit or a numeric sum of 0 and 1. |
| $\{0,1\}^N$ | The set of all strings of length $N$ made from 0 and 1. |
| $|x\rangle$ | The basis vector labelled by that entire string. For $N=1$, these are exactly $|0\rangle$ and $|1\rangle$ again. |
| $\alpha_x$ | The complex coefficient belonging to that basis vector. Its subscript is a label, not multiplication by $x$. |
| $\sum_x\alpha_x|x\rangle$ | Add all the weighted basis vectors. Zero coefficients contribute zero. |
| $\sum_x|\alpha_x|^2=1$ | Add the probabilities of **all** mutually exclusive complete outcomes; the total is 100%. |

The last equation does **not** say that every $|\alpha_x|^2$ equals 1. In the invented example, two probabilities were 3/4 and 1/4, and the others were zero. It is their **sum** that equals 1. The symbol $x$ is the outcome label; it does not combine the kets by itself. The sum sign performs the addition.

<aside class="takeaway">One basis vector names one definite complete outcome. One state vector specifies amplitudes for those outcomes. One measurement returns one outcome. The cost function then scores that returned candidate.</aside>

### When do we use the tensor product? It describes the joint system {#tensor-product-timing}

**Your overall picture is correct: gates change the joint state's $2^N$ amplitudes.** The tensor product tells us how to describe the system made of $N$ qubits, and how separately prepared states fit into that joint description. It is not a new optimisation step or a gate called “combine.”

| Point in standard QAOA | Physical action | Where tensor notation appears |
|---|---|---|
| Start with $N$ qubits in definite 0 | Prepare/reset the qubits. | Their joint state is $|0\rangle\otimes\cdots\otimes|0\rangle=|00\cdots0\rangle$. It already has $2^N$ amplitude slots: one 1, all others zero. |
| Prepare the uniform starting state | Apply a Hadamard gate to each qubit. | Each separate state becomes $|+\rangle$, so the joint state is $|+\rangle^{\otimes N}$. Expanding it gives the equal-amplitude vector. |
| Run cost and mixer gates | Change the joint state through the circuit. | We still use the same $2^N$-dimensional joint space. The state may become entangled and cease to factor into one state per qubit. |
| Read out a candidate | Measure all $N$ qubits in the computational basis. | One measurement returns one $N$-bit string, not the $2^N$ amplitudes. Reprepare and rerun for another sample. |

For example, starting with $|00\rangle$ and applying Hadamard to **only the first qubit** produces $(|00\rangle+|10\rangle)/\sqrt2$: its joint amplitude vector becomes $(1/\sqrt2,0,1/\sqrt2,0)^\mathsf T$. Applying Hadamard to the second qubit too produces four equal amplitudes $1/2$. These are actual gates changing amplitudes; writing the tensor product is the mathematics that describes their joint effect.

Keep the three sizes distinct: **$N$ logical qubits, $2^N$ complex amplitude coordinates in the pure-state description, and $N$ ordinary bits in one measured candidate.** A state vector is not itself an $N$-bit candidate. The device does not give us a classical list of amplitudes to edit independently. We apply implementable gates, whose structured action changes the joint amplitudes.

**Physical postulate — composition of systems, given here.** Standard quantum theory represents the joint state space of separate systems using the tensor product of their state spaces. We accept that composition rule; counting bitstrings alone is not a derivation of the physical postulate. Once the rule is accepted, multiplying coordinate dimensions gives $2^N$, and the explicit component calculations below are ordinary algebra. [IBM’s joint-system treatment](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/multiple-systems/quantum-information) develops this framework.

The symbol $\otimes$, read “tensor product,” describes the joint state of systems prepared in separate states. It is the mathematical rule for forming the joint description, not a physical command to merge the qubits. For example, $|0\rangle\otimes|1\rangle=|01\rangle$. The one-qubit plus state and the all-plus product state are

$$
|+\rangle=\frac{|0\rangle+|1\rangle}{\sqrt2},\qquad
|+\rangle^{\otimes N}=\frac1{\sqrt{2^N}}\sum_x|x\rangle.
$$

For two qubits, distributing the tensor product gives the four terms $(|00\rangle+|01\rangle+|10\rangle+|11\rangle)/2$. Each coefficient is $(1/\sqrt2)(1/\sqrt2)=1/2$, whose square is $1/4$. With $N$ qubits, each basis term picks one coefficient $1/\sqrt2$ from each factor, so its amplitude is $(1/\sqrt2)^N=1/\sqrt{2^N}$ and its probability is $1/2^N$. This accounts for all $2^N$ basis bitstrings and their probabilities sum to 1.

Measuring the all-plus state therefore samples every bitstring equally. A superposition is not just a classical random choice: its amplitudes have relative phases that can affect later outcomes.

Not every multi-qubit pure state is a product of separate one-qubit states. Such a state is **entangled**. For example, $(|00\rangle+|11\rangle)/\sqrt2$ has nonzero amplitudes for 00 and 11, and zero amplitudes for 01 and 10. If it were a product, the nonzero amplitudes for 00 and 11 would require both entries of both one-qubit vectors to be nonzero. Their products for 01 and 10 would then also be nonzero, a contradiction. This proves that this state is not a product. Its standard measurements give 00 or 11 with equal probability. A classical random process could produce those same correlated results; entanglement concerns the quantum state, not merely that one measurement distribution.

### What information belongs to one qubit across all the bitstrings? {#individual-qubit-information}

**Its identity stays fixed.** Qubit position 1 represents the same decision $x_1$ in every candidate. The operation/time meaning of that decision is stored in our classical encoding lookup; the qubit does not itself know the scheduling interpretation. Different basis strings specify different possible values at that same position.

**Its amplitudes need not be independent of the rest.** In a product state, separate one-qubit amplitude pairs are enough: multiplying their entries produces the joint amplitudes, as above. For an entangled pure state, no such collection of independent pairs reproduces the joint vector. We still have one joint amplitude per complete bitstring, rather than one amplitude attached to a qubit regardless of the others.

For two qubits, first-qubit value 0 occurs in complete outcomes 00 and 01. First-qubit value 1 occurs in 10 and 11. Therefore

$$
P(x_1=0)=|\alpha_{00}|^2+|\alpha_{01}|^2,\qquad
P(x_1=1)=|\alpha_{10}|^2+|\alpha_{11}|^2.
$$

Add **probabilities** here: we are grouping distinct complete readout outcomes, not coherently combining them with a gate. Knowing these two numbers does not recover the whole joint state. For example, the all-plus state gives all four outcomes with probability 1/4, while the entangled 00/11 state above gives only those two outcomes with probability 1/2 each. Both give each individual qubit a 50/50 readout, but their joint results differ.

**A local summary does exist.** The general mathematical description of one qubit considered by itself is its *reduced state*, usually written as a two-by-two density matrix. It predicts every measurement on that qubit alone, including phase-sensitive settings, but does not contain all its correlations with other qubits. Deriving and manipulating density matrices is outside this guide's pure-register circuit path. The relevant boundary is that a complete local summary need not be a pure-state amplitude pair, and local summaries do not generally determine the full joint state.

**A local gate shares one rule across all configurations of the other qubits.** Apply Hadamard to the first qubit. For second-qubit value 0, its sum/difference rule acts on the pair $\alpha_{00},\alpha_{10}$. For second-qubit value 1, exactly the same rule acts on $\alpha_{01},\alpha_{11}$:

$$
\begin{aligned}
\alpha'_{00}&=(\alpha_{00}+\alpha_{10})/\sqrt2,\\
\alpha'_{10}&=(\alpha_{00}-\alpha_{10})/\sqrt2,\\
\alpha'_{01}&=(\alpha_{01}+\alpha_{11})/\sqrt2,\\
\alpha'_{11}&=(\alpha_{01}-\alpha_{11})/\sqrt2.
\end{aligned}
$$

The prime means the amplitude after this gate. We group by the other qubit's value because the gate leaves that qubit untouched. For $N$ qubits, a gate on position $i$ applies its same two-entry transformation to each of the $2^{N-1}$ amplitude pairs that differ only at bit $i$. This is how one local physical operation has a structured action on the joint amplitude vector. It does not let us independently set every joint amplitude.

### Phase matters only through later interference

**Mathematical result used — Euler’s identity.** The formula below relates complex exponentials to sine and cosine. We use it as an imported mathematical identity, not a law of scheduling or measurement. Its proof through power series is outside the core reading path. We do show why it preserves amplitude length and why changing relative phase can affect later interference.

A factor $e^{\mathrm i\theta}=\cos\theta+\mathrm i\sin\theta$ has magnitude one. Multiplying one amplitude by it changes its **phase** while preserving its probability at that instant. Multiplying every amplitude by the same phase is a global phase with no observable effect.

Here $\theta$ is an angle in **radians**: a full turn is $2\pi$, a half-turn is $\pi$, and a quarter-turn is $\pi/2$. On a circle of radius one, $\cos\theta$ is the horizontal coordinate and $\sin\theta$ the vertical coordinate at that angle. Pythagoras gives $\cos^2\theta+\sin^2\theta=1$, which is why $|e^{\mathrm i\theta}|^2$ is one. Squared sine and cosine mean the square of their values, not doubling the angle.

Two identities will be used in the later one-qubit calculation: $\cos^2\theta+\sin^2\theta=1$ and $\sin(2\theta)=2\sin\theta\cos\theta$. The first was just explained geometrically. For the second, combining two rotations adds their angles. Multiply their complex coordinates: $(\cos\theta+\mathrm i\sin\theta)^2=\cos^2\theta-\sin^2\theta+\mathrm i(2\sin\theta\cos\theta)$. This represents the point at angle $2\theta$, whose imaginary part is $\sin(2\theta)$, giving the second identity. We will identify where each is used rather than assume the final probability formula.

Relative phases can change probabilities after an operation combines amplitudes. For a small algebra illustration, $|+\rangle$ and $(|0\rangle-|1\rangle)/\sqrt2$ give the same 50/50 outcomes when measured immediately, but a Hadamard transform maps them to $|0\rangle$ and $|1\rangle$, respectively. The Hadamard matrix is $H_{\mathrm{Had}}=2^{-1/2}\begin{pmatrix}1&1\\1&-1\end{pmatrix}$; its rows implement the sum-and-difference rule already worked through above. The sum or cancellation of amplitudes is **interference**.

### Operators and the Pauli matrices

**Definition / convention.** An operator is a rule acting on state vectors; the matrices below define the particular named Pauli operators. Their actions are obtained by matrix multiplication. Choosing to use these operators for QAOA is an algorithm design decision.

A quantum operator is a linear transformation on statevectors. The Pauli matrices used here are

$$
X=\begin{pmatrix}0&1\\1&0\end{pmatrix},\quad
Y=\begin{pmatrix}0&-\mathrm i\\\mathrm i&0\end{pmatrix},\quad
Z=\begin{pmatrix}1&0\\0&-1\end{pmatrix}.
$$

$X$ swaps the two basis states. $Z$ changes the sign of $|1\rangle$. $Y$ swaps the states with phases. A subscript, such as $X_i$, means this operator acts on qubit $i$ and as identity on the others. The product $Z_iZ_j$ has eigenvalue $z_iz_j$ on $|x\rangle$.

**Physical postulate / model assumption — ideal closed-system evolution.** Between measurements, we model coherent, noiseless evolution of the isolated register by **unitary** operators. A unitary operator is a square matrix whose conjugate transpose is its inverse: applying it and then its inverse returns the starting vector. Such operators preserve vector length and therefore total squared amplitude and probability. This is a mathematical property of unitary matrices; using them for the closed, ideal system is the physical modelling rule. Measurement and noisy open-system processes need a more general description; this statement is not a claim that every physical process is unitary on the register alone. A Hermitian operator equals its conjugate transpose; its eigenvalues are real. A Hamiltonian is a Hermitian generator of coherent evolution. **Mathematical result used:** if $\widehat H$ is Hermitian and $\theta$ is real, $e^{-\mathrm i\theta\widehat H}$ is unitary. This follows by diagonalising the Hermitian matrix: its real eigenvalues acquire phase factors of magnitude one. The general diagonalisation theorem is outside scope; our diagonal cost operator makes the action explicit without that theorem’s full proof. For the diagonal cost Hamiltonian, the exponential simply multiplies each basis amplitude by $e^{-\mathrm i\theta E(x)}$. No general matrix-exponential calculation is needed to understand this action.

### Where the exponential gate form comes from

**Physical law — Schrödinger evolution, given here.** For a closed system with a time-independent physical Hamiltonian $\widehat H_{\mathrm{phys}}$, quantum mechanics gives evolution $U(t)=e^{-\mathrm i t\widehat H_{\mathrm{phys}}/\hbar}$. Here $t$ is physical elapsed time and $\hbar$ is the reduced Planck constant, a physical constant setting the scale. The differential equation and its general solution are outside this guide; [MIT’s time-evolution notes](https://ocw.mit.edu/courses/22-02-introduction-to-applied-nuclear-physics-spring-2012/b5106a499ae03e36b5a2e002355668f9_MIT22_02S12_lec_ch6.pdf) give that development.

**Algorithm choice / units convention.** QAOA uses gates with this mathematical form, generated by chosen cost and mixer operators. Scale factors are absorbed into adjustable angles such as $\gamma$ and $\beta$. These are circuit parameters, not scheduling start times. The programmed cost operator need not equal the device’s natural Hamiltonian; gates can be synthesised to implement its exponential. Hardware pulse synthesis is outside scope. The phase action of the resulting cost gate is inside scope and is shown in chapter 11.

### Expected energy is an average over outcomes {#expected-energy}

**Yes: standard QAOA usually trains its circuit angles to minimise this average.** Our final practical goal is to obtain a good valid candidate. The training loop needs a score for a *whole sampling distribution*, because one angle choice produces many possible answers. Expected energy is the usual choice of that training score. Here “energy” means the existing model cost $E(x)$, including any penalties; it is not electricity consumed by the computer.

Imagine fixing the angles, preparing and measuring that same circuit repeatedly, and calculating the cost of each returned string. The expected energy is the probability-weighted average cost for this fixed distribution. A finite batch gives an estimate: add its observed costs and divide by the number of samples. For example, costs 0, 2, 0 and 6 have average $(0+2+0+6)/4=2$, while their best observed cost is 0. The average does not need to equal the cost of any individual outcome.

The loop is: **choose angles → generate samples → score them → estimate their average cost → use that feedback to propose new angles**. The cost formula stays fixed. The angles change the state, its amplitudes and hence the distribution. After or during training, retain the best independently validated candidate seen. [IBM's QAOA walkthrough](https://quantum.cloud.ibm.com/docs/en/tutorials/quantum-approximate-optimization-algorithm) explicitly separates expectation-based parameter training from final sampling.

### Why optimise an average when we want the best answer?

The average is a **training objective** chosen to encourage cheap outcomes across the distribution. It can be estimated from sampled costs without knowing the optimum in advance. It gives the classical optimiser numerical feedback as it searches the circuit angles. This is a design choice; it is not the only possible training objective.

Your concern is real: **lowering the average does not always increase the chance of the very best outcome**. Consider this invented example, with three feasible candidates of costs 0, 2 and 10. Cost 0 is the optimum. These are illustrative distributions, not claims about what a particular QAOA circuit reaches.

| Outcome cost | Probability under distribution A | Probability under distribution B |
|---|---:|---:|
| 0, the optimum | 10% | 0% |
| 2 | 0% | 100% |
| 10 | 90% | 0% |

For A, the expected cost is $0.10\cdot0+0\cdot2+0.90\cdot10=9$. For B, it is $0\cdot0+1\cdot2+0\cdot10=2$. Mean-cost training prefers B, even though only A can generate the optimum. This explains why average cost, probability of reaching a target, and best cost observed in a fixed sample budget must be reported separately.

There is still a useful exact limiting statement. Every candidate cost is at least the global minimum. Therefore their probability-weighted average cannot lie below that minimum. If the average equals the global minimum exactly, all nonoptimal candidates must have probability zero: any positive weight on a larger cost would increase the average. Finite circuit families, finite parameter searches and finite sampling generally do not establish that ideal endpoint.

One alternative is **CVaR**, which trains using the average of only a chosen lowest-cost fraction of outcomes, rather than all outcomes. Chapter 11 defines it precisely. Directly using the best cost in a finite batch is also possible, but its value depends strongly on luck and batch size; repeated batches can return different minima for unchanged angles. Alternative training scores change what the optimiser favours and require their own evaluation. None automatically certifies the best possible schedule.

### The compact expression, after its meaning

**Derivation from probability.** Measuring gives candidate $x$ with probability $|\alpha_x|^2$, and that candidate has cost $E(x)$. An average cost therefore adds “probability times cost” over all candidates. The bra–operator–ket expression below is compact notation for that average in this diagonal case, not another physical postulate to memorise.

The bra $\langle\psi|$ is the conjugate transpose of $|\psi\rangle$. Because $\widehat H_C$ is diagonal,

$$
\langle\psi|\widehat H_C|\psi\rangle=\sum_x|\alpha_x|^2E(x).
$$

This is the probability-weighted mean energy. It is not necessarily the energy of the best sample or the probability of measuring an optimum. If the distribution includes many mediocre states and one rare excellent state, those statistics tell different stories.

<aside class="takeaway">The cost operator writes energy into phases. A mixer combines amplitudes so those phases can influence measurement probabilities. Neither step alone is a “choose the minimum” operation.</aside>

## 11 · QAOA as a complete algorithm {#qaoa}

The **quantum approximate optimisation algorithm** alternates a problem-dependent phase operation and a mixing operation, and uses a classical optimiser to choose their angles. Its original formulation is due to [Farhi, Goldstone and Gutmann](https://arxiv.org/abs/1411.4028). Here we use a minimisation convention throughout.

### First reading · What each part of QAOA is doing

The one-qubit walkthrough in chapter 10 used Hadamard → sign change → Hadamard to isolate interference. QAOA uses the same principle of phase followed by amplitude mixing, with **different gates chosen for the optimisation problem**. Its mixer is not simply the final Hadamard from that demonstration.

A **layer** means one cost step followed by one mixer step. There are $L$ layers. The subscript $\ell$ is a lowercase ell identifying a layer, from 1 through $L$. The Greek letters $\gamma$ (gamma) and $\beta$ (beta) name its two adjustable angles.

| Part | What we already know | What the quantum algorithm does |
|---|---|---|
| Candidate $x$ | A complete proposed assignment of the scheduling bits. | A measured circuit run produces one such bitstring. |
| Cost $E(x)$ | A fixed formula containing our penalties and, if present, objective. | The cost step changes each candidate amplitude's phase according to this number. It does not immediately change its probability. |
| Cost angle $\gamma_\ell$ | A real parameter for circuit layer $\ell$. | Controls the strength of that cost-dependent phase change. Gamma is not a processing time or a penalty weight. |
| Mixer angle $\beta_\ell$ | A second real parameter for that layer. | Controls how strongly the mixer combines amplitudes, so their phases can affect probabilities. |
| Classical optimiser | An ordinary algorithm searching over numerical parameters. | Proposes angles, receives measured cost estimates, and tries new angles. It does not replace our fixed scheduling data. |

At fixed angles, prepare the circuit afresh for each sample, measure bitstrings, calculate their original costs, and average them to estimate how that circuit performs. The classical optimiser uses that feedback to search for better angles. We can inspect individual good samples too; the average and the best sample are different statistics.

For example, if measured samples have costs 0, 2, 0 and 6, their sample mean is $(0+2+0+6)/4=2$. The best observed cost is 0. A low mean tends to favour low-cost samples, but it is not a certificate that every sample is feasible or that the optimum has been found.

The cost Hamiltonian $\widehat H_C$ is the operator that assigns our existing number $E(x)$ to basis state $|x\rangle$. Here “energy” is the mathematical score derived from the model; it is not the machine's running time or the electricity used by the processor. We implement gates derived from that operator. The formulas below specify their exact action.

### How does numerical feedback tell the optimiser what to change? {#using-cost-feedback}

**The cost is part of the algorithm in two places.** First, its known coefficients determine the quantum cost gates, so the circuit already contains problem-specific structure. Second, we evaluate that same cost on measured candidates to score how the current circuit performs. The scheduling modeller supplies the objective, but it is not arbitrary noise disconnected from the search. During training, the cost assigned to a particular bitstring stays fixed.

Separate the two functions involved. $E(x)$ scores **one candidate string**. For a one-layer circuit, define $J(\gamma,\beta)$ as the **expected cost produced by the chosen angles**:

$$
J(\gamma,\beta)=\sum_x p_{\gamma,\beta}(x)E(x).
$$

Here $p_{\gamma,\beta}(x)$ is the probability of measuring candidate $x$ after running the circuit with those angles. It is the squared magnitude of that circuit's amplitude for $x$. Changing angles changes the probability weights, not $E(x)$. Standard mean-cost training searches for low values of $J$. With $L$ layers, its input is all $2L$ angles instead of this one pair.

**One score alone does not tell us a direction.** The classical optimiser knows the angles it tried and the estimated score for each trial. It deliberately changes angles, compares the results, and uses those comparisons to choose further trials. It receives a relationship between settings and scores, not an unexplained number with no record of where it came from.

**Invented feedback example.** Hold $\gamma$ fixed and vary only $\beta$. Suppose sufficiently precise sample estimates give:

| Trial | Mixer angle $\beta$ in radians | Estimated mean cost |
|---|---:|---:|
| 1 | 0.20 | 6.0 |
| 2 | 0.30 | 4.0 |
| 3, proposed after comparing 1 and 2 | 0.40 | 4.5 |

These are chosen teaching numbers, not measured results from the guide's example circuit. From trials 1 and 2, increasing the angle by $0.30-0.20=0.10$ reduced the estimated cost by $4.0-6.0=-2.0$. The estimated local slope is therefore $-2.0/0.10=-20$: a negative sign suggests trying a larger angle. Trial 3 tests that suggestion. It is worse than trial 2, so the optimiser can keep trial 2 as its current best and investigate a smaller region around it. It does not assume that increasing the angle helps forever. Those three trials alone do not prove where even the local minimum lies.

This illustrates the information used by numerical optimisation. A **finite-difference** method estimates slopes from controlled parameter changes; gradient-based methods use slope estimates to propose updates. Other methods build local approximations from several trials without explicitly calculating a gradient. For example, [IBM's walkthrough](https://quantum.cloud.ibm.com/docs/en/tutorials/quantum-approximate-optimization-algorithm) uses the classical optimiser COBYLA. The choice of optimiser is another algorithm choice, not a quantum law. For many angles, it must explore their combined effects; optimising each independently once is generally insufficient.

**Why comparisons can be informative.** In the ideal circuit, gate entries vary smoothly with the angles. Consequently the joint amplitudes, probabilities and mean cost also vary smoothly, even though each sampled answer is a discrete bitstring. This gives angle changes a meaningful local trend to investigate. Smooth does not mean a single easy valley: there can be many local minima and nearly flat regions. Finite samples add statistical uncertainty, so a small difference between two sample means may be noise; more samples, repeated evaluations or uncertainty-aware decisions may be needed before trusting that direction.

We therefore have a structured quantum family of candidate distributions, derived from the cost, plus a classical numerical search over its controls. Feedback makes that search informed. It does not make it infallible, guarantee a global optimum, or establish that it beats classical optimisation of the original scheduling problem.

### Do we use the amplitudes, or just score the measured bitstrings? {#amplitudes-and-readout}

**Both have a role.** The quantum circuit evolves the amplitudes. Their squared magnitudes determine the candidate probabilities, while their relative phases affect what later gates do. We therefore care about amplitudes when designing and explaining the circuit. On quantum hardware, however, ordinary readout does not give the classical optimiser their full vector. It gives sampled bitstrings. A small classical state-vector simulator can expose amplitudes internally; that is a simulation facility, not the hardware's ordinary output.

For each trial angle setting, prepare and run a fresh circuit for each shot. Every shot returns one complete candidate. Calculate $E(x)$ for each, use the sample costs to estimate the training objective, and let the classical optimiser propose another angle setting. Changing those angles controls the amplitudes indirectly through gates; the optimiser does not edit an independent amplitude table.

At the same time, decode candidates, check the original scheduling rules, and retain the lowest-cost valid answer found, including good answers encountered during training if the reporting protocol allows it. The most frequent string need not have the lowest cost. The mean used to train the distribution and the best individual answer retained are separate records. The fixed classical cost model scores bitstrings; the quantum state carries amplitudes; the classical optimiser uses the measured feedback to search circuit controls. None of these components needs to infer the scheduling meaning by inspecting an amplitude.

### Why use the cost to change phases?

We cannot simply request “give every good solution high probability”: identifying those solutions is the search problem. We can, however, implement gates derived from the cost's known individual and pair terms. This uses the structure of the QUBO without first listing every candidate and finding its score. The cost step attaches different phases to candidates according to $E(x)$. At that instant their probabilities have not changed. The mixer then combines amplitudes so relative phases affect the next distribution. Repeating those operations gives a family of distributions, and the classical optimiser searches its angle parameters.

This is a proposed search mechanism, not a theorem that higher cost automatically cancels or that lower cost automatically adds. The angles and the whole problem determine the interference. For example, setting all angles to zero leaves standard QAOA's initial uniform distribution unchanged even when candidate costs differ. We must measure, score samples and compare performance; the presence of a quantum circuit alone establishes no advantage. The original [QAOA construction](https://arxiv.org/abs/1411.4028) and [IBM's implementation walkthrough](https://quantum.cloud.ibm.com/docs/en/tutorials/quantum-approximate-optimization-algorithm) make the circuit and classical feedback explicit.

<figure class="feedback-figure" aria-label="QAOA classical feedback loop"><figcaption>The search has a quantum circuit inside a classical feedback loop</figcaption><ol class="feedback-steps"><li><b>Choose angles</b><span>The classical optimiser proposes circuit parameters.</span></li><li><b>Run fresh circuits</b><span>Prepare → cost phases → mixing → measurement.</span></li><li><b>Score the samples</b><span>Decode bitstrings, check rules and calculate the fixed cost.</span></li><li><b>Use the feedback</b><span>Cost estimates guide the next angle proposal.</span></li></ol><p class="feedback-return">↶ New angles return to the circuit; the scheduling data and cost coefficients stay fixed.</p><p>After the angle search, collect a final batch and report validated candidates. This loop describes a heuristic search; it does not certify the optimum.</p></figure>

### The purpose of every step, before its formula

**Model assumption.** The circuit explanations below use ideal gates and pure states, without noise or hardware compilation errors. This lets us isolate the mechanism. It is not a prediction that real hardware will exactly match every ideal probability.

| Step | What changes? | Why do it? | What does not follow automatically? |
|---|---|---|---|
| Prepare the all-plus state | Each complete bitstring initially has the same amplitude and probability. | This is an easy-to-prepare starting point that initially excludes no candidate. It uses no prior knowledge of the optimum. | Uniform sampling alone favours no solution. This is an algorithm choice. |
| Apply the cost step | Amplitude directions change according to each candidate's cost. Their lengths stay the same. | Put information from the known cost formula into the state through reversible phase gates. | A lower cost has not yet become a higher probability. |
| Apply the mixer | Each output amplitude combines contributions from other candidate amplitudes. | Convert relative phase information into interference that can change measurement probabilities. The standard X mixer connects candidates differing by bit flips. | The interference need not favour good candidates for arbitrary angles. |
| Repeat cost and mixer layers | Later phases act on the state produced by earlier mixing. | Give the tunable circuit more opportunities to use problem-dependent joint structure. | More layers do not guarantee a better result from a finite optimiser or noisy device. |
| Prepare and measure repeated runs | Each run produces one ordinary candidate bitstring. | Obtain answers we can decode and enough samples to estimate costs. | One run does not reveal the amplitude list or certify an optimum. |
| Update the angles classically | The next circuit uses different gate parameters. | We do not know the useful angles in advance; measured costs provide feedback for searching them. | This outer search can itself be difficult. |
| Decode and validate | Convert output bits into start choices and check the original rules. | A candidate must still be a valid answer to the scheduling problem. | A quantum sample, or a low score alone, is not an independent validation. |

Notice why both cost and mixing appear. Repeated cost steps alone keep the initial measurement probabilities unchanged. The standard X mixer alone also leaves the all-plus state's probabilities uniform. To see why, each X operator swaps equal amplitudes, so each leaves that state unchanged. The sum of $N$ such X operators therefore multiplies it by $N$: it is an eigenstate of the mixer Hamiltonian. The mixer exponential then adds only a common phase $e^{-\mathrm i\beta N}$, leaving every measurement probability unchanged. Their alternation is the mechanism we investigate; it is not an automatic minimum-finding instruction.

### General circuit · Initial state, cost, mixer

**Algorithm choice.** The following equations define standard QAOA’s particular starting state and gate sequence. Quantum physics permits many other circuits; it does not dictate this optimisation recipe. The preceding table explains the purpose of each chosen part.

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

**Derivation / intuition.** The cost operator has $|x\rangle$ as an eigenvector with eigenvalue $E(x)$. Applying its exponential therefore attaches the scalar phase $e^{-\mathrm i\gamma E(x)}$ to that component. This follows from the mathematical exponential power series: each operator power acts as the corresponding power of $E(x)$. The gate changes direction, while its unit-magnitude factor preserves length. We show its action rather than require a general matrix-exponential course.

If $|\psi\rangle=\sum_x\alpha_x|x\rangle$, then

$$
U_C(\gamma)|\psi\rangle=\sum_x\alpha_xe^{-\mathrm i\gamma E(x)}|x\rangle.
$$

The probabilities $|\alpha_x|^2$ are unchanged by this step. Low-energy states do not automatically receive larger probabilities. The energy-dependent relative phases become useful only when subsequent operations mix amplitudes.

### What the X mixer actually does

**Mathematical result used — commuting exponentials.** If two finite matrices commute, their exponential sum factors into the product of their exponentials. This follows from multiplying their power series and using the binomial theorem for commuting matrices. We use that result to split the sum of separate-qubit X operators into separate gates. It would not be valid for arbitrary noncommuting operators. The second identity below follows by separating even and odd powers and using $X^2=I$: the even powers give $\cos\beta\,I$, and the odd powers give $-\mathrm i\sin\beta\,X$. The detailed numerical action is then derived in the one-bit example.

The $X_i$ operators commute because they act on different qubits: applying them in either order gives the same result, $X_iX_j=X_jX_i$. Thus the mixer factors into one-qubit operations, and since $X^2=I$,

$$
U_M(\beta)=\prod_i e^{-\mathrm i\beta X_i},\qquad
e^{-\mathrm i\beta X}=\cos\beta\,I-\mathrm i\sin\beta\,X.
$$

For a single application of this factor, each output amplitude combines the old amplitude at that bitstring with the amplitude at the bitstring whose chosen bit is flipped. That is the local source of interference. Repeated layers can create structured, correlated distributions. The direction of the improvement depends on the angles and on the whole energy landscape; it is not guaranteed by the mixer alone.

### Example · A one-bit mechanism demonstration, not a scheduling benchmark

Let $E(x)=x$, whose minimum is at $x=0$. In the initial plus state the amplitudes of 0 and 1 are both $1/\sqrt2$. The cost step multiplies the zero amplitude by $e^{-\mathrm i\gamma\cdot0}=1$, and the one amplitude by $e^{-\mathrm i\gamma\cdot1}=e^{-\mathrm i\gamma}$. The resulting state is $(|0\rangle+e^{-\mathrm i\gamma}|1\rangle)/\sqrt2$.

The mixer is $\cos\beta I-\mathrm i\sin\beta X$. To obtain its output amplitude at 0, take $\cos\beta$ times the old amplitude at 0 and add $-\mathrm i\sin\beta$ times the old amplitude at 1, because $X$ swaps the two states. Call that output amplitude $\alpha_0'$:

$$
\alpha_0'=\frac{\cos\beta-\mathrm i\sin\beta e^{-\mathrm i\gamma}}{\sqrt2}.
$$

To turn the amplitude into a probability, take its squared magnitude. First separate real and imaginary parts using $e^{-\mathrm i\gamma}=\cos\gamma-\mathrm i\sin\gamma$. Distributing $-\mathrm i\sin\beta$ gives $-\mathrm i\sin\beta\cos\gamma-\sin\beta\sin\gamma$, since $(-\mathrm i)(-\mathrm i)=-1$. Therefore

$$
\alpha_0'=\frac{(\cos\beta-\sin\beta\sin\gamma)-\mathrm i\sin\beta\cos\gamma}{\sqrt2}.
$$

For a complex number, squared magnitude is the real part squared plus the imaginary part squared. The common denominator $\sqrt2$ is squared too, giving 2:

$$
\begin{aligned}
|\alpha_0'|^2={}&\frac12\left[(\cos\beta-\sin\beta\sin\gamma)^2
+\sin^2\beta\cos^2\gamma\right]\\
={}&\frac12\left[\cos^2\beta-2\cos\beta\sin\beta\sin\gamma
+\sin^2\beta\sin^2\gamma+\sin^2\beta\cos^2\gamma\right].
\end{aligned}
$$

The last two terms combine to $\sin^2\beta(\sin^2\gamma+\cos^2\gamma)=\sin^2\beta$. Adding that to $\cos^2\beta$ gives 1. The remaining middle term has $2\cos\beta\sin\beta=\sin(2\beta)$. Thus the probability is

$$
\Pr(x=0)=\frac{1-\sin(2\beta)\sin\gamma}{2}.
$$

For $\gamma=\pi/2$, $\beta=-\pi/4$, the probability is 1. Reversing the sign of that $\beta$ gives probability 0. This intentionally simple calculation isolates phase-to-probability conversion. It does not establish that angles for interacting scheduling models are easy to find.

For those specific angles, $\sin\gamma=1$ and $\sin(2\beta)=\sin(-\pi/2)=-1$, so the formula gives $(1-(-1)\cdot1)/2=1$. Reversing the mixer sign gives $\sin(2\beta)=1$ and therefore $(1-1\cdot1)/2=0$. With no mixer, $\beta=0$ makes $\sin(2\beta)=0$, leaving probability $1/2$ regardless of the cost phase. These are the three cases in the laboratory below.

<div id="phase-lab" class="lab" aria-label="Interactive phase and mixer demonstration"><p>The phase-and-mixer laboratory requires JavaScript. The exact probability formula and its derivation are given above.</p></div>

### Example · See costs, phases and probabilities separately

Reuse the invented two-bit energy from chapter 02. Its four fixed costs are 1, −1, 4 and 6 for 00, 01, 10 and 11, respectively. The visual computes one ideal QAOA layer exactly. Start at equal amplitudes, apply the cost phases, then mix. The two angle presets demonstrate distributions favouring lower or higher costs; neither is presented as a general optimisation guarantee. The all-zero angles retain a uniform distribution. Arrow lengths represent amplitudes; probability bars show their squared lengths.

<div id="qaoa-register-lab" class="lab" aria-label="Two-qubit QAOA cost phase mixer and sampling explorer"><p>For γ = −π/2 and β = −π/4, the final probabilities are (1/2, 1/2, 0, 0), with mean cost 0. Reversing β gives (0, 0, 1/2, 1/2), with mean cost 5. Before mixing, all four probabilities are 1/4. This teaching instance and exact formulas remain readable without JavaScript.</p></div>

### Turn the circuit family into a search procedure

1. Build and audit the encoding, energy, and Ising coefficients.
2. Choose $L$, an initial parameter vector, an optimiser, and a total budget.
3. For each parameter proposal, prepare the circuit and estimate its objective. A statevector simulator can compute the ideal expectation exactly; hardware usually estimates it from samples.
4. Give that scalar estimate to the classical optimiser, which proposes new angles. Use multiple starts if the landscape warrants them, and count that work in the budget.
5. At the selected angles, collect a final batch of bitstrings. Decode each one and validate it against the original scheduling model.
6. Report raw sample statistics, best validated objective, training cost, final sampling cost, and whether noise or hardware was involved.

The circuit evaluates a distribution; the optimiser searches parameters. Neither part automatically certifies a global minimum. For the ideal circuit family, adding a layer cannot worsen the globally best attainable expectation, because its angles may be zero. A finite optimiser or noisy device can nevertheless perform worse at larger depth.

### Gate-level connection to the Ising coefficients

**Definition / derivation.** The rotation-gate names below use the explicitly stated half-angle convention. Matching their exponents to the desired cost phase produces the factor of 2 in each gate angle; that factor is bookkeeping, not a new physical law. Terms composed only of Z operators commute because they are diagonal in the same basis, so their cost phases can be implemented term by term.

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

### Did we find a solution, our best solution, or the optimum? {#optimality-guarantees}

**A finite QAOA run generally provides candidates, not a guarantee of the globally best answer.** If we validate every candidate and retain the one with the lowest objective, we have the **best valid solution found in that search**. “Optimal” is a stronger statement: no valid solution anywhere in the declared problem has a better objective. A high sampling frequency, many unsuccessful attempts to improve the incumbent, or agreement among several heuristics does not prove that statement.

Keep two claims separate. A correct encoding and penalty argument can prove that *a global minimum of the mathematical model* solves the intended problem. The search algorithm must still find that minimum. Defining the correct answer mathematically does not guarantee that a finite optimiser reaches it.

**How a guarantee can arise.** Let $F^*$ be the unknown minimum of the original objective over all feasible schedules. Let $U$ be the objective of our best independently validated schedule. Because the optimum cannot be worse than a feasible candidate, $F^*\le U$. Separately, derive a valid **lower bound** $B$: a proof that no feasible schedule can have objective below $B$. Combining them gives

$$
B\le F^*\le U,\qquad 0\le U-F^*\le U-B.
$$

If $B=U$, the bounds force $F^*=U$: we have proved optimality. If they differ, $U-B$ is a certified upper bound on how far our candidate is from optimal. Exhaustive search, exact-solver bounds, or a problem-specific argument can supply a certificate. A solution found by QAOA can be certified using such evidence; QAOA need not have produced the proof itself.

**Invented example.** Our validated schedule finishes at time 12. A resource argument proves no schedule can finish before time 10. Therefore the unknown optimum lies between 10 and 12, and our schedule is at most 2 time units worse than optimal. If we later find a schedule finishing at 10, the existing bound immediately proves it optimal. If instead we merely sample the time-12 schedule a million times, the bound remains 10 and optimality remains unresolved.

**Special case: feasibility penalties.** If the energy is a sum of nonnegative penalties and a candidate has energy zero, zero is already a known lower bound. That candidate is a global energy minimum and, under the proved encoding, feasible. This certifies feasibility at the tested deadline. It does not by itself prove the shortest possible deadline: that needs evidence ruling out every shorter possibility, such as a certified infeasible preceding integer deadline in the monotone horizon search. Failing to sample a zero-energy candidate does not prove infeasibility.

**Always name the scope.** A proof for a restricted machine set, fixed horizon, fixed random scenario, local neighbourhood or primary objective applies to that scope. A globally optimal small subproblem inside a hybrid does not make the whole factory policy globally optimal. Likewise, minimising makespan does not prove minimum monetary cost unless that is the objective actually modelled and certified. Approximation theorems, when available for a particular algorithm and problem class, must state their assumptions and bound; they are not a blanket exact-optimum guarantee for general QAOA scheduling.

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

To derive that change formula, flipping $x_i$ replaces it by $1-x_i$. The change in its value is $(1-x_i)-x_i=1-2x_i$: +1 for a 0→1 flip and −1 for a 1→0 flip. Its linear term therefore changes by $a_i(1-2x_i)$. Each pair touching it changes by $w_{ij}x_j(1-2x_i)$ or $w_{ji}x_j(1-2x_i)$, depending on which index was stored first. All other terms, including the constant, have identical values before and after the flip and cancel in the difference. Add the changed terms and factor out their common $(1-2x_i)$ to obtain the formula above.

### Quantum annealing and embedding

**Physical theorem used — quantum adiabatic theorem.** Under appropriate smoothness, gap and slowness conditions, an isolated system initially in a ground state can remain close to the evolving ground-state subspace. The gap here is the energy separation between that ground-state subspace and the states above it. The theorem’s proof and quantitative error bounds are outside scope. Its conditions matter: the annealing intuition below is not a guarantee for an arbitrary finite, noisy run. **Algorithm choice:** the interpolation schedules are chosen to try to exploit this behaviour.

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

All sixteen $y$ words are encoding-valid because each group has only one threshold bit. The exactly-once penalties are zero under these substitutions. Expand every remaining conflict term as follows:

| Original conflict | Substitute the indicators | Expand the product |
|---|---|---|
| $x_1x_5$ | $(1-y_1)(1-y_3)$ | $1-y_1-y_3+y_1y_3$ |
| $x_1x_6$ | $(1-y_1)y_3$ | $y_3-y_1y_3$ |
| $x_2x_6$ | $y_1y_3$ | $y_1y_3$ |
| $x_3x_7$ | $(1-y_2)(1-y_4)$ | $1-y_2-y_4+y_2y_4$ |
| $x_3x_8$ | $(1-y_2)y_4$ | $y_4-y_2y_4$ |
| $x_4x_8$ | $y_2y_4$ | $y_2y_4$ |
| $x_2x_3$ | $y_1(1-y_2)$ | $y_1-y_1y_2$ |
| $x_6x_7$ | $y_3(1-y_4)$ | $y_3-y_3y_4$ |

Now add the eight expanded rows. There are two constants, giving $1+1=2$. The coefficient of $y_1$ is $-1+1=0$; that of $y_2$ is −1; that of $y_3$ is $-1+1+1=1$; and that of $y_4$ is $-1+1=0$. The coefficient of $y_1y_3$ is $1-1+1=1$, and that of $y_2y_4$ is also 1. Finally, $y_1y_2$ and $y_3y_4$ each appear once with coefficient −1. Collecting these contributions gives

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
| [IBM Quantum Learning, Quantum information](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information) | State vectors, amplitudes, normalisation and measurement. |
| [IBM Quantum Learning, Quantum Coins](https://quantum.cloud.ibm.com/learning/en/modules/quantum-mechanics/superposition-with-qiskit) | Hadamard gates, relative phase and interference. The guide's visual performs local ideal calculations and requires no IBM account or hardware. |
| [IBM Quantum Learning, Bloch sphere](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/bloch-sphere) | Single-qubit geometry, relative phase, poles and the distinction between pure and mixed states. |
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

`guide.md` is the editable source. `build.py` rebuilds the reading edition using Python packages `markdown` and `latex2mathml`; runtime dependencies are not needed to read the HTML. `audit.py` runs local mathematical checks with Python's standard library and the repository's baseline builder. `audit-report.json` records the executed checks. `visuals.js` contains the four additional conceptual visuals; `check-visuals.cjs` independently checks their calculations with Node.js and records the checked source hash in `visual-audit-report.json`. The build embeds that report and verifies the source match. `QUALITY.md` records the revision and validation passes for this edition.
