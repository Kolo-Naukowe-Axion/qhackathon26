# Classical reference design for the quantum-first catering project

17 October 2026. The active extension is paired-course v3, retaining the
corrected repair-clean v2 physical policies. The lower sections document the
base raw scheduling model; the following additions define whole-meal scoring.
The classical track establishes reference values, checks the formulation and
measures any loss from restricting quantum inputs. Quantum samples decode to
their own schedules; the reference solver does not finish or repair them.

## Current V3implementation and retained evidence

`native_slots.solve_native` now introduces a classical Boolean completion flag
for each meal and enforces complete=main_covered AND side_covered. U counts
weighted incomplete meals; W adds main+side-2*complete for unpaired waste.
These are classical CP variables, not additional QUBO or hardware qubits.
The emitted plan is independently checked for actual complete handovers,
unpaired disposal and per-batch material balance. Mandatory repair cleaning
and disabled aggregate/phase-aware mechanisms are unchanged.

`meal_reference.solve_bundle` minimizes the same offered quadratic objective
with exact one-hot and crossing-conflict constraints. The compiler's full-span
penalty proof makes its optimum equal the literal QUBO ground energy. This
reference reads the shared graph; distinguish it from the raw reference that
does not enumerate programs or read QUBO conflicts. Exact sector enumeration
also covers the small quantum portfolios. Existing literal SA supports the
new objective without repair.

`output/catering-foundation-v3/` freezes four6customer inputs, exact raw tuples
S0=(2,0,6,6),S1=(3,0,5,5),S2=(2,1,6,6),S3=(3,1,6,6), plus nested fixed
quantum/128/256bit restrictions. Their reference statuses/gaps are per-file;
an offered-domain optimum is not a raw optimum. The separate complete35qubit
cell at `output/catering-complete-cell-v3/` has no option cap and certifies
(0,0,2,2) using raw CP, offered CP, independent subset checking and sector
enumeration. It is deliberately classically easy. The larger QAOA pilot is
retained with negative quality gaps; neither experiment establishes quantum
or VeloxQ superiority. Reproduce and verify using catering/README.md.

## 1. Three reference tasks

| Task | Question | Implementation/status |
|---|---|---|
| Raw kitchen reference | What is the best plan in the full declared physical domain? | Implemented: catering/native_slots.py, direct CP-SAT |
| Exact encoded reference | What is the best answer to the precise input given to quantum? | Implemented for small cases: literal exhaustive QUBO enumeration and independent raw selection audit |
| Same-QUBO heuristic | What does a generic classical sampler return on those exact coefficients? | Implemented: catering/methods/classical.py, seeded Metropolis SA without repair |

These answer different questions. A raw optimum is not a ground-energy claim
for an arbitrary restricted QUBO. A restricted ground state is not an optimum
of the broader kitchen. SA is a heuristic control, not an optimality certificate.

The fixed-per-customer comparison uses the same CP model with cross-customer
batch sharing disabled. This is an operational policy ablation, not a deliberately
weak greedy algorithm or evidence that one solver is better than another.

## 2. Inputs and scope

Use the exact versioned instance and observed snapshot provided to the quantum
track: recipes, allowed yields, grid/horizon, demand groups and priorities,
departures/reveal times, calendars, qualified staff, committed batches, previous
unstarted programs, outages and mandatory recovery operations. Record both hashes.

The current complete domain is core-contiguous-repair-clean.v2. It freezes the
whole future program of started batches, uses contiguous packing by one worker,
immediate terminal cleaning, and a fixed earliest-compatible recovery-clean
policy. This is a declared restricted physical policy, not arbitrary packing
or the ambitious phase-aware kitchen. Ingredient/holding/power capacities and
money are disabled. The raw reference must reject unsupported features rather
than ignore them. Changing the physical policy requires a new matched release.

Subtract committed allocations from demand for the new-decision equations.
Some of those allocations are future handovers; they are reserved by the
conservative policy, not already delivered meals. Replay completion is separate.

## 3. Direct CP-SAT formulation

### Batch slots and decision variables

For menu m, let D_m be its total residual demanded lots. Create D_m optional
batch slots. This is an exact bound: every active new batch must serve at least
one residual lot, so a feasible solution cannot need more than D_m batches.
These are integer/Boolean solver variables, not a qubit-count estimate.

For each slot b choose:

- Active flag z_b, allowed yield y_b, served quantity q_b and surplus w_b.
- Prep, cook and packing start times; phase ends follow recipe durations.
- One preparation station, one cooker and an eligible worker for each role.
- A contiguous prefix of used packing positions, each assigned to one same-menu
  demand group. Position assignments encode both quantities and packing order.
- Indicators of an exact match with each relevant previous unstarted program.

The direct model builds these decisions from raw input. It imports no option
generator, QUBO compiler or QUBO conflict list. The independent checker evaluates
the decoded operations, allocations and disposals, not the CP constraints.

### Quantity and timing constraints

With inactive slots forced to zero quantities:

    z_b <= q_b <= y_b
    w_b = y_b - q_b
    sum of assignments to group d + missed_d = residual_d

Yield/cooking-duration tables enforce allowed batch sizes. New operations start
on or after the snapshot time and finish within the horizon. Cooking follows
preparation. The cooker clean starts immediately at cook completion. Packing
starts after cooking; successive used positions are consecutive recipe-length
intervals. Each assigned position must finish by its customer's departure and
start no earlier than the demand reveal. At departure, cooked food must be no
older than the recipe's freshness limit. No demand can be served twice.

Use optional intervals and NoOverlap for equipment and attended worker time.
Cooker occupation includes the full cook plus terminal clean. Cook attendance
can be shorter than cooking; its worker is released after attendance. Prep,
packing and cleaning require attendance throughout. Overlapping resource roles
of one worker remain mutually exclusive. Each individual operation must fit one
declared calendar window, even if two windows touch. Half-open boundaries allow
one operation to finish exactly when another starts.

Reserve committed operations, actual worker attendance, calendar closures,
outages and recovery-clean equipment/worker intervals. Block the cooker while
it awaits its recovery clean as well as during the clean itself.

### Objective and exact priorities

Minimize lexicographically:

    U = sum_d priority_d * missed_d
    W = committed surplus + sum_b w_b
    B = sum_b z_b
    R = |previous programs| + B - 2 * retained_exact_programs

R compares semantic program identities, not interchangeable CP slot labels.
Retention requires identical menu, yield, times, resource/worker assignments and
allocation order. It is not a loosely defined count of changed batches.

The current implementation uses an exact integer scalarization. Starting at
w_R=1, choose each more important weight greater than the largest possible
weighted contribution of every lower-priority component. Checked finite bounds
make this equivalent to lexicographic optimization. Reject coefficients outside
the conservative integer range. If a larger future model exceeds that range,
use sequential component optimization; do not silently weaken the priorities.

Weights can differ between raw and encoded models because their bounds differ.
Compare the operational tuples across models. Compare literal energies only
within the same QUBO identity, including its constant and energy scale.

### Why this covers the declared domain

Map each feasible new batch into an optional same-menu slot; the slot bound
above suffices. Copy its times, yield, worker/resource choices and ordered
allocations. The direct constraints accept those values. Conversely, every
active slot reconstructs one legal local batch; global resource and demand
constraints produce a valid full plan. Sorting interchangeable same-menu slots
by prep time only breaks labeling symmetry. It does not remove physical plans.

This argument covers the stated grid and fixed recovery policy. Agreement with
small exhaustive cases supports the implementation, not a proof of every
possible future extension.

## 4. Mandatory post-repair clean and expected regression answers

The clean is required even when no later C2 batch is selected. It takes ten
minutes of C2 and a qualified worker. In the current fixture, W2 cleans A during
60–70, so the fixed recovery policy reserves W2/C2 during 70–80. New C2 cooking
cannot start before 80. C1 becomes usable at 70.

| Case | Exact U,W,B,R | Meaning |
|---|---|---|
| S0 | 0,0,1,0 | Retain the original new B batch |
| S1 | 0,0,1,2 | Share a two-lot B batch across the two departures |
| S2 | 1,0,0,1 | Miss the nominal B order; still perform recovery cleaning |
| S3 | 1,0,1,2 | Serve only the urgent B order, using C1 |

These are frozen correctness cases. In S2, the earliest available cooker is
C1 at 70: twenty minutes of cooking plus ten of packing finishes at 100, after
the nominal departure at 90. C2 cannot offer an earlier finish. This provides a
simple independent explanation of the missed-order result.

Optimizing the time/worker of recovery cleaning is a future physical-profile
extension. Do not let the classical reference optimize that freedom while the
quantum model fixes it, or compare the resulting values as equal-domain results.

## 5. Reference on the exact quantum input

Use the frozen bundle without changing variables, coefficients, constants,
penalties, coverage or candidate options. For at most 22 bits, enumerate the
literal QUBO exactly with the existing integer-range checks. For the tiny
physical audits, independently enumerate potentially feasible option subsets
and check their raw plans; the current helper supports at most four residual
lots. Neither limit is a claim that larger instances are impossible to solve.

For the unit-demand conflict representation, feasible selections are independent
sets. A future larger exact adapter can branch on select/exclude decisions and
prune conflicting neighbors. It must derive/check physical compatibility and
its objective bound; a timeout returns an incumbent and bound, not an optimum.
This adapter is optional further work, not an implemented benchmark result.

The older optional-interval program master remains valid for the original
missed-register encoding. It explicitly rejects the newer coverage-reward
encoding, because separately adding missed cost would double-count service.

Report three values when certified:

    full physical optimum <= exact restricted optimum <= best valid quantum return

The ordering is lexicographic on the same (U,W,B,R), under matching physical
semantics. The first difference measures representation loss; the second
measures search loss within that representation. Report the first differing
component and the full tuples. Do not interpret later component differences
as independent improvements when an earlier component is worse.

If the raw reference is time-limited, retain its incumbent/bound and leave the
full representation gap unresolved unless those bounds suffice to certify it.
An incumbent alone must not be labeled the full optimum.

For the current quantum-first prototype, the complete reference is (0,0,2,2),
while caps 8/12/16/20 have exact value (1,0,2,2). The lost lot is caused by the
restriction before quantum runs. Classical reference values must not be used
as an optimal-plan teacher for constructing the evaluation option pools.

## 6. Heuristic control and experimental protocol

Keep the existing same-QUBO SA baseline small and reproducible. It uses seeded
random bits, exact integer flip deltas, a declared annealing schedule and restart
count, and no feasibility repair. Decode every returned best-of-restart state.
Its return-validity fraction is not the validity of every visited state and
must not be presented as comparable to every quantum measurement shot.

For each frozen evaluation case:

1. Validate input hashes and the committed/recovery boundary.
2. Run the raw reference and record whether optimality is certified.
3. Compute the exact encoded reference wherever the declared audit permits.
4. Run the declared SA control and each method on the identical bundle.
5. Independently decode/check returns and publish all failures/timeouts.

Default small reference budget: ten seconds, one local CPU worker, seed 2026.
This is a cap, not a required runtime. Use predeclared separate settings for
larger references; do not artificially handicap classical solvers to create a
quantum win. A three-second timeout or a difficult penalty landscape is not a
classical-hardness certificate. No H100, WCSS allocation or external service is
needed for this design or the current small fixtures.

Keep two timings: the raw pipeline build/search total and algorithm search
time. Current raw CP timing excludes SDK import/process startup; label that.
Record actual wall time, worker count, seeds, objective evaluations or flip
proposals, and quantum shots/circuit work separately. Equal wall time and equal
sample counts answer different questions; do not pretend they are interchangeable.

## 7. Outputs, status and reproduction

Every reference row records case/profile/input identity, full versus restricted
scope, method/version/settings, independently checked plan, U/W/B/R, solver
status, scalar objective/weights and bound, timing and work counts. Same-QUBO
returns also use the shared bundle hash, semantic bit order and literal energy.

- OPTIMAL certifies the optimum only within the recorded model/domain.
- FEASIBLE provides a checked incumbent; retain the bound separately.
- UNKNOWN provides no solver solution; a separately checked fallback must be
  labeled as a fallback rather than attributed to the solver.
- INFEASIBLE is a solver conclusion for that model. Failure to obtain a valid
  sample is not such a conclusion. MODEL_INVALID is a model error.

Current raw CP and exact/SA controls are implemented and covered by the
32-test catering suite. No new classical solver or quantum experiment is
claimed merely by this design document.

    .venv-stage2/bin/python -m unittest discover -s tests/catering -v
    .venv-stage2/bin/python -m catering.native_slots --scenario S3 \
      --seconds 10 --workers 1 --output /tmp/NEW-catering-S3.json
    .venv-stage2/bin/python -m catering.benchmark_classical \
      --small-only --seconds 3 --output output/NEW-classical-check

Fresh output paths are required. Current checked small results are in
output/catering-classical-v2/; common inputs are in
output/catering-foundation-v2/. Old v1 outage answers are superseded. Preserve
their provenance rather than merging them into the corrected comparison table.

The implementation order is deliberately limited: use the existing raw CP,
exact audit and SA controls now; integrate method returns; add a larger exact
adapter only if a released quantum case needs it. Quantum encoding, circuit
design and the main workload remain the project's central work.


## Current local reference and integration status — 17 October

The V3 classical foundation is implemented, not waiting on a new compute allocation.
`output/catering-foundation-v3/` has independently checked raw CP optima for all four
six-customer scenarios and same-offered-input references/SA. The complete small
35-bit cell agrees across raw CP, offered-domain CP, subset audit and sector
exhaustion at (0,0,2,2). The new 12-customer S3 scale release has finite five-second
references (FEASIBLE/FEASIBLE/UNKNOWN at 512/1024/2048); no optimum is inferred.
See [the scale handoff](VELOXQ.md) for the measured tuples and workload scope.

The V3 game viewer exposes the raw versus offered-domain distinction and shows
all eight larger quantum pilot gaps. The standard raw decoder/checker remains the
acceptance gate for the other owners' returns. Current verification: 45 Python
catering tests (one optional SDK test skipped in the lightweight environment),
with the SDK circuit-equivalence test available in the quantum environment.


A second predeclared local pass now exists in output/catering-classical-scale-v3/:
30seconds/reference, one worker, seed2026, plus2seconds of cold raw-bit SA per
frozen scale bundle. Raw CP FEASIBLE(5,1,11,11); same-offered CP returns FEASIBLE
(6,1,10,10)/(7,2,11,11)/(8,3,8,8) at512/1024/2048. Cold SA's returned states include
valid weak incumbents at512/1024 and no valid return at2048. No optimum or backend
advantage follows. The longer experiment preserves the original five-second
receipts, uses the same bundle hashes, reports call/loading/solver time separately,
and never feeds its plans to quantum initialization. Reproduce with
python -m catering.benchmark_meal_scale --output output/NEW-CLASSICAL-SCALE.
