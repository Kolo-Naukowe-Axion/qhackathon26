"""Publish only a complete sealed TRAIN neighborhood; never inspect partial minima."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from stage2.schedule_neighborhood_audit import summarize,digest,CHECKPOINT_SHA256

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def same(a,b):
 if isinstance(a,dict):return isinstance(b,dict)and a.keys()==b.keys()and all(same(a[k],b[k])for k in a)
 if isinstance(a,list):return isinstance(b,list)and len(a)==len(b)and all(same(x,y)for x,y in zip(a,b))
 if isinstance(a,float):return type(b)in(int,float)and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-8)
 return type(a)is type(b)and a==b

def main():
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);a=p.parse_args();path=a.report.resolve();path=path/'report.json'if path.is_dir()else path
 report=json.loads(path.read_text())
 # All completion gates precede inspecting any minimum or ranked candidate.
 assert report['complete_checked_grid']and report['witnesses_complete_valid']and report['source_stable']
 assert report['actual_grid_execution_count']==report['declared_execution_count']==12184 and report['actual_oracle_replay_count']==24
 directory=path.parent;protocol=json.loads((directory/'protocol.json').read_text())
 assert protocol['schema']=='stage2-schedule-neighborhood-audit.v1'and protocol['seeds']==list(range(8))and protocol['actor_seed']==900000
 assert protocol['source_hashes']==report['source_hashes']and protocol['checkpoint_sha256']==report['checkpoint_sha256']==CHECKPOINT_SHA256
 for name,expected in report['source_hashes'].items():assert sha(directory/'source_snapshot'/name)==expected,name
 assert sha(directory/'selected-checkpoint.json')==CHECKPOINT_SHA256
 assert sha(ROOT/'stage2/schedule_neighborhood_audit.py')==report['source_hashes']['stage2/schedule_neighborhood_audit.py']
 rows=report['rows'];witnesses=report['oracle_witnesses'];assert len(rows)==12184 and len(witnesses)==24
 logged=[json.loads(line)for line in(directory/'rows.jsonl').read_text().splitlines()if line.strip()]
 assert Counter(map(digest,logged))==Counter(map(digest,rows+witnesses))
 tasks={t['task_id']:t for t in protocol['tasks']};assert len(tasks)==12184
 observed=set()
 for row in rows:
  assert row['task_id']not in observed;observed.add(row['task_id']);task=tasks[row['task_id']]
  for key in ('context_id','variant_id','config','schedule','phase','actor_seed'):assert row[key]==task[key],key
  assert row['valid']and not row.get('issues')and not row.get('error')and row['decode_mismatches']==0 and row['identity_audit']['valid']
  assert row['config']['seed']in range(8)and row['phase']=='TRAIN-finite-neighborhood'
  assert row['source_manifest_sha256']==digest(report['source_hashes'])and row['checkpoint_sha256']==CHECKPOINT_SHA256
  assert row['metrics_sha256']==digest(row['metrics'])
 for row in witnesses:assert row['valid']and row['original_grid_metrics_match']and row['original_grid_physical_trace_match']and row['phase']=='offline-oracle-witness'
 rebuilt=summarize(protocol['contexts'],rows);assert same(rebuilt,report['summary']),'Retained summary disagrees with full grid'
 analysis_path=directory.parent/'retention-analysis.json';analysis=json.loads(analysis_path.read_text());bounds_path=directory.parent/'necessary-bound-supplement.json';bounds=json.loads(bounds_path.read_text())
 assert analysis['report_sha256']==bounds['report_sha256']==sha(path)
 assert all(analysis[k]for k in ('all_rows_match_report','all_declared_variants_present','source_snapshot_matches_manifest','retained_trace_hashes_match'))
 assert len(analysis['independent_retained_trace_checks'])==27 and all(r['checked']['valid']and r['checked']['terminal_requirements_met']for r in analysis['independent_retained_trace_checks'])
 assert bounds['primary_only']and bounds['secondary_gap']is None and len(bounds['rows'])==24
 independent_path=ROOT/'output/stage2-search/final-independent-audit/train-headroom-audit.json';independent=json.loads(independent_path.read_text())
 assert independent['valid']and independent['grid_rows']==12184 and independent['separate_oracle_replays']==24 and independent['retained_physical_identity_replays']==27
 assert independent['report_sha256']==sha(path)and independent['protocol_sha256']==sha(directory/'protocol.json')and independent['retention_analysis_sha256']==sha(analysis_path)and independent['bound_supplement_sha256']==sha(bounds_path)
 contexts=[]
 for c,s in zip(protocol['contexts'],rebuilt):
  assert s['context_id']==c['context_id']and s['complete_checked_neighborhood']and s['invalid']==0
  tapes=[]
  for tape in s['per_tape']:
   triples=sorted({(r['metrics']['orders']-r['metrics']['shipped'],r['metrics']['total_tardiness_ticks'],r['metrics']['total_cost'])for r in rows if r['context_id']==c['context_id']and r['config']['seed']==tape['seed']})
   tapes.append(dict(**tape,distinct_objective_triples=triples,distinct_objective_triple_count=len(triples)))
  certs=[r for r in bounds['rows']if r['context_id']==c['context_id']];assert len(certs)==8
  for cert in certs:
   tape=next(t for t in tapes if t['seed']==cert['config']['seed']);assert cert['finite_neighborhood_witness_missing_upper_bound']==tape['lex_min'][0]and cert['certificate']['instance_sha256']==tape['physical_instance_sha256']
   assert cert['primary_interval_width']==cert['finite_neighborhood_witness_missing_upper_bound']-cert['necessary_missing_lower_bound']>=0
  summary=dict(primary_certified_tapes=sum(r['primary_optimum_certified']for r in certs),sum_missing_lower_bound=sum(r['necessary_missing_lower_bound']for r in certs),secondary_gap=None)
  contexts.append(dict(necessary_bound_summary=summary,**{k:v for k,v in s.items()if k not in('per_tape','all_fixed_variant_ranks')},radius=c['radius'],variant_count=len(c['variants']),
   per_tape=tapes,fixed_variants=s['all_fixed_variant_ranks']))
 sources={}
 for label,pth in [('independent_audit',independent_path),('retention_audit',analysis_path),('necessary_bounds',bounds_path),('scheduler',directory.parent/'sacct.psv'),('report',path),('protocol',directory/'protocol.json'),('all_rows',directory/'rows.jsonl'),('checkpoint',directory/'selected-checkpoint.json'),('exporter',Path(__file__))]:
  sources[label]=dict(path=str(pth.relative_to(ROOT)),sha256=sha(pth))
 accounting=[line.split('|')for line in(directory.parent/'sacct.psv').read_text().splitlines()];accounting=next(r for r in accounting if r[0]=='6117537');assert accounting[1:3]==['COMPLETED','0:0'];wall=int(accounting[3]);workers=int(accounting[4]);allocated=int(accounting[5]);assert allocated==wall*workers
 inherited=json.loads((directory/'selected-checkpoint.json').read_text());parts=list(map(int,accounting[6].split(':')));total_cpu=parts[0]*3600+parts[1]*60+parts[2]
 cost=dict(scheduler_elapsed_seconds=wall,allocated_cpus=workers,allocated_cpu_hours=allocated/3600,scheduler_total_cpu_seconds=total_cpu,recorded_gpu_hours=0,inherited_fit_episodes=inherited['fit_episodes'],inherited_validation_episodes=inherited['validation_episodes'],inherited_training_wall_seconds=inherited['actual_wall_seconds'],inherited_training_workers=inherited['workers'],scope='Grid and24oracle replays counted once. Inherited CEM fit/validation is prior shared work, not new neighborhood samples. Local audit/setup costs are separate; do not double-add nested worker/Slurm process CPU.')
 output=dict(schema='stage2-neighborhood-view.v1',source_files_verified=True,role='TRAIN',final_policy_changed=False,
  complete_checked_grid=True,witnesses_complete_valid=True,source_stable=True,actual_grid_execution_count=12184,actual_oracle_replay_count=24,
  cost=cost,cpu_seconds=report['cpu_seconds'],wall_seconds=report['wall_seconds'],actions=protocol['actions'],contexts=contexts,sources=sources,
  source_hashes=report['source_hashes'],physical_check_scope='Per-execution frozen independent checker plus canonical identity audit recorded in the complete grid. Export verifies task/row/source hashes and recomputes every finite summary, not a new physical replay of all variants.',
  interpretation='Offline TRAIN0–7 finite-neighborhood audit. Common fixed sequence and per-tape hindsight winners remain different. No final policy changes, full6^8 optimum, held-out improvement or positive-minimum infeasibility claim.')
 target=Path(__file__).resolve().parent/'research/neighborhood-evidence.json';target.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(dict(output=str(target),contexts=len(contexts),grid=12184,witnesses=24)))
if __name__=='__main__':main()
