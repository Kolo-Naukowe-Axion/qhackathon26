# Stage 2: measured capability and limits

Status: 17 October 2026, all ten final cohorts completed: 23,552 executions, 74 method/context groups and no invalid rows. The [complete report](../output/stage2-search/final-complete-report/report.json) contains all 41 declared paired contrasts. An [independent audit](../output/stage2-search/final-independent-audit/complete-audit-seal.json) verifies 592 original retained traces and fresh numerical anchors for every row. Policy/source selection was sealed before any final outcomes; no policy is switched using these results.

## What we can do

The executable factory retains 15 machines in two halls, four physical AGVs, ten skilled workers with shifts/breaks, three-component matched BOMs, shared portable tools and service, setup families, alternate manufacturing modes, batch heat treatment, maintenance, finite reserved buffers/output blocking, raw-stock delivery, quality/repair/replacement, charging, stationary battery/solar/grid limits, tariffs/carbon, urgent orders and sequentially revealed disruptions. See [the numerical and executable scope](../stage2/README.md). It is a synthetic model; geometry and timings are not industrial calibration.

The preselected cheap controllers have this final performance. Every row uses 256 complete environment tapes, 32 per exogenous leaf, weighted by the actual leaf probabilities. Actor replicas, where applicable, are nested inside those tapes. Demand may increase by two urgent orders.

| Initial orders | Simulated calendar | All orders shipped | Mean missing orders | Mean cutoff-censored deadline debt, minutes |
|---:|---:|---:|---:|---:|
|10|96 h|98.97%|0.0103|1,314.74|
|11|96 h|97.92%|0.0317|2,289.97|
|12|96 h|94.98%|0.0750|3,263.63|
|13|96 h|88.22%|0.1492|4,664.86|
|14|96 h|80.66%|0.2781|5,983.07|
|16|96 h|8.80%|2.6906|13,040.94|
|24|96 h|0 observed|10.0209|31,238.54|
|32|**240 h**|91.02%|0.1023|113,997.54|

This is the frontier of the tested controllers. It is **not a physical infeasibility threshold**. The 32-order case grants six additional days with unchanged resources and deadlines, and incurs heavy lateness. It must not be presented as solving 32 orders in 96 h. Zero observed all-success cases at 24 does not mean zero true probability; the conservative one-sided 95% boundary upper bound is approximately 1.81% under the report's independent bounded-tape assumptions.

## Which approaches helped

An eight-segment CEM schedule is cheap to deploy and improves 24-order mean missing from 11.5992 for the original strong heuristic to 10.0209. Its paired exploratory 95% mean-difference interval versus a broader searched static control is [-0.5511,-0.1981] missing orders. At 16, its validation lead reverses: 2.6906 missing versus 2.6030 for that static and 2.4194 for PPO. We preserve the preselected CEM result and the reversal.

Independent-future model-predictive control improves 12-order mean missing to 0.0377 and 16-order mean missing to 2.3014. At 16 it completes every order on 17.41% of tapes, versus 8.80% for the selected CEM; the paired exploratory 95% mean-missing difference is −0.3892, interval [-0.5680,-0.2163]. The 13-order improvement is uncertain, and 14-order MPC worsens mean missing to 0.3414 versus 0.2781 for the selected cheap policy. At 24, four-future MPC misses 11.2677, worse than the selected CEM's 10.0209. More planning is not uniformly better.

PPO does not establish an adaptive-RL benefit here. The 16-order PPO 2026 and its matched constant static control have identical fulfillment on all 256 final tapes. A separately declared diagnostic reproduces the sole secondary-metric difference: PPO switches actions 3→1→3 on seed 10062, but both ship 9/18 and PPO worsens debt/cost. This disproves a globally constant-policy interpretation without creating evidence of useful adaptation. [Exact audit](../output/stage2-search/final-independent-audit/postfreeze-rare-ppo-10062/report.json), [selection and cost distinctions](STAGE2_METHOD_SELECTION.md).

A separate fixed TRAIN-only neighborhood audit exhausts 41 schedules at 12 orders
and 741 each at 16/24, across eight TRAIN tapes: 12,184 executions plus 24 explicitly
declared oracle witness replays. Total misses, original → best **single shared**
schedule → **per-tape hindsight** oracle, are 0→0→0 at 12,21→19→15 at 16 and 76→76→69
at 24. The original receives no primary gain from a common nearby schedule at 24.
These are unweighted eight-TRAIN-tape totals, not held-out population estimates.
The oracle uses outcome knowledge and is not a deployed policy; the finite
neighborhood is not all 6^8 schedules. All necessary lower bounds are zero, so
positive minima do not prove a physical capacity limit. [Exact domain, flatness and
costs](STAGE2_SCHEDULE_NEIGHBORHOOD_AUDIT.md).

## What the quantum component establishes

Simulated QAOA actually selects local dispatch actions in the full physical factory. Across the final stochastic comparisons it executes 452,338 circuits, of which 174,965 have coupling and 272,854 are trivial one-bit circuits. 40,455 larger offers use explicitly recorded classical fallback. Actual integrated circuits have at most five **total** bits, including slack. This is decomposition with substantial classical state/filtering/angle-search work, not a lossless five-qubit encoding of the factory.

At 12 orders, mean missing is 0.1503 for QAOA,0.1183 for matched SA and 0.1401 for matched uniform sampling. QAOA−SA is +0.0320 with nominal 97.5% interval [-0.0144,+0.0794]; QAOA−uniform is +0.0103 with [-0.0426,+0.0636]. These two predeclared primary contrasts correct for a family of two. They demonstrate **no quantum advantage** and do not prove equivalence. Other comparisons are exploratory pointwise 95% intervals. A tested CEM/QAOA hybrid also regresses and was rejected. No physical QPU or VeloxQ result is claimed.

## Proof and reproduction

An independent checker reconstructs resource occupation, transport, BOM consumption, power/SOC, quality and metrics against a freshly rebuilt instance; a separate identity audit fixes the unit/attempt quality stream. Complete-group audits reject hidden invalid or dropped executions. Empirical paired-prefix checks probe future-information leakage. These checks establish the stated coverage, not universal nonanticipativity or global optimization.

On 93.44% of final 32-order tapes, executed missing matches a conservative offline quality/material lower bound; this certifies the **primary missing-order objective on those realized tapes**. A particularly clear audit-only witness at seed 10020 proves a nonzero optimum: 32 demanded, 31 shipped, and the last pump's unavoidable initial-plus-repair failure forces at least one miss. Thus `L=U=1`. Hidden QA draws enter only the offline proof. The posthoc explanatory replay is excluded from the 256-tape estimates and the predeclared presentation replays. Deadline debt/cost optimality remains unknown. [Proof illustration](STAGE2_JUDGES_EXPLANATION.md#an-audit-only-example-of-a-nonzero-optimum).

The stock envelope explains why 32 is a meaningful stretch: 34 blanks/type permit 32 initial plus two rush demands, whereas 33/34 initial orders have all-success probability at most 50% from material conservation alone, and 35+ at most zero. This needs no QA independence assumption and does not certify schedulability. [Conservation and necessary bounds](STAGE2_CAPACITY_BOUNDS.md#material-envelope-of-the-held-full-factory).

The separate deterministic four-pump CP fixture currently has a certified optimum interval [1480,1567] minutes. It disables many flagship mechanisms; this is not the stochastic factory's global gap. A bounded two-hour follow-up on that unchanged fixture is running. [Reference scope](STAGE2_REFERENCE_MULTI.md).

Fresh all-rule development demos run in roughly 1.3 s on the local CPU: the static and small-QAOA paths use the Python standard library; the saved CEM path additionally needs NumPy. A clean minimal environment reproduced all three. These are development demonstrations, excluded from final estimates; hardware/version details and measured timings are retained. No GPU training was needed, and recorded GPU-hours and physical-QPU calls are zero.

The completed final campaign used 70.42 allocated CPU-hours and 68.58 measured episode process CPU-hours. These are part of the research total, not additional to it. As of 01:27 UTC the research ledger has 400.11 finished allocated CPU-hours including failed jobs; only the bounded exact-reference job remains running, with 3.28 allocated CPU-hours elapsed at that snapshot. Local work is separately retained where measured, not a complete host-wide CPU meter. Nested planning/check/inference timers must not be added together, and sums of episode wall times are not campaign elapsed. [Reconciled immutable accounting snapshot](../output/stage2-search/final-compute-0127-summary.json).

## Submission status

The [requirement matrix](STAGE2_JUDGES_EXPLANATION.md#formal-requirement-matrix) distinguishes technical evidence from submission duties. Both mandatory baseline QAOA simulator artifacts exist, but GitHub metadata last checked at 00:42 UTC reports the repository private. The public-MIT requirement is therefore not met yet. Stage 2 remains local under the user's publication hold. Completed video, team declaration and form receipt are unverified. No publication, submission or jury acceptance is asserted.
