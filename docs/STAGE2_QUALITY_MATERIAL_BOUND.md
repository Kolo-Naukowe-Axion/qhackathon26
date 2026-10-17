# Realized primary lower bounds from quality and finite stock

For eight full TRAIN scenarios with32 initial orders, possible two urgent orders,
and a240-hour horizon, the retained schedules attain the minimum possible number
of unfulfilled orders: zero on seven tapes, one on seed6. This certifies only the
primary objective on these eight realized instances. Deadline debt, energy cost
and carbon are not globally optimized. Extra calendar time does not represent
an algorithmic speedup at the default96-hour deadline.

The nonzero bound is substantive. Seed6 reveals34orders and provides34housing
blanks (30initial+4delivered). The original `P05/housing/1` has first QA draw
0.002496832313424578 and repair QA draw0.009310723651156354. Every legal housing
route includes heat treatment with at least0.02 manufacturing defect risk;
nonnegative wear and accumulated history cannot reduce this floor. Repair leaves
fixed residual risk0.02. Both draws lie safely below even conservative floors
0.0199999999. The original housing is therefore unusable under every policy,
even one knowing the tape. A successful P05 requires a replacement consuming a
second physical housing blank. Matched BOM lineage prevents substitution from
another product. Delivering all34orders would consume at least35housingblanks,
contradicting the supply bound. The checked33-shipment schedule attains the
missing-order lower bound1.

`stage2/quality_material_bound.py` reconstructs hash uniforms independently with
exact fractions and uses conservative required-step risk floors. A three-material
unit-profit knapsack relaxation bounds the number of orders that could satisfy
necessary blank requirements. Its chosen subset is not itself a schedule; it
ignores time, workers, machines, transport, energy and other constraints, making
its shipment count an upper bound. Only matching it with a full checked physical
witness certifies an attained primary optimum.

The proof is bound to the audited engine action domain and fixed unit identities.
It rejects changed repair/replacement limits, accepted initial WIP, extra births,
non-RAW original units, duplicate identities, altered assembly recipe, intermediate
QA, negative mode wear, and risk parameters invalidating monotonicity. It requires
an independent reaudit when the engine digest changes. Generic final-pump bounds
assume the engine's fixed `${order}/pump/1` identity; they do not license choosing
fresh UIDs to redraw inspection randomness. The concrete housing proof relies on
original component identities, also enforced by the replay checker.

Keyed future draws appear only in this offline certificate. They are never
controller features, policy decisions, lookahead real-tape inputs or training
labels for a deployed predictor. No reserved final tape was used to design this
proof or select its example. Root and two independent agents audited the theorem,
guards, exact knapsack on small exhaustive cases, and actual seed6 witness.

Evidence: `output/stage2-search/quality-material-primary-bound/report.json`,
eight compressed full traces and certificates, frozen source copies, reproducible
witness driver and original source manifest. The independent audit record is
`docs/STAGE2_QUALITY_MATERIAL_INDEPENDENT_AUDIT.md`. Run
`python -m unittest tests.stage2.test_quality_material_bound` for the five guard,
arithmetic, relaxation and sensitivity tests.
