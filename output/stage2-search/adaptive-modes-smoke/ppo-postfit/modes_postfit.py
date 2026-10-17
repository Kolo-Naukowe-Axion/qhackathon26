"""New18-action post-fit replay and used-action static diagnostics; VAL only."""
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import gzip,hashlib,json,multiprocessing
from pathlib import Path
import subprocess,time
from stage2 import adaptive_modes as a
from stage2 import adaptive_evidence as e

PHYSICAL=('operations','moves','worker_moves','events','energy','metrics','admission_history')


def read_trace(row):return json.loads(gzip.decompress(Path(row['trace_path']).read_bytes()))


def collect(fit,output,workers=32,job=None,local_smoke=False):
 fit=Path(fit).resolve();output=Path(output).resolve();start=time.perf_counter();artifact=json.loads((fit/'selected-checkpoint.json').read_bytes())
 if artifact.get('schema')!='stage2-adaptive-modes-policy.v1' or artifact.get('actions')!=list(a.ACTIONS):raise ValueError('Exact18-action artifact required')
 if artifact['source_hashes']!=a.hashes() or not artifact.get('maintenance_outage_guard') or not artifact.get('identity_supplement'):raise ValueError('Source/guard/identity mismatch')
 if artifact['train_seeds']!=list(range(32)) or artifact['validation_seeds']!=list(range(100,116)) or artifact['final_tapes']!=0:raise ValueError('Declared development split required')
 if job:
  accounting=subprocess.check_output(['sacct','-X','-j',job,'--parsable2','--noheader','--format=JobID,State,ExitCode,ElapsedRaw,AllocCPUS,TotalCPU,CPUTimeRAW,NodeList'],text=True)
  records=[line.split('|') for line in accounting.splitlines() if line.strip()];matched=[r for r in records if r[0]==job]
  if len(matched)!=1 or matched[0][1]!='COMPLETED' or matched[0][2]!='0:0':raise RuntimeError('Actual successful fit completion required')
 elif local_smoke and all(c['config']['orders']==1 for c in artifact['contexts']):accounting='Explicit completed one-order local smoke attestation; no scheduler'
 else:raise ValueError('Scheduler completion proof required outside one-order smoke')
 if output.exists():raise ValueError('Use new post-fit evidence directory')
 output.mkdir(parents=True)
 def write(name,payload):
  path=output/name;path.parent.mkdir(parents=True,exist_ok=True)
  with path.open('xb') as target:target.write(payload)
 for name in ('selected-checkpoint.json','protocol.json','episodes.jsonl'):write('original/'+name,(fit/name).read_bytes())
 for name,sha in artifact['source_hashes'].items():
  payload=(fit/'source_snapshot'/name).read_bytes()
  if e.digest(payload)!=sha:raise ValueError('Fit source snapshot mismatch')
  write('original/source_snapshot/'+name,payload)
 policies=artifact['policies_by_context'];sha=[e.digest(e.canonical(policy)) for policy in policies]
 if sha!=artifact['selected_policy_sha256']:raise ValueError('Selected policy digest mismatch')
 for policy,digest in zip(policies,sha):
  payload=(fit/'policies'/(digest+'.json')).read_bytes()
  if e.digest(e.canonical(json.loads(payload)))!=digest:raise ValueError('Selected archived blob mismatch')
  name='policies/'+digest+'.json'
  if not (output/name).exists():write(name,payload)
 original_rows=[json.loads(line) for line in (fit/'episodes.jsonl').read_text().splitlines()]
 if len(original_rows)!=artifact['fit_episodes']+artifact['validation_episodes']:raise ValueError('Original episode counters incomplete')
 for row in original_rows:
  allowed=range(100,116) if row['phase']=='VALIDATION' else range(32)
  if row['seed'] not in allowed:raise ValueError('Unexpected factory tape in original log')
 tasks=[]
 def task(c,policy,seed,prefix):
  return dict(context_id=c,context=artifact['contexts'][c],policy=policy,seed=seed,actor_seed=0,
   phase='POSTFIT-REUSED-VAL',deterministic=True,interval=artifact['interval'],source_hashes=artifact['source_hashes'],
   policy_sha256=e.digest(e.canonical(policy)),trace_path=str(output/f'{prefix}-context{c}-seed{seed}.json.gz'))
 for c,policy in enumerate(policies):tasks += [task(c,policy,seed,'selected') for seed in range(100,116)]
 with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool:rows=list(pool.map(a.rollout,tasks))
 analysis=[];static_tasks=[];physical={}
 for row in rows:
  trace=read_trace(row);physical[row['context_id'],row['seed']]={key:trace.get(key) for key in PHYSICAL}
 for c,policy in enumerate(policies):
  group=[r for r in rows if r['context_id']==c];key=list(a.selection_key(group));declared=artifact['selection'][c]['key']
  sequences=[tuple(step['action'] for step in row['trajectory']) for row in group];used=sorted({x for seq in sequences for x in seq})
  analysis.append(dict(context_id=c,config=artifact['contexts'][c]['config'],policy_kind=policy['kind'],selected_update=artifact['selection'][c]['selected_update'],
   declared_selection_key=declared,replayed_selection_key=key,key_agrees=e.keys_agree(key,declared),all_valid=all(r['valid'] for r in group),
   action_sequence_histogram={','.join(map(str,seq)):n for seq,n in Counter(sequences).items()},
   action_descriptors={str(x):a.ACTIONS[x] for x in used},constant_episodes=sum(len(set(seq))==1 for seq in sequences),
   per_episode_action_changes=[r['action_changes'] for r in group],static_diagnostic_actions=[] if policy['kind']=='static' else used))
  if policy['kind']!='static':
   for action in used:
    static_tasks += [dict(task(c,dict(kind='static',action=action),seed,f'static-action{action}'),static_action=action) for seed in range(100,116)]
 if static_tasks:
  with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool:static_rows=list(pool.map(a.rollout,static_tasks))
 else:static_rows=[]
 for task0,row in zip(static_tasks,static_rows):
  row['static_action']=task0['static_action'];trace=read_trace(row)
  row['physical_lists_match_selected']=all(trace.get(key)==physical[row['context_id'],row['seed']][key] for key in PHYSICAL)
 comparisons=[]
 for item in analysis:
  for action in item['static_diagnostic_actions']:
   group=[r for r in static_rows if r['context_id']==item['context_id'] and r['static_action']==action]
   comparisons.append(dict(context_id=item['context_id'],action=action,weights=a.ACTIONS[action],key=list(a.selection_key(group)),
    all_valid=all(r['valid'] for r in group),identical_selected_physical_trajectories=sum(r['physical_lists_match_selected'] for r in group),runs=len(group)))
 write('selected-replay.json',json.dumps(rows,indent=2).encode()+b'\n');write('used-action-static-replays.json',json.dumps(static_rows,indent=2).encode()+b'\n')
 report=dict(schema='adaptive-modes-postfit.v1',training_job=job,training_scheduler_accounting=accounting,fit_directory=str(fit),
  source_hashes=artifact['source_hashes'],driver_sha256=e.digest(Path(__file__).read_bytes()),runtime=e.runtime_metadata(),
  original_training_runtime=artifact['runtime'],selected=analysis,static_diagnostics=comparisons,
  selected_replays=len(rows),static_replays=len(static_rows),
  all_replays_valid=all(r['valid'] for r in rows+static_rows),all_selected_keys_match=all(x['key_agrees'] for x in analysis),
  fit_costs=dict(actual_wall_seconds=artifact['actual_wall_seconds'],parent_cpu_seconds=artifact['parent_cpu_seconds'],
   summed_rollout_cpu_seconds=artifact['summed_rollout_cpu_seconds'],summed_rollout_wall_seconds=artifact['summed_rollout_wall_seconds'],
   raw_log_rollout_cpu_seconds=sum(r['cpu_seconds'] for r in original_rows),raw_log_rollout_wall_seconds=sum(r['wall_seconds'] for r in original_rows)),
  replay_rollout_cpu_seconds=sum(r['cpu_seconds'] for r in rows+static_rows),replay_rollout_wall_seconds_sum=sum(r['wall_seconds'] for r in rows+static_rows),
  total_collection_wall_seconds=time.perf_counter()-start,final_tapes=0,
  role='Reused development validation selected-policy reproducibility and used-action static diagnostics; no untouched performance or full-static-domain superiority claim')
 write('report.json',json.dumps(report,indent=2).encode()+b'\n');write('modes_postfit.py',Path(__file__).read_bytes())
 manifest=dict(schema='adaptive-modes-postfit-seal.v1',files={str(p.relative_to(output)):e.digest(p.read_bytes()) for p in sorted(output.rglob('*')) if p.is_file()})
 manifest['seal_sha256']=e.digest(e.canonical(manifest));write('manifest.json',json.dumps(manifest,indent=2).encode()+b'\n')
 for path in output.rglob('*'):
  if path.is_file():path.chmod(0o444)
 print(json.dumps({key:report[key] for key in ('all_replays_valid','all_selected_keys_match','selected','static_diagnostics','total_collection_wall_seconds')},indent=2),flush=True)
 if not report['all_replays_valid'] or not report['all_selected_keys_match']:raise RuntimeError('Post-fit mismatch retained for diagnosis')
 return report


if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--fit',required=True);p.add_argument('--output',required=True);p.add_argument('--workers',type=int,default=32)
 p.add_argument('--training-job');p.add_argument('--local-smoke',action='store_true');args=p.parse_args()
 collect(args.fit,args.output,args.workers,args.training_job,args.local_smoke)
