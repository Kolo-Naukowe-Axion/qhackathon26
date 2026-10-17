"""Budgeted NumPy QAOA experiment, separate from the five-bit hardware profile.

CPU simulation only. The QUBO is a fixed action pool, including every slack bit.
No factory, dispatch, constraint or original quantum backend is changed here.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import platform
import time

import numpy as np

from .qubo import QUBO, anneal, greedy_reference
from .quantum import problem_metadata, _scale


class BudgetExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class Budget:
    max_bits: int = 20
    memory_mib: float = 1024
    seconds: float = 60
    evaluations: int = 32
    chunk_states: int = 65536
    reference_core_bits: int = 16
    sa_sweeps: int = 50
    sa_restarts: int = 2

    def validate(self):
        if not 1 <= self.max_bits <= 24:
            raise ValueError("Total-bit cap must be 1..24, including slack")
        if not math.isfinite(self.seconds) or self.seconds <= 0:
            raise ValueError("Positive finite time budget required")
        if not math.isfinite(self.memory_mib) or self.memory_mib <= 0:
            raise ValueError("Positive finite memory budget required")
        if self.evaluations < 1 or self.chunk_states < 2 or self.chunk_states & (self.chunk_states-1):
            raise ValueError("Positive evaluations and power-of-two chunk >=2 required")
        if not 0 <= self.reference_core_bits <= 20 or min(self.sa_sweeps,self.sa_restarts) < 1:
            raise ValueError("Reference cap must be 0..20; SA budgets positive")


def memory_estimate(n: int, chunk_states=65536) -> int:
    """Conservative numerical-array allowance; Python/runtime RSS is additional.

    64 bytes/basis state covers energy, complex state, probabilities/CDF and
    expression temporaries; 16 MiB + chunk workspace covers bounded scratch.
    """
    return 64*(1 << n) + 16*1024**2 + 128*min(1 << n,chunk_states)


def _validate_qubo(q):
    if len(q.candidates) > q.size or q.size > 24:
        raise ValueError("Invalid core/total variable count")
    if not all(math.isfinite(x) for x in [q.offset,*q.linear,*q.quadratic.values()]):
        raise ValueError("Finite QUBO coefficients required")
    if any(not 0 <= i < j < q.size for i,j in q.quadratic):
        raise ValueError("Expected strictly upper-triangular QUBO terms, counted once")


class Kernel:
    """Float64 energies, complex128 amplitudes; basis index bit i is variable i."""
    def __init__(self, q: QUBO, budget: Budget = Budget()):
        budget.validate(); _validate_qubo(q)
        if q.size > budget.max_bits:
            raise BudgetExceeded(f"{q.size} total bits exceed cap {budget.max_bits} (slack included)")
        self.estimated_bytes=memory_estimate(q.size,budget.chunk_states)
        if self.estimated_bytes > budget.memory_mib*1024**2:
            raise BudgetExceeded("Conservative numerical-array memory allowance exceeds budget")
        self.q,self.budget=q,budget
        self.started=time.perf_counter(); self.deadline=self.started+budget.seconds
        self.evaluations=0; self.size=1 << q.size
        self.energies=np.empty(self.size,dtype=np.float64)
        for lo,hi,indices in self.chunks():
            self.guard()
            values=np.full(hi-lo,q.offset,dtype=np.float64)
            for i,a in enumerate(q.linear):
                if a: values += a*((indices >> i)&1)
            for (i,j),a in q.quadratic.items():
                values += a*(((indices >> i)&1)&((indices >> j)&1))
            self.energies[lo:hi]=values
        if not np.isfinite(self.energies).all():
            raise ValueError("QUBO energy overflow")
        self.preprocessing_seconds=time.perf_counter()-self.started

    def guard(self):
        if time.perf_counter() > self.deadline:
            raise BudgetExceeded("Cooperative elapsed-time budget exhausted")

    def chunks(self, size=None):
        for lo in range(0,self.size if size is None else size,self.budget.chunk_states):
            hi=min(lo+self.budget.chunk_states,self.size if size is None else size)
            yield lo,hi,np.arange(lo,hi,dtype=np.uint32)

    def evolve(self,gammas,betas,cost_scale=None, *, charge=True):
        if len(gammas) != len(betas) or not 1 <= len(gammas) <= 4:
            raise ValueError("Matching one to four QAOA layers required")
        if not all(math.isfinite(x) for x in [*gammas,*betas]):
            raise ValueError("Finite angles required")
        scale=_scale(self.q) if cost_scale is None else float(cost_scale)
        if not math.isfinite(scale) or scale <= 0: raise ValueError("Positive finite scale required")
        if charge and self.evaluations >= self.budget.evaluations:
            raise BudgetExceeded("Angle-evaluation budget exhausted")
        self.guard()
        if charge: self.evaluations += 1
        state=np.full(self.size,1/math.sqrt(self.size),dtype=np.complex128)
        chunk=self.budget.chunk_states
        for gamma,beta in zip(gammas,betas):
            for lo,hi,_ in self.chunks():
                self.guard()
                state[lo:hi] *= np.exp((-1j*gamma/scale)*(self.energies[lo:hi]-self.q.offset))
            cosine,sine=math.cos(beta),-1j*math.sin(beta)
            for qubit in range(self.q.size):
                stride=1 << qubit
                if stride <= chunk//2:
                    # Batch many small butterflies together, avoiding millions of Python loops.
                    for lo in range(0,self.size,chunk):
                        self.guard()
                        view=state[lo:min(lo+chunk,self.size)].reshape(-1,2,stride)
                        a,b=view[:,0,:].copy(),view[:,1,:].copy()
                        view[:,0,:]=cosine*a+sine*b
                        view[:,1,:]=sine*a+cosine*b
                else:
                    for block in range(0,self.size,2*stride):
                        for off in range(0,stride,chunk):
                            self.guard(); length=min(chunk,stride-off)
                            left=slice(block+off,block+off+length)
                            right=slice(block+stride+off,block+stride+off+length)
                            a,b=state[left].copy(),state[right].copy()
                            state[left]=cosine*a+sine*b
                            state[right]=sine*a+cosine*b
        return state


def statevector(q,gammas,betas,*,budget=Budget(),cost_scale=None):
    return Kernel(q,budget).evolve(gammas,betas,cost_scale)


def _classification(q,indices):
    """Independent resource/conflict classification, never inferred from QUBO energy."""
    feasible=np.ones(len(indices),dtype=bool); reward=np.zeros(len(indices))
    for i,c in enumerate(q.candidates): reward += c.reward*((indices >> i)&1)
    for i,j in q.conflicts: feasible &= ~((((indices >> i)&1)&((indices >> j)&1)).astype(bool))
    for resource,cap in q.capacities.items():
        load=np.zeros(len(indices),dtype=np.int64)
        for i,c in enumerate(q.candidates): load += c.resources.get(resource,0)*((indices >> i)&1).astype(np.int64)
        feasible &= load <= cap
    return feasible,reward


def _sample(q,counts):
    rows=[]
    for state,count in sorted(counts.items()):
        bits=[(int(state)>>i)&1 for i in range(q.size)]
        chosen=[i for i in range(len(q.candidates)) if bits[i]]
        rows.append(dict(state=int(state),bitstring=format(int(state),f"0{q.size}b"),count=int(count),
            bits=bits,indices=chosen,feasible=q.feasible(chosen),energy=q.energy(bits),
            reward=sum(q.candidates[i].reward for i in chosen)))
    valid=[r for r in rows if r['feasible']]
    if valid:
        best=max(valid,key=lambda r:(r['reward'],-r['energy'],r['count'],-r['state']))
        chosen=best['indices']; repaired=False
    else:
        best=min(rows,key=lambda r:(r['energy'],r['state']))
        chosen=greedy_reference(q,best['indices']); repaired=True
    return dict(selected=[q.candidates[i].id for i in chosen],reward=sum(q.candidates[i].reward for i in chosen),
        feasible=q.feasible(chosen),repaired=repaired,raw=best,samples=rows,
        raw_counts={r['bitstring']:r['count'] for r in rows},
        sampled_core_feasible_fraction=sum(r['count'] for r in valid)/sum(counts.values()))


def _exact_reference(kernel):
    q=kernel.q; n=len(q.candidates)
    if n > kernel.budget.reference_core_bits:
        return dict(status='skipped_core_budget',core_bits=n,max_core_bits=kernel.budget.reference_core_bits)
    best=-math.inf; mask=0; feasible_count=0
    for _,_,indices in kernel.chunks(1 << n):
        kernel.guard(); valid,reward=_classification(q,indices); feasible_count += int(valid.sum())
        values=np.where(valid,reward,-np.inf); k=int(np.argmax(values))
        if values[k] > best: best=float(values[k]); mask=int(indices[k])
    chosen=[i for i in range(n) if mask>>i&1]
    if not q.feasible(chosen): raise AssertionError('Independent reference feasibility disagreement')
    return dict(status='exact',selected=[q.candidates[i].id for i in chosen],reward=best,
        selections_examined=1 << n,feasible_selections=feasible_count,proven_optimal_within_pool=True)


def select_qaoa(q,*,seed=0,layers=1,shots=1024,budget=Budget(),angles=None):
    """Auditable simulator experiment with separate equal-shot uniform/exact/SA controls.

    All costs included in elapsed_seconds. Deadline checks are cooperative, not an
    OS hard kill; an over-budget run raises rather than silently changing solver.
    Final selected actions come only from samples, except explicit greedy repair.
    """
    started=time.perf_counter()
    if layers not in (1,2,3,4) or not isinstance(shots,int) or not 1 <= shots <= 1_000_000:
        raise ValueError('Layers1..4 and shots1..1000000 required')
    kernel=Kernel(q,budget); scale=_scale(q); rng=np.random.default_rng(seed)
    history=[]; best_value=math.inf; best_theta=None; optimize_started=time.perf_counter()
    if angles is not None:
        if len(angles) != 2*layers: raise ValueError('Angles are all gamma then all beta')
        trials=[list(angles)]
    else:
        trials=[[0.0]*(2*layers)]
    # Deterministic bounded random search followed by coordinate refinement.
    while kernel.evaluations < (1 if angles is not None else budget.evaluations):
        if kernel.evaluations and time.perf_counter()-kernel.started > budget.seconds*.65: break
        if trials: theta=trials.pop(0)
        elif kernel.evaluations < min(8,budget.evaluations//2):
            theta=[*rng.uniform(-math.pi,math.pi,layers),*rng.uniform(-math.pi/2,math.pi/2,layers)]
        else:
            theta=best_theta.copy(); j=(kernel.evaluations//2)%(2*layers)
            theta[j] += (-1 if kernel.evaluations%2 else 1)*(.7/(1+kernel.evaluations/(4*layers)))
        state=kernel.evolve(theta[:layers],theta[layers:],scale)
        probs=np.abs(state); probs *= probs
        value=float(np.dot(probs,kernel.energies)); del state,probs
        if value < best_value:
            best_value,best_theta=value,list(map(float,theta))
            history.append(dict(evaluation=kernel.evaluations,expected_energy=value,angles=best_theta))
    optimization_seconds=time.perf_counter()-optimize_started
    final_started=time.perf_counter()
    # This reconstruction is an additional, explicitly counted statevector evolution.
    state=kernel.evolve(best_theta[:layers],best_theta[layers:],scale,charge=False)
    probabilities=np.abs(state); probabilities *= probabilities; del state
    norm=float(probabilities.sum()); probabilities /= norm
    probability_digest=hashlib.sha256(memoryview(probabilities.astype('<f8',copy=False))).hexdigest()
    sampled=Counter(map(int,rng.choice(kernel.size,size=shots,p=probabilities)))
    uniform_rng=np.random.default_rng(seed ^ 0xB451)
    uniform_counts=Counter(map(int,uniform_rng.integers(0,kernel.size,size=shots)))
    selected=_sample(q,sampled); uniform=_sample(q,uniform_counts)
    sampling_seconds=time.perf_counter()-final_started
    reference_started=time.perf_counter(); reference=_exact_reference(kernel)
    reference_seconds=time.perf_counter()-reference_started
    if reference['status']=='exact':
        for control in (selected,uniform):
            control['sampled_exact_reward_hit_fraction']=sum(r['count'] for r in control['samples'] if r['feasible'] and math.isclose(r['reward'],reference['reward'],rel_tol=0,abs_tol=1e-8))/shots
    diagnostics_started=time.perf_counter(); ground=float(kernel.energies.min())
    ideal=dict(core_feasible_probability=0.,zero_penalty_probability=0.,qubo_ground_probability=0.,
        exact_reward_hit_probability=0. if reference['status']=='exact' else None,
        uniform_core_feasible_probability=0.,uniform_exact_reward_hit_probability=0. if reference['status']=='exact' else None)
    for lo,hi,indices in kernel.chunks():
        kernel.guard(); valid,reward=_classification(q,indices); p=probabilities[lo:hi]; e=kernel.energies[lo:hi]
        ideal['core_feasible_probability'] += float(p[valid].sum())
        ideal['uniform_core_feasible_probability'] += float(valid.sum())/kernel.size
        ideal['zero_penalty_probability'] += float(p[valid & np.isclose(e,-reward,rtol=0,atol=1e-8)].sum())
        ideal['qubo_ground_probability'] += float(p[np.isclose(e,ground,rtol=0,atol=1e-8)].sum())
        if reference['status']=='exact':
            hit=valid & np.isclose(reward,reference['reward'],rtol=0,atol=1e-8)
            ideal['exact_reward_hit_probability'] += float(p[hit].sum())
            ideal['uniform_exact_reward_hit_probability'] += float(hit.sum())/kernel.size
    if reference['status']=='exact':
        uniform['probability_at_least_one_exact_in_same_shots']=-math.expm1(shots*math.log1p(-ideal['uniform_exact_reward_hit_probability'])) if ideal['uniform_exact_reward_hit_probability'] < 1 else 1.
    diagnostics_seconds=time.perf_counter()-diagnostics_started; del probabilities
    kernel.guard(); sa_started=time.perf_counter()
    sa=anneal(q,seed,budget.sa_sweeps,budget.sa_restarts)
    chosen=[i for i in range(len(q.candidates)) if sa['bits'][i]]; raw_feasible=q.feasible(chosen)
    if not raw_feasible: chosen=greedy_reference(q,chosen)
    sa.update(selected=[q.candidates[i].id for i in chosen],reward=sum(q.candidates[i].reward for i in chosen),
        raw_feasible=raw_feasible,feasible=q.feasible(chosen),repaired=not raw_feasible)
    sa_seconds=time.perf_counter()-sa_started; kernel.guard()
    fields=[-a/2 for a in q.linear]
    for (i,j),a in q.quadratic.items(): fields[i]-=a/4; fields[j]-=a/4
    hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('quantum_scaling.py','qubo.py','quantum.py')}
    return dict(schema='stage2-quantum-scaling.v1',method='numpy_qaoa_statevector' if q.size else 'classical_empty_pool',
        quantum_executed=False,physical_quantum_executed=False,quantum_algorithm_simulated=q.size>0,
        **selected,proven_optimal_within_pool=False,qubo=q.summary(),problem=problem_metadata(q),
        seed=seed,shots=shots,budget=asdict(budget),estimated_array_memory_bytes=kernel.estimated_bytes,
        optimization=dict(method='seeded_random_then_coordinate_exact_expectation',
            evaluations=kernel.evaluations,final_reconstruction_evolutions=1,
            gamma=best_theta[:layers],beta=best_theta[layers:],cost_scale=scale,
            expected_energy=best_value,history_best_improvements=history,fixed_angles=angles is not None),
        circuit=dict(layers=layers,qubits=q.size,cost='exp(-i gamma (QUBO-offset)/scale)',
            mixer='exp(-i beta sum X)',precision='complex128/float64',
            bit_order='basis index bit i is variable i; counts q[n-1]...q[0]',
            logical_gate_counts=dict(h=q.size,rz=layers*(sum(a!=0 for a in fields)+len(q.quadratic)),
                cx=2*layers*len(q.quadratic),rx=layers*q.size),
            gate_count_scope='H then merged RZ fields, CX-RZ-CX per nonzero ZZ, RX; no transpilation'),
        ideal=ideal,exact_ground_energy=ground,probabilities_sha256_float64_little_endian=probability_digest,
        uniform=dict(shots=shots,seed=seed ^ 0xB451,**uniform),reference=reference,sa=sa,
        timings=dict(preprocessing_seconds=kernel.preprocessing_seconds,angle_optimization_seconds=optimization_seconds,
            final_evolution_and_sampling_seconds=sampling_seconds,exact_reference_seconds=reference_seconds,
            ideal_diagnostics_seconds=diagnostics_seconds,sa_seconds=sa_seconds),
        elapsed_seconds=time.perf_counter()-started,source_sha256=hashes,
        runtime=dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform(),backend='CPU'),
        preprocessing_scope='QUBO energy table included; caller-side candidate generation and build_qubo are outside select_qaoa and must be timed by caller',
        limitations=['Classical noiseless circuit simulation; no QPU execution or quantum advantage.',
            'Fixed candidate domain only; preprocessing, exact angle expectation and postselection are classical.',
            'Deadline is cooperative; memory allowance excludes Python/runtime baseline and retained JSON.',
            'Uniform uses equal shots; SA/exact have separately disclosed, unequal computational work.'])


def main():
    import argparse
    from .qubo import build_qubo
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path); parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--bits',type=int,default=20); parser.add_argument('--memory-mib',type=float,default=1024)
    parser.add_argument('--seconds',type=float,default=60); parser.add_argument('--evaluations',type=int,default=32)
    parser.add_argument('--shots',type=int,default=1024); parser.add_argument('--layers',type=int,default=1)
    parser.add_argument('--seed',type=int,default=0)
    args=parser.parse_args()
    if args.output.exists(): raise ValueError('Output exists; preserve earlier evidence')
    data=json.loads(args.input.read_text()); build_started=time.perf_counter()
    q=build_qubo(data['candidates'],data.get('conflicts',()),data.get('capacities',{}))
    build_seconds=time.perf_counter()-build_started
    result=select_qaoa(q,seed=args.seed,layers=args.layers,shots=args.shots,
        budget=Budget(max_bits=args.bits,memory_mib=args.memory_mib,seconds=args.seconds,evaluations=args.evaluations))
    result['timings']['build_qubo_seconds']=build_seconds
    result['elapsed_including_qubo_construction_seconds']=result['elapsed_seconds']+build_seconds
    result['input_sha256']=hashlib.sha256(args.input.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('qubo','reward','feasible','reference','ideal','timings','elapsed_seconds')},indent=2))


if __name__=='__main__': main()
