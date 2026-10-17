"""Classical list-scheduling column generation without a full QUBO matrix."""
import random
import time

from .window_qubo import assignments,conflict_reasons,check_plan,digest


def generate(problem,attempts=64,wanted=8,seed=7001,seconds=30):
    began=time.perf_counter();cpu=time.process_time();ops={o['id']:o for o in problem['operations']}
    domains={name:sorted(assignments(problem,op),key=lambda row:(row['end'],row['start'],row['machine'],row['worker']))for name,op in ops.items()}
    raw_count=sum(map(len,domains.values()))
    if raw_count>500000:raise ValueError('Local raw-domain cap500000 assignments')
    if any(not domain for domain in domains.values()):raise ValueError('An operation has an empty raw assignment domain')
    tails={}
    def tail(name):
        if name not in tails:tails[name]=min(ops[name]['durations'].values())+max((tail(op['id'])for op in ops.values()if name in op['predecessors']),default=0)
        return tails[name]
    for name in ops:tail(name)
    parents=[];keys=set();history=[];checks=0
    for trial in range(attempts):
        if time.perf_counter()-began>=seconds:break
        rng=random.Random(seed+trial*1009);chosen=set();plan=[]
        while len(chosen)<len(ops):
            ready=[op for op in ops.values()if op['id']not in chosen and set(op['predecessors'])<=chosen]
            ready.sort(key=lambda op:(op['due']-tails[op['id']],op['id']))
            op=ready[0]if trial==0 else rng.choice(ready[:min(4,len(ready))]);alternatives=[]
            # Stop after enough EARLIEST feasible alternatives; no objective solver.
            target=1 if trial==0 or rng.random()<.8 else 3
            for row in domains[op['id']]:
                legal=True
                for prior in plan:
                    checks+=1
                    if conflict_reasons(problem,row,prior,ops):legal=False;break
                if legal:alternatives.append(row)
                if len(alternatives)>=target:break
            if not alternatives:break
            row=rng.choice(alternatives);plan.append(row);chosen.add(op['id'])
        complete=len(chosen)==len(ops);entry=dict(trial=trial,complete=complete,scheduled=len(chosen))
        if complete:
            checked=check_plan(problem,plan)
            if not checked['valid']:raise AssertionError('Classical parent failed raw schedule checker')
            plan=sorted(plan,key=lambda row:row['operation']);key=digest(plan);entry.update(objective=checked['objective'],distinct=key not in keys)
            if key not in keys:parents.append(plan);keys.add(key)
        history.append(entry)
        if len(parents)>=wanted:break
    return dict(parents=parents,history=history,raw_assignment_candidates=raw_count,compatibility_checks=checks,
        wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,
        cp_teacher_used=False,scope='Seeded randomized topological list scheduling over raw finite domains; no time-indexed QUBO matrix built. Every complete parent independently checked.')
