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

Use Python 3.11 for the SDK checks, separately from the Python 3.12+ catering
foundation environment. The commands below use one environment consistently;
the retained SDK checks used NumPy 2.4.6, dimod 0.12.22, VeloxQ SDK 1.0.0 and
pytest 9.1.1. These tests use no token and submit no jobs.

```sh
python3.11 -m venv .venv-veloxq
.venv-veloxq/bin/python -m pip install -r requirements-solver.txt pytest==9.1.1
.venv-veloxq/bin/python -m pytest tests/catering/test_conditioning.py tests/catering/test_veloxq_adapter.py tests/catering/test_veloxq_penalty.py -q
.venv-veloxq/bin/python -m catering.tune_veloxq --output output/NEW-CONDITIONING
.venv-veloxq/bin/python -m catering.veloxq_pilot --output output/NEW-OFFLINE-PILOT
```

The full release checker also requires Node.js 20+ and npm for the site build;
the Python-only SDK tests above do not. Run that checker in the foundation
environment using [the catering guide](../catering/README.md#verify-without-training).

Historical `job_ledger.json` entries retain the submitting machine's absolute
`output_dir` as provenance. The submission cap counts entries, without opening
those old directories. On another machine, locate retained artifacts beneath
the repository's `output/` tree; do not try to recreate `/home/raf`.

Restoration tools have separate scopes: `restore-compressed-evidence.mjs`
verifies/restores the indexed JSON evidence; `restore_veloxq_evidence.py` handles
the original VeloxQ subtree and its HDF5 gzip files; `restore-large-evidence.py`
only verifies/copies downloaded historical release assets. The latter does not
download or extract a complete project environment. Restoring every historical
factory archive is unnecessary for the catering release checks and substantially
increases disk usage.

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
.venv-veloxq/bin/python -m catering.veloxq_pilot \
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
.venv-veloxq/bin/python -m catering.veloxq_pilot \
  --output output/NEW-NOIDLE --formulation no-idle --num-steps 20000
# --allow-external and a suitable --max-service-jobs are still required to submit.
.venv-veloxq/bin/python -m catering.veloxq_pilot --output output/EXISTING-JOB --resume
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


## Scaling and classical context

The following three jobs share cold initialization, 20,000 steps and 512
replicas. Counts include sample multiplicity. **Non-empty** means at least one
new batch selected; it does not imply a complete meal delivered. Empty plans are
feasible, so validity alone is insufficient.

| Source / solver bits | Valid | Non-empty | Best U | Backend s | Adapter + recovery s | SA best U | CP best U (5 s cap) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 512 / 486 | 512/512 | 143/512 | 9 | 1.663 | 7.399 | 7 | 7 |
| 1,024 / 998 | 512/512 | 102/512 | 11 | 5.442 | 15.813 | 8 | 8 |
| 2,048 / 2,022 | 512/512 | 62/512 | 13 | 19.229 | 32.757 | 11 | No incumbent |

Lower U is better; U counts missed priority-weighted complete meal lots, each
of ten meals. These cases have equal priorities. The 100,000-step width-486 job
is a separate deeper run and is excluded from this equal-step table.

Backend time is the service's reported `running_time`, not an end-to-end speed
claim. Adapter time includes the failed download attempt plus measured recovery
where needed, excluding the unmeasured gap between attempts. SA uses the same
no-idle matrix, three seeds and a two-second search cap per seed (four restarts,
100 sweeps); its whole calls range from 0.871–1.377, 2.037–2.048 and 2.150–2.213 s
at the three widths. CP uses the identical offered programs with hard constraints
and the original objective, rather than the penalized sampling matrix. The
retained five-second CP calls took 5.009/5.040/5.415 s including construction;
the last returned UNKNOWN. These differ in compute, budgets and initialization
and are context, not a controlled solver speed ranking.

Sources: [service report](../output/catering-velox-conditioned-service-v1/report.json),
[SA report](../output/catering-velox-noidle-controls-v1/report.json), and the
[512](../output/catering-velox-scale-v3/scale-512-reference.json),
[1,024](../output/catering-velox-scale-v3/scale-1024-reference.json) and
[2,048](../output/catering-velox-scale-v3/scale-2048-reference.json) CP receipts.
The earlier 30-second CP incumbents mentioned above are separate runs.


## Hybrid follow-up (18 October): VeloxQ on a classical plan

Question: can VeloxQ improve a classical plan instead of searching from
scratch? Five capped jobs (ledger 61→66 of an authorized 70) test two
workflows on the 30-second CP plans. All returned rows are checked by the same
decoder; no repair. Neighbourhoods were chosen offline by exact enumeration,
which already knew an improvement existed, so this measures whether VeloxQ
finds it, not neighbourhood selection.

**Whole-matrix warm start (width 486).** `--initializer incumbent` repeats the
checked CP plan (U=6) in all 512 starting rows. VeloxQ does not keep or polish
it: at 20,000 steps the best return is U=9 and 376/512 rows are empty plans,
as without a start. After only 10 steps no row equals the start and 413/512 are
already empty. The start is serialized and accepted, but the dynamics leave it.

**Large-neighbourhood step (width 2,022).** `catering.velox_lns` keeps the plan
outside two freed one-hot blocks and sends only the exact sub-QUBO (its energy
equals the full sampling energy for every freed assignment, tested). Exact
enumeration of none-or-one program per freed block certifies the sub-optimum.

| Step | Sub-QUBO bits / couplers | Steps | Start (U,W,B,R) | Exact sub-optimum | VeloxQ best (shots) | Backend s |
|---|---:|---:|---|---|---|---:|
| 1, blocks 15+16 | 162 / 11,249 | 20,000 | (8,3,8,8) | (7,3,9,9) | **(7,4,9,9)** (25/512) | 2.0 |
| 2, blocks 4+25 | 207 | 20,000 | (7,4,9,9) | (6,5,10,10) | (7,4,9,9) (239/512) | 1.4 |
| 2, blocks 4+25 | 207 | 100,000 | (7,4,9,9) | (6,5,10,10) | (7,4,9,9) (289/512) | 4.8 |

Step 1 serves one more meal lot than the CP plan it started from; the full
2,048-source plan is independently valid. It is not the exact sub-optimum
(one more discarded component lot, or ten portions). Step 2 needs a coordinated three-bit change, as
step 1 did, but VeloxQ returns the unchanged plan even with five times more
steps. Both moves have no improving single flip.

Context, not a race: exact enumeration of these neighbourhoods takes seconds
on a laptop, and CP with 240 s and four workers reaches U=5/5/6 at the three
widths ([controls](../output/catering-velox-warmstart-v1/controls/)). The
insight is where VeloxQ fits: as a solver for a small, exactly checkable
sub-QUBO inside a classical loop it can improve a plan; as a polisher of a
whole plan it currently cannot. [Study report](../output/catering-velox-warmstart-v1/report.json).
