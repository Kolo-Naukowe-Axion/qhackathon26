"""Audit complete TRAIN32 reward cohort; preserve actor/environment hierarchy."""
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'output/stage2-search/axion-download-2348/selector-reward-6117350'
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
 protocol_path=BASE/'protocol.json';report_path=BASE/'report.json';rows_path=BASE/'rows.jsonl';independent_path=BASE/'root-independent-summary.json'
 protocol=read(protocol_path);report=read(report_path);independent=read(independent_path)
 tasks={row['task_id']:row for row in protocol['tasks']}
 rows=[json.loads(line)for line in rows_path.read_text().splitlines()if line]
 assert len(tasks)==len(protocol['tasks'])==len(rows)==len(report['rows'])==2240
 assert report['source_stable'] and {row['task_id']for row in rows}==set(tasks)
 report_rows={row['task_id']:row for row in report['rows']}
 assert len(report_rows)==len(rows)
 code_hashes=protocol['source_hashes']
 for path,digest in code_hashes.items():assert sha(BASE/'source_snapshot'/path)==digest
 groups=defaultdict(list);instances={};common_settings={}
 for row in rows:
  task=tasks[row['task_id']];saved=report_rows[row['task_id']]
  for key in ('policy_id','config','weights','solver_options','seed_role'):
   assert row[key]==task[key]and row[key]==saved[key]
  assert row['metrics']==saved['metrics']and row['physical_instance_sha256']==saved['physical_instance_sha256']
  assert row['valid']and not row['issues']and not row['decode_mismatches']
  assert row['seed_role'].startswith('TRAIN0–31')and 0<=row['config']['seed']<32
  assert task['source_hashes']==code_hashes and row['config']['horizon']==5760
  key=row['config']['orders'],row['config']['seed'];digest=row['physical_instance_sha256']
  if key in instances:assert instances[key]==digest
  else:instances[key]=digest
  weights=deepcopy(row['weights']);weights.pop('selector');weights.pop('policy_seed')
  options=deepcopy(row['solver_options']);options.pop('reward_mode')
  setting=(weights,options)
  if row['config']['orders']in common_settings:assert common_settings[row['config']['orders']]==setting
  else:common_settings[row['config']['orders']]=setting
  groups[row['config']['orders'],row['policy_id']].append(row)
 summaries={(row['orders'],row['policy_id']):row for row in report['summary']}
 root_summary={(row['orders'],row['policy']):row for row in independent}
 assert set(groups)==set(summaries)==set(root_summary)
 exported=[]
 for (orders,policy),members in sorted(groups.items()):
  members.sort(key=lambda row:row['config']['seed']);assert [row['config']['seed']for row in members]==list(range(32))
  expected=summaries[orders,policy];root=root_summary[orders,policy]
  shipped=sum(row['metrics']['shipped']for row in members);required=sum(row['metrics']['orders']for row in members)
  complete=sum(row['metrics']['all_orders_fulfilled']for row in members);debt=sum(row['metrics']['total_tardiness_ticks']for row in members)
  assert expected['runs']==root['runs']==32 and expected['invalid']==0
  assert expected['shipped']==root['shipped']==shipped and expected['required']==root['required']==required
  assert expected['complete']==root['complete']==complete and expected['total_tardiness']==debt
  assert root['missing']==(required-shipped)/32 and root['debt']==debt/32
  first=members[0]
  exported.append(dict(orders=orders,policy_id=policy,method=first['weights']['selector'],reward_mode=first['solver_options']['reward_mode'],
   actor=first['weights']['policy_seed']if'-actor'in policy else None,
   tapes=[dict(seed=row['config']['seed'],valid=row['valid'],decode_mismatches=len(row['decode_mismatches']),
    orders=row['metrics']['orders'],shipped=row['metrics']['shipped'],complete=row['metrics']['all_orders_fulfilled'],
    cutoff_debt=row['metrics']['total_tardiness_ticks'],cost=row['metrics']['total_cost'])for row in members]))
 # Independently retain the exact n12 equality, per physical tape, across actors.
 exact={row['config']['seed']:row['metrics']for row in groups[12,'exact-priority-lex']}
 n12_equal=all(row['metrics']==exact[row['config']['seed']]for (orders,policy),members in groups.items()
  if orders==12 and '-priority-lex-actor'in policy for row in members)
 assert n12_equal
 actor_groups=defaultdict(list)
 for group in exported:
  if group['actor']is not None:actor_groups[group['orders'],group['method'],group['reward_mode']].append(group)
 actor_summary=[]
 for (orders,method,reward),members in sorted(actor_groups.items()):
  assert sorted(row['actor']for row in members)==[7,13,29]
  clustered=[]
  for seed in range(32):
   factory=[group['tapes'][seed]for group in members];assert len({row['orders']for row in factory})==1
   clustered.append(dict(seed=seed,missing=mean(row['orders']-row['shipped']for row in factory),
    complete=mean(row['complete']for row in factory),debt=mean(row['cutoff_debt']for row in factory)))
  actor_summary.append(dict(orders=orders,method=method,reward_mode=reward,actors=[7,13,29],environments=32,
   mean_missing=mean(row['missing']for row in clustered),complete_fraction=mean(row['complete']for row in clustered),
   mean_cutoff_debt=mean(row['debt']for row in clustered),
   actor_total_shipped_range=[min(sum(t['shipped']for t in group['tapes'])for group in members),max(sum(t['shipped']for t in group['tapes'])for group in members)]))
 sources={str(path.relative_to(ROOT)):sha(path)for path in (protocol_path,report_path,rows_path,independent_path)}
 out=dict(schema='stage2-reward-confirmation-viewer.v1',runs=2240,valid=2240,decode_mismatches=0,
  seed_role='Full contiguous TRAIN0–31 development confirmation; not held-out or an unbiased unseen-data estimate',
  groups=exported,actor_aggregates=actor_summary,n12_priority_lex_actor_metrics_equal_exact=n12_equal,
  physical_instance_hashes={f'{orders}:{seed}':digest for (orders,seed),digest in sorted(instances.items())},
  source_hashes=sources,frozen_code_hashes=code_hashes,source_files_verified=True,final_tapes_used=0,
  actor_rule='Average actors7/13/29 within each of32 shared physical environment tapes first; actors are not96 independent environments',
  metric_definition='cutoff_debt includes delivered lateness plus unfinished-order debt only through5760; eventual unfinished lateness is unknown',
  encoding_scope='Corrected reward in rich-factory local start selection; distinct from three-bit baseline certificates and earlier23-bit scaling fixtures; CPU simulations/fallbacks, no physical QPU or speedup claim')
 target=Path(__file__).with_name('report.json');target.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(dict(runs=2240,groups=len(exported),actor_aggregates=len(actor_summary),n12_priority_lex_equal=n12_equal)))

if __name__=='__main__':main()
