"""Offline IQM star-topology routing of the isolated four-bit rank candidate.

Uses the existing compilation/marginalization helpers read-only. It never
creates an IQMProvider, submits a job or treats the proxy as live calibration.
Run only in the separate requirements-odra environment.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time


ROOT=Path(__file__).resolve().parents[1]


def digest(raw):return hashlib.sha256(raw).hexdigest()


def compile_experiment(output,routing_seeds=8,source_seed=2026):
    import numpy as np
    from qiskit import QuantumCircuit,qasm3,qpy
    from iqm.qiskit_iqm import IQMFakeAdonis
    from solver.odra import compile_candidate,classical_probabilities
    from .rank_quantum import classify_basis
    output=Path(output)
    if output.exists()and any(output.iterdir()):raise ValueError('Use an empty output directory')
    if routing_seeds<1:raise ValueError('At least one routing seed required')
    output.mkdir(parents=True,exist_ok=True)
    backend=IQMFakeAdonis()
    source_root=ROOT/'output/stage2-search/rank-quantum-final'
    versions={d.metadata['Name']:d.version for d in importlib.metadata.distributions()
              if 'iqm'in d.metadata['Name'].lower()or d.metadata['Name'].lower()in ('qiskit','qiskit-aer','numpy')}
    source_hashes={name:digest((ROOT/name).read_bytes())for name in
                   ('solver/odra.py','stage2/rank_iqm.py','stage2/rank_quantum.py')}
    instance=json.loads((source_root/'instance.json').read_text())
    (output/'instance.json').write_bytes((source_root/'instance.json').read_bytes())
    summary=[]
    for variant in ('sat_only','sparse_optional_lp'):
        model_path=source_root/variant/'source-model.json'
        model=json.loads(model_path.read_text());_,basis=classify_basis(model,instance)
        ground=[row['state']for row in basis if row['deadline_success']]
        for layers in (1,2):
            began=time.perf_counter();source=source_root/variant/f'p{layers}-seed{source_seed}'
            result_path=source/'result.json';qasm_path=source/'circuit.qasm'
            original=json.loads(result_path.read_text())
            logical=QuantumCircuit.from_qasm_str(qasm_path.read_text())
            if logical.num_qubits!=4 or logical.num_clbits!=4:raise ValueError('Expected four-bit logical candidate')
            compiled,selected_seed,error=compile_candidate(logical,backend,seeds=routing_seeds)
            logical_p=classical_probabilities(logical);native_p=classical_probabilities(compiled)
            max_error=float(np.max(np.abs(logical_p-native_p)))
            source_error=float(np.max(np.abs(logical_p-original['ideal_basis_probabilities'])))
            assert max_error<1e-10 and source_error<1e-12
            gates={str(k):int(v)for k,v in compiled.count_ops().items()}
            assert set(gates)<=set(backend.target.operation_names)|{'barrier'}
            unmeasured=compiled.remove_final_measurements(inplace=False)
            wiring=[]
            for instruction in compiled.data:
                if instruction.operation.name=='measure':
                    qubit=instruction.qubits[0]
                    wiring.append(dict(classical_bit=compiled.find_bit(instruction.clbits[0]).index,
                        native_circuit_qubit=compiled.find_bit(qubit).index,
                        statevector_qubit_after_measurement_removal=unmeasured.find_bit(qubit).index))
            layout=compiled.layout
            record=dict(schema='stage2-rank-iqm-offline.v1',variant=variant,layers=layers,
                source_angle_seed=source_seed,logical_qubits=logical.num_qubits,
                physical_proxy_qubits=compiled.num_qubits,classical_bits=compiled.num_clbits,
                proxy_backend=backend.name,proxy_coupling_edges=[list(edge)for edge in backend.coupling_map.get_edges()],
                proxy_native_operations=list(backend.target.operation_names),native_gate_counts=gates,
                native_depth=compiled.depth(),native_unmeasured_depth=unmeasured.depth(),
                layout_seed=selected_seed,routing_candidates=routing_seeds,
                routing_selection='Existing compile_candidate: minimum CZ count, then depth, then transpiler seed',
                initial_layout={str(bit):int(index)for bit,index in layout.initial_layout.get_virtual_bits().items()}if layout else None,
                final_layout={str(bit):int(index)for bit,index in layout.final_layout.get_virtual_bits().items()}if layout and layout.final_layout else None,
                classical_measurement_wiring=sorted(wiring,key=lambda row:row['classical_bit']),
                logical_probabilities=logical_p.tolist(),native_marginal_probabilities=native_p.tolist(),
                probability_max_error=max_error,helper_reported_max_error=error,
                source_experiment_probability_max_error=source_error,
                preserved_ground_states=ground,
                logical_ground_probability=float(sum(logical_p[state]for state in ground)),
                routed_ground_probability=float(sum(native_p[state]for state in ground)),
                preprocessing=model['construction'],versions=versions,source_sha256=source_hashes,
                retained_source=dict(model_path=str(model_path),model_sha256=digest(model_path.read_bytes()),
                    qasm_path=str(qasm_path),qasm_sha256=digest(qasm_path.read_bytes()),
                    result_path=str(result_path),result_sha256=digest(result_path.read_bytes())),
                compilation_seconds=time.perf_counter()-began,
                physical_quantum_executed=False,live_odra5_calibration_used=False,no_quantum_speedup_claim=True,
                scope='Offline IQMFakeAdonis star-topology proxy; not a physical ODRA5 job or live calibration')
            directory=output/f'{variant}-p{layers}';directory.mkdir()
            (directory/'logical-circuit.qasm').write_bytes(qasm_path.read_bytes())
            (directory/'source-model.json').write_bytes(model_path.read_bytes())
            (directory/'source-result.json').write_bytes(result_path.read_bytes())
            (directory/'native-circuit.qasm').write_text(qasm3.dumps(compiled))
            with (directory/'native-circuit.qpy').open('wb')as handle:qpy.dump(compiled,handle)
            record['native_artifacts_sha256']={name:digest((directory/name).read_bytes())
                for name in ('native-circuit.qasm','native-circuit.qpy')}
            (directory/'report.json').write_text(json.dumps(record,indent=2)+'\n')
            summary.append({key:record[key]for key in ('variant','layers','logical_qubits','physical_proxy_qubits',
                'native_gate_counts','native_depth','native_unmeasured_depth','layout_seed','probability_max_error',
                'logical_ground_probability','routed_ground_probability','compilation_seconds')})
    for name,sha in source_hashes.items():assert digest((ROOT/name).read_bytes())==sha,'Source changed during experiment'
    report=dict(schema='stage2-rank-iqm-offline-experiment.v1',runs=summary,versions=versions,
        source_sha256=source_hashes,physical_quantum_executed=False,live_odra5_calibration_used=False,
        no_quantum_speedup_claim=True,
        limitations=['IQMFakeAdonis supplies a local five-qubit star proxy, not current ODRA5 connectivity or calibration.',
            'Native depth and CZ counts are proxy compilation costs; device execution and noise tolerance remain untested.',
            'Angles use fixed source seed2026; p2 probabilities are this example, not averages across optimization seeds.',
            'Exact classical structural/SAT preprocessing and simulator angle optimization remain necessary costs.',
            'No remote job was submitted or sampled.'])
    (output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'output/stage2-search/rank-iqm')
    parser.add_argument('--routing-seeds',type=int,default=8)
    parser.add_argument('--source-seed',type=int,default=2026)
    args=parser.parse_args();report=compile_experiment(args.output,args.routing_seeds,args.source_seed)
    print(json.dumps(report['runs'],indent=2))


if __name__=='__main__':main()
