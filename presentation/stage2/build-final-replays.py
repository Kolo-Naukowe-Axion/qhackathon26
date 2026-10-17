"""Fresh-check the first predeclared leaf/tape/actor of frozen selected policies."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from stage2.compare_evaluations import load_evidence,select_rows,file_hash,digest,PHYSICAL_SOURCES
from stage2.check import check_trace
from stage2.spec import build

def main():
 p=argparse.ArgumentParser();p.add_argument('--index',type=Path,required=True);a=p.parse_args()
 index=json.loads(a.index.read_text());target=Path(__file__).resolve().parent/'traces';records=[]
 for orders,cohort,method in [(12,'strong-cheap','static-grid-12'),(32,'frontier','selected-stretch-32')]:
  directory=Path(index[cohort]);manifest,evaluation,reference=load_evidence(directory)
  assert manifest['evaluation_role']=='final'
  for name in PHYSICAL_SOURCES:assert file_hash(ROOT/name)==manifest['source_hashes'][name],name
  protocol=manifest['protocol']['payload'];seed=protocol['leaves'][0]['seeds'][0];actor=manifest['actor_seeds'][0]
  config=dict(orders=orders,horizon=14400 if orders==32 else 5760,profile='full')
  rows=select_rows(manifest,evaluation,method,config)
  row=next(r for r in rows if r['seed']==seed and r['policy_seed']==actor)
  assert row['leaf']==0
  source=directory/'traces'/Path(row['trace_path']).name;raw=source.read_bytes();assert file_hash(source)==row['trace_sha256']
  trace=json.loads(raw);instance=build(**config,seed=seed);assert digest(instance)==row['physical_instance_sha256']
  checked=check_trace(trace,instance);assert checked['valid']and checked['terminal_requirements_met']
  cm=checked['metrics']
  for key in ['delivered_orders','unfulfilled_orders','terminal_deadline_debt_ticks','total_cost']:assert abs(cm[key]-row['checker_metrics'][key])<1e-5,key
  compressed=gzip.compress(raw,mtime=0);name=f'final-first-leaf0-{orders}-{config["horizon"]}';out=target/(name+'.json.gz');out.write_bytes(compressed)
  evidence=dict(schema='stage2-optional-replay-evidence.v1',label=f'FINAL · predeclared tape{seed} / actor{actor} · {orders} initial orders · {config["horizon"]//60}h',
   seed_role='FINAL; first predeclared leaf0/tape/actor, selected independently of outcome',
   horizon_scope='240h =10 days; extra calendar time with due dates unchanged'if orders==32 else'96h cutoff; actual shipments and censored deadline debt retained',
   source_path=str(source.relative_to(ROOT)),source_trace_sha256=row['trace_sha256'],trace_sha256=hashlib.sha256(compressed).hexdigest(),trace_sha256_convention='Gzip file bytes; original JSON activity data unchanged',
   instance_sha256=digest(instance),manifest_sha256=manifest['manifest_sha256'],protocol_sha256=protocol['protocol_sha256'],
   cohort_path=str((directory/'evaluation.json').relative_to(ROOT)),cohort_sha256=file_hash(directory/'evaluation.json'),
   fresh_independent_check=checked,checker_sha256=file_hash(ROOT/'stage2/check.py'),metrics=trace['metrics'],operations=len(trace['operations']),moves=len(trace['moves']),
   activity_data_changed=False,secondary_optimality_gap=None,compressed_bytes=len(compressed),decompressed_bytes=len(raw),
   predeclared_first_tape=True,selection=dict(cohort=cohort,method_id=method,config=config,leaf=0,seed=seed,actor=actor),source_evidence=reference)
  (target/(name+'.evidence.json')).write_text(json.dumps(evidence,indent=2)+'\n')
  records.append(dict(config=config,seed=seed,actor=actor,leaf=0,method_id=method,viewer_path='./traces/'+out.name,
   trace_sha256=evidence['trace_sha256'],fresh_check_valid=True,predeclared_first_tape=True,scope=f'{cm["delivered_orders"]}/{cm["delivered_orders"]+cm["unfulfilled_orders"]} shipped; cutoff debt {cm["terminal_deadline_debt_ticks"]} min, model cost {cm["total_cost"]:.2f}.',
   source_path=str(source.relative_to(ROOT)),source_trace_sha256=row['trace_sha256'],evidence_path=str((target/(name+'.evidence.json')).relative_to(ROOT))))
 report=target/'final-first-replay-index.json';report.write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(records,indent=2))
if __name__=='__main__':main()
