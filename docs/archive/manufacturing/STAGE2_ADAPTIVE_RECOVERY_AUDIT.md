# Independent audit of adaptive recovery v12

Audited `stage2/adaptive_recovery.py` SHA-256 `7fbe58fb6131e0a2101bf7f2a0282bc8c81e3ab09a6ccf7ce0e01da8f5b9498e`, without changing the running fit or physical source files. Six actions choose WIP4/6/8 and QA guard0/4; routing, admission, tool homes and physical recovery remain the explicit context's settings. This is a small controller trained for this factory, not a pretrained general scheduling model.

No causal, split, inference-sign or static-fallback defect was found in the inspected implementation. The following checks are retained under `output/stage2-search/adaptive-recovery-independent-audit/`:

- `direct-smoke.json` and three complete gzipped traces compare the actual n12/n16/n24 strong contexts on TRAIN seed0 with actor seeds0/17/91. Static callback and direct control match exactly in operations, transport, worker walks, events, energy, metrics, admission history and algorithm audit. All traces independently pass the anchored physical checker and terminal battery requirement. This checks equivalence, not completeness: shipped counts are14/14,14/18,12/26 respectively.
- `inference-audit.json` checks64 pure inference cases against Torch: NumPy old-log-probability maximum absolute error`2.10e-7`, critic maximum error`4.47e-8`, all deterministic argmax actions agree. Actor seeds propagate into weights, hidden-field perturbations leave actions unchanged, and cached callbacks do not invent decisions. This is arithmetic/causal falsification evidence, not a proof over every history.
- In the full minute-grid H5760 contexts, macro decisions occur at0,720,1440,2160,2880,3600,4320,5040. Calls between boundaries preserve the current action. CEM's eight normalized time segments align with those boundaries for these contexts. That alignment should not be assumed for arbitrary horizons or coarser time grids.

Training draws factory seeds only from0–31. Validation uses100–115 with actor0 and deterministic argmax; final tapes remain untouched. PPO training actor seeds are separate from factory tapes and advance with rollout count. Observation features are the documented32 public aggregates plus the controller's own prior action; the policy does not read hidden factory seeds or unrevealed QA draws.

Reward shaping telescopes exactly to terminal reward under the undiscounted Monte Carlo returns used here. The terminal reward makes one missing order dominate its bounded secondary terms. Its deadline/cost scalarization remains a training surrogate; validation selection uses the explicit lexicographic key `(invalid, missing, cutoff deadline debt, total cost)`. Descriptive action-change counts are not a schedule-stability penalty.

The static incumbent is validated first and stays eligible throughout checkpoint selection. Strict key improvement is required to replace it, so a learned checkpoint cannot be selected with a worse recorded validation key. Repeated validation comparison is model selection on reused development data, rather than an unbiased held-out performance estimate. Strong context priors are conservatively **DEVELOPMENT-selected**, including earlier validation-informed iteration; the referenced earlier campaign files contain both TRAIN and VAL, so their filenames alone do not prove TRAIN-only prior selection.

CEM's preliminary top-seven sequence filter averages rewards on unequal observed TRAIN subsets. It then reranks those finalists plus the static incumbent on common TRAIN0–7 before taking one candidate per context to VAL. This is a heuristic search/filter with selection bias, not an unbiased estimate of each discarded sequence's quality. The unchanged static fallback limits validation regression; it does not establish generalization.

## Evidence gaps and supplemental seal

The original v12 episode log drops trajectories and has no per-row network digest/update identifier. Rejected validation networks are not all retained because `selected-checkpoint.json` is overwritten. The selected policy remains reproducible; a complete independent replay of the exploration path is not supported by those logs. Initialization, cloning and whole rollout/rerank/validation batches can overrun the requested duration: the time budget is soft, and actual wall time must be reported.

`sequential.summary().simulation_cpu_seconds` sums rollout **wall** time. Adaptive v12 rows separately record actual worker `cpu_seconds`; those literal row values must be summed for CPU accounting. In the existing one-update smoke, the TRAIN batch's label12.4559CPU seconds corresponds to12.3457 actual worker CPU seconds. These worker totals include checks/source guards and exclude unisolated learner/orchestration work. Prior teacher/search costs must also be carried forward.

The separate `stage2/adaptive_evidence.py` overlay SHA-256 `a1cc3c0c6b3691f9b4e86b3cd78a25d495aeba20d11ad962850c3bb3538064ee` leaves all v12 sources and original results intact. Five tests cover raw cost/split/counter reconciliation, source/log tamper rejection, selected-policy digests, read-only hash-seal verification, exact16-tape mocked replay aggregation and mismatch handling. Mocked tests do not count as actual selected-policy validation runs.

The utility requires an explicit completed-run attestation and a new output directory. It archives the original checkpoint/protocol/log/source snapshot, selected policy blobs and its own overlay source; records source/package/runtime/allocation/thread metadata; labels priors and missing exploration records honestly; and separates summed worker CPU, summed rollout wall and original total wall. Runtime metadata describes the seal/replay process; it must not be presented retrospectively as the original fit environment. Optional caller-supplied original runtime/job evidence is separately hashed and labeled.

Its optional replay executes each selected deterministic context on every declared VAL100–115 tape using the frozen original backend. It retains full selected traces and public trajectories, anchors checking to a fresh instance, reconciles cost/debt/fulfillment/terminal metrics, and compares the replayed key with the exact declared checkpoint key. Integer components must match exactly; the cost check additionally reports a tiny floating tolerance. Failed replay is preserved as `replay_mismatch`, rather than silently accepting a new result. This is validation reproducibility, not untouched final evidence.

A seal-only demonstration on the already completed one-update smoke is retained in `adaptive-recovery-independent-audit/ppo-smoke-seal/`; its23-file seal verifies, and no additional factory tape was executed for that demonstration. At the initial audit, allocated selected-policy VAL replay had not launched; the completed follow-up is recorded below. Read-only files and hashes provide integrity checks; they are not an authenticated signature or an OS-immutable archive.

Standalone invocation against the frozen source root:

```sh
PYTHONPATH=/frozen/v12 /path/to/python /overlay/adaptive_evidence.py FIT_DIR \
  --output NEW_EVIDENCE_DIR --execution-complete --replay --workers 32
```

Verify a transferred archive with `adaptive_evidence.verify_seal(directory)`. No final tape, external hardware or new policy fit is required for sealing.

## Completed fit and selected-policy replay

All three32-CPU Axion fits6117339 completed, followed by actual selected-policy replay/seals6117453. Local evidence is `output/stage2-search/axion-adaptive-evidence-2349/results/{0-ppo-2026,1-ppo-2027,2-cem-2026}/selected-seal/`; all three75-file seals verify after transfer. All144 selected VAL traces pass independent physical replay and the separate identity supplement, and all nine context selection keys reproduce exactly. The protocol remains TRAIN0–31 fitting and reused VAL100–115 selection, with no final tape.

| Method |12-order missing|16-order missing|24-order missing|Selected behavior|
|---|---:|---:|---:|---|
|PPO2026|0|44|188|Constant6/4 at12/16;24 retains static4/4|
|PPO2027|0|50|188|Constant6/4 at12;4→6 at720 at16;24 retains static4/4|
|CEM2026|0|31|164|Eight-segment open-loop time schedules|

Missing counts sum across sixteen VAL tapes, which contain210/274/402 realized orders. Both PPO networks'12-order policies and PPO2026's16-order policy exactly match their constant6/4 controls in every physical list and metric. PPO2027's16-order switch loses to constant6/4 (50 versus44 missing). Nonzero nominal changes therefore do not establish adaptive benefit.

CEM's selected action sequences, with action IDs0=4/0,1=4/4,2=6/0,3=6/4,4=8/0,5=8/4, are12:`[5,4,5,3,0,5,5,5]`,16:`[2,5,1,1,1,1,3,1]`,24:`[5,1,1,1,4,3,0,1]`. All processing modes remain standard. At16 orders CEM misses31 versus44 for the best of its actually used constant controls; at24 it misses164 versus188 among its used controls. At12 it ties constant6/4's zero missing and reduces summed cutoff debt50175→48840, with higher cost. These diagnostic comparisons use reused validation and the subset of statics actually used, so they do not prove superiority over the whole static domain or state-dependent RL advantage. The separate broad static campaign should also be reported.

PPO2026 actual fit wall1200.165s, worker rollout CPU28682.036s; PPO2027 wall1205.536s, worker CPU29317.276s; CEM wall1216.086s, worker CPU31627.777s. CEM recorded9096 fitting/720 validation rollouts; PPO2026 recorded9048/816 and PPO2027 recorded9368/816. Scheduler elapsed1201/1207/1216s,32 CPUs each, actual total CPU07:58:46/08:09:23/08:47:19. Requested1200s limits are soft. Raw scheduler records are in `axion-adaptive-modes-2359/accounting-completed.txt`; complete rollout CPU/wall scopes are in each sealed report. Old rejected network/trajectory evidence remains unavailable, as disclosed above.

The guarded final-backend adapter was checked separately in job6117469 using identical selected policies, deterministic inference,720-minute decisions and actor0. All144 guarded traces pass core and identity checking; all144 physical trajectories and metrics exactly match their original selected-policy traces, every selection key stays unchanged, and observed guard activations are zero. Reports/full traces are under `output/stage2-search/axion-adaptive-modes-2359/guarded-v12-6117469/`. This establishes equivalence for these selected VAL executions, not for every possible policy or future tape. Algorithm audit timing fields are explicitly excluded from physical equality. The frozen original v12 module and physical core were not changed.
