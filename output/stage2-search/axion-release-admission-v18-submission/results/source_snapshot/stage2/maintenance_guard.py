"""Opt-in causal maintenance exclusion during machine outages.

The original maintenance loop omits its production loop's outage test. This
algorithm restriction temporarily suppresses maintenance eligibility only;
physical operations/checker and every default remain unchanged.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import time

from .admission import AdmissionMixin
from .recovery_routing import RecoveryRoutingFactory,ROOT,SOURCES as SHARED_SOURCES

SOURCES=('stage2/maintenance_guard.py',)+SHARED_SOURCES


def overlaps(start,end,a,b):return start<b and a<end


def public_outage_reasons(factory,machine_id,start,end):
    """Revealed event intervals and union of unrevealed public support only."""
    reasons=[]
    for event in factory.trace['events']:
        if event['type']=='outage' and event['tick']<=factory.t and event['machine']==machine_id and overlaps(start,end,event['start'],event['end']):
            reasons.append(dict(source='observed',start=event['start'],end=event['end'],revealed_at=event['tick']))
    for index,stage in enumerate(factory.i['uncertainty_stages']):
        if stage['reveal_tick']<=factory.t:continue
        for outcome in stage['outcomes']:
            for event in outcome['events']:
                if event['type']=='machine_outage' and event['machine']==machine_id and overlaps(start,end,event['start'],event['end']):
                    reasons.append(dict(source='unrevealed_public_support',stage=index,outcome=outcome['id'],
                        reveal_tick=stage['reveal_tick'],start=event['start'],end=event['end']))
    return reasons


class MaintenanceOutageGuardMixin:
    def __init__(self,*args,maintenance_outage_guard=False,**kwargs):
        if type(maintenance_outage_guard) is not bool:raise ValueError('Maintenance guard must be an explicit boolean')
        super().__init__(*args,**kwargs)
        self.maintenance_outage_guard=maintenance_outage_guard;self.maintenance_guard_spans=[]
        self._maintenance_last_span={};self.maintenance_guard_calls=0

    def service_resources(self):
        if not self.maintenance_outage_guard:return super().service_resources()
        length=self.i['maintenance']['duration'];saved=[]
        try:
            for machine in self.machines.values():
                if machine['busy']>self.t or machine['output'] or machine['wear']<self.i['maintenance']['wear_limit']-12*self.i.get('time_scale',1):continue
                reasons=public_outage_reasons(self,machine['id'],self.t,self.t+length)
                if not reasons:continue
                saved.append((machine,machine['busy']))
                # Keep the dictionary intact: tool-service hall lookup and
                # other workers/tools retain original physical semantics.
                machine['busy']=self.t+1;self.maintenance_guard_calls+=1
                signature=json.dumps(reasons,sort_keys=True);last=self._maintenance_last_span.get(machine['id'])
                if last is not None and self.maintenance_guard_spans[last]['last_tick']==self.t-1 and self.maintenance_guard_spans[last]['signature']==signature:
                    self.maintenance_guard_spans[last]['last_tick']=self.t
                else:
                    self._maintenance_last_span[machine['id']]=len(self.maintenance_guard_spans)
                    self.maintenance_guard_spans.append(dict(machine_id=machine['id'],first_tick=self.t,last_tick=self.t,
                        attempted_duration=length,reasons=reasons,signature=signature))
            return super().service_resources()
        finally:
            unexpected=[]
            for machine,old_busy in saved:
                if machine['busy']!=self.t+1:unexpected.append(machine['id'])
                machine['busy']=old_busy
            if unexpected:raise RuntimeError('Guarded maintenance unexpectedly changed machine bookings: '+','.join(unexpected))

    def finish(self):
        super().finish()
        self.trace.setdefault('algorithm_audit',{})['maintenance_outage_guard']=dict(enabled=self.maintenance_outage_guard,
            blocked_eligible_calls=self.maintenance_guard_calls,
            spans=[{k:v for k,v in row.items() if k!='signature'} for row in self.maintenance_guard_spans],
            scope='Causal conservative maintenance restriction using observed outages and unrevealed public support; physical core unchanged')


class MaintenanceGuardFactory(MaintenanceOutageGuardMixin,RecoveryRoutingFactory):pass
class AdmissionMaintenanceGuardFactory(MaintenanceOutageGuardMixin,AdmissionMixin,RecoveryRoutingFactory):pass


def run(instance,weights=None,controller=None,*,admission=False,maintenance_outage_guard=False,**options):
    cls=AdmissionMaintenanceGuardFactory if admission else MaintenanceGuardFactory
    return cls(instance,weights,controller,maintenance_outage_guard=maintenance_outage_guard,**options).run()


def hashes():return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def campaign(output,tasks_file):
    from .spec import build
    from .check import check_trace
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False);sources=hashes()
    tasks0=json.loads(Path(tasks_file).read_text())['tasks'];chosen=[t for t in tasks0 if t['task_id'] in (404,412,420,428)]
    if len(chosen)!=4 or any(t['config']['seed']!=4 or t['config']['orders']!=24 for t in chosen):raise ValueError('Expected four diagnosed TRAIN outage cases')
    protocol=dict(schema='stage2-maintenance-outage-guard.v1',source_hashes=sources,
        source_tasks_file=str(tasks_file),source_tasks_sha256=hashlib.sha256(Path(tasks_file).read_bytes()).hexdigest(),
        tasks=chosen,selection='Four previously INVALID turbo TRAIN n24seed4 cases; preserve unguarded originals,not an unbiased rate',
        final_tapes=0,validation_tapes=0)
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    for name in SOURCES:
        path=output/'source_snapshot'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
    rows=[];start=time.perf_counter()
    for task in chosen:
        for enabled in (False,True):
            if hashes()!=sources:raise RuntimeError('Frozen maintenance-guard source drift')
            before=time.perf_counter();cpu=time.process_time();instance=build(**task['config'])
            trace=run(instance,task['weights'],**task['solver_options'],maintenance_outage_guard=enabled)
            checked=check_trace(trace);payload=json.dumps(trace,separators=(',',':')).encode();path=output/f"task{task['task_id']}-guard{int(enabled)}.json.gz"
            path.write_bytes(gzip.compress(payload,mtime=0))
            rows.append(dict(task_id=task['task_id'],policy_id=task['policy_id'],config=task['config'],weights=task['weights'],
                enabled=enabled,valid=checked['valid'],issues=checked['issues'],metrics=trace['metrics'],
                guard=trace['algorithm_audit']['maintenance_outage_guard'],trace_path=str(path),
                trace_sha256=hashlib.sha256(payload).hexdigest(),wall_seconds=time.perf_counter()-before,cpu_seconds=time.process_time()-cpu))
            (output/'rows.json').write_text(json.dumps(rows,indent=2)+'\n')
    result=dict(**protocol,rows=rows,wall_seconds=time.perf_counter()-start,source_stable=hashes()==sources)
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--tasks-file',type=Path,required=True);a=p.parse_args()
    r=campaign(a.output,a.tasks_file);print(json.dumps(dict(rows=[{k:x[k] for k in ('task_id','enabled','valid','issues')} for x in r['rows']],wall_seconds=r['wall_seconds']),indent=2))


if __name__=='__main__':main()
