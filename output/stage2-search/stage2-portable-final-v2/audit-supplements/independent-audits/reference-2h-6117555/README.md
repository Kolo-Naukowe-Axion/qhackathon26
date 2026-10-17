# Independent audit of reference job 6117555

The unchanged four-pump reference search returned **FEASIBLE**, incumbent makespan **1541**, and CP-SAT lower bound **1524**. This is the same numerical instance `3c6bda8b…` and frozen `reference_multi.py` source `226dced1…`. All nine returned payload files agree with their original local manifest. Returned artifact hashes, the transfer archive, fresh instance reconstruction, original schedule/trace round trips and raw accounting agree. No factory or solver was rerun by this audit.

The lower bound is reported by CP-SAT on the audited declared reference domain. It is not a new independent arithmetic proof or a claim of proven optimality. The preserved arithmetic bound 1482 is weaker. The four-pump incumbent's absolute excess over its unknown optimum is bounded above by 17 minutes; its relative excess, divided by the unknown optimum, is at most `17/1524 ≈ 1.11549%`.

## Literal identity-auditor discrepancy

The raw CP witness passes the unchanged fresh-instance physical checker, all-orders fulfillment, terminal requirements and independent metrics. Its frozen generic identity audit returns **false** with one issue: `unit_before_identity_birth` for `P04/pump/1`, move74. That literal rejection is preserved in `raw-new_cp-stock-identity.json`; it is not suppressed or relabeled. The old 1567 hint has the same kind of literal rejection for P03/pump/1, preserved in `raw-hint-stock-identity.json`. The 2482 heuristic passes the generic identity audit.

The new raw timings are:

| Event | Minute |
|---|---:|
| Previous AGV delivery, move62, reaches A1 | 1381 |
| Raw move74 dispatch/reservation begins; AGV remains parked at A1 | 1382 |
| P04 assembly starts; its canonical pump identity is born | 1420 |
| Assembly completes and move74 pickup begins | 1480 |
| First loaded movement begins | 1481 |
| Pump reaches QA1; QA starts | 1488 |
| QA ends | 1533 |
| Physical shipment ends | 1541 |

There are no empty or loaded legs before identity birth. The reference explicitly permits an empty dispatch to wait for its future source output while reserving destination space. The generic identity supplement instead dates every part reference at dispatch start. `reference_identity.py` implements a separate, exact-instance/source-guarded identity check for this reference interpretation: canonical birth, parent and immutable QA identities remain mandatory; physical pickup **and every loaded leg** must follow both birth and producer completion. It passes all 76 raw moves. This is not a change to the generic checker or flagship policy domain.

## Separately derived witness satisfying the original identity auditor

`derived-normalized-witness.json` is an explicitly derived copy, **not literal solver output** and not a new experiment. The only structural change is move74's `start`, from 1382 to 1420. The AGV is already at A1; the wait and QA input reservation only shrink. All 76 loaded/empty paths, pickups, drops, operations, worker movements, shipping times, energy rows, horizon and instance remain identical. The raw trace's cached `metrics={}` also remains unchanged; metrics are freshly reconstructed by the physical checker.

This derived witness passes the unchanged physical checker, terminal requirements **and the unchanged generic identity auditor**, and still ships all four orders by 1541. The original raw CP trace and schedule remain byte-for-byte unchanged. The precise one-field transformation and all fresh results are recorded in `report.json`. Six tests reject before-birth pickup/loading, unknown cargo, altered QA keys, actual prebirth empty travel and changed numerical scope, while verifying the exact one-field copy and immutable original.

The broader CP dispatch domain provides a valid relaxation lower bound for the stricter birth-at-dispatch interpretation. The derived witness supplies an upper bound in that stricter interpretation. Thus **[1524,1541]** remains valid without asserting that the two domains have identical optima.

## Comparison and scope

The retained heuristic makespan is 2482 on the identical instance. All four orders are fulfilled with zero deadline debt; raw/derived CP, hint and heuristic have the same minimum 2704 kWh grid energy and cost 270.4. The fixed horizon base load plus mandatory standard-mode process energy establishes that minimum; constant tariff, no solar and full initial/final stationary charge prevent free battery savings.

If the unknown reference optimum is `O ∈ [1524,1541]`, the heuristic's absolute excess lies in `[941,958]` minutes and `(2482−O)/O` lies in **[61.06424%,62.86089%]**. These are certified intervals, not an exact known heuristic gap. The fixture has one AGV, one worker, seven fixed stations and deterministic quality, with explicitly nonbinding mechanisms. No flagship global gap, final-policy improvement or quantum advantage follows.

Slurm reports completion with exit 0:0, 7174 seconds and 16 CPUs: 31.88444 allocated CPU-hours. The process reports 7173.4946 wall seconds and 114101.4528 CPU seconds. All costs are separately recorded; no new solver/factory execution, final-tape sample, policy change, publication or deployment occurs in this audit. Earlier 1480/1482 arithmetic, 1466 CP bound and 1567 witness artifacts remain preserved historical evidence.
