# Stage 2 planning core — development evidence, 17 October 2026

**Scope update, 17 October:** this document explains the earlier factory/planning study. The newly authorized manufacturing recovery entry, complete assignment-sector QAOA results and current rubric evidence are in [STAGE2_ENTRY.md](STAGE2_ENTRY.md). Original outcomes below remain unchanged.

The new optimization core formulates complete deterministic pump/BOM scheduling
cells as QUBOs, verifies their schedules against a raw interval CP model, and
measures exact reductions, restricted trajectory encodings and actual simulated
QAOA circuits. The strongest measured full physical factory controller remains
the previous classical incumbent. Neither new advisory integration is promoted.

[Interactive schedules and encoding comparison](http://127.0.0.1:4187/stage2/planning.html)
are separate from the frozen final campaign. See also
[view provenance](STAGE2_PLANNING_VIEW.md).

## Declared scheduling model and certificate

Each assignment bit selects an operation, alternative machine, qualified worker
and integer-grid start. Full pump cells contain all housing, rotor and flange
recipes, a three-parent assembly join and final pump QA: **16 operations per
pump**. Calendars include shifts and breaks; attendance is start-only or full;
worker hall travel must fit a working interval. Machine-dependent part-transfer
minimum lags, machine-dependent initial delivery releases and due dates are
explicit. The boundary state is a declared hypothetical raw backlog, rather
than an observed full-factory state.

The integer objective is `(H+1) * weighted terminal tardiness + makespan`.
Every operation and the makespan register have one-hot constraints. Resource
occupation, travel, precedence and makespan links are quadratic pair penalties.
The nonnegative objective is bounded above by `B` over feasible assignments;
the compiler uses `P=B+1`. Every violated constraint costs at least `P`, so if
the instance is feasible, every global ground state is feasible and
objective-optimal **for this declared discrete model**. Upper-triangular
coefficients are counted once.

This is not a lossless encoding of the physical simulator. Capacitated/empty
AGV motion, buffers, portable tools/service, power, batching, stochastic quality
and recovery are excluded. Final QA is not shipment. Those mechanisms remain
active in the separately checked full-factory executions.

`stage2/window_qubo.py` contains the compiler, independent raw schedule checker,
raw native interval CP reference, literal unconstrained-QUBO CP reference and
exact conditional-energy substitution. Native CP never receives the QUBO
coefficients or compiler conflict list. The literal solver sees only the
energy coefficients. A literal solver reporting FEASIBLE is not relabeled
OPTIMAL merely because its returned schedule matches the independently proved
raw CP optimum.

## Exact reductions and price of realism

`window_reduction.py` removes an assignment only when another mandatory
operation has no compatible remaining assignment. Fixed-point arc consistency
preserves **all feasible schedules**, without an incumbent or objective oracle.
Makespan values unsupported after pruning also disappear.

| Pump cell | Operations | Unary-domain baseline bits | Support-pruned bits | Couplers after pruning |
|---|---:|---:|---:|---:|
| 2 pumps, H1440, grid60 | 32 | 2,359 | 1,189 | 103,680 |
| 2 pumps, H1440, grid30 | 32 | 4,223 | 2,512 | 401,472 |
| 3 pumps, H1920, grid60 | 48 | 4,564 | 3,055 | 457,719 |
| 4 pumps, H1920, grid60 | 64 | 6,007 | 3,941 | 650,912 |

The baseline already prunes individual illegal calendar/skill/time choices.
It is not a count of all possible machine × worker × time combinations, nor a
universal minimum representation.

Machine-only family changeovers have a useful exact compact encoding when the
directed setup matrix satisfies the triangle inequality and machines have
uninterrupted availability. Enforce the setup gap for every time-ordered pair
on the same machine. Adjacent pairs enforce the actual transition. For
nonadjacent pairs, the sum of intervening adjacent setup times is at least the
direct setup time, so those extra inequalities cannot remove a legal schedule.
Initial-family transitions use the same argument. Nonmetric matrices and
unsupported machine calendars are rejected, rather than silently overconstrained.

This adds **zero binary variables**, although it adds couplers. Human setup
crews are not modeled: these are machine-only/automated changeovers, using the
factory's actual transition durations.

| Same 32-operation cell | Bits | Couplers without / with changeovers | Raw CP optimum without / with changeovers |
|---|---:|---:|---:|
| grid60 | 1,189 | 103,680 / 105,434 | 1,946,535 / 1,946,535 |
| grid30 | 2,512 | 401,472 / 408,990 | 1,254,585 / 1,254,585 |
| grid15 | 5,443 | 1,629,385 / 1,664,149 | 887,055 / 908,670 |

All six are proved OPTIMAL, with encoded CP plans independently checked in
their QUBOs. The whole experiment takes 65.72 seconds and 1.52 GB peak RSS.

Finer native CP references with changeovers prove **793,320 at grid5** and
**787,555 at grid1**, in 5.76 and 9.71 seconds. Peak RSS is 2.38 GB. No enormous
fine-grid QUBO is constructed: grid1 already has 115,878 unary assignment
candidates before support pruning. The grid15 setup optimum is 15.38% worse
than the minute-grid optimum; grid30 and grid60 are 59.30% and 147.16% worse.
Start-grid coarsening is a real, measured accuracy loss and must not be labeled
an exact qubit reduction.

Evidence: `output/stage2-search/window-pump-campaign-mac-v1/`,
`window-setup-costs-mac-v1/`, `window-fine-grid-mac-v1/`.

## Conditional QAOA and restricted trajectories

`planning_quantum.py` substitutes fixed bits into the **same complete planning
energy**, including the constant. Small local circuits therefore optimize an
exact restriction, rather than a substitute dispatch reward.
`planning_compressed.py` additionally replaces a two-choice one-hot pair by
`x_a=1-z, x_b=z`. This affine reduction keeps the polynomial quadratic and
preserves every one-hot assignment of that local neighborhood. All fixed-bit
and candidate-selection work is classical and recorded.

Random three-operation blocks failed to improve their initial full-pump plans;
even exact block optimization did not improve them. A guided, plateau-accepting
pilot also remained stuck. These are search failures, not evidence that QAOA
finds global optima. The 64-operation heuristic initializer fails altogether,
despite the raw CP reference finding a feasible schedule.

`trajectory_qubo.py` explores a different representation: one bit per order
chooses between two **classically generated complete internal pump schedules**.
Cross-order resource conflicts and the makespan register remain QUBO terms.
Every supplied trajectory is independently internally checked, and every
restricted pattern selection is checked against the raw schedule model.

| Cell | Restricted master | Exact restricted-pool objective | Full raw CP reference | Restriction loss |
|---|---:|---:|---|---|
| 32 operations, grid60 | 5 bits / 6 couplers | 2,119,575 | OPTIMAL 1,946,535 | 8.89% |
| 32 operations, grid30 | 5 bits / 5 couplers | 1,384,365 | OPTIMAL 1,254,585 | 10.34% |
| 48 operations, grid60 | 8 bits / 16 couplers | 4,295,100 | FEASIBLE 3,603,360 plus recorded bound | 19.20% above the CP incumbent; full optimum unresolved |
| 64 operations | No master accepted | — | Feasible raw CP schedule exists | Two heuristic parents not found |

These are **restricted pools**, not a way to retain thousands of arbitrary
scheduling variables losslessly in five qubits. Two parent trajectories per
order mean only `2^orders` recombinations. Their classical construction is
substantive work, and classical enumeration of these tiny masters is easy.
All actual QPU calls and GPU hours are zero. The initial parent rule selects
the first two distinct feasible heuristic parents, without a CP optimum teacher.

Evidence: `trajectory-master-mac-v2/`. The failed v1 experiment, including its
driver error, remains separately retained.

## Circuit redesign inspired by the linked paper

The useful transferable idea in [Gu et al.](https://arxiv.org/abs/2610.22367)
is to compare different representations and circuits with an independent
correctness evaluator and explicit resource accounting. Their reversible
arithmetic/decoder circuits are not a scheduling solver to download. We do not
use Anthropic services or reintroduce autoresearch.

`trajectory_mixer.py` prepares a uniform single-excitation W state for the
makespan register and uses an ordered XY chain mixer. Order-choice bits retain
the X mixer. This preserves makespan one-hot exactly; incompatible resource
combinations still carry their original penalties. The one-hot penalty, zero
throughout the reachable subspace, can be removed from the phase circuit.
Preparation gates are included in all reported resources.

On the eight-qubit/48-operation restricted pool, across seeds 7/13/29:

| p2 method | Single-shot pool-optimum probability | Compiled CX count | Compiled depth |
|---|---|---:|---|
| Standard X QAOA | 0.4826% each seed | 64 | 67 |
| XY/W QAOA | 19.2330%, 18.4550%, 2.5826%; mean 13.4236% | 48 | 81–83 |
| Classical uniform within one-hot domain | 2.5% | — | — |

The XY mean is 5.37× the stronger uniform control's single-shot concentration,
and the actual 32-shot draws hit the pool optimum for all three XY/p2 seeds.
This is a small exploratory comparison, not a runtime advantage over classical
optimization. Training uses **64 exact simulated expectation evaluations**;
these are not 64 physical measurement shots. All statevector/energy-table and
angle-search costs are classical and retained. Classical exact controls remain
trivial at this size. On the five-qubit cases p1 XY costs more CX gates, and p2
CX counts are equal; there is no blanket gate-count improvement.

Independent Qiskit replay verifies all 36 emitted X/XY circuits and their
logical transpilation, with maximum probability discrepancy below 2.84e-15.
An earlier 48 planning-block circuit audit also passes. Logical resource counts
use all-to-all connectivity and basis RZ/SX/X/CX, not an ODRA calibration/routing
model. No physical-device feasibility claim follows from qubit count alone.

Generic density-matrix noise tests retain the ideal-trained angles and include
144 circuit/channel combinations. For the eight-qubit p2 case, mean XY ground
probability changes from 13.42% ideal to 11.94%, 10.22% and 7.84% in the three
declared noise settings. These use Aer depolarizing channel parameters, not
measured gate infidelities; they omit relaxation, crosstalk and device routing.
They are sensitivity tests, not hardware predictions.

Evidence: `trajectory-mixer-mac-v1/`, `trajectory-circuit-audit-mac-v1/`,
`trajectory-noise-mac-v1/`.

Time-indexed scheduling and variable pruning follow established methodology,
including [Venturelli et al.](https://arxiv.org/abs/1506.08479).
Constraint-preserving alternating mixers are established by
[Hadfield et al.](https://arxiv.org/abs/1709.03489); we do not claim their invention.

## Full-factory integration is not promoted

`window_factory.py` extracts actual public-state prefixes without future tape
access. It preserves the configured strong factory adapters and subjects all
execution to the original physical and identity checkers. Suggested starts and
workers are predictions, not committed physical plans.

The first routing/priority override fails badly on two development seeds.
A softer priority tie-break preserves routing but also fails validation.
On **16 fresh seeds 50000000–50000015**, all 48 physical traces pass checking:

| Method | Mean missing orders | Mean terminal deadline debt | Mean measured run time |
|---|---:|---:|---:|
| Existing strong static recovery controller | 1.4375 | 7,576.9375 | 0.881 s |
| Soft constructive window advice | 2.1250 | 8,650.9375 | 2.671 s |
| Soft compressed QAOA window advice | 2.1250 | 8,650.9375 | 3.419 s |

The quantum and constructive methods have identical shipment/debt results on
all 16 seeds. Physical validity does not imply full order fulfillment. The
short-prefix objective omits whole-factory consequences and is not a suitable
replacement for the incumbent. All bad trajectories are retained; these
fresh validation tapes are not added to the earlier frozen final estimates.

Evidence: `window-integration-mac-v1/`, `window-integration-mac-v2-soft/`,
`window-soft-validation-mac-v1/`.

## Reproducibility and next decision

Campaigns copy literal sources before running, record package versions and
input/coefficient hashes, check source stability and seal file manifests.
The first two exploratory window runs retain source hashes but lack copied
source snapshots; they are historical prototypes, not the primary reproducible
claims above. Small tests exhaustively compare ground states, raw schedules,
conditional energies and affine reductions. Thirty additional randomized small
DAG/calendar/crew/setup instances agree with native CP and preserve every
enumerated feasible schedule through pruning.

The current research direction is broader **component-trajectory pools**:
retain cross-component BOM precedence, compare restricted-pool optimum and
raw-model reference, and use small conditional circuits to search a larger
global master. Merely shrinking a two-parent master further would not make
its combinatorial search domain ambitious. New work must improve either the
quality/qubit frontier or full-factory behavior before being promoted.

### Subsequent component-pool diagnostic

`component-columns-mac-v1/` now constructs the broader masters, starting at
128 operations/32 component groups and stepping down. Eight independently
checked global heuristic parents produce a250-bit/4,453-coupler master for the
128-operation cell. Its formal unconstrained pattern product is very large,
but that number must not be confused with the number of compatible schedules.

An independent native optional-interval/precedence/crew/setup model in
`column_reference.py` proves each retained component pool optimal in0.02–0.21s.
**Every pool optimum equals its best already-known parent.** The generic
unconstrained-QUBO solver can return worse schedules within15s; these are not
promoted over the parent incumbent. Larger bit counts alone did not create a
useful new search problem.

`component-columns-enriched-mac-v1/` adds raw-checked route-suffix time shifts,
with24/48 columns per component. Across all four sizes, the native restricted
reference still proves no improvement over the best parent. The largest master
has1,429bits/175,399couplers; there is no justification for spending QAOA
simulation compute on these unchanged optima. Those negative results remain
retained. Next candidate generation must add useful machine/worker/time
flexibility, rather than simply more copies of rigid parent trajectories.

The original pilot guarded/skipped its128-operation raw reference. A subsequent
complete raw reference was actually attempted, followed by the compact model
below. The original skip remains historical evidence, not the current result.
Raw same-model optima for the smaller64/48/32-operation cells are
1,945,958 /1,297,680 /908,670. All are deterministic grid15 cells with
machine-only metric setups, under their recorded different horizons.

### Complete native reference with shared walking functions

`component-raw-reference128-mac-v1/` first tries the complete128-operation raw
table model with a checked heuristic hint and120s solve budget. It returns
UNKNOWN, no new feasible solution and a zero lower bound. The known heuristic
parent remains valid; UNKNOWN does not make the instance infeasible.

`window_interval_reference.py` instead derives exact unions of start-grid
intervals for each eligible machine/worker mode directly from raw calendars.
It does not read the QUBO, compiled conflicts, restricted columns or the compiler's
assignment generator. Native occupation, raw BOM/transport, metric setup and
worker hall travel constraints remain. A piecewise function gives the earliest
completion of a required walk after each operation's attended end. Sharing this
function per operation/worker replaces one calendar-slot disjunction per pair.
It retains exactly the same raw walking condition, including breaks and the
case where no remaining calendar interval can fit the walk.

Forty additional randomized small problems compare every analytically generated
mode domain with raw unary enumeration, and compare the compact optimum with
both exhaustive complete schedules and the previous native reference. A separate
exhaustive boundary test checks the shared walking function against the original
calendar condition, including intervals shorter than the walk.

| Raw grid15 cell | Compact v2 status | Objective / feasible upper bound | Certified lower bound |
|---|---|---:|---:|
|32 operations, H1440|OPTIMAL|908,670|908,670|
|48 operations, H1920|OPTIMAL|1,297,680|1,297,680|
|64 operations, H2880|OPTIMAL|1,945,958|1,945,958|
|128 operations, H4320|FEASIBLE|15,951,151|7,626,567|

The128-operation solve uses120s plus model construction. The shared-function
revision reduces its native variables414,442→46,498 and construction3.00s→0.34s.
The complete four-cell campaign records137.90s wall/522.96 process CPU seconds
and1.405GB peak process RSS, versus6.741GB in the previous native revision.
The earlier128-operation feasible schedule20,812,381 and bound5,033,967 are
retained. These are model-implementation comparisons, not a quantum speedup,
and the concurrent CPU conditions are not a normalized solver benchmark.

Evidence: `component-compact-reference-mac-v1/` and `-v2/`. The raw128-operation
quality gap is still wide. No bound in this section applies to the complete
stochastic physical factory or to a finer time grid.

`component-reference128-refine-mac-v1/` subsequently continues the same raw
problem for600s, using the previous reference's own checked feasible plan as
a disclosed hint. It finds13,941,691 with lower bound8,071,630, still FEASIBLE.
The independent checker reconstructs weighted terminal tardiness3,226 and
makespan2,145, giving4321·3226+2145=13,941,691. This is35.23% below the original
heuristic parent, but its solver-certified relative interval gap remains42.10%.
The run records600.57s wall/2363.21 process CPU seconds and1.322GB peak RSS.
The operation-pool optimum below is therefore **40.45% above this newer raw
feasible incumbent**; its22.76% comparison is explicitly the older compact-v2
snapshot, not a current tight quality claim.

### Operation pools recover flexibility, with measured loss

Machine/worker-flexible component suffix pools in
`component-columns-flexible-mac-v1/` and `-v2/` mostly remain parent-optimal.
The first32-operation pool improves makespan by75 objective units; broadening
its strategy changes which candidates survive the cap, so v2 is not a nested
superset and does not retain that gain. All originals remain in both pools.

`operation_columns.py` instead retains every complete parent assignment and
adds nearby unary-feasible rows in round-robin machine/worker mode order. Each
operation is independently selectable; routes are no longer frozen as a single
component trajectory. The global one-hot QUBO still penalizes all raw BOM,
occupation, setup and walk incompatibilities. This is exact within the retained
finite pool, a deliberately lossy restriction of the full raw assignment domain.
Neither the raw CP optimum nor its plan enters candidate construction.

|Operations|Pool QUBO bits / couplers|Best heuristic parent|Proven pool optimum|Reference loss|
|---|---:|---:|---:|---|
|32|1,489 /112,060|1,124,895|908,670|0% on this grid15 instance|
|48|2,265 /174,001|1,758,795|1,470,600|13.33% above proven raw optimum|
|64|3,054 /242,677|2,853,473|2,637,398|35.53% above proven raw optimum|
|128|6,046 /491,109|21,525,346|19,580,896|22.76% above compact-v2 raw feasible incumbent; true raw optimum unknown|

The largest pool improves its known parent by9.03%, **using the classical native
pool solver**. Quantum search has not recovered that gain. The32-operation
pool retains the instance optimum but not every feasible schedule. Its numerical
problem hash matches the earlier full5,443-bit/1,664,149-coupler time-indexed
grid15/setup QUBO. No instance-independent lossless compression is claimed.

Evidence: `operation-columns-mac-v1/`, all four pool optima independently
decoded and checked. `operation-compiler-audit128-mac-v1/` verifies every saved
linear/quadratic coefficient, group, variable and metadata value against a
specialized singleton-operation compiler. The latter reduces measured build
time244.62s→6.52s without changing a coefficient. This is a classical engineering
improvement, not quantum optimization.

### Wider conditional search and invariant-sector simulation

`column_blocks.py` substitutes the full supplied master energy, keeps two choices
per selected operation, and applies the exact affine one-hot pair reduction.
All reachable minimal makespan choices remain; the register uses the established
W-state/XY circuit. `operation-column-blocks128-mac-v1/` retains nine runs:
exact, uniform-onehot and QAOA-XY, three seeds,64 blocks,32 shots. All stay at the
parent21,525,346; even exact local searches find no improving neighborhood.
These six-qubit blocks do not solve the6,046-bit master globally.

Classical width probes expand blocks and change the resource/BOM conflict closure.
The first closure variants fail. The v3 probe finds one small improvement in
one classical run, with other runs still stalled. These are development-guided
algorithm choices, not predeclared final estimates.

`sector_mixer.py` simulates the **same physical logical circuit** using only its
invariant makespan single-excitation sector. For n binary choices and k makespan
qubits, it stores k·2^n amplitudes instead of2^(n+k). It does not reduce the
logical circuit's n+k qubits, remove resource conflicts or use an oracle for
feasible schedules. Uniform initialization and exchange mixers are unchanged.
Small tests compare every sector energy and probability with the full simulator.

`operation-sector-blocks32-mac-v1/` tests the closure with16-operation caps,
three seeds,16 iterations and proposal-only/exact/uniform/QAOA controls. Every
method remains at1,124,895. Maximum actual QAOA circuit size is18 logical qubits;
campaign peak RSS is109.8MB and wall time8.89s. Thus the obstacle in this pilot
is useful neighborhood construction, not the Mac's memory capacity.

`operation-sector-circuit-audit-mac-v1/` independently replays **all48 actual
QAOA circuits** in Qiskit's full Hilbert space, including preparation and logical
transpilation. All pass: maximum probability discrepancy1.12e-15 and compiled
probability discrepancy2.06e-14. There are no physical-QPU calls or hardware
connectivity claims. The direct proposal is explicitly evaluated as a classical
control; a precomputed improving proposal must not be advertised as a discovery
made by quantum sampling.

The unchanged algorithm is then run for256 blocks per method/seed in
`operation-sector-blocks32-long-mac-v1/`. All three QAOA runs reach1,103,205,
an improvement of21,690 (1.93%) from the heuristic initializer. All three direct
classical-proposal and all three uniform controls reach the same result; exact
seed7 reaches1,103,265 and the other exact controls reach1,103,205. This remains
21.41% above the proven908,670 grid15 optimum. Adaptive neighborhoods differ
when plateau choices differ, so an exact conditional solver need not produce the
best final global trajectory. No quantum advantage follows from these runs.

The longer campaign reaches **21 logical qubits** (up to16 binary choices plus
the makespan register), records147.12s wall/146.14 process CPU seconds, and
328.3MB peak RSS. The largest observed21-qubit sector has327,680 amplitudes
instead of2,097,152. This is a classical memory reduction for an invariant
sector, not a reduction of the logical quantum register. The full global
operation-pool QUBO is never claimed to run as one circuit.

`operation-sector-circuit-audit-long-mac-v1/` replays all768 longer-run QAOA
circuits in Qiskit's full Hilbert space. Every raw QASM probability agrees with
the sector simulation (maximum2.89e-15). However **three aggressive level3
compilations fail the1e-10 probability tolerance**, with maximum discrepancy
3.93e-6. That failed audit is retained. Per-pass diagnostics identify the first
change at `RemoveIdentityEquivalent` and the larger change at
`CommutativeCancellation`; no layout permutation explains it. Merely setting
`approximation_degree=1.0` does not remove the observed discrepancy.

The documented setting requests no approximation, subject to numerical
tolerance; see [IBM's transpiler configuration documentation](https://quantum.cloud.ibm.com/docs/en/guides/defaults-and-configuration-options).
The remedy is to verify generated circuits rather than assume that setting alone
meets this experiment's stricter test. `operation-sector-circuit-audit-long-mac-v2/`
checks level3 first, then uses level1 or level0 only if the check fails. It retains
the rejected aggressive counts and discrepancy, exports the actual selected
compiled QASM, and does not relax the tolerance. All768 raw/selected compiled
circuits now pass, with exactly three level1 fallbacks; maximum selected compiled
probability discrepancy2.06e-14. Counts for rejected optimized circuits must not
be used as resource counts for a verified implementation.

### Local reproduction

Use the existing NumPy/ORTools environment for solver experiments, and the
separate Qiskit environment for independent circuit audits. Each campaign output
directory must be new, so a rerun cannot overwrite the retained evidence.

```sh
.venv-stage2/bin/python -m stage2.window_interval_experiments \
  --campaign output/stage2-search/component-columns-mac-v1 \
  --output output/stage2-search/compact-reference-rerun

.venv-stage2/bin/python -m stage2.column_search_experiments \
  --case output/stage2-search/operation-columns-mac-v1/case3 \
  --output output/stage2-search/sector-search-rerun \
  --iterations 256 --width 16 --proposal closure --engine sector

.venv/bin/python -m stage2.column_sector_audit \
  --campaign output/stage2-search/operation-sector-blocks32-long-mac-v1 \
  --output output/stage2-search/sector-circuit-audit-rerun \
  --max-qubits 22 --verified-fallback
```

The optional local evidence viewer is
`http://127.0.0.1:4187/stage2/planning.html?scaling=1`. It visualizes saved raw
references and restricted-pool losses; it does not disguise a replay as a new
solver execution. The original physical-factory final evidence remains separate.
