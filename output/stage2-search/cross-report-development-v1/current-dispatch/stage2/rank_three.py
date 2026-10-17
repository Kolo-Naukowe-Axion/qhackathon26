"""Three semantic order bits with a certified nonlinear fourth-bit decoder.

Isolated baseline-B research candidate. Construction uses physical cuts and SAT
proofs, followed by exhaustive validation; no schedule labels fit the QUBO.
Quantum and IQM dependencies are imported only by their explicit offline phases.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import mean
import time

from .rank_probe import _clauses,sat_proof,verify_unsat_proof,partial_critical_path,earliest_schedule,independent_grid_score
from .rank_quantum import RankEnergy,canonical_digest
from solver.stage1 import validate

ROOT=Path(__file__).resolve().parents[1]


def add(*polynomials):
    result=Counter()
    for polynomial in polynomials:
        for term,value in polynomial.items():result[term]+=value
    return {term:value for term,value in result.items()if value}


def neg(polynomial):return {term:-value for term,value in polynomial.items()}


def mul(*polynomials):
    result={():1}
    for polynomial in polynomials:
        following=Counter()
        for left,a in result.items():
            for right,b in polynomial.items():following[tuple(sorted(set(left)|set(right)))]+=a*b
        result={term:value for term,value in following.items()if value}
    return result


def derive_polynomial():
    one={():1};a={(0,):1};b={(1,):1};d={(2,):1}
    c=add(one,neg(a),mul(a,b))
    physical=mul(add(one,b),a,add(one,neg(d)))
    triangle=add(b,neg(mul(b,d)),neg(mul(b,c)),mul(c,d))
    energy=add(physical,triangle)
    if any(len(term)>2 for term in energy):raise AssertionError('Cubic terms did not cancel')
    return energy,c,physical,triangle


def four_penalties():
    one={():1};a={(0,):1};b={(1,):1};c={(2,):1};d={(3,):1}
    return [mul(b,add(one,neg(c))),mul(add(one,neg(a)),add(one,neg(c))),
        mul(add(one,neg(c)),add(one,neg(d))),mul(a,add(one,neg(d))),
        add(b,neg(mul(a,b)),neg(mul(b,c)),mul(a,c)),
        add(b,neg(mul(b,d)),neg(mul(b,c)),mul(c,d))]


def decode(bits):
    if len(bits)!=3 or any(value not in (0,1)for value in bits):raise ValueError('Expected binary [a,b,d]')
    a,b,d=bits;c=1-a+a*b
    return [a,b,c,a,b,c,d,b,c]


def model_energy(model,bits):
    return model['offset']+sum(a*b for a,b in zip(model['linear'],bits))+sum(value*bits[i]*bits[j]for i,j,value in model['quadratic'])


def structural_compile(instance,four,cuts):
    """Only numerical physics, structural cuts and the old polynomial enter."""
    started=time.perf_counter()
    if canonical_digest(instance)!=four['instance_sha256']or four['horizon']!=8:raise ValueError('Expected the certified official H8 instance')
    if four['decoder']['equal_variable_groups']!=[[0,3],[1,4,7],[2,5,8],[6]]:raise ValueError('Unexpected semantic variable aliases')
    expected=add(*four_penalties())
    supplied={():four['offset'],**{(i,):value for i,value in enumerate(four['linear'])if value},
              **{(i,j):value for i,j,value in four['quadratic']if value}}
    if supplied!=expected:raise ValueError('Four-bit source differs from the six-penalty decomposition')
    for cut in cuts:
        witness=partial_critical_path(instance,cut['assignments'])
        if witness is None or witness['lower_bound']<=8:raise AssertionError('Physical cut has no deadline witness')
    clauses=_clauses(cuts);proofs=[]
    def impossible(assumptions,purpose):
        answer=sat_proof(clauses,assumptions)
        if answer['satisfiable']:raise AssertionError(f'Unproved structural implication: {purpose}')
        verify_unsat_proof(clauses,assumptions,answer['unsat_proof'])
        proofs.append(dict(purpose=purpose,assumptions=[[i,value]for i,value in sorted(assumptions.items())],**answer))
    # Reprove all five alias edges from physical clauses rather than trusting a label list.
    for group in four['decoder']['equal_variable_groups']:
        for other in group[1:]:
            impossible({group[0]:0,other:1},'equal semantic variables')
            impossible({group[0]:1,other:0},'equal semantic variables')
    for a in (0,1):
        for b in (0,1):
            c=1-a+a*b
            impossible({0:a,1:b,2:1-c},'c = NOT a OR b')
    polynomial,c,physical,triangle=derive_polynomial()
    model=dict(schema='rank-nonlinear-deadline-qubo.v1',encoding='structural-nonlinear-semantic-rank',
        instance_sha256=canonical_digest(instance),horizon=8,
        variables=[dict(index=0,name='a',original_order_bit=0),dict(index=1,name='b',original_order_bit=1),dict(index=2,name='d',original_order_bit=6)],
        offset=polynomial.get((),0),linear=[polynomial.get((i,),0)for i in range(3)],
        quadratic=[[term[0],term[1],value]for term,value in sorted(polynomial.items())if len(term)==2],
        decoder=dict(semantic_bit_order=['a','b','d'],derived_c='1-a+a*b',full_order_bit_expressions=['a','b','c','a','b','c','d','b','c'],
            kind='nonlinear Boolean semantic relation; not a schedule lookup table'),
        construction=dict(prior_four_bit=four['construction'],additional_physical_cut_rechecks=len(cuts),
            additional_sat_queries=len(proofs),additional_sat_search_nodes=sum(row['search_nodes']for row in proofs),
            complete_schedule_scores_used=0,lp_variables=0,
            disclosure='Reuses certified physical/SAT preprocessing; adds independently replayed semantic implications'),
        zero_set_scope='All H8 feasible full machine orders via deterministic nonlinear decoder; positive energies need not equal E4')
    proof=dict(schema='stage2-three-bit-structural-proof.v1',clauses=clauses,sat_implication_proofs=proofs,
        c_polynomial=[dict(bits=list(term),coefficient=value)for term,value in sorted(c.items())],
        nonnegative_summands=['(1+b)*a*(1-d)','b-b*d-b*c+c*d, with c=1-a+a*b'],
        expanded_summands=[[dict(bits=list(term),coefficient=value)for term,value in sorted(p.items())]for p in (physical,triangle)],
        exact_cubic_cancellation=True,construction_seconds=time.perf_counter()-started)
    return model,proof


def verify(instance,model,four):
    basis=[];decoded_good=[]
    for state in range(8):
        bits=[(state>>i)&1 for i in range(3)];full=decode(bits);a,b,d=bits;c=full[2]
        summands=[(1+b)*a*(1-d),b-b*d-b*c+c*d]
        assert all(value>=0 for value in summands)
        energy=model_energy(model,bits);old=model_energy(four,[a,b,c,d])
        assert energy==sum(summands)and ((energy==0)==(old==0))
        schedule=earliest_schedule(instance,full)
        errors=None if schedule is None else validate(instance,schedule['schedule'],schedule['makespan'])
        good=schedule is not None and not errors and schedule['makespan']<=8
        assert (energy==0)==good
        expanded=sum(value<<i for i,value in enumerate(full))
        if good:decoded_good.append(expanded)
        basis.append(dict(state=state,bitstring=format(state,'03b'),bits=bits,expanded_order_bits=full,
            expanded_state=expanded,c=c,energy=energy,four_bit_energy=old,nonnegative_summands=summands,
            makespan=None if schedule is None else schedule['makespan'],
            schedule=None if schedule is None else schedule['schedule'],official_validator_errors=errors,deadline_success=good))
    good_original=[];official_schedules=0
    for state in range(512):
        full=[(state>>i)&1 for i in range(9)];makespan=independent_grid_score(instance,full)
        good=makespan is not None and makespan<=8
        reduced=[full[0],full[1],full[6]]
        represented=decode(reduced)==full and model_energy(model,reduced)==0
        assert represented==good
        if good:good_original.append(state)
        schedule=earliest_schedule(instance,full)
        if schedule is not None:
            assert not validate(instance,schedule['schedule'],schedule['makespan'])
            assert schedule['makespan']==makespan;official_schedules+=1
    assert sorted(decoded_good)==good_original and len(set(decoded_good))==5
    return dict(schema='stage2-three-bit-verification.v1',basis=basis,
        original_order_bitstrings_checked=512,official_schedules_validated=official_schedules,
        retained_good_original_states=good_original,all_five_distinct_orders_retained=True,
        exact_minimum_bits_for_all_order_retaining_deterministic_basis_decoder=(len(good_original)-1).bit_length(),
        minimality_scope='Only deterministic computational-basis decoders required to retain all five distinct feasible machine orders; not a universal quantum solver lower bound')


def build_artifacts(output):
    output=Path(output);directory=output/'structural'
    directory.mkdir(parents=True,exist_ok=False)
    source=ROOT/'output/stage2-search/rank-probe/sat-only-final'
    four_path=source/'structural-four-bit-model.json';proof_path=source/'report.json'
    instance=json.loads((ROOT/'instances/instance_3x3.json').read_text())
    four=json.loads(four_path.read_text());prior=json.loads(proof_path.read_text())
    model,proof=structural_compile(instance,four,prior['minimal_nogoods'])
    verified=verify(instance,model,four)
    provenance=dict(source_model_sha256=hashlib.sha256(four_path.read_bytes()).hexdigest(),
        source_proof_sha256=hashlib.sha256(proof_path.read_bytes()).hexdigest(),
        source_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        instance_sha256=canonical_digest(instance),official_stage1_unchanged=True,physical_quantum_executed=False)
    for name,data in [('model.json',model),('proof.json',proof),('verification.json',verified),('instance.json',instance),('provenance.json',provenance)]:
        (directory/name).write_text(json.dumps(data,indent=2)+'\n')
    provenance['structural_artifacts_sha256']={name:hashlib.sha256((directory/name).read_bytes()).hexdigest()
        for name in ('model.json','proof.json','verification.json','instance.json')}
    (directory/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    (directory/'source-four-bit-model.json').write_bytes(four_path.read_bytes())
    (directory/'source-four-bit-proof.json').write_bytes(proof_path.read_bytes())
    return dict(model=model,proof=proof,verification=verified,provenance=provenance)


def qaoa_experiment(output,seeds=(2026,17,83),shots=1024):
    from qiskit import QuantumCircuit,transpile
    from qiskit.quantum_info import Statevector
    from qiskit_aer import AerSimulator
    from .quantum import _optimize,circuit_metadata
    output=Path(output);directory=output/'qaoa';directory.mkdir(exist_ok=False)
    provenance=json.loads((output/'structural/provenance.json').read_text())
    for name,digest in provenance['structural_artifacts_sha256'].items():
        assert hashlib.sha256((output/'structural'/name).read_bytes()).hexdigest()==digest
    model=json.loads((output/'structural/model.json').read_text())
    basis=json.loads((output/'structural/verification.json').read_text())['basis']
    q=RankEnergy(model['linear'],{(i,j):value for i,j,value in model['quadratic']},model['offset'])
    ground=[row['state']for row in basis if row['deadline_success']];rows=[]
    for layers in (1,2):
        for seed in seeds:
            probabilities,optimization=_optimize(q,layers,seed,512,4,'coordinate')
            metadata=circuit_metadata(q,optimization['gamma'],optimization['beta'],optimization['cost_scale'])
            circuit=QuantumCircuit.from_qasm_str(metadata['openqasm2'])
            independent=Statevector.from_instruction(circuit.remove_final_measurements(inplace=False)).probabilities()
            error=max(abs(a-b)for a,b in zip(probabilities,independent));assert error<1e-12
            simulator=AerSimulator(method='statevector',seed_simulator=seed)
            compiled=transpile(circuit,simulator,optimization_level=0,seed_transpiler=seed)
            counts={key.replace(' ',''):int(value)for key,value in simulator.run(compiled,shots=shots).result().get_counts().items()}
            assert sum(counts.values())==shots
            selected=min((int(key,2)for key in counts),key=lambda state:(basis[state]['energy'],-counts[format(state,'03b')],state))
            uniform_rng=random.Random(seed^0x51D3);uniform_counts=Counter(uniform_rng.randrange(8)for _ in range(shots))
            record=dict(schema='stage2-three-bit-qaoa.v1',layers=layers,seed=seed,shots=shots,logical_qubits=3,
                optimization=optimization,circuit=metadata,ideal_probabilities=probabilities,raw_counts=counts,
                ideal_deadline_probability=sum(probabilities[state]for state in ground),
                sampled_deadline_fraction=sum(value for key,value in counts.items()if int(key,2)in ground)/shots,
                selected_sample=basis[selected],qiskit_probability_max_error=float(error),
                uniform=dict(ideal_deadline_probability=len(ground)/8,
                    raw_counts={format(state,'03b'):count for state,count in sorted(uniform_counts.items())},
                    sampled_deadline_fraction=sum(count for state,count in uniform_counts.items()if state in ground)/shots,
                    log10_no_success_probability=shots*math.log10(1-len(ground)/8)),
                preprocessing=model['construction'],source_provenance=provenance,
                source_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                physical_quantum_executed=False,no_quantum_speedup_claim=True)
            run_dir=directory/f'p{layers}-seed{seed}';run_dir.mkdir()
            (run_dir/'result.json').write_text(json.dumps(record,indent=2)+'\n')
            (run_dir/'circuit.qasm').write_text(metadata['openqasm2'])
            (run_dir/'raw-counts.json').write_text(json.dumps(counts,indent=2)+'\n')
            rows.append({key:record[key]for key in ('layers','seed','shots','ideal_deadline_probability','sampled_deadline_fraction','selected_sample','qiskit_probability_max_error')})
    aggregate=[dict(layers=p,mean_ideal_deadline_probability=mean(row['ideal_deadline_probability']for row in rows if row['layers']==p),
        mean_sampled_deadline_fraction=mean(row['sampled_deadline_fraction']for row in rows if row['layers']==p),uniform_ideal_deadline_probability=5/8)for p in (1,2)]
    report=dict(schema='stage2-three-bit-qaoa-experiment.v1',runs=rows,aggregate=aggregate,
        physical_quantum_executed=False,no_quantum_speedup_claim=True,
        disclosure='Classical QAOA circuit simulation; uniform also almost certainly finds a valid optimum at equal 1024 shots')
    (directory/'summary.json').write_text(json.dumps(report,indent=2)+'\n');return report


def iqm_experiment(output):
    import importlib.metadata
    from qiskit import QuantumCircuit,qasm3,qpy
    from iqm.qiskit_iqm import IQMFakeAdonis
    from solver.odra import compile_candidate,classical_probabilities
    output=Path(output);directory=output/'iqm';directory.mkdir(exist_ok=False)
    backend=IQMFakeAdonis();rows=[]
    for layers in (1,2):
        source=output/'qaoa'/f'p{layers}-seed2026'
        result=json.loads((source/'result.json').read_text())
        logical=QuantumCircuit.from_qasm_str((source/'circuit.qasm').read_text())
        native,seed,error=compile_candidate(logical,backend,seeds=8)
        probabilities=classical_probabilities(native)
        assert len(probabilities)==8 and max(abs(a-b)for a,b in zip(probabilities,result['ideal_probabilities']))<1e-10
        run_dir=directory/f'p{layers}';run_dir.mkdir()
        (run_dir/'native-circuit.qasm').write_text(qasm3.dumps(native))
        with (run_dir/'native-circuit.qpy').open('wb')as handle:qpy.dump(native,handle)
        wiring=[dict(classical_bit=native.find_bit(instruction.clbits[0]).index,physical_qubit=native.find_bit(instruction.qubits[0]).index)
                for instruction in native.data if instruction.operation.name=='measure']
        unmeasured=native.remove_final_measurements(inplace=False)
        for row in wiring:
            instruction=next(instruction for instruction in native.data if instruction.operation.name=='measure'and native.find_bit(instruction.clbits[0]).index==row['classical_bit'])
            row['statevector_qubit_after_measurement_removal']=unmeasured.find_bit(instruction.qubits[0]).index
        row=dict(layers=layers,source_angle_seed=2026,logical_qubits=logical.num_qubits,
            physical_proxy_qubits=native.num_qubits,native_gate_counts=dict(native.count_ops()),native_depth=native.depth(),
            routing_seed=seed,routing_candidates=8,logical_probability_max_error=error,
            native_marginal_probabilities=probabilities.tolist(),classical_measurement_wiring=wiring,
            initial_layout={str(bit):int(index)for bit,index in native.layout.initial_layout.get_virtual_bits().items()},
            final_layout={str(bit):int(index)for bit,index in native.layout.final_layout.get_virtual_bits().items()}if native.layout.final_layout else None,
            native_unmeasured_depth=unmeasured.depth(),
            source_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            source_result_sha256=hashlib.sha256((source/'result.json').read_bytes()).hexdigest(),
            source_qasm_sha256=hashlib.sha256((source/'circuit.qasm').read_bytes()).hexdigest(),
            native_artifacts_sha256={name:hashlib.sha256((run_dir/name).read_bytes()).hexdigest()for name in ('native-circuit.qasm','native-circuit.qpy')},
            physical_quantum_executed=False,live_odra5_calibration_used=False,
            scope='Offline IQMFakeAdonis star proxy; no device job, live calibration or noise test',
            qiskit_version=importlib.metadata.version('qiskit'),iqm_client_version=importlib.metadata.version('iqm-client'))
        (run_dir/'report.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row)
    (directory/'summary.json').write_text(json.dumps(dict(schema='stage2-three-bit-iqm.v1',runs=rows),indent=2)+'\n')
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=('structural','qaoa','iqm'),default='structural')
    parser.add_argument('--output',type=Path,default=ROOT/'output/stage2-search/rank-three')
    args=parser.parse_args()
    if args.phase=='structural':
        result=build_artifacts(args.output)
        print(json.dumps(dict(variables=len(result['model']['variables']),construction=result['model']['construction'],
            retained_states=result['verification']['retained_good_original_states'],polynomial=result['model']['quadratic']),indent=2))
    elif args.phase=='qaoa':print(json.dumps(qaoa_experiment(args.output)['aggregate'],indent=2))
    else:print(json.dumps(iqm_experiment(args.output),indent=2))


if __name__=='__main__':main()
