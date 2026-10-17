# Frozen evaluation and cross-source paired evidence

The evaluator contract was independently reviewed before reserved final execution. No final factory tape was executed during this audit. Root retained ownership of `final_eval.py`; this task added `compare_evaluations.py`, tests and development smoke artifacts without changing physical sources or the low-level statistics implementation.

## Findings and fixes coordinated with the evaluator owner

- Inherited static/teacher `policy_seed=0` could defeat actor replicas because `setdefault` preserved it. Root now overrides the seed before callback construction and after context composition, and declares `actor_seed_policy`. Multiple-actor MPC rejects an explicit fixed planner seed. Callback base weights must preserve the override too.
- A physically replayable trace could fail its terminal reserve while `checked.valid` remained true. Final evaluation now requires terminal feasibility separately.
- The pre-run physical-instance hash did not itself prove that the checker used that instance. Root now checks against an independent copy of the built instance, compares the executed instance digest, and requires exact execution horizon/tick units.
- Cached simulator order/debt and energy/carbon summaries were insufficient independent outcome evidence. Root now retains full `checker_metrics`, reconciles core outcomes and floating cost/carbon/SOC quantities, and invalidates mismatches.
- Internal protocol mass/hash checks alone could accept rehashed but wrong scenario weights. Root now binds final leaf/outcome probabilities and seed branch labels to the configured model before execution. This reads exogenous labels, not factory/quality outcomes.

These fixes belong to their evaluator source snapshot. Old reports do not acquire the new guarantees just because the new reader exists.

## Strict cross-report aggregator

`stage2.statistics.paired_report` is deliberately a low-level reducer. It checks complete tape/actor groups and validity flags, but does not verify physical-instance hashes, method/config filtering, source groups, checkpoint identities or protocol provenance. A corruption test demonstrates that it accepts matching seed IDs from different physical instances. Use `stage2.compare_evaluations` to gate comparisons across evaluator packages.

The wrapper requires completed `manifest.json`, `evaluation.json` and matching `rows.jsonl`. It checks the manifest seal; exact expected execution identities; role/protocol/leaf/tape weights; per-method checkpoint hashes; actor declarations; full checker metrics; terminal feasibility; cached-versus-independent metrics; and executed-versus-built numerical instance hashes. Missing/duplicate/invalid selected executions suppress comparison. Physically valid incomplete fulfillment remains included in the primary missing-order loss.

Engine, numerical-specification, blueprint and independent-checker source hashes must match across groups. Every paired environment must also have the same numerical-instance hash and mandatory demand across actors/methods. Dispatch and other algorithm/evaluator source differences are retained explicitly. This supports historical-dispatch learned/MPC methods versus newer-dispatch strong methods, while preserving their implementation distinction; it cannot attribute a difference to one isolated feature without a matched ablation.

Stored absolute remote checkpoint/selection/trace paths remain opaque provenance. The reader checks the downloaded package files and stored hashes without opening execution-host paths or requiring the old environment to be installed. It is an evidence-consistency gate, not a physical rechecker, digital signature or defense against deliberately fabricated files. Older cached-only evaluator output is rejected rather than silently upgraded.

```sh
.venv-stage2/bin/python -m stage2.compare_evaluations \
  --left DOWNLOADED_OLD_GROUP --left-method METHOD_A \
  --right DOWNLOADED_NEW_GROUP --right-method METHOD_B \
  --config '{"orders":12,"horizon":5760,"profile":"full"}' \
  --bootstrap 2000 --output NEW_COMPARISON.json
```

Outputs distinguish missing orders, cutoff-censored deadline debt, delivered-only tardiness, total cost and carbon. Right-minus-left negative favors the right method for each loss. Method definitions, frozen/actual runtimes, source differences, package hashes, aggregator/statistics hashes and cost-scope limitations accompany the numbers.

## Statistical scope

Each environment tape has its declared leaf probability divided by its leaf sample count. Means and CVaR90 use those weights, including a fractional tail boundary. Replicas average within each environment for one CVaR; joint actor/environment CVaR separately retains each actor's conditional mass. Different replica counts can be compared without inventing additional independent factories.

Bootstrap draws resample whole paired environments within each fixed exogenous stratum. Actor cohorts stay together and fixed. Confidence intervals are empirical, conditional on the observed actor cohorts and pseudorandom tape design; they are pointwise and not corrected for multiple comparisons. A tail-risk difference is the difference between methods' CVaRs, not CVaR of per-tape differences. These estimates do not prove all-future robustness or global optimality.

Current runtime metadata records Python/platform/package versions. It does not fully characterize CPU allocation, architecture or thread settings, and runtime drift is not a physical-source change. The wrapper retains and flags frozen/actual runtime differences and deliberately offers no wall-time speedup metric. Training/teacher work, rollout planning and inference remain explicit per-manifest costs; cross-host timing claims need appropriate hardware/allocation evidence.

## Actual development smoke and tests

`output/stage2-search/cross-report-development-v1/` retains two complete copied source snapshots with identical physical/verifier sources. One uses historical dispatch SHA `da50ae48f77512be433b042e8f6b8ecb40f7b2adc5ff35ba61bc769e3762b8a0`; the other uses current dispatch SHA `575c243418fc282ec4de8864ff6744809ed0d920a948607b83e271fa9e0c6fe5`. Each evaluates one initial order on DEVELOPMENT tapes0/1 with actor seeds901/902: eight episodes total. Both selection files deliberately include inherited static `policy_seed=0` and use the QAOA selector.

All eight traces pass anchored physical/terminal checks and metric reconciliation. The source-copy audit confirms originals stayed unchanged. The actor-seed audit checks all248 actual simulated calls: each sampler seed equals its declared actor plus dispatch tick. Both groups produce equal outcome metrics on this small smoke, and the paired wrapper reports two environments, not eight. The200-bootstrap comparison is API evidence, not a performance or generalization result.

Nine tests cover cross-dispatch grouping, different replica counts, physical-instance/source mismatches, invalid/terminal/legacy rows, missing replicas and seed-contract absence, cached metrics/weights/checkpoint/seal corruption, runtime disclosure, remote-path opacity and rows-log integrity. Synthetic metadata fixtures are labeled as such and are not factory results.
