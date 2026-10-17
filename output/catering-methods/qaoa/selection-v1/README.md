# QAOA optimizer/depth selection (TRAIN cases only)

`opt_bench.py` compares angle-optimization strategies (random best-of-N, COBYLA,
L-BFGS-B with finite differences, random-then-COBYLA, layerwise COBYLA) for the
`xy` and `xy_multiangle_warm` variants at depths 1–3 and 64/256 evaluations,
5 seeds each, CVaR alpha=0.1, exact sector simulation. Cases: complete cell,
foundation-v3 S0 and S1. S2/S3 were never run. `results.jsonl` holds the
median loss, P(optimum) and P(valid) per row.

Selected (best mean rank of median P(optimum) at both budgets):
`xy_multiangle_warm`, depth 3, `layerwise`.

Note: the cell rows come from a first run whose case list also contained S3;
it was stopped before any S3 row was computed (no S3 output exists), and the
remaining TRAIN rows were produced by the same script with cases S0/S1.
