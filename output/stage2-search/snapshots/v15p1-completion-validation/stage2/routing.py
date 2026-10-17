"""Process-scoped public-state ETA routing over unchanged factory physics.

This reuses AdvancedFactory's existing heuristic. It does not predict hidden
quality outcomes, replace actual calendar checks, or guarantee completion times.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from copy import deepcopy
import gzip
import hashlib
import json
import multiprocessing
from pathlib import Path
import time
import traceback

from .admission import AdmissionMixin
from .kitting import KitToolingSpecialistFactory

ROOT=Path(__file__).resolve().parents[1]
SOURCE_NAMES=("stage2/routing.py","stage2/engine.py","stage2/spec.py","stage2/check.py",
    "stage2/dispatch.py","stage2/qubo.py","stage2/quantum.py","stage2/advanced.py",
    "stage2/specialist.py","stage2/tooling.py","stage2/kitting.py","stage2/admission.py",
    "instances/stage2/metaltech_pressure.json")


def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCE_NAMES}


def assert_sources(expected):
    if hashes()!=expected:raise RuntimeError('Routing experiment source changed; retain failure and freeze again')


class RoutingMixin:
    def __init__(self,*args,routing_policy=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.routing_scoped=routing_policy is not None
        policy=dict(eta_processes=[],free_buffer_processes=[])
        if routing_policy is not None:
            if set(routing_policy)-set(policy):raise ValueError('Unknown scoped routing option')
            policy.update(deepcopy(routing_policy))
        for key,processes in policy.items():
            if not isinstance(processes,(list,tuple)) or not set(processes)<=set(self.i['modes']):
                raise ValueError('Scoped routing processes must belong to the declared physical process table')
            policy[key]=sorted(set(processes))
        self.routing_policy=policy;self.routing_calls=Counter();self.routing_eta_calls=Counter();self.routing_free_calls=Counter()
        self.trace['provenance']['scoped_routing']=dict(enabled=self.routing_scoped,**policy)

    def choose_machine(self,part):
        if not self.routing_scoped:return super().choose_machine(part)
        step=self.next_step(part)
        if step is None:return super().choose_machine(part)
        process=step['process'];eta=process in self.routing_policy['eta_processes']
        free=process in self.routing_policy['free_buffer_processes']
        self.routing_calls[process]+=1
        if eta:self.routing_eta_calls[process]+=1
        if free:self.routing_free_calls[process]+=1
        original=self.weights
        self.weights=dict(original,routing_estimate_finish=eta,routing_free_buffers=free)
        try:return super().choose_machine(part)
        finally:self.weights=original

    def finish(self):
        super().finish()
        self.trace.setdefault('algorithm_audit',{})['scoped_routing']=dict(enabled=self.routing_scoped,
            policy=deepcopy(self.routing_policy),calls=dict(self.routing_calls),
            eta_calls=dict(self.routing_eta_calls),free_buffer_calls=dict(self.routing_free_calls),
            scope='Existing public-state ETA score only; actual tool, calendar, transport and process checks unchanged')


class RoutingFactory(RoutingMixin,KitToolingSpecialistFactory):pass
class AdmissionRoutingFactory(AdmissionMixin,RoutingFactory):pass


def run(instance,weights=None,controller=None,*,routing_policy=None,tool_policy=None,
        kit_reservation=True,admission=False):
    cls=AdmissionRoutingFactory if admission else RoutingFactory
    return cls(instance,weights,controller,routing_policy=routing_policy,
        tool_policy=tool_policy,kit_reservation=kit_reservation).run()


def prepare_tasks(teacher_path):
    teacher_path=Path(teacher_path).resolve();teacher=json.loads(teacher_path.read_text())
    if teacher.get('policy_selection_role')!='training_only_last_update' or set(teacher.get('train_seeds',[]))-set(range(32)):
        raise ValueError('The routing probe requires a training-only selected teacher')
    current=hashes()
    physical=('stage2/engine.py','stage2/spec.py','stage2/check.py','instances/stage2/metaltech_pressure.json')
    for name in physical:
        if teacher['source_hashes'].get(name)!=current[name]:raise ValueError('Routing teacher physical source mismatch: '+name)
    # Dispatch has a later calendar-aware opt-in extension. The campaign uses
    # selector=priority and never calls its QUBO branch; disclose both digests.
    scopes={'none':[],'QA':['QA'],'QA+ASSEMBLY':['QA','ASSEMBLY'],'T+F':['T','F'],
        'all':['T','F','S','WASH','HEAT','QA','ASSEMBLY']}
    tasks=[]
    for orders,wip,guard in ((12,8,4),(16,4,0)):
        index=next(i for i,c in enumerate(teacher['configs']) if c==dict(orders=orders,horizon=5760,profile='full'))
        weights=dict(teacher['actions'][teacher['policy']['actions'][index]]['weights'],
            wip_limit=wip,qa_guard_threshold=guard,worker_calendar=True,preposition=False,
            admission_rule='family',selector='priority',routing_estimate_finish=False,routing_free_buffers=False)
        for name,processes in scopes.items():
            for free in (False,True):
                policy=dict(eta_processes=processes,free_buffer_processes=['QA'] if free else [])
                for seed in range(8):
                    tasks.append(dict(task_id=len(tasks),policy_id=name+'-freeQA'+str(int(free)),
                        config=dict(orders=orders,horizon=5760,profile='full'),seed=seed,weights=weights,
                        routing_policy=policy,tool_policy=dict(mode='hard'),kit_reservation=True,admission=True))
    return tasks,dict(path=str(teacher_path),sha256=hashlib.sha256(teacher_path.read_bytes()).hexdigest(),
        prior_source_hashes=teacher['source_hashes'],prior_training_wall_seconds=teacher.get('actual_wall_seconds'),
        prior_fit_episodes=teacher.get('fit_episodes'),role='TRAIN0–7 routing ablation, no held-out claim',
        dispatch_difference='Later dispatch opt-in extension does not execute under fixed priority selector')


def simulate(task):
    from .spec import build
    from .check import check_trace
    started=time.perf_counter();cpu=time.process_time();trace=None
    result={key:task[key] for key in ('task_id','policy_id','config','seed','weights','routing_policy')}
    try:
        assert_sources(task['source_hashes']);instance=build(**task['config'],seed=task['seed'])
        result['physical_instance_sha256']=hashlib.sha256(json.dumps(instance,sort_keys=True).encode()).hexdigest()
        trace=run(instance,task['weights'],routing_policy=task['routing_policy'],tool_policy=task['tool_policy'],
            kit_reservation=task['kit_reservation'],admission=task['admission'])
        checked=check_trace(trace)
        result.update(valid=checked['valid'],issues=checked['issues'],metrics=trace['metrics'],
            routing_audit=trace['algorithm_audit']['scoped_routing'])
        assert_sources(task['source_hashes'])
    except Exception as exc:result.update(valid=False,error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
    if trace is not None and (task['seed']==0 or not result['valid']):
        path=Path(task['output'])/f"trace-n{task['config']['orders']}-{task['policy_id']}-s{task['seed']}.json.gz"
        payload=json.dumps(trace,separators=(',',':')).encode();path.write_bytes(gzip.compress(payload,mtime=0))
        result.update(trace_path=str(path),trace_sha256=hashlib.sha256(payload).hexdigest())
    result.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu)
    return result


def campaign(teacher_path,output,workers=2,prepare_only=False):
    if not 1<=workers<=2:raise ValueError('Bounded local experiment permits at most two workers')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    sources=hashes();tasks,teacher=prepare_tasks(teacher_path)
    for task in tasks:task.update(source_hashes=sources,output=str(output))
    for name in SOURCE_NAMES:
        path=output/'source_snapshot'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
    protocol=dict(schema='stage2-scoped-routing-training.v1',source_hashes=sources,teacher=teacher,tasks=tasks,
        seeds=list(range(8)),role='TRAIN only; final and validation tapes untouched',workers=workers,
        physical_model='Unchanged numerical instance; public-state ETA reused as causal ranking heuristic')
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    if prepare_only:return protocol
    started=time.perf_counter();rows=[]
    with (output/'rows.jsonl').open('x') as log:
        if workers==1:
            for task in tasks:
                row=simulate(task);rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
        else:
            with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool:
                futures={pool.submit(simulate,t):t for t in tasks}
                for future in as_completed(futures):
                    task=futures[future]
                    try:row=future.result()
                    except Exception as exc:row=dict(task_id=task['task_id'],policy_id=task['policy_id'],config=task['config'],seed=task['seed'],valid=False,error=str(exc))
                    rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
    assert_sources(sources);summary=[]
    for orders in (12,16):
        for policy in sorted({r['policy_id'] for r in rows}):
            selected=[r for r in rows if r['config']['orders']==orders and r['policy_id']==policy]
            row=dict(orders=orders,policy_id=policy,episodes=len(selected),invalid=sum(not r['valid'] for r in selected))
            if len(selected)==8 and not row['invalid']:
                row.update(shipped=sum(r['metrics']['shipped'] for r in selected),orders_total=sum(r['metrics']['orders'] for r in selected),
                    complete=sum(r['metrics']['all_orders_fulfilled'] for r in selected),
                    mean_unfulfilled=sum(r['metrics']['orders']-r['metrics']['shipped'] for r in selected)/8,
                    mean_tardiness=sum(r['metrics']['total_tardiness_ticks'] for r in selected)/8,
                    mean_cost=sum(r['metrics']['total_cost'] for r in selected)/8)
            summary.append(row)
    report=dict(schema=protocol['schema'],source_hashes=sources,teacher=teacher,summary=summary,
        rows=sorted(rows,key=lambda r:r['task_id']),wall_seconds=time.perf_counter()-started,
        actual_cpu_seconds=sum(r.get('cpu_seconds',0) for r in rows),
        final_tapes_executed=0,validation_tapes_executed=0)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--teacher',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--workers',type=int,default=2);p.add_argument('--prepare-only',action='store_true')
    a=p.parse_args();report=campaign(a.teacher,a.output,a.workers,a.prepare_only)
    print(json.dumps({key:report[key] for key in ('summary','wall_seconds') if key in report},indent=2))


if __name__=='__main__':main()
