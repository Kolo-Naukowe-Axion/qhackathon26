# Causal scenario rollout controller

`stage2/mpc.py` evaluates complete simulated continuations from the current
factory state. This is classical model predictive control over a finite bank of
dispatch policies, rather than an optimal solution of the complete factory.
The physical engine is unchanged. Every actual output trace receives the full
independent checker, including its immutable random-tape audit.

## Decisions and policy memory

At each planning boundary, candidates include the incumbent, verified external
policies, and optionally 32 static policies (WIP 3/4/6/8, eco/standard,
family preference 0/24, rental off/on). The incumbent is always eligible and wins
an exact tie. Strong routing coefficients can be imported from a training-only
static artifact. Its off/on rental variants permit investment to be declined.
After a rental has been irreversibly requested, otherwise identical static
off/on variants have the same physical future and are deduplicated.

A threshold policy is an actual closed-loop continuation: its queue thresholds,
mode decisions and hysteresis run at every engine controller callback, in both
the scenario and the actual factory. Between planning boundaries the selected
policy keeps running. An incumbent threshold controller retains its congestion
memory; each candidate future receives a separate copy of that memory. Switching
to a different policy explicitly starts that policy with fresh memory. Simulated
callbacks cannot mutate actual policy memory. The actual selected first decision
is checked against the corresponding simulated first decision.

## Causality and resumed simulations

The resumed loop is mechanically derived from `Factory.run` using a guarded AST
transformation. Only the starting tick and the handling of an already-processed
initial boundary change. A changed loop shape fails closed pending another audit.
Regression tests compare resumed physical traces with uninterrupted execution.

The real controller sees the public observation. A forecast copies the current
physical simulator state, including work already in progress. Before any future
decision executes, its instance seed is replaced by an independent planning
seed. Planning seeds depend only on the separate planning seed, tick and scenario
index; the actual environment seed does not enter this computation. All candidate
policies share the same sampled futures at a planning boundary.

The copied historical prefix was generated under the actual tape, while future
events use a newly sampled tape. These are **conditional counterfactuals**, not
measured single-seed runs. They are labeled accordingly and are not exported as
independently measured factory executions. `--check-futures` optionally runs the
independent physical checker while omitting the single-seed quality/exogenous
tape audit; the scope is recorded explicitly. The actual final execution always
receives the complete checker. Explicit physical infeasibility, a failed optional
physical check, or an unmet terminal battery constraint penalizes a candidate.

This remains a simulator-based conditional forecast, not a learned calibrated
posterior of unknown failures. Forecast count and planning seed sensitivity must
be measured; one sampled future can produce poor decisions.

## Objective and cost accounting

Candidate ranks are lexicographic:

1. Number of physically invalid sampled futures.
2. Mean unfulfilled order count.
3. Mean tardiness plus 0.25 times the empirical upper-tail CVaR90 of tardiness.
4. Mean energy-plus-rental cost.

Fractional tail mass is handled exactly for finite scenario counts. A reduction
in mean unfulfilled count cannot be traded against tardiness by a scalar weight.
Legacy scalar losses remain in logs for compatibility and are labeled display
only. A candidate cap truncates the bank deterministically after retaining the
incumbent; results are conditional on that declared finite candidate domain.

Logs retain all candidate policy parameters and provenance, scenario seeds,
metrics, check scope, first-boundary weights, policy memory, selected policy,
scenario timings and planning timings. Source files and the generated continuation
are hashed. Imported artifacts retain their external training/simulation costs;
these must be included or explicitly amortized in comparisons. Counterfactual
rollouts count as planning compute, never as extra measured evaluation tapes.

## Artifacts and versions

Static teachers require a training-only selection role, training seeds within
0–31, and matching order count, horizon, profile and physical source hashes.
Threshold banks require matching physical sources and the exact threshold
controller version. An older supported threshold schema can be loaded only with
`--adapt-threshold`; the original digest and explicit adapter are retained. This
adapter does not permit a different physical engine. Validation-selected threshold
policies can be used as frozen candidates, with that selection role disclosed;
they are not relabeled training-only teachers.

Training uses seeds 0–31. Validation 100–115 may select a frozen controller or
planning configuration. The reserved final protocol at seeds 10000+ is not used
by training, candidate construction, the examples, or these tests.

## Example

Run from a snapshot with the same physical hashes as both artifacts:

```sh
python -m stage2.mpc --orders 12 --seed 0 --scenarios 4 --interval 720 \
  --planning-seed 27491 --static-teacher training-teacher.json \
  --threshold-bank checkpoint.json --adapt-threshold \
  --no-default-actions --candidate-limit 4 --check-futures \
  --output output/mpc-training-smoke
```

The old positional Python `run` and `RolloutController` APIs remain supported.
Use `initial_policy` or `--start-with-bank` to choose the initial incumbent.
Otherwise the supplied initial weights remain the incumbent. No quantum hardware
or quantum advantage claim is involved in this controller.
