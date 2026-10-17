"""Predeclared strong static-control factorial, guarded and TRAIN-only.

Two balanced16-tape phases preserve a fair fallback if the fixed wall cap binds.
No reward override, online adaptation, physical change, or final tape access.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
import gzip
import hashlib
import itertools
import json
import multiprocessing
from pathlib import Path
import time
import traceback

from .completion_policy import AdmissionCompletionFactory,SOURCES as COMPLETION_SOURCES
from .maintenance_guard import MaintenanceOutageGuardMixin
from .bom_probe import flow_metrics
from .recovery_routing import BASE_WEIGHTS,ROOT

SOURCES=('stage2/static_control.py','stage2/maintenance_guard.py')+COMPLETION_SOURCES


class GuardedCompletionFactory(MaintenanceOutageGuardMixin,AdmissionCompletionFactory):pass


def hashes():return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def policies(contexts=(12,16,24)):
    result=[]
    for orders in contexts:
        if orders not in (12,16,24):raise ValueError('Only declared n12/n16/n24 contexts')
        for wip,qa_guard,mode,qa_route,credit,bom in itertools.product((4,6,8),(0,4),('eco','standard','turbo'),(False,True),(0,270),(False,True) if orders==24 else (False,)):
            weights=dict(BASE_WEIGHTS,wip_limit=wip,qa_guard_threshold=qa_guard,mode=mode,policy_seed=0,bom_priority=False)
            if orders in (16,24):weights.update(due=1.,family=0.,tool_distance=1 if orders==16 else 8)
            if bom:weights.update(bom_priority='join',bom_join_weight=6,bom_progress_weight=1)
            options=dict(tool_policy={'mode':'hard'},kit_reservation=orders!=24,recovery_policy={'enabled':True},
                routing_policy={'eta_processes':['QA'] if qa_route else [],'free_buffer_processes':[]},
                completion_policy={'credit_minutes':credit,'reclaim_dead_slots':False},maintenance_outage_guard=True)
            original=(wip==(8 if orders==12 else 4) and qa_guard==4 and mode=='standard' and not qa_route and credit==0 and not bom)
            result.append(dict(policy_id=f'n{orders}-w{wip}-g{qa_guard}-{mode}-QA{int(qa_route)}-credit{credit}-join{int(bom)}',
                config=dict(orders=orders,horizon=5760,profile='full'),weights=weights,solver_options=options,original_prior=original))
    return result


def tasks(contexts=(12,16,24),seeds=range(32)):
    declared=[]
    for seed in seeds:
        if seed not in range(32):raise ValueError('TRAIN0–31 only')
        for policy in policies(contexts):
            task=deepcopy(policy);task['task_id']=len(declared);task['config']['seed']=seed
            task['seed_role']='TRAIN static-control predeclared factorial';task['retain_trace']=seed==0;declared.append(task)
    return declared


def validate_tasks(declared):
    if not declared:raise ValueError('Explicit TRAIN static-control task list required')
    known={p['policy_id']:p for p in policies()};seen=set()
    for task in declared:
        seed=task['config']['seed'];policy=known.get(task['policy_id'])
        if seed not in range(32) or not task['seed_role'].startswith('TRAIN static-control') or policy is None:raise ValueError('Outside declared TRAIN factorial')
        if task['weights']!=policy['weights'] or task['solver_options']!=policy['solver_options'] or {k:v for k,v in task['config'].items() if k!='seed'}!=policy['config']:
            raise ValueError('Task differs from the fixed factorial; guard must remain ON,no reward/reclaim')
        key=(task['policy_id'],seed)
        if key in seen:raise ValueError('Duplicate static-control policy/tape')
        seen.add(key)
    for policy in {t['policy_id'] for t in declared}:
        if {t['config']['seed'] for t in declared if t['policy_id']==policy}!=set(range(32)):
            raise ValueError('Every declared policy must contain the same32 TRAIN tapes')


def simulate(task):
    from .spec import build
    from .check import check_trace
    started=time.perf_counter();cpu=time.process_time();factory=None;trace=None
    row={key:deepcopy(task[key]) for key in ('task_id','policy_id','config','weights','solver_options','original_prior','seed_role')}
    try:
        if task['config']['seed'] not in range(32) or not task['solver_options'].get('maintenance_outage_guard',False):raise ValueError('TRAIN only and explicit guard ON')
        if hashes()!=task['source_hashes']:raise RuntimeError('Static-control source drift before episode')
        instance=build(**task['config']);factory=GuardedCompletionFactory(instance,task['weights'],**task['solver_options']);trace=factory.run()
        checked=check_trace(trace,instance);mismatch=[d['tick'] for d in trace['qubo_decisions'] if sorted(d['result']['selected'])!=sorted(d['committed'])]
        row.update(valid=checked['valid'] and not mismatch,issues=checked['issues'],decode_mismatches=mismatch,
            metrics=trace['metrics'],flow=flow_metrics(trace),guard=trace['algorithm_audit']['maintenance_outage_guard'],
            credited_units=len(trace['algorithm_audit']['completion_policy']['credited_units']),
            physical_instance_sha256=hashlib.sha256(json.dumps(instance,sort_keys=True).encode()).hexdigest())
        if hashes()!=task['source_hashes']:raise RuntimeError('Static-control source drift after episode')
    except Exception as exc:
        row.update(valid=False,error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
        if factory is not None:trace=factory.trace
    if trace is not None and (task.get('retain_trace',False) or not row['valid']):
        payload=json.dumps(trace,separators=(',',':')).encode();path=Path(task['output'])/f"trace-task{task['task_id']}.json.gz"
        path.write_bytes(gzip.compress(payload,mtime=0));row.update(trace_path=str(path),trace_sha256=hashlib.sha256(payload).hexdigest())
    row.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu);return row


def summarize(rows,scope):
    groups=defaultdict(list)
    for row in rows:groups[(row['config']['orders'],row['policy_id'])].append(row)
    summary=[]
    for (orders,policy),all_rows in sorted(groups.items()):
        used=[r for r in all_rows if r['config']['seed']<scope]
        entry=dict(orders=orders,policy_id=policy,runs=len(used),expected_runs=scope,all_observed_invalid=sum(not r['valid'] for r in all_rows),
            original_prior=all_rows[0]['original_prior'],eligible=len(used)==scope and all(r['valid'] for r in all_rows),
            weights=all_rows[0]['weights'],solver_options=all_rows[0]['solver_options'])
        if entry['eligible']:entry.update(shipped=sum(r['metrics']['shipped'] for r in used),required=sum(r['metrics']['orders'] for r in used),
            missing=sum(r['metrics']['orders']-r['metrics']['shipped'] for r in used),complete=sum(r['metrics']['all_orders_fulfilled'] for r in used),
            total_tardiness=sum(r['metrics']['total_tardiness_ticks'] for r in used),total_cost=sum(r['metrics']['total_cost'] for r in used))
        summary.append(entry)
    candidates=[]
    for orders in sorted({x['orders'] for x in summary}):
        ordered=sorted((s for s in summary if s['orders']==orders and s['eligible']),key=lambda x:(x['missing'],x['total_tardiness'],x['total_cost'],x['policy_id']))
        priors=[s for s in summary if s['orders']==orders and s['original_prior']]
        candidates.append(dict(orders=orders,best=ordered[0] if ordered else None,top3=ordered[:3],original_priors=priors,
            selection='TRAIN-only; eligible complete balanced scopes,zero observed invalids,lex missing before debt/cost; candidates require reused validation'))
    return summary,candidates


def campaign(output,declared,workers=32,max_seconds=1740):
    declared=deepcopy(declared);validate_tasks(declared)
    if workers<1 or max_seconds<60 or max_seconds>1740:raise ValueError('Positive workers and60–1740second cap required')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False);sources=hashes()
    for task in declared:task.update(source_hashes=sources,output=str(output))
    for name in SOURCES:
        path=output/'source_snapshot'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
    protocol=dict(schema='stage2-strong-static-control.v1',source_hashes=sources,tasks=declared,workers=workers,max_seconds=max_seconds,
        phases=[list(range(16)),list(range(16,32))],fallback='Balanced first16 if measured phase1 forecast does not fit; all extra/invalid rows retained and any known invalid disqualifies its policy',
        scope='Predeclared TRAIN factorial,guard ON,no reward override,reclaim OFF,no validation/final',final_tapes=0,
        selection='Missing orders before total deadline debt before cost; original priors retained even outside top3')
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');started=time.perf_counter();rows=[];completed_phases=[];reason=None
    with (output/'rows.jsonl').open('x') as log,ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool:
        for phase in (0,1):
            elapsed=time.perf_counter()-started
            if phase==1 and elapsed*2.25+60>max_seconds:
                reason='Phase1 measured elapsed plus1.25x remaining forecast exceeds cap';break
            phase_tasks=[t for t in declared if (t['config']['seed']<16)==(phase==0)];done=0
            batch_size=workers*4
            for offset in range(0,len(phase_tasks),batch_size):
                if time.perf_counter()-started>=max_seconds-60:
                    reason='Fixed wall cap guard reached; selection uses completed balanced first16';break
                batch=phase_tasks[offset:offset+batch_size]
                for row in pool.map(simulate,batch):rows.append(row);log.write(json.dumps(row)+'\n');done+=1
                log.flush()
            if done==len(phase_tasks):completed_phases.append(phase)
            else:break
    scope=32 if completed_phases==[0,1] else (16 if completed_phases==[0] else 0)
    summary,candidates=summarize(rows,scope) if scope else ([],[])
    result=dict(**protocol,rows=sorted(rows,key=lambda r:r['task_id']),summary=summary,candidates=candidates,selected_train_tapes=scope,
        completed_phases=completed_phases,stop_reason=reason,wall_seconds=time.perf_counter()-started,
        cpu_seconds=sum(r.get('cpu_seconds',0) for r in rows),source_stable=hashes()==sources)
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    (output/'training-candidates.json').write_text(json.dumps(dict(source_hashes=sources,selected_train_tapes=scope,candidates=candidates,
        role='TRAIN-selected static candidates; not validation/final winner'),indent=2)+'\n');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tasks',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--workers',type=int,default=32);p.add_argument('--max-seconds',type=int,default=1740);a=p.parse_args()
    r=campaign(a.output,json.loads(a.tasks.read_text()),a.workers,a.max_seconds)
    print(json.dumps(dict(selected_train_tapes=r['selected_train_tapes'],wall_seconds=r['wall_seconds'],candidates=r['candidates'],invalid=sum(not x['valid'] for x in r['rows'])),indent=2))


if __name__=='__main__':main()
