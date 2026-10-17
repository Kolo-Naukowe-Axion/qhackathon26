# Bounded physical kit repacking

`stage2/kit_recovery.py` tries to release a blocked inspection output by physically
repacking accepted components between the two assembly input buffers. It is
disabled by default. No physical source, storage node, buffer capacity, resource,
transport duration, assembly recipe or quality rule is changed.

The motivating TRAIN seed8 state contained four reserved incomplete kits, each
with two components in assembly, while P05's accepted housing and flange blocked
both QA outputs. A missing third component could not be inspected. Borrowing one
assembly place could merely move the blockage: once the third component became
accepted, its target still needed another input place.

## Search and execution

The bounded BFS considers positions of currently observed, accepted, idle
housing/rotor/flange components in assembly inputs or QA outputs. Its only
destinations are the existing assembly stations. Nonmovable physical occupancy
and reservations reduce available capacity. Search never visits more than5000
states or more than six moves per plan, and returns the shallowest discovered
plan. Exhausting either bound is a retained search failure, not proof that no
physical solution exists.

If a currently complete accepted kit exists among QA-blocking orders, that is
the target domain. Otherwise, the planner can stage a blocking order's currently
accepted components while physically leaving room for its complete three-part
kit. It explicitly waits for genuinely observed acceptance of the missing
component(s); no future inspection result is assumed. This conditional staging
extension is necessary because the seed8 deadlock initially contains no complete
accepted kit at all.

A typical plan moves a donor component from A1 to A2, then moves P05's two
accepted QA outputs to A1. A1 now has one real empty input place for P05's third
component. Every leg uses the original `Factory.move`: AGV availability, empty
travel, edge reservations, pickup/drop timing, battery, input capacity and
in-flight destination reservations all remain real. Legs execute serially; the
next starts only after the prior one arrives. Existing assembly-related
in-flight legs must finish before planning.

While recovery is active, ordinary assembly arrivals and other assembly starts
are locked. Other manufacturing continues. New acceptance of the target's
missing component permits another original physical leg. The target then uses
the original assembly method and original parent consumption. Locks release
when the target actually starts assembly. Donor orders retain their original
targets, so normal assembly dispatch physically returns staged donors later.
Parts are never teleported or removed from inventory.

Continuing manufacturing can create a different, fully accepted kit on a QA
output while the original target is still incomplete. The controller may then
run another bounded search and explicitly retarget to that observed complete
kit. This is logged separately from success. It avoids waiting on unknown future
quality when a real complete kit can release capacity now. Old target mappings
are restored on retarget/abort; no committed AGV leg is canceled.

Default enabled-policy timing is120 quiet production-start minutes before
triggering,120minutes cooldown, and a720-minute maximum lock. Times convert to
the instance's tick size. An observed QA-output blockage is also required.
Quiet time is a heuristic trigger, not a deadlock certificate. Search failures,
actual legs, retargets, timeouts and any active recovery at the horizon remain
in `algorithm_audit.physical_kit_recovery`.

## API

```python
trace = stage2.kit_recovery.run(
    instance, weights, controller,
    tool_policy={"mode": "hard"},
    kit_reservation=True,
    admission=True,
    recovery_policy={"enabled": True, "quiet_minutes": 120},
)
```

This composes with the frozen KitToolingSpecialistFactory, optionally preceded
by AdmissionMixin. QA guard0 disables that guard; admission weights retain their
existing meaning. Omitting recovery options preserves current kit-policy
physical behavior exactly. No frozen final-evaluator backend is changed or
silently opted in by this module.

## Diagnostic evidence and limits

Six tests pass: bounded search and invalid physical occupancy, default-disabled
equivalence, complete independent checking and paired causality on four diagnosed
tapes, exact logged physical legs/assembly locks, and timeout restoration.
The current source SHA256 is
`de405130cf3b1ef6ed76a5dc3c27893c23bfc65cf87bde2eae5d0cdd8b3bde8b`.
Raw traces, source snapshot and all exploratory variants are retained under
`output/stage2-search/physical-kit-recovery-diagnostic/`.

| Deliberately selected failed TRAIN tape | Enabled recovery,120min trigger | Total required | Tardiness,min |
| --- | --- | --- | --- |
|8|12 shipped|12|3947|
|15|12 shipped|14|9034|
|24|14 shipped|14|5993|
|26|12 shipped|12|2492|

All four actual traces are physically valid. Seed15 leaves the original P11
order's final pump scrapped after two QA failures and the urgent U01 order
unfinished. Its two misses are not both urgent. These four tapes were chosen because prior methods failed,
so they cannot estimate general performance. A60-minute trigger retains the
same shipment counts here but worsens seed24 tardiness from5993 to9761minutes.
The earlier prototype without observed-complete-kit retargeting had timeouts
and shipped only10/14 on seed15; those negatives are retained. Its exact earlier
source was not archived and is explicitly marked as exploratory provenance.

The BFS ignores future unknown outcomes and does not jointly optimize future
manufacturing. A conditional target can fail inspection, lack material, miss a
shift, or remain incomplete. Physical capacity can leave no legal repacking
sequence. Staged donors can delay other orders. A timeout releases locks without
pretending a recovery succeeded. This is neither universal deadlock freedom nor
a global scheduling solution. Validation and reserved final tapes were not run.
