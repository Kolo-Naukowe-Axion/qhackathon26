"""Exact local dual-rail elimination, with independently testable affine map.

When a mandatory group has exactly two surviving candidates, x_a+x_b=1 permits
x_a=1-z and x_b=z. Affine substitution keeps the energy quadratic, eliminates
one qubit per such group, and preserves every one-hot assignment of the declared
neighborhood. It does not compress an arbitrary global planning instance to a
few qubits, nor compute any optimum as preprocessing.
"""
from collections import defaultdict
import time

import numpy as np

from .planning_quantum import energy_table,optimize,qasm
from .window_qubo import conditional_qubo


def compress(q,free,fixed):
    original=conditional_qubo(q,free,fixed);positions={i:j for j,i in enumerate(free)};expressions={};eliminated=[];count=0
    for name,group in q.groups.items():
        active=[i for i in group if i in positions]
        if len(active)==2 and all(fixed.get(i,0)==0 for i in group if i not in positions):
            a,b=sorted(active);expressions[positions[a]]=(1,count,-1);expressions[positions[b]]=(0,count,1)
            eliminated.append(dict(group=name,complement=a,variable=b,reduced_index=count));count+=1
    for j in range(len(free)):
        if j not in expressions:expressions[j]=(0,count,1);count+=1
    linear=[0]*count;quadratic=defaultdict(int);offset=original['offset']
    for i,value in enumerate(original['linear']):
        c,j,a=expressions[i];offset+=value*c;linear[j]+=value*a
    for(i,k),value in original['quadratic'].items():
        c,j,a=expressions[i];d,l,b=expressions[k];offset+=value*c*d;linear[j]+=value*a*d;linear[l]+=value*b*c
        if j==l:linear[j]+=value*a*b
        else:quadratic[tuple(sorted((j,l)))]+=value*a*b
    block=dict(linear=linear,quadratic={k:v for k,v in quadratic.items()if v},offset=offset)
    return dict(block=block,original=original,expressions=expressions,eliminated=eliminated,
        original_bits=len(free),compressed_bits=count,objective_used=False,incumbent_cost_used=False)


def expand(reduction,values):
    return [c+a*values[j]for i,(c,j,a)in sorted(reduction['expressions'].items())]


def sample_compressed(q,free,fixed,method='qaoa',seed=0,shots=512,evaluations=48,layers=1):
    began=time.perf_counter();cpu=time.process_time();reduction=compress(q,free,fixed);block=reduction['block'];energies=energy_table(block);n=len(block['linear'])
    if shots<1:raise ValueError('Positive shots required')
    optimization=None
    if method=='qaoa':
        optimization=optimize(block,energies,seed,layers,evaluations);probabilities=optimization.pop('probabilities');probabilities/=probabilities.sum()
    elif method=='uniform':probabilities=np.full(1<<n,1/(1<<n))
    elif method=='exact':probabilities=np.zeros(1<<n);probabilities[int(np.argmin(energies))]=1
    else:raise ValueError('Unknown method')
    counts=np.random.default_rng(seed).multinomial(shots,probabilities);observed=np.flatnonzero(counts);winner=min(observed,key=lambda i:(int(energies[i]),int(i)))
    values=[(int(winner)>>j)&1 for j in range(n)];original=expand(reduction,values);full=[fixed.get(i,0)for i in range(len(q.linear))]
    for i,v in zip(free,original):full[i]=v
    if q.energy(full)!=int(energies[winner]):raise AssertionError('Compressed energy differs from full QUBO')
    optimum=int(np.min(energies))
    result=dict(method='compressed_'+method,original_free_bits=len(free),free_bits=n,shots=shots,seed=seed,layers=layers,
        energy=int(energies[winner]),bits=full,decoded=q.decode(full),conditional_exact_energy=optimum,
        exact_hit_probability=float(probabilities[energies==optimum].sum()),zero_penalty_probability=float(probabilities[energies<q.penalty].sum()),
        sampled_exact_hits=int(counts[energies==optimum].sum()),observed_counts={str(int(i)):int(counts[i])for i in observed},
        optimization=optimization,reduction=dict(eliminated=reduction['eliminated'],objective_used=False,scope='All one-hot assignments of this conditional neighborhood retained'),
        conditional_block=dict(linear=block['linear'],quadratic=[[i,j,v]for(i,j),v in sorted(block['quadratic'].items())],offset=block['offset'],free=free,fixed=[[i,v]for i,v in sorted(fixed.items())]),
        physical_qpu_calls=0,quantum_algorithm_simulated=method=='qaoa',wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu)
    if optimization:result['qasm']=qasm(block,optimization['gammas'],optimization['betas'],optimization['cost_scale'])
    return result
