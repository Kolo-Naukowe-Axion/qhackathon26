# Process-scoped ETA routing probe

`stage2/routing.py` tests whether a queue/worker-calendar estimate helps at QA
while hurting routing elsewhere. The nominal score charges only six ticks per
queued input; QA attendance/processing is much longer. This motivates a bounded
comparison, not a claim that a more complicated score is inherently better.

The module reuses `AdvancedFactory.estimated_machine_finish` and its existing
free-input-buffer filter. It adds no predicted physics or learned model. ETA
uses public work, travel, tool state and known worker calendars as a ranking
heuristic. Joint crew fits, tool homes, real transport, buffers, wear, energy and
quality are still decided by the original physical methods. An estimated finish
is not a guaranteed feasible completion time or a lower bound.

## Controller contract

```python
trace = stage2.routing.run(
    instance, weights, controller,
    routing_policy={"eta_processes": ["QA"], "free_buffer_processes": ["QA"]},
    tool_policy={"mode": "hard"},
    kit_reservation=True,
    admission=True,
)
```

The factory composes `RoutingMixin` with the frozen
`KitToolingSpecialistFactory`, optionally preceded by `AdmissionMixin`. Guard0
disables the QA worker guard; `kit_reservation=False` disables kit reservations.
The tool policy is passed through unchanged; the campaign specifies hard homes
explicitly. Existing defaults of the underlying ToolingMixin remain its defaults.

`routing_policy=None` disables the new scoping layer entirely, preserving any
existing global flags and producing identical physical actions. An explicit
policy, including two empty process lists, selects scoped mode: during each
`choose_machine` call the two original flags are enabled only for the listed
processes. The original weight dictionary identity and contents are restored in
`finally`, even if routing raises. No flag leaks to later scheduling decisions.
Only declared physical process names are accepted.

Initial assembly targets are chosen by whole-kit admission rather than
`choose_machine`. Consequently the ASSEMBLY scope mainly affects pumps returning
for rework; QA+ASSEMBLY is not a replacement for initial kit allocation.

## Predeclared bounded training comparison

The local campaign runs exactly160 measured episodes, with at most two workers:

- Loads12/16; full5760-minute horizon; TRAIN seeds0–7 only.
- ETA process sets: none, QA, QA+ASSEMBLY, T+F, all seven processes.
- Free-buffer process sets: none or QA.
- Hard portable-tool homes, whole-kit reservations, persistent family admission,
  worker calendars enabled and prepositioning disabled throughout.
- Load12 uses its measured routing prior, WIP8 and guard4. Load16 uses its own
  measured routing prior, WIP4 and guard0. All other weights stay fixed.

The prior is the training-only artifact from
`output/stage2-search/routing-coefficients-training/training-teacher.json`.
Its preprocessing/training costs and original source hashes are retained. A
later dispatch extension supports an explicit calendar-aware QUBO opt-in, but
this campaign fixes `selector=priority` and does not execute that branch. The
physical engine, numerical specification and checker must match the prior.

```sh
python -m stage2.routing \
  --teacher output/stage2-search/routing-coefficients-training/training-teacher.json \
  --output output/stage2-search/scoped-routing-training --workers 2
```

`--prepare-only` writes the complete task protocol and source snapshot without
executing episodes. Existing output directories are refused. Every actual run
receives the full independent checker; failures remain rows. Source changes
abort comparison rather than being mixed silently. The output retains protocol,
frozen source copies, all rows, aggregate results, costs and deterministically
selected seed0 traces for every variant. Invalid groups receive no valid-only
performance summary. Validation and reserved final tapes are not run.

Development tests establish default-off physical equivalence, process-specific
flag scoping and exception restoration, plus three full checked and paired-causal
tapes. Any reported improvement is a TRAIN result requiring later independent
selection/evaluation; regressions are retained with the same completeness metric.

## Completed bounded probe

All160 runs passed the independent checker. The campaign took213.82seconds wall
and389.22process CPU-seconds using two local workers. Frozen module SHA:
`2997cb4bd643bb0f46529a6591121ce11b95089dda37c37236fa14fe744bbe34`.
Raw evidence is in `output/stage2-search/scoped-routing-training/`; the paired
per-tape deltas and tail values are in `matched-comparisons.json`.

| Load | ETA scope; free-buffer filtering off | Shipped/required across8 TRAIN tapes | Complete tapes | Mean tardiness, min |
| --- | --- | --- | --- | --- |
|12|None|108/108|8/8|3432.50|
|12|QA|108/108|8/8|3167.75|
|12|T+F|108/108|8/8|3875.25|
|12|All|98/108|7/8|7025.63|
|16|None|110/140|0/8|15646.13|
|16|QA|111/140|0/8|14660.13|
|16|T+F|108/140|0/8|15345.25|
|16|All|107/140|0/8|14877.00|

QA+ASSEMBLY exactly matched QA on these tapes. The QA free-buffer filter reduced
the gains. Global ETA lost10 orders on load12/seed1 despite physical validity.
Physical validity alone does not establish order fulfillment.

The narrow QA result is mixed. At load12 its mean tardiness improves7.7%, but
empirical CVaR90 increases from5404 to6043minutes. For eight equally weighted
tapes this tail statistic equals the worst observed tape. At load16 it ships
one additional order overall, with improvements on two tapes and regressions on
two; mean cost increases from745.04 to777.81. Mean tardiness and its observed
tail both improve there. These are selection-sensitive TRAIN results, not a
generalization or robust dominance claim. No validation or final tapes were run.
