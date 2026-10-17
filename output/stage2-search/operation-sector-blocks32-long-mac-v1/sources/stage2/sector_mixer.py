"""Exact simulation inside the makespan single-excitation sector.

Stores k*2**n amplitudes for n binary choices and k makespan qubits, instead of
2**(n+k). This is a CLASSICAL simulation reduction from a circuit invariant;
the emitted circuit still has n+k logical qubits and all resource penalties.
No resource-feasible-state oracle, quantum hardware or speedup is implied.
"""
import math
import random
import time

import numpy as np

from .trajectory_mixer import circuit,invariant_block


def sector_energies(q,max_amplitudes=16_777_216):
    n,k=len(q.columns),len(q.makespans)
    if n<1 or k<1 or k*(1<<n)>max_amplitudes:
        raise ValueError('Declared invariant-sector amplitude budget exceeded')
    indices=np.arange(1<<n,dtype=np.uint64)
    masks=[((indices>>i)&1).astype(np.int64)for i in range(n)]
    base=np.full(1<<n,q.offset,dtype=np.int64)
    for i in range(n):
        base+=q.linear[i]*masks[i]
    for(i,j),value in q.quadratic.items():
        if j<n:
            base+=value*masks[i]*masks[j]
    energies=np.broadcast_to(base,(k,len(base))).copy()
    for register in range(k):
        j=n+register
        energies[register]+=q.linear[j]
        for i in range(n):
            value=q.quadratic.get((i,j),0)
            if value:
                energies[register]+=value*masks[i]
    return energies


def evolve_sector(q,energies,gammas,betas,scale):
    n,k=len(q.columns),len(q.makespans)
    if energies.shape!=(k,1<<n) or len(gammas)!=len(betas) or len(gammas)not in(1,2):
        raise ValueError('Matching declared binary/register sector and one/two layers required')
    state=np.full(energies.shape,1/math.sqrt(energies.size),dtype=np.complex128)
    phase=(energies.astype(float)-float(energies[0,0]))/scale
    for gamma,beta in zip(gammas,betas):
        state*=np.exp(-1j*gamma*phase)
        c,s=math.cos(beta),-1j*math.sin(beta)
        for bit in range(n):
            pairs=state.reshape(-1,2,1<<bit)
            a,b=pairs[:,0,:].copy(),pairs[:,1,:].copy()
            pairs[:,0,:]=c*a+s*b
            pairs[:,1,:]=c*b+s*a
        for register in range(k-1):
            a,b=state[register].copy(),state[register+1].copy()
            state[register]=c*a+s*b
            state[register+1]=c*b+s*a
    return state


def sample_sector(q,seed=7,layers=2,evaluations=64,shots=32,method='qaoa_xy'):
    if layers not in(1,2)or evaluations<4 or shots<1:
        raise ValueError('One/two layers, >=4 angle evaluations and positive shots required')
    began,cpu=time.perf_counter(),time.process_time()
    energies=sector_energies(q)
    block=invariant_block(q)
    scale=max([1]+[abs(v)for v in block['linear']]+[abs(v)for v in block['quadratic'].values()])
    rng=random.Random(seed)
    best=None
    calls=0
    centered=energies.astype(float)-float(energies[0,0])
    def evaluate(angles):
        nonlocal best,calls
        probability=np.abs(evolve_sector(q,energies,angles[:layers],angles[layers:],scale))**2
        value=float(np.dot(probability.ravel(),centered.ravel()))
        calls+=1
        if best is None or value<best[0]:
            best=value,list(angles),probability
        return value
    if method=='qaoa_xy':
        starts=[[.7]*layers+[.35]*layers,[rng.uniform(0,2*math.pi)for _ in range(2*layers)]]
        for angles in starts:
            value=evaluate(angles)
            limit=min(evaluations,calls+evaluations//2-1)
            step=.8
            while calls<limit:
                changed=False
                for axis in range(2*layers):
                    for direction in(-1,1):
                        if calls>=limit:break
                        trial=list(angles)
                        trial[axis]=(trial[axis]+direction*step)%(2*math.pi)
                        cost=evaluate(trial)
                        if cost<value:
                            angles,value,changed=trial,cost,True
                if not changed:step*=.5
        _,angles,probability=best
    elif method=='uniform_onehot':
        probability=np.full(energies.shape,1/energies.size)
        angles=None
    elif method=='exact':
        probability=np.zeros(energies.shape)
        probability.ravel()[int(np.argmin(energies))]=1
        angles=None
    else:
        raise ValueError('qaoa_xy, uniform_onehot or exact required')
    probability=probability/probability.sum()
    counts=np.random.default_rng(seed).multinomial(shots,probability.ravel())
    seen=np.flatnonzero(counts)
    winner=min(seen,key=lambda i:(int(energies.ravel()[i]),int(i)))
    n,k=len(q.columns),len(q.makespans)
    register,pattern=divmod(int(winner),1<<n)
    bits=[(pattern>>i)&1 for i in range(n)]+[int(i==register)for i in range(k)]
    energy=int(energies.ravel()[winner])
    if q.energy(bits)!=energy:
        raise AssertionError('Sector sample differs from conditional QUBO energy')
    optimum=int(np.min(energies))
    result=dict(method=method,simulation='exact makespan single-excitation sector',layers=layers,seed=seed,
                qubits=n+k,binary_choice_qubits=n,makespan_qubits=k,sector_amplitudes=energies.size,
                full_statevector_amplitudes=str(1<<(n+k)),shots=shots,angle_evaluations=calls,
                energy=energy,bits=bits,decoded=q.decode(bits),conditional_exact_energy=optimum,
                exact_hit_probability=float(probability[energies==optimum].sum()),
                sampled_exact_hits=int(counts.reshape(energies.shape)[energies==optimum].sum()),
                zero_penalty_probability=float(probability[energies<q.penalty].sum()),
                makespan_invariant_leakage=0.,
                observed_counts={str((int(i)%(1<<n))|(1<<(n+int(i)//(1<<n)))):int(counts[i])for i in seen},
                gammas=angles[:layers]if angles else None,betas=angles[layers:]if angles else None,
                cost_scale=scale,physical_qpu_calls=0,wall_seconds=time.perf_counter()-began,
                process_cpu_seconds=time.process_time()-cpu,
                scope='Exact classical simulation of the SAME logical W/XY circuit invariant sector. Logical qubit count is unchanged; resource/BOM conflicts remain penalized. Ideal exact-expectation training cost included.')
    if angles:
        result['qasm']=circuit(q,angles[:layers],angles[layers:],scale)
    return result
