# Stage 2: necessary capacity bounds

These are **infeasibility certificates and optimistic resource bounds**, not solver results. Code: `stage2/bounds.py` (Python standard library only). Reproduce with:

```sh
python3 -m stage2.bounds --profile coarse --orders 24
python3 -m stage2.bounds --profile full --orders 24
```

Each JSON report includes the complete numerical instance's canonical SHA-256 digest, tick duration, horizon, profile, assumptions, per-order relaxed transport witnesses, and certificate descriptions. `--instance path.json` accepts a numerical instance or a trace containing `instance`. The output is printed; the module does not change instance files or traces.

**Capacity scope:** the certificates hold the initial machine/tool pool fixed. The current model permits an endogenous calibration-kit lease; the single-kit certificate therefore proves that doing without added capacity fails, **not that the complete investment-enabled problem is infeasible**. The report separates `nominal_completion_impossible_with_initial_capacity` from `full_model_infeasibility_proven`, and does not promote fixed-capacity certificates to whole-model infeasibility when lease options exist.

## Main findings

The original coarse factory and the refined factory are **different numerical/action models**. The refined model has one-minute movement/handling steps, finer rounding of manufacturing durations, and short attendance for automatic machinery. The original has fifteen-minute movement/handling steps and full-interval attendance. Changing these interpretations is a documented model revision; it is not evidence that a solver overcame the original capacity shortage.

| Necessary bound for 24 nominal pumps | Coarse: 15-minute ticks, 384 ticks | Refined: 1-minute ticks, 5,760 ticks |
|---|---:|---:|
| Minimum part movements | 456 | 456 |
| Minimum loaded travel | 1,200 ticks = 300 fleet-hours | 1,200 minutes = 20 fleet-hours |
| Loaded travel + load/unload | 2,112 ticks = 528 fleet-hours | 2,112 minutes = 35.2 fleet-hours |
| Including unavoidable loaded-traction recharge | 2,272 ticks = 568 fleet-hours | 2,272 minutes = 37.87 fleet-hours |
| Available time of four AGVs | 1,536 ticks = 384 fleet-hours | 23,040 minutes = 384 fleet-hours |
| Minimum loaded bridge crossings | 72 | 72 |
| Minimum bridge occupancy | 288 ticks = 72 hours | 288 minutes = 4.8 hours |

The coarse profile cannot finish all 24 orders in 96 hours: mandatory AGV use alone exceeds fleet capacity. Ignoring charging, its makespan is at least 528 ticks = **132 hours**. Including the unavoidable recharge term gives at least 568 ticks = **142 hours**. Empty repositioning, tool transport, charger travel and congestion were all granted free.

The refined profile removes that particular obstruction. It encounters a different certificate once the precision certification requirements are enforced: **one calibration kit cannot support the nominal workload within the qualified worker calendars**.

## Precision calibration certificate

The explicit rule used here is:

```json
{"certification_modes":{"precision":{"T":["eco","standard"],"F":["eco","standard"],"QA":["precision"]}}}
```

Six of the 24 nominal orders require precision. Every completed pump entails three component inspections and one final inspection. At one-minute resolution, ordinary inspection lasts 45 minutes and precision inspection lasts `ceil(45 × 3/2) = 68` minutes. The single calibration kit is occupied throughout inspection, and its life is measured in processing minutes.

Therefore minimum inspection occupancy is:

`18 × 4 × 45 + 6 × 4 × 68 = 4,872 minutes`.

The kit begins with its full 600-minute life. Each service restores at most 600 minutes and takes 60 minutes while holding the kit. Even granting perfect life utilization, at least:

`ceil((4,872 − 600) / 600) = 8 services`

are necessary. Processing plus service requires at least **5,352 kit-minutes**.

Service needs a setup-qualified worker; inspection needs a QA-qualified worker. For this instance, the **union of those qualified worker pools** is unavailable during six 30-minute break intervals per day. Over four days, the tool has at most:

`5,760 − 4 × 6 × 30 = 5,040 usable minutes`.

Thus `5,352 > 5,040`, a **312-minute deficit**, before any setup, transport, quality failure, startup delay, urgent order or disruption.

This calculation does **not** add a generic idle penalty on top of services. It bounds processing and service together by one tool's capacity inside the **union** of the processing/service worker calendars. A break usable by a service worker would not be removed from that union. Both activities are unavailable in these particular break intervals.

This certificate assumes the instance supplies one kit throughout the horizon, enforced certification, full attendance at QA and servicing, and the exported breaks. An allowed extra kit, changed break coverage, different service/life rule, or longer horizon requires recomputing the bound. It does not certify infeasibility of a revised factory with additional capacity.

For scale, with the same every-fourth-order precision pattern:

| Nominal orders | Minimum QA + necessary service | Qualified calendar capacity | Interpretation |
|---|---:|---:|---|
| 22 | 4,840 min | 5,040 min | Necessary condition passes; only 200 min slack before startup/transport/setups/rework |
| 23 | 5,020 min | 5,040 min | Necessary condition passes; only 20 min slack |
| 24 | 5,352 min | 5,040 min | Certified impossible with one kit |

Passing the first two rows does **not** establish feasible schedules. In particular, the kit cannot begin useful inspection at time zero; the table grants that startup period free. No claim that 22 or 23 orders can actually finish is made here.

## Labor bounds and attendance

For each required recipe step, the code minimizes the tabulated integer duration over all eligible machines and **all explicitly permitted certified modes**. Zero setup time is granted. It uses the exported attendance table rather than assuming that every automatic machine needs a worker throughout its cycle.

For a same-family batch with maximum size `B`, if each member has independently minimized duration `d_i`, then every actual batch of duration `D` satisfies `B × D ≥ sum(d_i)`. Summing this relaxation by process/family gives a valid optimistic processing/attendance bound. No claim is made that these ideal batches can be formed on time.

Without precision restrictions, the original coarse profile needs at least **1,152 fully attended processing worker-ticks**, while ten workers supply only **1,120 ticks** after shifts and breaks. With the explicit precision rules, this becomes **1,230 ticks**. Tool servicing adds at least 56 ticks in this coarse certified instance, and setups, maintenance and worker walking are still omitted.

In the refined certified profile, the declared automatic start attendance reduces the processing labor bound to **8,772 worker-minutes**, against **16,800 available worker-minutes**. Necessary tool servicing adds at least 900 worker-minutes (480 calibration, 360 milling and 60 welding). This aggregate labor test therefore does not prove refined-model infeasibility. A separately reported full-attendance counterfactual must not be confused with the implemented automatic-attendance model.

The code also enumerates every subset of processing skills. Demand for that subset cannot exceed the total calendar capacity of workers qualified for at least one included skill. These necessary cuts expose multiskill competition without incorrectly assigning one worker's capacity independently to every skill.

## Why the transport bound is valid

Every component starts at `RAW_A`, follows its required process sequence, and must reach the same assembly machine as its two matching components. The resulting pump must pass final QA and physically reach `SHIP_B`. AGVs carry one component/unit at a time.

The code computes all-pairs graph shortest paths and a layered dynamic program over eligible machines. It evaluates every eligible assembly machine as a **shared join**: the three minimized component paths all terminate at that assembler, and the pump's remaining path starts there. It then minimizes the combined cost. It never independently sends the three components to different assemblers and adds those incompatible optima.

Separate exact relaxed DPs minimize loaded distance, number of moves, loaded travel plus handling, and interhall crossings. Their minimizing routes may differ. Each number is independently a lower bound for every complete physical schedule; it is not a proposed feasible schedule.

For this layout, each pump requires at least 19 movements: six housing legs, six rotor legs, five flange legs, and two final-pump legs. Each nonzero move costs its shortest loaded travel plus one loading and one unloading tick. Staying on the same physical machine would cost zero, rather than inventing a needless move.

The minimum is 50 loaded travel ticks plus 38 handling ticks = **88 AGV-ticks per pump**. Each of the three components must cross from its raw-stock hall A to assembly hall B, yielding at least three loaded crossings per pump.

Loaded travel alone consumes at least `1,200 × 2 = 2,400` SOC units. All four initial batteries are granted free, totaling 480 units. Charging adds at most 12 SOC units per tick, so at least `ceil((2,400−480)/12) = 160` additional AGV charging ticks are unavoidable. This valid lower bound grants empty traction, terminal reserve and travel to chargers free.

## Other checks and limits

- Per-process machine occupancy is compared with all eligible machines' total horizon capacity.
- Tool processing plus necessary service is compared with tool capacity. For fully attended tool processes, the processing/service worker-calendar union tightens this capacity.
- Initial stock is 30 blanks of each component type, versus 24 required nominally. A stock shortfall is reported without declaring infeasibility when procurement may add stock.
- Quality failures, scrap, rework, replacements, urgent arrivals, shocks, maintenance, setups, worker movement and power limits are relaxed away. They cannot rescue an otherwise impossible fixed-capacity nominal workload.
- Extra machine/tool purchases change the capacity assumptions. Initial WIP and purchased finished components also change the nominal source/route assumptions.

## Verification performed

The layered machine-path DP was compared with exhaustive enumeration of every eligible-machine path for each of the three component recipes and both assembly joins. It also passed a synthetic counterexample where choosing the nearest first machine is globally worse than choosing a farther machine. Numeric regression checks reproduced coarse AGV requirements (2,112 / 2,272), 72 bridge crossings, refined certified QA work (4,872), service-inclusive tool work (5,352), worker-calendar capacity (5,040), and the 312-minute deficit. Removing certification explicitly removes that refined certificate, as expected.

## Material envelope of the held full factory

The stretch case's32 initial orders has a concrete structural meaning. Each shipped pump irreversibly consumes one matched housing, rotor and flange. Each type has30 initial blanks and one scheduled delivery of four, for34 total. Replacement components consume additional blanks. Canonical initial component records are unreleased demands; their existence does not create extra stock. The optional paid capacity action adds a calibration tool, and emergency material procurement is outside the held action domain.

Consequently, if realized demand is `D`, every policy has at least `max(0,D−34)` missing orders, even with unlimited calendar time, perfect quality and free processing/transport. Rush adds two demands with probability one half. With33 or34 initial orders, the all-orders-fulfilled probability is therefore at most50%; with35 or more it is zero.32 is the largest initial count with no material-only obstruction on either rush branch. Passing that necessary condition does not establish a feasible schedule, a reliable controller or secondary optimality.

This is a conservation argument under the actual held inventory/action domain; it needs no independence assumption for quality draws. It is separate from the [idealized quality ceiling](STAGE2_IDEAL_QUALITY_CEILING.md) and the realized-tape quality/material certificates. The independent arithmetic export at [structural-stock-envelope/report.json](../output/stage2-search/structural-stock-envelope/report.json) enumerates all eight exogenous leaves for initial counts28–36, reads stock/delivery/reveal tables from the unchanged numerical model, records source hashes and executes no factory simulations. Its horizon is240h, which includes both possible scheduled delivery times; the same total-stock ceiling applies to the96h full model.
