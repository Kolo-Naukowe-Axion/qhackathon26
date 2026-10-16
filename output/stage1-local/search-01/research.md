# Stage 1 offline refinement

## Goal
Improve reliability of actual valid samples while retaining optimal makespans 4/8.
Prefer a shallower QAOA circuit if its validation probability remains at least 99.5%.

## Success Metric
Mean valid-sample fraction on fixed seeds; QAOA also reports exact statevector probability.
No statistical claim across different scheduling instances is made.

## Constraints
- Tier: 1, local foreground execution; pause_every: never (user requested continued iteration).
- max_iterations: 12; max_seconds_per_iteration: 300.
- Evaluator: python -m solver.refine (JSON summaries, independent feasibility and optimum guard).
- Keep policy: score_improvement, separately for quantum and classical candidates.
- noise_runs: 3 screening seeds; ten new seeds validate the selected settings.
- min_delta: 0.001; target: quantum >=99.5% valid with <=3 layers; classical >=99.5% valid.
- Guard: exact optimal makespan, real unmodified samples, no remote API/hardware, no answer warm start.
- Existing working tree is preserved; only settings change between trials, with no Git resets or automatic commits.

## Current Approach
Four-qubit domain-wall QAOA and 39-variable one-hot simulated annealing.

## Search Space
Shared or per-qubit X mixer; layers 2..5; 8..32 restarts.
Anneal with 2000..8000 sweeps, geometric/linear schedules, default/custom beta range.

## History
| Iteration | Candidate | Mean valid | Median seconds | Decision |
| --- | --- | --- | --- | --- |
| 1 | shared p3, 32 restarts | 95.75195% | 6.0675 | keep |
| 2 | shared p4, 16 restarts | 97.53418% | 4.8912 | keep |
| 3 | local p2, 32 restarts | 81.74642% | 5.9937 | retain evidence; do not promote |
| 4 | local p3, 16 restarts | 100.00000% | 6.9548 | keep |
| 5 | local p4, 8 restarts | 100.00000% | 5.7121 | retain evidence; do not promote |
| 6 | shared p5, 16 restarts | 99.72331% | 8.4227 | retain evidence; do not promote |
| 7 | geometric 2000 | 94.79167% | 0.3377 | keep |
| 8 | geometric 4000 | 96.74479% | 0.6588 | keep |
| 9 | geometric 8000 | 98.37240% | 1.3216 | keep |
| 10 | linear 2000 | 97.85156% | 0.1369 | retain evidence; do not promote |
| 11 | geometric 2000 beta .1..32 | 94.98698% | 0.2753 | retain evidence; do not promote |
| 12 | linear 4000 beta .1..32 | 97.52604% | 0.1792 | retain evidence; do not promote |
