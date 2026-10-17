"""Constraint-guided trajectory-neighborhood proposals, without a CP teacher."""
import random
import time

from .window_qubo import conflict_reasons
from .planning_compressed import sample_compressed


def guided_neighborhood(q,bits,seed=0,groups=5,max_bits=16):
    rng=random.Random(seed);ops={o['id']:o for o in q.problem['operations']};names=list(ops)
    chosen={name:next(i for i in q.groups[name]if bits[i])for name in names}
    successors={name:[o['id']for o in ops.values()if name in o['predecessors']]for name in names}
    terminal=[name for name in names if not successors[name]]
    if rng.random()<.5:
        anchor=max(terminal,key=lambda name:(q.variables[chosen[name]]['end']-ops[name]['due'],rng.random()))
    else:anchor=rng.choice(names)
    neighbors={name:set(ops[name]['predecessors']+successors[name])for name in names}
    for resource in('machine','worker'):
        values={q.variables[i][resource]for i in chosen.values()}
        for value in values:
            ordered=sorted((name for name in names if q.variables[chosen[name]][resource]==value),key=lambda name:q.variables[chosen[name]]['start'])
            for a,b in zip(ordered,ordered[1:]):neighbors[a].add(b);neighbors[b].add(a)
    selected=[anchor];front=list(neighbors[anchor]);rng.shuffle(front)
    while front and len(selected)<groups:
        name=front.pop(0)
        if name in selected:continue
        selected.append(name);extra=list(neighbors[name]-set(selected));rng.shuffle(extra);front.extend(extra)
    options={};checks=0
    fixed_rows=[q.variables[i]for name,i in chosen.items()if name not in selected]
    for name in selected:
        current=q.variables[chosen[name]];legal=[]
        for i in q.groups[name]:
            candidate=q.variables[i]
            if i==chosen[name]or candidate['end']>current['end']:continue
            okay=True
            for row in fixed_rows:
                checks+=1
                if conflict_reasons(q.problem,candidate,row,ops):okay=False;break
            if okay:legal.append(i)
        if legal:
            legal.sort(key=lambda i:(q.variables[i]['end'],q.variables[i]['start'],rng.random()))
            # Mix earliest alternatives with nearby changes; all from raw domains.
            if rng.random()<.5:extra=legal[0]
            else:
                nearest=sorted(legal,key=lambda i:(abs(current['start']-q.variables[i]['start']),rng.random()));extra=rng.choice(nearest[:min(3,len(nearest))])
            options[name]=[chosen[name],extra]
    while True:
        free=[i for choices in options.values()for i in choices]
        fixedmax=max((q.variables[i]['end']for name,i in chosen.items()if name not in options),default=0);possible={fixedmax}
        for choices in options.values():possible={max(t,q.variables[i]['end'])for t in possible for i in choices}
        possible|={q.variables[i]['start']for i in q.groups['@makespan']if bits[i]}
        free.extend(i for i in q.groups['@makespan']if q.variables[i]['start']in possible)
        if len(free)<=max_bits:break
        options.pop(next(reversed(options)))
    fixed={i:v for i,v in enumerate(bits)if i not in free}
    return free,fixed,dict(anchor=anchor,selected_groups=selected,variable_groups=list(options),compatibility_checks=checks,
        proposal_scope='Classical DAG/resource-chain selection; no-later alternatives individually compatible with fixed schedule. All interactions among free groups remain in exact QUBO. Plateau acceptance allowed. No CP or exact optimality teacher.')


def guided_search(q,initial,method='exact',seed=7,iterations=128,shots=512,evaluations=48):
    if not q.decode(initial)['valid']:raise ValueError('Checked feasible initial schedule required')
    began=time.perf_counter();cpu=time.process_time();rng=random.Random(seed);bits=list(initial);energy=q.energy(bits);best=(energy,list(bits));history=[]
    for step in range(iterations):
        free,fixed,proposal=guided_neighborhood(q,bits,seed+step*1009)
        result=sample_compressed(q,free,fixed,method,seed+step*73,shots,evaluations)
        accepted=result['energy']<energy or(result['energy']==energy and rng.random()<.5)
        if accepted:
            if not result['decoded']['valid']:raise AssertionError('Nonworsening result from feasible incumbent must be feasible')
            bits=result['bits'];energy=result['energy']
        if energy<best[0]:best=(energy,list(bits))
        result.update(proposal=proposal,accepted=accepted,incumbent_energy_after=energy,best_energy_after=best[0]);history.append(result)
    return dict(method='guided_compressed_'+method,seed=seed,iterations=iterations,energy=best[0],bits=best[1],decoded=q.decode(best[1]),history=history,
        wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,cp_teacher_used=False,physical_qpu_calls=0)
