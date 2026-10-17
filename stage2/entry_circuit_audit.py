"""Independent full-Hilbert Qiskit replay of the 18-qubit entry circuit.

Larger circuits are parsed and transpiled for resources, not statevector replay.
No backend object or remote service is constructed.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import qiskit
from qiskit import qasm2, transpile
from qiskit.quantum_info import Statevector

from .assignment_qaoa import AssignmentSector
from .window_qubo import compile_qubo


def audit(campaign, output):
    campaign, output = Path(campaign), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for directory in sorted(p for p in campaign.iterdir() if (p/'problem.json').exists()):
        source = directory/'test-qaoa_xy-101.json'
        result = json.loads(source.read_text())
        circuit = qasm2.loads(result['qasm']).remove_final_measurements(inplace=False)
        compiled = transpile(circuit, basis_gates=['rz','sx','x','cx'], optimization_level=1, seed_transpiler=7)
        row = dict(case=directory.name, logical_qubits=circuit.num_qubits,
                   native_gates=dict(compiled.count_ops()), native_depth=compiled.depth(),
                   connectivity='Unrestricted logical connectivity; physical routing not performed',
                   source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                   qasm_sha256=hashlib.sha256(result['qasm'].encode()).hexdigest(),
                   full_hilbert_replayed=False)
        if circuit.num_qubits <= 18:
            problem = json.loads((directory/'problem.json').read_text())
            sector = AssignmentSector.build(compile_qubo(problem, support_pruning=True))
            opt = result['optimization']
            expected = np.abs(sector.evolve(opt['gammas'], opt['betas'], opt['scale']))**2
            indices = np.array([sum(bit << i for i,bit in enumerate(sector.bits(k)))
                                for k in range(len(expected))], dtype=np.int64)
            actual = Statevector.from_instruction(circuit).probabilities()
            error = float(np.max(np.abs(actual[indices]-expected)))
            leakage = float(max(0, actual.sum()-actual[indices].sum()))
            row.update(full_hilbert_replayed=True, hilbert_states=len(actual),
                       max_probability_error=error, outside_onehot_probability=leakage,
                       valid=error<1e-10 and leakage<1e-10)
            if not row['valid']:
                raise AssertionError(row)
        rows.append(row)
    result = dict(schema='qfactoria-entry-independent-qiskit-audit.v1',
                  qiskit_version=qiskit.__version__, rows=rows,
                  valid=bool(rows) and any(r.get('valid') for r in rows),
                  physical_qpu_calls=0, veloxq_calls=0,
                  scope='Independent full-Hilbert probabilities for 18 qubits only; larger QASM parsed/transpiled. Native counts include preparation, cost and mixer, without hardware routing.')
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign',required=True)
    parser.add_argument('--output',required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.campaign,args.output),indent=2))
