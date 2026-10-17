# Released-order family admission

`stage2/release_admission.py` tests one concrete scheduling restriction without changing physical production. The unchanged family admission ranks all known pending orders, takes the first available scheduling slots, then admits only members of that head whose release has arrived. A known future release can therefore reserve a slot while a released order outside the head waits. Read-only original-prior seed0 traces show this for360 initial minutes at n12 and240 minutes at n16. These are observed underfill opportunities, not a proved throughput loss: waiting can preserve useful family setups and batching.

The optional rule instead selects the family head from publicly released orders. It preserves previously admitted slots, every order, every physical component and the objective. No stock, machine, worker, tool, buffer, transport or processing constraint changes. It does not retire failed orders or reclaim inventory. Only the order dictionary visible inside `AdmissionSet.update` is temporarily filtered; `finally` restores the original dictionary even on exceptions. The existing family ranking and admission history remain intact. No uncertainty seed, future quality draw or unrevealed urgent arrival is consulted. Deepcopy preserves the admission-set backlink to the copied factory.

The `ReleaseAwareMixin` flag is `release_aware_admission=False` by default. `ReleaseAwareFactory` composes it with the frozen guarded completion/recovery/family-admission backend. Enabled use is restricted to FAMILY admission and rejects the unaudited dead-slot-reclaim combination. Disabled use preserves the original admission object and exact physical behavior.

One128-episode paired TRAIN0–31 experiment compares off/on at two fixed contexts: original n12 WIP8/QAguard4/standard, and matched n16 WIP6/QAguard4/standard. Both use hard tool homes, kit reservations, physical recovery, family admission, maintenance guard on, QA routing off, completion credit0 and BOM priority off. There are no new thresholds or scales. If primary fulfillment does not improve, the direction stops; lower debt alone cannot conceal fewer shipped orders. All setup minutes, actual multiunit process batches, flow descriptors, costs and per-tape regressions remain retained.

Five tests cover default equivalence, already-admitted future-slot preservation without deleting orders/parts, exception restoration, deepcopy backlinks, three actual checked/paired-causal traces and the exact128-run TRAIN protocol rejecting final/altered/partial tasks. Every campaign episode receives the full physical checker, selected/committed equality check and before/after source hashes. The immutable v18 snapshot and Slurm6117495 submission are retained under `output/stage2-search/axion-release-admission-v18-submission/`. No validation or reserved final tapes are authorized by this driver.

## Completed result: reject this rule

All128 episodes passed every physical/source check. The paired controls exactly reproduce their corresponding static-grid episodes. Filling the early scheduling slots makes the factory substantially worse:

| TRAIN32 context | Off shipped/required | On shipped/required | Off→on complete tapes | Off→on setup minutes |
|---|---:|---:|---:|---:|
|n12 WIP8|422/424|406/424|31→23|55875→76575|
|n16 WIP6|465/552|387/552|3→0|49635→95205|

Aggregate tardiness rises110484→226576 at n12 and429070→595214 at n16. n16 multiunit process batches fall153→120; n12 batches remain125. Setup occupancy increases37% and92%, respectively. These outcomes support the value of family continuity; they do not isolate every causal path behind the regressions. In particular, a visibly unused scheduling slot did not establish a net loss: admitting another family can incur enough later setups and congestion to be harmful.

The rule is unselected and the direction stops without validation. The run used16.33s driver wall time; Slurm17s on32 CPUs,544 allocated CPU-seconds and467.643 consumed CPU-seconds, peak0.95GiB, zero GPUs. All rows, first-tape off/on traces, immutable source and accounting remain retained rather than discarded as an unsuccessful idea.
