# Recent literature and pretrained-policy audit

Audited 17 October 2026 using the primary papers and the authors' public
repository. No external code was imported or executed, no checkpoint was
unpickled, and no training or physical-model change was made. The Hugging Face
papers lookup workflow supplemented direct primary-source checks.

**Assessment:** the available checkpoint is a useful later warm-start experiment,
with unverified transfer benefit. It does not establish an hours-long shortcut to
our integrated factory. Buffer/assembly safety is the more immediate conceptual
connection; benchmark it as a separately checked algorithm.

## FJSP-LB-MK: related, with a different meaning of kitting

Zhang et al. model category-specific pallets for steel-plate part sorting, using
operation–machine decisions and graph features. Their assumptions omit failures
and dynamic order insertions. They pretrain on synthetic 10×5 instances, then
fine-tune on industrial lines with PPO/KL regularization; initial transfer can
worsen makespan. Reported hardware is RTX 3080 Ti/i9-10980XE, with a 10,000-iteration
training cap and batch 20. I found no reported wall-clock training budget, so
GPU-hours or H100 speedup cannot be inferred. [Primary paper, §§III–V](https://arxiv.org/html/2602.24180v1)

Our matched housing/rotor/flange consumption into a new pump is structurally
different from category pallet sharing. **Inference:** adapting the input graph,
feasible-action masks, BOM joins and resource reservations is substantive
engineering. Changes for workers, portable tools, AGVs, power, uncertainty and
rework would require new features and training/evaluation. Reusing selected
encoders is plausible; successful zero-shot policy transfer is unverified.

## A checkpoint exists; deployment is not verified

The inspected commit is
`91d9278185b2be8ad4d65eb7840a15ab997c22f5`. Its complete, non-truncated 49-entry tree
contains one `.pt`: `FJSP_LB_MK/model/save_10_5.pt`, 849,961 bytes. I downloaded it
without credentials, verified its git-blob hash and inspected only ZIP directory
metadata. SHA256 is
`594f93a9f9838f89bf508297b3019ebaae8a0482a6f3abf91a3be7412198f0ce`.
[Official tree](https://api.github.com/repos/shishunzhang1995/FJSP-LB-MK/git/trees/91d9278185b2be8ad4d65eb7840a15ab997c22f5?recursive=1),
[checkpoint](https://github.com/shishunzhang1995/FJSP-LB-MK/blob/91d9278185b2be8ad4d65eb7840a15ab997c22f5/FJSP_LB_MK/model/save_10_5.pt)

The fine-tuning script explicitly loads that file as pretraining initialization.
Its measured quality, training provenance and compatibility were not executed or
verified. [Official fine-tuning loader](https://github.com/shishunzhang1995/FJSP-LB-MK/blob/91d9278185b2be8ad4d65eb7840a15ab997c22f5/FJSP_LB_MK/train_real_data.py#L65)

Reproduction needs attention: `config.json` caps iterations at 1,000, while
`config_train_file.json` uses 10,000,000. The evaluation script imports
`PPO_model`, absent from the inspected tree, and its GPU branch selects an
author-local checkpoint path. These are verified release details, not runtime
failures observed by executing it.
[Config](https://github.com/shishunzhang1995/FJSP-LB-MK/blob/91d9278185b2be8ad4d65eb7840a15ab997c22f5/FJSP_LB_MK/config.json),
[training config](https://github.com/shishunzhang1995/FJSP-LB-MK/blob/91d9278185b2be8ad4d65eb7840a15ab997c22f5/FJSP_LB_MK/config_train_file.json),
[evaluator](https://github.com/shishunzhang1995/FJSP-LB-MK/blob/91d9278185b2be8ad4d65eb7840a15ab997c22f5/FJSP_LB_MK/test_with_RL_model.py#L123)

The public release list was empty. The linked Google Drive dataset archive was
not inspected, so this audit makes no claim that other weights cannot exist.
No license file appeared in the inspected tree; license compatibility was not
established and no external implementation was copied.

**Inference for this deadline:** retain the existing verified factory and
solvers. A future transfer experiment should use an adapter around our own
feasibility checks, compare random initialization against the released
initialization under equal budgets, and retain negative results. A fast
checkpoint download alone does not remove the adaptation/validation work.

## Assembly deadlocks: a closer conceptual reference

Wang et al.'s abstract addresses distributed processing followed by actual
assembly with limited buffers. It describes HCCE with a Petri-net deadlock
amending method, IDAM, claiming deadlock-free solutions within its studied
model. The abstract does not mention Banker's algorithm. [Primary abstract,
arXiv:2501.14765](https://arxiv.org/abs/2501.14765)

**Inference:** this supports investigating completion-safe resource allocation
for our assembly buffers. It does not prove our new reservation heuristic deadlock
free across transport, tools, skills, rework and disruptions. Until those
conditions are established, describe the implementation as a structural or
Banker-inspired heuristic and report the independent replay and actual
counterexamples. No theorem or checkpoint transfer to our full model was
verified in this bounded audit.

Audit metadata and hashes:
`output/stage2-search/literature-audit/fjsp-lb-mk-audit.json` and
`fjsp-lb-mk-tree.json`.
