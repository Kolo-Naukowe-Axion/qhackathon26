# Exact reference for a deterministic tiny factory

The one-pump reference has a proved CP-SAT optimum and a complete, independently checked physical execution. With the flagship's manufacturing durations, its optimal shipping time is **566 minutes**, compared with **616 minutes** for the existing dispatch heuristic on the identical numerical instance: an **8.83% makespan gap**. This is a validation instance, not an optimality certificate for the 24-order flagship.

The retained artifacts are in `output/stage2-search/tiny-reference-final/`. Each case contains the complete instance, optimal and heuristic traces, and a report with artifact hashes, source hashes, CP-SAT version/status/bound, budgets, and independent replay results. The source files were stable throughout all four retained runs.

| Declared case | CP-SAT optimum and bound | Heuristic shipping time | Heuristic gap |
| --- | ---: | ---: | ---: |
| Manufacturing scale 15, short automatic attendance, early empty preposition permitted | 566 min | 616 min | 8.83% |
| Same case, AGV dispatch delayed until source processing finishes | 576 min | 616 min | 6.94% |
| Manufacturing scale 15, full attendance at every operation | 1,007 min | 1,018 min | 1.09% |
| Manufacturing scale 1, short automatic attendance | 139 min | 158 min | 13.67% |

All eight traces are physically valid, fulfill their one order, preserve terminal stationary SOC, and have matching earlier objective tiers within each comparison. Constant energy cost is 67.6 units in each scale-15 run and 8.24 in the scale-1 run. Attendance and dispatch changes are explicit model/action-domain ablations; their effects are not solver improvements.

## Numerical scope

`stage2/reference.py:make_tiny` declares one pump, its housing/rotor/flange, 16 required process operations, and 19 required part deliveries. There is one station for each process: T1, F1, WASH1, H1 and QA1 in hall A; S1 and A1 in hall B. The graph has one-minute spokes and a four-minute bridge. Every delivery includes one minute of loading and one of unloading, plus every required empty leg from the AGV's actual previous destination.

There is one fully qualified worker and one AGV. Machine input capacity is one, except assembly capacity three. A finished unit blocks its machine until actual pickup. Destination space is reserved at dispatch, including empty repositioning, and remains occupied/reserved until the receiving operation consumes its input. Assembly consumes the three accepted, matched components and creates the pump. Acceptance and physical shipping remain explicit events.

The furnace has **batch capacity one** in this fixture. Exactly one standard mode is available. One material family makes every setup zero. Tools begin mounted at their only eligible station and have `portable:false`; this prevents gratuitous tool transport from creating unmodeled AGV preposition actions. Life, wear limits, initial AGV energy and grid capacity are explicitly large enough to be nonbinding. The worker has continuous availability and no breaks. Quality probabilities and wear risk are zero, so all keyed inspection outcomes pass. There are no shocks, investment options or in-horizon external deliveries. Solar is zero; tariffs and carbon intensity are constant. The stationary battery starts full and must end equally full.

These are declared parameter choices, not assertions that the real flagship mechanisms are unimportant. `validate_scope` rejects inputs that would activate omitted constraints, including portable tools, alternative modes, multi-member batches, binding life/wear/SOC/grid limits, worker breaks, nonzero quality risk and shocks. It does not silently turn such a changed instance into a relaxation.

Parts may move only to the next required eligible station, accepted BOM join, accepted shipping or a scrap dock after rejection. RAW and unrelated machine inputs are not temporary WIP warehouses. This is the shared factory routing rule. A bounded repair would change the next required route, but quality failures are impossible in this deterministic fixture.

## CP formulation and exactness argument

The implementation uses the standard interval and circuit primitives documented in the [OR-Tools scheduling guide](https://developers.google.com/optimization/scheduling/job_shop) and [CP-SAT model source](https://github.com/google/or-tools/blob/stable/ortools/sat/python/cp_model.py). The following factory constraints are this project's formulation, rather than claims supplied by those examples.

For each operation, integer start/end variables enforce its fixed duration. Its incoming delivery must finish before processing starts. Its outgoing pickup must follow completion. A machine's no-overlap interval extends from processing start **through outgoing pickup**, thereby including output blocking.

For every incoming part, the input-capacity interval extends from **dispatch start through receiving-operation start**. A cumulative constraint counts these reservations and physical inputs together. In particular, all three assembly inputs persist until the common assembly start; the model cannot release buffer space merely because a vehicle arrived.

A Hamiltonian circuit through a dummy node chooses the order of the 19 mandatory AGV deliveries. Conditional arc constraints require the next dispatch to follow the previous drop and its pickup to allow the complete empty path from the previous destination. Loaded duration and both handling intervals are then fixed. The initial arc starts at RAW_A; the final arc requires no fictitious depot return. One AGV makes separate lane-conflict constraints redundant. Unique paths on the transport tree remove route ambiguity.

A second circuit chooses the worker's order over the 16 attendance intervals. Consecutive intervals are separated by the declared hall travel time when their halls differ. Automatic machines require the first five processing minutes at scale 15; welding, QA and assembly require full attendance. The exporter places actual worker walks in the corresponding gaps. These walks may occur before parts arrive. Early empty AGV reposition is also permitted, but pickup waits for actual source completion and destination capacity is reserved throughout dispatch. The heuristic requests both resources later; its candidate-generation restriction contributes to its measured gap.

For the declared direct-transfer instance, every complete execution has exactly these process and part-transfer activities. Physical resource use determines feasible operation times, reservation intervals, and AGV/worker orders, which satisfy the CP constraints. Conversely, every CP solution expands to the primitive movements, attendance, processing and BOM events checked by `stage2/check.py`. Arbitrary temporary warehousing, tool transfers and reservation-cancellation preposition actions are outside this fixture's declared activity domain.

All mandatory processing energy is fixed. With no solar, constant positive tariff and a nonbinding grid cap, the base load over the fixed horizon plus mandatory machine work is a lower bound on grid cost. The full-to-full lossy stationary battery cannot reduce it. Optional AGV charging or powered maintenance would strictly increase it; unnecessary tool service can be deleted without harming production. The retained CP schedules attain this lower bound and fulfill the order with zero tardiness. Thus minimizing shipping time is the actual final tie-break among equivalent earlier objective tiers, rather than an unexplained replacement for the lexicographic objective.

CP-SAT reports `OPTIMAL` with an equal best objective bound for each retained case, using one search worker. The independent checker verifies each incumbent's physical execution; it does not independently prove the CP model's completeness. The full-attendance case has an additional analytic certificate below. Automatic-attendance optimality relies on CP-SAT's exact search and the stated model-to-execution argument.

An `INFEASIBLE` status from a deliberately shortened reference horizon concerns the encoded direct-transfer, minimum-extra-energy activity domain. The report explicitly leaves `global_infeasibility_proven:false`; it does not promote that status into a claim about every optional action of the full environment.

## Independent 1,007-minute certificate

With full attendance, the only worker must perform all **975 minutes** of processing. Its first operation cannot start before the first material arrives, which takes at least four minutes. Welding in hall B and subsequent component inspection in hall A require an earlier worker round trip totaling four minutes.

After the last component QA finishes, every component process is complete and assembly is the only remaining next process. That last component requires eight minutes of loaded transport and handling to assembly. After assembly, the pump requires another eight minutes to return to final QA. No other processing can fill either gap. Those gaps already include the worker's corresponding walks; the bound does not add them again. Accepted final shipping then takes eight more minutes.

Therefore:

`975 + 4 + 4 + 8 + 8 + 8 = 1,007 minutes`.

The CP witness attains 1,007, independently certifying this case's optimum. `full_attendance_lower_bound` computes the same bound directly from instance routes, durations and travel tables without CP variables.

## Reproduction and checks

Use the isolated environment with OR-Tools 9.15.6755:

```sh
.venv-stage2/bin/python -m pip install ortools==9.15.6755
.venv-stage2/bin/python -m unittest discover -s tests/stage2 -p test_reference.py
.venv-stage2/bin/python -m stage2.reference --processing-scale 15 --deterministic-limit 20 --wall-limit 60 --output output/stage2-search/tiny-reference-final/automatic
.venv-stage2/bin/python -m stage2.reference --processing-scale 15 --full-attendance --deterministic-limit 20 --wall-limit 60 --output output/stage2-search/tiny-reference-final/full-attendance
.venv-stage2/bin/python -m stage2.reference --processing-scale 15 --dispatch-after-ready --deterministic-limit 20 --wall-limit 60 --output output/stage2-search/tiny-reference-final/dispatch-restricted
.venv-stage2/bin/python -m stage2.reference --processing-scale 1 --deterministic-limit 20 --wall-limit 60 --output output/stage2-search/tiny-reference-final/compressed
```

The tests verify complete BOM activity counts, scope rejection, exact bound/status, physical replay, actual early preposition with delayed pickup, invariant energy cost, rejection of a corrupted CP witness, and the independent full-attendance certificate. The checker also rejects moving WIP into unrelated buffers to free a blocked machine and moving permanently mounted tools as cargo.

The CP model has 775 variables, including 652 Booleans, before presolve in these runs. **These are CP model statistics, not qubit counts or a QUBO formulation.** No quantum hardware is needed for this classical reference. Its purpose is to catch modeling mistakes and quantify a real same-instance heuristic gap; the full 24-order global optimality gap remains unknown.
