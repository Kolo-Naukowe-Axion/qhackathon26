"""Explicit guardtrue execution adapter for already selected v12 policies."""
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
import gzip,hashlib,json,multiprocessing
from pathlib import Path
import time
from stage2 import adaptive_recovery as a
from stage2 import adaptive_evidence as e
from stage2 import maintenance_guard as guard
from stage2.identity_audit import audit_trace
from stage2.spec import build
from stage2.check import check_trace

PHYSICAL=('operations','moves','worker_moves','events','energy','metrics','admission_history')


def no_timing(value):
 if isinstance(value,dict):return {k:no_timing(v) for k,v in value.items() if k not in ('wall_seconds','maintenance_outage_guard')}
 if isinstance(value,list):return [no_timing(v) for v in value]
 return value


def replay(task):
 start=time.perf_counter();cpu=time.process_time()
 if a.hashes()!=task['original_source_hashes'] or guard.hashes()!=task['guard_source_hashes']:raise RuntimeError('Held inference/guard source mismatch')
 c=task['context'];instance=build(**c['config'],seed=task['seed']);expected=deepcopy(instance)
 controller=a.Controller(task['policy'],c['weights'],0,True,task['interval'])
 trace=guard.run(instance,c['weights'],controller,maintenance_outage_guard=True,**c['solver_options'])
 checked=check_trace(trace,expected);identity=audit_trace(trace,expected);m=trace['metrics'];cm=checked['metrics']
 reconciliation=(m['shipped']==cm['delivered_orders'] and m['orders']-m['shipped']==cm['unfulfilled_orders'] and m['total_tardiness_ticks']==cm['terminal_deadline_debt_ticks'] and abs(m['total_cost']-cm['total_cost'])<1e-8)
 original=json.loads(gzip.decompress(Path(task['original_trace']).read_bytes()))
 physical={key:trace.get(key)==original.get(key) for key in PHYSICAL}
 payload=json.dumps(trace,separators=(',',':')).encode();path=Path(task['trace_path'])
 with path.open('xb') as target:target.write(gzip.compress(payload,mtime=0))
 if a.hashes()!=task['original_source_hashes'] or guard.hashes()!=task['guard_source_hashes']:raise RuntimeError('Source changed during replay')
 return dict(context_id=task['context_id'],seed=task['seed'],policy_sha256=task['policy_sha256'],
  valid=checked['valid'] and checked['terminal_requirements_met'] and identity['valid'] and reconciliation,
  physical_issues=checked['issues'],identity_issues=identity['issues'],metric_reconciliation=reconciliation,
  metrics=m,checker_metrics=cm,physical_comparison=physical,all_physical_lists_and_metrics_equal=all(physical.values()),
  algorithm_audit_equal_ignoring_timing_and_guard_adapter=no_timing(trace.get('algorithm_audit'))==no_timing(original.get('algorithm_audit')),
  guard=trace['algorithm_audit']['maintenance_outage_guard'],trajectory=controller.trajectory,
  trace_path=path.name,trace_sha256=e.digest(payload),trace_gzip_sha256=e.digest(path.read_bytes()),
  wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu)


def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--seal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--workers',type=int,default=32)
 args=p.parse_args();verified=e.verify_seal(args.seal);artifact=json.loads((args.seal/'original/selected-checkpoint.json').read_bytes())
 if a.hashes()!=artifact['source_hashes']:raise RuntimeError('v12 source/inference differs')
 if args.output.exists():raise ValueError('Preserve earlier guarded replay output')
 args.output.mkdir(parents=True);began=time.perf_counter();tasks=[];guard_sources=guard.hashes()
 for c,context in enumerate(artifact['contexts']):
  policy=artifact['policies_by_context'][c]
  for seed in range(100,116):
   tasks.append(dict(context_id=c,context=context,policy=policy,policy_sha256=e.digest(e.canonical(policy)),seed=seed,
    original_source_hashes=artifact['source_hashes'],guard_source_hashes=guard_sources,interval=artifact['interval'],
    original_trace=str((args.seal/f'trace-context{c}-seed{seed}.json.gz').resolve()),trace_path=str((args.output/f'trace-context{c}-seed{seed}.json.gz').resolve())))
 with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn')) as pool:rows=list(pool.map(replay,tasks))
 groups=[]
 for c in range(len(artifact['contexts'])):
  rs=[r for r in rows if r['context_id']==c]
  groups.append(dict(context_id=c,config=artifact['contexts'][c]['config'],original_selection_key=artifact['selection'][c]['key'],guarded_selection_key=e.selection_key(rs),
   all_valid=all(r['valid'] for r in rs),identical_physical_trajectories=sum(r['all_physical_lists_and_metrics_equal'] for r in rs),
   guard_activated_episodes=sum(r['guard']['blocked_eligible_calls']>0 for r in rs),guard_blocked_calls=sum(r['guard']['blocked_eligible_calls'] for r in rs)))
 report=dict(schema='guarded-v12-selected-replay.v1',original_seal=str(args.seal.resolve()),original_seal_verified=verified,
  original_policy_inference_unchanged=True,adapter='Only maintenance_outage_guard=True backend; original v12 controller/weights/policy/interval/argmax/actor0 unchanged',
  original_source_hashes=artifact['source_hashes'],guard_source_hashes=guard_sources,driver_sha256=e.digest(Path(__file__).read_bytes()),runtime=e.runtime_metadata(),
  rows=rows,groups=groups,all_valid=all(r['valid'] for r in rows),runs=len(rows),final_tapes=0,
  rollout_cpu_seconds=sum(r['cpu_seconds'] for r in rows),rollout_wall_seconds_sum=sum(r['wall_seconds'] for r in rows),wall_seconds=time.perf_counter()-began,
  role='Reused development validation adapter verification; not untouched final performance evidence')
 (args.output/'guarded-report.json').write_text(json.dumps(report,indent=2)+'\n');(args.output/'guarded_selected_replay.py').write_bytes(Path(__file__).read_bytes())
 print(json.dumps(dict(all_valid=report['all_valid'],runs=len(rows),groups=groups,wall_seconds=report['wall_seconds']),indent=2),flush=True)
 if not report['all_valid']:raise RuntimeError('Guarded selected replay invalid; evidence retained')


if __name__=='__main__':main()
