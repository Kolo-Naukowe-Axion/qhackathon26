# Stage 1 offline refinement

## Goal
Improve reliability of actual valid samples while retaining optimal makespans 4/8.
Prefer a shallower QAOA circuit if its validation probability remains at least 99.5%.

## Success Metric
Mean valid-sample fraction on fixed seeds; QAOA also reports exact statevector probability.
No statistical claim across different scheduling instances is made.

## Constraints
- Tier: 1, local foreground execution; pause_every: never (user requested continued iteration).
- max_iterations: 6; max_seconds_per_iteration: 300.
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

Follow-up hypothesis: a slower cooldown can escape the remaining local minima; compare linear and geometric schedules at higher sweep budgets. Prior best: 98.372% valid, geometric 8000.

| 1 | linear 8000 | 99.41406% | 0.5509 | keep |
| 2 | linear 16000 | 99.60938% | 1.0611 | keep |
| 3 | linear 32000 | 99.80469% | 2.1444 | keep |
| 4 | linear 64000 | 99.86979% | 4.2115 | retain evidence; do not promote |
| 5 | geometric 32000 | 99.47917% | 5.2914 | retain evidence; do not promote |
| 6 | linear 16000 beta .1..8 | 97.98177% | 1.3533 | retain evidence; do not promote |
