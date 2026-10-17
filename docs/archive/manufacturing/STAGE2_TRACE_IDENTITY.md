# Supplemental canonical lineage and QA stream verification

`stage2/identity_audit.py` is an independent supplement to the frozen physical checker. It imports neither the engine nor checker validity helpers. Use **both** against the same trusted fresh numerical instance:

```python
physical = check_trace(trace, instance)
identity = audit_trace(trace, instance)
valid = physical['valid'] and identity['valid']
```

An execution may be valid and incomplete. Orders that never reach assembly legitimately have no pump birth; any order that does reach assembly has at most one initial pump, with a fixed identity.

The supplement verifies:

- Each initial order has exactly one `${order}/housing/1`, `${order}/rotor/1`, `${order}/flange/1`, with matching immutable order/recipe/family/release fields. Initial pump records and duplicate/alternative component IDs are rejected. A supplied instance anchors the initial trace identity tables.
- Urgent order IDs follow the engine's fixed `U01,U02,...` revelation order. Otherwise changing the order name could also redraw all of its nominally canonical component streams. Each urgent order creates exactly the same three canonical component IDs, once, at revelation.
- Every non-rework assembly birth has singleton output `${order}/pump/1`. A renamed output, second initial pump, or fresh pump identity after scrap is rejected. Assembly repair reuses the original pump identity.
- A replacement is exactly `original_component_uid + '~r1'`, once, with a matching authorized new-unit birth. Pump replacements, recursive replacements and alternative suffixes are rejected.
- Executed operation/parent/part-move/event references refer to authorized identities after birth. Per-unit recipe-step keys match operation units; primary unit/order identities agree. Batched components may belong to different orders, as in the physical model.
- Each QA event references the unit and bounded attempt on its QA operation, and its actual audit uniform equals the first64 SHA-256 bits of `"{seed}:quality:{unit_id}:{attempt}"`, divided by`2**64`. Operation IDs are diagnostic references; changing them does not change the stream. Duplicate unit/attempt inspection events do not create fresh draws.

This closes a specific semantic coverage gap without changing historical checker, engine, spec, source groups or physical instances. Frozen `check.py` already verifies much component/replacement genealogy but did not require the canonical pump name. The current engine always emits canonical pump IDs; the gap concerns independent verification of an adversarial rewritten artifact.

## Retained verification

Eight tests in `tests/stage2/test_identity_audit.py` pass, including coherent renaming of every pump reference and its QA draw, initial/urgent renaming, duplicates, replacement suffix/pump restrictions, unknown references, operation-ID invariance and bounded attempts.

`output/stage2-search/canonical-identity-audit/report.json` checks20 retained traces with both independent physical replay and the new supplement: three strong n12/n16/n24 TRAIN traces, all eight n32/H14400 TRAIN witnesses, the complete checked QAOA factory trace, and eight optimal/heuristic tiny-reference traces. All pass. The seed6 n32 witness exercises the real `P05/housing/1~r1` replacement lineage. These checks replay existing artifacts and execute no new factory or final tape.

The retained `adversarial-renamed-pump-legacy-accepted.json.gz` rewrites `P01/pump/1` to `P01/pump/2` throughout a real checked trace, including all genealogy/recipe-step keys and the newly keyed QA uniform. Its unchanged passed outcome remains consistent. The old anchored physical checker accepts it; the supplement rejects `pump_birth_identity`. This is a negative test artifact, not a production solution.

Supplement SHA-256: `3faf6ca7e90e8061babef543aeb68e19a292ce8dbcab309d4412f0a258f95c70`. Frozen physical checker remains `40c96bf26f19aa10e33566332d55133f8bd73c32878753668202b4690ce4bf5b`; engine/spec digests are retained in the report. A final evaluator may source-guard this additional module alongside its existing anchored core checker, preserving historical core contracts.

## Legacy metadata note

The numerical blueprint's descriptive `quality.paired_key` array still lists `operation_id`. That legacy array does not select the executed random stream. The actual frozen engine, independent checker and [trace contract](../../../stage2/TRACE_CONTRACT.md) use `quality:{unit_id}:{attempt}`. The supplement reports this discrepancy explicitly as an informational metadata note and verifies the actual key. No instance or blueprint was rewritten during this audit.

This supplement does not replace physical replay, prove nonanticipativity or establish optimality. Without a supplied trusted numerical instance, its external anchoring is limited to the trace's own initial tables; that limitation is returned in provenance.
