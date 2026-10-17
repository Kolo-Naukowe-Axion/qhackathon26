"""One-pass TRAIN-only finite schedule neighborhood headroom audit.

Each execution is causal time-only control. The hindsight per-tape minimum is
an offline oracle over this declared neighborhood, never a selected policy.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from copy import deepcopy
import gzip
import hashlib
import itertools
import json
import multiprocessing
from pathlib import Path
import time
import traceback

from .adaptive_recovery import Controller, ACTIONS, SOURCES as BASE_SOURCES
from .maintenance_guard import MaintenanceOutageGuardMixin
from .recovery_routing import AdmissionRecoveryRoutingFactory, ROOT

CHECKPOINT_SHA256='d2ae8337daadd1baec7840e29b69500d91a548bbd3c0b4b5378f2b22ba6203e9'
SOURCES=tuple(dict.fromkeys(('stage2/__init__.py','stage2/schedule_neighborhood_audit.py','stage2/maintenance_guard.py',
    'stage2/identity_audit.py')+BASE_SOURCES))
ACTOR_SEED=900000

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def hashes():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES}

def load_checkpoint(path):
    path=Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=CHECKPOINT_SHA256:raise ValueError('Frozen CEM6 checkpoint SHA mismatch')
    a=json.loads(path.read_text())
    for n,s in a['source_hashes'].items():
        if hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=s:raise ValueError(f'Checkpoint source drift: {n}')
    if a['method']!='cem' or a['actions']!=list(ACTIONS):raise ValueError('Expected original six-action CEM artifact')
    if [c['config']['orders'] for c in a['contexts']]!=[12,16,24]:raise ValueError('Expected frozen three contexts')
    if any(p['kind']!='schedule' or len(p['schedule'])!=8 for p in a['policies_by_context']):raise ValueError('Expected eight-segment schedules')
    return a

def neighborhood(original,radius):
    original=tuple(original)
    if len(original)!=8 or any(type(a) is not int or a not in range(6) for a in original) or radius not in (1,2):raise ValueError('Declared eight-segment six-action radius1/2 domain required')
    schedules={original}
    for distance in range(1,radius+1):
        for positions in itertools.combinations(range(8),distance):
            for replacements in itertools.product(*(tuple(a for a in range(6) if a!=original[p]) for p in positions)):
                s=list(original)
                for p,a in zip(positions,replacements):s[p]=a
                schedules.add(tuple(s))
    return sorted(schedules)

def declare(artifact):
    contexts=[];tasks=[]
    for j,c in enumerate(artifact['contexts']):
        n=c['config']['orders'];original=artifact['policies_by_context'][j]['schedule'];radius=1 if n==12 else 2
        variants=[dict(variant_id=i,schedule=list(s),hamming_distance=sum(a!=b for a,b in zip(s,original))) for i,s in enumerate(neighborhood(original,radius))]
        contexts.append(dict(context_id=j,config=c['config'],radius=radius,original_schedule=original,
            original_variant_id=next(v['variant_id'] for v in variants if v['schedule']==original),variants=variants))
        for v in variants:
            for seed in range(8):tasks.append(dict(task_id=len(tasks),context_id=j,config=dict(c['config'],seed=seed),**v,
                phase='TRAIN-finite-neighborhood',actor_seed=ACTOR_SEED,retain_trace=seed==0 and v['schedule']==original))
    return contexts,tasks

class AuditFactory(MaintenanceOutageGuardMixin,AdmissionRecoveryRoutingFactory):pass

def construct(instance,artifact,context_id,schedule):
    c=artifact['contexts'][context_id]
    if c['config']!=dict(orders=len(instance['orders']),horizon=instance['horizon_ticks'],profile=instance['profile']):raise ValueError('Instance/context mismatch')
    if len(schedule)!=8 or any(type(a) is not int or a not in range(6) for a in schedule):raise ValueError('Invalid schedule')
    base=dict(c['weights'],selector='priority',policy_seed=ACTOR_SEED)
    controller=Controller(dict(kind='schedule',schedule=list(schedule)),base,ACTOR_SEED,True,artifact['interval'])
    options=deepcopy(c['solver_options'])
    if options.pop('admission',False) is not True:raise ValueError('Expected unchanged admission context')
    return AuditFactory(instance,base,controller,maintenance_outage_guard=True,**options),controller

def metric_key(row):
    m=row['metrics'];return (m['orders']-m['shipped'],m['total_tardiness_ticks'],m['total_cost'])

def simulate(task):
    from .spec import build
    from .check import check_trace
    from .identity_audit import audit_trace
    start=time.perf_counter();cpu=time.process_time();trace=None
    row={k:deepcopy(v) for k,v in task.items() if k not in ('source_hashes','checkpoint','output')}
    try:
        if task['config']['seed'] not in range(8):raise ValueError('Only TRAIN0–7 tapes allowed')
        if hashes()!=task['source_hashes']:raise RuntimeError('Source drift before execution')
        artifact=load_checkpoint(task['checkpoint']);instance=build(**task['config']);factory,controller=construct(instance,artifact,task['context_id'],task['schedule']);trace=factory.run()
        checked=check_trace(trace,instance);identity=audit_trace(trace,instance)
        mismatches=sum(d['result'].get('selected') is None or d.get('committed') is None or
            sorted(d['result']['selected'])!=sorted(d['committed']) for d in trace.get('qubo_decisions',[]))
        row.update(valid=checked['valid'] and checked.get('terminal_requirements_met',False) and identity['valid'] and mismatches==0,
            issues=checked['issues'],identity_audit=identity,decode_mismatches=mismatches,metrics=trace['metrics'],physical_instance_sha256=digest(instance),
            source_manifest_sha256=digest(task['source_hashes']),checkpoint_sha256=CHECKPOINT_SHA256,
            action_ids=[d['action_id'] for d in trace['decisions'] if 'action_id' in d],
            metrics_sha256=digest(trace['metrics']),
            physical_trace_sha256=digest({k:trace[k] for k in ('operations','moves','worker_moves','events','energy','metrics')}))
        if hashes()!=task['source_hashes']:raise RuntimeError('Source drift after execution')
    except Exception as exc:row.update(valid=False,error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
    if trace is not None and (task.get('retain_trace') or not row['valid']):
        payload=json.dumps(trace,separators=(',',':')).encode();p=Path(task['output'])/f"trace-{task['phase']}-{task['task_id']}.json.gz";p.write_bytes(gzip.compress(payload,mtime=0))
        row.update(trace_path=str(p),trace_sha256=hashlib.sha256(payload).hexdigest())
    row.update(wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu)
    return row

def summarize(contexts,rows):
    results=[]
    for c in contexts:
        rs=[r for r in rows if r['context_id']==c['context_id'] and r['phase']=='TRAIN-finite-neighborhood'];expected=len(c['variants'])*8
        unique={(r['variant_id'],r['config']['seed']) for r in rs};valid=len(rs)==expected and len(unique)==expected and all(r['valid'] for r in rs)
        valid=valid and all(len({r.get('physical_instance_sha256') for r in rs if r['config']['seed']==seed})==1 for seed in range(8))
        s=dict(context_id=c['context_id'],orders=c['config']['orders'],expected_rows=expected,actual_rows=len(rs),invalid=sum(not r['valid'] for r in rs),
            complete_checked_neighborhood=valid,scope='Development only; offline finite-neighborhood oracle, not full6^8 optimum or causal deployed selector')
        if valid:
            by_tape=[]
            for seed in range(8):
                group=[r for r in rs if r['config']['seed']==seed];best=min(group,key=lambda r:(metric_key(r),r['schedule']));worst=max(group,key=metric_key)
                original=next(r for r in group if r['variant_id']==c['original_variant_id'])
                by_tape.append(dict(seed=seed,lex_min=list(metric_key(best)),lex_max=list(metric_key(worst)),
                    first_lexicographic_minimum_variant_id=best['variant_id'],schedule=best['schedule'],original_key=list(metric_key(original)),
                    physical_instance_sha256=best['physical_instance_sha256'],witness_task_id=best['task_id'],
                    distinct_physical_trajectories=len({r['physical_trace_sha256'] for r in group}),
                    distinct_metric_outcomes=len({r['metrics_sha256'] for r in group}),
                    original_physical_equivalent_variants=sum(r['physical_trace_sha256']==original['physical_trace_sha256'] for r in group)))
            fixed=[]
            for v in c['variants']:
                g=[r for r in rs if r['variant_id']==v['variant_id']];fixed.append(dict(variant_id=v['variant_id'],schedule=v['schedule'],
                    aggregate_key=[sum(metric_key(r)[i] for r in g) for i in range(3)]))
            best_fixed=min(fixed,key=lambda v:(v['aggregate_key'],v['schedule']))
            s.update(per_tape=by_tape,best_common_fixed_variant=best_fixed,
                original_common_fixed_variant=next(v for v in fixed if v['variant_id']==c['original_variant_id']),
                offline_per_tape_oracle_aggregate_key=[sum(t['lex_min'][i] for t in by_tape) for i in range(3)],all_fixed_variant_ranks=sorted(fixed,key=lambda v:(v['aggregate_key'],v['schedule'])))
        else:s['envelope_suppressed']='Missing,duplicate,invalid or incomplete execution; no valid-only envelope'
        results.append(s)
    return results

def campaign(output,checkpoint,workers=32,seconds=1680):
    if not 1<=workers<=32 or not 0<seconds<=1680:raise ValueError('Bounded32CPU/28minute execution budget required')
    artifact=load_checkpoint(checkpoint);contexts,declared=declare(artifact);output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False);sources=hashes()
    for t in declared:t.update(source_hashes=sources,checkpoint=str(Path(checkpoint).resolve()),output=str(output))
    for n in SOURCES:
        p=output/'source_snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    (output/'selected-checkpoint.json').write_bytes(Path(checkpoint).read_bytes())
    protocol=dict(schema='stage2-schedule-neighborhood-audit.v1',contexts=contexts,tasks=declared,source_hashes=sources,
        checkpoint_sha256=CHECKPOINT_SHA256,actions=list(ACTIONS),actor_seed=ACTOR_SEED,workers=workers,wall_budget_seconds=seconds,
        seeds=list(range(8)),role='One-pass TRAIN-only offline headroom audit; original final closed; no policy selection or deployment',
        reward='Original priority dispatch; no RewardMixin or selector override beyond priority',
        oracle_witness_rule='After complete valid grid, rerun first lexicographic minimum schedule separately percontext/tape; excluded from estimates',
        trajectory_hash_scope='operations,moves,worker_moves,events,energy,metrics; excludes controller decisions and timing',
        invalid_rule='Any invalid stops new submissions; any invalid/missing/duplicate suppresses affected context neighborhood envelope; all failures retained')
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');started=time.perf_counter();rows=[];witnesses=[];deadline=started+seconds
    with (output/'rows.jsonl').open('x') as log,ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool:
        it=iter(declared);pending={};invalid_seen=False
        def submit():
            if invalid_seen or time.perf_counter()>=deadline:return False
            t=next(it,None)
            if t is None:return False
            pending[pool.submit(simulate,t)]=t;return True
        for _ in range(workers*2):submit()
        while pending:
            done,_=wait(pending,return_when=FIRST_COMPLETED)
            for f in done:
                t=pending.pop(f)
                try:r=f.result()
                except Exception as exc:r={k:deepcopy(t[k]) for k in ('task_id','context_id','config','variant_id','schedule','phase')};r.update(valid=False,error=str(exc))
                rows.append(r);log.write(json.dumps(r)+'\n');log.flush()
                invalid_seen=invalid_seen or not r['valid'];submit()
        summary=summarize(contexts,rows)
        for s in summary:
            if invalid_seen or not s['complete_checked_neighborhood']:continue
            for entry in s['per_tape']:
                if time.perf_counter()>=deadline:break
                original=declared[entry['witness_task_id']];task=dict(original,phase='offline-oracle-witness',retain_trace=True)
                r=pool.submit(simulate,task).result();baseline=next(x for x in rows if x['task_id']==original['task_id'])
                r['original_grid_metrics_match']=r.get('metrics')==baseline.get('metrics');r['original_grid_physical_trace_match']=r.get('physical_trace_sha256')==baseline.get('physical_trace_sha256')
                r['valid']=r['valid'] and r['original_grid_metrics_match'] and r['original_grid_physical_trace_match'];witnesses.append(r)
                log.write(json.dumps(r)+'\n');log.flush()
    complete=len(rows)==len(declared) and all(s['complete_checked_neighborhood'] for s in summary)
    result={k:v for k,v in protocol.items() if k!='tasks'}
    result.update(rows=sorted(rows,key=lambda r:r['task_id']),summary=summary,oracle_witnesses=witnesses,
        complete_checked_grid=complete,witnesses_complete_valid=len(witnesses)==24 and all(r['valid'] for r in witnesses),
        wall_seconds=time.perf_counter()-started,cpu_seconds=sum(r.get('cpu_seconds',0) for r in rows+witnesses),source_stable=hashes()==sources,
        declared_execution_count=len(declared),actual_grid_execution_count=len(rows),actual_oracle_replay_count=len(witnesses))
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--workers',type=int,default=32);p.add_argument('--seconds',type=float,default=1680);a=p.parse_args();r=campaign(a.output,a.checkpoint,a.workers,a.seconds)
    print(json.dumps({k:r[k] for k in ('complete_checked_grid','witnesses_complete_valid','actual_grid_execution_count','actual_oracle_replay_count','wall_seconds','source_stable')}))

if __name__=='__main__':main()
