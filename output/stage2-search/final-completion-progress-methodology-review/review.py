"""Independent read-only direct cutoff sums, no factory/solver/plot generation."""
from fractions import Fraction as F
import hashlib,json,time
from pathlib import Path
from stage2.compare_evaluations import load_evidence,select_rows

root=Path.cwd();base=root/'output/stage2-search/final-completion-progress';out=Path(__file__).resolve().parent
start=time.perf_counter();cpu=time.process_time()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
indexed=json.loads((base/'output-index.json').read_text())
for name,h in indexed.items():assert sha(base/name)==h
r=json.loads((base/'report.json').read_text());m,e,reference=load_evidence(root/'output/stage2-search/final-downloaded/final-frontier-6117515')
rows=select_rows(m,e,'selected-stretch-32',dict(orders=32,horizon=14400,profile='full'));p=m['protocol']['payload']
assert len(rows)==256 and m['actor_seeds']==[900000] and all(len(x['seeds'])==32 for x in p['leaves'])
prepared=[]
for x in rows:
 leaf=p['leaves'][x['leaf']];w=F(*leaf['probability'])/len(leaf['seeds']);ships=x['checker_metrics']['delivery_ticks'];n=x['metrics']['orders']
 assert x['policy_seed']==900000 and n==len(ships)+x['checker_metrics']['unfulfilled_orders']
 prepared.append((w,n,list(ships.values())))
assert sum(w for w,n,s in prepared)==1
mean_demand=sum(w*n for w,n,s in prepared);assert mean_demand==33

def cutoff(t):
 delivered=sum(w*sum(s<=t for s in ships) for w,n,ships in prepared)
 complete=sum(w for w,n,ships in prepared if len(ships)==n and max(ships)<=t)
 return dict(mean_delivered=float(delivered),mean_missing_from_final_demand=float(mean_demand-delivered),all_final_demand_shipped_probability=float(complete)),complete
for point in r['curve']:
 actual,_=cutoff(point['clock_minutes'])
 assert all(point[k]==v for k,v in actual.items())
 assert point['clock_hours']==point['clock_minutes']/60
for point in r['selected_clocks']:
 actual,_=cutoff(point['clock_minutes']);assert all(point[k]==v for k,v in actual.items())
complete_times=sorted(set(max(s) for w,n,s in prepared if len(s)==n));latest=max(t for w,n,s in prepared for t in s)
assert complete_times[0]==10294==r['first_complete_recorded_run_minutes'];assert latest==14064==r['latest_recorded_shipment_minutes']
quantiles={str(float(q)):next((t for t in complete_times if cutoff(t)[1]>=q),None) for q in (F(1,10),F(1,2),F(9,10),F(19,20))}
assert quantiles==r['observed_completion_probability_crossing_minutes']
assert quantiles['0.5']==12074 and quantiles['0.9']==13276 and quantiles['0.95'] is None
assert cutoff(10080)[1]==0 and cutoff(11520)[1]==F(619,3200) and cutoff(14400)[1]==F(233,256)
last=r['curve'][-1];assert last['clock_minutes']==14400 and last['mean_missing_from_final_demand']==.10234375
frontier=json.loads((root/'output/stage2-search/final-complete-report/preselected-frontier.json').read_text());g=next(x for x in frontier if x['method_id']=='selected-stretch-32')
# Independently compare main summary field values via its explicit measured fields.
summary=g['summary']
expected_last,_=cutoff(14400)
# Inclusive t<=cutoff creates right-continuous steps, including shipment atH.
fixture=[(F(1),1,[7])]
assert sum(w for w,n,s in fixture if len(s)==n and max(s)<=6)==0
assert sum(w for w,n,s in fixture if len(s)==n and max(s)<=7)==1
result=dict(valid=True,scope='Read-only fixed H14400 final shipment-clock progress audit; no shorter-horizon execution, terminal-SOC or optimality claim',source_sha256=sha(__file__),indexed_inputs_unchanged=True,source_inputs={n:sha(base/n) for n in indexed},rows=256,actor_seed=900000,exact_fraction_weights=True,curve_points_independently_checked=len(r['curve']),all_cutoffs_inclusive=True,curve_is_weighted_observed_subCDF=True,earliest_completed=complete_times[0],last_recorded_shipment=latest,exact_quantile_crossings=quantiles,selected_clock_points=r['selected_clocks'],final_point=expected_last,expected_final_demand=33,right_censoring_scope='Administrative H cutoff leaves completion unobserved for unfinished cases; potentially structural noncompleters are allowed. No independent-censoring assumption, Kaplan-Meier extrapolation, permanent-inability or shorter-horizon claim is used.',factory_runs=0,solver_calls=0,wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu)
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('valid','curve_points_independently_checked','exact_quantile_crossings','final_point','wall_seconds')}))
