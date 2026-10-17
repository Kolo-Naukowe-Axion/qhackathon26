"""One bounded release-aware FAMILY-admission ablation, default off."""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor,as_completed
from copy import deepcopy
import gzip
import hashlib
import json
import multiprocessing
from pathlib import Path
import time
import traceback

from .admission import AdmissionSet
from .static_control import GuardedCompletionFactory,policies,SOURCES as STATIC_SOURCES
from .recovery_routing import ROOT

SOURCES=('stage2/release_admission.py',)+STATIC_SOURCES


class ReleasedFamilyAdmissionSet(AdmissionSet):
    def update(self,values):
        f=self.factory
        if f.weights.get('admission_rule','due')!='family':return super().update(values)
        original=f.orders
        # Existing admitted orders remain visible even if a caller manually
        # installed an unreleased one. Only admission's temporary view changes.
        public={oid:o for oid,o in original.items() if o['release_tick']<=f.t or oid in self}
        f.release_admission_audit['calls']+=1
        f.release_admission_audit['excluded_future_order_views']+=len(original)-len(public)
        try:
            f.orders=public
            return super().update(values)
        finally:f.orders=original


class ReleaseAwareMixin:
    def __init__(self,*args,release_aware_admission=False,**kwargs):
        if type(release_aware_admission) is not bool:raise ValueError('Explicit boolean release-aware admission required')
        super().__init__(*args,**kwargs)
        self.release_aware_admission=release_aware_admission
        if release_aware_admission:
            if self.weights.get('admission_rule','due')!='family':raise ValueError('Release-aware ablation is FAMILY only')
            if self.completion_policy.get('reclaim_dead_slots',False):raise ValueError('Dead-slot reclaim composition is not audited')
            previous=self.admitted;self.admitted=ReleasedFamilyAdmissionSet(self,previous)
            self.admitted.history=deepcopy(previous.history)
            self.release_admission_audit=dict(enabled=True,calls=0,excluded_future_order_views=0,
                semantics='Family head among publicly released orders only; admitted slots and every physical order/unit retained')

    def finish(self):
        super().finish()
        if self.release_aware_admission:self.trace['algorithm_audit']['release_aware_admission']=deepcopy(self.release_admission_audit)


class ReleaseAwareFactory(ReleaseAwareMixin,GuardedCompletionFactory):pass


def hashes():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES}


def tasks():
    result=[]
    for n in (12,16):
        policy=next(p for p in policies((n,)) if p['weights']['wip_limit']==(8 if n==12 else 6)
            and p['weights']['qa_guard_threshold']==4 and p['weights']['mode']=='standard'
            and not p['solver_options']['routing_policy']['eta_processes']
            and p['solver_options']['completion_policy']['credit_minutes']==0)
        for seed in range(32):
            for enabled in (False,True):
                t=deepcopy(policy);t['task_id']=len(result);t['config']['seed']=seed;t['solver_options']['release_aware_admission']=enabled
                t['policy_id']=f'n{n}-releaseaware{int(enabled)}';t['seed_role']='TRAIN0–31 paired released-family admission; no validation/final';t['retain_trace']=seed==0;result.append(t)
    return result


def validate_tasks(declared):
    expected={t['task_id']:t for t in tasks()}
    if len(declared)!=128:raise ValueError('Exactly128 declared paired TRAIN episodes required')
    if len({t['task_id'] for t in declared})!=128:raise ValueError('Duplicate TRAIN task')
    for t in declared:
        if t!=expected.get(t['task_id']):raise ValueError('Only the predeclared TRAIN family-release experiment is allowed')


def simulate(task):
    from .spec import build
    from .check import check_trace
    from .bom_probe import flow_metrics
    started=time.perf_counter();cpu=time.process_time();f=None;trace=None
    row={k:deepcopy(task[k]) for k in ('task_id','policy_id','config','weights','solver_options','seed_role')}
    try:
        if hashes()!=task['source_hashes']:raise RuntimeError('Source drift before release-admission episode')
        instance=build(**task['config']);f=ReleaseAwareFactory(instance,task['weights'],**task['solver_options']);trace=f.run();checked=check_trace(trace,instance)
        mismatch=[d['tick'] for d in trace['qubo_decisions'] if sorted(d['result']['selected'])!=sorted(d['committed'])]
        row.update(valid=checked['valid'] and not mismatch,issues=checked['issues'],decode_mismatches=mismatch,metrics=trace['metrics'],flow=flow_metrics(trace),
            physical_instance_sha256=hashlib.sha256(json.dumps(instance,sort_keys=True).encode()).hexdigest(),admission_history=trace['admission_history'],
            release_admission_audit=trace['algorithm_audit'].get('release_aware_admission'),
            setup_minutes=sum(op['setup_ticks'] for op in trace['operations'])*instance['tick_minutes'],
            batched_operations=sum(op['kind']=='process' and len(op['unit_ids'])>1 for op in trace['operations']))
        if hashes()!=task['source_hashes']:raise RuntimeError('Source drift after release-admission episode')
    except Exception as exc:
        row.update(valid=False,error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
        if f is not None:trace=f.trace
    if trace is not None and (task.get('retain_trace') or not row['valid']):
        payload=json.dumps(trace,separators=(',',':')).encode();p=Path(task['output'])/f"trace-task{task['task_id']}.json.gz";p.write_bytes(gzip.compress(payload,mtime=0));row.update(trace_path=str(p),trace_sha256=hashlib.sha256(payload).hexdigest())
    row.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu);return row


def campaign(output,workers=32):
    declared=tasks();validate_tasks(declared);output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False);source=hashes()
    for t in declared:t.update(source_hashes=source,output=str(output))
    for n in SOURCES:
        p=output/'source_snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    protocol=dict(schema='stage2-released-family-admission.v1',tasks=declared,source_hashes=source,workers=workers,scope='One128-run TRAIN-only ablation; no thresholds,no validation,no final',criterion='Unfulfilled orders primary; retain setup/batching/debt/cost regressions; stop if no primary gain')
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[];start=time.perf_counter()
    with (output/'rows.jsonl').open('x') as log,ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool:
        pending={pool.submit(simulate,t):t for t in declared}
        for future in as_completed(pending):
            task=pending[future]
            try:r=future.result()
            except Exception as exc:r=dict(task_id=task['task_id'],policy_id=task['policy_id'],config=task['config'],valid=False,error=str(exc))
            rows.append(r);log.write(json.dumps(r)+'\n');log.flush()
    grouped=defaultdict(list)
    for r in rows:grouped[(r['config']['orders'],r['policy_id'])].append(r)
    summary=[]
    for (n,pid),rs in sorted(grouped.items()):
        e=dict(orders=n,policy_id=pid,runs=len(rs),invalid=sum(not r['valid'] for r in rs))
        if not e['invalid']:e.update(shipped=sum(r['metrics']['shipped'] for r in rs),required=sum(r['metrics']['orders'] for r in rs),complete=sum(r['metrics']['all_orders_fulfilled'] for r in rs),tardiness=sum(r['metrics']['total_tardiness_ticks'] for r in rs),cost=sum(r['metrics']['total_cost'] for r in rs),setup_minutes=sum(r['setup_minutes'] for r in rs),batched_operations=sum(r['batched_operations'] for r in rs))
        summary.append(e)
    result=dict(**protocol,rows=sorted(rows,key=lambda r:r['task_id']),summary=summary,wall_seconds=time.perf_counter()-start,cpu_seconds=sum(r.get('cpu_seconds',0) for r in rows),source_stable=hashes()==source)
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--workers',type=int,default=32);a=p.parse_args()
    if a.workers<1:raise ValueError('Positive workers required')
    r=campaign(a.output,a.workers);print(json.dumps(dict(summary=r['summary'],wall_seconds=r['wall_seconds']),indent=2))


if __name__=='__main__':main()
