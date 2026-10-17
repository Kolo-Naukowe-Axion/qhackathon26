"""Explicit reused-VALIDATION overlay; held TRAIN driver remains unchanged.

Only tapes100–115 are allowed. This is model selection, not the reserved final
evaluation. No training, reward change or implicit maintenance guard is added.
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

from .completion_policy import AdmissionCompletionFactory,SOURCES as COMPLETION_SOURCES
from .bom_probe import flow_metrics
from .recovery_routing import ROOT,terminal_diagnosis

SOURCES=('stage2/completion_validation.py',)+COMPLETION_SOURCES


def hashes():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES}


def tasks(completion_templates,bom_templates):
    """Template artifacts were selected on TRAIN, before this comparison."""
    completion=json.loads(Path(completion_templates).read_text());bom=json.loads(Path(bom_templates).read_text());out=[]
    choices=[]
    for n in (12,24):
        for credit in (0,270):
            choices.append(next(t for t in completion if t['config']['orders']==n and t['config']['seed']==0 and
                t['solver_options']['completion_policy']==dict(credit_minutes=credit,reclaim_dead_slots=False)))
    qa=deepcopy(next(t for t in bom if t['config']['orders']==24 and t['config']['seed']==0 and t['policy_id']=='priority-control-QA1'))
    qa['policy_id']='QA-only-credit0';qa['solver_options'].pop('reward_mode',None)
    qa['solver_options']['completion_policy']=dict(credit_minutes=0,reclaim_dead_slots=False);choices.append(qa)
    for template in choices:
        for seed in range(100,116):
            row={k:deepcopy(template[k]) for k in ('policy_id','config','weights','solver_options')}
            row['task_id']=len(out);row['config']['seed']=seed;row['seed_role']='REUSED_VALIDATION100–115; explicit policy selection, not final'
            row['retain_trace']=seed==100;out.append(row)
    return out


def validate_tasks(declared):
    if not declared:raise ValueError('An explicit reused-validation protocol is required')
    for task in declared:
        if task['config']['seed'] not in range(100,116) or not task['seed_role'].startswith('REUSED_VALIDATION'):
            raise ValueError('Only explicitly labeled REUSED_VALIDATION100–115 is permitted; TRAIN/final prohibited')
        if task['config']['orders'] not in (12,24) or task['weights'].get('selector','priority')!='priority':
            raise ValueError('Only declared n12/n24 static priority contexts are authorized')
        if task['solver_options'].get('completion_policy',{}).get('reclaim_dead_slots',False):raise ValueError('Reclaim was rejected; keep it off')
        if task['solver_options'].get('reward_mode','original')!='original':raise ValueError('Reward/completion combination is untested')
    keys=[(t['config']['orders'],t['policy_id'],t['config']['seed']) for t in declared]
    if len(set(keys))!=len(keys):raise ValueError('Duplicate reused-validation tape/policy')


def simulate(task):
    from .spec import build
    from .check import check_trace
    started=time.perf_counter();cpu=time.process_time();trace=None;factory=None
    row={k:deepcopy(task[k]) for k in ('task_id','policy_id','config','weights','solver_options','seed_role')}
    try:
        validate_tasks([task])
        if hashes()!=task['source_hashes']:raise RuntimeError('Validation overlay source drift before episode')
        instance=build(**task['config']);options=deepcopy(task['solver_options'])
        if not options.pop('admission',False):raise ValueError('Explicit family admission is required')
        options.pop('reward_mode',None)
        factory=AdmissionCompletionFactory(instance,task['weights'],**options);trace=factory.run();checked=check_trace(trace,instance)
        mismatches=[d['tick'] for d in trace['qubo_decisions'] if sorted(d['result']['selected'])!=sorted(d['committed'])]
        row.update(valid=checked['valid'] and not mismatches,issues=checked['issues'],decode_mismatches=mismatches,
            metrics=trace['metrics'],flow=flow_metrics(trace),diagnosis=terminal_diagnosis(factory),
            completion_audit=trace['algorithm_audit']['completion_policy'],
            physical_instance_sha256=hashlib.sha256(json.dumps(instance,sort_keys=True).encode()).hexdigest())
        if hashes()!=task['source_hashes']:raise RuntimeError('Validation overlay source drift after episode')
    except Exception as exc:
        row.update(valid=False,error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
        if factory is not None:trace=factory.trace
    if trace is not None and (task.get('retain_trace',False) or not row['valid']):
        payload=json.dumps(trace,separators=(',',':')).encode();path=Path(task['output'])/f"trace-task{task['task_id']}.json.gz"
        path.write_bytes(gzip.compress(payload,mtime=0));row.update(trace_path=str(path),trace_sha256=hashlib.sha256(payload).hexdigest())
    row.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu);return row


def campaign(output,declared,workers=32):
    declared=deepcopy(declared);validate_tasks(declared)
    if workers<1:raise ValueError('Positive CPU workers required')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False);sources=hashes()
    for task in declared:task.update(source_hashes=sources,output=str(output))
    for name in SOURCES:
        p=output/'source_snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
    protocol=dict(schema='stage2-completion-reused-validation.v1',tasks=declared,source_hashes=sources,workers=workers,
        scope='Explicit reused VALIDATION100–115 for static policy selection; no training or reserved final execution',
        actor_seed=7,maintenance_outage_guard=False,reward_mode='original',reclaim_dead_slots=False,
        final_tapes=0,selection='Lexicographic invalidity,missing orders,total tardiness,total cost; never debt before missing')
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter();rows=[]
    with (output/'rows.jsonl').open('x') as log:
        with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool:
            pending={pool.submit(simulate,t):t for t in declared}
            for future in as_completed(pending):
                task=pending[future]
                try:row=future.result()
                except Exception as exc:row=dict(task_id=task['task_id'],policy_id=task['policy_id'],config=task['config'],valid=False,error=str(exc))
                rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
    groups=defaultdict(list)
    for row in rows:groups[(row['config']['orders'],row['policy_id'])].append(row)
    summary=[]
    for (orders,policy),rs in sorted(groups.items()):
        item=dict(orders=orders,policy_id=policy,runs=len(rs),invalid=sum(not x['valid'] for x in rs))
        if not item['invalid']:item.update(shipped=sum(x['metrics']['shipped'] for x in rs),required=sum(x['metrics']['orders'] for x in rs),
            complete=sum(x['metrics']['all_orders_fulfilled'] for x in rs),missing=sum(x['metrics']['orders']-x['metrics']['shipped'] for x in rs),
            total_tardiness=sum(x['metrics']['total_tardiness_ticks'] for x in rs),total_cost=sum(x['metrics']['total_cost'] for x in rs))
        summary.append(item)
    result=dict(**protocol,rows=sorted(rows,key=lambda r:r['task_id']),summary=summary,wall_seconds=time.perf_counter()-start,
        cpu_seconds=sum(x.get('cpu_seconds',0) for x in rows),source_stable=hashes()==sources)
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--tasks',type=Path,required=True);p.add_argument('--workers',type=int,default=32);a=p.parse_args()
    result=campaign(a.output,json.loads(a.tasks.read_text()),a.workers)
    print(json.dumps({k:result[k] for k in ('summary','wall_seconds','source_stable')},indent=2))


if __name__=='__main__':main()
