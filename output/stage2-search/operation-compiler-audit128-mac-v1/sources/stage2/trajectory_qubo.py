"""Compact quantum recombination of complete pump scheduling trajectories.

Each order has two classical feasible internal schedules. One binary variable
selects its ENTIRE route/BOM/crew/machine/time trajectory. Cross-order conflicts
and a one-hot makespan register form a genuine quadratic master problem.
This is exact for the supplied trajectory pool, a RESTRICTION of the original
discrete problem. All parent-generation cost and the full-model gap matter.
"""
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass

from .window_qubo import check_plan,digest


def terminal_cost(problem,plan):
    ops={o['id']:o for o in problem['operations']};nonterminal={prior for o in ops.values()for prior in o['predecessors']}
    return (problem['horizon']+1)*sum(ops[row['operation']].get('weight',1)*max(0,row['end']-ops[row['operation']]['due'])for row in plan if row['operation']not in nonterminal)


@dataclass
class TrajectoryQUBO:
    problem:dict
    columns:dict
    linear:list
    quadratic:dict
    offset:int
    penalty:int
    makespans:list
    conflicts:list

    def energy(self,bits):
        if len(bits)!=len(self.linear)or any(x not in(0,1)for x in bits):raise ValueError('Binary vector required')
        return self.offset+sum(v*x for v,x in zip(self.linear,bits))+sum(v*bits[i]*bits[j]for(i,j),v in self.quadratic.items())

    def decode(self,bits):
        n=len(self.columns)
        if sum(bits[n:])!=1:return dict(valid=False,issues=['makespan_one_hot'])
        plan=[row for i,columns in enumerate(self.columns.values())for row in columns[bits[i]]]
        checked=check_plan(self.problem,plan);end=self.makespans[bits[n:].index(1)]
        if checked['valid']and checked['makespan']>end:checked=dict(checked,valid=False,issues=['makespan_link'])
        return dict(checked,plan=plan,energy=self.energy(bits),encoded_makespan=end)

    def metadata(self):
        return dict(schema='stage2-complete-trajectory-recombination-qubo.v1',orders=len(self.columns),operations=len(self.problem['operations']),
            trajectory_choice_bits=len(self.columns),makespan_bits=len(self.makespans),variables=len(self.linear),couplers=len(self.quadratic),penalty=self.penalty,
            incompatible_trajectory_pairs=len(self.conflicts),problem_sha256=digest(self.problem),
            pool_sha256=digest(self.columns),scope='Exact objective/constraints over two supplied complete trajectories per order; all other raw schedules excluded. Classical parent generation is a substantive cost; no lossless global compression claim.')


def compile_trajectory_qubo(problem,columns):
    from .window_qubo import validate
    validate(problem);ops={o['id']:o for o in problem['operations']};covered=set();owner={}
    for name,options in columns.items():
        if len(options)!=2:raise ValueError('Exactly two trajectories per order required')
        ids={r['operation']for r in options[0]}
        if ids&covered:raise ValueError('Trajectory groups must partition operations')
        if any({r['operation']for r in plan}!=ids for plan in options):raise ValueError('Both trajectories must contain identical mandatory operations')
        sub=dict(problem,operations=[o for o in problem['operations']if o['id']in ids])
        if any(set(o['predecessors'])-ids for o in sub['operations']):raise ValueError('Cross-group precedence unsupported by this order-column constructor')
        for plan in options:
            if not check_plan(sub,plan)['valid']:raise ValueError('Each trajectory must be independently internally feasible')
        covered|=ids;owner.update({oid:name for oid in ids})
    if covered!=set(ops):raise ValueError('Every raw operation required exactly once')
    names=list(columns);n=len(names);ends=sorted({max(row['end']for row in plan)for options in columns.values()for plan in options})
    bound=sum(max(terminal_cost(problem,plan)for plan in options)for options in columns.values())+max(ends);penalty=bound+1
    linear=[0]*(n+len(ends));quad=defaultdict(int);offset=0;conflicts=[]
    # Affine expression for selecting trajectory value c: c=0 ->1-x, c=1 ->x.
    def add_pair(i,choice,j,other,value):
        nonlocal offset
        a,b=(1,-1)if choice==0 else(0,1);c,d=(1,-1)if other==0 else(0,1)
        offset+=value*a*c;linear[i]+=value*b*c;linear[j]+=value*d*a;quad[tuple(sorted((i,j)))]+=value*b*d
    for i,name in enumerate(names):
        costs=[terminal_cost(problem,p)for p in columns[name]];offset+=costs[0];linear[i]+=costs[1]-costs[0]
        for j,other in enumerate(names[i+1:],i+1):
            sub=dict(problem,operations=[o for o in problem['operations']if owner[o['id']]in(name,other)])
            for a in(0,1):
                for b in(0,1):
                    if not check_plan(sub,columns[name][a]+columns[other][b])['valid']:
                        conflicts.append([name,a,other,b]);add_pair(i,a,j,b,penalty)
        for choice,plan in enumerate(columns[name]):
            end=max(r['end']for r in plan)
            for j,t in enumerate(ends,n):
                if end>t:
                    # Affine trajectory choice multiplied by a plain makespan bit.
                    a,b=(1,-1)if choice==0 else(0,1);linear[j]+=penalty*a;quad[i,j]+=penalty*b
    offset+=penalty
    for i,t in enumerate(ends,n):
        linear[i]+=t-penalty
        for j in range(i+1,n+len(ends)):quad[i,j]+=2*penalty
    return TrajectoryQUBO(deepcopy(problem),deepcopy(columns),linear,{k:v for k,v in quad.items()if v},offset,penalty,ends,conflicts)


def columns_from_parents(problem,parents):
    if len(parents)!=2:raise ValueError('Two complete independently checked parents required')
    for parent in parents:
        if not check_plan(problem,parent)['valid']:raise ValueError('Invalid parent plan')
    names=sorted({o['id'].split('/')[0]for o in problem['operations']})
    return {name:[[row for row in plan if row['operation'].split('/')[0]==name]for plan in parents]for name in names}
