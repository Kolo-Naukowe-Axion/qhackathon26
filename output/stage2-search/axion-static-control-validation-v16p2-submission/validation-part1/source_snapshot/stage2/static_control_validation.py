"""Reused validation of TRAIN-selected static grid candidates, never final."""
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

from .static_control import GuardedCompletionFactory,policies,SOURCES as GRID_SOURCES,hashes as grid_hashes
from .bom_probe import flow_metrics
from .recovery_routing import ROOT

SOURCES=('stage2/static_control_validation.py',)+GRID_SOURCES


def hashes():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES}


def prepare(training_reports):
    declared=[];contexts=set()
    for filename in training_reports:
        p=Path(filename);report=json.loads(p.read_text())
        if report['source_hashes']!=grid_hashes() or report['selected_train_tapes'] not in (16,32):raise ValueError('Changed source or incomplete TRAIN selection')
        for context in report['candidates']:
            n=context['orders']
            if n in contexts:raise ValueError('Duplicate TRAIN context reports')
            contexts.add(n);choices={}
            ranked=sorted((x for x in report['summary'] if x['orders']==n and x['eligible']),
                key=lambda x:(x['missing'],x['total_tardiness'],x['total_cost'],x['policy_id']))
            matched=[x for x in ranked if not x['solver_options']['routing_policy']['eta_processes']
                and not x['solver_options']['routing_policy']['free_buffer_processes']
                and x['solver_options']['completion_policy']=={'credit_minutes':0,'reclaim_dead_slots':False}
                and x['weights']['bom_priority'] is False]
            tagged=[(x,'global_TRAIN_top2') for x in ranked[:2]]
            if matched:tagged.append((matched[0],'matched_18action_TRAIN_winner'))
            tagged.extend((x,'original_guarded_prior') for x in context['original_priors'])
            ranks={x['policy_id']:i+1 for i,x in enumerate(ranked)}
            for choice,role in tagged:
                signature=json.dumps(dict(weights=choice['weights'],options=choice['solver_options']),sort_keys=True)
                if signature not in choices:choices[signature]=dict(choice=choice,roles=[])
                choices[signature]['roles'].append(role)
            if len(choices)>4:raise ValueError('At most global top2 plus matched winner plus original prior')
            for entry in choices.values():
                choice=entry['choice']
                for seed in range(100,116):
                    declared.append(dict(task_id=len(declared),policy_id=choice['policy_id'],config=dict(orders=n,horizon=5760,profile='full',seed=seed),
                        weights=deepcopy(choice['weights']),solver_options=deepcopy(choice['solver_options']),original_prior=choice['original_prior'],
                        eligible_from_training=choice['eligible'],seed_role='REUSED_VALIDATION100–115; TRAIN-selected static candidates,not final',retain_trace=seed==100,
                        selection_provenance=dict(training_report=str(p),training_report_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                            selected_train_tapes=report['selected_train_tapes'],training_source_hashes=report['source_hashes'],
                            train_summary={k:v for k,v in choice.items() if k not in ('weights','solver_options')},
                            selection_roles=entry['roles'],global_train_rank=ranks.get(choice['policy_id']),
                            matched_domain='QA routing off,completion credit0,BOMoff;18 WIP/QAguard/T-Fmode actions',
                            criterion='Prospective revised third slot: global TRAIN top2 plus matched18action TRAIN winner plus guarded original prior; deduplicated,at most4')))
    validate_tasks(declared);return declared


def validate_tasks(declared):
    if not declared:raise ValueError('Explicit reused-validation candidate list required')
    known={p['policy_id']:p for p in policies()};seen=set();groups=defaultdict(set)
    for task in declared:
        seed=task['config']['seed'];policy=known.get(task['policy_id'])
        if seed not in range(100,116) or not task['seed_role'].startswith('REUSED_VALIDATION') or policy is None:
            raise ValueError('Only declared static policies on explicit reused VALIDATION100–115; final/TRAIN prohibited')
        if task['weights']!=policy['weights'] or task['solver_options']!=policy['solver_options']:
            raise ValueError('Validation differs from guarded TRAIN factorial policy')
        if {k:v for k,v in task['config'].items() if k!='seed'}!=policy['config']:raise ValueError('Physical validation config differs')
        if task['selection_provenance']['training_source_hashes']!=grid_hashes():raise ValueError('TRAIN policy source changed')
        key=(task['policy_id'],seed)
        if key in seen:raise ValueError('Duplicate policy/validation tape')
        seen.add(key);groups[task['config']['orders']].add(task['policy_id'])
    if any(len(v)>4 for v in groups.values()):raise ValueError('Too many validation candidates per context')
    for pid in {t['policy_id'] for t in declared}:
        if {t['config']['seed'] for t in declared if t['policy_id']==pid}!=set(range(100,116)):raise ValueError('Every candidate requires all16 paired validation tapes')


def simulate(task):
    from .spec import build
    from .check import check_trace
    started=time.perf_counter();cpu=time.process_time();factory=None;trace=None
    row={k:deepcopy(task[k]) for k in ('task_id','policy_id','config','weights','solver_options','original_prior','eligible_from_training','seed_role','selection_provenance')}
    try:
        if task['config']['seed'] not in range(100,116) or not task['solver_options']['maintenance_outage_guard']:raise ValueError('Validation range/guard mismatch')
        if hashes()!=task['source_hashes']:raise RuntimeError('Static validation source drift')
        instance=build(**task['config']);factory=GuardedCompletionFactory(instance,task['weights'],**task['solver_options']);trace=factory.run();checked=check_trace(trace,instance)
        mismatches=[d['tick'] for d in trace['qubo_decisions'] if sorted(d['result']['selected'])!=sorted(d['committed'])]
        row.update(valid=checked['valid'] and not mismatches,issues=checked['issues'],decode_mismatches=mismatches,metrics=trace['metrics'],flow=flow_metrics(trace),
            guard=trace['algorithm_audit']['maintenance_outage_guard'],physical_instance_sha256=hashlib.sha256(json.dumps(instance,sort_keys=True).encode()).hexdigest())
        if hashes()!=task['source_hashes']:raise RuntimeError('Static validation source drift after episode')
    except Exception as exc:
        row.update(valid=False,error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
        if factory is not None:trace=factory.trace
    if trace is not None and (task.get('retain_trace',False) or not row['valid']):
        payload=json.dumps(trace,separators=(',',':')).encode();path=Path(task['output'])/f"trace-task{task['task_id']}.json.gz";path.write_bytes(gzip.compress(payload,mtime=0))
        row.update(trace_path=str(path),trace_sha256=hashlib.sha256(payload).hexdigest())
    row.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu);return row


def campaign(output,declared,workers=32):
    declared=deepcopy(declared);validate_tasks(declared)
    if workers<1:raise ValueError('Positive workers required')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False);sources=hashes()
    for task in declared:task.update(source_hashes=sources,output=str(output))
    for name in SOURCES:
        p=output/'source_snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
    protocol=dict(schema='stage2-static-control-reused-validation.v1',source_hashes=sources,tasks=declared,workers=workers,
        scope='Explicit reused VALIDATION100–115; selected on TRAIN only; no reserved final',final_tapes=0,
        selection='Known TRAIN invalid disqualifies; lex missing orders before deadline debt before cost; original guarded priors retained')
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter();rows=[]
    with (output/'rows.jsonl').open('x') as log,ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool:
        pending={pool.submit(simulate,t):t for t in declared}
        for future in as_completed(pending):
            task=pending[future]
            try:result=future.result()
            except Exception as exc:result=dict(task_id=task['task_id'],policy_id=task['policy_id'],config=task['config'],
                original_prior=task['original_prior'],eligible_from_training=task['eligible_from_training'],valid=False,error=str(exc))
            rows.append(result);log.write(json.dumps(result)+'\n');log.flush()
    groups=defaultdict(list)
    for row in rows:groups[(row.get('config',{}).get('orders'),row.get('policy_id'))].append(row)
    summary=[]
    for (orders,pid),rs in sorted(groups.items(),key=str):
        entry=dict(orders=orders,policy_id=pid,runs=len(rs),invalid=sum(not r['valid'] for r in rs),original_prior=rs[0].get('original_prior',False),
            eligible=len(rs)==16 and all(r['valid'] and r.get('eligible_from_training',False) for r in rs))
        if not entry['invalid']:entry.update(shipped=sum(r['metrics']['shipped'] for r in rs),required=sum(r['metrics']['orders'] for r in rs),
            missing=sum(r['metrics']['orders']-r['metrics']['shipped'] for r in rs),complete=sum(r['metrics']['all_orders_fulfilled'] for r in rs),
            total_tardiness=sum(r['metrics']['total_tardiness_ticks'] for r in rs),total_cost=sum(r['metrics']['total_cost'] for r in rs),
            weights=rs[0]['weights'],solver_options=rs[0]['solver_options'])
        summary.append(entry)
    selected=[]
    for n in sorted({x['orders'] for x in summary if x['orders'] is not None}):
        eligible=[x for x in summary if x['orders']==n and x['eligible']]
        selected.append(dict(orders=n,best=min(eligible,key=lambda x:(x['missing'],x['total_tardiness'],x['total_cost'],x['policy_id'])) if eligible else None))
    result=dict(**protocol,rows=sorted(rows,key=lambda r:r.get('task_id',-1)),summary=summary,selected=selected,
        wall_seconds=time.perf_counter()-start,cpu_seconds=sum(r.get('cpu_seconds',0) for r in rows),source_stable=hashes()==sources)
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--training-report',type=Path,action='append');p.add_argument('--tasks-out',type=Path)
    p.add_argument('--tasks',type=Path);p.add_argument('--output',type=Path);p.add_argument('--workers',type=int,default=32);a=p.parse_args()
    if a.training_report:
        if not a.tasks_out or a.tasks_out.exists():raise ValueError('New --tasks-out required')
        a.tasks_out.write_text(json.dumps(prepare(a.training_report),indent=2)+'\n');return
    if not a.tasks or not a.output:raise ValueError('Explicit --tasks and --output required')
    r=campaign(a.output,json.loads(a.tasks.read_text()),a.workers);print(json.dumps(dict(summary=r['summary'],selected=r['selected'],wall_seconds=r['wall_seconds']),indent=2))


if __name__=='__main__':main()
