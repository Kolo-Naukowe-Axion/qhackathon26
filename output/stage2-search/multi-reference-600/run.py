"""Bounded local CPU driver over frozen reference_multi, with retained hints."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from stage2.reference_multi import solve
from stage2.check import check_trace

EXPECTED='226dced1939ee824a0e661d4112efc488be4de3286e6280e9da4e58163700efe'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--pumps',type=int,choices=(2,3,4),required=True)
 p.add_argument('--attendance',choices=('automatic','full','both'),default='both')
 p.add_argument('--wall-limit',type=float,default=600);p.add_argument('--deterministic-limit',type=float,default=600)
 p.add_argument('--incumbent-trace',type=Path,help='Optional checked witness for one attendance case, not serialized proof state')
 p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.incumbent_trace and a.attendance=='both':p.error('An explicit incumbent is for one attendance case only')
 if sha(ROOT/'stage2/reference_multi.py')!=EXPECTED:raise ValueError('Frozen reference source changed; obtain a new reviewed hash')
 a.output.mkdir(parents=True,exist_ok=False)
 names=('stage2/reference_multi.py','stage2/reference.py','stage2/check.py','stage2/engine.py')
 sources={name:sha(ROOT/name)for name in names}
 manifest=dict(schema='multi-reference-cpu-campaign.v1',pumps=a.pumps,attendance=a.attendance,
  source_sha256=sources,runner_sha256=sha(Path(__file__)),wall_limit_per_case=a.wall_limit,
  deterministic_limit_per_case=a.deterministic_limit,workers_per_case=1,
  fresh_search=True,resumed_cp_proof=False,scope='Matched-BOM deterministic tiny reference only',
  final_heldout_tapes_used=0,started_at=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
 write(a.output/'manifest.json',manifest);summaries=[]
 for attendance in (('automatic','full')if a.attendance=='both'else(a.attendance,)):
  if sha(ROOT/'stage2/reference_multi.py')!=EXPECTED:raise ValueError('Frozen reference source drifted between cases')
  suffix='-full'if attendance=='full'else''
  prior=ROOT/f'output/stage2-search/multi-reference-pilot/n{a.pumps}-scale15{suffix}'
  instance=json.loads((prior/'instance.json').read_text());previous=json.loads((prior/'report.json').read_text())
  heuristic=json.loads((prior/'heuristic-trace.json').read_text());heuristic_check=check_trace(heuristic)
  candidates=[(prior/'heuristic-trace.json',heuristic,heuristic_check)]
  for path in ([a.incumbent_trace]if a.incumbent_trace else [prior/'cp-trace.json']):
   if path and path.exists():
    trace=json.loads(path.read_text());checked=check_trace(trace)
    if trace['instance']!=instance or not checked['valid']or not checked['all_orders_fulfilled']or not checked['terminal_requirements_met']:
     raise ValueError('Incumbent must be physically valid, complete and on the identical instance')
    candidates.append((path,trace,checked))
  path,hint,checked=min(candidates,key=lambda row:max(row[2]['metrics']['delivery_ticks'].values()))
  destination=a.output/attendance;destination.mkdir()
  hint_record=dict(path=str(path),sha256=sha(path),makespan=max(checked['metrics']['delivery_ticks'].values()),
   declaration='Fresh solve with validated upper bound and complete warm-start hints; no CP proof state resumed')
  write(destination/'hint.json',hint_record);write(destination/'instance.json',instance)
  began=time.perf_counter()
  exact=solve(instance,wall_limit=a.wall_limit,deterministic_limit=a.deterministic_limit,workers=1,seed=0,incumbent=hint)
  artifacts={'heuristic-trace.json':heuristic}
  if 'trace'in exact:artifacts['cp-trace.json']=exact.pop('trace')
  if 'schedule'in exact:artifacts['cp-schedule.json']=exact.pop('schedule')
  for name,data in artifacts.items():write(destination/name,data)
  delivered=max(heuristic_check['metrics']['delivery_ticks'].values())
  same_tiers=bool(exact.get('validation',{}).get('valid')and abs(heuristic_check['metrics']['total_cost']-exact['validation']['metrics']['total_cost'])<1e-5)
  comparison=dict(heuristic_policy={'wip_limit':1,'mode':'standard'},heuristic_makespan_ticks=delivered,
   same_earlier_objective_tiers=same_tiers,cp_status=exact['status'],
   optimum_makespan_ticks=exact['objective_ticks']if exact['optimal']else None,
   heuristic_makespan_gap=(delivered/exact['objective_ticks']-1)if exact['optimal']and same_tiers else None,
   proved_lower_bound_ticks=exact['best_bound_ticks'],flagship_global_gap=None)
  report=dict(exact=exact,heuristic_validation=heuristic_check,comparison=comparison,hint=hint_record,
   artifacts_sha256={name:sha(destination/name)for name in artifacts},
   provenance=dict(source_sha256=sources,sources_stable_during_run=sources=={name:sha(ROOT/name)for name in names},
    prior_report_sha256=sha(prior/'report.json'),fresh_search=True,resumed_cp_proof=False))
  write(destination/'report.json',report)
  row=dict(pumps=a.pumps,attendance=attendance,status=exact['status'],objective=exact['objective_ticks'],
   bound=exact['best_bound_ticks'],valid=exact.get('validation',{}).get('valid'),
   heuristic=delivered,elapsed_seconds=time.perf_counter()-began,hint_makespan=hint_record['makespan'])
  summaries.append(row);write(a.output/'summary.json',summaries);print(json.dumps(row),flush=True)

if __name__=='__main__':main()
