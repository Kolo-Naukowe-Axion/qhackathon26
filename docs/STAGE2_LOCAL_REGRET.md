# Offline continuation audit of local QUBO decisions

`stage2/local_regret.py` measures whether a locally exact linear-reward choice
also gives the best eventual factory result among the feasible choices at that
one boundary. This is an offline audit using realized future outcomes. Its
continuation oracle is not a deployable causal policy, an unrestricted scheduling
optimizer, or a claim of quantum advantage.

## Fixed experiment

The backend is the unchanged hard-home ToolingFactory, without whole-kit
reservations or QA-worker protection. Numerical instances use the full5760-minute
model, initial loads8/12 and TRAIN seeds0/1/2. Concrete static routing weights come
from the training-only measured prior, with worker calendars on and prepositioning
off. The baseline uses the exact local selector at every dispatch boundary.
The prior's source hashes and training costs remain in the protocol; every run
uses one newly frozen complete source version.

From each baseline, the audit takes the first two chronological dispatches with
at least one encoded coupling,2–4 core candidates, and no more than five total
variables including slack. There are at most12 selected boundaries. One-bit
uncoupled calls cannot enter this audit. The exact local action can still have
multiple tied optima; ties and alternative actions are retained.

Every feasible core subset is enumerated directly from the original candidate
resource demands, capacities and pairwise conflicts. This includes the empty
subset. The enumeration does not infer feasibility from QUBO energy or rely on
the solver's chosen action. With at most four candidates it requires no more
than16 subsets per boundary, hence no more than192 complete counterfactual runs,
plus six baselines.

## Same-model forced continuations

Each alternative restarts the identical factory from the beginning on the same
environment tape. Exact causal dispatch runs normally before and after the one
forced boundary. A process-local, same-thread wrapper calls the original
`dispatch.choose` first, reconstructing all candidates, conflicts, capacities
and concrete offered operations. Their SHA must match the frozen baseline pool.
The forced subset is independently checked again and checked against the
compiled QUBO. Only the returned candidate indices change; actual starts still
use the original physical process method.

The wrapper is restored in `finally`, including on invalid forces, pool mismatch
or an exception. Nested/concurrent wrappers and use from another thread are
rejected. The runner is sequential; it never patches another process or edits a
physical source file. This facility is an offline experimental override, not an
engine feature or an online planner.

Physical commitments and observations strictly before the target tick are hashed
and must match the baseline. Full records of intervals committed earlier remain
included even if they extend beyond the boundary. Timestamps, solver timers and
future outcomes are excluded. The full target pool is hashed independently.
Forcing the original exact action is tested to reproduce the entire baseline's
physical trace, not merely its prefix.

Every completed counterfactual receives the full independent physical and
immutable-tape checker. Selected candidate IDs must exactly equal committed IDs
at every dispatch. Failures and partial executions remain explicit records;
partial executions also receive a checker attempt. No failed alternative is
silently dropped. An incomplete/invalid audit is flagged rather than presented
as an exhaustive valid oracle.

## Oracle and controls

True continuation outcomes are ranked lexicographically by unfulfilled order
count, total tardiness and energy-plus-rental cost. Total tardiness uses the same
engine metric, including horizon-based lateness of unfulfilled orders. The best
observed valid continuation is a conditional oracle among these one-tick subsets
under the fixed future exact policy. Later dispatch decisions are not optimized
by the oracle.

Controls include the original exact linear-reward action, an actual bounded
statevector QAOA sample, an equal-shot uniform baseline, and an exact local
random-tie choice. They use the same frozen pool. Each control's selected subset
is looked up in the complete continuation table, so its future outcome is
measured without redundant reruns. QAOA angle training, sampling and all QUBO
preprocessing are timed in the control-generation wall/CPU cost. No QPU is used.
All circuit/sampling metadata remain available.

Per-control outcome differences are vectors. A positive unfulfilled difference
is worse even if its tardiness/cost differences are negative. Tardiness should be
called regret only when the primary unfulfilled count ties; otherwise report the
complete vector. QAOA beating a linear-reward decision in eventual factory
outcome would show surrogate misalignment or exploration, not quantum advantage.
The offline oracle uses future outcomes unavailable to the deployed selector.

## Reproduction and evidence

```sh
python -m stage2.local_regret \
  --teacher output/stage2-search/routing-coefficients-training/training-teacher.json \
  --output output/stage2-search/local-continuation-regret --max-boundaries 12
```

Existing output is refused. The protocol, all frozen source files, complete
baseline/counterfactual traces, every alternative row, full pool/prefix digests,
control metadata, per-boundary outcomes and total costs are retained. Source
changes abort the audit. No validation or reserved final tape is used.

Tests cover independent original constraints, empty subsets, whole-trace exact
reproduction, complete feasible-set forcing, physical prefix preservation,
changed-pool and invalid-force rejection, and exception-safe wrapper restoration.
This small selected-boundary audit cannot estimate regret across all factory
states or certify a full factory optimum.

## Completed bounded audit

The frozen module SHA256 is
`f2e4c3284718c7e4976b56e6bdc33f26b5e0d81e3b760af8ad923a2637d9253f`.
Five tests passed. The prescribed six baseline context/tapes produced12 eligible
boundaries and39 feasible-core continuations. Every continuation was valid, all
pool/prefix/commit checks passed, and the exact-action forced continuations
reproduced baseline metrics. Wall time was44.26seconds, process CPU43.57seconds;
future evaluations consumed38.17seconds and control generation0.0132seconds.

The exact linear-reward action was lexicographically worse than the realized
continuation oracle at8/12 selected boundaries. At two boundaries of the same
load12/seed0 factory it left one additional order unfulfilled. These are two
separate one-tick deviations in one environment, not two independent factory
failures, and their gains must not be added.

At minute121 in that factory, the conflicting offers were P01's flange on S1
(linear reward298.36) and P09's flange on S2 (reward200), both requiring W02.
Taking the lower-reward offer ultimately fulfilled the extra order under the
otherwise unchanged future exact policy. The coupled local model was solved
correctly; its objective did not encode the full downstream consequence.

QAOA, equal-shot uniform and exact-random-tie controls chose the same action as
the exact linear selector at all12 boundaries. All12 QAOA executions were actual
coupled2–3bit classical circuit simulations, with no one-bit calls or fallback.
They therefore inherited precisely the same continuation regret. The audit
shows no quantum improvement; solving an inadequate surrogate more accurately
cannot supply the missing long-term objective.

This realized-future audit does not prove that a causal predictor could identify
the oracle choice before uncertainty is revealed. It is a selected early-boundary
mechanism study on TRAIN tapes, not an estimate over all states or independent
test performance. Full evidence and a concise summary are retained in
`output/stage2-search/local-continuation-regret/` and `mechanism-summary.json`.
