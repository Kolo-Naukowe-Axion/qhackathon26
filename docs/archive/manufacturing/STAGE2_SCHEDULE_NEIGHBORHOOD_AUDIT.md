# Fixed schedule neighborhood headroom audit

This is an additional TRAIN-only diagnostic after original final evaluation
closed. It does not tune or replace a selected policy, reopen validation, or
alter final estimates. A causal time schedule can be evaluated normally; choosing
the best schedule separately after seeing each tape is an offline clairvoyant
oracle over the enumerated set.

The frozen selected six-action CEM checkpoint has SHA256
`d2ae8337daadd1baec7840e29b69500d91a548bbd3c0b4b5378f2b22ba6203e9`.
The exact original Controller, context weights, admission/recovery/routing/tool
options and original priority dispatch remain in use. The separately audited
maintenance guard is explicitly on. Actor seed is900000, independent of the
environment. No physical source or frozen final evaluation source is edited.

Before outcomes, enumerate lexicographically all eight-segment six-action
schedules with Hamming distance at most1 from the frozen n12 schedule (41), and
distance at most2 for each n16/n24 schedule (741 each). Each runs on all TRAIN
seeds0–7:12,184 executions. Each action changes WIP4/6/8 and QA guard0/4 only;
the existing eight-segment Controller and interval retain their original timing.
This is one pass, without iterative coordinate ascent or expanded search.

Every execution retains metrics, complete source and checkpoint hashes, physical
instance hash, physical/checker/identity/decode validity and CPU/wall costs.
The physical trajectory hash includes operations, moves, worker moves, events,
energy and metrics; it excludes controller decisions and timing. Distinct hashes,
distinct metric outcomes and original-trajectory-equivalent schedule counts
measure flatness, not causal credit assignment quality by themselves. Seed0
traces for the original three schedules are retained. All invalid traces and
failures remain; any invalid stops new submissions. Missing, duplicate or invalid
rows suppress the affected context envelope instead of computing a valid-only
minimum. All variants on each tape must have the same instance hash.

Only after a complete valid neighborhood, report lexicographic minima and maxima
of (missing orders, deadline debt, total cost), the best common fixed schedule
over these eight TRAIN tapes, and the aggregate of per-tape oracle minima. These
are descriptive development numbers, not independent generalization estimates,
the full6^8 optimum, global factory optimality, or evidence of physical
infeasibility. Separately replay the first lexicographic minimum schedule on
each context/tape as an oracle witness (24 maximum), retaining full checked
traces and requiring exact grid metrics and physical-trajectory hash equality.
Oracle witnesses never enter original final scores.

A checked zero-missing oracle witness establishes physical feasibility for that
one tape at that horizon, despite any failure by the original schedule. A
positive minimum over these41/741 schedules does **not** establish physical
infeasibility: a schedule outside this neighborhood, a state-dependent rule, or
another routing/dispatch policy may do better. Improvement measures a restricted
controller/search gap, not a certified global optimality gap.

The resource cap is32 CPU workers, zero GPUs, one30-minute Slurm job. Internal
submission budget is28 minutes, reserving shutdown time. Incomplete enumeration
must remain labeled incomplete; partial minima are suppressed. Costs of all
executions and the original checkpoint training remain explicit.

The inherited checkpoint records9,096 fitting episodes,720 reused-validation
episodes and1,216.0855 seconds of32-worker wall time, in addition to its shared
static-prior development. Those historical costs are not charged again as new
audit executions and are not treated as free pretraining. Frozen source is
`output/stage2-search/snapshots/v21p1-oracle-audit`, module SHA256
`7c69a7b69f15ad259ccb1105a1beeab7f8b58bbe09dafedf15b8b90030ea452a`.
The bounded job is6117537; submission metadata and successful exact frozen
spawned-worker smoke are retained under
`output/stage2-search/axion-oracle-audit-v21p1-submission/`.
Small engineering verification is separate: three local test invocations ran15
factory rollouts, and two frozen-worker preflights ran two more. Their CPU time
was not separately retained and is not claimed to be zero; the recorded test
wall times and explicit count are in `preflight-cost-disclosure.json`.

Implementation: [schedule_neighborhood_audit.py](../../../stage2/schedule_neighborhood_audit.py).
Tests: [test_schedule_neighborhood_audit.py](../../../tests/stage2/test_schedule_neighborhood_audit.py).
Five tests cover exact domain counts, original/direct guarded equivalence, actual
worker identity and source guards, paired causality, invalid-envelope gates,
and the distinction between one common policy and the per-tape oracle.

## Complete TRAIN-only result

Job6117537 completed all12,184 grid executions and24 prespecified witness
replays. Every row passes the anchored checker, canonical identity supplement,
source checks and decode gate. All27 retained traces were additionally checked
against fresh numerical instances locally; each witness exactly reproduces its
grid metrics and canonical physical-trajectory hash. Raw rows, report, protocol,
checkpoint and source snapshots were checked against their retained hashes.
The report and supplements are now held byte-stable.

The table sums outcomes over the same eight TRAIN tapes. Each entry is
**(missing orders, deadline debt, cost)**. The common fixed winner is selected
retrospectively on all eight development tapes; the per-tape oracle chooses a
different schedule after each outcome. Neither is a new deployed policy or a
held-out performance estimate.

| Initial orders; actual demands across8 | Original frozen CEM6 | Best common fixed neighborhood schedule | Clairvoyant per-tape neighborhood oracle |
|---|---|---|---|
|12;108|(0,18960,5670.46)|(0,18960,5670.46)|(0,13241,5573.74)|
|16;140|(21,105744,6721.05)|(19,103574,6753.37)|(15,86804,6660.02)|
|24;204|(76,246916,6262.51)|(76,233278,6824.17)|(69,221946,6927.35)|

This does not cure n16/n24 **controller shortfalls within this neighborhood**.
It is not a physical capacity threshold. Only26/741 n16 schedules have a
lexicographically better common aggregate than the original;4 tie and711 are
worse. At n24 only2/741 improve the common aggregate, both through deadline debt
with the same76 missing orders;1 ties and738 are worse. At n12,13/41 tie and28
are worse. Its first lexicographic common winner changes a nominal action but
has the same physical trajectory as the original on all eight tapes.

The independent necessary quality/material bound was applied only after the
complete grid and witnesses were sealed. It gives lower bound0 on all24 TRAIN
instances. Zero-missing checked witnesses certify the primary optimum0 on eight
n12 tapes and one n16 tape. The other15 positive witness minima remain globally
unresolved. No positive primary infeasibility certificate arises here, and no
secondary optimum is claimed.

Nominal schedule multiplicity is substantial, but this is not a wholly flat
domain. Per tape there are13–24 distinct physical trajectories among41 n12
schedules,354–516 among741 n16 schedules, and402–534 among741 n24 schedules.
Schedules physically identical to the original number13–21,4–27 and2–15,
respectively. These hashes exclude controller decisions and timing. Distinct
full metric outcomes and objective triples are also retained separately. These
observations concern this six-action time-schedule neighborhood; they do not
establish a limit for all RL, state-dependent admission, routing or richer
production policies.

Driver wall time was1507.813s. Slurm elapsed1511s on32 CPUs gives48352 allocated
CPU-seconds; consumed CPU was45387s. Worker rollouts report45364.672 CPU-seconds;
these nested cost measures must not be summed. The local complete retention
verification,27 additional checker passes and24 necessary bounds took6.846s
wall/6.826s CPU. No GPU or quantum execution occurred in this audit.

Full retained evidence is
`output/stage2-search/axion-oracle-audit-v21p1-submission/results/` plus its
`retention-analysis.json`, `necessary-bound-supplement.json` and `sacct.psv`.
The2.73MB `compact-supplement/` contains explicit report/protocol extracts,
unchanged supplements/checkpoint/source copies and an immutable evidence index.
It pins full report/protocol/raw-row SHA256 values without packaging their
92.3MB/34.5MB/70.2MB repeated data. The compact extract is **not** a self-contained
audit of all raw rows; the full originals remain retained at those paths.
