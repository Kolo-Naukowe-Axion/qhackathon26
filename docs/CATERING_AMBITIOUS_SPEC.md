# Lunch under pressure: ambitious catering production specification

Design revision 1 — 17 October 2026, Europe/Warsaw.

**Status:** the user subsequently selected catering as the active direction to
try. This remains an implementation target, not a completed model, solver result,
hardware run or prediction of a competition score. Preserve the verified factory
as a fallback. Quantum/VeloxQ execution remains held.

The agreed [work allocation](CATERING_METHOD_WORKSPLIT.md) is Codex-owned shared
foundation first, then four independent method owners: VeloxQ, QAOA, VQE and
classical benchmarks. All consume the [same solver contract](CATERING_SOLVER_CONTRACT.md).
The implementation handoff gate is not satisfied merely by this written spec.

This document is the authoritative ambitious catering design. It supersedes
older catering sketches wherever it explicitly changes their assumptions.
The [earlier proposal](CATERING_VELOXQ_PROPOSAL.md) records the discussion and tiny
audit; [compute notes](STAGE2_COMPUTE_ACCESS.md) record the latest access checks.

## 1. The idea and the claim we want to earn

A central kitchen has confirmed lunch orders, finite equipment and staff, and
food that remains acceptable for only a declared time after cooking. It must
choose what batches to create, how much each should contain, which customer
orders share their output, and when and where to prepare, cook and pack them.
An urgent order and/or a cooker failure arrives after production starts.
The planner must adapt using the actual remaining stock, work and capacity.

The output is a checked production and handover plan with explicit missed meals,
discarded food, costs and changes. A solver is not allowed to hide an unserved
order by shifting a departure or serve food beyond the model's age limit.

The proposed contribution has three parts:

1. **Endogenous production:** the jobs, quantities and customer allocation are
   decisions, rather than a fixed set of factory operations with renamed labels.
2. **An encoding study:** determine how much of that decision structure can be
   represented compactly, at what interaction/circuit cost, and with what loss
   if choices are deliberately restricted.
3. **An integrated recovery experiment:** native classical methods, same-QUBO
   samplers, and a small quantum experiment answer the same operational question
   at clearly stated scopes.

A useful hypothesis is that sharing batches saves repeated preparation/cleaning
but competes with freshness, departure times, holding space and recovery options.
It must become a measured finding. No novelty, superiority or advantage is
established by writing this specification.

## 2. What “most ambitious” means here

The ambitious operational model includes:

| Mechanism | Required semantics |
|---|---|
| Batch creation | Optional new batches with menu and allowed yield choices |
| Sharing | One same-menu batch can supply several customer/departure groups |
| Resource choices | Eligible prep stations, cookers and identified qualified workers |
| Scheduling | Preparation, cooking, packing and equipment cleaning on a finite grid |
| Freshness | Cook-end-to-fixed-handover age checked for every supplied lot |
| Service | Explicit missed demand; fixed customer departures |
| Food accounting | Produced, handed over, currently held and discarded quantities |
| Ingredients | Finite menu-specific ingredient budgets; no consumption twice |
| Holding | Finite combined cooked/packed holding capacity |
| Electricity | Aggregate instantaneous power limit and a time-dependent energy ledger |
| Recovery | Preserve actual past/running work; replan legal future continuations |
| Disruptions | Normal, urgent-order, cooker-outage and combined cases |

Ingredients, holding and power are the first features to defer if the core
implementation gates fail. Their disabled profiles remain different declared
models, not lossless reductions of the full ambitious model.

The scope deliberately excludes vehicle routing, uncertain food chemistry,
allergen/cross-contamination certification, arbitrary sequence-dependent wash
matrices, cross-menu component BOMs, forecast-driven speculative orders,
learned demand prediction and equipment-purchase decisions. These would require
new semantics and validation, not just additional descriptive labels.

## 3. Proposed synthetic flagship

All numbers in this section are synthetic fixture parameters. They are not
operational food-safety guidance, actual catering records, calibrated costs or
proof that every order can be fulfilled.

### 3.1 Calendar, demand and units

- Production window: 07:00–13:30, represented as minutes 0–390.
- Initial time step: 10 minutes; 39 intervals and 40 boundary points.
- Quantity unit: one lot of 10 meals. Sub-lot allocation is outside this version.
- Starts are grid-aligned. Durations in the fixture are exact multiples of the
  grid; a finer-grid sensitivity is a separate instance, not a hidden rounding.
- Intervals are half-open: an operation ending at time t releases its resource
  for another operation starting at t.

| Customer | Chicken meals | Vegetable meals | Pasta meals | Fixed handover |
|---|---:|---:|---:|---|
| A | 40 | 20 | 20 | 12:00 |
| B | 20 | 30 | 10 | 11:30 |
| C | 10 | 10 | 20 | 12:30 |
| D | 20 | 20 | 20 | 13:00 |

There are 240 meals, or 24 lots, in 12 nominal demand groups. A demand group is
identified by customer, menu and departure, not just by customer name.
The urgent order adds two groups: B/vegetable/12:00 and B/pasta/12:00, each two
lots. B's original 11:30 commitments remain separate. All service weights are
one in the initial fixture; unequal priorities require a separate declared profile.

### 3.2 Equipment, workers and recipes

Equipment:

- Prep stations P1 and P2, each unary.
- Cookers C1 and C2, each unary and eligible for all three menus initially.
- Packing line K1, unary, processing one lot per 10-minute interval.

Identified workers and proposed qualifications:

| Worker | Prepare | Start/attend cooking | Pack | Clean |
|---|---|---|---|---|
| W1 | Yes | Yes | Yes | Yes |
| W2 | Yes | No | Yes | Yes |
| W3 | No | Yes | Yes | Yes |

Workers are available throughout the initial calendar. Availability calendars
are explicit input arrays, allowing shift/outage sensitivities without changing
the mathematics. There is no worker travel time in this one-room kitchen.

| Menu | Batch yield, lots | Preparation | Cooking for yields 1/2/4 | Packing | Maximum age |
|---|---|---:|---|---|---:|
| Chicken | 1, 2, 4 | 10 min | 20 / 30 / 40 min | 10 min per served lot | 60 min |
| Vegetable | 1, 2, 4 | 10 min | 20 / 20 / 30 min | 10 min per served lot | 60 min |
| Pasta | 1, 2, 4 | 10 min | 10 / 20 / 30 min | 10 min per served lot | 40 min |

Each new batch has one preparation operation. Cooking starts after preparation
and occupies the selected cooker for its whole processing interval. A qualified
worker attends the first 10 minutes of cooking; the remaining cooking interval
is unattended. This is a synthetic attendance rule, not a claim about a real
recipe. The cooker remains occupied after cooking until its mandatory immediate
10-minute terminal clean finishes; cleaning also requires one qualified worker.

Packing starts after cooking. It may be represented as one 10-minute operation
per allocated lot, with a worker and K1 required for each interval. Allocated
lots need not all be packed consecutively. Internally valid batch programs may
use different workers for different operations. A worker cannot simultaneously
start a cooker, pack a lot or clean another cooker.

Unused output is not packed merely to create artificial work. The handling of
unallocated cooked output is specified in the waste policy below. Prepared
ingredients waiting for their cooking operation have no separate buffer limit
in this revision; the finite holding limit applies after cooking.

### 3.3 Ingredient, holding and power profiles

The ambitious default profile proposes ingredient budgets sufficient for 12
chicken lots, 14 vegetable lots and 12 pasta lots. These are menu-specific input
units: no implicit sharing of a chicken ingredient with a vegetable dish.
One yielded lot consumes one menu-specific ingredient unit when preparation
starts. Unused raw ingredients remain stock; they do not automatically become
food waste at the end of the planning window.

Cooked and packed food share a holding capacity of eight lots. A served lot
occupies this capacity from cook completion until its fixed customer handover,
including all time spent packing and waiting. Immediate disposal removes an
unallocated lot at cook completion. A separate disposal time must be specified
if immediate disposal is disabled.

Synthetic power draws are 0.5 kW per active prep station, 4 kW per cooking
operation, 0.5 kW for K1 and 0.5 kW during each cooker clean. The initial site
power limit is 8 kW. Attendance does not add a second copy of machine power.
Cooking's power interval ends at cook completion; cleaning has its own power.

Proposed tariff profile: 60 grosz/kWh before 10:00, 100 from 10:00–12:00 and 70
after 12:00. These values are synthetic coefficients. Use an exact common
denominator for energy prices rather than floating-point comparisons. With
power in 0.1 kW units and 10-minute intervals, energy cost in grosz has denominator
60; multiply by 60 for integer energy-cost ticks.

The initial ledger includes variable ingredients, attended labor, disposal and
energy only. If monetary optimization is enabled, ingredient prices, labor rates
and disposal prices must also be supplied as integer/rational fixture inputs and
source-labeled. Do not invent a calibrated business saving from this tariff table.
Opening-hours decisions, standby activation and demand charges are outside this
revision's monetary profile.

## 4. Four scenarios and the event-time correction

The earlier 09:30 event time was illustrative. An outage ending at 10:10 could
miss the critical cooking window entirely when lunch must still be fresh at
11:30–13:00. Retain the disruption, but use an explicit event parameter and
validate that it interacts with actual production.

The proposed flagship event time is **10:50**, with cooker C2 unavailable until
**11:30** in outage cases. This is a new design choice, not a measured result.
Use 09:30 only as a separately declared timing sensitivity if desired.

| Case | Information revealed at 10:50 |
|---|---|
| S0 — control | No new order; no capacity change |
| S1 — urgent | Add 20 vegetable and 20 pasta meals for B at 12:00 |
| S2 — outage | C2 becomes unavailable 10:50–11:30 |
| S3 — combined | Both the urgent order and C2 outage |

All four cases start from the same nominal plan and exactly the same physically
executed prefix. The original plan is built without seeing the realized case.
Generate and freeze that plan once using a declared baseline method and tie-break.
The event time, outage duration, fixture and baseline-selection rule must be
frozen before test-set solver comparisons.

The fixture acceptance checks require useful residual decisions and at least
some work already started. Record whether a cooker is actually processing at
the event and how many batches remain untouched. If there is no affected work
or spare-capacity alternative, report that outcome; do not move the outage after
seeing which method wins.

S0 still invokes the same recovery interface. Its result distinguishes gains
from ordinary replanning from gains specifically caused by the event.

## 5. Physical state and recovery contract

This ambitious version supports phase-aware continuations. That extends the
older conservative proposal, which committed the whole future local program
of every started batch. Keep both policies as named ablations; never compare
their optima as though their decision domains were identical.

### 5.1 Snapshot at the event

The state contains:

- Current time and the observed event.
- Actual completed operations and handovers, with identities and timestamps.
- Running operations, assigned resources, expected ends and remaining attendance.
- Every existing batch's menu, produced/remaining yield, completed phase,
  cook completion if known, packed-lot records and locked allocations.
- Remaining raw ingredient stocks; consumed inputs cannot be credited back.
- Equipment availability and cleaning status.
- Holding inventory, expiration times and resource reservations.
- The previously planned but unstarted operations for change accounting.
- Accumulated prefix costs and waste as immutable ledger contributions.

Only actual handover counts as fulfilled demand in the executed prefix.
Packed but unhanded food is inventory, not an already delivered order.
Packed customer labels remain locked in the first implementation. Unpacked
same-menu output may be allocated to any eligible residual group after the
event, subject to quantities, age and any declared commitment locks.

An operation starting exactly at the event boundary is unstarted unless the
state explicitly records that it began before the event was revealed. Record
one deterministic event/operation ordering rule and use it in every method.

### 5.2 Legal continuations

Completed work is immutable. Running operations on unaffected resources finish
on their current resources; their already committed occupancy and attendance
remain in the capacity calendar. Future operations may change if their physical
predecessors and inventory state permit it.

For each existing unfinished batch, choose exactly one continuation:

1. Complete its legal remaining operations and allocate its available output.
2. Retain already packed valid allocations and discard other available output.
3. Abandon the batch's remaining material under the declared disposal policy.

Not every branch is available in every state. A partially packed batch cannot
be re-prepared to create another full yield, and a running cooking operation
cannot be restarted on a second cooker without recording the first material as
lost and creating a new batch with new ingredients.

Every selected continuation references the existing batch identity. There is no
way to select two continuations of the same material or to reuse a consumed lot.

### 5.3 What an actual cooker failure does

The outage policy must be determined from the state, rather than silently
pretending that interrupted cooking completed:

- If C2 is idle at 10:50, future starts are blocked until 11:30.
- If C2 is cooking across 10:50, the interrupted batch's entire in-process
  quantity is discarded in the default failure policy. It serves no demand.
  Its consumed ingredients and incurred work remain charged. The affected
  operation ends at failure; the batch's canceled suffix cannot reserve resources.
- If cooking ended at 10:50, process its completion before the failure under the
  declared boundary rule. Cooked food is retained; C2 still loses capacity.
- If C2 is in cleaning when it fails, its already cooked output is retained.
  The cooker remains dirty and unavailable.
- After repair, C2 needs a full 10-minute clean before another cook begins.
  The default fixture requires this post-repair clean in every outage case,
  including when C2 was idle. It is a mandatory residual task requiring a
  qualified worker, starting no earlier than 11:30 and ending by the horizon.
  C2 stays unavailable for cooking until the selected clean finishes.
  This task also satisfies any interrupted batch's unfinished terminal clean;
  do not book two overlapping copies of the same physical cleanup.

The safe fallback is an idle-boundary capacity-withdrawal fixture. It keeps
the four scenarios and avoids interrupted-batch semantics if phase-aware
recovery is not validated in time. Label it as capacity withdrawal rather than
a demonstrated live cooking failure.

## 6. Hard constraints and accounting identities

### 6.1 Demand and delivery

For demand group d, let D_d be residual confirmed demand in lots, y_d the lots
handed over validly at its fixed departure, and u_d the missed lots:

    y_d + u_d = D_d,       0 <= u_d <= D_d.

No customer receives more than its confirmed amount. Lots cannot be delivered
before the order is revealed, packed after departure, or counted twice.
The urgent B orders' 12:00 departure does not relax the original B/11:30 groups.
There is no soft lateness term in this fixed-departure specification.

### 6.2 Batch material balance

For every produced batch, its yielded quantity equals:

    handed-over lots + currently held lots + discarded lots.

During production, distinguish not-yet-cooked in-process material from cooked
output. At the terminal horizon, held perishable output must be delivered under
an allowed handover or disposed of; it cannot disappear from the ledger.
Partially executed snapshots carry these balances across the event.

For every ingredient menu stock:

    opening stock + allowed deliveries = consumed stock + remaining raw stock.

There are no ingredient deliveries in the first fixture. WIP creation consumes
ingredients once; continuing WIP consumes none of those ingredients a second time.

### 6.3 Freshness and ordering

For every allocated lot l from batch b serving group d:

    preparation_end <= cooking_start;
    cooking_end <= packing_start_l;
    packing_end_l <= departure_d;
    0 <= departure_d - cooking_end <= maximum_age_menu.

Cooking-end timestamps are shared by all output of a batch. Packing a box later
does not reset its food age. Eligibility is checked at handover, including early
waiting. A freshness boundary equal to the limit is accepted in this model.

### 6.4 Resource and capacity constraints

At every relevant time interval:

- Each unary station, cooker and packing line has at most one occupant.
- Each identified worker attends at most one operation and is qualified.
- Running/preserved work and post-repair cleaning consume capacity.
- Cooked/packed holding load does not exceed the holding limit.
- Aggregate machine power does not exceed the site limit.
- Total new-batch ingredient consumption does not exceed residual stock.

For grid-aligned fixture intervals, checking every grid cell is sufficient.
If non-grid endpoints are later introduced, partition time at every load change;
do not leave short overlaps invisible between sampled instants.

There is no general rule that all conflicts are pairwise. Holding, power and
ingredient capacity can be violated by a group even when every pair is allowed.
Those need cumulative constraints, not an incomplete pair-conflict graph.

## 7. Food waste: the explicit policy

The ambitious version models **discarded food/material**, not only an excess
production proxy. It reports three separate quantities:

1. Cooked/packed lots discarded without handover.
2. Prepared/in-process meal-equivalent lots lost, including interrupted cooking.
3. Unused raw ingredients remaining as inventory.

The first two contribute to modeled waste; the third does not. A synthetic
meal-equivalent lot treats menu quantities comparably but is not a measured mass
or environmental footprint. Report categories separately even when summed.

Default rules:

- A new batch's yielded lots that are allocated to no demand are discarded at
  cook completion. Handling is included in the synthetic cleaning convention;
  no unmodeled extra worker is implied.
- A known canceled/failed batch disposes of its affected material at the event.
- Existing cooked inventory may be retained only while fresh and useful. Its
  continuation specifies handover or disposal no later than expiry/horizon.
- Nothing is donated, sold to another customer or carried into tomorrow unless
  a later model explicitly introduces that outlet.
- Disposal never contributes to demand coverage.

This policy can be restrictive. A later version may permit unallocated surplus
to wait for future demand, but that requires inventory/allocation decisions and
information rules. Do not quietly turn immediate disposal into free recourse.

## 8. Objective and exact scalarization

The default reported objective is lexicographic:

    (U, W, B, R)

where:

- U = missed confirmed lots, or a predeclared integer priority-weighted sum.
- W = discarded cooked plus prepared/in-process meal-equivalent lots.
- B = number of new cooking batches started in the decision horizon.
- R = changes to the previous unstarted plan.

Prefix contributions are constants when comparing recovery decisions, but
remain in the whole-day report. Do not count an existing cooking batch again
as a new batch when only its packing continuation changes.

An optional monetary profile uses:

    (U, W, C, B, R)

C is integer-scaled variable ingredient, labor, disposal and energy cost.
This profile is enabled only with complete declared prices and valid bounds.
It is not already implemented or calibrated. Compare methods within the same
profile. Minimizing batch count is a capacity/setup proxy, not automatically
equivalent to minimizing money.

For an objective vector f_1,...,f_k of nonnegative integer components bounded
by F_1,...,F_k, define w_k=1 and recursively:

    w_i = 1 + sum_(j>i) w_j * F_j;
    C_objective = sum_i w_i * f_i.

A one-unit improvement in an earlier component then dominates every possible
change in later components. Bounds must be computed from the represented domain
and carried in the artifact. If coefficient ranges become harmful, investigate
sequential lexicographic solves or a stated alternative objective, with the
extra solve cost included. Do not silently clip dominance weights.

For complete batch/continuation options, waste, batch count and variable cost
are nonnegative per-option coefficients plus prefix constants. Missed demand
is linear in its register. A declared Hamming distance to previous option
selections gives a linear change objective:

    R = sum_(i with previous bit 0) x_i
        + sum_(i with previous bit 1) (1 - x_i).

Removed old options contribute constant cancellation cost. Newly offered
options use previous bit 0. Stable semantic option IDs are required. This counts
replacing one old program by a new one as two bit changes; it must not be labeled
“one batch rescheduled.” A more physical operation-level change metric can be
reported separately or introduced with an explicitly audited encoding.

## 9. First exact QUBO: batch and continuation options

### 9.1 Meaning of a bit

An option is one legal local batch program, never a pre-solved complete kitchen
schedule. It includes:

- New-batch identity or the existing WIP batch it continues.
- Menu, yield or residual quantity and material state.
- Resource assignments and operation intervals still requiring decisions.
- Allocated lot quantities by demand group and their packing/handover times.
- Cleaning, holding-load and power-load profiles.
- Ingredients newly consumed, disposal events and objective contributions.

Let x_b select option b. Let a_db be its valid lot coverage for group d.
For an existing WIP batch g, G_g is its set of mutually exclusive continuations;
require sum_(b in G_g) x_b = 1. Discard is a real option where physically allowed.
Mandatory recovery tasks, such as C2's post-repair clean, also have an exactly-one
group of legal worker/time options. These task options serve no meal demand.
Every C2 cook option starting before the selected recovery clean ends is
incompatible with that clean option, even if their intervals do not overlap.
Include those pairs to enforce cross-option precedence. Running/common fixed
occupations are accounted for separately and must not be charged again.
For new batches no exactly-one constraint is needed unless slot labels are
introduced as an explicit representation. Their resource use and demand balance
already limit selection.

Generate options from raw recipes, calendars and the state, without copying a
full optimal schedule into the option pool. Eliminate exact duplicate local
programs and record all restrictions on waiting, packing order and allocations.
If only consecutive packing is generated, that is a restriction of Section 3,
not a complete representation of arbitrary legal packing.

### 9.2 Demand and bounded registers

Encode each integer u_d in [0,D_d] with L_d=ceil(log2(D_d+1)) bits, using a
bounded binary representation. For D_d=0, use no bits and substitute zero.
For D_d>0, one such set of weights is:

    1, 2, ..., 2^(L_d-2), D_d - (2^(L_d-1)-1).

For L_d=1 there is only the final weight. The weights sum to D_d and represent
every integer from 0 to D_d, sometimes more than once. Duplicated encodings
affect sampling probabilities and must be counted in state-space comparisons.

Use the demand penalty:

    P * sum_d (sum_b a_db*x_b + u_d - D_d)^2.

The twelve nominal demand groups need 22 shortfall bits before executed work
is subtracted; the urgent groups add four. These are not the whole register.

### 9.3 Unary conflicts and cumulative capacities

Build forbidden pairs F from raw unary resource occupations and mutually
incompatible locked material/decision choices. Their energy is:

    P * sum_((b,c) in F) x_b*x_c.

For each cumulative capacity row r, let h_rb be integer option load and K_r
capacity remaining after fixed work. Encode bounded nonnegative slack s_r:

    P * (sum_b h_rb*x_b + s_r - K_r)^2.

This applies to ingredient totals and grid-cell holding/power rows. Scale
fractional power into integer units before building penalties.
If fixed load already exceeds capacity, the boundary state or event profile
must be rejected/resolved physically; a negative residual capacity is not a
valid unsigned slack register.

Delete provably nonbinding capacity rows and exact duplicates. Count row slacks
even when their large contribution makes the encoding unattractive. Pairwise
conflicts alone do not enforce these aggregate constraints.

### 9.4 Energy and correctness contract

The literal energy is:

    E = C_objective
        + P * sum_d (coverage_d + u_d - D_d)^2
        + P * sum_g (sum_(b in G_g) x_b - 1)^2
        + P * sum_((b,c) in F) x_b*x_c
        + P * sum_r (load_r + s_r - K_r)^2.

Every term is at most quadratic. An option's internally invalid behavior is
removed by construction and independently checked after decoding.
On the declared complete finite-grid option domain:

1. Every feasible option selection has zero penalty for suitable registers.
2. Zero penalty implies coverage, continuation, pair and cumulative constraints.
3. If C_objective is nonnegative and B_upper bounds it on feasible assignments,
   any P>B_upper makes a feasible global minimum better than every infeasible
   assignment, provided at least one feasible assignment exists.
4. A global minimum then optimizes the declared scalarized objective in that
   option domain. A heuristic sample is not a certificate of this minimum.

Use a checked feasible witness to establish existence, or an independent native
reference. The no-WIP core can miss all demand as a fallback; do not assume that
this automatically handles mandatory cleaning/running work in every recovery state.

For a linear expanded objective C0+sum c_i*x_i, the upper bound
C0+sum max(0,c_i) bounds the whole bit domain. Retain constants from Hamming
cost and penalties; check nonnegativity from the original component meanings.
If a proposed objective is quadratic, derive a bound including its quadratic
coefficients. The earlier linear-only bound is not sufficient.

Infeasible best samples and large penalties are observations, not proofs of an
infeasible scheduling instance or a difficult benchmark.

## 10. Compact representation alternatives

The option encoding is the first correctness reference, not a commitment to
enumerating every possible detailed local program at flagship scale.

### 10.1 Exact preprocessing

Apply calendar, qualification, departure and freshness filtering. Substitute
past decisions and common mandatory future occupations. Aggregate truly
interchangeable lots. Remove duplicate options and redundant capacity rows.
Use symmetry breaking only for genuinely interchangeable resources/batch slots
with identical availability, costs, eligibility and boundary states.

A dominance deletion needs a replacement argument preserving demand coverage,
all continuation groups, resource/load profiles and objective. “Cheaper alone”
is not sufficient when the alternative uses a different scarce interval.

### 10.2 Counter encodings

Coverage and capacity squares can create large cliques. A partial-sum network
can replace one long sum with exact local additions and bounded sum registers.
It may add bits while reducing interaction degree; squared local additions
with several bits can still create cliques inside their factors. Invalid sum
codes, carries and overflow must be constrained and tested.

Compare bits, couplers, maximum degree, coefficient range, generation time,
memory, same-model optimum and compiled quantum gates. “Fewer couplers” does
not imply fewer qubits or lower runtime.

### 10.3 Factored batch slots

A more compact candidate uses a finite number of optional batch slots. For each
slot, represent activation, menu/yield, assignments, start/packing decisions
and customer quantities separately. Its native constraints define the same
target operational domain when slot bounds are sufficient.

This version has no fixed qubit count until fully compiled. Conditional duration,
menu compatibility, active-slot consistency, freshness and resource overlap can
produce higher-order products. Quadratize them or use another exact quadratic
construction, counting every auxiliary bit and proving penalties.

Inactive slots must have a canonical zero state or their extra degeneracy must
be measured. A slot upper bound based only on nominal demand may fail after
an event or when existing material is discarded; prove it for each declared
profile. Preserve all WIP identities separately from interchangeable new slots.

This is a representation research task, not a promise that binary indexing
compresses the full kitchen into a handful of qubits for free.

### 10.4 Restricted neighborhoods

If exact compact encodings remain too large, freeze outside choices and optimize
a selected group of batches/allocations/resource intervals. For a canonical QUBO
E=c+sum h_i*x_i+sum_(i<j) J_ij*x_i*x_j, fixing x_j=z_j outside a set S gives:

    h'_i = h_i + sum_(j outside S) J_ij*z_j, for i in S,

with internal quadratic terms unchanged and outside terms added to the constant.
Use the appropriate symmetric coefficient lookup convention.
Preserve crossing capacity/continuation/demand conditions; do not simply drop edges.

The restricted optimum is not the full optimum. Reconstruct and check the whole
plan, compare the same neighborhood with classical controls, and report the gap
to a broader native reference. Include the neighborhood selection/generation
cost and a selector-only/initializer-only control.

## 11. Honest register accounting

For the direct ambitious option encoding:

    N = M + S_demand + S_capacity + A_encoding.

M counts all offered new-batch, WIP-continuation and mandatory recovery-task
option bits, not the number of batches selected in the final schedule.
S_capacity counts ingredient, holding
and power slack bits. A_encoding is zero for the literal squares above, but may
be positive for counter/factored variants or other compiled mechanisms.
Continuation one-hot penalties use the existing option bits.

| Scenario | Demand-register count before prefix substitution | Full total |
|---|---:|---|
| S0 control | 22 | M_0 + 22 + S_capacity,0 + A_0 |
| S1 urgent | 26 | M_1 + 26 + S_capacity,1 + A_1 |
| S2 outage | 22 | M_2 + 22 + S_capacity,2 + A_2 |
| S3 combined | 26 | M_3 + 26 + S_capacity,3 + A_3 |

These are accounting formulas, not measured sizes. The earlier M+22/M+26
formulas apply to the simpler model without the extra cumulative capacities.
For an actual replan, compute demand-register counts from residual demand.
Different scenarios can change options, capacity rows and continuation groups.

The ambition has a concrete encoding cost even before counting options. At
the beginning of the day, blindly encoding all 39 holding rows, 39 power rows
and three ingredient rows in the stated profile would add:

| Unpruned capacity slack | Register bits |
|---|---:|
| Holding capacity 8 lots: 39 rows times 4 bits | 156 |
| Power capacity 16 half-kW units: 39 rows times 5 bits | 195 |
| Ingredient bounds 12, 14 and 12: 4 bits each | 12 |
| Total capacity slacks | 363 |

Power rows are divided by their common coefficient unit of 0.5 kW; using finer
0.1 kW units without normalization would waste register bits. This literal
unpruned construction would therefore be M+385 bits nominal, before any other
encoding changes. It is a design accounting example, not a compiled instance
or a lower bound. Safe deletion of nonbinding/duplicate rows, exact substitution,
different encodings and smaller quantum fixtures can change it substantially.
It establishes why the full ambitious model must not be casually promised to
fit a 140-qubit device.

A direct QAOA register needs one circuit qubit per compiled binary variable,
plus any circuit workspace. This is not an error-corrected resource estimate.
Sequential runs reuse the device and require the maximum width, not the sum.
VeloxQ variables do not occupy quantum hardware.

The only executed catering algebra checks remain the separate 18-bit nominal
and 16-bit outage supplied-option toys. They omit the ambitious WIP/worker/
capacity mechanisms. Neither their counts nor the unrelated factory's 28-qubit
bridge establish the ambitious kitchen's width.

## 12. Solver architecture and useful integration

The shared pipeline is:

    raw instance + observed state
        -> independently checked baseline/reference
        -> complete or explicitly restricted encoding
        -> selected solver
        -> decode without hidden repair
        -> independent physical/material checker
        -> whole-day metrics and ledger.

### 12.1 Native reference

Use a native optional-interval scheduling model with bounded quantities,
resource calendars, ingredient/holding/power cumulatives and conditional batch
logic. It must derive its constraints from raw recipes/state, not the QUBO's
conflict list. Tiny instances also need independent direct enumeration.

Report OPTIMAL/FEASIBLE/UNKNOWN/INFEASIBLE with incumbent and bound. An UNKNOWN
full reference cannot certify a restricted optimum or make a positive heuristic
energy into an infeasibility proof.

### 12.2 Classical operational baselines

- Per-customer batches with earliest-departure scheduling.
- A reasonable same-menu sharing heuristic with freshness checks.
- A baseline that keeps the old plan where legal and inserts urgent work.
- Same-QUBO simulated annealing.
- Exact restricted-domain optimization where tractable.

Baselines must enforce the same declared physics and get the same revealed
information and optional initializer. Arbitrarily weak or invalid baselines
do not establish a useful contribution.

### 12.3 VeloxQ

VeloxQ receives a medium/large QUBO from this same catering workflow if the
direction is activated and service use is authorized. Its role is a production
selection/recovery decision, not an unrelated benchmark.

Compare cold runs against SA on identical coefficients and against the native
model at the operational level. Warm starts are optional only after backend
support and semantic bit mapping are verified. Measure compilation, serialization,
network, backend, decoding and checking time separately and end-to-end.
Sparse structure and beneficial runtime must be measured, not assumed.

The user has limited service usage. Verify the billing unit, remaining allowance,
job count and runtime ceiling before any pilot. No automatic retries or broad
parameter sweeps against the service. A failed/negative result stays in evidence.

### 12.4 Quantum simulation and IBM hardware

Start with a complete small kitchen instance where several interacting batch,
sharing and timing choices remain. A second acceptable scope is a clearly
conditional neighborhood in the ambitious kitchen. Do not encode one already
selected full schedule and describe decoding it as solving the kitchen.

Construct the cost Hamiltonian from the audited QUBO using x=(1-Z)/2. Retain
the offset and coefficient convention. Use a shallow QAOA implementation with
a documented initializer/mixer; any feasibility-preserving mixer needs its own
reachability and circuit-cost analysis. Evaluate raw samples independently.

Tune parameters on TRAIN simulator instances before freezing the hardware
workload. Use matched uniform, classical and initializer-only controls.
Sampling success is empirical; no hardware optimum or quantum advantage is
promised by the architecture.

## 13. Compute and IBM minute budget

Latest verified access is in [compute notes](STAGE2_COMPUTE_ACCESS.md):

- Local M5 Pro: 48 GB unified memory, 15 CPU and 16 GPU cores.
- WCSS Axion account accepts non-submitting checks for 128 GB and 1 TB CPU
  requests and one Hopper GPU. Actual queueing matters; no node is reserved.
- No current Vast.ai instance; the other configured SSH host timed out.
- IBM free allowance is a public plan, not a verified personal remaining balance.

Generic dense complex128 state storage is 4/16/32/64/128 GiB at 28/30/31/32/33
qubits before workspace. Target 18–28 useful circuit qubits initially; investigate
30–32 only after memory/time checks. Sector/tensor compression requires a
separate validity/performance explanation and cannot establish generic capacity.

IBM's [Open Plan](https://quantum.cloud.ibm.com/docs/en/guides/plans-overview)
currently describes up to 10 QPU minutes per 28-day rolling window. User-reported
roughly 140-qubit access does not identify the actual backend or usable circuit
size. Retrieve the exact target, compile to its native gates/connectivity,
inspect gate errors/depth and estimate scheduled duration before any submission.

An illustrative hardware workload is four scenarios times three frozen parameter
settings times two repeated executions, each at 4,096 shots: 24 circuits and
98,304 shots. Repeats characterize some execution variation; they do not create
24 independent kitchen instances.

IBM's [simple usage estimate](https://quantum.cloud.ibm.com/docs/en/guides/estimate-job-run-time)
gives approximately 36–82 seconds for that workload under its typical timing
assumptions and depending on sub-job grouping. That is not our actual compiled
estimate. Deep routing, mitigation, calibration circuits or payload splitting
can increase it. A candidate all-in campaign cap is 2–5 minutes if measured
timing and the actual remaining allowance support it. Include controls in the
shot/job total; 24 production circuits alone do not constitute all controls.

Simulator tuning is CPU/GPU work, not IBM QPU usage. Queue waiting is distinct
from billed execution, but can still prevent a run before the submission deadline.
No hardware optimization loop is assumed to fit 10 minutes. No paid fallback,
new rental or remote quantum/service job is authorized by this specification.

## 14. Experiment design

### 14.1 Correctness before performance

For tiny complete domains:

1. Enumerate bitstrings and independently reconstruct every selection.
2. Check zero penalty exactly matches feasible raw schedules/registers.
3. Check QUBO energy equals objective plus the literal penalty expression.
4. Match ground-state objective to independent feasible enumeration/native CP.
5. Round-trip binary/Ising conversion, variable order and decoded identities.
6. Audit integer bounds, scalarization and penalty conditions.

Include negative fixtures for double-serving a lot, doubled WIP continuations,
overlapping staff, stale handover despite early packing, aggregate holding/power
violations without pairwise conflicts, ingredient reuse, missing cleaning,
outage boundaries, lost cooking and invalid bounded-register codes.

### 14.2 Operational value

Use constructed witnesses to demonstrate:

- Sharing can avoid duplicated preparation/cleaning when departures are close.
- Sharing can be impossible when departures are farther apart than maximum age.
  For example, one batch with a 60-minute limit cannot serve departures 90
  minutes apart, regardless of packing; this is a mathematical illustration.
- Larger yields can reduce batch count while increasing disposal or holding load.
- An urgent order can be served by reallocating eligible unpacked stock or by
  producing a new batch; already handed-over lots cannot be reclaimed.
- Cooker loss can destroy WIP and consume replacement ingredients/capacity.

Use real checked fixtures to establish which of these mechanisms actually bind.
The flagship must not be presented as exhibiting every tradeoff before solving it.

### 14.3 Representation experiments

Compare complete options, safely reduced options, counters and the factored
candidate where implemented. Separately compare capped pools/neighborhoods.
Hold the operational domain and objective fixed for exact-encoding comparisons.
Report when two representations instead solve different restrictions.

The main curve is quality versus actual resource use: bits, couplers, coefficient
range, compile time/memory, end-to-end solve time and, for circuits, native gates
and depth. A lossless reduction needs proof/checks; a lossy reduction needs a gap.

### 14.4 Scaling and evaluation discipline

Start from tractable tiny instances; the proposed 4-customer flagship is an
unverified target. Scale customers, menus, departure windows, resource alternatives
and congestion. Do not inflate meal counts while leaving identical decisions
and describe that as increased combinatorial complexity.

Use distinct TRAIN/validation/test fixtures and freeze chosen settings before
test. The four events form a paired comparison from one prefix, not four
independent factory samples. Repeat across independent synthetic demand/state
fixtures before claiming generalization. Retain infeasible, UNKNOWN and failed
rows; do not condition results only on cases a solver happens to fulfill.

Report objective tuples, actual food categories, fulfilled lots, batch count,
schedule changes, raw feasibility rate, best/median outcomes, valid-sample
diversity, reference gap/bound, full runtime and compute allocation. Label raw
and repaired results, and include repair-only controls if repair is introduced.

## 15. Demo and explanation contract

Use the user's preferred game-like style to expose decisions and evidence.
Do not begin with a dense result dashboard before explaining the kitchen.

The screen should show:

- The four customer orders and fixed departure clocks.
- Equipment, actual workers and the current production timeline.
- Batch size and which customer lots share each batch.
- A freshness/holding indicator based on cook completion and handover.
- Food ledger: ingredients, in-process food, held output, served and discarded.
- The 10:50 event, affected material/capacity and the changed future plan.
- Objective tuple before/after and an independent-check result.
- Solver/representation label, bit/qubit count and real run provenance.

Allow S0/S1/S2/S3 selection with the same executed prefix. Display running work
as committed, changed future work explicitly, and discarded food as a measured
model event rather than a decorative counter. Distinguish a saved replay from
a fresh solve. A browser animation is not proof of a live quantum result.

The proposed narrative is: “One shared batch can serve several offices, but
only while fresh. A cooker fails and another order arrives. We preserve what
already happened, decide which production to keep or replace, and check every
portion, worker and resource. Then we show what a smaller encoding loses.”

## 16. Data, modules and evidence artifacts

Proposed implementation layout, not files already created:

    catering/domain.py          raw entities, units and profile validation
    catering/state.py           prefix execution and event/state transitions
    catering/check.py           independent event/resource/material checker
    catering/native.py          raw optional-interval reference model
    catering/options.py         complete/restricted local-program generation
    catering/qubo.py            literal energy, registers, weights and bounds
    catering/compact.py         optional counters/factored research variants
    catering/decode.py          semantic sample decoding without hidden repair
    catering/quantum.py         local circuits, simulator and compilation audit
    catering/experiment.py      declared scenarios, budgets and evidence capture

Every retained run should record raw input/state hashes, scenario and revealed
time, representation restrictions, generation parameters, ordered semantic bit
map, literal QUBO/Ising coefficients and offset, objective/penalty bounds, solver
versions/settings, hardware/allocation, raw results, decoded plan, independent
checks and all timing components. Retain seeds where supported and distinguish
them from independently repeated remote calls.

For hardware, additionally retain backend/target timestamp, final layouts,
native circuit, measurements, shots, execution identifiers, usage and raw counts.
No token or credential belongs in artifacts or the repository.

## 17. Build gates, de-scoping order and feasibility verdict

### Gate A — close the raw semantics

Freeze the fixture/profile, event ordering, failure/disposal behavior, stock
rules, continuation boundaries and cost profile. Implement state transitions
and the independent checker before relying on any optimizer.

### Gate B — prove a complete small instance

Build a native reference, complete local option domain and direct QUBO for a
small instance. Exhaustively check the algebra and match the independent optimum.
Exercise all four event cases, including a failed batch if that feature is claimed.
Record actual counts. There is no pass merely for reaching a chosen qubit target.

### Gate C — establish actual operational value

Produce at least one checked sharing/freshness/waste tradeoff and a useful
recovery comparison with sensible baselines. If the full flagship is too large,
reduce customers/time choices transparently while keeping those interactions.

### Gate D — measure representations

Count the broader domain before selecting a compression. Implement exact
reductions first, then one meaningful compact/restricted alternative. Measure
all auxiliaries and any lost objective value; do not promise two unfinished
encoding families as completed contributions.

### Gate E — local quantum and device compilation

Run matched local quantum/classical controls, then compile a frozen small
workload against the actual IBM target and estimate its complete budget.
If routed depth or sampling quality is poor, reduce the circuit scope with
explicit domain/gap accounting. More qubits are not automatically an improvement.

### Gate F — bounded service and hardware execution

Only after explicit authorization, verified balances and the earlier gates,
run the selected VeloxQ pilot and/or IBM campaign. Service latency and queues
are separate risks. Keep useful offline evidence if external access fails.

### Gate G — presentation and release

Show one coherent production question, checked math, a truthful comparison,
explicit limitations and a reliable game-like replay. Final video, public
release and submission retain their existing separate workflow.

If time becomes binding, defer factored encoding, then monetary optimization,
then power/holding/ingredient capacities. Keep explicit batching, sharing,
freshness, material/waste accounting and the four declared scenarios. If
phase-aware WIP recovery cannot be validated, fall back to the declared
conservative continuation policy with an idle-boundary capacity withdrawal.
Do not remove difficult cases from a published result table after the fact.

**Verdict:** this is technically credible as a hybrid research/demo project.
The strongest achievable entry does not require running the entire ambitious
kitchen on a quantum processor. The most uncertain work is complete option
generation/compact compilation and validated WIP recovery, not the existence
of a QUBO syntax or a headline device width. Completing every ambitious feature
and obtaining reliable hardware results before the hackathon deadline is not
established; early gates decide what can honestly be claimed. Preserve the
verified factory work until catering has earned a demonstrated improvement.

## 18. Current evidence boundary

| Item | Current state |
|---|---|
| Detailed ambitious specification | This document |
| Tiny supplied-option catering algebra | Verified separately: 18/16 bits |
| Full ambitious kitchen implementation | Not built |
| Four full scenario register counts | Unknown |
| Actual waste/WIP/aggregate-capacity implementation | Proposed here |
| Native catering reference at flagship scale | Not built |
| Catering QAOA/circuit timing on IBM target | Not built |
| Physical catering quantum execution | None |
| Catering VeloxQ execution or advantage | None |
| IBM personal remaining balance/backend | Unverified |

Earlier toy optima are both (missing, tardiness, excess, batches)=(0,0,0,2);
they do not demonstrate this ambitious waste model or a disruption benefit.
The later [mentor guidance](STAGE2_MENTOR_FEEDBACK.md) welcomes substantive
mathematical/algorithmic extensions but does not approve a particular project
or guarantee awards. Keep the distinction between a proposal, a checked
implementation and measured operational/hardware results visible everywhere.
