# Whole-kit space reservation

`stage2/kitting.py` addresses assembly-buffer fragmentation with a causal
scheduling restriction. It leaves the numerical instance, physical buffers,
portable tools, transport, processing, workers, quality and order objective
unchanged. This is a classical control heuristic; it has no global optimality or
universal deadlock-avoidance guarantee.

## Observed failure and rescue

In a development run with 12 initial orders, environment seed4, hard portable-tool
homes and QA guard4, station A2's six input places held housings and flanges from
P05, P09 and P11. Each order needed its rotor to complete the three-component kit.
P05's accepted rotor remained on QA1's output because A2 had no input place. That
output blocked further inspection. Three incomplete kits had occupied all six
places even though no kit could be assembled.

The diagnostic terminal state is retained in
`output/stage2-search/tooling-deadlock-n12-s4-terminal.json`. It shipped7/12 orders.
The corresponding kitting rescue shipped12/12, with4199minutes total tardiness;
the full trace is `output/stage2-search/kitting-deadlock-n12-s4.json`. An independent
recheck returned valid with zero issues. Its SHA256 is
`457fdf8f8ae7a66a91697f51eb24c3a1fbc61d43b5e984efd7c3536148fccc6f`.
This is one TRAIN-tape diagnostic, not held-out or aggregate evidence. Different
policies, loads or tapes can regress and must remain in comparisons.

## Policy

The BOM contains exactly three physical components: housing, rotor and flange.
On observing an accepted component for an unassigned order, the policy reserves
one conceptual three-place kit position at an assembly station. A station with
input capacity6 therefore admits at most two concurrent unassembled order kits.
Candidate stations are ranked by active kit count, then existing physical and
in-flight input occupancy, then station ID. Orders are considered by known due
date and ID. No hidden future arrival or quality draw enters this choice.

Reservation is bookkeeping, not physical occupancy. Each component still travels
through the original AGV/edge/battery model, and every actual input arrival obeys
the original capacity check. The existing assembly process consumes its three
parents only when a real operation commits. A successful pump creation releases
the kit reservation; a failed attempt to start assembly does not. Pump rework
still requires physical return transport and input space.

The mixin temporarily filters only the assembly scheduling pass to eligible kit
orders. A `finally` block restores the exact original order dictionary. Inventory,
subsequent dispatch, public observations and final metrics retain all orders.
Trace audit records reservation history and deferred order-ticks.

## Remaining failure modes

- All kit positions can belong to incomplete orders while an accepted component
  of an unreserved order occupies a QA output. Blocking that transfer can prevent
  inspection of the reserved kits' missing components. Acquiring reservation
  earlier in the QA flow is a possible future policy, not implemented here.
- A pump returning from failed final inspection occupies real assembly input
  space outside the three-component reservation count. The physical move remains
  blocked when full; conceptual reservations cannot authorize overflow.
- An order with an irrecoverable missing component can retain a reservation and
  cause starvation. Reservations are not a proof that the remaining kit will
  eventually become feasible.
- Finite buffers, blocked outputs, worker calendars, tool homes, AGV contention
  and scarce input material can create other cycles. Restricting admission can
  also reduce throughput when a less constrained policy would have succeeded.

## API and evaluation

```python
trace = stage2.kitting.run(
    instance, weights, controller,
    tool_policy={"mode": "hard"},
    specialist=True,
    kit_reservation=True,
    admission=True,
)
```

Tool policy omission selects the advanced factory without a tool-home mixin.
`specialist` enables the QA-worker guard; its threshold stays in `weights`.
`admission` enables persistent order admission ranking (`admission_rule` and its
coefficients also stay in weights). Four explicit admission compositions retain
the corresponding non-admission factory behavior. With reservation disabled, the
original assembly logic runs unchanged.

The frozen evaluator selects this only through `kind: kitting` or the explicit
`backend: kitting`. It resolves and seals `kit_reservation: true` by default for
that backend, supports an explicit false ablation and per-context weights/tool
policies, and hashes the kitting source. Existing backend defaults are unchanged.
The battery remains the baseline battery; energy, MPC and common-burn-in
combinations are not silently introduced. All actual traces receive the full
checker, including random-tape auditing.

Development tests cover disabled-mode physical equivalence, four complete-kit
positions competing with five orders, reservation release, exception recovery,
paired causality, a real seed16 pump QA failure/return/repair, and physical
full-buffer rejection. The evaluator also checks direct composed equivalence and
the explicit option contract. Reserved final tapes are not used by these tests.
