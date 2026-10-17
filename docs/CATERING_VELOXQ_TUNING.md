# VeloxQ recovery: condition the penalties before spending more quota

17 October 2026. The original owner inputs and prior service receipts remain
unchanged. This is an additional solver-side representation of the same offered
kitchen choices. It changes invalid-state energies and receives a separate hash;
it is not an identical-matrix comparison with the original cold runs.

## Diagnosis

The first scale runs used 512 replicas and 2,000 steps, cold start. Of 512 returns,
5, 1 and 0 were valid at widths 512, 1,024 and 2,048. Those observations establish
an unsuccessful initial configuration, not the solver's best performance.
The original proof used the sum of all absolute objective coefficients to set P.
A valid but much tighter deletion bound avoids summing the entire graph.

## A strict proof of the smaller penalty

Write the unchanged objective as

    F(x) = c + sum_i a_i x_i + sum_{i<j} b_ij x_i x_j.
    D_i = max(0,-a_i) + sum_{j != i} max(0,-b_ij).
    P = 1 + max_i D_i.
    E = F + P sum_g (sum_{i in g} x_i - 1)^2
          + P sum_{(i,j) in conflicts} x_i x_j.

Deleting selected program i can increase F by at most D_i, on any binary
assignment. Each anchor block has exactly one idle bit; that bit has no objective
terms and no conflicts. Blocks partition all variables. Conflicts join program
bits from different blocks. Under precisely these checked assumptions:

1. Fill any empty block with idle. The objective stays fixed and E falls by P.
2. For an overfull block, delete a selected bit. Its squared penalty falls by at
   least P, other conflict penalties cannot rise, and objective loss is at most
   D_i < P. Repeat until each block has one choice, filling empty blocks if needed.
3. If two remaining selected programs conflict, replace either with its own
   block's idle. One-hot penalties stay zero, at least one conflict penalty
   disappears, and objective loss is at most D_i < P.

Every infeasible assignment therefore has a strictly improving finite path to a
feasible assignment. Every global ground state is feasible, and feasible costs
are exactly F, so the original and conditioned matrices have precisely the same
optimal schedules and literal feasible energies. This proves neither that a
heuristic reaches a ground state nor that single-bit dynamics improve: step 3
can require a two-bit swap. No repair path is applied to returned samples.

The compiler rejects unproven structures and reconstructs the entire original
polynomial before transforming it, so hidden extra terms cannot be dropped.

| Variables | Original P | New proven P | Reduction |
|---:|---:|---:|---:|
| 512 | 443,079,397 | 3,510,865 | 126.2x |
| 1,024 | 1,897,074,756 | 6,695,137 | 283.4x |
| 2,048 | 7,710,553,294 | 12,002,257 | 642.4x |

No deadlines, menus, options, bit order, weights, objective or physical rules
change. Existing QAOA/VQE/VeloxQ results remain valid on their original inputs.
Nobody needs to rerun their work to accommodate this experiment. Any new
conditioned runs must identify their own matrix and controls explicitly.

## Reproduce locally

```sh
.venv/bin/python -m pytest tests/catering/test_conditioning.py tests/catering/test_veloxq_adapter.py -q
.venv-stage2/bin/python -m catering.tune_veloxq --output output/NEW-CONDITIONING
.venv/bin/python -m catering.veloxq_pilot --output output/NEW-OFFLINE-PILOT
```

The ablation predeclares three seeds per tier, original vs conditioned SA,
four restarts, 100 sweeps, two seconds per search. All returns are retained,
re-scored against the original frozen matrix and independently decoded. Source
snapshots, hashes, build time, search time and whole-call time are retained.
`output/catering-velox-conditioning-v2/` is the authoritative local ablation;
v1 was an exploratory development pass and is not the release receipt.
A local SA result cannot stand in for a VeloxQ measurement.

## One service job at a time

`catering.veloxq_pilot` defaults to no external execution. It can read an existing
VELOX_TOKEN or the ignored local `.env.velox-local`. It never prints the key.
The local ledger initially contained four attempts. While this follow-up ran,
a teammate pushed a 54-attempt ledger; integration takes the union, preserving
all 61 attempts (54 prior-owner plus seven new jobs here). Maximum jobs is the
reconciled ledger total, not additional calls. No further service calls are planned
by this pass.

```sh
# Example after the 61-entry reconciliation; check current usage before submitting:
.venv/bin/python -m catering.veloxq_pilot \
  --output output/NEW-CONDITIONED-512 --allow-external --max-service-jobs 62
```

First isolate the penalty change at the original 512/2,000 settings on width512.
Inspect validity and best checked tuple before escalating. A separately labeled
all-idle warm start is implemented through the SDK's Spectrum data, with num_rep
identical SPIN rows and checked variable order. Its backend acceptance and benefit
must be measured; successful serialization alone does not establish either.
Use `--initializer all-idle` for that separate ablation. Compare against idle and
give the same initializer to classical controls. A supplied CP optimum must not
be misrepresented as improvement found by VeloxQ.

Preserve raw service packets, responses, statistics and failures. Wrapper result
samples retain both sampling_energy and the original frozen reported_energy.
No invalid rows disappear, no repairs or CP fallback enter the service result.
SDK source: https://github.com/quantumz-io/veloxq_sdk (installed 1.0.0 inspected).

## Removing redundant idle variables

A second equivalent formulation removes each idle variable. Let G contain all
original cross-block conflicts and all pairs of programs sharing an anchor.
Use the unchanged program-only objective and

    E_noidle(x) = F(x) + P sum_{(i,j) in G} x_i x_j.

Every invalid assignment selects an exclusion edge. Deleting either endpoint
removes at least P of penalty and increases F by at most D_i < P. Every ground
state is therefore an independent set of G. Such a state has at most one program
per anchor; fill each empty anchor with its idle to obtain the unique original
feasible assignment. This is a bijection on feasible schedules with identical
objective values. All program bits survive unchanged, including in invalid
returns. The adapter only reconstructs their redundant idle choices before the
original checker; it never removes a selected program.

Source widths 512/1,024/2,048 become actual service widths 486/998/2,022. Both
counts must be shown. Extra tests exhaust every reduced state and every original
state in twenty independently weighted tiny models, checking strict descent,
feasible-set bijection, energies and ground states.

The SDK download path sometimes reset its TLS connection after the backend had
completed. Results were recovered by saved job ID without submitting again.
The adapter now retrieves the signed storage URL through the authenticated API,
then downloads with a fresh storage client carrying no VeloxQ authentication
header. The first failed adapter receipts remain intact alongside recovered
results. Recovery time must be added to the failed attempt's wall time; its
original total_s alone is not a successful end-to-end measurement.

Run the second formulation explicitly:

```sh
.venv/bin/python -m catering.veloxq_pilot \
  --output output/NEW-NOIDLE --formulation no-idle --num-steps 20000
# --allow-external and a suitable --max-service-jobs are still required to submit.
.venv/bin/python -m catering.veloxq_pilot --output output/EXISTING-JOB --resume
```

--resume downloads an existing saved job only. It submits zero additional jobs.

## Measured follow-up

All seven exploratory submissions are retained in
`output/catering-velox-conditioned-service-v1/`. They consumed 36,640 reported
quota units and reported total_cost=0.0. Three completed jobs needed a separate
download recovery; those did not create additional solver jobs. The account was
checked before execution: balance USD0, hackathon quota group, approximately
1.998 billion remaining units. This is not a statement about quota units equaling
credits or minutes.

All rows use 512 returned samples. Steps are shown because the changes are not
all isolated to one lever; these are exploratory results, not a held-out study.

| Source / actual solver bits | Representation | Steps | Valid rows | Best (U,W,B,R) |
|---|---|---:|---:|---|
| 512 / 512 | deletion-bound, cold | 2,000 | 8/512 | (13,4,4,4) |
| 512 / 512 | deletion-bound, idle start | 2,000 | 8/512 | (13,7,5,5) |
| 512 / 512 | deletion-bound, cold | 20,000 | 17/512 | (13,3,3,3) |
| 512 / 486 | no-idle, cold | 20,000 | 512/512 | (9,6,9,9) |
| 512 / 486 | no-idle, cold | 100,000 | 512/512 | (8,7,12,12) |
| 1,024 / 998 | no-idle, cold | 20,000 | 512/512 | (11,6,10,10) |
| 2,048 / 2,022 | no-idle, cold | 20,000 | 512/512 | (13,3,2,2) |

The no-idle representation produced valid schedules at all three scales. The
source-width512 comparison at equal 20,000 steps isolates its benefit relative
to deletion-bound alone. The same-formulation local SA control, three seeds,
four restarts x100 sweeps and two-second search caps, is retained in
`output/catering-velox-noidle-controls-v1/`: best U=7/8/11 across the three source
widths. Those budgets and hardware differ from VeloxQ. The older 30-second CP
incumbents attain U=6/7/8. Thus feasibility is substantially improved but VeloxQ
has not won the scheduling-quality comparison. No result is repaired or replaced
by a classical incumbent in the raw VeloxQ record.
