# Observed Stage2 mechanism activity

The two retained hard-tool-home examples exercise most of the physical model. Both independently pass `check_trace`; TRAIN0 ships13/14 orders and VALIDATION100 ships14/14, including two revealed urgent orders. Physical validity and the stationary terminal reserve are satisfied even in the incomplete run. These are development examples, not final evaluation tapes or evidence of universal reliability.

Reports: `output/stage2-search/activity-tooling-n12-train0.json` and `activity-tooling-n12-val100.json`. Each records the absolute input path, compressed-file and decompressed-JSON SHA256, checker hash/coverage/unsupported list, and audit-source hash. Raw inputs are `tooling-routing-train32/n12-s0-hard-all.json.gz` and `tooling-routing-validation16/n12-s100-hard-all.json.gz`. The instance has15 physical machines,10 workers,4 AGVs and5760 one-minute execution ticks.

| Observed mechanism | TRAIN0 | VALIDATION100 |
|---|---:|---:|
| Production machines used |14/15|14/15|
| Completed production operations |225|230|
| Nonzero family setups |63|57|
| Setup occupation, minutes |2475|2205|
| Multiunit homogeneous heat batches |5|6|
| BOM joins creating pumps |14|14|
| Precision-mode operations |20|22|
| Failed QA inspections |4|6|
| Repair-route production operations, including repeat QA |8|12|
| Tool services |11|13|
| Machine maintenance |7|7|
| Physical portable-tool moves |6|6|
| Part transports |272|278|
| Empty travel, aggregate AGV minutes |654|648|
| Loaded travel, aggregate AGV minutes |1000|940|
| AGV charge sessions |34|33|
| Worker hall walks |132|124|
| Attended activity, aggregate worker minutes |9185|9186|
| Walking, aggregate worker minutes |264|248|
| Output-held time, aggregate machine minutes |7195|3601|
| QA1/QA2 full input-or-reserved-buffer minutes |2256/2174|1289/1093|
| Delivered rental calibration kits |1|1|
| Scheduled stock deliveries |1|1|
| Grid derating minutes |0|720|
| Minimum grid headroom, kW |0|0|
| Stationary battery charge/discharge minutes |200/0|200/0|
| Minimum raw housing/rotor/flange stock |18/18/18|18/18/18|

All10 workers perform attended work. Attendance uses actual `worker_intervals`, with the contract's whole-operation fallback only where explicit intervals are absent, including service/maintenance. Walking is separate; occupied time is the union of attendance and walking, never nominal full automated processing duration. Independent checker calendars enforce skills, shifts, breaks and travel. These counts do not measure how much each calendar restriction changes the objective.

Output-held intervals start at operation completion and end at physical pickup. A heat batch blocks until its last member is picked up. Output with no later pickup stays held until the execution horizon. The audit unions intervals per machine, clips every duration to the execution horizon, and separately confirms zero overlap with processing or maintenance in both examples. The current physical contract rejects starting another operation while the previous output remains present; it does not support implicit same-machine handoffs without clearing output. A corruption test verifies rejection, preventing such a trace from becoming activity evidence.

Input occupancy includes an inbound reservation from **dispatch**, before pickup or arrival, until the operation consumes that unit. Assembly consumes its three parent units. Output-held units do not also count as inputs. Full buffers and zero grid headroom are observed constraint contact; they do not establish a causal bottleneck or the gain available from more capacity.

Several enabled mechanisms are inactive here. F3 has zero production under the selected hard-home routing restriction; it remains physically eligible. Neither trace uses eco/turbo modes, stationary discharge, terminal scrap or replacement. VALIDATION100 realizes a delayed delivery; neither example realizes a machine outage. Both use the priority selector, so their QUBO calls, simulated QAOA calls and local bit counts are zero. A separate energy ablation is required to demonstrate stationary discharge. General nonanticipativity, emergency buying, leased machines, interruption/resume and hard operating/carbon caps are not established by this report; the checker explicitly lists its unsupported coverage, and `feature_status` is retained as descriptive metadata rather than counted as exercised evidence.

## A separate stock-activation stress scenario

`output/stage2-search/activity-stock-stress-n32-train0/` retains a checked full trace and audit. This deliberately uses32 initial orders and WIP32, with the same stock, delivery, resource physics and TRAIN0 tape. It is a mechanism demonstration, not a selected production policy: it ships only11/34 orders. The run took18.93 local CPU seconds and its physical source hashes remained unchanged.

Each raw stock starts at30 and first reaches zero at tick360. The31st release of each component recipe occurs at tick1800, when the actual D1 delivery adds four blanks per type. The two urgent orders later consume the final stock. Thus finite supply really constrains further blank release during that interval; this does not show that stock is the dominant cause of poor throughput. No stock exhaustion is observed in either main n12 example, so the main benchmark should not be described as stock-constrained.

Verification: eight tests in `tests/stage2/test_activity_audit.py` cover unions, last-member batch pickup, missing pickups, actual checked partial horizons, illegal same-machine continuation, dispatch-time buffer reservations and BOM consumption, inventory replay, and explicit worker attendance. Run `python -m unittest discover -s tests/stage2 -p test_activity_audit.py -v` with the Stage2 environment. Generate a new report with `python -m stage2.activity_audit TRACE.json.gz --output REPORT.json`.
