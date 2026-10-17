"""Optional composition of frozen physical recovery and process-scoped routing.

The diagnostic driver uses explicitly selected TRAIN failures. Its completion
rates are not unbiased performance estimates. Physical source modules stay fixed.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
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
from .kit_recovery import RecoveryFactory
from .routing import RoutingMixin

ROOT=Path(__file__).resolve().parents[1]
SOURCES=('stage2/recovery_routing.py','stage2/routing.py','stage2/kit_recovery.py',
    'stage2/engine.py','stage2/spec.py','stage2/check.py','stage2/dispatch.py',
    'stage2/qubo.py','stage2/quantum.py','stage2/advanced.py','stage2/specialist.py',
    'stage2/tooling.py','stage2/kitting.py','stage2/admission.py','instances/stage2/metaltech_pressure.json')
BASE_WEIGHTS=dict(wip_limit=8,mode='standard',due=.25,remaining=-4.,family=24.,setup=10,
    lease_calibration=True,selector='priority',policy_seed=0,tool_distance=0,
    qa_guard_threshold=4,worker_calendar=True,preposition=False,admission_rule='family')


class RecoveryRoutingFactory(RoutingMixin,RecoveryFactory):pass
class AdmissionRecoveryRoutingFactory(AdmissionMixin,RecoveryRoutingFactory):pass


def run(instance,weights=None,controller=None,*,routing_policy=None,recovery_policy=None,
        tool_policy=None,kit_reservation=True,admission=False):
    cls=AdmissionRecoveryRoutingFactory if admission else RecoveryRoutingFactory
    return cls(instance,weights,controller,routing_policy=routing_policy,recovery_policy=recovery_policy,
        tool_policy=tool_policy,kit_reservation=kit_reservation).run()


def hashes():return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def assert_sources(expected):
    if hashes()!=expected:raise RuntimeError('Recovery/routing source changed; retain failure and freeze again')


def terminal_diagnosis(factory):
    """Descriptive terminal evidence, never a certificate of infeasibility."""
    horizon=factory.i['horizon_ticks'];minutes=factory.i['tick_minutes'];period=factory.i.get('day_ticks',96)
    unfinished={oid for oid in factory.orders if oid not in factory.shipped}
    parts=[dict(id=p['id'],order_id=p['order_id'],recipe=p['recipe'],status=p['status'],
        accepted=p['accepted'],location=p['location'],moving=p.get('moving',False),busy=p['busy'],
        next_process=factory.next_step(p) and factory.next_step(p)['process'],attempt=p['attempt'],replacement=p.get('replacement',0))
        for p in factory.parts.values() if p['order_id'] in unfinished and p['status'] not in ('consumed','disposed','scrap','shipped')]
    qualified=[]
    for worker in factory.workers.values():
        if 'qa' not in worker['skills']:continue
        available=0
        for tick in range(horizon):
            phase=tick%period;a,b=worker['daily_shift']
            available+=a<=phase<b and not any(start<=phase<end for start,end in worker['breaks'])
        intervals=[];qa_intervals=[]
        for operation in factory.trace['operations']:
            attendance=operation.get('worker_intervals') or [dict(worker_id=wid,start=operation['start'],end=operation['end'],skills=['qa'] if operation['process']=='QA' else []) for wid in operation['worker_ids']]
            for interval in attendance:
                if interval['worker_id']==worker['id']:
                    intervals.append((interval['start'],interval['end']))
                    if 'qa' in interval['skills']:qa_intervals.append((interval['start'],interval['end']))
        for move in factory.trace['worker_moves']:
            if move['worker_id']==worker['id']:intervals.append((move['start'],move['end']))
        def union_length(rows):
            total=0;end=-1
            for start,stop in sorted(rows):
                total+=max(0,stop-max(start,end));end=max(end,stop)
            return total
        qualified.append(dict(worker_id=worker['id'],calendar_available_minutes=available*minutes,
            occupied_all_skills_and_walk_minutes=union_length(intervals)*minutes,qa_attendance_minutes=union_length(qa_intervals)*minutes))
    latest=max((op['start'] for op in factory.trace['operations'] if op['kind']=='process'),default=0)
    return dict(unfinished_orders=sorted(unfinished),unfinished_parts=parts,
        next_process_counts=dict(Counter(p['next_process'] for p in parts if not p['accepted'])),
        accepted_component_count=sum(p['accepted'] and p['recipe']!='pump' for p in parts),
        quiet_production_start_minutes=(horizon-latest)*minutes,last_production_start_tick=latest,
        buffers={mid:dict(input_count=factory.input_count(mid),in_flight_reserved=factory.reserved[mid],
            input_capacity=m['input_capacity'],blocked_output=sorted(m['output']),busy_until=m['busy'])
            for mid,m in factory.machines.items() if m['process'] in ('QA','ASSEMBLY')},
        qa_qualified_workers=qualified,recovery_active=deepcopy(factory.recovery_active),
        recovery_status_counts=dict(Counter(r['status'] for r in factory.recovery_history)),
        interpretation='Trajectory diagnosis only. Late unfinished work or utilization cannot prove the original full problem infeasible.')


def diagnostic_tasks():
    cases={12:[15],13:[3,5,20],14:[0,3,6,31]};tasks=[]
    for orders,seeds in cases.items():
        for wip in (4,6,8):
            for guard in (0,4):
                for qa in (False,True):
                    for seed in seeds:
                        tasks.append(dict(task_id=len(tasks),policy_id=f'w{wip}-guard{guard}-QA{int(qa)}',
                            config=dict(orders=orders,horizon=5760,profile='full',seed=seed),
                            weights=dict(BASE_WEIGHTS,wip_limit=wip,qa_guard_threshold=guard),
                            solver_options=dict(tool_policy=dict(mode='hard'),kit_reservation=True,admission=True,
                                recovery_policy=dict(enabled=True),routing_policy=dict(eta_processes=['QA'] if qa else [],free_buffer_processes=[])),
                            seed_role='TRAIN; deliberately selected prior failures',
                            selection='Predeclared known TRAIN failures, not unbiased completion-rate estimation'))
    return tasks


def simulate(task):
    from .spec import build
    from .check import check_trace
    started=time.perf_counter();cpu=time.process_time();factory=None;trace=None
    row={key:task[key] for key in ('task_id','policy_id','config','weights','solver_options','seed_role')}
    try:
        if task['config']['seed'] not in range(32):raise ValueError('This driver accepts only declared TRAIN0–31')
        assert_sources(task['source_hashes'])
        instance=build(**task['config']);options=task['solver_options'];cls=AdmissionRecoveryRoutingFactory if options.get('admission',False) else RecoveryRoutingFactory
        factory=cls(instance,task['weights'],**{k:v for k,v in options.items() if k!='admission'})
        trace=factory.run();checked=check_trace(trace)
        row.update(valid=checked['valid'],issues=checked['issues'],metrics=trace['metrics'],
            diagnosis=terminal_diagnosis(factory),algorithm_audit=trace['algorithm_audit'],physical_instance_sha256=hashlib.sha256(json.dumps(instance,sort_keys=True).encode()).hexdigest())
        assert_sources(task['source_hashes'])
    except Exception as exc:row.update(valid=False,error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
    if trace is not None and task.get('retain_trace',False):
        path=Path(task['output'])/f"trace-task{task['task_id']}.json.gz";payload=json.dumps(trace,separators=(',',':')).encode()
        path.write_bytes(gzip.compress(payload,mtime=0));row.update(trace_path=str(path),trace_sha256=hashlib.sha256(payload).hexdigest())
    row.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu)
    return row


def campaign(output,tasks=None,workers=2,prepare_only=False):
    if workers<1:raise ValueError('Positive worker count required')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False);sources=hashes()
    tasks=deepcopy(diagnostic_tasks() if tasks is None else tasks)
    for task in tasks:
        if task['config']['seed'] not in range(32):raise ValueError('TRAIN0–31 only; validation/final prohibited')
        task.update(source_hashes=sources,output=str(output))
    for name in SOURCES:
        path=output/'source_snapshot'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
    protocol=dict(schema='stage2-recovery-routing-probe.v1',source_hashes=sources,tasks=tasks,workers=workers,
        scope='TRAIN diagnostic or explicitly supplied TRAIN protocol; no validation/final execution',
        physical_model='Unchanged; frozen recovery +scoped routing composition',validation_tapes=0,final_tapes=0)
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    if prepare_only:return protocol
    started=time.perf_counter();rows=[]
    with (output/'rows.jsonl').open('x') as log:
        if workers==1:
            for task in tasks:
                row=simulate(task);rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
        else:
            with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool:
                pending={pool.submit(simulate,t):t for t in tasks}
                for future in as_completed(pending):
                    task=pending[future]
                    try:row=future.result()
                    except Exception as exc:row=dict(task_id=task['task_id'],policy_id=task['policy_id'],config=task['config'],valid=False,error=str(exc))
                    rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
    assert_sources(sources);groups=defaultdict(list)
    for row in rows:groups[(row['config']['orders'],row['policy_id'])].append(row)
    summary=[]
    for (orders,policy),rs in sorted(groups.items()):
        entry=dict(orders=orders,policy_id=policy,runs=len(rs),invalid=sum(not r['valid'] for r in rs),seeds=sorted(r['config']['seed'] for r in rs))
        if not entry['invalid']:
            entry.update(shipped=sum(r['metrics']['shipped'] for r in rs),required=sum(r['metrics']['orders'] for r in rs),
                complete=sum(r['metrics']['all_orders_fulfilled'] for r in rs),
                missing=sum(r['metrics']['orders']-r['metrics']['shipped'] for r in rs),
                total_tardiness=sum(r['metrics']['total_tardiness_ticks'] for r in rs))
        summary.append(entry)
    result=dict(**protocol,rows=sorted(rows,key=lambda r:r['task_id']),summary=summary,
        wall_seconds=time.perf_counter()-started,cpu_seconds=sum(r.get('cpu_seconds',0) for r in rows))
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--tasks',type=Path);p.add_argument('--workers',type=int,default=2);p.add_argument('--prepare-only',action='store_true')
    a=p.parse_args();result=campaign(a.output,json.loads(a.tasks.read_text()) if a.tasks else None,a.workers,a.prepare_only)
    print(json.dumps({k:result[k] for k in ('summary','wall_seconds') if k in result},indent=2))


if __name__=='__main__':main()
