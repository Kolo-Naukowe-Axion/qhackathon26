# Frozen selected-policy evaluation

`stage2/final_eval.py` prepares and evaluates an immutable selection. It does not
choose policies, retrain checkpoints, rank candidates on final outcomes, or supply
a default final protocol. Preparation alone never executes a factory simulation.
The reserved 256-tape evaluation was globally frozen and started at00:32UTC on
17October2026. `output/stage2-search/final-frozen-bundle-v20p2/` binds all policies,
checkpoints, sources and protocol before outcomes. Jobs6117508–6117517 are
recorded in `final-v20p2-submission.json`; policies are closed to further tuning.

## Selection specification

Create a JSON file with this shape. Paths are relative to this specification;
freeze resolves them to absolute immutable artifact references.

```json
{
  "schema": "stage2-selected-policy-spec.v1",
  "configs": [{"orders": 12, "horizon": 5760, "profile": "full"}],
  "actor_seeds": [900000, 900001, 900002],
  "trace_policy": "first_per_leaf",
  "selection_provenance": {
    "data": "TRAIN 0–31; development validation 100–115",
    "criterion": "Declare the exact selection rule here",
    "training_cost": "Record all shared and method-specific CPU/GPU costs"
  },
  "methods": [{
    "id": "selected-static",
    "kind": "context_static",
    "checkpoint": "selected-training-teacher.json",
    "selection_provenance": {"selection_data": "TRAIN", "training_wall_seconds": 0}
  }]
}
```

Every method requires selection/cost provenance. The runner preserves all other
method fields, checkpoint metadata and checkpoint digests; no precomputation is
silently free. Artifact metadata retains selection roles, original source
digests, teacher costs and adaptation disclosures. Shared costs should be charged
once or explicitly amortized when comparing methods, never multiplied blindly
by evaluation tapes. Wall times from different hardware are not interchangeable.

Supported methods:

| `kind` | Policy fields |
| --- | --- |
| `static` | Explicit `weights`; optional `weights_by_config` entries containing `config` and `weights` |
| `context_static` | `checkpoint` with measured context/action selections; extracts the artifact's concrete weights |
| `threshold` | `checkpoint`; `adapt_threshold: true` explicitly permits the supported historical controller adapter |
| `sequential` | `checkpoint`; `adapt_learner: true` explicitly permits policy-only learner-version adaptation; `deterministic` defaults true |
| `advanced`, `specialist` | Static weights with that causal dispatch backend; normalized to `kind: static` plus explicit `backend` |
| `tooling` | Static weights with the advanced portable-tool-home decoder; explicit `tool_policy`, optional `specialist: true` for the QA guard |
| `kitting` | Explicit whole-kit reservation decoder; optional tool homes, QA guard and admission. Seals `kit_reservation: true` for this backend, or explicit false for its ablation |
| `recovery`, `recovery_routing` | Audited tool-home/specialist/kit composition with explicit `recovery_policy.enabled`; optional process-scoped `routing_policy` |
| `recovery_mpc` | The same recovery/routing physical decoder, with an inline independent-future action bank in `mpc`; checkpoint banks are rejected |
| `mpc` | `weights`, optional `static_teacher`, `threshold_bank` list and `adapt_threshold`; `mpc` dictionary supplies `scenarios`, `interval`, `actions`, `candidate_limit`, `risk_weight`, `physical_check_futures`, etc. |

For threshold/sequential/context-static policies, `backend` can select baseline,
advanced or specialist dispatch explicitly. A method may restrict `configs` to a
subset of the manifest contexts. All artifacts must support the requested
contexts. The runner never substitutes a policy trained on a different horizon
or order count.

The strongest combined tool/worker/admission candidate can be represented
without changing any physical definitions:

```json
{
  "id": "hard-home-qa-campaign",
  "kind": "tooling",
  "specialist": true,
  "admission": true,
  "tool_policy": {"mode": "hard"},
  "weights_by_config": [{
    "config": {"orders": 12, "horizon": 5760, "profile": "full"},
    "weights": {
      "wip_limit": 4, "mode": "standard", "lease_calibration": true,
      "qa_guard_threshold": 4, "admission_rule": "campaign"
    }
  }],
  "selection_provenance": {"data": "Declare actual training/validation selection", "training_wall_seconds": 0}
}
```

This is a schema example, not a selected final policy or performance claim.
`tool_policy_by_config` can instead provide one `config`/`tool_policy` entry per
requested context. The same per-context option exists for `energy_policy`.
The portable resources remain physically movable; hard homes and the QA worker
guard are disclosed algorithm restrictions. Hard homes may leave an otherwise
eligible machine unused. Soft homes are a distinct candidate and must not be
substituted for a selected hard-home policy.

`admission` defaults false and accepts an explicit boolean. When true, the
AdmissionMixin changes only persistent WIP order ranking; controls remain in
weights (`admission_rule`, `admission_due`, `admission_family`,
`admission_urgent`). Rules are `due`, `family`, `priority`, and `campaign`.
Already admitted orders retain their slots through completion. The due rule
matches existing admission behavior exactly. Admission can compose with baseline,
advanced, specialist, tooling, or energy factories. MPC and the common burn-in
hook currently refuse admission composition rather than ignoring the option.
Both admission and tooling source digests enter every frozen manifest.

For whole-kit assembly admission use `kind: kitting` (or explicitly select
`backend: kitting` for a checkpoint controller). The existing tool, worker-guard,
admission and per-context options retain their meanings. Only this backend
defaults kit reservation on; all older backends remain unchanged. The manifest
stores the resolved boolean. `kit_reservation: false` provides its matched
disabled ablation. Kitting retains the baseline battery and rejects an energy
policy combination; MPC and common-burn-in combinations are not supported.
See [the kitting protocol](STAGE2_KITTING.md) for the single-tape rescue and
remaining deadlock/starvation limitations.

Physical recovery is an explicit backend requiring `specialist: true`, a concrete
`tool_policy`, and a `recovery_policy` containing a boolean `enabled`. It can
retain admission and optional `routing_policy` (or per-context variants). It
executes real AGV transfers and locks assembly traffic; it adds no storage.
`recovery_mpc` preserves this runtime class, reservations, accepted components,
admission backlinks and recovery locks in each independently seeded continuation.
Its futures are conditional planning work; only the actual run is a measured
immutable-tape factory. Unsupported energy/checkpoint-bank compositions fail
instead of being silently ignored.

Optional separate ablations use `backend: energy` with `energy_policy` and an
`advanced` boolean, or `backend: burnin` with `boundary_tick` and `prefix_weights`.
The burn-in hook preserves and reports its independent bundle verification.
Baseline battery behavior remains the default. Changing battery behavior can
change SOC/cost observations and therefore a learned policy's production actions;
production invariance must be measured, never assumed. MPC accepts only its
audited baseline backend here, avoiding a forecast/actual battery mismatch.

## Freeze, then execute

Freeze checks the numerical physical source hashes for all checkpoints and
constructs controller contracts without running reserved factory tapes. The
manifest seals the specification, complete protocol payload, source digests,
artifact paths/digests, configurations, actor seeds, provenance and trace rule.

```sh
python -m stage2.final_eval freeze --selection selected.json \
  --protocol output/stage2-search/final-heldout-protocol.json --output frozen-final.json
```

This command alone is preparation. After the selected policy manifest has been
reviewed and frozen by the parent task, final execution is a separate command:

```sh
python -m stage2.final_eval run --manifest frozen-final.json \
  --output output/stage2-search/final-selected-evaluation --workers 32 --execute-final
```

Changed source, protocol, specification, or checkpoints are rejected. An existing
output directory is refused. The runner does not resume, merge or overwrite an
older run. Final-role manifests require explicit `--execute-final`; development
mode cannot disguise reserved tapes. Exact physical versions must match; a
historical policy adapter cannot authorize a changed physical engine.

Use a single frozen snapshot containing the old matched physical core and every
selected algorithm module. Its location may differ from the artifact location;
the immutable artifact paths must remain available to workers.

## Development-only verification

Development protocols must be explicitly marked and use only 0–31 or 100–115.
They are not final performance samples and need not be stratified.

```sh
python -m stage2.final_eval development-protocol --seeds 0,1 --output dev-protocol.json
python -m stage2.final_eval freeze --selection selected-dev.json \
  --protocol dev-protocol.json --development --output frozen-dev.json
python -m stage2.final_eval run --manifest frozen-dev.json --output output/dev-evaluation --workers 2
```

Tests use development seeds only. They verify immutable provenance, every policy
hook, supported explicit adapters, failure retention, actor clustering, trace
selection and the final-execution gate. No test defaults to the reserved protocol.

## Output and statistical unit

The output contains the frozen `manifest.json`, incrementally flushed
`rows.jsonl`, final `evaluation.json`, and any predeclared traces. Each execution
row records its concrete physical instance SHA, independent checker SHA,
checkpoint SHAs, manifest/protocol SHA, method/configuration, environment tape
ID, actor seed, probability weight, metrics, validation issues, errors and costs.
MPC internal scenarios are charged planning work, not additional measured tapes.
Every actual execution receives the complete physical and immutable-tape checker.
Actual revealed exogenous leaves must match the predeclared tape's leaf.

The checker is anchored to a separate copy of the built numerical instance. Its
digest must match the executed instance, and the execution horizon/tick units
must equal the frozen context. Terminal reserve is required separately. The full
`checker_metrics` dictionary is retained; order counts, fulfillment, cutoff debt,
cost/carbon/grid and stationary SOC must agree with cached simulator summaries.
Any mismatch invalidates the row. Final freeze also verifies the probability map
and exogenous seed labels against the numerical model without running a factory.

Declared actor seeds override inherited `policy_seed` before callback construction,
including artifact base weights. Multi-actor MPC rejects a fixed planning seed;
a deliberately fixed planner seed is permitted only with one actor. Runtime
metadata records package versions, architecture, logical CPUs, available Slurm
allocation and thread settings. Those are diagnostic metadata, not normalized
cross-host speedup evidence. Freeze on the actual immutable execution host because
selection/protocol/checkpoint references are absolute. Use
`stage2.compare_evaluations` for downloaded cross-source paired reports.

All failures remain rows. Worker crashes have explicit unknown timing fields,
rather than invented zero compute. Invalid/incomplete output groups do not receive
valid-only performance summaries. Physical validity and full order fulfillment
remain distinct: a valid trace can still leave orders unfulfilled.

The default retained full trace is the first predeclared tape in each leaf and
the first actor seed, separately for each selected method/configuration. This
rule depends on no outcomes. All invalid traces available to the worker are
retained additionally. `trace_policy` can instead be `none` or `all`.

Actors are replicas nested within each environment tape. Summaries report both
CVaR90 across environment tapes of actor-averaged losses and joint CVaR90 retaining
actor variation with mass `tape_weight / actor_replicas`. The latter can reveal
risky action sampling hidden by actor averaging. `statistics.paired_report`
reports both and bootstraps complete environment clusters within exogenous
strata, preserving actor dependence. Neither actor replicas nor MPC futures
increase the independent environment-tape count.

## Local selector evidence

Each actual row includes `qubo_telemetry`, derived from its already checked
`trace.qubo_decisions`; telemetry does not rerun the checker or selector. It
separates total calls, encoded coupled calls, actual simulated QAOA calls and
their intersection (`coupled_qaoa_calls`). Requested QAOA is counted separately.
One-bit uncoupled simulations remain disclosed as trivial calls. Classical
fallbacks above five total encoded variables cannot increase the count or maximum
size of actual simulated circuits. Core/slack/total bit maxima, coupler maxima,
bit histograms, empty-pool calls, physical-QPU flags, feasibility repairs and
decoder mismatches are reported separately. Coupling includes any slack-variable
quadratic terms; it does not assert global factory-scale quantum computation.

Solver feasibility repair retains the solver's `repaired` flag. If selected
candidate IDs differ from committed IDs, the row is explicitly invalidated with
`qubo_decode_commit_mismatch`; that failure is never relabeled as repair.

Only recorded timings are summarized: `result.elapsed_seconds` and nested
`sampling.optimization.elapsed_seconds`, with coverage counts. Their scopes differ:
ordinary classical selector timing includes encoding, while QAOA-request timing
(including its oversized classical fallback) begins after encoding. Angle search
is a subset of result time and must not be added again. Separate encoding,
isolated solver and decoding durations are unavailable and remain null. Complete
episode wall/CPU and MPC planning costs remain separate from these local fields.

## Selected recovery artifacts and objective variants (23:51 UTC)

`adaptive_recovery` now loads the exact held six-action checkpoint without an inference adapter. Source hashes, feature/action tables, context mapping, network tensor shapes and finite values, eight-segment schedules and720-minute macro intervals are checked. Every decoder option is derived from the saved context; method-level overrides are rejected. Evaluation uses the same deterministic argmax that selected checkpoints on validation. This does not turn repeatedly inspected validation tapes into held-out evidence.

Static/non-MPC backends can explicitly declare `reward_mode` (`original`, `no-batch`, `priority-lex`). The held reward mixin preserves original offers, conflicts, capacities and selected/committed IDs; its process-local dispatch override is restored in `finally`. Reward overrides are rejected for MPC, burn-in and adaptive checkpoint compositions whose continued states were not trained/audited under that objective.

Every selected execution additionally runs the canonical lineage/identity supplement against the freshly built immutable numerical anchor. Missing or changed canonical births, replacement IDs or quality-draw identity invalidate the row. The physical core checker remains separately hashed. The cross-report postprocessor requires matching identity-auditor coverage whenever that source is in the frozen manifest.

The latest22 evaluator tests plus10 strict-comparator tests pass, including corrected QAOA direct-execution equivalence and dynamic adaptive schedule equivalence, actor seeds, artifact contracts, physical anchoring and rejected unsupported composition.

## Guarded and18-action inference, development replay and post-evaluation certificates

`maintenance_outage_guard: true` is an explicit causal execution restriction:
maintenance cannot overlap observed outages or any unrevealed public-support
outage interval. It changes no physical table. For recoveryMPC, the guarded runtime
class is constructed before every continuation is deep-copied; a checked24-order
outage regression verifies both actual and sampled-future execution. Legacy MPC
and burn-in guard compositions remain unsupported and fail before execution.
The original six-action checkpoint keeps its inference implementation and gains
an explicit adapter disclosure when the guard is requested; all144 selected
development replays match unchanged physical trajectories with zero activation.

`adaptive_modes` loads the held18-action checkpoint with its exact action order,
32features, network dimensions, context options and720-minute interval. The
measured maintenance guard and identity-supplement flags are required. Disabling
the guard, passing a six-action artifact, changing decoder options or changing
held inference sources is rejected.

`selected_run.py` replays one named selected method/context on a knowndevelopment
tape using these same frozen-source, instance and identity checks. It cannot
execute reserved final seeds. The formal evaluator remains the final-test entry.

`certify_evaluations.py` reads already completed, strictly checked evidence and
then constructs an offline necessary quality/material bound for each fixed tape.
It rejects mismatched physical sources, instances, demand, missing identity
coverage and any witness below the asserted bound. It reports the weighted
primary-optimum attainment rate and an upper bound on the unknown missing-order
gap; it never promotes positive U−L to an exact gap. Zero U=L includes trivial
all-fulfilled witnesses. Deadline-debt/cost gaps remain unknown. Future keyed
draws used by this postprocessor never enter a deployed controller.


Post-evaluation certificates are deliberately restricted to the audited full minute-grid
horizons5760/14400; other horizons are outside this postprocessor's declared audited scope. The engine
processes completions and reveals at the cutoff before stopping; the underlying
quality/material relaxation correctly includes events at that boundary. Completion
credit composes only with static/context-static recovery. `stage2/final_report.py`
aggregates completed evidence without changing policies; it keeps the preselected
incumbent map and applies nominal97.5percent intervals only to the two predeclared
12-order QAOA-vs-SA/uniform mean-missing contrasts. Other contrasts are exploratory.

## Complete final campaign —17October2026,01:22UTC

All ten source-sealed cohorts completed cleanly:74 method/context groups,23,552
executions, zero invalid rows. The [complete aggregation](../output/stage2-search/final-complete-report/report.json)
contains all41 declared contrasts; earlier partial exports are preserved.
The [complete independent audit seal](../output/stage2-search/final-independent-audit/complete-audit-seal.json)
verifies all592 original retained traces and every row's fresh numerical anchor.
All43 global-bundle files and both40-file runtime archives remain unchanged.

The two family-of-two quantum primary intervals include zero. No post-final
policy switching, new inference search or quantum advantage claim is made.
[Measured capability and limits](STAGE2_RESULTS.md) separates the eight fixed
cheap selections from predeclared alternate-controller comparisons, primary
realized-tape certificates, posthoc explanatory replays and pending submission
duties. The later TRAIN-only neighborhood audit is not a final-policy selection.
