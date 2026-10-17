# Whole-recipe quantum bridge — completed local development study

17 October2026. The quantum method now runs on a **restricted representation of
the same32-operation manufacturing recovery model**, with all housing, rotor,
flange, pump assembly and final QA operations retained. This is a genuine
larger-model integration result, separate from the earlier synthetic five-step
microscope and failed fixed-boundary release ladders.

It does **not** establish quantum advantage or a new source of recovery value:
the explicitly charged classical constructive stage already finds the best
recovery schedule. The contribution is a checked quantum recombination of
complete real-model component trajectories, with actual circuits and controls.

## Representation and frozen protocol

Use the unchanged saved `manufacturing-recovery-v2` raw inputs for heat outage
and replacement heat capacity,32 operations each. For each input, generate64
distinct checked whole-model schedules by seeded randomized raw topological list
scheduling: seed17021, at most256 attempts and12 seconds. Both cases finish64
parents in64 attempts, approximately0.344 seconds each. No native-reference
answer, QUBO optimum or saved optimal-plan rows enter generation.

Partition each whole plan into eight complete component trajectories: housing,
rotor, flange and final pump operations for each of two orders. Choose one
trajectory per component. All mandatory operations remain covered; conflicts
and precedence between different components remain explicit QUBO penalties.
This changes the represented domain: unsupplied internal component schedules
are excluded. It is not lossless compression of the full assignment QUBO.

The successful v2 candidate rule retains the **first and best constructive
parent**, where best uses the original declared raw schedule objective. It then
appends remaining trajectories ordered by component completion, total start
times and canonical identity. Caps2/3/4 are nested prefixes; all candidates are
saved before references are imported. The best constructive parent is disclosed
as a substantive classical control, not a discovery credited to QAOA.

Compile the existing exact component-column QUBO, including a makespan register,
and simulate its assignment one-hot sector. The circuit has18,28 or36 logical
qubits; storing only the invariant sector does not reduce this register size.
Use QAOA p2/CVaR alpha0.25,64 exact simulated objective evaluations,512 sampled
shots and seeds7/13/29. Controls are512 uniform one-hot samples,32-replica
one-hot SA with256 proposals per replica, an independent native restricted-pool
CP reference, complete exact sector energies and the constructive parent.
These budgets are unequal and are reported, not presented as a runtime race.

Preparing the full sector energy table is exact classical enumeration and
already reveals its optimum to an observer. Training does not consume the
minimum or a CP solution, but this is not scalable quantum computation.

## Actual v2 results

Every native restricted-pool reference proves OPTIMAL. Every exact sector
minimum agrees with it. The checked raw objective is `1441*T + makespan`.

| Case / cap | Logical qubits / couplers | Sector states | Pool optimum T / makespan | QAOA optimum runs | Uniform optimum runs | SA optimum runs |
|---|---:|---:|---:|---:|---:|---:|
| Outage2 |18 /33|512|45 /945|3/3|3/3|3/3|
| Outage3 |28 /117|26,244|45 /945|3/3|0/3|3/3|
| Outage4 |36 /217|262,144|45 /945|3/3|0/3|3/3|
| Replacement2 |18 /31|512|0 /855|3/3|3/3|3/3|
| Replacement3 |28 /110|26,244|0 /855|3/3|0/3|3/3|
| Replacement4 |36 /206|262,144|0 /855|3/3|0/3|3/3|

All18 QAOA and18 SA returned schedules pass the whole original raw-model
checker, without substituting a reference plan. Only6/18 uniform returned
encodings are valid, including their makespan register;8/18 contain raw-valid
operation plans, but two of those have inconsistent encoded completion bounds.
An invalid encoding never counts as an optimal return merely because its raw
objective happens to equal the reference. Table optimum runs require a valid
encoding and literal QUBO energy equal to the pool optimum; a valid plan with
an unnecessarily large completion register also does not count as an encoded
optimum. Every raw sampled count, chosen bits,
emitted QASM and checked whole plan
is retained. Three seeds are optimizer/sampling replicas on two known synthetic
instances, not18 independent industrial problems.

At replacement cap4, QAOA's ideal exact-energy hit probability is0.0136025 for
each selected-angle run, versus0.0000114441 under uniform one-hot sampling.
There are three exact ground states among262,144 sector states. This is
probability concentration in an explicitly restricted domain. It is not a
runtime advantage: QAOA takes about1.29–1.47 seconds per run after shared
preparation, whereas the native pool reference proves the optimum in0.0065
seconds including construction, and SA takes about0.021 seconds. The classical
constructive stage itself already provides the globally optimal0/855 plan.

The successful v2 campaign takes12.088 seconds, including construction,
candidate generation, shared preparation, all references and54 stochastic
method runs. Source hashes remain stable. Both v2 restricted optima match the
existing complete-model optima, so objective restriction loss is zero **on these
two specific inputs**. Feasible schedules outside the trajectory pool are still
excluded; zero measured optimum loss is not universal losslessness.

## Preserved failure and redesign

The earlier v1 uses the first two constructive parents as mandatory anchors,
then chooses earliest-component trajectories. Although the64-parent source
contains much better whole schedules, that selection discards their coordinated
components. Its outage pool optimum remains260415 instead of65790, and its
replacement pool remains65790 instead of855. Larger pools alone do not fix it.
Many larger-domain QAOA returns are invalid, while SA finds the restricted
optimum. Its complete14.980-second campaign, all54 method runs, raw counts and
sources remain separate and unchanged.

V2 is an explicitly development-guided redesign after that failure: preserve
the actual classical incumbent before adding tempting local trajectories. Its
results are not held-out evidence. The prior0.295-second exploratory reference
check of the existing four-parent recovery pool is also disclosed in both
protocols; it supplied no candidate-generating plan.

## Independent circuit verification

The circuit audit parses and logically transpiles all18 actual v2 QAOA circuits
to RZ/SX/X/CX at optimization level1, including state preparation, cost and
mixers. It independently full-Hilbert replays all six18-qubit circuits before
and after transpilation with Qiskit2.1.2. All pass the1e-10 probability/leakage
tolerance. The larger28/36-qubit circuits are parsed/transpiled only; they are
not independently full-Hilbert replayed. These counts assume unrestricted
connectivity and supply no physical routing/calibration or hardware-readiness
claim. The audit takes6.545 seconds with stable source hashes.

## Reproduction and deliverables

Implementation: [recipe_bridge.py](../../../stage2/recipe_bridge.py).
Tests: [test_recipe_bridge.py](../../../tests/stage2/test_recipe_bridge.py).
The two tests cover complete operation partition, nested candidate retention,
incumbent preservation, deterministic raw generation inputs, input immutability
and invalid parent rejection. Existing compiler/sector tests supply the broader
exact polynomial and quantum implementation checks. The combined targeted run
of recipe-bridge, column-QUBO and assignment-QAOA tests passes all nine tests,
including cross-column BOM precedence, exhaustive ground-state validity,
sector-energy preservation and independent full-Hilbert pair rotations.

```sh
.venv-stage2/bin/python -m unittest tests.stage2.test_recipe_bridge -v
.venv-stage2/bin/python -m stage2.recipe_bridge --anchor-policy first_two --output output/NEW-BRIDGE-V1
.venv-stage2/bin/python -m stage2.recipe_bridge --anchor-policy first_and_incumbent --output output/NEW-BRIDGE-V2
.venv-odra/bin/python -m stage2.recipe_bridge_audit --campaign output/NEW-BRIDGE-V2 --output output/NEW-BRIDGE-AUDIT
```

Evidence: [v1 failure](../../../output/recipe-bridge-review-v1/report.json),
[v2 whole-recipe integration](../../../output/recipe-bridge-review-v2/report.json),
[independent circuit audit](../../../output/recipe-bridge-circuit-audit-v1/report.json),
[all54 return/count reporting audit](../../../output/recipe-bridge-reporting-audit-v1.json).
The reporting audit independently checks selected literal energies, original
raw plans, decoder validity and every retained observed state/count. The UI
exporter has a regression test excluding invalid states whose raw objective
matches the optimum; its regenerated valid optimum totals are QAOA18/18,
SA18/18 and uniform6/18.
Each output refuses existing directories and retains protocols, literal source
snapshots and file hashes. No VeloxQ, remote services, credentials, physical
QPU, paid compute, publishing or deployment was used.
