"""Classical and quantum-block search of the SAME complete window QUBO."""
from __future__ import annotations

import math
import random
import time

from .window_qubo import conflict_reasons


def constructive(q):
    """Earliest-finish topological heuristic, not a CP teacher or hidden optimum."""
    ops={o['id']:o for o in q.problem['operations']};chosen={};plan=[]
    while len(chosen)<len(ops):
        ready=[o for o in ops.values()if o['id']not in chosen and set(o['predecessors'])<=set(chosen)]
        if not ready:raise ValueError('No topological frontier')
        op=min(ready,key=lambda o:(o['due'],o['id']));options=sorted(q.groups[op['id']],key=lambda i:(q.variables[i]['end'],q.variables[i]['start'],i))
        feasible=[i for i in options if all(not conflict_reasons(q.problem,q.variables[i],a,ops)for a in plan)]
        if not feasible:return dict(valid=False,reason='constructive_dead_end',scheduled=len(chosen),cp_teacher_used=False)
        i=feasible[0];chosen[op['id']]=i;plan.append(q.variables[i])
    makespan=max(a['end']for a in plan);chosen['@makespan']=next(i for i in q.groups['@makespan']if q.variables[i]['start']==makespan)
    bits=[int(i in chosen.values())for i in range(len(q.linear))]
    checked=q.decode(bits)
    if not checked['valid']:raise AssertionError('Constructive schedule failed independent checking')
    return dict(valid=True,bits=bits,energy=q.energy(bits),decoded=checked,cp_teacher_used=False)


def anneal(q,seed=0,proposals=30000,restarts=4,initial=None):
    """One-hot-preserving Metropolis moves; makespan register minimized exactly.

    Domain preservation is explicit classical preprocessing, not post-hoc repair.
    No schedule constraint is removed from the QUBO energy used for acceptance.
    """
    if proposals<1 or restarts<1:raise ValueError('Positive proposal/restart budgets required')
    began=time.perf_counter();cpu=time.process_time();rng=random.Random(seed);adj=[[]for _ in q.linear]
    for(i,j),v in q.quadratic.items():adj[i].append((j,v));adj[j].append((i,v))
    names=[n for n in q.groups if n!='@makespan'];zmap={q.variables[i]['start']:i for i in q.groups['@makespan']}
    best=None;accepted=0;total=0
    for restart in range(restarts):
        if initial is not None:
            bits=list(initial)
        else:
            selected={rng.choice(g)for g in q.groups.values()};bits=[int(i in selected)for i in range(len(q.linear))]
        chosen={n:next(i for i in q.groups[n]if bits[i])for n in q.groups}
        # Exact auxiliary minimization for this complete assignment.
        currentmax=max(q.variables[chosen[n]]['end']for n in names)
        bits[chosen['@makespan']]=0;chosen['@makespan']=zmap[currentmax];bits[chosen['@makespan']]=1
        fields=[q.linear[i]+sum(v*bits[j]for j,v in adj[i])for i in range(len(bits))]
        energy=q.energy(bits)
        if best is None or energy<best[0]:best=(energy,list(bits))
        high=max(q.penalty,1)*(2 if restart else .25);low=1
        for step in range(proposals):
            total+=1;name=rng.choice(names);old=chosen[name];new=rng.choice(q.groups[name])
            if new==old:continue
            newmax=max(q.variables[new if n==name else chosen[n]]['end']for n in names)
            oldz=chosen['@makespan'];newz=zmap[newmax]
            changes={old:-1,new:1}
            if oldz!=newz:changes.update({oldz:-1,newz:1})
            items=list(changes.items());delta=sum(fields[i]*d for i,d in items)
            delta+=sum(q.quadratic.get(tuple(sorted((i,j))),0)*di*dj for k,(i,di)in enumerate(items)for j,dj in items[k+1:])
            temperature=high*(low/high)**(step/max(1,proposals-1))
            if delta<=0 or rng.random()<math.exp(-delta/temperature):
                accepted+=1
                for i,d in items:
                    bits[i]+=d
                    for j,v in adj[i]:fields[j]+=v*d
                chosen[name]=new;chosen['@makespan']=newz;energy+=delta
                if energy<best[0]:best=(energy,list(bits))
            if step%5000==0 and energy!=q.energy(bits):raise AssertionError('Incremental QUBO energy drift')
    if best[0]!=q.energy(best[1]):raise AssertionError('Returned QUBO energy mismatch')
    return dict(method='one_hot_annealing',seed=seed,proposals=total,restarts=restarts,accepted=accepted,
                energy=best[0],bits=best[1],decoded=q.decode(best[1]),
                wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,
                initial_cp_teacher_used=False,repairs=0,
                scope='One-hot-preserving search with analytic makespan-register minimization; every accepted move scored by original full QUBO energy. Initial source must be disclosed separately.')


def block_search(q,initial,method='qaoa',seed=0,iterations=12,shots=1024,evaluations=64):
    from .planning_quantum import neighborhood,sample_block
    if not q.decode(initial)['valid']:raise ValueError('A physically checked feasible incumbent is required')
    began=time.perf_counter();cpu=time.process_time();bits=list(initial);energy=q.energy(bits);history=[]
    for step in range(iterations):
        free,fixed=neighborhood(q,bits,seed+step*101,groups=3,alternatives=1)
        result=sample_block(q,free,fixed,method,seed+step*1009,shots,evaluations)
        before=energy
        if result['energy']<energy:
            if not result['decoded']['valid']:raise AssertionError('Energy improvement from feasible incumbent is infeasible')
            energy=result['energy'];bits=result['bits']
        result['incumbent_energy_before']=before;result['incumbent_energy_after']=energy
        history.append(result)
    return dict(method='conditional_'+method,seed=seed,iterations=iterations,energy=energy,bits=bits,
                decoded=q.decode(bits),history=history,wall_seconds=time.perf_counter()-began,
                process_cpu_seconds=time.process_time()-cpu,repairs=0,
                scope='Classical neighborhood construction and incumbent retention around exact conditional full-planning QUBOs. Angle training/statevector/shot work all included. No physical quantum execution.')
