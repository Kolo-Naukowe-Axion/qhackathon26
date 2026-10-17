# Task-specific learned dispatch experiment

Historical prototype note: this document describes the initial one-step bandit
and its16-action domain. Current sequential PPO, static search, warm starts and
48-action comparisons are documented in `STAGE2_SEQUENTIAL.md` and the measured
`STAGE2_EXPERIMENT_LOG.md`. The old coarse15-minute factory is archived and must
not be used as the current full-profile feasibility evidence.

Implemented 2026-10-16 in `stage2/learning.py`. This is a small, trained-from-scratch
**one-step contextual bandit** using PyTorch REINFORCE. It chooses an interpretable
dispatch configuration for one complete causal factory simulation. It is not a
pretrained foundation optimizer, not a sequential controller, and not a quantum
algorithm. Its role is to test whether learning where to place scheduling effort
improves results within the available time, rather than assuming that it will.

## Decisions and observable context

Sixteen actions combine eight priority/setup parameter rules with standard or
turbo machining. Rules range from due-date priority to long remaining route,
short remaining route, family grouping and seeded diversified priorities. All
weights are saved in the artifact. The learned policy therefore selects real
engine behavior, rather than a label around an unchanged heuristic.

Eight numerical features describe initial observable workload: order count,
horizon, nominal operation density, machine count, mean due date relative to the
horizon, precision-order fraction, grid capacity, and a constant feature. Future
shocks, the random seed, hidden quality values and later observations are excluded.
With only one fixed factory context, this honestly reduces to learning a global
choice among sixteen policies. A configurable context grid permits testing
generalization across loads and planning horizons.

The network has two 64-unit tanh hidden layers, a categorical actor and scalar
baseline. Training uses REINFORCE with a detached learned baseline, batch-centered
and scaled advantages, entropy regularization, a value loss and gradient clipping.
It starts from random weights. Training does not reuse weights from another
factory or claim that large pretrained scheduling models support this state.

## Physical validity and reward

Every episode calls the actual `stage2.engine.run` and independent
`stage2.check.check_trace`. Invalid episodes receive a penalty and remain in the
results; they are never silently discarded. Check codes and counts are retained.
The scalar reward prioritizes missing orders, then bounded normalized tardiness,
then a small bounded energy-cost term; terminal battery failure is heavily
penalized. At a fixed context one additional completed order dominates all
tardiness/energy differences. This is a training surrogate; the report also
retains fulfillment, tardiness, energy, carbon and an empirical worst-decile
tardiness mean. It does not claim to solve the full CVaR objective globally.

An episode may be physically valid while incomplete. Those are different claims.
All-fulfilled rates require both a valid trace and every realized order shipped.
The instance can reveal urgent arrivals, so reported realized order count can
exceed the configured initial order count.

## Comparators and evaluation

The same action set, simulator, checker and training seeds are available to:

- REINFORCE contextual policy learning.
- Random search, which selects its measured best incumbent separately for each
  training context at evaluation time. It does not take random evaluation actions.
- Context-specific categorical cross-entropy search with elite updates and an
  exploration floor; its evaluation action is also the best measured incumbent.
- A finite-grid baseline that covers all sixteen actions on each training tape
  without duplicate episodes. It stops when the grid is exhausted or its wall
  budget expires. This is particularly important because exhaustive empirical
  policy selection may be cheaper and stronger than learning for this action set.

Each method receives an equal requested wall-time fit budget, which includes
its initialization and simulation/checking time. The final batch can overrun;
actual wall time, episode count, batch size and worker count are reported. A
`--max-episodes` cap is available for smoke checks, but an episode-capped smoke
test must not be described as an equal-wall-time result. Training and inference
costs are separate. Validation/test measurement time is not hidden inside fit time.
Different runtime libraries can have different import overhead; this is counted.

Fixed disjoint seed sets are training 0–31, validation 100–115, and test 1000–1031.
All methods are evaluated on the same held-out seeds and contexts. Validation is
reported separately; the current implementation does not tune hyperparameters
or choose a favorable test seed from it. The default command evaluates test once
per fit; repeated human iteration on those results would turn that test into
development data and require a fresh final test set.

Source SHA-256 values for the engine, instance builder, checker, learner and
blueprint are captured before fit and checked every batch and before/after
evaluation. An engine edit aborts the experiment instead of silently combining
multiple models. JSON artifacts save all per-episode measurements and parameters;
PyTorch checkpoints also save weights. Load locally generated checkpoints with
`torch.load(..., weights_only=True)` when inspecting or resuming them.

Unseen-context REINFORCE evaluation feeds the new observable context into the
network. The random/CEM/grid comparators use their nearest training context in the
same normalized feature space. Neither method receives future scenario data.
No global optimum or global optimality gap is inferred from these comparisons.

## Compute and execution

The simulator is Python/CPU-bound and the policy has only a few thousand
parameters. The initial implementation deliberately requests no GPUs. PyTorch
uses one CPU thread; independent simulator episodes can use `--workers` processes.
Profile throughput before increasing resources. GPU allocation solely to run
this small network would provide no established benefit.

```
.venv-stage2/bin/python -m stage2.learning --profile-only --orders 24 --horizon 384
.venv-stage2/bin/python -m stage2.learning --method all --orders 24 --horizon 384 \
    --seconds 120 --batch-size 16 --workers 4 --seed 2026 \
    --output output/stage2-search/learning-pilot
python3 -m unittest discover -s tests/stage2 -p test_learning.py
```

Use `--configs path.json` to supply an array such as
`[{"orders":12,"horizon":384,"profile":"full"},{"orders":24,"horizon":768,"profile":"full"}]`.
Treat a different horizon as a different instance configuration and compare all
methods on exactly the same configurations. Extending the horizon does not
remove mechanisms, but can change which time-dependent disruptions or shifts
occur. The artifact keeps that choice explicit.

## Initial smoke check and discovered failure

A 32-training-episode smoke check ran all three methods on the small
`orders=1,horizon=192` configuration. It verified that gradient updates, simulator
calls, independent checks, checkpoint writing and held-out evaluation execute.
It is not evidence that learning improves the factory. This tiny context offered
little policy separation and the three methods produced effectively equal
fulfillment/tardiness outcomes.

Importantly, one held-out episode (`seed=1011`, action `short-tail-turbo`) exposed
the checker's `part_drop_location` issue at tick 95, move M24. The root engineering
task was notified; this needs resolution before meaningful training claims.
Initial outputs are kept under `/tmp/stage2-learning-smoke` rather than promoted
as validated research artifacts. After fixes, rerun from a fixed source snapshot
and evaluate on a fresh final holdout if the current test seeds informed repairs.
