# Portable-tool homes: throughput and failure evidence

`stage2/tooling.py` adds a causal tool-assignment heuristic over the unchanged
physical factory. Portable tools retain their mobility, life, service needs and
physical eligibility. The policy changes which legal assignments it considers;
it does not mount tools, teleport inventory or remove transport/service checks.

The default home map is:

| Tool | Preferred station |
|---|---|
| mill1 | F1 |
| mill2 | F2 |
| weld1 | S1 |
| weld2 | S2 |
| calibration1 | QA1 |
| paid calibration rental | QA2 |

The motivation was an observed imbalance: one mill moved 32 times while its peer
moved only 3. Preparation could repeatedly borrow an idle tool from another
station, delaying work at that station. The experiment tests a concrete remedy
rather than assuming that every tool relocation is useful.

## Policies and physical scope

`mode="off"` reproduces the existing `AdvancedFactory` physical action lists and
metrics. `mode="soft"` prefers a locally available or home tool and protects a
foreign tool when its home already has admitted input or an incoming reserved
part. It can borrow when that demand is absent. Existing deliveries reserved for
a particular part remain honored.

`mode="hard"` considers tools assigned to the current station and restricts
part routing to stations with a home tool. Under the default mill map this
leaves F3 unused by this particular algorithm. F3 remains physically eligible in
the underlying instance. This is an explicit heuristic restriction that can lose
the unrestricted optimum; full-factory global gap remains unknown. Hard homes
are not claimed to be without loss of generality.

A paid rental can receive queued work before its known delivery, but processing
cannot use the resource until it actually arrives. Tool transport remains an
AGV movement with the existing path, capacity and SOC constraints. Service still
occurs at the tool's actual location. Worker calendars/skills, setup, blocking,
power, quality and material rules stay in the physical engine and are verified
by the independent replay checker.

The implementation temporarily narrows the tool candidate dictionary during a
process decision and restores the complete dictionary in a `finally` block.
Hard routing uses the same restoration discipline for candidate machines. These
are candidate views of the same resource objects; committed state changes and
moves persist. Asynchronous completions always see the full dictionaries. No
physical resource attributes are overwritten. In-flight preparations remain in
the view so the original duplicate-preparation guard still applies.

`ToolingFactory` combines this policy with `AdvancedFactory`.
`ToolingSpecialistFactory` also combines the existing QA-worker guard. The latter
is an experimental combination; its results below show adverse interactions.
`tool_policy` supports a kind subset and an explicit alternative `homes` map for
subsequent controlled studies. Static home choices are fixed for a run.

## API and frozen sources

```python
from stage2.tooling import run
trace = run(instance, weights, controller=None,
            tool_policy={"mode": "hard"}, specialist=False)
```

The full default tool policy is mode soft, all three tool kinds, optional soft
routing disabled and home penalty 12. Selecting mode hard uses the map above and
its station eligibility restriction. Exact selected weights and the complete
home map are saved in `output/stage2-search/tooling-selection/selection.json`.

The source is frozen at SHA256
`8117e6039c103c723bf50996bec5c789d639f287e0284797525164a1da01f316`.
Physical engine/specification/checker and existing advanced/specialist sources
were not edited. Twelve focused tests cover off equivalence, home pressure,
borrowing, in-flight and reserved delivery handling, dictionary restoration on
exceptions, physical portability, rental birth, kind isolation and full paired
trace replay. The combined owned test suite passes 112 tests.

## Development protocol

The initial pilot used TRAIN 0–3, WIP4, standard mode, a rental, calendar filling
and 10-minute early empty dispatch. All 40 runs passed the physical and empirical
prefix checks. At 8 initial orders the no-home policy shipped 36 of 38 actual
orders; soft/all and hard/all each shipped 38. At 12 initial orders the counts were
42/54 without homes, 47/54 soft/all and 46/54 hard/all. Both accepted-peer/tool
choices and transport changed as actual legal scheduling decisions.

The stronger comparison then reused the saved TRAIN-only routing teacher:
`output/stage2-search/routing-coefficients-training/training-teacher.json`.
Its existing 6144 base-policy plus 640 routing-grid episodes are reused prior
training, not new tooling computation. Each context used its recorded static
weights. Calendar filling was enabled and early empty dispatch disabled, matching
the stronger calendar control requested for this comparison. The n10 case used
the n12 prior nominated by the existing frontier development study.

TRAIN 0–31 compared no homes, soft/all and hard/all. A baseline Factory comparator
was also included for n8/n12. After hard homes improved the training results,
only no-home and hard-home policies advanced to VALIDATION 100–115. Soft homes
were rejected. Final seeds 10000+ were never accessed; the development CLI rejects
that range. These validation tapes are used for selection and are not independent
final-test evidence.

Seven reports retain all 616 development executions, full compressed traces,
per-run objectives/tool usage, source snapshots and hashes. Every execution
passed physical replay and terminal requirements; all policy groups passed the
empirical paired reveal-prefix audit. Source hashes were stable within every
batch. The prefix audit is not a general nonanticipativity proof.

## Strong-prior training results

Each row aggregates 32 actual tapes. Demand is 296 for n8, 360 for n10 and 424 for
n12, including revealed urgent orders. Horizon tardiness includes unfinished
orders' debt at the final horizon.

| Context | No-home shipped | Hard-home shipped | No-home complete tapes | Hard-home complete tapes | No-home tardiness | Hard-home tardiness |
|---|---:|---:|---:|---:|---:|---:|
| n8, calendar | 296/296 | 296/296 | 32/32 | 32/32 | 23846 | 5309 |
| n12, calendar | 392/424 | 409/424 | 17/32 | 26/32 | 239129 | 180414 |
| n10, prior12, QA guard2 | 345/360 | 357/360 | 30/32 | 31/32 | 134284 | 90642 |
| n12, QA guard4 | 388/424 | 409/424 | 18/32 | 26/32 | 222032 | 169087 |

For context, the unchanged baseline Factory produced 364/424 orders and 14/32
complete tapes at n12 with the same production prior. Calendar filling therefore
already improves this control before tool homes are added.

**Negative evidence:** soft homes regress sharply under these stronger, higher
WIP priors. They ship 220/424 at n12/calendar, 107/360 at n10/guard2 and 238/424 at
n12/guard4. Their favorable weak-prior pilot does not transfer. All these poor
partial traces are retained and remain physically valid. The experiment does not
claim to prove the mechanism of every deadlock.

## Validation and selected candidate

Each row below aggregates 16 validation tapes. Demand is 146 for n8, 178 for n10
and 210 for n12.

| Context | No-home shipped | Hard-home shipped | No-home complete tapes | Hard-home complete tapes | No-home tardiness | Hard-home tardiness |
|---|---:|---:|---:|---:|---:|---:|
| n8, calendar | 146/146 | 146/146 | 16/16 | 16/16 | 7704 | 2333 |
| n12, calendar | 191/210 | 208/210 | 8/16 | 14/16 | 123284 | 81161 |
| n10, prior12, QA guard2 | 178/178 | 173/178 | 16/16 | 15/16 | 55361 | 53918 |
| n12, QA guard4 | 196/210 | 185/210 | 9/16 | 11/16 | 104045 | 118792 |

The n12/calendar hard-home candidate reduces mean missing orders from 1.1875 to
0.125 and completes 14/16 tapes, while retaining the same full physical problem.
Its two remaining misses are urgent order U02 on seed 107 and U01 on seed 115;
neither was scrapped. This leaves further scheduling opportunity rather than
establishing an intrinsic quality impossibility or a global optimum.

The n12 candidate uses WIP8, standard mode, due weight 0.25, remaining weight −4,
family weight 24, setup weight 10, tool-distance weight 0, a calibration rental,
calendar filling, early empty dispatch disabled, and **no QA guard**. The exact
weights, backend settings and all 16 witness paths are in `selection.json`.

The guarded interactions must not be hidden: hard homes hurt n10's previously
perfect validation completion, and n12/guard4 loses shipments even though its
number of fully completed tapes rises. Full-tape rate alone would conceal those
bad partial cases. The selected n12 configuration uses no QA guard, and n10's
existing no-home guarded controller remains preferable on these development
results. A sealed final comparison is still required.

## Reports and reproduction

- `tooling-pilot-train/report.json`: 40 pilot runs.
- `tooling-routing-train32/report.json`: 256 stronger-prior runs.
- `tooling-guard2-n10-train32/report.json`: 96 targeted guarded runs.
- `tooling-guard4-n12-train32/report.json`: 96 targeted guarded runs.
- `tooling-routing-validation16/report.json`: 64 validation runs.
- `tooling-guard2-n10-validation16/report.json`: 32 validation runs.
- `tooling-guard4-n12-validation16/report.json`: 32 validation runs.

All directories are under `output/stage2-search/`. Batch elapsed times are saved
individually; several batches overlap, so summing their wall times is not an
end-to-end runtime measurement. Work used local CPU processes only. No GPU,
quantum hardware, VPN or cluster connection was used for this tooling study.

```sh
.venv-stage2/bin/python -m stage2.tooling \
  --orders 8 12 --seeds 100 101 102 103 104 105 106 107 \
  108 109 110 111 112 113 114 115 --workers 2 \
  --variants off hard-all --no-preposition \
  --teacher output/stage2-search/routing-coefficients-training/training-teacher.json \
  --output output/stage2-search/tooling-routing-validation16
```

`tooling-selection/showcase-train0-n12-hard.json` is an uncompressed checked trace
from the first training tape for visualization. It is a deterministic example,
not a selectively chosen final-evaluation success. Existing physical portability
and unused capacity remain visible in that trace.
