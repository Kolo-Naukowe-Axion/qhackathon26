# Stage 2 research implementation

**Direction update:** catering is the active direction to try. Its
[foundation/method work allocation](../docs/CATERING_METHOD_WORKSPLIT.md) and
[solver contract](../docs/CATERING_SOLVER_CONTRACT.md) are written; the catering
foundation is not yet implemented. This directory and the results below describe
the verified factory fallback. They are not catering results.

**Current technical status — 17 October 2026:** all 14 agreed non-VeloxQ core
requirements passed. Start with [current status](../docs/STAGE2_STATUS.md),
[manufacturing study](../docs/STAGE2_MANUFACTURING_STUDY.md) and
[whole-recipe quantum bridge](../docs/STAGE2_RECIPE_BRIDGE.md). The main studio
shows the 32-operation recovery case, representation frontier, 18–36 logical-qubit
QAOA bridge, feature accounting and synthetic economics. Scaling reaches 128
operations with explicit reference limits. No quantum advantage is established.

```sh
.venv-stage2/bin/python -m stage2.entry_demo --port 4192
```

Open [the production studio](http://127.0.0.1:4192/manufacturing/#merit).
Fresh execution is local simulation; the static build displays retained results.
The [smaller residual-cell study](../docs/STAGE2_ENTRY.md) remains at `/entry/`.
Actual VeloxQ service/credit use, final synchronized video, human rehearsal and
public release/submission remain separate open duties.

For the original model, read
[the current complete explanation](../docs/STAGE2_CURRENT_EXPLAINED.md) first,
or open the local [Start here guide](http://127.0.0.1:4187/stage2/start.html).
They distinguish the full physical factory below from the later, separately
simplified planning cells, and identify which results are classical or quantum.
The earlier explanation-only pause was superseded by the user's entry-refinement request.

The executable factory is `spec.py` + `engine.py`. The original Stage1 entry,
instances, validator and selected artifacts remain separate. The full Stage2
profile uses one-minute time steps and a 96-hour horizon by default. All measured
solvers below preserve the physical specification; their routing, admission and
candidate restrictions are explicit algorithm choices.

Start with [measured capability and limits](../docs/STAGE2_RESULTS.md), then the
[judge-facing explanation and formal requirement matrix](../docs/STAGE2_JUDGES_EXPLANATION.md).
The current final-evaluation status and all incomplete/submission limitations are
explicit there; a replay or a valid partial execution is not a completed order set.
For why a constant macro setting still produces dynamic scheduling, see
[the control layers and proof meanings](../docs/STAGE2_CONTROL_LAYERS.md).

## Factory

Each pump needs one matched housing, rotor and flange, followed by assembly and
final inspection. The 15 machines occupy two halls. Four battery-powered AGVs
carry individual parts or portable tools across a graph with exclusive lanes,
including a single shared bridge. Machine outputs block until pickup; finite
destination input space is reserved before a trip begins.

Ten individually tracked workers have qualifications, daily shifts, breaks and
walking time. Family changes require qualified setup attendance. Turning,
milling, washing and heat treatment need short tending; welding, inspection and
assembly require full attendance. Heat batches share a family and have bounded
capacity. Tool location, remaining life and service are physical resources;
machine wear and maintenance are separate.

The grid, deterministic solar, lossy stationary battery, time-varying prices and
carbon intensity interact with machine loads and AGV charging. Manufacturing
modes affect duration, electricity, wear and inspection risk. Inspection reveals
keyed quality outcomes; repair, replacement and final scrap are bounded. Three
uncertainty stages reveal a possible mill outage, supply/grid stress, and urgent
orders. A paid calibration-tool rental has lead time and a hard investment
budget. Future outcomes are excluded from controller observations.

Quality execution uses the immutable key `quality:{unit_id}:{attempt}`. The older
descriptive `quality.paired_key` metadata also lists `operation_id`; that field
does not select the executed random stream. The identity audit reports this
legacy metadata discrepancy and checks actual canonical births, bounded
replacements and unit/attempt draws. Frozen numerical instances remain byte
preserved; renaming a part cannot legitimately obtain a new quality draw.

Emergency procurement, physical machine leasing, interruption/resumption,
overtime and hard operating-cost/carbon caps are not implemented. Stock is finite
and usually nonbinding in measured 8/12/24-order examples; it certifiably binds
in a32-order quality/material witness described below. Some legal actions,
such as careful welding/assembly, are outside the baseline dispatch macro. These
limits are part of the model/solver scope, not hidden features.

## Solvers and evidence

| Module | Role |
|---|---|
| `identity_audit.py` | Supplemental canonical births, replacements and hidden-draw identity checks against a fresh instance |
| `selector_reward.py`, `completion_policy.py`, `maintenance_guard.py` | Explicit reward, pump-completion and causal maintenance-availability controls; original defaults retained |
| `quantum_scaling.py` | Separate capped24-total-bit CPU statevector experiment on saved pools; no full-factory23-bit execution or quantum advantage |
| `check.py` | Independent physical replay; validity, fulfillment and terminal requirements are separate |
| `advanced.py` | Worker calendar gaps, optional route estimates and AGV prepositioning |
| `specialist.py`, `tooling.py` | Scarce-worker protection and portable-tool homes; both can regress |
| `admission.py`, `kitting.py`, `kit_recovery.py` | Persistent admission, whole-kit space heuristics and bounded physical component repacking |
| `qubo.py`, `dispatch.py`, `quantum.py` | Exact local action-selection QUBO; classical controls and actual QAOA simulation with at most 5 total bits; oversize fallback labeled |
| `sequential.py`, `threshold.py`, `mpc.py` | Learned macro policies, interpretable thresholds and independently sampled scenario lookahead |
| `recovery_routing.py`, `recovery_mpc.py`, `adaptive_recovery.py` | Explicit strong-backend routing, independently sampled lookahead and bounded PPO/CEM with an exact static fallback |
| `reference.py`, `reference_multi.py` | Exact/ bounded deterministic fixtures with matched physical comparators; no flagship optimum claim |
| `energy.py` | Causal battery policies and an exact clairvoyant fixed-load battery reference |
| `burnin.py` | Reachable initial WIP through a real common prefix and retained reachability witness |
| `rank_probe.py`, `rank_three.py` | Separate structural reduction of the official 3×3 B example; all five deadline-8 schedules preserved in three semantic bits |
| `final_eval.py`, `statistics.py`, `freeze.py` | Immutable selected-policy evaluation, stratified paired statistics and source snapshots |
| `compare_evaluations.py` | Strict paired evidence across source groups with identical physical instances/verifiers |
| `quality_material_bound.py` | Offline necessary-quality/material lower bounds, matched to full checked primary-optimal witnesses |

The full factory is not encoded losslessly into five qubits. Classical code
maintains the physical state, makes high-level choices and builds restricted
local candidate sets. The QUBO is exact within that set, with all slack counted;
the full-policy global tardiness/cost gap remains unknown. The separate three-bit
B result is instance/deadline specific and includes charged classical structural
preprocessing. Neither result establishes quantum speedup.

Eight TRAIN32-order/240-hour witnesses attain the global minimum number of
unfulfilled orders on their fixed tapes: seven complete everything, while one
necessarily lacks a housing blank after unavoidable original-component scrap.
This certifies the primary objective only. Extra calendar time, selected training
tapes and the unknown deadline-debt/cost gap remain explicit in
`docs/STAGE2_QUALITY_MATERIAL_BOUND.md`.

## Reproduce a checked baseline

From the repository root, using the isolated experiment environment:

```sh
.venv-stage2/bin/python -m stage2.run --orders 12 --seed 0 --wip 8 --lease \
  --output output/stage2-baseline-example
.venv-stage2/bin/python -m unittest discover -s tests/stage2
```

The baseline example is a reproducibility command, not the selected strongest
policy. Its trace embeds all numerical tables and the independent checker result.
Stage2 viewer assets live only under `presentation/stage2/`.

## Research records and frozen tests

`docs/STAGE2_EXPERIMENT_LOG.md` records actual measured results, costs, failures
and changing hypotheses. `output/stage2-search/compute-ledger.json` records
bounded allocations. Immutable sources, raw per-run measurements, checked traces
and selection provenance remain under `output/stage2-search/`.

TRAIN tapes 0–31 and validation 100–115 may guide algorithms. Ordinary tests 1000–1031
were inspected during development and must not substitute for the untouched
final protocol. The reserved final 256 tapes begin at 10000 and are stratified over
the eight declared disruption leaves. Final evaluation requires a frozen concrete
selection and explicit execution; actors remain nested within environment tapes.
No ODRA/VPN or VeloxQ work is part of the current compute authorization.

## Minimal dependencies

The physical engine, independent checker, priority scheduler and exact small-pool
selector require only Python's standard library. Saved learned-policy inference
and the separate larger statevector simulator additionally use
`pip install -r stage2/requirements-inference.txt`. Optional exact CP references
use `stage2/requirements-reference.txt`. A full research fit additionally needs
Torch; the Axion records retain the actual CPU Torch2.14.1+cpu runtime.
No Torch or GPU is needed to replay a selected NumPy policy.

The subsequent [local QAOA training study](../docs/STAGE2_QAOA_LOCAL_TRAINING.md)
adds reversible adjoint gradients, multistart depth search and CVaR tail lifting
for the existing whole-recipe assignment circuit. Fitting uses the optional
`stage2/requirements-qaoa-fit.txt` environment; it runs entirely on this Mac.
Its retained trials and independent circuit/transfer checks are separate from
the original bridge evidence and do not establish quantum advantage.

A package version or source hash records the measured environment; it does not
normalize timings across machines. The isolated Stage2 files are separate from
the Stage1 solver requirements.
