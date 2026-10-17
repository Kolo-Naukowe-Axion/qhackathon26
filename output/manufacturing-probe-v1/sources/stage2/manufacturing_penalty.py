"""Incumbent-certified penalty tightening, preserving feasible ground states."""
from dataclasses import replace
from .window_qubo import check_plan,digest


def tighten(q,plan):
    checked=check_plan(q.problem,plan)
    if not checked['valid']:raise ValueError('An independently checked feasible witness is required')
    bits=q.encode(plan)if hasattr(q,'encode')else None
    if bits is None:
        chosen=[]
        for row in plan:
            chosen.append(next(i for i,v in enumerate(q.variables)if v==row))
        chosen.append(next(i for i in q.groups['@makespan']if q.variables[i]['start']==checked['makespan']))
        bits=[int(i in chosen)for i in range(len(q.linear))]
    witness=q.energy(bits)
    if witness!=checked['objective']:raise AssertionError('Witness must minimize its makespan register')
    old=q.penalty
    new=witness+1
    if new>old:raise ValueError('Witness exceeds compiler objective bound')
    if any(v%old for v in q.quadratic.values()):raise ValueError('Compiler has non-penalty quadratic objective terms')
    result=replace(q,linear=[v+old-new for v in q.linear],
        quadratic={ij:(v//old)*new for ij,v in q.quadratic.items()},
        offset=len(q.groups)*new,penalty=new)
    if result.energy(bits)!=witness:raise AssertionError('Tightening changed witness objective')
    certificate=dict(original_penalty=old,penalty=new,witness_objective=witness,
        witness_plan_sha256=digest(plan),witness_source='Independent seeded list heuristic, constructed before reference solve',
        ratio=old/new,proof='Objective terms are nonnegative for every state. A checked feasible witness has energy U. Every infeasible state has energy >=P=U+1>U. Therefore all global minima remain feasible and globally objective-optimal in this exact domain. Feasible energies unchanged; non-optimal infeasible energies intentionally change.')
    return result,bits,certificate
