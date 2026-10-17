"""Causal reward ablations over identical frozen dispatch candidates.

No physical or candidate-domain change. The process-local override is restored
in finally and refuses nested or cross-thread execution.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor,as_completed
from contextlib import contextmanager
from copy import deepcopy
import gzip
import hashlib
import json
import multiprocessing
from pathlib import Path
import threading
import time
import traceback

from .admission import AdmissionMixin
from .kit_recovery import RecoveryFactory
from .recovery_routing import BASE_WEIGHTS,ROOT,SOURCES as SHARED_SOURCES

SOURCES=('stage2/selector_reward.py',)+SHARED_SOURCES
_ACTIVE=False
MODES=('original','no-batch','priority-lex')


def reweight(candidates,priorities,mode):
    """Keep IDs/resources fixed; return explicit stable operation-rank weights."""
    if mode not in MODES:raise ValueError('Unknown selector reward')
    if len(candidates)!=len(priorities):raise ValueError('Candidate/priority length mismatch')
    result=deepcopy(candidates)
    if mode=='no-batch':
        lo=min(priorities,default=0);hi=max(priorities,default=0)
        for candidate,priority in zip(result,priorities):candidate['reward']=200+100*(hi-priority)/(1+hi-lo)
    elif mode=='priority-lex':
        # Fixed-domain ordering only. Equal public priorities break stably by
        # the original engine request index, rather than a hidden future key.
        order=sorted(range(len(result)),key=lambda j:(priorities[j],j));n=len(order)
        for rank,j in enumerate(order):result[j]['reward']=2**(n-1-rank)
    return result


@contextmanager
def reward_override(mode,records=None):
    global _ACTIVE
    from . import dispatch
    from .qubo import select
    if mode not in MODES:raise ValueError('Unknown selector reward')
    if _ACTIVE:raise RuntimeError('Nested/concurrent reward override prohibited')
    original=dispatch.choose;owner=threading.get_ident();_ACTIVE=True
    def wrapped(offers,instance,active,tick,grid_cap,priorities,method='greedy',seed=0):
        if threading.get_ident()!=owner:raise RuntimeError('Reward override cannot cross threads')
        if mode=='original':return original(offers,instance,active,tick,grid_cap,priorities,method,seed)
        started=time.perf_counter()
        # The unchanged constructor computes every original machine/unit/tool/
        # worker-interval conflict and every cumulative power capacity. Its
        # cheap greedy result is retained as preprocessing, never as our solver.
        _,evidence=original(offers,instance,active,tick,grid_cap,priorities,'greedy',seed)
        construction_seconds=time.perf_counter()-started;legacy=deepcopy(evidence['candidates'])
        candidates=reweight(legacy,priorities,mode)
        result=select(candidates,evidence['conflicts'],evidence['capacities'],method=method,seed=seed,sweeps=100,restarts=4)
        result['objective']=dict(mode=mode,scope='Same original frozen operation/crew candidate domain',
            stable_ties='Original request index after equal public priority',
            original_candidate_rewards=[c['reward'] for c in legacy],
            public_priorities=list(priorities),construction_including_greedy_seconds=construction_seconds)
        evidence.update(candidates=candidates,result=result)
        if records is not None:records.append(dict(tick=tick,mode=mode,candidates=len(candidates),
            construction_including_greedy_seconds=construction_seconds,total_wall_seconds=time.perf_counter()-started))
        return [int(cid[1:]) for cid in result['selected']],evidence
    dispatch.choose=wrapped
    try:yield
    finally:dispatch.choose=original;_ACTIVE=False


class RewardMixin:
    def __init__(self,*args,reward_mode='original',**kwargs):
        if reward_mode not in MODES:raise ValueError('Unknown selector reward')
        super().__init__(*args,**kwargs);self.reward_mode=reward_mode;self.reward_records=[]

    def run(self):
        # Default delegates directly, so every original numerical/physical
        # decision and existing candidate-domain limitation is preserved.
        if self.reward_mode=='original':return super().run()
        with reward_override(self.reward_mode,self.reward_records):return super().run()

    def finish(self):
        super().finish()
        self.trace.setdefault('algorithm_audit',{})['selector_reward']=dict(mode=self.reward_mode,
            calls=deepcopy(self.reward_records),scope='Reward-only ablation; original offers,resource conflicts and capacities',
            lexicographic_limit='Dominates lower-ranked candidate rewards within this fixed pool; not global factory optimality or sequential worker reassignment')


class RewardFactory(RewardMixin,RecoveryFactory):pass
class AdmissionRewardFactory(AdmissionMixin,RewardFactory):pass


def run(instance,weights=None,controller=None,*,admission=False,**options):
    cls=AdmissionRewardFactory if admission else RewardFactory
    return cls(instance,weights,controller,**options).run()


def hashes():return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def diagnostic_tasks():
    tasks=[]
    for selector,mode in [('priority','original')]+[('exact',m) for m in MODES]:
        for seed in list(range(8))+[15,23,25,26]:
            tasks.append(dict(task_id=len(tasks),policy_id=f'{selector}-{mode}',config=dict(orders=12,horizon=5760,profile='full',seed=seed),
                weights=dict(BASE_WEIGHTS,selector=selector,policy_seed=7),solver_options=dict(admission=True,
                    tool_policy={'mode':'hard'},kit_reservation=True,recovery_policy={'enabled':True},reward_mode=mode),
                seed_role='TRAIN0–7 plus diagnosed failures15/23/25/26',retain_trace=True))
    return tasks


def simulate(task):
    from .spec import build
    from .check import check_trace
    start=time.perf_counter();cpu=time.process_time();trace=None;factory=None
    row={k:deepcopy(task[k]) for k in ('task_id','policy_id','config','weights','solver_options','seed_role')}
    try:
        if task['config']['seed'] not in range(32):raise ValueError('Only TRAIN0–31 are authorized by this driver')
        if hashes()!=task['source_hashes']:raise RuntimeError('Source drift before episode')
        instance=build(**task['config']);options=deepcopy(task['solver_options']);cls=AdmissionRewardFactory if options.pop('admission',False) else RewardFactory
        factory=cls(instance,task['weights'],**options);trace=factory.run();checked=check_trace(trace)
        mismatches=[d['tick'] for d in trace['qubo_decisions'] if sorted(d['result']['selected'])!=sorted(d['committed'])]
        row.update(valid=checked['valid'] and not mismatches,issues=checked['issues'],decode_mismatches=mismatches,
            metrics=trace['metrics'],physical_instance_sha256=hashlib.sha256(json.dumps(instance,sort_keys=True).encode()).hexdigest(),
            reward_audit=trace['algorithm_audit']['selector_reward'])
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
    protocol=dict(schema='stage2-selector-reward.v1',tasks=tasks,source_hashes=sources,workers=workers,
        scope='TRAIN reward ablation; candidate constraints unchanged; no validation/final tapes')
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
