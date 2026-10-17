# Matched priority-rule experiments

All comparisons below use the same full minute-grid factory, seeds 0–7, 96-hour horizon, physical checker and priority selector. Both rule families were selected on these training seeds. These are training comparisons, not held-out evidence. All 288 new-rule runs passed physical checking.

| Initial orders | Previous grid best | New priority best | Mean missing: previous → new | Mean tardiness minutes: previous → new |
| --- | --- | --- | ---: | ---: |
| 12 | w4-standard-lease1-priority | w8-family-standard-lease1 | 2.625 → 1.750 | 7573.4 → 8907.4 |
| 16 | w6-standard-lease1-priority | w2-family-standard-lease1 | 5.625 → 7.250 | 15928.8 → 18041.5 |
| 24 | w3-turbo-lease1-priority | w4-family-standard-lease1 | 13.500 → 13.500 | 34978.8 → 34074.0 |

The added family rule helps fulfillment at load 12, does not beat the existing load-16 incumbent, and improves tardiness at equal mean fulfillment at load 24. This supports retaining different teachers by workload. It does not establish a universal benefit from family priority.

`protocol.json`, `measurements.jsonl`, and `summary.json` contain the 288-run new-rule experiment. The previous grid reference is `output/stage2-search/axion-results/grid-v1-6116782/`. `matched-comparison.json` preserves both complete summary rows.

The separate `validation-load8/` experiment pairs the same 16 development-validation tapes 100–115. Family WIP6/standard/lease completes 16/16 at mean tardiness 1460.19 minutes; the earlier WIP6/eco/lease rule completes 15/16 at 2191.56 minutes. Both have 16/16 physically valid traces. These validation results informed development and must not be described as final untouched test results.

Timing is retained for reproducibility, but the earlier grid ran on Axion and these added-rule measurements ran locally. Do not infer a solver speed comparison from those different machines. Neither experiment used GPUs or quantum hardware.
