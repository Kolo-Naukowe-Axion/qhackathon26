"""Lineage-aware pump completion credit and observed-dead admission reclaim.

Both controls are off by default. No order/part/objective is erased; physical
inventory, movement, inspection and replacement limits are unchanged.
"""
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

from .admission import AdmissionMixin,AdmissionSet
from .bom_probe import flow_metrics,SOURCES as AUDIT_SOURCES
from .recovery_routing import RecoveryRoutingFactory,BASE_WEIGHTS,ROOT,terminal_diagnosis

SOURCES=('stage2/completion_policy.py',)+AUDIT_SOURCES


class ReclaimAdmissionSet(AdmissionSet):
    """Scheduling slots only. Base deepcopy preserves the factory reference."""
    def difference_update(self,values):
        super().difference_update(values)
        factory=self.factory
        dead=factory.observed_unrecoverable_orders()
        for oid,reason in dead.items():
            if oid in factory.retired_orders:continue
            occupied=len(self);was_admitted=oid in self
            pending=[o['id'] for o in factory.orders.values() if o['id'] not in self and o['id'] not in factory.shipped
                and o['id'] not in dead and o['release_tick']<=factory.t]
            factory.retired_orders[oid]=dict(tick=factory.t,reason=reason,reclaimed_admitted_slot=was_admitted,
                occupied_before=occupied,wip_limit=int(factory.weights.get('wip_limit',6)),
                released_pending_orders=sorted(pending),blocked_admission_evidence=was_admitted and
                occupied>=int(factory.weights.get('wip_limit',6)) and bool(pending))
            self.discard(oid)

    def update(self,values):
        factory=self.factory;original=factory.orders
        factory.orders={oid:o for oid,o in original.items() if oid not in factory.retired_orders}
        try:
            if factory.weights.get('admission_rule','due')=='due':
                slots=max(0,int(factory.weights.get('wip_limit',6))-len(self))
                head=sorted((o for o in factory.orders.values() if o['id'] not in self and o['id'] not in factory.shipped),
                    key=lambda o:(o['due_tick'],o['release_tick'],o['id']))[:slots]
                return set.update(self,(o['id'] for o in head if o['release_tick']<=factory.t))
            return super().update(oid for oid in values if oid not in factory.retired_orders)
        finally:factory.orders=original


class CompletionMixin:
    def __init__(self,*args,completion_policy=None,**kwargs):
        policy=dict(credit_minutes=0.,reclaim_dead_slots=False)
        if completion_policy:policy.update(completion_policy)
        if set(policy)!={'credit_minutes','reclaim_dead_slots'} or policy['credit_minutes']<0:
            raise ValueError('Unknown/invalid completion policy')
        if type(policy['reclaim_dead_slots']) is not bool:raise ValueError('Reclaim flag must be explicit boolean')
        super().__init__(*args,**kwargs)
        self.completion_policy=policy;self.retired_orders={};self.completion_credits={}
        self._lineage_key=None;self._lineage={};self._dead_key=None;self._dead={}
        if policy['reclaim_dead_slots']:
            if not isinstance(self.admitted,AdmissionSet):raise ValueError('Dead-slot reclaim requires explicit admission backend')
            prior=self.admitted;self.admitted=ReclaimAdmissionSet(self,prior);self.admitted.history=deepcopy(prior.history)

    def pump_lineage(self):
        key=len(self.trace['operations'])
        if key!=self._lineage_key:
            self._lineage={uid:tuple(op['parent_unit_ids']) for op in self.trace['operations']
                if op['kind']=='process' and op['process']=='ASSEMBLY' and op['parent_unit_ids'] and not op['is_rework']
                for uid in op['unit_ids']}
            self._lineage_key=key
        return self._lineage

    def completion_credit(self,part):
        if self.completion_policy['credit_minutes']==0 or part['recipe']!='pump' or part['status'] in ('scrap','disposed','shipped'):
            return 0.
        parents=self.pump_lineage().get(part['id'],())
        if len(parents)!=3 or len(set(parents))!=3:return 0.
        pieces=[self.parts[uid] for uid in parents]
        if {p['recipe'] for p in pieces}!={'housing','rotor','flange'} or any(p['status']!='consumed' for p in pieces):return 0.
        if any(p['order_id']!=part['order_id'] for p in pieces):return 0.
        return max(0,float(self.weights.get('due',1)))*self.completion_policy['credit_minutes']/(self.i['tick_minutes']*self.i.get('time_scale',1))

    def priority(self,part):
        base=super().priority(part);credit=self.completion_credit(part)
        if credit:
            item=self.completion_credits.setdefault(part['id'],dict(first_tick=self.t,last_tick=self.t,
                evaluations=0,distinct_priority_ticks=0,credit_score=credit,parents=list(self.pump_lineage()[part['id']])))
            item['evaluations']+=1
            if item['evaluations']==1 or item['last_tick']!=self.t:item['distinct_priority_ticks']+=1
            item['last_tick']=self.t
        return base-credit

    def observed_unrecoverable_orders(self):
        key=(len(self.trace['events']),len(self.parts))
        if key==self._dead_key:return self._dead
        grouped=defaultdict(list)
        for part in self.parts.values():grouped[part['order_id']].append(part)
        result={}
        for oid,parts in grouped.items():
            if oid in self.shipped:continue
            pumps=[p for p in parts if p['recipe']=='pump']
            if any(p['status'] not in ('scrap','disposed') for p in pumps):continue
            if pumps:
                result[oid]='Observed final pump scrap; frozen factory has no pump replacement';continue
            for recipe in ('housing','rotor','flange'):
                components=[p for p in parts if p['recipe']==recipe]
                if components and all(p['status'] in ('scrap','disposed') for p in components) and any(p.get('replacement',0)>=1 for p in components):
                    result[oid]=f'Observed exhausted {recipe} replacement; no live/unreleased alternative component';break
        self._dead_key=key;self._dead=result;return result

    def finish(self):
        super().finish()
        self.trace.setdefault('algorithm_audit',{})['completion_policy']=dict(policy=deepcopy(self.completion_policy),
            credited_units=deepcopy(self.completion_credits),retired_orders=deepcopy(self.retired_orders),
            scope='Causal scheduling credit/reclaim only; all orders,parts and unfulfilled debt remain in physical state/objective',
            call_count_caution='Credit evaluations/distinct priority ticks are not committed decisions or total waiting time')


class CompletionFactory(CompletionMixin,RecoveryRoutingFactory):pass
class AdmissionCompletionFactory(CompletionMixin,AdmissionMixin,RecoveryRoutingFactory):pass


def run(instance,weights=None,controller=None,*,admission=False,**options):
    cls=AdmissionCompletionFactory if admission else CompletionFactory
    return cls(instance,weights,controller,**options).run()


def hashes():return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def diagnostic_tasks():
    tasks=[]
    for orders in (12,16,24):
        base=dict(BASE_WEIGHTS,policy_seed=7);qa=False
        if orders in (16,24):base.update(wip_limit=4,due=1.,family=0.,tool_distance=1 if orders==16 else 8)
        if orders==16:qa=True
        if orders==24:base.update(bom_priority='join',bom_join_weight=6,bom_progress_weight=1)
        for credit in (0,270):
            for reclaim in (False,True):
                for seed in list(range(8))+([15] if orders==12 else []):
                    tasks.append(dict(task_id=len(tasks),policy_id=f'credit{credit}-reclaim{int(reclaim)}',
                        config=dict(orders=orders,horizon=5760,profile='full',seed=seed),weights=dict(base),
                        solver_options=dict(admission=True,tool_policy={'mode':'hard'},kit_reservation=orders!=24,
                            recovery_policy={'enabled':True},routing_policy={'eta_processes':['QA'] if qa else [],'free_buffer_processes':[]},
                            completion_policy=dict(credit_minutes=credit,reclaim_dead_slots=reclaim)),
                        seed_role='TRAIN0–7 plus diagnosed n12seed15; structural2x2 ablation',retain_trace=seed in (0,15)))
    return tasks


def simulate(task):
    from .spec import build
    from .check import check_trace
    start=time.perf_counter();cpu=time.process_time();trace=None;factory=None
    row={key:deepcopy(task[key]) for key in ('task_id','policy_id','config','weights','solver_options','seed_role')}
    try:
        if task['config']['seed'] not in range(32):raise ValueError('TRAIN0–31 only')
        if hashes()!=task['source_hashes']:raise RuntimeError('Source drift before episode')
        instance=build(**task['config']);options=deepcopy(task['solver_options']);cls=AdmissionCompletionFactory if options.pop('admission',False) else CompletionFactory
        factory=cls(instance,task['weights'],**options);trace=factory.run();checked=check_trace(trace)
        mismatch=[d['tick'] for d in trace['qubo_decisions'] if sorted(d['result']['selected'])!=sorted(d['committed'])]
        row.update(valid=checked['valid'] and not mismatch,issues=checked['issues'],decode_mismatches=mismatch,
            metrics=trace['metrics'],flow=flow_metrics(trace),diagnosis=terminal_diagnosis(factory),
            completion_audit=trace['algorithm_audit']['completion_policy'],
            observed_unrecoverable_orders=factory.observed_unrecoverable_orders(),
            physical_instance_sha256=hashlib.sha256(json.dumps(instance,sort_keys=True).encode()).hexdigest())
        if hashes()!=task['source_hashes']:raise RuntimeError('Source drift after episode')
    except Exception as exc:
        row.update(valid=False,error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
        if factory is not None:trace=factory.trace
    if trace is not None and (task.get('retain_trace',False) or not row['valid']):
        payload=json.dumps(trace,separators=(',',':')).encode();path=Path(task['output'])/f"trace-task{task['task_id']}.json.gz"
        path.write_bytes(gzip.compress(payload,mtime=0));row.update(trace_path=str(path),trace_sha256=hashlib.sha256(payload).hexdigest())
    row.update(wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu);return row


def campaign(output,tasks=None,workers=2):
    tasks=deepcopy(diagnostic_tasks() if tasks is None else tasks)
    if workers<1 or any(t['config']['seed'] not in range(32) for t in tasks):raise ValueError('Positive workers and TRAIN0–31 required')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False);sources=hashes()
    for task in tasks:task.update(source_hashes=sources,output=str(output))
    for name in SOURCES:
        path=output/'source_snapshot'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
    protocol=dict(schema='stage2-completion-policy.v1',source_hashes=sources,tasks=tasks,workers=workers,
        scope='TRAIN-only lineage completion-credit x observed-dead-slot reclaim; no physical/order/objective deletion',
        precheck='n12seed15 scrap occurs after all orders admitted with3/8 slots occupied; no dead-pump scrap in n16/n24 TRAIN0–7 controls',validation_tapes=0,final_tapes=0)
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter();rows=[]
    with (output/'rows.jsonl').open('x') as log:
        with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool:
            pending={pool.submit(simulate,t):t for t in tasks}
            for future in as_completed(pending):
                task=pending[future]
                try:row=future.result()
                except Exception as exc:row=dict(task_id=task['task_id'],policy_id=task['policy_id'],config=task['config'],valid=False,error=str(exc))
                rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
    groups=defaultdict(list)
    for row in rows:groups[(row['config']['orders'],row['policy_id'])].append(row)
    summary=[]
    for (orders,policy),rs in sorted(groups.items()):
        entry=dict(orders=orders,policy_id=policy,runs=len(rs),invalid=sum(not r['valid'] for r in rs),seeds=sorted(r['config']['seed'] for r in rs))
        if not entry['invalid']:entry.update(shipped=sum(r['metrics']['shipped'] for r in rs),required=sum(r['metrics']['orders'] for r in rs),
            complete=sum(r['metrics']['all_orders_fulfilled'] for r in rs),total_tardiness=sum(r['metrics']['total_tardiness_ticks'] for r in rs),
            retired_orders=sum(len(r['completion_audit']['retired_orders']) for r in rs),
            observed_blocking_dead_slots=sum(v['blocked_admission_evidence'] for r in rs for v in r['completion_audit']['retired_orders'].values()))
        summary.append(entry)
    result=dict(**protocol,rows=sorted(rows,key=lambda r:r['task_id']),summary=summary,wall_seconds=time.perf_counter()-start,
        cpu_seconds=sum(r.get('cpu_seconds',0) for r in rows),source_stable=hashes()==sources)
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--tasks',type=Path);p.add_argument('--workers',type=int,default=2);a=p.parse_args()
    result=campaign(a.output,json.loads(a.tasks.read_text()) if a.tasks else None,a.workers)
    print(json.dumps({k:result[k] for k in ('summary','wall_seconds','source_stable')},indent=2))


if __name__=='__main__':main()
