# Reward-only dispatch ablation

`stage2/selector_reward.py` keeps the existing frozen operation/crew offers, all resource conflicts and every cumulative power constraint. It changes only candidate rewards, using a process-local dispatch wrapper restored in `finally`. Nested and cross-thread overrides are rejected. Independent processes can run matched episodes in parallel. Default `original` calls the original factory directly.

Three objectives have explicit meanings:

- Original: `(1 + batch_size) * 100 + normalized_priority * 100`, where normalized priority lies in[0,1). An extra batch unit adds100, enough to outweigh almost the entire priority range.
- No-batch: `200 + normalized_priority * 100` for every operation. This removes the extra batch incentive while retaining the single-operation base and existing public priority normalization. It still trades off several lower-ranked starts against fewer higher-ranked starts.
- Priority-lex: sort original candidates by public priority, breaking ties by stable request index; assign rewards `2 ** (N - 1 - rank)`. Each candidate outweighs all lower-ranked candidates combined. Exact maximization therefore gives lexicographic acceptance over this fixed candidate domain. It is not a global factory objective or automatically equivalent to sequential priority with worker reassignment. The dynamic range can make approximate solvers harder; quantum or annealing success must be measured under the new coefficients.

For each changed objective, the unchanged dispatch constructor creates the original constraints with its cheap greedy result charged as preprocessing; the requested solver is then applied to the rewritten rewards. Construction and solver costs remain explicit. No future quality draw, hidden shock or seed-specific order rule enters the reward. Six tests cover batch-priority inversion, correction by both objectives, invariant resources/constraints, exact lexicographic dominance and stable ties, default physical equivalence, wrapper restoration, independent physical checks and paired causality.

The predeclared48-episode development comparison uses n12 TRAIN0–7 plus diagnosed severe failures15/23/25/26, all under the same strong recovery/hard-home/family-admission/WIP8/QA-guard4 backend. Every episode passed the full checker and selected/committed checks. These selected tapes are not an unbiased completion-rate estimate.

| Policy | Shipped/required | Complete tapes | Total tardiness ticks |
|---|---:|---:|---:|
| Original exact |102/160|1/12|219653|
| No-batch exact |158/160|11/12|47946|
| Priority-lex exact |158/160|11/12|44440|
| Strong sequential priority |158/160|11/12|44875|

The39.23s two-worker run retains every source, trace, raw row, preprocessing cost and failure in `output/stage2-search/selector-reward-targeted-training/`. This largely explains the prior exact-selector collapse through reward semantics rather than solver inability. The remaining original-pump scrap case and higher-load failures remain part of the objective. Improved local reward does not establish end-to-end optimality or quantum advantage.

The follow-up file `output/stage2-search/selector-reward-paired-train32-tasks.json` contains512 paired TRAIN0–31 episodes for n12/13/14/16 with all four controls. It preserves each context's strong-selector-cohort weights; n13 explicitly inherits the n12 prior. This is prepared for root dispatch, not a validation or final result. Run with `python -m stage2.selector_reward --tasks <file> --output <new-directory> --workers 32`. Existing controls may be reused only after checking the exact physical/algorithm configuration and source provenance. This driver refuses validation/final seeds and output overwrite; all invalid episodes remain retained.
