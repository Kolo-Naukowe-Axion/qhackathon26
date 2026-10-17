"""Sparse compiler specialized to singleton operation columns.

Unary rows are checked once. Binary incompatibilities use the already tested
raw assignment conflict predicate, avoiding repeated whole-resource calendar
validation for every pair. Independent reference/decode checkers are unchanged.
"""
from collections import defaultdict
from copy import deepcopy

from .column_qubo import ColumnQUBO,subproblem
from .trajectory_qubo import terminal_cost
from .window_qubo import validate,check_plan,conflict_reasons


def compile_operations(problem,columns):
    validate(problem)
    ops={op['id']:op for op in problem['operations']}
    groups,variables,cost={},[],[]
    if set(columns)!=set(ops):
        raise ValueError('One operation-named group per raw operation required')
    bound=0
    for name,options in columns.items():
        if not options:
            raise ValueError('Nonempty unary column pool required')
        groups[name]=[]
        values=[]
        raw=subproblem(problem,{name})
        for choice,option in enumerate(options):
            if len(option)!=1 or option[0]['operation']!=name or not check_plan(raw,option)['valid']:
                raise ValueError('Every column must contain one valid matching raw operation')
            groups[name].append(len(variables))
            variables.append(dict(group=name,choice=choice,end=option[0]['end']))
            value=terminal_cost(problem,option)
            cost.append(value)
            values.append(value)
        bound+=max(values)
    nonterminal={p for op in ops.values()for p in op['predecessors']}
    terminals=set(ops)-nonterminal
    ends=sorted({option[0]['end']for name,options in columns.items()if name in terminals for option in options})
    lower=max(min(option[0]['end']for option in columns[name])for name in terminals)
    ends=[end for end in ends if end>=lower]
    groups['@makespan']=[]
    for end in ends:
        groups['@makespan'].append(len(variables))
        variables.append(dict(group='@makespan',end=end))
        cost.append(end)
    bound+=max(ends)
    penalty=bound+1
    linear=list(cost)
    quadratic=defaultdict(int)
    offset=penalty*len(groups)
    for members in groups.values():
        for k,i in enumerate(members):
            linear[i]-=penalty
            for j in members[k+1:]:
                quadratic[i,j]+=2*penalty
    conflicts=[]
    names=list(columns)
    for ai,a in enumerate(names):
        for b in names[ai+1:]:
            for ca,first in enumerate(columns[a]):
                for cb,second in enumerate(columns[b]):
                    if conflict_reasons(problem,first[0],second[0],ops):
                        i,j=groups[a][ca],groups[b][cb]
                        quadratic[i,j]+=penalty
                        conflicts.append([i,j])
        for ca,option in enumerate(columns[a]):
            i=groups[a][ca]
            for j in groups['@makespan']:
                if option[0]['end']>variables[j]['end']:
                    quadratic[i,j]+=penalty
    return ColumnQUBO(deepcopy(problem),deepcopy(columns),groups,variables,linear,
                      dict(quadratic),offset,penalty,bound,conflicts)
