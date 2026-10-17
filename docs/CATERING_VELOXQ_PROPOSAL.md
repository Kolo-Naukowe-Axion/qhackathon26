# Catering production: a concrete dual-award proposal

Decision memo, 17 October 2026. Research and proposed problem definition, not an
executed VeloxQ experiment or a claim of industrial deployment. The optional
offline algebra probe described below is a separate, much smaller model.

**Latest decision:** the user now selected catering as the direction to try.
The earlier factory-selected/catering-parked decisions below are historical.
Keep the implemented factory as a fallback. Catering remains one integrated
Stage 2 effort, with no independent VeloxQ side project. Codex owns the shared
foundation; four people then own methods under the
[async work allocation](CATERING_METHOD_WORKSPLIT.md) and
[common solver contract](CATERING_SOLVER_CONTRACT.md).

**Detailed ambitious design:** [Lunch under pressure — full specification](CATERING_AMBITIOUS_SPEC.md)
now defines an expanded proposal with explicit disposal, phase-aware WIP
continuations, interrupted cooking, ingredient/holding/power capacities, exact
QUBO equations, alternative encodings and implementation gates. It uses a
proposed 10:50–11:30 lunch-window outage instead of the earlier illustrative
09:30–10:10 interval. It supersedes this discussion memo where the assumptions
differ; none of those expanded mechanisms is implemented by writing the spec.
In particular its cumulative-capacity registers add to the earlier M+22/M+26
core formulas. Keep the measured 18/16-bit toy distinct from both full proposals.

## Recap refinement — strongest focused first version

### User clarification: retain the disruption

The user explicitly wants to retain the disruption/replanning scenario; asking
why it was included was not a request to remove it. It tests a different decision
from planning an empty kitchen: adapt to newly revealed demand/capacity while
preserving committed production. The illustrative09:30 time is not a requirement.
Declare event timing and frozen-state semantics before evaluating results; use
the idle-boundary outage policy already specified below. This clarification does
not reverse the decision to keep the factory as the main entry.

### Qubit accounting and reduction strategy

The only compiled catering instances remain18bits/93couplers (nominal) and
16bits/72couplers (outage-filtered). These are supplied-option algebra audits,
not the full kitchen or executed QAOA circuits. A direct register encoding uses
one circuit qubit per QUBO bit, excluding implementation-dependent workspace;
connectivity, depth and gate counts still require compilation. VeloxQ binary
variables are not physical qubits. The factory's28-qubit bridge is a different
model and does not establish a catering register size.

For the proposed direct option encoding, let M be the number of retained local
batch-program options. With bounded binary missed-demand registers, the base
register size is M + sum_d ceil(log2(D_d+1)); there are no further auxiliaries
in this direct squared-balance/pair-conflict core. The twelve nominal demand
groups in the flagship table contribute22missed-demand bits. The urgent order
adds two new demand groups of two lots each, adding four bits before boundary
substitution; it also changes the option domain. Residual demand after committing
started batches can lower these counts. Thus nominal M+22 and urgent M'+26 are
accounting formulas, not measured full-kitchen sizes. M/M' have not been compiled.
Keeping shared customer departures fixed is part of this count's scope.
The revealed event is classical input to a new solve, not a quantum register of
possible worlds. Nominal/event runs reuse a device; their qubit counts are not
added together. A joint stochastic/robust scenario model would be a different
formulation and could require additional variables.

For the four event variants, the base direct-register accounting before freezing
started work is:

| Event case | Full proposed register | Measured supplied-option toy |
|---|---|---|
| Normal day | M_normal + 22 | 18 bits |
| Urgent order | M_urgent + 26 | Not built |
| Cooker outage | M_outage + 22 | 16 bits |
| Urgent order and outage | M_both + 26 | Not built |

Each M is that case's own count of retained batch-program options; none of these
full counts is measured. The toy column describes a different, much smaller
demand/option domain and must not be substituted into the full-model formulas.
For a revealed-state replan, replace22/26by the sum of register lengths for the
actual residual demand after boundary substitution. Four runs need the largest
register of the four, not their sum. With the unmodified full direct encoding,
a140qubit ceiling leaves at most118option bits nominal/outage, or114with the
urgent order, before any extra implementation workspace. This is an arithmetic
condition, not evidence that the full kitchen fits those option limits.

Excess production is the current food-waste proxy. It does not establish actual
discarded/expired portions. An explicit disposal rule/quantity would need its own
semantics, coefficients and register accounting. Keeping the current excess
cost does not by itself add bits beyond the option selections; the chosen yield
and allocated lots determine each option's excess coefficient.

Use safe unary filtering (calendar/departure/freshness/skills), exact substitution
of committed decisions, and proved interchangeable-resource symmetries before
restricting choices. Only remove a dominated option when replacement preserves
coverage, all resource/boundary compatibility and objective. After any reduction,
combine the selected decisions with the committed plan and independently check
the complete kitchen outcome.

Complete tiny instances can target roughly18–28decision qubits as a development
goal, retaining active batch/yield/sharing/resource/freshness tradeoffs. There is
no guarantee every feature or a meaningful disruption fits that budget. A smaller
conditional neighborhood must be labeled as such, with outside decisions fixed
by exact substitution. Candidate caps, coarser time grids and shorter windows
restrict the original decision domain; measure their objective loss against a
broader independent reference. Binary indexing may reduce choice-register bits
but can introduce higher-order interactions or quadratization auxiliaries; it
is not a free QUBO reduction. Counter encodings may reduce couplers while adding
bits. Report both costs, coefficient ranges and circuit compilation resources.

The proposed scientific contribution is a measured representation/resource
tradeoff with verified scheduling value. Neither a large register nor deliberate
solver difficulty establishes originality, points or a VeloxQ advantage. No new
catering run, QPU call or VeloxQ call accompanies this clarification.

### Resource envelope supplied by the user

The user reports a maximum accessible physical device size of140qubits, with
possible simulation access to one H100 or a CPU with128GBRAM. Treat these as
planning assumptions, not verified bookings, free-memory measurements or permission
to provision remote compute. No hardware/backend identity, calibration, H100
variant or actual simulator performance has been confirmed by this exchange.

For a generic dense double-precision statevector, memory for the state alone is
16*2^n bytes:28qubits=4GiB,30=16GiB,31=32GiB,32=64GiB,33=128GiB.
This follows the [Aer memory model](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.StatevectorSimulator.html).
[NVIDIA lists H100 variants with80/94GB](https://www.nvidia.com/en-sg/data-center/h100/);
the actual available GPU capacity is unknown.32qubits may fit a single state on
those resources, but simulator workspace, stored diagonals, multiple vectors,
parallel jobs and repeated optimization evaluations reduce usable capacity/time.
33double-precision qubits leave no workspace in128GiB and exceed128decimalGB.
Single precision halves the state storage; any use must validate numerical results.
Symmetry-sector or tensor-network simulation can exceed dense-statevector limits
for suitable circuits, but has no generic140-qubit capacity guarantee.

Plan routine generic simulation around24–28qubits, then benchmark30–32only when
the exact circuit/implementation fits memory and the experiment budget. Begin
physical compilation assessments on a small useful18–28qubit core; device width
140is a ceiling, not a target or a guarantee of useful deep QAOA. Measure native
two-qubit gates, routed depth and actual calibration/connectivity before choosing
a physical run. No hardware execution is authorized by these resource assumptions.

The integrated plan remains a broader classical/QUBO model for native references
and possible VeloxQ, plus a small meaningful quantum core/neighborhood from that
same decision. Reduce exact redundancies first; measure the loss of any later
restriction. Keep active batch/yield/allocation/freshness/resource tradeoffs in
the quantum fixture, and compare against the identical restricted classical
problem plus a broader reference. This recommendation does not activate catering
or supersede the factory main entry. It also does not claim that the unknown
full catering register will fit32or140qubits.

The user requested a full reminder and the strongest catering version, without
reversing the factory decision. The recommended first catering core is joint
batch creation/yield selection, same-menu output allocation across customers,
and freshness-constrained equipment/worker scheduling, with customer departures
fixed as inputs. Only lots packed before their departure and within the declared
synthetic cook-end-to-departure age limit may serve demand. Unserved demand is
explicitly counted as missed lots, rather than silently moving departure times.

This deliberately narrows the older soft-lateness proposal below. With fixed
departures, prioritize missed confirmed lots, then excess produced lots, batch
count and changes to the unstarted plan; derive scalarization weights from
finite bounds. No separate lateness term is needed when successful allocations
must meet the fixed departure. The same quadratic demand-balance/resource-conflict
formulation applies, with individually invalid options filtered before encoding.

If soft departure delays are added later and each customer has one combined
handover, all of that customer's portions must use that shared actual departure
in freshness checks. Independent portion handover times would represent split
handover service and must not be described as a single customer departure.
That semantic choice needs explicit decisions/linking, not an unnoticed shortcut.

The proposed memorable result remains a tradeoff to demonstrate, not an outcome
already observed: a larger shared batch saves cooking/cleaning occupation but
may be too old for a later customer; smaller separate batches can preserve
freshness at a capacity cost. Compare a reasonable fixed-per-order/greedy batching
policy with joint planning, native raw-model CP and same-QUBO samplers. Keep
VeloxQ inside this one workflow and preserve its existing execution hold.

No new catering implementation or experiment accompanies this recap. The18/16-bit
audit remains the full extent of completed catering evidence.

## Reassessment after the later mentor response

The user subsequently supplied an [official response](STAGE2_MENTOR_FEEDBACK.md)
welcoming another domain when it adds genuine mathematical/algorithmic complexity,
value, originality and correctness. This reduces the earlier concern about
leaving MetalTech; it does not approve this particular kitchen formulation or
confirm simultaneous award eligibility. The original proposal below remains
a proposed direction, not a decision to replace the current factory entry.

The substantive distinction is endogenous production: choose batch yields and
allocate their output across customers, rather than only placing a fixed set of
operations. Demand balance couples those choices, while cooking/packing capacity
and freshness constrain timing. For example, one40-meal batch may share output
across customers, while two20-meal batches may fit freshness/departure requirements
at the cost of extra cooking/cleaning occupation. This tradeoff must be shown in
actual checked fixtures; it is not established by the story alone.

Current evidence is limited to the18/16-bit supplied-option audit. Both nominal
and outage toy optima have the same tuple (0,0,0,2), so this audit proves algebra
on those domains, not a useful disruption benefit or full-kitchen optimum.
The flagship optional-batch/worker/replanning model and exact counter alternative
are not yet implemented/evaluated. Coverage squares may create dense couplings;
there is no basis to assume this is a favorable VeloxQ instance family.

Updated recommendation: retain the verified factory as the current main entry.
Before any pivot, perform a bounded offline comparison that establishes a genuine
batch-sharing/freshness tradeoff, independent raw-model reference and correct
QUBO, with construction/variable/coupler costs. If pursued, catering should be a
controlled generalization or a replacement centerpiece in the same project,
not a detached VeloxQ side project. Select the best evidenced workload before
spending limited service usage. No new experiment or service call is made by
this reassessment.

## Recommendation

Build a central catering kitchen that **chooses production batches, shares each
batch across customer orders, and schedules cooking and packing under freshness
and departure constraints**. Replan after a new order or a resource outage while
preserving work already performed. Make production the central problem; dispatch
deadlines are inputs and vehicle routing is outside this version.

This is a credible candidate for both award categories, subject to the two
eligibility uncertainties below. There is no evidence yet that VeloxQ wins on
this formulation, or that this project is likely to beat the other teams.

The scientific question is: **which correct representation gives useful kitchen
plans within a response-time budget, and where does each solver become useful?**
The practical question is: **an order changed while lunch production was underway;
can we still fulfill the commitments without unnecessary extra production?**

## What the solver investigation actually establishes

The developers' [white paper, v2](https://arxiv.org/html/2501.19221v2) reports its
clearest distinction in large sparse QUBOs, alongside tests on dense graphs. It
does not certify optimality, and short cloud jobs can be dominated by API overhead.
This is vendor evidence, not a reproduced catering benchmark.

The public [benchmark repository](https://github.com/quantumz-io/velox-data) supplies
scripts, raw plotting data and small example instances; its README says larger
instances are available on request and some implementations remain proprietary.
It is not a full open solver implementation or a ready catering scheduler.

The [current SDK documentation](https://github.com/quantumz-io/veloxq_sdk/wiki/solvers-and-backends)
exposes repetitions, steps, backend selection and optional `init_state` samples.
Those controls support a cold-start versus previous-plan experiment, but actual
backend handling and account limits are not verified. Public capability is not
evidence that a particular token has access to each backend. No seed control or
warm-start benefit is assumed. The installed SDK and current public docs differ
in domain-handling details; pin and audit the exact version before execution.

The [railway application study](https://arxiv.org/html/2512.19340v1) finds a large
gap between a practical native ILP and direct QUBO approaches. QUBO construction
and interaction count become limiting. Its reported outcomes do not establish a
VeloxQ advantage over native scheduling optimization.

Inference: try medium-sized, bounded production decisions with explicit coupling
and coefficient accounting. Do not inflate a tiny problem to match a headline
variable count, assume sparse graphs are automatically easy, or claim that GPU
execution is quantum execution.

## Eligibility and prize scope

Challenge sections 5, 11 and 15 ask for a manufacturing/scheduling extension and
meaningful end-to-end VeloxQ integration. Central catering production is a
defensible scheduling connection, but its acceptance has not been confirmed.
Industry classification alone does not decide competition eligibility.

The locally cached **Regulations v5.10.2026**, section 6.1, and challenge section
15 name an overall award and a special VeloxQ award without an express prohibition
on one team receiving both. They also do not explicitly guarantee that possibility.
The current website links to the regulations, but this research could not retrieve
and compare the live PDF bytes. No organizer message was sent.

Prepared question:

> Does a central catering kitchen's production-scheduling problem, with shared
> cooking batches, equipment capacity, packing, freshness limits and customer
> departure deadlines, qualify for Stage 2 and Best Use of VeloxQ? Can the same
> project/team receive both the overall and VeloxQ awards?

The cached regulations have a three-minute video limit, whereas the detailed
challenge permits five minutes. Until clarified, a video within three minutes
satisfies both stated length limits. Do not let this discrepancy disappear from
the final submission check.

## Concrete flagship instance

All figures below are **synthetic design parameters**, not food-safety guidance,
measurements from a caterer, or a claim that these orders are schedulable.

Planning calendar: 07:00-13:30. Initial declared time grid: 10 minutes. Quantities
are lots of ten meals; quantities below a lot and continuous start times are
outside this first model. Perform a finer-grid reference on tractable instances
to quantify this choice's cost.

| Customer | Chicken menu | Vegetable menu | Pasta menu | Ready-for-dispatch deadline |
|---|---:|---:|---:|---|
| Office A | 40 | 20 | 20 | 12:00 |
| Office B | 20 | 30 | 10 | 11:30 |
| Office C | 10 | 10 | 20 | 12:30 |
| Office D | 20 | 20 | 20 | 13:00 |

Total: 240 meals, 24 lots. The same menu may be cooked in a batch serving more
than one customer. There are two preparation stations, two batch-cooking units,
one packing line and three identified workers. Each operation requires one
qualified worker for its declared attended interval. No recipe science, temperature
control, unmeasured carbon saving or medical claims are part of the model.

Each batch follows **prepare -> cook -> assemble/pack**. The complete local
program includes occupation intervals for its equipment and workers and a fixed
terminal-cleaning interval on cooking equipment. Cleaning is per batch, not an
arbitrary predecessor-dependent matrix. That keeps this first model correct and
avoids claiming unsupported cleaning semantics.

Choose batch yields of 10, 20 or 40 meals. A transparent initial duration table,
in minutes, is:

| Menu | Prepare | Cook, 10/20/40 meals | Pack per 10 meals | Maximum cook-end to customer handover |
|---|---:|---|---:|---:|
| Chicken | 10 | 20/30/40 | 10 | 60 |
| Vegetable | 10 | 20/20/30 | 10 | 60 |
| Pasta | 10 | 10/20/30 | 10 | 40 |

A start/end boundary uses half-open intervals. Packing cannot begin before the
batch is cooked. Each customer's allocated lots have explicit packing-completion
times. Customer handover is the later of its requested departure time and that
completion time: early finished portions wait, while late handover incurs tardiness.
Freshness is checked at that handover, including the early waiting period. Vehicle
availability and travel time are not modeled. Raw ingredients are initially sufficient in the first core; scarce raw
ingredients, finite holding buffers and cross-menu shared components are later
extensions, not already enforced properties of the first core.

Initial freshness limits are modeled quality parameters. They are hard constraints
in this synthetic problem. Soft late completion is allowed until the calendar
cutoff; output beyond the holding limit cannot serve demand. Packed meal surplus
is not assumed destroyed. Report unallocated output as excess stock; classify
disposal only when the model actually includes a disposal/expiry event.

At 09:30, independently declared event variants are:

1. No event (control).
2. Office B adds 20 vegetable and 20 pasta meals, due at 12:00.
3. Cooking unit 2 is unavailable 09:30-10:10.
4. Both events occur.

Use a packing-line outage as a separately declared sensitivity case, not an
unreported substitute if the oven outage has little effect. Add high-load cases
and permit missed-demand outcomes rather than silently discarding infeasible
instances. A native reference must establish which fixtures are feasible.

## Decisions, objective and information

Choose batch quantities, group compatible same-menu demand, assign equipment and
workers, choose operation times and allocate finished portions to customer demand.
The first core shares **same-menu complete batches across customers**. Sharing a
rice component across different menus requires an explicit material-flow/BOM
extension and must not be claimed for this core.

Use the declared lexicographic objective:

1. Minimize unfulfilled confirmed meal lots by the cutoff.
2. Minimize total lot-weighted ready-for-dispatch tardiness.
3. Minimize excess produced lots.
4. Minimize cooking-batch count.
5. Minimize changes to the previous unstarted plan, when a valid previous plan exists.

Always report the individual metrics and makespan alongside the integer
scalarization. Derive strict dominance weights from finite component bounds;
do not invent weights after inspecting held-out results. Forecast-driven optional
preproduction is outside this confirmed-demand first core. Demand arrivals are
revealed at their event times; no solver receives future event realizations.

Freeze completed work and continuing operations, including their resource
occupation after 09:30. The first core conservatively commits the **whole remaining
local program of every already-started batch**, including its future packing.
Those reservations and their allocated lots are boundary conditions; only fully
unstarted batches are replanned. Their delivery metrics remain fixed contributions
to the reported whole-kitchen result. Residual demand excludes those already
allocated lots. This is a declared restricted recovery policy, not unrestricted
reoptimization of the packing of a running batch.

A breakdown blocks affected future capacity. Do not
silently cancel an operation already running on the failed resource: the initial
outage fixtures must either place the failure at an idle boundary or explicitly
define the interrupted-batch disposition. Prefer the idle-boundary variant first.
The first fixtures must ensure that all preserved batch-program reservations are
compatible with the outage interval. Replanning partially committed batch suffixes
would require a further boundary-state extension and a new reference comparison.

## QUBO formulation to build

Use a **finite production-option model**. An option is one internally valid local
batch program: menu/yield, allocated customer quantities, equipment/worker choices,
grid times, packing completions and cleaning. It is not a complete kitchen plan.
Generate these from raw recipes and calendars without a full CP optimum teacher.
Record the generation cost. Aggregate interchangeable lots so physically identical
servings do not create factorially many duplicate options.

Let x_b select option b, a_db be the lots it supplies to customer/menu demand group
d, and u_d be bounded integer missed lots. The demand equations are:

    sum_b a_db * x_b + u_d = demand_d

Each u_d is encoded with a bounded binary register, including zero. If the chosen
encoding has duplicate representations, account for that in quantum state-space
and sampling comparisons. Each resource-conflicting pair of options (b,c) receives
a penalty x_b*x_c. Internally invalid options never enter the domain. An option
overlapping a fixed continuing operation is also invalid.

With nonnegative linear objective C(x,u), the core energy is:

    E = C(x,u)
        + P * sum_d (sum_b a_db*x_b + u_d - demand_d)^2
        + P * sum_(b,c in resource conflicts) x_b*x_c

All counts are integers. Feasible schedules have zero penalty, and any violation
has penalty at least P. All-missed is a feasible fallback for this core. If B bounds
the nonnegative objective over feasible assignments, P>B forces global ground
states to be feasible and objective-optimal within the declared option domain.
For the proof and implementation, it is simplest to use the sum of all nonnegative
bit-cost coefficients as a conservative B over the entire bit domain when those
coefficients are nonnegative, as in the tiny audit. A Hamming-distance change cost
can introduce negative expanded coefficients; retain its constant and bound its
nonnegative component before expansion, or use C0 + sum_i max(0,c_i) for a valid
expanded linear upper bound. Fixed boundary costs are constants in both comparisons.

The native CP reference should independently enforce demand equations and raw
optional resource intervals, rather than reading the QUBO's pair-conflict list.
An independent event checker reconstructs capacities, quantities, timing and metrics.
This formulation is exact only when every allowed local program is included.

Compare three representations where feasible:

1. Complete finite-grid option domain, with safe unary filtering.
2. Exact bounded partial-sum counters replacing dense demand-sum squares. These
   can trade more bits for fewer interactions; correctness and cost must be checked.
3. A clearly labeled capped option pool or restricted replan window. Compare its
   optimum with the broader raw-model reference to measure restriction loss.

Counter encodings and candidate caps are experiments, not established VeloxQ
improvements. Large candidate groups can create one-hot/coverage cliques, so a
sparse-looking scheduling story does not guarantee a sparse QUBO. Compute actual
nonzero coefficients, degree distribution, coefficient range, memory and build time.

## Role of each method

- A dispatch heuristic supplies a cheap feasible operational baseline.
- Native CP-SAT on the same declared model supplies reference solutions/bounds.
- SA uses the identical QUBO coefficients to isolate sampler differences.
- VeloxQ solves a complete medium-sized replan or a bounded large neighborhood.
- If the account permits it, the documented SDK SBM solver provides an additional
  same-service/GPU comparison. Availability and matched backend configuration
  must be verified before this is promised as an experiment.
- QAOA solves small complete core fixtures if they fit, or an explicitly exact
  conditional restriction of the same catering energy. Report which one it is.

Do not send every tiny quantum-sized neighborhood as a separate cloud job.
Measure whether one larger replan amortizes API overhead. If using fixed outside
decisions for neighborhoods, preserve every coupling to them through exact
substitution, including constants, and physically validate the whole schedule.

The SDK's optional initial states motivate comparing cold runs with a mapped,
checked repaired previous plan. A changed model requires a fresh variable map;
old bit positions are not stable identities. Backend acceptance, benefit and
actual work performed must be measured. Compare controls with the same initializer.

## Experiments that would make the integration convincing

Begin with default VeloxQ settings, then a small declared repetitions/steps grid
on TRAIN cases. Verify account limits before committing to a campaign. Retain
default and tuned results; give competing heuristics a documented tuning budget.
The test set remains unused for formulation/parameter selection.

Scale independent decision structure: number of customer/menu groups, batches,
eligible resources, time choices and congestion. Increasing meal counts while
keeping all batch decisions identical is not meaningful combinatorial scaling.
Proposed workload sizes are 4/8/16/32 customer orders, with compilation and
resource-capacity checks before solver calls. Actual resulting QUBO sizes are
measured, never padded to a target count.

Test nominal, urgent-order, outage and combined cases, with several independently
generated kitchen instances per cell. Compare identical instances and seeds/tapes
where supported. Repeated cloud calls are replicates, not guaranteed seed control.

Report: valid-sample rate; best feasible metric tuple; certified gap or reference
gap with the distinction preserved; time-to-first-feasible and time-to-declared
quality target where observable; complete response time; backend time; build time;
peak memory; and variation across repeated runs. Native CP and QUBO controls
must solve the same problem and get equivalent hints. Report raw and repaired
outputs separately, including repair cost and the repair-only baseline.
Record CPU/GPU hardware and allocation for every method. A remote-GPU versus
local-CPU latency comparison is a service-level result, not an isolated
algorithmic or quantum speedup. Compare both equal response-time budgets and
quality targets rather than treating nominal iteration counts as equal work.

Development acceptance targets, not predictions: a verified quantum/hybrid
complete small solution, exact or tightly bounded same-model references, and a
useful measured VeloxQ regime on larger cases. If native CP dominates all kitchen
cases, keep the result rather than manufacture a VeloxQ advantage. Explain whether
the backend adds useful solution alternatives, scalability or neither.

## What has actually been checked now

`scripts/probe-catering-design.py` is a small algebra audit: two menus, four
ten-meal demand lots, two ovens, one packing line, fixed local batch options,
bounded packing wait, mandatory terminal equipment cleaning, and an outage.
It exhaustively checks every bitstring against an independent resource-occupancy
checker. It is deliberately not the flagship component/worker model.

| Toy domain | Bits | Bitstrings checked | Minimum metric tuple (missing, tardiness, excess, batches) |
|---|---:|---:|---|
| Nominal, 14 supplied local options | 18 | 262,144 | (0,0,0,2) |
| Outage-filtered, 12 supplied options | 16 | 65,536 | (0,0,0,2) |

Every ground state is feasible; zero-penalty assignments exactly match the
independent checker; minimum energy equals minimum independently feasible
objective. These are exact option-pool checks, not arbitrary-start kitchen optima
or VeloxQ/QAOA performance evidence. All physical-QPU and VeloxQ calls are zero.

Evidence and retained source:
`output/catering-design-audit-20261017/report.json` and `source.py`.
Reproduce in a fresh directory with:

    .venv-stage2/bin/python scripts/probe-catering-design.py --output output/new-catering-audit

## Build order and jury story

1. Settle production-scope and dual-award eligibility; the question above is ready.
2. Implement the raw core and independent checker, plus tiny native references.
3. Compile the QUBO, prove its scope/weights and exhaustively test tiny fixtures.
4. Establish baseline, quantum and VeloxQ results on the same core before adding mechanisms.
5. Run the declared size/congestion/formulation experiments and held-out evaluation.
6. Present a real run, a source-backed result table and one disruption recovery.

The jury story should be: **the original fixed-job factory did not decide batch
quantities or share output across customers. Catering requires both, plus a
freshness/deadline tradeoff. We formulated those differences, measured the cost
of each representation, and established where each solver helps.**

The hypothetical demo starts at 09:30 with the event already revealed. A user
selects the event, a fresh solver run returns a schedule, and an independent checker
shows quantity/resource/age validity and delivery metrics. Saved traces are
separately labeled. Report excess portions and late orders, not unmeasured
environmental or health outcomes.

Prior kitchen optimization research exists, including the
[ghost-kitchen study](https://arxiv.org/abs/2408.07417). It supports the practical
problem type, not novelty or performance claims for this new formulation.

Existing VeloxQ and physical-QPU holds are unchanged. This work uses public
research and offline local checks only; it does not request a token, contact
organizers, submit a remote job, commit, publish or deploy the proposal.
