"""Causal assembly-mode controls over the frozen recovery/routing factory.

The selective control uses current time and public duration/horizon data only.
It cannot inspect instance seeds, future quality draws or hidden scenarios.
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

from .admission import AdmissionMixin
from .recovery_routing import RecoveryRoutingFactory,BASE_WEIGHTS,ROOT,terminal_diagnosis,SOURCES as PHYSICAL_SOURCES
from .spec import duration

SOURCES=('stage2/quality_policy.py',)+PHYSICAL_SOURCES


class QualityMixin:
    def __init__(self,*args,quality_policy=None,**kwargs):
        policy=dict(mode='standard',start_fraction=.75,margin_minutes=60)
        if quality_policy:policy.update(quality_policy)
        if set(policy)!={'mode','start_fraction','margin_minutes'}:raise ValueError('Unknown quality-policy option')
        if policy['mode'] not in ('standard','all-careful','selective'):raise ValueError('Unknown quality mode')
        if not 0<=policy['start_fraction']<=1 or policy['margin_minutes']<0:raise ValueError('Invalid public quality threshold')
        super().__init__(*args,**kwargs)
        self.quality_policy=policy;self.quality_decisions=[]
        self.trace['provenance']['assembly_quality_policy']=deepcopy(policy)

    def assembly_mode(self,m,p,mode):
        if m['process']!='ASSEMBLY' or self.quality_policy['mode']=='standard':return mode
        if self.quality_policy['mode']=='all-careful':return 'careful'
        # Rework has a fixed residual risk in the frozen model, so slowing it
        # cannot buy a lower inspection probability. No keyed draw is read.
        if p.get('rework') or p['recipe']!='pump':return mode
        horizon=self.i['horizon_ticks']
        if self.t<horizon*self.quality_policy['start_fraction']:return mode
        step=self.next_step(p);assembly=duration(self.i,'ASSEMBLY',step['base_ticks'],m,'careful')
        setup=0 if m['family'] in (None,p['family']) else self.i['setup_matrix'][m['family']][p['family']]
        qa_mode=self.selected_mode('QA',p['order_id']);qa_step=self.i['recipes']['pump'][-1]
        qa=min(duration(self.i,'QA',qa_step['base_ticks'],q,qa_mode) for q in self.machines.values() if q['process']=='QA')
        # Optimistic transport + an explicit public buffer are a ranking guard,
        # not a promise that calendars/resources permit delivery in time.
        transport=min(sum(d for _,_,d in self.path(m['id'],q['id']))+
            sum(d for _,_,d in self.path(q['id'],'SHIP_B'))
            for q in self.machines.values() if q['process']=='QA')
        margin=self.quality_policy['margin_minutes']/self.i['tick_minutes']
        return 'careful' if self.t+setup+assembly+qa+transport+margin<=horizon else mode

    def process(self,m,parts,mode='standard',parents=None,kind='process',preview=False,prepare_only=False):
        chosen=self.assembly_mode(m,parts[0],mode)
        result=super().process(m,parts,chosen,parents=parents,kind=kind,preview=preview,prepare_only=prepare_only)
        if result and not preview and not prepare_only and m['process']=='ASSEMBLY':
            operation=self.trace['operations'][-1]
            self.quality_decisions.append(dict(operation_id=operation['id'],tick=self.t,unit_id=parts[0]['id'],
                requested_mode=mode,chosen_mode=chosen,is_rework=operation['is_rework'],wear_before=operation['wear_before']))
        return result

    def finish(self):
        super().finish()
        self.trace.setdefault('algorithm_audit',{})['assembly_quality_policy']=dict(policy=deepcopy(self.quality_policy),
            decisions=deepcopy(self.quality_decisions),scope='Causal mode choice; original duration/attendance/quality physics')


class QualityFactory(QualityMixin,RecoveryRoutingFactory):pass
class AdmissionQualityFactory(AdmissionMixin,QualityFactory):pass


def run(instance,weights=None,controller=None,*,admission=False,**options):
    cls=AdmissionQualityFactory if admission else QualityFactory
    return cls(instance,weights,controller,**options).run()


def hashes():return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def diagnostic_tasks():
    tasks=[]
    for orders,seeds,wip,qa in ((12,[15],8,False),(12,[15],6,True),(13,[3,5,20],6,False),(14,[0,3,6,31],6,True)):
        for mode in ('standard','all-careful','selective'):
            for seed in seeds:
                tasks.append(dict(task_id=len(tasks),policy_id=f'w{wip}-QA{int(qa)}-{mode}',
                    config=dict(orders=orders,horizon=5760,profile='full',seed=seed),
                    weights=dict(BASE_WEIGHTS,wip_limit=wip),solver_options=dict(admission=True,
                        tool_policy={'mode':'hard'},kit_reservation=True,recovery_policy={'enabled':True},
                        routing_policy={'eta_processes':['QA'] if qa else [],'free_buffer_processes':[]},
                        quality_policy={'mode':mode}),seed_role='TRAIN deliberately selected prior failures',retain_trace=True))
    return tasks


def simulate(task):
    from .spec import build
    from .check import check_trace
    started=time.perf_counter();cpu=time.process_time();trace=None
    row={key:deepcopy(task[key]) for key in ('task_id','policy_id','config','weights','solver_options','seed_role')}
    try:
        if task['config']['seed'] not in range(32):raise ValueError('TRAIN0–31 only')
        if hashes()!=task['source_hashes']:raise RuntimeError('Source drift before episode')
        instance=build(**task['config']);options=deepcopy(task['solver_options'])
        cls=AdmissionQualityFactory if options.pop('admission',False) else QualityFactory
        factory=cls(instance,task['weights'],**options);trace=factory.run();checked=check_trace(trace)
        row.update(valid=checked['valid'],issues=checked['issues'],metrics=trace['metrics'],diagnosis=terminal_diagnosis(factory),
            quality_audit=trace['algorithm_audit']['assembly_quality_policy'],
            quality_events=[e for e in trace['events'] if e['type'] in ('qa_result','repair','scrap')],
            physical_instance_sha256=hashlib.sha256(json.dumps(instance,sort_keys=True).encode()).hexdigest())
        if hashes()!=task['source_hashes']:raise RuntimeError('Source drift after episode')
    except Exception as exc:row.update(valid=False,error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
    if trace is not None and task.get('retain_trace',False):
        payload=json.dumps(trace,separators=(',',':')).encode();path=Path(task['output'])/f"trace-task{task['task_id']}.json.gz"
        path.write_bytes(gzip.compress(payload,mtime=0));row.update(trace_path=str(path),trace_sha256=hashlib.sha256(payload).hexdigest())
    row.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu);return row


def campaign(output,tasks=None,workers=2):
    output=Path(output).resolve();tasks=deepcopy(diagnostic_tasks() if tasks is None else tasks)
    if workers<1 or any(t['config']['seed'] not in range(32) for t in tasks):raise ValueError('Positive workers and TRAIN0–31 required')
    output.mkdir(parents=True,exist_ok=False);sources=hashes()
    for task in tasks:task.update(source_hashes=sources,output=str(output))
    for name in SOURCES:
        path=output/'source_snapshot'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
    protocol=dict(schema='stage2-assembly-quality-probe.v1',tasks=tasks,source_hashes=sources,workers=workers,
        scope='TRAIN diagnostic only; explicitly selected failures; original physical modes; no validation/final tapes')
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
        entry=dict(orders=orders,policy_id=policy,runs=len(rs),invalid=sum(not r['valid'] for r in rs))
        if not entry['invalid']:entry.update(shipped=sum(r['metrics']['shipped'] for r in rs),required=sum(r['metrics']['orders'] for r in rs),
            complete=sum(r['metrics']['all_orders_fulfilled'] for r in rs),total_tardiness=sum(r['metrics']['total_tardiness_ticks'] for r in rs))
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
