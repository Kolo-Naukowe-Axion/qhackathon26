# Reachable mid-production initialization

`stage2/burnin.py` creates an initial WIP benchmark by executing a real common
policy for the first 480 minutes of the full factory. At the decision boundary,
each suffix policy inherits the resulting parts, active operations, transport,
worker appointments, tools, stock and battery. Existing commitments continue.
The module adds no new physical transition and edits none of the engine,
specification, advanced policy or independent checker.

The boundary is after tick-480 completions and revelation, before new production
or controller decisions. It must be strictly inside the horizon and aligned with
the existing controller interval. The default prefix is standard mode, WIP4,
calibration lease, priority selection, calendar filling and 10-minute early empty
AGV dispatch. New ETA and BOM options are disabled during this common prefix.

## Artifacts and verification

Every execution exports:

- A **public snapshot** with current observed orders, parts, stock, machines,
  workers, tools, admitted orders, active commitments, reserved buffers, blocked
  machine outputs, shipments, SOC and observed events. It contains neither the
  actual generation seed nor future realized events. Numerical QA debug draws
  are removed. Observed pass/fail results remain available.
- An immutable prefix record set with its canonical SHA256 digest. This includes
  operations and moves committed before the boundary even when their execution
  ends later. Events occurring at the boundary before decisions are included.
- A full execution witness and independent verification report. The full private
  witness retains the actual seed and post-run audit tape because the physical
  checker needs them. They are not passed to the suffix controller.
- A normal standalone Stage2 trace, carrying prefix/snapshot digests in its
  provenance. The ordinary factory viewer can consume its uncompressed form.

`verify(bundle)` runs the independent full-trace checker, checks that retained
prefix records remain the exact leading records of the completed execution,
rejects shortened or changed commitment histories, and independently reconstructs
active operations/moves/walks, input reservations, blocked outputs, shipments,
SOC and observed events from those records. `common_prefix(bundles)` verifies
identical prefix and public snapshot across methods on the same actual tape.
Comparisons between different tapes are not required to have identical snapshots
because past quality observations can already differ.

The detailed part/worker/tool cache snapshot is an inspection artifact rather
than a separately replay-proven checkpoint. Standalone cold restart from that
snapshot is unsupported. The witness proves reachability through actual factory
execution and verifies the retained physical trace. General policy
nonanticipativity remains unproved; paired reveal-prefix tests provide empirical
evidence. These limitations are explicit in each verification report.

Resource cache semantics are disclosed: AGV location/SOC fields describe the
committed trip endpoint, while active move records describe physical transit.
Worker hall caches describe committed walk destinations. Tool usage and machine
wear include committed active operations. Zero-power tool servicing remains an
active resource commitment even though the engine excludes it from its power
load cache.

A suffix controller receives the existing compact public observation. Static
suffix weights override the common prefix weights at the boundary; if a
controller is also supplied, those static overrides initialize the suffix and
its returned updates take precedence. No controller call occurs before the
boundary. Full-horizon objective values include the common prefix, making them
comparable across paired suffix methods. The remaining horizon is 5280 minutes
for the default 5760-minute run.

## Running it

```sh
.venv-stage2/bin/python -m stage2.burnin compare \
  --orders 8 12 24 --seeds 20 21 22 23 --workers 4 \
  --boundary 480 --horizon 5760 \
  --output output/stage2-search/burnin-v1-development

.venv-stage2/bin/python -m stage2.burnin verify \
  output/stage2-search/burnin-v1-development/n8-s20-eta-soft-join.json.gz

.venv-stage2/bin/python -m unittest discover \
  -s tests/stage2 -p test_burnin.py
```

The 19 focused tests cover actual WIP reachability, common immutable commitments,
public controller observations, static/controller switching, boundary completion
inclusion, zero-power service, source preservation, paired reveal-prefix
causality, and corruption of prefix records, reservations, blocked outputs,
shipping, future observations, private fields and full physical witnesses.

## Frozen development results

`output/stage2-search/burnin-v1-development/report.json` contains all 48 runs:
three initial order counts × four actual tapes × four suffix policies. Source
hashes before and after matched; all full physical witnesses and every paired
method prefix check passed. The batch used four local CPU processes and took
14.14 seconds wall time. No GPU or quantum device was used.

These are development seeds 20–23. Seeds 20–22 reveal two urgent orders and seed
23 reveals none, so aggregate actual demand is 38, 54 and 102 orders for initial
counts 8, 12 and 24. These demand totals are preserved in every raw row.

| Initial orders | Suffix policy | Shipped / actual demand | Fully fulfilled tapes | Total tardiness, min | Total cost |
|---:|---|---:|---:|---:|---:|
| 8 | retain standard | 38/38 | 4/4 | 9558 | 2622.05 |
| 8 | turbo | 35/38 | 3/4 | 10162 | 2684.89 |
| 8 | routing ETA | 38/38 | 4/4 | 4321 | 2596.11 |
| 8 | ETA + soft join | 38/38 | 4/4 | 3973 | 2594.80 |
| 12 | retain standard | 43/54 | 0/4 | 34323 | 3199.39 |
| 12 | turbo | 38/54 | 0/4 | 39037 | 3184.30 |
| 12 | routing ETA | 42/54 | 0/4 | 32633 | 3044.97 |
| 12 | ETA + soft join | 43/54 | 0/4 | 30459 | 3038.91 |
| 24 | retain standard | 46/102 | 0/4 | 141328 | 2897.48 |
| 24 | turbo | 46/102 | 0/4 | 139293 | 2991.18 |
| 24 | routing ETA | 47/102 | 0/4 | 135573 | 3186.43 |
| 24 | ETA + soft join | 48/102 | 0/4 | 135909 | 3183.67 |

The routing policies enable free-buffer filtering and the finish-time estimate.
Soft join uses accepted-peer weight 4, peer-progress weight 0. Other prefix policy
settings persist. All methods see exactly the same actual state within each
paired tape. Counts above include unfinished production in the horizon objective
rather than discarding difficult orders. Valid partial traces at 12/24 orders
are explicitly distinguished from complete fulfilled solutions.

At tick 480 every case retains four or five active operations; cases retain zero
to two active AGV moves. The deterministic showcase
`showcase-public-snapshot.json` is the first development tape (8 initial orders,
seed 20), with 5 processing and 19 waiting parts at the boundary. The corresponding
`showcase-trace.json` uses ETA+soft join and is a normal full checked viewer trace.
It is a visualization example, not independent evaluation evidence.

The n8 soft-join candidate preserves full fulfillment on all four development
tapes while reducing total tardiness from 9558 to 3973 minutes. The n24 candidate
improves shipments from 46 to 48 across 102 orders but remains incomplete. These
results motivate a frozen held-out comparison; they establish neither universal
policy superiority nor the full factory optimum. The 24-order global gap remains
unknown.

Frozen burn-in source SHA256:
`a7e082ae5fcd91fca2062dca795de3323dc39f8021f4d56636d83d0e6d232b0f`.
The report directory contains source snapshots and exact hashes for all physical
and algorithm files. Earlier development directories are retained as historical
iterations; the `burnin-v1-development` report is the frozen result above.
