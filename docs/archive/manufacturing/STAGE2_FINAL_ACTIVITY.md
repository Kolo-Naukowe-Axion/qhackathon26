# Physical activity in predeclared retained final traces

`stage2/final_activity.py` is a standalone standard-library postprocessor outside the frozen evaluator's source list. It does not run the factory, a policy or a checker. It verifies manifest/protocol seals, measured-row/trace/instance hashes and existing physical/identity/terminal statuses, then counts recorded events and intervals. Its own source hash and a code snapshot accompany each report.

The selection is fixed by the manifest: the first declared environmental seed and first declared actor in each of the eight disruption leaves. First means declaration order, not lowest numerical seed/actor. A missing, corrupted or invalid chosen execution is retained as a failed activity entry and never replaced with an interesting or successful alternative. Aggregate activity is suppressed unless all eight selected entries verify. Six synthetic semantic/integrity tests cover those rules, event/operation distinctions, actual versus requested arrivals, horizon-boundary arrivals, incomplete charging intervals, battery flows/curtailment and hash/leaf rejection. Fixtures are not additional factory experiments.

Reports are `output/stage2-search/final-activity/selected-12.json` and `selected-stretch-32-v2.json`, with adjacent `.analysis-source.py` copies. Both verify all eight selected entries. The earlier stretch v1 report remains retained; v2 adds explicit horizon, energy/contact checks and source capture without changing its activity counts. The context has256 evaluation environments, but **the activity summaries describe only eight retained realizations per context**. They are not probability-weighted averages or rates over all256, and actors are not additional environments.

| Observed activity per retained case, unweighted eight-case mean |Selected12:96h|Stretch32:240h|
|---|---:|---:|
|Completed production operations|208.125|539.125|
|Family setups|46|42.75|
|Setup occupation, minutes|1642.5|1567.5|
|Rework operations, including repeat QA|7|18.5|
|Completed QA inspections|55.5|141.25|
|Failed QA inspections|3.5|9.25|
|Machine maintenance completed|6.875|29.375|
|Portable-tool services completed|10|29.875|
|AGV transport arrivals|260|651.5|
|AGV charge sessions ended|30.625|75.25|
|Completed bridge crossings, empty and loaded|136|340.5|
|Worker hall walks|97|254.5|
|Actual initial BOM joins|13|33|

The horizons, loads and selected policies differ. These are descriptive event counts, not an efficiency or algorithm-scaling comparison;240hours provides additional resource-hours. Fewer setups at32 orders does not establish their cause or a universal batching improvement.

Each of the sixteen retained traces uses14 of15 machines; F3 is unused. Every case receives the rented calibration kit and actually uses it after arrival. A rental request is counted separately from its delivered physical birth and later AGV/tool use. Assembly consumes three recorded matched parents:104 joins/312 consumption events at12 and264/792 at32 across the eight cases. Multiunit process-completion events do not become multiple completed operations; completed operation IDs are deduplicated.

Completions/reveals at the horizon boundary are included because the engine processes that boundary before stopping. Travel/attendance/setup durations clip to `[0,H)`, while energy rows cover ticks0 throughH-1. Charging commitment, observed charging duration and an ended session are separate counts. Bridge crossings count the actual HUB_A/HUB_B legs, including empty repositioning, not a schematic animation or every transport request.

Battery charge/discharge, AC input/output, grid import, nonnegative-grid/no-export behavior, solar curtailment, SOC transitions/bounds and cap contact are explicit per trace. Curtailment is not export and stationary battery output is not a grid feed-in. Activity or contact is not a causal bottleneck certificate. The reports do not redo input-buffer occupancy: recovery can transfer a staged component again before consumption, so a simple next-consumption reconstruction would overcount that residence.

No scrap or replacement occurs in these sixteen retained examples. This does not imply absence across the full evaluation. In particular, the separate seed10020 audit-only proof witness contains an unavoidable final-pump scrap, but was not one of these predeclared first-per-leaf traces and must not be inserted into this set. Conversely, an enabled mechanism is not counted as exercised merely because it appears in the model's feature flags. There are no marginal-capacity or general deadlock-freedom claims.
