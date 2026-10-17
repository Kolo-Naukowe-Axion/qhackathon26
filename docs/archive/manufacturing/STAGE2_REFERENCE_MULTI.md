# Exact deterministic references with 2–4 matched-BOM pumps

`stage2/reference_multi.py` extends the deterministic one-pump reference to at most four pumps. It preserves `stage2/reference.py` and the production engine/checker. This is a scoped classical CP-SAT reference, not an exact formulation of the stochastic flagship factory.

## Declared numerical instance

Each pump has its own housing, rotor and flange, followed by assembly and final QA/shipping: **16 operations and 19 required part transfers per pump**. There are seven fixed stations, one shared worker and one AGV. Each order's assembly consumes exactly its own three components; orders cannot exchange matched BOM parts.

The original recipes, manufacturing durations, two-hall tree layout, worker hall travel, finite input capacities, output blocking and singleton heat treatments remain. The default processing scale15 uses the original manufacturing minutes; scale1 is a compressed regression fixture.

All orders have release zero, identical family alloy_A, and due time equal to the horizon. These orders are label-symmetric; sorting their first housing-operation starts removes only equivalent relabelings, not physical schedules or objective values. Pump parts remain matched when an entire order is relabeled.

The worker is explicitly continuously available for the entire horizon: `day_ticks=horizon+1`, shift `[0,day_ticks]`, no breaks. This matters because several pumps can extend past midnight. Leaving a periodic midnight boundary outside the CP model would silently relax a binding calendar. This fixture deliberately makes calendars nonbinding; it does not represent realistic staffing.

## Exactness domain and scope guards

The model optimizes every mandatory operation start, every part-transfer dispatch/pickup/drop, the complete AGV delivery sequence, and the complete worker attendance sequence. It includes:

- Precedence through each component and final pump recipe, with all three same-order component deliveries preceding assembly.
- Machine occupation from operation start through the following pickup, preserving blocked outputs.
- Destination input reservations from AGV dispatch until processing/assembly starts, including all three assembly inputs.
- A Hamiltonian path through all mandatory transfers, with the actual empty shortest-path reposition from the previous delivery location and loaded travel plus handling. Early dispatch may preposition the empty AGV and wait for source completion. An optional ablation requires dispatch only after source completion.
- A worker path through every operation's attended interval, with hall-walk duration between successive attended tasks. Automatic operations release the worker after their declared start attendance; full-attendance mode reserves the worker throughout processing.

The positive tree gives a unique route. There is no arbitrary intermediate part warehousing or independent standalone empty-AGV preposition action. Empty repositioning occurs inside a mandatory part-transfer dispatch, as in the original reference's declared domain. The scope must remain explicit when comparing with a broader logistics model.

Energy tariffs/carbon are flat, solar zero, electrical capacity nonbinding, stationary SOC begins and ends full, and modes are fixed standard. Quality/rework probabilities are zero; no shocks, urgent orders, investments or material deliveries occur. Tool life, machine wear and AGV initial traction must exceed **aggregate** workload across every pump. These features are checked before solving rather than silently omitted when they become binding.

The validator reuses every original one-order scope guard, checks exact unit/order identities, and adds aggregate shared-resource guards. Changed families/releases/deadlines, periodic calendars inside the horizon, shortages, binding aggregate tool life/wear/traction, alternative modes, quality risk or unmatched BOMs are rejected.

## Objective and certificates

Every modeled order must ship within the declared horizon. All due times equal that horizon, so complete schedules have zero tardiness. With fixed required processing and flat positive energy prices, the exported idle stationary-battery policy attains the same minimum operating cost across complete schedules. CP minimizes the final physical shipment time after these earlier objective tiers.

The report preserves actual CP status (`OPTIMAL`, `FEASIBLE`, `UNKNOWN`, or `INFEASIBLE`), best objective bound, any feasible objective, solver response/model statistics, deterministic and wall budgets, worker count and seed. Only `OPTIMAL` plus a valid complete exported trace establishes this domain's optimum. `FEASIBLE` retains an incumbent and lower bound; it is not relabeled exact. `UNKNOWN` invents no CP witness. An infeasibility proof applies only to the declared numerical model, never the flagship.

Necessary workload bounds for worker attendance, machine processing and loaded transport/handling are reported separately. They exclude empty travel, worker walks, blocking and join gaps; passing them does not establish feasibility.

Each exported solution is replayed by the unchanged independent checker. Trace shipment IDs, operation order IDs and assembly-parent IDs are constructed per order. Traversal of each resource path must visit every mandatory activity exactly once. The exporter retains empty and loaded route legs, SOC accounting, worker walks, machine wear, QA events, consumption events and constant-price electricity telemetry.

## Same-instance heuristic comparison

The initial comparator is the unchanged engine with `wip_limit=1, mode=standard`, a serial-order heuristic. Its independently checked complete schedule provides a CP upper bound and complete operation/move/resource-arc hints; the hints do **not** fix choices. Both executions use exactly the same numerical instance and finite buffers.

The report computes an exact heuristic makespan gap only when CP proves optimality and both traces fulfill all orders with matching earlier objective tiers/cost. If CP is only feasible, its better witness can still demonstrate an improvement over the serial heuristic, but the final optimality gap remains unknown.

## Reproduction and budget

```sh
.venv-stage2/bin/python -m stage2.reference_multi \
  --pumps 2 --processing-scale 15 --wall-limit 15 --deterministic-limit 10 \
  --workers 1 --output /path/to/new-empty-directory
```

Use `--full-attendance` for fully manual processing, and `--dispatch-after-ready` for the source-completion dispatch restriction. The output directory must be new. Reports include canonical instance/source/artifact hashes and whether source files stayed stable during execution. No final held-out tape is used.

The initial frozen source SHA-256 is `226dced1939ee824a0e661d4112efc488be4de3286e6280e9da4e58163700efe`. Local pilots use bounded one-worker CPU searches; larger remote budgets require preserving the same source and scope. All timeouts, negative results and incomplete proof bounds are retained.

## Validation

Six tests in `tests/stage2/test_reference_multi.py` cover 1–4-pump activity counts and per-order joins, aggregate omitted-resource guards, continuous-calendar guards, three-pump physical export, adversarial cross-order parent swaps, a bounded two-pump CP search, and short-horizon model infeasibility.

The one-pump compressed regression independently proved makespan139 versus the serial heuristic158, agreeing with the original reference. The new multi-pump pilots are retained under `output/stage2-search/multi-reference-pilot/`; their actual statuses and bounds must be read from each report.

## Stronger comparisons and constructive upper bounds

The separate development grid in `output/stage2-search/multi-reference-heuristic-grid/report.json` tries WIP limits 1 through the pump count and remaining-work weights −4, 0 and 4, always at standard mode. All 54 traces pass the physical checker; **28 are incomplete and remain in the report**. Selection is on these deterministic fixtures themselves; this is not held-out evaluation.

Its best complete automatic makespans are 1238, 1860 and 2482 minutes for two, three and four pumps. Full-attendance best complete makespans are **1991, 2984 and 3960**, improving on the original serial comparator's 2042, 3066 and 4090. Any full-attendance performance claim must acknowledge these stronger baselines.

The 600-second two-pump automatic search proves **863 minutes**, with a complete independently checked physical trace and matching CP lower bound. Relative to the strongest development-grid comparator 1238, the heuristic takes 43.45% longer; the exact schedule reduces completion time by 30.29%. These are two ways of describing the same scoped comparison, not flagship optimality gaps.

`output/stage2-search/multi-reference-constructive/run.py` constructs larger complete schedules from retained checked blocks. Concatenating the proven two-pump schedule with the one-pump 566-minute schedule gives three pumps in **1435 minutes**. Repeating the two-pump schedule gives four pumps in **1732 minutes**. Each join includes six actual empty-AGV minutes from shipping to raw stock. The exporter rebuilds global SOC, wear, worker paths and matched BOM; both complete traces pass a fresh independent check. These are constructive upper bounds, not larger-instance optimum claims or resumed CP proof states.

## Full-attendance analytic lower bound

For the original scale15 numerical layout, a safe bound is **975n + 20 minutes** for n complete pumps under full attendance. Its parts occupy disjoint time intervals:

1. Before any processing, a raw part needs at least four minutes to reach its first station, including handling. All first recipe steps are in hall A, and the initial AGV is at raw stock.
2. All mandatory processing takes 975n minutes and reserves the single worker throughout.
3. The flange precedence chain forces a worker hall subsequence A → B (weld) → A (wash/inspection) → B (assembly) → A (final pump inspection). At least four two-minute hall walks occur between the first and last processing operations. Worker walks and attended processing cannot overlap.
4. The chronologically last required processing operation must be a pump's final inspection: every other mandatory operation has a required processing descendant. Its final shipping transfer takes at least eight minutes after processing ends.

Thus 4 + 975n + 8 + 8 is necessary. Empty repositioning, buffer blocking and extra walks are optimistically free. The proof does not multiply the one-pump 1007-minute optimum by n, and it does not add the one-pump assembly-join delay per pump: other pumps may fill such delays. This analytic certificate is separate from the immutable226d CP runs; their saved `best_bound_ticks` remains the bound actually reported by CP, not this derived bound.

The executable independent arithmetic certificate is retained at `output/stage2-search/multi-reference-bounds/build.py`. It reads actual processing durations, shortest physical distances, handling and worker travel from each saved instance, and checks full attendance and hall placement before applying the proof. Its two/three/four-pump bounds are **1970 / 2945 / 3920**. Four additional tests in `tests/stage2/test_reference_multi_bounds.py` check scope rejections, numerical route/walk changes, multiple counts/scales and complete physical witnesses. It leaves the frozen CP module untouched.

`output/stage2-search/multi-reference-summary/build.py` combines retained search reports, these separate certificates, checked constructive upper bounds and the stronger heuristic grid. It preserves each actual CP status and bound. When only an interval for the optimum is known, it reports a **heuristic-gap interval**, not a fictitious exact gap. Runs still executing are marked `RUNNING`; they contribute no invented objective or bound.

## Automatic-attendance prefix certificate

The same independent certificate script now separately handles the original scale15 automatic fixture. Mandatory attendance is 350n minutes. No process can complete before minute64: first raw delivery takes at least4 minutes, and every first T/F operation needs at least60 processing minutes. Before64, the single turning and milling stations permit at most one start each. Their five-minute tending intervals account for at most10 mandatory attendance minutes, leaving at least54 minutes without mandatory attendance in that initial64-minute prefix.

After any flange's welding operation, its matched chain forces B→A (wash/QA), A→B (assembly), and B→A (final inspection): three two-minute worker walks after64. These six minutes cannot overlap mandatory attendance or the initial prefix. The first A→B walk is deliberately excluded because it may fit inside that prefix. The last required processing operation is a fully attended pump inspection; physical shipping then needs at least8 further minutes.

Therefore **350n + 54 + 6 + 8 = 350n + 68** is a necessary bound: **768 / 1118 / 1468** for two/three/four automatic pumps. “Without mandatory attendance” does not assert that the worker literally does nothing; optional activity cannot remove elapsed time or the mandatory workload. No per-pump join gap is added. The proof was independently reviewed before being included in the evidence.

`automatic_certificate` fails closed on initial WIP, additional T/F stations, first-operation duration below60, changed five-minute T/F tending, automatic S/QA/assembly attendance, shortened initial delivery, nonzero setup or binding maintenance. Numerical workload, subsequent walk duration and final shipping distance are read from the instance. Seven tests now cover the full and automatic certificates, including adversarial assumptions and retained complete witnesses. These are separate analytic bounds: active226d CP searches are unchanged and their actual solver bounds remain intact.

## Stronger conditional buffer/BOM certificate

The strict fixture has one assembly input of capacity3 and one blocked QA output. An accepted component can exist only in that QA output or on its mandatory path into the assembly input. Inbound moves already reserve destination capacity, so at most **four accepted, unconsumed components** exist before a worker visit to hallB. QA fully attends the sole worker in hallA; no additional components can become accepted while that worker remains in B. Two assembly starts need six distinct accepted components. Therefore a B visit can start at most one assembly.

The first productive B visit must weld a flange: every pump needs such a flange, and welding still needs later A wash/QA before assembly. That first B visit cannot already assemble a pump. Thus n pumps require at least **n+1 productive B visits** and **2(n+1) hall walks**, returning to A for final QA.

For full attendance, the bound becomes **975n + 4n + 16**: **1974 / 2953 / 3932** minutes. For automatic attendance, only the first outward walk may overlap the initial prefix; all remaining2n+1 walks are after64. The bound becomes **350n + 54 + (4n+2) + 8 = 354n + 64**: **772 / 1126 / 1480** minutes. These remain lower bounds, never reported CP outputs.

Generate the new guarded artifacts with `python output/stage2-search/multi-reference-bounds/build.py --buffer-bom`. They use distinct `*-buffer.json` paths. Earlier prefix/full artifacts and their executable source are byte-preserved under `history-prefix/` with a hash manifest. Ten certificate tests include rejection of extra assembly capacity, additional QA, autonomous QA/assembly, initial accepted/WIP extensions, arbitrary warehousing, changed hall mapping and extra QA output capacity. These assumptions do not hold automatically in the two-assembly-station flagship.

## Retained search outcomes

The three-pump automatic search proves **1191 minutes** in971.15 seconds on one CPU, with a fresh complete physical check. Its strongest development heuristic takes1860, an exact56.17% excess makespan (35.97% completion-time reduction). The3600-second value is a budget cap; this proof finished early. The two-pump automatic optimum remains863. All larger full-attendance600-second negative searches remain retained; their stronger heuristic upper bounds lead the comparison.

| Pumps | Attendance | Strongest certified lower bound | Best checked complete upper bound | Optimum proved? |
|---|---|---:|---:|---|
| 2 | Automatic | 863 | 863 | Yes |
| 3 | Automatic | 1191 | 1191 | Yes |
| 4 | Automatic | 1482 | 1567 | No; supplemental arithmetic bound; CP bound remains1466 |
| 2 | Full | 1974 | 1980 | No |
| 3 | Full | 2953 | 2984 | No |
| 4 | Full | 3932 | 3960 | No |

Bounds combine actual CP proof bounds with separately guarded analytic certificates; upper bounds may come from CP, a heuristic or a checked construction. Each source remains explicit in `multi-reference-summary/report.json`. This table is a retained snapshot, not a live status endpoint.

A separate30-second/one-CPU worker/machine relaxation was also tried for n3/n4, retaining recipe/BOM precedence, optimistic loaded-transfer lags, machine processing and exact worker hall transitions, while dropping buffers, output blocking and the shared AGV sequence. It did **not** improve the then-current analytic bounds: n3 remained1118 and n4 remained1468. Relaxed incumbents1251/1732 are explicitly **not physical feasible witnesses**, and neither relaxation was solved optimally. Reports and all dropped constraints are retained at `output/stage2-search/multi-reference-relaxation/n{3,4}-30/report.json`; no further budget was spent on this formulation.

The four-pump automatic longer search ended **FEASIBLE1732, reported CP lower bound1400**, at deterministic time3600 after3311.33 solver-wall seconds (3312.81 seconds including export/check). It did not improve the checked concatenation hint. Its64 operations and76 moves ship all four pumps and pass the independent physical checker. All four owning source hashes remained stable throughout the run, including frozen reference source226d. At that snapshot, the strongest separate arithmetic lower bound was1480, giving the remaining optimum interval **[1480,1732]**; no stronger CP proof or optimum is inferred from that unsuccessful search. The full report, schedule, hint and checked trace remain at `output/stage2-search/multi-reference-3600/n4/automatic/`. No additional local job was launched in that campaign.

## One bounded parallel follow-up

A separately authorized Axion job6117466 ran the identical four-pump automatic instance with16 CP workers, unchanged reference source `226dced1939ee824a0e661d4112efc488be4de3286e6280e9da4e58163700efe`, unchanged reference/checker/engine hashes and the retained1732-minute checked hint. The canonical instance SHA256 remains `3c6bda8bbf315951447394c68053894ff4a756be1c63f826de7c58739b5c3f7e`. The entire source, driver, input and hint were copied into an isolated remote snapshot; no shared solver or physics source was edited. This was a fresh search, not continuation of a serialized CP proof.

The result is **FEASIBLE1567**, with reported **CP lower bound1466**. A fresh local independent check verifies all64 operations,76 moves, four shipments at629/1078/1355/1567 and terminal requirements. The CP bound improves the earlier1400 but remains weaker than the independently guarded1480 arithmetic bound. The combined certified interval is therefore **[1480,1567]**, with no optimum proof. The new witness reduces factory completion time by165 minutes (9.53%) versus1732. The strongest tested heuristic2482 consequently has an excess-makespan interval of58.39–67.70%, not an exact gap.

The job used16 allocated CPUs and16GB requested RAM, a1770-second CP wall cap and1800-second scheduler cap, with deterministic limit1e9 so wall time governed. It completed normally at1779 scheduler seconds: **7.9067 allocated CPU-hours**, Slurm TotalCPU27754 seconds, reported batch MaxRSS1747388K, **zero GPU-hours**, no budget overrun. Solver-wall time was1770.170 seconds; end-to-end driver/check/export time1778.747 seconds. Hardware and compute budget differ from the earlier local runs, so this is not a controlled parallel-speedup experiment.

All original negative reports remain unchanged. Frozen inputs, full source, CP schedule/trace, job logs, raw Slurm accounting and independently checked cost are retained under `output/stage2-search/multi-reference-parallel-axion/`; `independent-audit.json` pins archiveSHA `98e28b20d8d99b07b3a25da9f4b1e2716b1fad22c276a230a55b2fb83e32480c` and traceSHA `29e39634c0fcb366d441fa315839f175179c2fd3668eea04bd6a1d52ea46c267`. No further job was launched after this bounded follow-up.

## Subsequent bounded search and independent overlap proof

At01:15UTC on17October, one fresh Axion search6117555 started from the checked
1567-minute witness on the identical numerical instance and unchanged exact
reference source226d. It uses16 CPU workers, fixed seed2027, a7170-second CP cap
inside a7200-second scheduler limit, and at most32 allocated CPU-hours. It is
not a resumed serialized CP proof or a change to the flagship. Its result remains
pending; no improved upper bound is inferred while it runs.

Separately, a guarded arithmetic extension raises the automatic four-pump lower
bound from1480 to **1482 minutes**, without running any solver or factory. Let P
be the first64-minute prefix outside required attendance, with measure at least54;
let R contain the2(n+1) necessary productive-excursion hall walks. Only the first
selected outward walk can overlap P. If that overlap is o≤2, the worker arrives
in hallB by66, but no required hallB work can start before72. A post-prefix waiting
interval therefore contributes at least o and is disjoint from P, R and required
attendance. This compensates the overlap and retains all4(n+1) required walk
minutes in the union. Add350n required attendance and8 final shipping minutes:
the bound is **354n+66**, or774/1128/1482 for2/3/4 pumps.

The proof handles extra unproductive walks; it does not falsely assert54 minutes
of pure nonwalking idle. Exact numerical/source guards, the set-union proof,
three tests and all26 matching retained complete automatic witnesses are in
[output/reference-bound-extension](../../../output/reference-bound-extension/PROOF.md).
Two independent reviews agree. The existing CP bound1466 and every earlier
1480/prefix/full-attendance artifact remain unchanged. The current combined
four-pump optimum interval is therefore **[1482,1567]**, with no optimum proof
and no extension to the two-assembler stochastic factory.

## Completed two-hour follow-up:17October2026,03:16UTC

This completed record supersedes the pending status and current-interval wording
in the historical sections above. Axion job6117555 ended normally with
**FEASIBLE1541**, reported **CP lower bound1524**, and `optimal=false`.
The scoped optimum is therefore in **[1524,1541] minutes**. The17-minute width
bounds the incumbent's possible excess; the actual optimality gap is unknown.
The former1567-minute upper bound improves by26 minutes, or1.66%. The strongest
tested same-fixture heuristic2482 has excess over the unknown optimum in
**[61.0642%,62.8609%]**, not an exact known gap. None of these comparisons bounds
the unrestricted stochastic factory or changes a selected final policy.

The exact formulation, numerical instance and physical sources are unchanged:
reference sourceSHA `226dced1939ee824a0e661d4112efc488be4de3286e6280e9da4e58163700efe`,
canonical instanceSHA `3c6bda8bbf315951447394c68053894ff4a756be1c63f826de7c58739b5c3f7e`.
All nine frozen payload hashes, source hashes, transport archive members and
schedule/trace roundtrips were independently checked. This was a fresh
16-worker CP-SAT search at seed2027 with a checked1567-minute incumbent, complete
warm-start hints and a makespan cutoff1567. No choices were fixed and no
serialized proof state was resumed. The valid incumbent ensures that the cutoff
cannot exclude an optimum; byte-identical serialized CP models are not claimed.
The new solver lower bound1524 dominates the preserved arithmetic bound1482 and
the previous CP bound1466. Those historical artifacts remain unchanged.

### Literal raw trace and explicit derived witness

The raw CP trace has64 operations and76 moves, with four shipments at
784/1177/1496/1541. Its original physical checker and terminal checks pass.
However, the **unmodified stock identity auditor rejects the raw trace**:
`move74` books `P04/pump/1` at1382, before its canonical birth at assembly start1420.
The earlier1567-minute hint has its own retained stock identity rejection.
Neither raw rejection is suppressed or relabeled as a stock-audit pass.

In the new trace, preceding AGV `move62` ends at1381 atA1. The pump is assembled
atA1 during1420–1480; `move74` picks it up at1480 and its first loaded leg starts
at1481. There are no earlier travel legs in that move. Thus the early booking
reserves a parked AGV and future destination capacity, rather than transporting
an unborn pump. A separate exact-instance/source-guarded reference audit checks
canonical identities, producer completion, pickup and every loaded leg, matched
BOM parents and fixed QA draws. It passes all76 raw moves. Its narrower
physical-encounter interpretation is disclosed separately from stock auditing.

An explicitly labeled **derived constructive witness**, not literal solver
output, changes exactly one field: `move74.start` from1382 to1420. This shortens
the parked AGV/destination reservation. Every operation, leg, pickup, drop,
energy record and identifier remains identical. Both raw and derived
`trace.metrics` fields remain the exporter's empty dictionary; actual metrics
are freshly recomputed by the checker, and those recomputed metrics match
exactly. The derived witness passes the **unchanged** physical, terminal and
stock identity checks, still completing in1541 minutes. No factory, solver or
new performance sample was run to construct it.

The original CP dispatch domain permits earlier future-identity bookings. Its
1524 lower bound is also valid for the stricter birth-at-dispatch subset; the
derived1541 witness supplies an upper bound for both. This justifies
[1524,1541] without claiming that both domains have equal optima. Six adversarial
tests pass, including rejection of prebirth pickup or loaded travel, unknown
cargo, redrawn QA, real prebirth empty travel in the normalization and a changed
numerical scope. A second independent review reruns the audit and reproduces
the complete held report except its elapsed timer and the exact saved derived
witness.

### Cost and reproducible evidence

Slurm records7174 elapsed seconds with16 allocated CPUs:
**31.884444 allocated CPU-hours**, within the7200-second scheduler cap.
The CP cap was7170 seconds, actual solver wall7170.320 seconds, driver wall
7173.495 seconds and measured process CPU114101.4528 seconds
(31.694848 CPU-hours). Allocation, process and nested wall timers describe the
same job and are not additive. Recorded GPU use is zero. Different hardware and
budgets prevent interpreting the incumbent improvement as a parallel speedup.

- [Literal completed solver report](../../../output/stage2-search/multi-reference-2h-axion/completed/multi-reference-2h-20261017T0116/result/report.json), SHA `9ceba65416fbe4376e5ad84baeec144042a7fd61a9a396949deeb7310184c0cd`.
- [Independent physical/source/identity audit](../../../output/stage2-search/final-independent-audit/reference-2h-6117555/report.json), SHA `d0e913cbae461891b66404e831c7d868b3c3d814bce4fb75d104aba5b444f4ac`.
- [Explicit derived witness](../../../output/stage2-search/final-independent-audit/reference-2h-6117555/derived-normalized-witness.json), SHA `76bc078f004a0176effc955dc7810d0ff3d49442da00e047465c45be2e11182a`.
- [Independent second-review seal](../../../output/stage2-search/reference-2h-methodology-review/final-seal.json), SHA `96bca6796eff427102dbdc59c14ffb1693b70e04594ecf17baebc08087a54a14`.
- [Raw scheduler accounting](../../../output/stage2-search/accounting-20261017-0316.txt) and [completed research accounting](../../../output/stage2-search/final-compute-0316-summary.json).

Run the mutation checks without launching a factory or solver:

```sh
.venv-stage2/bin/python -m unittest discover \
  -s output/stage2-search/final-independent-audit/reference-2h-6117555 \
  -p test_reference_identity.py -v
```

The original final outcomes, frozen40-source snapshots, primary certificates and
full-evidence-v2 archive remain unchanged. This reference return is a separately
labeled supplementary result.
