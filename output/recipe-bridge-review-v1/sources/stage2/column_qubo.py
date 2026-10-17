"""Multi-choice component-trajectory QUBO, retaining cross-component BOM edges.

Unlike two whole-pump trajectories, independent component trajectories create a
much larger recombination space. Every selected trajectory retains actual future
machine/worker/time assignments; cross-group resource and BOM incompatibilities
are penalized. Exact for the supplied finite column pool only.
"""
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass

from .window_qubo import validate,check_plan,digest
from .trajectory_qubo import terminal_cost


def subproblem(problem,ids):
    operations=[dict(op,predecessors=[p for p in op['predecessors']if p in ids])for op in problem['operations']if op['id']in ids]
    return dict(problem,operations=operations)


@dataclass
class ColumnQUBO:
    problem:dict
    columns:dict
    groups:dict
    variables:list
    linear:list
    quadratic:dict
    offset:int
    penalty:int
    objective_bound:int
    pair_conflicts:list

    def energy(self,bits):
        if len(bits)!=len(self.linear)or any(x not in(0,1)for x in bits):raise ValueError('One binary value per column/register bit required')
        return self.offset+sum(v*x for v,x in zip(self.linear,bits))+sum(v*bits[i]*bits[j]for(i,j),v in self.quadratic.items())

    def decode(self,bits):
        if any(sum(bits[i]for i in group)!=1 for group in self.groups.values()):return dict(valid=False,issues=['one_hot_column_or_makespan'])
        plan=[];choices={}
        for name,options in self.columns.items():
            i=next(i for i in self.groups[name]if bits[i]);choice=self.variables[i]['choice'];choices[name]=choice;plan.extend(options[choice])
        end=next(self.variables[i]['end']for i in self.groups['@makespan']if bits[i]);checked=check_plan(self.problem,plan)
        if checked['valid']and checked['makespan']>end:checked=dict(checked,valid=False,issues=['makespan_link'])
        return dict(checked,plan=plan,choices=choices,encoded_makespan=end,energy=self.energy(bits))

    def encode(self,plan):
        if not check_plan(self.problem,plan)['valid']:raise ValueError('A complete valid raw plan required')
        bits=[0]*len(self.linear)
        for name,options in self.columns.items():
            ids={r['operation']for r in options[0]};part=sorted((r for r in plan if r['operation']in ids),key=lambda r:r['operation']);key=digest(part)
            choices=[k for k,p in enumerate(options)if digest(sorted(p,key=lambda r:r['operation']))==key]
            if not choices:raise ValueError('Raw plan outside this trajectory pool:'+name)
            bits[self.groups[name][choices[0]]]=1
        end=max(r['end']for r in plan);bits[next(i for i in self.groups['@makespan']if self.variables[i]['end']==end)]=1
        return bits

    def metadata(self):
        combinations=1
        for options in self.columns.values():combinations*=len(options)
        return dict(schema='stage2-component-column-qubo.v1',operations=len(self.problem['operations']),column_groups=len(self.columns),
            variables=len(self.linear),couplers=len(self.quadratic),column_choices={k:len(v)for k,v in self.columns.items()},
            unconstrained_pattern_combinations=str(combinations),makespan_bits=len(self.groups['@makespan']),penalty=self.penalty,
            feasible_objective_upper_bound=self.objective_bound,incompatible_column_pairs=len(self.pair_conflicts),problem_sha256=digest(self.problem),pool_sha256=digest(self.columns),
            scope='All supplied component choices and cross-component BOM/resource constraints retained. Exact within restricted pool, not lossless full raw-model compression.')


def compile_columns(problem,columns):
    validate(problem);ops={o['id']:o for o in problem['operations']};covered=set();group_ids={}
    variables=[];groups={};cost=[];bound=0
    for name,options in columns.items():
        if not options:raise ValueError('Every mandatory component needs a trajectory')
        ids={r['operation']for r in options[0]}
        if ids&covered or not ids:raise ValueError('Nonempty disjoint operation partition required')
        for option in options:
            if {r['operation']for r in option}!=ids or not check_plan(subproblem(problem,ids),option)['valid']:raise ValueError('Internally invalid or mismatched component trajectory')
        covered|=ids;group_ids[name]=ids;groups[name]=[];values=[]
        for choice,option in enumerate(options):
            groups[name].append(len(variables));variables.append(dict(group=name,choice=choice,end=max(r['end']for r in option)))
            value=terminal_cost(problem,option);cost.append(value);values.append(value)
        bound+=max(values)
    if covered!=set(ops):raise ValueError('Columns must partition ALL raw operations')
    # In a complete DAG every operation precedes a terminal. Therefore a feasible
    # makespan is the end of a terminal operation, not any arbitrary column end.
    nonterminal={p for o in ops.values()for p in o['predecessors']};terminal=set(ops)-nonterminal
    ends=sorted({r['end']for options in columns.values()for option in options for r in option if r['operation']in terminal})
    lower=max((min(max(r['end']for r in option if r['operation']in terminal)for option in options)
               for name,options in columns.items()if group_ids[name]&terminal),default=0)
    ends=[t for t in ends if t>=lower];groups['@makespan']=[]
    for t in ends:groups['@makespan'].append(len(variables));variables.append(dict(group='@makespan',end=t));cost.append(t)
    bound+=max(ends);penalty=bound+1;linear=list(cost);quad=defaultdict(int);offset=penalty*len(groups);conflicts=[]
    for members in groups.values():
        for k,i in enumerate(members):
            linear[i]-=penalty
            for j in members[k+1:]:quad[i,j]+=2*penalty
    names=list(columns)
    for ai,a in enumerate(names):
        for b in names[ai+1:]:
            raw=subproblem(problem,group_ids[a]|group_ids[b])
            for ca,first in enumerate(columns[a]):
                for cb,second in enumerate(columns[b]):
                    if not check_plan(raw,first+second)['valid']:
                        i,j=groups[a][ca],groups[b][cb];quad[i,j]+=penalty;conflicts.append([i,j])
        for ca,option in enumerate(columns[a]):
            end=max(r['end']for r in option);i=groups[a][ca]
            for j in groups['@makespan']:
                if end>variables[j]['end']:quad[i,j]+=penalty
    return ColumnQUBO(deepcopy(problem),deepcopy(columns),groups,variables,linear,dict(quad),offset,penalty,bound,conflicts)


def component_columns(parents):
    pool=defaultdict(dict)
    for plan in parents:
        parts=defaultdict(list)
        for row in plan:parts['/'.join(row['operation'].split('/')[:2])].append(row)
        for name,rows in parts.items():
            rows=sorted(rows,key=lambda r:r['operation']);pool[name][digest(rows)]=rows
    return {name:list(values.values())for name,values in sorted(pool.items())}
