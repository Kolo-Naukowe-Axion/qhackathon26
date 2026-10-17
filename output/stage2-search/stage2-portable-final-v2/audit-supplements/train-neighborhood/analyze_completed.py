"""Read-only integrity/summary supplement, no policy or factory execution."""
from collections import Counter
import gzip,hashlib,json
from pathlib import Path
import sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from stage2.check import check_trace
from stage2.spec import build
from stage2.quality_material_bound import certificate
analysis_started=time.perf_counter();analysis_cpu=time.process_time()

out=Path(__file__).resolve().parent
results=out/'results'
report=json.loads((results/'report.json').read_text());protocol=json.loads((results/'protocol.json').read_text())
raw=[json.loads(s) for s in (results/'rows.jsonl').read_text().splitlines()]
rows=[r for r in raw if r['phase']=='TRAIN-finite-neighborhood'];witnesses=[r for r in raw if r['phase']=='offline-oracle-witness']
assert sorted(rows,key=lambda r:r['task_id'])==report['rows']
assert witnesses==report['oracle_witnesses']
assert report['complete_checked_grid'] and report['witnesses_complete_valid'] and report['source_stable']
assert len(raw)==12208 and len(rows)==12184 and len(witnesses)==24 and len({r['task_id'] for r in rows})==12184
submission=json.loads((out/'submission-manifest.json').read_text());assert protocol['source_hashes']==submission['files']
assert hashlib.sha256((results/'selected-checkpoint.json').read_bytes()).hexdigest()==protocol['checkpoint_sha256']
for name,sha in protocol['source_hashes'].items():
 assert hashlib.sha256((results/'source_snapshot'/name).read_bytes()).hexdigest()==sha
 assert hashlib.sha256((Path(__file__).resolve().parents[3]/name).read_bytes()).hexdigest()==sha
seen=set()
for r in rows:
 key=(r['context_id'],r['variant_id'],r['config']['seed']);assert key not in seen;seen.add(key)
 t=protocol['tasks'][r['task_id']]
 assert all(r[k]==t[k] for k in ('context_id','variant_id','schedule','config','actor_seed','hamming_distance'))
 assert r['valid'] and r['identity_audit']['valid'] and r['decode_mismatches']==0
for c in protocol['contexts']:
 for v in c['variants']:
  for seed in range(8):assert (c['context_id'],v['variant_id'],seed) in seen
traces=[];independent_checks=[]
for r in rows+witnesses:
 if 'trace_path' not in r:continue
 p=results/Path(r['trace_path']).name;payload=gzip.decompress(p.read_bytes());assert hashlib.sha256(payload).hexdigest()==r['trace_sha256']
 t=json.loads(payload);assert t['metrics']==r['metrics']
 assert hashlib.sha256(json.dumps({k:t[k] for k in ('operations','moves','worker_moves','events','energy','metrics')},sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==r['physical_trace_sha256']
 assert hashlib.sha256(json.dumps(t['instance'],sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==r['physical_instance_sha256']
 fresh=build(**r['config']);checked=check_trace(t,fresh)
 assert checked['valid'] and checked['terminal_requirements_met']
 assert checked['metrics']['unfulfilled_orders']==r['metrics']['orders']-r['metrics']['shipped']
 assert checked['metrics']['terminal_deadline_debt_ticks']==r['metrics']['total_tardiness_ticks']
 assert abs(checked['metrics']['total_cost']-r['metrics']['total_cost'])<1e-5
 assert checked['provenance']['checker_sha256']==protocol['source_hashes']['stage2/check.py']
 independent_checks.append(dict(task_id=r['task_id'],phase=r['phase'],checked=checked))
 traces.append(dict(task_id=r['task_id'],phase=r['phase'],trace=str(p),trace_sha256=r['trace_sha256']))
assert len(traces)==27
summary=[]
for s in report['summary']:
 c=protocol['contexts'][s['context_id']];rs=[r for r in rows if r['context_id']==s['context_id']];by_seed={seed:[r for r in rs if r['config']['seed']==seed] for seed in range(8)}
 assert all(len({r['physical_instance_sha256'] for r in group})==1 for group in by_seed.values())
 for w in [r for r in witnesses if r['context_id']==s['context_id']]:
  assert w['valid'] and w['original_grid_metrics_match'] and w['original_grid_physical_trace_match']
  entry=next(t for t in s['per_tape'] if t['seed']==w['config']['seed'])
  assert entry['first_lexicographic_minimum_variant_id']==w['variant_id']
  candidates=[r for r in by_seed[w['config']['seed']] if [r['metrics']['orders']-r['metrics']['shipped'],r['metrics']['total_tardiness_ticks'],r['metrics']['total_cost']]==entry['lex_min']]
  assert w['schedule']==min(r['schedule'] for r in candidates)
 original=[r for r in rs if r['variant_id']==c['original_variant_id']]
 summary.append(dict(orders=s['orders'],horizon=c['config']['horizon'],variants=len(c['variants']),tapes=8,
  original_key=s['original_common_fixed_variant']['aggregate_key'],best_common_fixed_key=s['best_common_fixed_variant']['aggregate_key'],
  offline_per_tape_oracle_key=s['offline_per_tape_oracle_aggregate_key'],original_complete_tapes=sum(r['metrics']['all_orders_fulfilled'] for r in original),
  offline_oracle_complete_tapes=sum(t['lex_min'][0]==0 for t in s['per_tape']),
  per_tape=s['per_tape'],best_common_fixed_schedule=s['best_common_fixed_variant']['schedule'],
  physical_trajectory_flatness=dict(distinct=[t['distinct_physical_trajectories'] for t in s['per_tape']],
   metric_outcomes=[t['distinct_metric_outcomes'] for t in s['per_tape']],original_equivalent_variants=[t['original_physical_equivalent_variants'] for t in s['per_tape']],
   distinct_objective_triples=[len({(r['metrics']['orders']-r['metrics']['shipped'],r['metrics']['total_tardiness_ticks'],r['metrics']['total_cost']) for r in by_seed[seed]}) for seed in range(8)])) )
# Authorized post-seal offline necessary-bound supplement; never a controller input.
bound_started=time.perf_counter();bound_cpu=time.process_time();bounds=[]
assert hashlib.sha256((Path(__file__).resolve().parents[3]/'stage2/quality_material_bound.py').read_bytes()).hexdigest()=='c16698d81a2803df30c4b8d331904a14f45a375040ac9a3ca750b151e2e80236'
for c in protocol['contexts']:
 context_summary=next(x for x in report['summary'] if x['context_id']==c['context_id'])
 for seed in range(8):
  config=dict(c['config'],seed=seed);fresh=build(**config);bound=certificate(fresh)
  tape=next(t for t in context_summary['per_tape'] if t['seed']==seed)
  assert bound['instance_sha256']==tape['physical_instance_sha256']
  lower=bound['unfulfilled_lower_bound'];upper=tape['lex_min'][0];assert lower<=upper
  bounds.append(dict(context_id=c['context_id'],config=config,necessary_missing_lower_bound=lower,
   finite_neighborhood_witness_missing_upper_bound=upper,primary_interval_width=upper-lower,
   primary_optimum_certified=lower==upper,witness_task_id=tape['witness_task_id'],certificate=bound))
necessary=dict(scope='Post-seal supplementary offline hidden-tape proof; no controller feature, selection or original final performance',
 report_sha256=hashlib.sha256((results/'report.json').read_bytes()).hexdigest(),rows=bounds,
 wall_seconds=time.perf_counter()-bound_started,cpu_seconds=time.process_time()-bound_cpu,
 primary_only=True,secondary_gap=None)
(out/'necessary-bound-supplement.json').write_text(json.dumps(necessary,indent=2)+'\n')
for s in summary:
 b=[b for b in bounds if b['config']['orders']==s['orders']]
 s['necessary_bound_summary']=dict(sum_missing_lower_bound=sum(x['necessary_missing_lower_bound'] for x in b),
  sum_witness_upper_bound=sum(x['finite_neighborhood_witness_missing_upper_bound'] for x in b),
  primary_certified_tapes=sum(x['primary_optimum_certified'] for x in b),
  positive_primary_certified_tapes=sum(x['primary_optimum_certified'] and x['necessary_missing_lower_bound']>0 for x in b),
  interpretation='Global primary interval from existing necessary relaxation and checked finite-class witness; positive finite-class min alone is not infeasibility')
result=dict(scope='Read-only complete TRAIN0–7 offline fixed-neighborhood oracle, not selected policy, validation or final',
 report_sha256=hashlib.sha256((results/'report.json').read_bytes()).hexdigest(),analysis_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 all_rows_match_report=True,all_declared_variants_present=True,source_snapshot_matches_manifest=True,retained_trace_hashes_match=True,
 raw_rows=len(raw),grid_rows=len(rows),oracle_replays=len(witnesses),retained_traces=traces,summary=summary,
 wall_seconds=report['wall_seconds'],worker_cpu_seconds=report['cpu_seconds'],
 independent_retained_trace_checks=independent_checks,analysis_wall_seconds=time.perf_counter()-analysis_started,analysis_cpu_seconds=time.process_time()-analysis_cpu)
(out/'retention-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('retained_traces','summary','independent_retained_trace_checks')},indent=2))
for s in summary:print(json.dumps({k:v for k,v in s.items() if k not in ('per_tape',)}))
