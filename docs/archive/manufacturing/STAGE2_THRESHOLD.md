# Interpretable state-dependent factory control

`stage2/threshold.py` searches causal policies over the existing, frozen physical
factory. It adds no machines, relaxes no constraints, and does not change hidden
defects, events or time granularity. Every episode runs the same independent
checker. The purpose is to test a stronger low-dimensional classical controller
alongside static rules, open-loop schedules and the neural PPO controller.

## The controller

At each hourly replanning callback it observes current process queues, accepted
components, overdue orders, time and revealed grid capacity. Its downstream
backlog is `queue_QA + queue_ASSEMBLY + max(0, accepted_components - 3)/3`.
Crossing either the downstream or heat-queue threshold enters a congested state.
It exits only after both queues fall below half their thresholds. This hysteresis
prevents changes from oscillating around one boundary.

Congestion selects the lower CONWIP limit and a congestion machining mode; a clear
factory selects a higher admission limit and a free-flow mode. A late-horizon,
overdue state can select a third mode when downstream congestion is absent. An
optional rule selects eco mode during an actually revealed grid derating. The
policy also chooses family and remaining-route priorities, due-date weight and
when to request the calibration-kit lease. It sees neither the environment seed
nor future outcomes. Rental delivery, investment budget, certification, running
operations and irreversible admission remain governed by the engine.

There are fifteen categorical parameters in routing-v3. Admission limits use 1/2/3/4/6/8;
machining modes use eco/standard/turbo. Other parameters select backlog thresholds,
priority coefficients and lease/late fractions of the public horizon. Two
additional routing coefficients control tool-distance weighting (0/1/2/4/8) and
independent setup scoring (0/3/10/30). These are machine-choice heuristic scores:
zero does not remove physical tool transport or setup duration. The full
domain is exported in every protocol. Sampled lower/upper WIP limits are sorted
into a valid pair, an explicit canonicalization of the factorized proposal.

This controller represents every ordinary static policy in the 48-action neural
experiment: set both WIP limits equal, all modes equal, disable the grid override,
disable late switching and choose an immediate or absent lease request. The
static embedding rejects unsupported setup/noise coefficients rather than
silently approximating a teacher. An integration test compares the actual factory
metrics of a fixed policy against its threshold embedding and independently
checks the resulting trace.

The class is still restricted: it cannot choose every schedule, every possible
state rule or arbitrary continuous thresholds. Aggregate public observations are
not a full Markov state. No global optimality claim follows from tuning it.

## Search and comparisons

Three methods share the exact policy domain, physical model and measurements:

- `cem`: categorical cross-entropy search, with a retained exploration floor and
  elite updates from paired training tapes.
- `random`: random search over the same parameter combinations, retaining a
  strong static/fixed prior as an eligible incumbent.
- `fixed`: the declared physics-inspired prior, or a supplied trained static
  teacher, measured with identical checking and scoring. It stops after its
  useful fixed measurements rather than consuming an arbitrary time allowance.

Every generation compares candidate policies on the **same** training tapes.
Generations cycle through known workloads; each workload has its own parameter
distribution and incumbent. The paired training tapes rotate within 0–31. Before
checkpoint selection, a bounded candidate shortlist is reranked on a common,
explicit training set, default 0–7. Cached results prevent repeated simulation of
the same source/configuration/policy/tape/role. Every actual episode is written
once to `measurements.jsonl`; cache hits and simulation CPU-seconds are reported.

Ranking is lexicographic: physical invalidity, mean unfulfilled orders, risk-
adjusted tardiness, then mean total cost including the lease. Risk-adjusted
tardiness is mean tardiness plus a declared weight (default .25) times empirical
CVaR at .9. Its discrete tail calculation uses a fractional boundary observation,
so sixteen equally weighted samples use the largest value and .6 of the next,
divided by 1.6. It is not the unweighted average of two worst samples. A test
checks that calculation explicitly. Set `--risk-weight 0` when comparing an
expected-tardiness-only search criterion; retain all original reported metrics.

Validation tapes 100–115 select checkpoints periodically. Validation choices
never feed the CEM proposal distribution or its training incumbent. The best
validation policy and the best training-reranked policy are kept separately.
The initial teacher/prior is eligible as a fallback. The final 10000+ holdout is
never run automatically; final evaluation requires an explicit seed list after
the method/model is frozen. Adaptive development on validation must be described
as such, not presented as an untouched test.

## Teachers, costs and provenance

`--teacher` accepts an actual training-only static checkpoint. It verifies the
same physical-source hashes, training seed split, workload coverage and exact
static-policy embedding. It rejects a validation-selected teacher; use the static
experiment's training-only `last-checkpoint.json` or the original v1 training-only
checkpoint. External teacher fit cost is recorded separately and must be included
or amortized in an end-to-end comparison. All methods can reuse that same prior.

`protocol.json` records parameter domains, source hashes, configurations, seed
roles, objectives and budgets. `checkpoint.json` records selected policies,
training incumbents, validation summaries, generation results, actual simulation
count, cache hits, simulation CPU time and wall time. Model/learner changes abort
the run. Raw measurements retain parameters, independent-check issues, physical
metrics, decision changes and rule-trigger counts. The saved factory trace's
action IDs explain why admission or machining mode changed.

The initial frozen `f452bd46...` experiment counted reason/action-label changes,
even if two labels selected identical weights. Its fulfillment, timing, cost and
physical checks are unaffected, but that counter must not be described as real
control adaptation. The current source separately records policy-weight changes
and reason-label changes; a regression test covers a late/free label transition
with identical machining/admission settings. Frozen measurements remain unchanged.

The old thirteen-parameter checkpoints are rejected by default after this source
revision. An explicit `--adapt-controller-version` evaluation option adds the old
fixed tool-distance value 4 and the old setup score (10 for nonzero family weight,
otherwise 3), preserving their policy behavior. It requires byte-identical physical
sources and records original hashes/parameters. It does not reinterpret the old
search as having optimized these additional knobs, and cannot authorize a model
change. Existing f452 experiments remain separately frozen.

The requested wall budget includes setup, paired candidate evaluation, reranking,
cache work and validation. An in-flight batch or initial fallback measurement can
overrun that deadline; actual cost is saved. Compare equal allocations and actual
costs. The implementation requests CPU only. It does not use a quantum processor,
VeloxQ or a pretrained model. A fixed QUBO selector may be passed through
`--selector`, with its additional runtime included.

## Running

```
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
python -m stage2.threshold --method cem --orders 8,12,16,24 \
  --seconds 900 --workers 32 --candidates 16 --generations 80 \
  --paired-tapes 4 --validation-every 5 --rerank-pool 8 \
  --teacher path/to/static/training-only-checkpoint.json \
  --output output/stage2-search/threshold-cem-v1

python -m stage2.threshold --method random --orders 8,12,16,24 \
  --seconds 900 --workers 32 --candidates 16 --generations 80 \
  --teacher path/to/static/training-only-checkpoint.json \
  --output output/stage2-search/threshold-random-v1

python -m stage2.threshold --checkpoint path/to/checkpoint.json \
  --evaluation-seeds 100,101,102,103 --workers 4 --save-traces \
  --output output/stage2-search/threshold-development-evaluation

python -m unittest discover -s tests/stage2 -p test_threshold.py
```

`--generations` counts total generations cycling through workloads, not that many
generations per workload. Use a fresh output directory to preserve prior logs.
The evaluation command keeps the checkpoint's complete configured workload list.
Final testing must use a separately chosen, untouched seed set instead of the
development seeds shown in the example.

Initial smoke evidence: the actual process-parallel search completed two
generations at the full minute-grid three-order load, including shared-tape
ranking, cached measurements, exact tail scoring and validation checkpoint
selection. All measured traces were physically valid. This verifies execution;
it does not establish an advantage at the harder twelve- or twenty-four-order
loads. That requires the saved matched experiments.
