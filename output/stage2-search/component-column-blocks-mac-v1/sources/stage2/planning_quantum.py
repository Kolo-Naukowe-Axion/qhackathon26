"""Small genuine QAOA blocks obtained by exact substitution in a planning QUBO.

No dispatch reward is substituted. Classical decomposition fixes the remaining
variables. Angle training uses noiseless simulated expectation values; reported
shot draws are classical Born sampling, not physical QPU calls or speedups.
"""
from __future__ import annotations

import math
import random
import time

import numpy as np

from .window_qubo import conditional_qubo


def energy_table(block, max_bits=16):
    n=len(block['linear'])
    if n>max_bits:raise ValueError('Explicit statevector cap:16 free QUBO bits')
    indices=np.arange(1<<n,dtype=np.uint64)
    table=np.full(1<<n,block['offset'],dtype=np.int64)
    for i,c in enumerate(block['linear']):table+=int(c)*((indices>>i)&1).astype(np.int64)
    for(i,j),c in block['quadratic'].items():table+=int(c)*(((indices>>i)&1)&((indices>>j)&1)).astype(np.int64)
    return table


def evolve(energies,n,gammas,betas,scale):
    if n<1 or n>16 or len(gammas)!=len(betas) or len(gammas)not in(1,2):raise ValueError('One/two layers and1–16bits required')
    if len(energies)!=(1<<n)or not math.isfinite(scale)or scale<=0:raise ValueError('Energy table/positive scale invalid')
    if not all(math.isfinite(v)for v in[*gammas,*betas]):raise ValueError('Finite angles required')
    state=np.full(1<<n,1/math.sqrt(1<<n),dtype=np.complex128)
    centered=(np.asarray(energies,dtype=float)-float(energies[0]))/scale
    for gamma,beta in zip(gammas,betas):
        state*=np.exp(-1j*gamma*centered)
        for bit in range(n):
            pairs=state.reshape(-1,2,1<<bit)
            a=pairs[:,0,:].copy();b=pairs[:,1,:].copy()
            pairs[:,0,:]=math.cos(beta)*a-1j*math.sin(beta)*b
            pairs[:,1,:]=math.cos(beta)*b-1j*math.sin(beta)*a
    return state


def optimize(block,energies,seed=0,layers=1,evaluations=64):
    """Expectation-only coordinate search. Never calls argmin on the energy table."""
    if evaluations<4:raise ValueError('At least4 declared angle evaluations required')
    n=len(block['linear']);scale=max([1]+[abs(v)for v in block['linear']]+[abs(v)for v in block['quadratic'].values()])
    rng=random.Random(seed);calls=0;best=None
    def evaluate(angles):
        nonlocal calls,best
        state=evolve(energies,n,angles[:layers],angles[layers:],scale)
        probabilities=np.abs(state)**2
        # Subtract only a fixed constant to keep cancellation under control.
        expectation=float(np.dot(probabilities,energies.astype(float)-float(energies[0])))
        calls+=1
        if best is None or expectation<best[0]:best=(expectation,list(angles),probabilities)
        return expectation
    starts=[[.7]*layers+[.35]*layers,[rng.uniform(0,2*math.pi)for _ in range(2*layers)]]
    for angles in starts:
        if calls>=evaluations:break
        value=evaluate(angles);step=.8
        # Each start receives its explicit share; no exact-solution teacher.
        limit=min(evaluations,calls+(evaluations//2)-1)
        while calls<limit:
            changed=False
            for axis in range(2*layers):
                for direction in(-1,1):
                    if calls>=limit:break
                    trial=list(angles);trial[axis]=(trial[axis]+direction*step)%(2*math.pi)
                    candidate=evaluate(trial)
                    if candidate<value:value=candidate;angles=trial;changed=True
            if not changed:step*=.5
    if best is None:raise AssertionError('No angle evaluation')
    return dict(gammas=best[1][:layers],betas=best[1][layers:],probabilities=best[2],
                expectation=best[0]+float(energies[0]),angle_evaluations=calls,cost_scale=scale)


def qasm(block,gammas,betas,scale):
    n=len(block['linear']);fields=[-c/2 for c in block['linear']]
    for(i,j),v in block['quadratic'].items():fields[i]-=v/4;fields[j]-=v/4
    lines=['OPENQASM 2.0;','include "qelib1.inc";',f'qreg q[{n}];',f'creg c[{n}];']
    for i in range(n):lines.append(f'h q[{i}];')
    for gamma,beta in zip(gammas,betas):
        for i,h in enumerate(fields):
            if h:lines.append(f'rz({2*gamma*h/scale:.17g}) q[{i}];')
        for(i,j),v in sorted(block['quadratic'].items()):
            lines.extend([f'cx q[{i}],q[{j}];',f'rz({gamma*v/(2*scale):.17g}) q[{j}];',f'cx q[{i}],q[{j}];'])
        for i in range(n):lines.append(f'rx({2*beta:.17g}) q[{i}];')
    lines.append('measure q -> c;')
    return '\n'.join(lines)+'\n'


def sample_block(q,free,fixed,method='qaoa',seed=0,shots=1024,evaluations=64,layers=1):
    began=time.perf_counter();cpu=time.process_time();block=conditional_qubo(q,free,fixed)
    energies=energy_table(block);n=len(free);optimization=None
    rng=np.random.default_rng(seed)
    if shots<1:raise ValueError('Positive shot/sample budget required')
    if method=='qaoa':
        optimization=optimize(block,energies,seed,layers,evaluations)
        probabilities=optimization.pop('probabilities');probabilities=probabilities/probabilities.sum()
    elif method=='uniform':probabilities=np.full(1<<n,1/(1<<n))
    elif method=='exact':
        # Explicit exact control, NEVER the source of a QAOA/uniform returned sample.
        probabilities=np.zeros(1<<n);probabilities[int(np.argmin(energies))]=1
    else:raise ValueError('Declared backends:qaoa,uniform,exact')
    counts=rng.multinomial(shots,probabilities);observed=np.flatnonzero(counts)
    winner=min(observed,key=lambda i:(int(energies[i]),int(i)))
    full=[fixed.get(i,0)for i in range(len(q.linear))]
    for j,i in enumerate(free):full[i]=(int(winner)>>j)&1
    assert q.energy(full)==int(energies[winner])
    # References are calculated only AFTER the actual sampled decision.
    optimum=int(np.min(energies));feasible=energies<q.penalty
    result=dict(method=method,free_bits=n,shots=shots,seed=seed,energy=int(energies[winner]),bits=full,
        observed_counts={str(int(i)):int(counts[i])for i in observed},conditional_exact_energy=optimum,
        sampled_exact_hits=int(counts[energies==optimum].sum()),exact_hit_probability=float(probabilities[energies==optimum].sum()),
        zero_penalty_probability=float(probabilities[feasible].sum()),decoded=q.decode(full),
        conditional_block=dict(linear=block['linear'],quadratic=[[i,j,v]for(i,j),v in sorted(block['quadratic'].items())],offset=block['offset'],free=free,fixed=[[i,v]for i,v in sorted(fixed.items())]),
        optimization=optimization,wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,
        quantum_algorithm_simulated=method=='qaoa',physical_qpu_calls=0,
        scope='Exact restriction of full planning-window QUBO. Unrestricted X mixer; best OBSERVED energy with classical postselection. Exact control reference never supplies QAOA/uniform output. All classical conditioning/statevector/angle work retained.')
    if optimization:result['qasm']=qasm(block,optimization['gammas'],optimization['betas'],optimization['cost_scale'])
    return result


def neighborhood(q,incumbent,seed=0,groups=3,alternatives=2,max_bits=16):
    """Classical decomposition chooses alternatives; conditional ENERGY is exact."""
    rng=random.Random(seed);names=[k for k in q.groups if k!='@makespan']
    selected=rng.sample(names,min(groups,len(names)));free=[];choices_by_group=[]
    for name in selected:
        members=q.groups[name];current=[i for i in members if incumbent[i]]
        if len(current)!=1:raise ValueError('A complete one-hot incumbent required')
        choices=[i for i in members if not incumbent[i]]
        extra=rng.sample(choices,min(alternatives,len(choices)))
        free.extend(sorted(current+extra))
        choices_by_group.append(current+extra)
    # Keep every potentially minimal makespan for these operation choices.
    # Nonminimal auxiliary values are dominated, not needed as free qubits.
    fixedmax=max((q.variables[i]['end']for n in names if n not in selected for i in q.groups[n]if incumbent[i]),default=0)
    possible={fixedmax}
    for options in choices_by_group:
        possible={max(t,q.variables[i]['end'])for t in possible for i in options}
    possible|={q.variables[i]['start']for i in q.groups['@makespan']if incumbent[i]}
    free.extend(i for i in q.groups['@makespan']if q.variables[i]['start']in possible)
    if len(free)>max_bits:raise ValueError('Neighborhood exceeds declared statevector budget')
    fixed={i:x for i,x in enumerate(incumbent)if i not in free}
    return free,fixed
