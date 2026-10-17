# Deadline boundary integration gate — 17 October 2026

Two bounded structural attempts failed to produce a useful quantum-sized
conditional recovery block. These failures remain unchanged. A subsequent
[whole-recipe trajectory bridge](STAGE2_RECIPE_BRIDGE.md) now supplies a checked
QAOA integration of the same 32-operation model through a different restricted
representation; it does not retroactively make either boundary attempt succeed.

Use the complete hard-deadline query for the saved32-operation replacement heat
case at completion cap900. The query retains818 logical assignment bits after
exact pruning. The starting schedule is the **first** saved heuristic parent,
not a selected best parent or a CP solution. It is a valid raw schedule but
late. Three parent assignments disappear under the hard query: P02 rotor QA,
pump assembly and final pump QA. These three operations initially become free;
every other parent assignment remains fixed with its complete resource
occupation, travel, setup and precedence effects.

Filter free candidates against fixed outside assignments, then apply exact
pairwise support propagation within the free block. Every release adds an
operation; no outside commitment is silently dropped. Both algorithms use only
the full query, original heuristic schedule, conflict graph and support counts.
They do not consume a reference solution, optimum, or the four missing rows
identified in the separate pool diagnostic.

Before outcomes, each attempt saves its protocol and literal source/input
snapshots. Stop at12 free operations, with24 logical-qubit and1,000,000-sector
state limits. A block must retain nonempty support domains and pass these size
guards before exact conditional enumeration. Only a zero-energy conditional
optimum would allow QAOA/uniform/one-hot SA comparisons. Fixed-bit substitution
retains the full polynomial constant, and any candidate would be decoded as a
whole merged original-model schedule.

| Attempt | Structural rule | Final free operations | Remaining candidate bits | Outcome |
|---|---|---:|---:|---|
| v1 | Minimize empty existing-free groups, maximize their surviving rows, lexical tie |12|98|Some mandatory domain empty; qubit guard exceeded|
| v2 | Prefer empty free group; minimize a candidate's outside blockers; then parent-time displacement and lexical identity; release its blockers |12|60|Some mandatory domain empty; qubit guard exceeded|

The second method is explicitly a development redesign after v1 failed, not an
independent held-out test. It does not erase the earlier failure. Times are
1.520 seconds for v1 and1.355 seconds for v2; both source-stability checks pass.
Both attempts stop before exact sector construction or quantum optimization.
There are zero quantum, uniform, annealing, CP-reference, remote or hardware runs
in these campaigns. No tokens, credits or publication are involved.

These failures concern two greedy structural release ladders from one particular
heuristic parent. They do **not** certify that every12-operation block is
infeasible, that no24-qubit representation exists, or that quantum recovery is
impossible. The original larger query is independently known to admit an on-time
plan. The obstacle here is finding a useful small neighborhood while retaining
all actual outside commitments.

Two exhaustive tiny tests verify every conditional energy against the expanded
parent polynomial, whole-plan decode equality, and filtering of a blocked
predecessor boundary. They validate the adapter; they are not a manufactured
small quantum success or performance result.

Implementation: [deadline_boundary.py](../stage2/deadline_boundary.py).
Tests: [test_deadline_boundary.py](../tests/stage2/test_deadline_boundary.py).
Reports: [v1](../output/deadline-boundary-review-v1/report.json),
[v2](../output/deadline-boundary-review-v2/report.json).

```sh
.venv-stage2/bin/python -m unittest tests.stage2.test_deadline_boundary -v
.venv-stage2/bin/python -m stage2.deadline_boundary --output output/NEW-BOUNDARY --method support_count
.venv-stage2/bin/python -m stage2.deadline_boundary --output output/NEW-BOUNDARY-V2 --method min_blockers
```

Each attempt refuses an existing directory. Frozen historical sources remain
inside each output, including v1 before the redesign. These bounded campaigns
stop at their declared gates. Neither produced a conditional recovery block.

## Subsequent integration through complete component trajectories

The successful [recipe-bridge v2 campaign](../output/recipe-bridge-review-v2/report.json)
retains all 32 original operations by choosing complete housing, rotor, flange
and pump trajectories, with cross-component constraints explicit. Its nested
caps use 18/28/36 logical qubits. All 18 QAOA returned schedules and all 18 SA
returns match their restricted optima and pass the whole-model checker. The
replacement cases reach zero tardiness and makespan 855.

This is a lossy trajectory representation, not the earlier fixed-parent
conditional neighborhood. Its classical constructive stage already contains
the same globally optimal recovery plan, and native pool CP and SA are faster
in the saved local experiment. It establishes implemented integration and
probability concentration within that pool, not quantum-discovered capacity
value or quantum advantage. The first trajectory selection also failed and is
retained separately. See the bridge report for generation/training costs,
raw sampled counts, uniform controls and independent circuit verification.
