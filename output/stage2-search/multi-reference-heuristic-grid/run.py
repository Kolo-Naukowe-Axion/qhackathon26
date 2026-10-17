"""Development-only deterministic priority grid; all witnesses gzip-retained."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from stage2.engine import run
from stage2.check import check_trace

OUT=Path(__file__).resolve().parent
names=('stage2/engine.py','stage2/check.py','stage2/reference_multi.py')
hashes=lambda:{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()for name in names}
before=hashes();rows=[]
for n in (2,3,4):
 for attendance in ('automatic','full'):
  suffix='-full'if attendance=='full'else''
  prior=ROOT/f'output/stage2-search/multi-reference-pilot/n{n}-scale15{suffix}'
  instance=json.loads((prior/'instance.json').read_text())
  for wip in range(1,n+1):
   for remaining in (-4,0,4):
    weights=dict(wip_limit=wip,mode='standard',remaining=remaining)
    started=time.perf_counter();trace=run(instance,weights);checked=check_trace(trace)
    trace['validation']=checked
    directory=OUT/f'n{n}-{attendance}-w{wip}-r{remaining}';directory.mkdir(exist_ok=False)
    raw=json.dumps(trace,separators=(',',':')).encode()
    with gzip.open(directory/'trace.json.gz','wb')as handle:handle.write(raw)
    row=dict(pumps=n,attendance=attendance,weights=weights,valid=checked['valid'],
     complete=checked['all_orders_fulfilled'],unfulfilled=checked['metrics']['unfulfilled_orders'],
     makespan=max(checked['metrics']['delivery_ticks'].values(),default=None)if checked['all_orders_fulfilled']else None,
     cost=checked['metrics']['total_cost'],elapsed_seconds=time.perf_counter()-started,
     trace_sha256=hashlib.sha256(raw).hexdigest(),path=str(directory/'trace.json.gz'))
    rows.append(row);(directory/'summary.json').write_text(json.dumps(row,indent=2)+'\n')
best=[]
for n in (2,3,4):
 for attendance in ('automatic','full'):
  feasible=[row for row in rows if row['pumps']==n and row['attendance']==attendance and row['valid']and row['complete']]
  best.append(min(feasible,key=lambda row:(row['makespan'],row['weights']['wip_limit'],row['weights']['remaining'])))
report=dict(schema='tiny-multi-heuristic-development-grid.v1',selection_role='Development on these same deterministic fixtures; no generalization claim',
 candidates=rows,best_complete=best,source_sha256=before,sources_stable_during_run=before==hashes(),
 final_heldout_tapes_used=0,disclosure='A comparator-strength check; incomplete/invalid cases retained, not averaged away')
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(cases=len(rows),invalid=sum(not row['valid']for row in rows),incomplete=sum(not row['complete']for row in rows),best=best),indent=2))
