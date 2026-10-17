"""Read-only CP result interpretation and explicit in-memory witness-copy audit."""
from copy import deepcopy
from fractions import Fraction
import hashlib,json,time
from pathlib import Path
from stage2.check import check_trace
from stage2.identity_audit import audit_trace
from stage2.reference_multi import validate_scope

ROOT=Path.cwd();B=ROOT/'output/stage2-search/multi-reference-2h-axion';RUN=B/'completed/multi-reference-2h-20261017T0116';OUT=Path(__file__).resolve().parent
start=time.perf_counter();cpu=time.process_time()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
r=json.loads((RUN/'result/report.json').read_text());i=json.loads((RUN/'instance.json').read_text());t=json.loads((RUN/'result/cp-trace.json').read_text());x=r['exact'];validate_scope(i)
assert sha(RUN/'result/report.json')=='9ceba65416fbe4376e5ad84baeec144042a7fd61a9a396949deeb7310184c0cd'
assert digest(i)==r['instance_sha256']=='3c6bda8bbf315951447394c68053894ff4a756be1c63f826de7c58739b5c3f7e' and t['instance']==i
for n,h in r['payload_hashes'].items():
 assert sha(RUN/n)==h and sha(B/'payload'/n)==h
 if n.startswith('stage2/'):assert sha(ROOT/n)==h
for n,h in r['artifact_hashes'].items():assert sha(RUN/'result'/n)==h
assert r['sources_stable_during_run'] and r['fresh_search'] and not r['cp_proof_resumed'] and r['final_tapes_used']==0
assert x['status']=='FEASIBLE' and x['optimal'] is False and x['objective_ticks']==1541 and x['best_bound_ticks']==1524
assert x['incumbent']['makespan']==1567 and x['incumbent']['scope']=='Validated upper bound and warm-start hints; no choices fixed'
raw_core=check_trace(t,deepcopy(i));raw_identity=audit_trace(t,i)
assert raw_core['valid'] and raw_core['all_orders_fulfilled'] and raw_core['terminal_requirements_met'] and not raw_identity['valid']
assert len(raw_identity['issues'])==1
issue=raw_identity['issues'][0];assert issue['code']=='unit_before_identity_birth' and issue['field']=='part_move' and issue['unit_id']=='P04/pump/1'
idx=next(j for j,m in enumerate(t['moves']) if m['id']=='move74');m=t['moves'][idx];op=next(o for o in t['operations'] if o['id']=='P04/pump/1/op0');previous=t['moves'][idx-1]
assert m['start']==1382 and m['pickup_tick']==1480 and op['start']==1420 and op['end']==1480
assert previous['id']=='move62' and previous['end']==1381 and previous['to']==m['from']=='A1'
assert m['legs'] and min(z['start'] for z in m['legs'])==1481 and all(z['loaded'] for z in m['legs'])
copy=deepcopy(t);copy['moves'][idx]['start']=op['start']
def differences(a,b,path=()):
 if type(a)!=type(b):return [path]
 if isinstance(a,dict):
  assert set(a)==set(b);return [z for k in a for z in differences(a[k],b[k],path+(k,))]
 if isinstance(a,list):
  assert len(a)==len(b);return [z for j,(c,d) in enumerate(zip(a,b)) for z in differences(c,d,path+(j,))]
 return [] if a==b else [path]
diff=differences(t,copy);assert diff==[('moves',idx,'start')]
normalized_core=check_trace(copy,deepcopy(i));normalized_identity=audit_trace(copy,i)
assert normalized_core['valid'] and normalized_core['all_orders_fulfilled'] and normalized_core['terminal_requirements_met'] and normalized_identity['valid']
assert raw_core['metrics']==normalized_core['metrics'] and max(normalized_core['metrics']['delivery_ticks'].values())==1541
heur=json.loads((ROOT/'output/stage2-search/multi-reference-heuristic-grid/report.json').read_text());h=next(v for v in heur['best_complete'] if v['pumps']==4 and v['attendance']=='automatic');assert h['valid'] and h['complete'] and h['makespan']==2482
lines=(ROOT/'output/stage2-search/accounting-20261017-0316.txt').read_text().splitlines();row=next(l.split('|') for l in lines if l.startswith('6117555|'));assert row[3]=='COMPLETED' and row[4]=='7174' and row[5]=='16'
result=dict(valid=True,scope='Supplementary deterministic reference interpretation,not new factory/solver/performance sample',source_sha256=sha(__file__),input_report_sha256=sha(RUN/'result/report.json'),input_trace_sha256=sha(RUN/'result/cp-trace.json'),canonical_instance_sha256=digest(i),frozen_payload_sources_match=True,status='FEASIBLE',optimal=False,cp_lower_bound=1524,constructive_witness_upper_bound=1541,optimum_interval=[1524,1541],interval_width_minutes=17,actual_optimality_gap_unknown=True,incumbent_improvement_minutes=26,incumbent_improvement_percent=float(Fraction(26,1567)*100),heuristic2482_excess_gap_interval_percent=[float((Fraction(2482,1541)-1)*100),float((Fraction(2482,1524)-1)*100)],
 raw_physical_check=raw_core,raw_stock_identity=raw_identity,
 explicit_in_memory_witness_copy=dict(only_difference=list(diff[0]),old_start=1382,new_start=1420,source_assembly_birth=1420,source_assembly_completion=1480,pickup=1480,first_loaded_leg=1481,previous_move_end=1381,previous_move_destination='A1',trace_metrics_field_remains_empty_dict=True,recomputed_checker_metrics_exactly_equal=True,physical_check=normalized_core,stock_identity=normalized_identity,physical_core_checks_always_original_or_explicitly_labeled_copy=True),
 lower_bound_scope='Original CP allows early future-identity dispatch booking; its1524lower bound also holds for stricter birth-at-dispatch feasible subset. Normalized witness supplies1541upper for both. No identical-optima claim or global flagshipgap.',
 hint_scope='Same frozen formulation with verified1567warmstart and upper cutoff; no choices fixed,no serialized CPproof resumption. Valid incumbent ensures cutoff cannot exclude an optimum.',
 cost=dict(slurm_elapsed_seconds=7174,allocated_cpus=16,allocated_cpu_seconds=7174*16,allocated_cpu_hours=7174*16/3600,reported_process_cpu_seconds=r['runtime']['process_cpu_seconds'],process_cpu_hours=r['runtime']['process_cpu_seconds']/3600,solver_wall_seconds=x['solver_wall_seconds'],driver_wall_seconds=r['runtime']['wall_seconds'],scope='Allocated/process/solverwall nested observations,not additive or normalizedspeedup'),
 frozen_sources_modified=False,raw_evidence_modified=False,factory_runs=0,solver_calls=0,new_performance_samples=0,wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu)
with (OUT/'report.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:result[k] for k in ('valid','status','optimum_interval','interval_width_minutes','incumbent_improvement_percent','heuristic2482_excess_gap_interval_percent','wall_seconds')}))
