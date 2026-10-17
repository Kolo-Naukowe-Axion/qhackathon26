"""Frozen learned CEM time schedule with corrected local selector rewards.

This is learned time-dependent control, not state-adaptive RL or quantum
advantage. Every selector has the same outer policy and candidate construction;
their later realized pools may diverge after different physical actions.
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

from .adaptive_recovery import Controller,ACTIONS,SOURCES as LEARNING_SOURCES
from .selector_reward import RewardMixin,SOURCES as REWARD_SOURCES
from .maintenance_guard import MaintenanceOutageGuardMixin
from .recovery_routing import AdmissionRecoveryRoutingFactory,ROOT

CHECKPOINT_SHA256='d2ae8337daadd1baec7840e29b69500d91a548bbd3c0b4b5378f2b22ba6203e9'
SOURCES=tuple(dict.fromkeys(('stage2/hybrid_schedule.py','stage2/maintenance_guard.py','stage2/identity_audit.py')+LEARNING_SOURCES+REWARD_SOURCES))
SELECTORS=('priority','exact','sa','qaoa','uniform')


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def hashes():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES}


def load_checkpoint(path):
    path=Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=CHECKPOINT_SHA256:raise ValueError('Frozen selected CEM6 checkpoint SHA mismatch')
    artifact=json.loads(path.read_text())
    for name,sha in artifact['source_hashes'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:raise ValueError(f'Checkpoint source mismatch:{name}')
    if artifact['method']!='cem' or artifact['actions']!=list(ACTIONS) or len(artifact['contexts'])!=3:raise ValueError('Expected frozen3-context CEM6 artifact')
    if any(p['kind']!='schedule' or len(p['schedule'])!=8 for p in artifact['policies_by_context']):raise ValueError('Expected selected8-segment schedules')
    return artifact


class HybridScheduleFactory(RewardMixin,MaintenanceOutageGuardMixin,AdmissionRecoveryRoutingFactory):pass


def construct(instance,artifact,*,selector='priority',actor_seed=7):
    if selector not in SELECTORS or type(actor_seed) is not int:raise ValueError('Explicit supported selector and independent integer actor seed required')
    indices=[j for j,c in enumerate(artifact['contexts']) if c['config']==dict(orders=len(instance['orders']),horizon=instance['horizon_ticks'],profile=instance['profile'])]
    if len(indices)!=1:raise ValueError('Instance outside frozen learned contexts')
    j=indices[0];context=artifact['contexts'][j];base=dict(context['weights'],selector=selector,policy_seed=actor_seed)
    # The callback reconstructs weights from this base at every macro tick.
    # Overriding the initial Factory weights alone would silently revert later.
    controller=Controller(artifact['policies_by_context'][j],base,actor_seed,True,artifact['interval'])
    options=deepcopy(context['solver_options'])
    if options.pop('admission',False) is not True:raise ValueError('Frozen hybrid requires explicit family-admission context')
    factory=HybridScheduleFactory(instance,base,controller,reward_mode='no-batch',maintenance_outage_guard=True,**options)
    return factory,controller


def run(instance,checkpoint,*,selector='priority',actor_seed=7):
    artifact=load_checkpoint(checkpoint);factory,controller=construct(instance,artifact,selector=selector,actor_seed=actor_seed)
    trace=factory.run()
    if hashlib.sha256(Path(checkpoint).read_bytes()).hexdigest()!=CHECKPOINT_SHA256:raise RuntimeError('Checkpoint changed during hybrid episode')
    trace['provenance']['hybrid_schedule']=dict(checkpoint_sha256=CHECKPOINT_SHA256,selector=selector,actor_seed=actor_seed,
        reward_mode='no-batch',maintenance_outage_guard=True,outer_policy='Frozen CEM6 learned8-segment time schedule; not state-adaptive RL')
    return trace


def telemetry(trace):
    result=dict(calls=0,coupled_calls=0,qaoa_calls=0,coupled_qaoa_calls=0,trivial_1bit_qaoa_calls=0,
        fallback_calls=0,repairs=0,decode_mismatches=0,max_total_bits=0,max_core_bits=0,max_slack_bits=0,max_couplers=0,max_actual_simulated_quantum_bits=0,
        physical_quantum_calls=0,pool_records=[],result_elapsed_seconds_sum=0.,qaoa_angle_optimization_seconds_sum=0.)
    for d in trace.get('qubo_decisions',[]):
        r=d['result'];q=r.get('qubo',{});actual=r.get('quantum_algorithm_simulated') is True;coupled=q.get('couplers',0)>0
        result['calls']+=1;result['coupled_calls']+=coupled;result['qaoa_calls']+=actual;result['coupled_qaoa_calls']+=actual and coupled
        result['fallback_calls']+=bool(r.get('fallback_reason')) and r.get('method')!='classical_empty_pool'
        result['repairs']+=r.get('repaired') is True;result['physical_quantum_calls']+=r.get('physical_quantum_executed') is True
        for out,key in (('max_total_bits','variables'),('max_core_bits','core_variables'),('max_slack_bits','slack_variables'),('max_couplers','couplers')):
            result[out]=max(result[out],q.get(key,0))
        bits=r.get('sampling',{}).get('circuit',{}).get('qubits',0) if actual else 0
        result['max_actual_simulated_quantum_bits']=max(result['max_actual_simulated_quantum_bits'],bits)
        result['trivial_1bit_qaoa_calls']+=actual and bits==1
        selected=r.get('selected');committed=d.get('committed')
        result['decode_mismatches']+=selected is None or committed is None or sorted(selected)!=sorted(committed)
        result['result_elapsed_seconds_sum']+=r.get('elapsed_seconds',0)
        result['qaoa_angle_optimization_seconds_sum']+=r.get('sampling',{}).get('optimization',{}).get('elapsed_seconds',0)
        result['pool_records'].append(dict(tick=d['tick'],pool_sha256=digest({k:d[k] for k in ('candidates','conflicts','capacities')}),
            selected=r['selected'],committed=d['committed'],method=r['method'],total_bits=q.get('variables'),couplers=q.get('couplers')))
    result['timing_scope']='Literal recorded elapsed_seconds only; angle optimization nested,not additive. No separate encoding/decoding timing available.'
    return result


def tasks():
    result=[]
    for n in (12,16,24):
        for selector in SELECTORS:
            for actor in ((7,) if selector in ('priority','exact') else (7,13,29)):
                for seed in range(8):
                    result.append(dict(task_id=len(result),config=dict(orders=n,horizon=5760,profile='full',seed=seed),selector=selector,actor_seed=actor,
                        seed_role='TRAIN0–7 learned CEM6 plus corrected local selection integration; no validation/final',retain_trace=seed==0))
    return result


def simulate(task):
    from .spec import build
    from .check import check_trace
    from .identity_audit import audit_trace
    from .bom_probe import flow_metrics
    row={k:deepcopy(task[k]) for k in ('task_id','config','selector','actor_seed','seed_role')};start=time.perf_counter();cpu=time.process_time();trace=None
    try:
        if hashes()!=task['source_hashes']:raise RuntimeError('Hybrid source drift before episode')
        if task['config']['seed'] not in range(8):raise ValueError('Only declared TRAIN0–7 pilot tapes')
        instance=build(**task['config']);trace=run(instance,task['checkpoint'],selector=task['selector'],actor_seed=task['actor_seed']);checked=check_trace(trace,instance);identity=audit_trace(trace,instance);quantum=telemetry(trace)
        row.update(valid=checked['valid'] and identity['valid'] and quantum['decode_mismatches']==0,issues=checked['issues'],identity_audit=identity,metrics=trace['metrics'],flow=flow_metrics(trace),
            qubo_telemetry=quantum,physical_instance_sha256=digest(instance),checkpoint_sha256=CHECKPOINT_SHA256,
            outer_action_ids=[x['action_id'] for x in trace['decisions'] if 'action_id' in x])
        if hashes()!=task['source_hashes']:raise RuntimeError('Hybrid source drift after episode')
    except Exception as exc:row.update(valid=False,error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
    if trace is not None and (task['retain_trace'] or not row['valid']):
        payload=json.dumps(trace,separators=(',',':')).encode();p=Path(task['output'])/f"trace-task{task['task_id']}.json.gz";p.write_bytes(gzip.compress(payload,mtime=0));row.update(trace_path=str(p),trace_sha256=hashlib.sha256(payload).hexdigest())
    row.update(wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu);return row


def campaign(output,checkpoint,workers=32):
    load_checkpoint(checkpoint);output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False);source=hashes();declared=tasks()
    for task in declared:task.update(source_hashes=source,checkpoint=str(Path(checkpoint).resolve()),output=str(output))
    for name in SOURCES:
        p=output/'source_snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
    (output/'selected-checkpoint.json').write_bytes(Path(checkpoint).read_bytes())
    protocol=dict(schema='stage2-hybrid-schedule-pilot.v1',source_hashes=source,checkpoint_sha256=CHECKPOINT_SHA256,tasks=declared,workers=workers,
        scope='Fixed CEM6 learned time schedules + no-batch selector; TRAIN0–7 only,no validation/final',actors='Nested replicas within environment,not independent environmental samples',
        controls='Priority/exact actor7;SA/QAOA/uniform actors7/13/29. Equal outercontext/schedule/construction/reward; realized later pools can differ after actions',maintenance_outage_guard=True,reward_mode='no-batch')
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter();rows=[]
    with (output/'rows.jsonl').open('x') as log,ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool:
        pending={pool.submit(simulate,t):t for t in declared}
        for future in as_completed(pending):
            task=pending[future]
            try:r=future.result()
            except Exception as exc:r=dict(task_id=task['task_id'],config=task['config'],selector=task['selector'],actor_seed=task['actor_seed'],valid=False,error=str(exc))
            rows.append(r);log.write(json.dumps(r)+'\n');log.flush()
    groups=defaultdict(list)
    for r in rows:groups[(r['config']['orders'],r['selector'],r['actor_seed'])].append(r)
    summary=[]
    for (n,selector,actor),rs in sorted(groups.items()):
        s=dict(orders=n,selector=selector,actor_seed=actor,runs=len(rs),invalid=sum(not r['valid'] for r in rs))
        if not s['invalid']:s.update(shipped=sum(r['metrics']['shipped'] for r in rs),required=sum(r['metrics']['orders'] for r in rs),complete=sum(r['metrics']['all_orders_fulfilled'] for r in rs),tardiness=sum(r['metrics']['total_tardiness_ticks'] for r in rs),cost=sum(r['metrics']['total_cost'] for r in rs))
        summary.append(s)
    result=dict(**protocol,rows=sorted(rows,key=lambda r:r['task_id']),summary=summary,wall_seconds=time.perf_counter()-start,cpu_seconds=sum(r.get('cpu_seconds',0) for r in rows),source_stable=hashes()==source)
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--workers',type=int,default=32);a=p.parse_args()
    if a.workers<1:raise ValueError('Positive workers required')
    r=campaign(a.output,a.checkpoint,a.workers);print(json.dumps(dict(summary=r['summary'],wall_seconds=r['wall_seconds']),indent=2))


if __name__=='__main__':main()
