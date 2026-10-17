# Portable evidence: start here

This page is copied to `audit-supplements/portable-overview/` in the compact
package. Its relative links below target that package layout. Other copied
project documents preserve their original repository links and may require the
full checkout to follow them.

The selected factory includes 15 machines, two halls, four AGVs, ten workers,
matched component BOMs, physical transport and charging, finite buffers, tool
service and leasing, shifts, maintenance, process modes, quality and bounded
recovery, stock deliveries, urgent demand and revealed disruptions. It is a
synthetic scheduling environment, not an industrially calibrated plant.

The headline selected controllers are classical. On the fixed final protocol,
the 12-initial-order, 96-hour context ships every realized order with weighted
probability 94.984375%; the 32-initial-order, **240-hour** context reaches
91.015625%, with substantial lateness. Each context may receive two urgent
orders. The 16/24-order, 96-hour cases remain unreliable. These are empirical
controller results, not physical infeasibility thresholds or whole-factory
optimality proofs.

## Verification and navigation

From the package root, using Python 3.12+:

```sh
python verify_package.py . --output verification.json
```

This hashes every indexed package file and freshly checks the physical instance,
identity, terminal conditions and metrics of exactly 24 predeclared retained
replays. It runs no controller and adds no performance samples. Install the
declared NumPy dependency only when executing the saved learned policy.

- [Complete measured report](../../measured-results/report.json): all 74 groups,
  23,552 original checked executions and 41 declared paired contrasts.
- [Original policy/source freeze](../../policies/global-freeze-index.json): fixed
  before final outcomes. The current source snapshot and legacy comparison
  source are distinct.
- [Predeclared replay index](../../retained-replay-index.json): first tape in each
  of eight uncertainty leaves, first actor, for each of three named methods.
- [Separate audit and analysis index](../../audit-supplement-index.json): exact
  package paths, hashes, origin paths and interpretation scopes for every
  supplement, including later reference work and immutable accounting.
- [Package manifest](../../package-manifest.json): file integrity relative to
  this local export, not an external signature.

The full raw archive is a separate export; this compact bundle does not claim
to reproduce all 23,552 trajectories. Its independent audits rebuild all row
anchors and freshly replay 592 original retained traces. Posthoc explanatory
witnesses and TRAIN-only neighborhood/oracle runs are separately labelled and
excluded from the frozen final population estimates.

## Quantum and resource scope

Actual QAOA simulation drives restricted local decisions, with at most five
total bits including slack and explicit classical fallback for larger offers.
The two predeclared primary QAOA comparisons establish no advantage; their
intervals do not prove equivalence. Classical state construction, angle search,
feasibility filtering and postselection retain their costs. No physical QPU,
VeloxQ or GPU training result is claimed.

On the measured Axion CPUs, the selected 12/16/24 controllers average about
3.33/3.41/3.77 process CPU seconds per checked episode; declared MPC comparisons
take 156.19/113.18/255.35 seconds. These include simulation/checking and have
different algorithmic budgets. Shared fitting and prior search are additional
development costs, not free pretraining. The immutable accounting supplement
states its own timestamp and separates allocation, worker CPU and local-meter
coverage.

No commit, push, publication, deployment, video recording or submission is
performed by creating this evidence export.
