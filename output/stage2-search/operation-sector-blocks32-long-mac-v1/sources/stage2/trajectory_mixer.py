"""One-hot-preserving QAOA for the complete-trajectory restricted master.

Only the makespan register is constrained by this mixer. Resource-incompatible
trajectory combinations still have their original penalties. No optimum oracle
or feasible-schedule enumeration prepares the initial state: binary choices are
|+>, makespan is the uniform single-excitation W state.
"""
import math
import random
import time

import numpy as np

from .planning_quantum import energy_table,qasm


def invariant_block(q):
    n=len(q.columns);linear=list(q.linear);quad=dict(q.quadratic)
    # Remove P(sum z-1)^2, identically zero on the invariant subspace.
    for i in range(n,len(linear)):
        linear[i]+=q.penalty
        for j in range(i+1,len(linear)):
            quad[i,j]=quad.get((i,j),0)-2*q.penalty
            if not quad[i,j]:quad.pop((i,j),None)
    return dict(linear=linear,quadratic=quad,offset=q.offset-q.penalty)


def initial_state(q):
    n=len(q.columns);k=len(q.makespans);total=len(q.linear)
    if total>16:raise ValueError('Statevector cap16')
    state=np.zeros(1<<total,dtype=np.complex128)
    for z in range(k):state[(np.arange(1<<n,dtype=np.int64)|(1<<(n+z)))]=1/math.sqrt((1<<n)*k)
    return state


def evolve(q,energies,gammas,betas,scale):
    n=len(q.columns);total=len(q.linear);state=initial_state(q);indices=np.arange(len(state),dtype=np.int64)
    phase=(energies.astype(float)-float(energies[0]))/scale
    for gamma,beta in zip(gammas,betas):
        state*=np.exp(-1j*gamma*phase)
        for bit in range(n):
            pairs=state.reshape(-1,2,1<<bit);a=pairs[:,0,:].copy();b=pairs[:,1,:].copy()
            pairs[:,0,:]=math.cos(beta)*a-1j*math.sin(beta)*b;pairs[:,1,:]=math.cos(beta)*b-1j*math.sin(beta)*a
        # Ordered nearest-neighbor XY partial mixers form a connected chain.
        for i in range(n,total-1):
            j=i+1;one=np.flatnonzero(((indices>>i)&1)&(1-((indices>>j)&1)));other=one^((1<<i)|(1<<j))
            a=state[one].copy();b=state[other].copy();state[one]=math.cos(beta)*a-1j*math.sin(beta)*b;state[other]=math.cos(beta)*b-1j*math.sin(beta)*a
    return state


def circuit(q,gammas,betas,scale):
    n=len(q.columns);k=len(q.makespans);block=invariant_block(q)
    generic=qasm(block,gammas,betas,scale).splitlines();header=generic[:4]
    header+=['gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }',
             'gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }']
    lines=header+[f'h q[{i}];'for i in range(n)]+[f'x q[{n}];']
    for j in range(k-1):
        theta=math.acos(1/math.sqrt(k-j));i=n+j
        lines.extend([f'rxx({theta:.17g}) q[{i}],q[{i+1}];',f'ryy({theta:.17g}) q[{i}],q[{i+1}];',f's q[{i+1}];'])
    # Reuse only the independently understood cost rotations from generic QASM.
    fields=[-v/2 for v in block['linear']]
    for(i,j),v in block['quadratic'].items():fields[i]-=v/4;fields[j]-=v/4
    for gamma,beta in zip(gammas,betas):
        for i,value in enumerate(fields):
            if value:lines.append(f'rz({2*gamma*value/scale:.17g}) q[{i}];')
        for(i,j),value in sorted(block['quadratic'].items()):lines.extend([f'cx q[{i}],q[{j}];',f'rz({gamma*value/(2*scale):.17g}) q[{j}];',f'cx q[{i}],q[{j}];'])
        lines.extend(f'rx({2*beta:.17g}) q[{i}];'for i in range(n))
        for i in range(n,len(q.linear)-1):lines.extend([f'rxx({beta:.17g}) q[{i}],q[{i+1}];',f'ryy({beta:.17g}) q[{i}],q[{i+1}];'])
    return '\n'.join(lines+['measure q -> c;'])+'\n'


def sample(q,seed=7,layers=1,evaluations=64,shots=512,method='qaoa_xy'):
    if layers not in(1,2)or evaluations<4 or shots<1:raise ValueError('One/two layers, >=4 angle evaluations and positive shots required')
    began=time.perf_counter();cpu=time.process_time();n=len(q.linear);block=invariant_block(q)
    energies=energy_table(dict(linear=q.linear,quadratic=q.quadratic,offset=q.offset));rng=random.Random(seed);best=None;calls=0
    scale=max([1]+[abs(v)for v in block['linear']]+[abs(v)for v in block['quadratic'].values()])
    def evaluate(angles):
        nonlocal best,calls
        state=evolve(q,energies,angles[:layers],angles[layers:],scale);probability=np.abs(state)**2;value=float(np.dot(probability,energies.astype(float)-float(energies[0])));calls+=1
        if best is None or value<best[0]:best=(value,list(angles),probability)
        return value
    if method=='uniform_onehot':probability=np.abs(initial_state(q))**2;angles=None
    elif method=='qaoa_xy':
        starts=[[.7]*layers+[.35]*layers,[rng.uniform(0,2*math.pi)for _ in range(2*layers)]]
        for angles in starts:
            value=evaluate(angles);limit=min(evaluations,calls+evaluations//2-1);step=.8
            while calls<limit:
                changed=False
                for axis in range(2*layers):
                    for direction in(-1,1):
                        if calls>=limit:break
                        trial=list(angles);trial[axis]=(trial[axis]+direction*step)%(2*math.pi);cost=evaluate(trial)
                        if cost<value:angles=trial;value=cost;changed=True
                if not changed:step*=.5
        _,angles,probability=best
    else:raise ValueError('qaoa_xy or uniform_onehot required')
    probability=probability/probability.sum();counts=np.random.default_rng(seed).multinomial(shots,probability);seen=np.flatnonzero(counts);winner=min(seen,key=lambda i:(int(energies[i]),int(i)));bits=[(int(winner)>>i)&1 for i in range(n)]
    if q.energy(bits)!=int(energies[winner]):raise AssertionError('Master sample energy mismatch')
    optimum=int(energies.min());excitation=np.array([sum((i>>j)&1 for j in range(len(q.columns),n))for i in range(1<<n)])
    row=dict(method=method,layers=layers,seed=seed,qubits=n,shots=shots,angle_evaluations=calls,
        energy=q.energy(bits),bits=bits,decoded=q.decode(bits),conditional_exact_energy=optimum,
        exact_hit_probability=float(probability[energies==optimum].sum()),zero_penalty_probability=float(probability[energies<q.penalty].sum()),
        makespan_invariant_leakage=float(probability[excitation!=1].sum()),observed_counts={str(int(i)):int(counts[i])for i in seen},
        gammas=angles[:layers]if angles else None,betas=angles[layers:]if angles else None,cost_scale=scale,
        phase_couplers=len(block['quadratic']),original_phase_couplers=len(q.quadratic),
        wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,physical_qpu_calls=0,
        scope='W-state makespan register and ordered XY chain mixer; binary trajectory choices use X. Only makespan one-hot is preserved, resource incompatibilities retain penalties. Reference argmin never supplies sampled output.')
    if angles:row['qasm']=circuit(q,angles[:layers],angles[layers:],scale)
    return row
