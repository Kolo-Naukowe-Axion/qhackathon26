"""Bounded TRAIN-only BOM-priority study on the strong recovery backend.

Only existing public-state priority weights and scoped routing flags change.
Flow diagnostics are post-run observations, never policy inputs.
"""
from __future__ import annotations

import argparse
from collections import defaultdict,Counter
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
from .recovery_routing import RecoveryRoutingFactory,BASE_WEIGHTS,ROOT,terminal_diagnosis,SOURCES as SHARED_SOURCES
from .selector_reward import RewardMixin

SOURCES=('stage2/bom_probe.py','stage2/selector_reward.py')+SHARED_SOURCES


class BOMFactory(RewardMixin,RecoveryRoutingFactory):pass
class AdmissionBOMFactory(AdmissionMixin,BOMFactory):pass


def run(instance,weights=None,controller=None,*,admission=False,**options):
    cls=AdmissionBOMFactory if admission else BOMFactory
    return cls(instance,weights,controller,**options).run()


def hashes():return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def variants():
    result=[dict(name='priority-control',weights=dict(bom_priority=False),reward_mode='original')]
    for rule in ('join','critical','slack'):
        for scale in (.25,1.):
            result.append(dict(name=f'{rule}-'+('quarter' if scale==.25 else 'default'),
                weights=dict(bom_priority=rule,bom_join_weight=24*scale,bom_progress_weight=4*scale,
                    bom_tail_weight=.5*scale,bom_slack_weight=scale),reward_mode='original'))
    result.append(dict(name='exact-no-batch-control',weights=dict(bom_priority=False,selector='exact'),reward_mode='no-batch'))
    return result


def diagnostic_tasks():
    tasks=[]
    for orders in (16,24):
        base=dict(BASE_WEIGHTS,wip_limit=4,due=1.,family=0.,tool_distance=1 if orders==16 else 8,policy_seed=7)
        for qa in (False,True):
            for variant in variants():
                if qa and variant['name'] not in ('priority-control','join-quarter','critical-quarter','slack-quarter'):continue
                for seed in range(8):
                    tasks.append(dict(task_id=len(tasks),policy_id=variant['name']+f'-QA{int(qa)}',
                        config=dict(orders=orders,horizon=5760,profile='full',seed=seed),
                        weights=dict(base,**variant['weights']),solver_options=dict(admission=True,
                            tool_policy={'mode':'hard'},kit_reservation=orders==16,recovery_policy={'enabled':True},
                            routing_policy={'eta_processes':['QA'] if qa else [],'free_buffer_processes':[]},
                            reward_mode=variant['reward_mode']),seed_role='TRAIN0–7 predeclared paired BOM probe',
                        retain_trace=seed==0))
    return tasks


def flow_metrics(trace):
    """Retrospective actual-tape delays, including censored stranded components."""
    horizon=trace['instance']['horizon_ticks'];minutes=trace['instance']['tick_minutes']
    accepted={};consumed={};scrap_pumps=[]
    for event in trace['events']:
        uid=event.get('unit_id','')
        if event['type']=='qa_result' and event['passed'] and '/pump/' not in uid:accepted[uid]=event['tick']
        if event['type']=='consume':consumed[uid]=event['tick']
        if event['type']=='scrap' and '/pump/' in uid:scrap_pumps.append(uid)
    occupied=Counter();attendance=Counter();previous={};preqa=[];assembly_wait=[];assembled=[]
    for op in sorted(trace['operations'],key=lambda x:(x['start'],x['id'])):
        if op['kind']!='process':continue
        proc=op['process'];occupied[proc]+=(op['end']-op['start'])*minutes
        attendance[proc]+=sum(v['end']-v['start'] for v in op['worker_intervals'])*minutes
        if proc=='QA':
            for uid in op['unit_ids']:
                if uid in previous:preqa.append(max(0,op['start']-previous[uid])*minutes)
        if proc=='ASSEMBLY' and op['parent_unit_ids']:
            parents=op['parent_unit_ids']
            if not all(uid in accepted for uid in parents):raise ValueError('Assembly flow audit missing accepted parents')
            assembly_wait.append((op['start']-max(accepted[uid] for uid in parents))*minutes)
            assembled.append(op['order_id'])
        for uid in op['unit_ids']:previous[uid]=op['end']
    stranded=sorted(set(accepted)-set(consumed))
    return dict(process_machine_occupied_minutes=dict(occupied),process_worker_attendance_minutes=dict(attendance),
        accepted_components=len(accepted),accepted_component_wait_until_consumption_or_horizon_minutes=
            sum((consumed.get(uid,horizon)-tick)*minutes for uid,tick in accepted.items()),
        stranded_accepted_components=len(stranded),stranded_component_ids=stranded,
        qa_inspections=len(preqa),pre_qa_processing_completion_to_inspection_start_minutes=sum(preqa),
        assembly_starts=len(assembled),accepted_kit_ready_to_initial_assembly_minutes=sum(assembly_wait),
        scrapped_final_pumps=scrap_pumps,
        interpretation='Actual-tape flow descriptors. Pre-QA delay includes transport/queues/calendars; component waits are horizon-censored. No hard capacity certificate.')


def simulate(task):
    from .spec import build
    from .check import check_trace
    started=time.perf_counter();cpu=time.process_time();trace=None;factory=None
    row={key:deepcopy(task[key]) for key in ('task_id','policy_id','config','weights','solver_options','seed_role')}
    try:
        if task['config']['seed'] not in range(32):raise ValueError('TRAIN0–31 only')
        if hashes()!=task['source_hashes']:raise RuntimeError('Source drift before episode')
        instance=build(**task['config']);options=deepcopy(task['solver_options']);cls=AdmissionBOMFactory if options.pop('admission',False) else BOMFactory
        factory=cls(instance,task['weights'],**options);trace=factory.run();checked=check_trace(trace)
        mismatches=[d['tick'] for d in trace['qubo_decisions'] if sorted(d['result']['selected'])!=sorted(d['committed'])]
        row.update(valid=checked['valid'] and not mismatches,issues=checked['issues'],decode_mismatches=mismatches,
            metrics=trace['metrics'],flow=flow_metrics(trace),diagnosis=terminal_diagnosis(factory),
            physical_instance_sha256=hashlib.sha256(json.dumps(instance,sort_keys=True).encode()).hexdigest())
        if hashes()!=task['source_hashes']:raise RuntimeError('Source drift after episode')
    except Exception as exc:
        row.update(valid=False,error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
        if factory is not None:trace=factory.trace
    if trace is not None and (task.get('retain_trace',False) or not row['valid']):
        payload=json.dumps(trace,separators=(',',':')).encode();path=Path(task['output'])/f"trace-task{task['task_id']}.json.gz"
        path.write_bytes(gzip.compress(payload,mtime=0));row.update(trace_path=str(path),trace_sha256=hashlib.sha256(payload).hexdigest())
    row.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu);return row


def campaign(output,tasks=None,workers=2):
    tasks=deepcopy(diagnostic_tasks() if tasks is None else tasks)
    if workers<1 or any(t['config']['seed'] not in range(32) for t in tasks):raise ValueError('Positive workers and TRAIN0–31 required')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False);sources=hashes()
    for task in tasks:task.update(source_hashes=sources,output=str(output))
    for name in SOURCES:
        path=output/'source_snapshot'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
    protocol=dict(schema='stage2-bom-probe.v1',source_hashes=sources,tasks=tasks,workers=workers,
        scope='TRAIN-only existing BOM priority coefficients,unchanged strong recovery physical model',
        scales='Quarter and full existing defaults; QA-only routing comparison restricted to quarter scales',validation_tapes=0,final_tapes=0)
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter();rows=[]
    with (output/'rows.jsonl').open('x') as log:
        with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool:
            pending={pool.submit(simulate,t):t for t in tasks}
            for future in as_completed(pending):
                task=pending[future]
                try:row=future.result()
                except Exception as exc:row=dict(task_id=task['task_id'],policy_id=task['policy_id'],config=task['config'],valid=False,error=str(exc))
                rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
    grouped=defaultdict(list)
    for row in rows:grouped[(row['config']['orders'],row['policy_id'])].append(row)
    summary=[]
    for (orders,policy),rs in sorted(grouped.items()):
        entry=dict(orders=orders,policy_id=policy,runs=len(rs),invalid=sum(not r['valid'] for r in rs),seeds=sorted(r['config']['seed'] for r in rs))
        if not entry['invalid']:
            entry.update(shipped=sum(r['metrics']['shipped'] for r in rs),required=sum(r['metrics']['orders'] for r in rs),
                complete=sum(r['metrics']['all_orders_fulfilled'] for r in rs),total_tardiness=sum(r['metrics']['total_tardiness_ticks'] for r in rs))
            for key in ('accepted_component_wait_until_consumption_or_horizon_minutes','stranded_accepted_components',
                'pre_qa_processing_completion_to_inspection_start_minutes','accepted_kit_ready_to_initial_assembly_minutes','assembly_starts'):
                entry[key]=sum(r['flow'][key] for r in rs)
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
