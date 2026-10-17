"""Independent Qiskit circuit replay for the whole-recipe bridge."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import qiskit
from qiskit import qasm2, transpile
from qiskit.quantum_info import Statevector

from .assignment_qaoa import AssignmentSector
from .column_qubo import compile_columns


def save(path,data):path.write_text(json.dumps(data,indent=2)+'\n')


def run(campaign,output):
    output.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[1]
    hashes={}
    for name in ['recipe_bridge_audit.py','assignment_qaoa.py','column_qubo.py','window_qubo.py','trajectory_qubo.py']:
        path=root/'stage2'/name;target=output/'sources'/'stage2'/name
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
        hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    save(output/'protocol.json',dict(campaign=str(campaign),full_hilbert_limit=18,
        transpiler_level=1,basis=['rz','sx','x','cx'],seed=7,tolerance=1e-10,
        connectivity='Unrestricted logical connectivity; no routing or hardware model',
        source_hashes=hashes,scope='All18 circuits parsed/transpiled; six18qubit circuits independently replayed before and after transpilation'))
    began=time.perf_counter();rows=[]
    for path in sorted(campaign.glob('*/cap-*/qaoa_xy-*.json')):
        d=path.parent;p=json.loads((d.parent/'problem.json').read_text())
        q=compile_columns(p,json.loads((d/'columns.json').read_text()))
        saved=json.loads((d/'qubo.json').read_text())
        assert q.linear==saved['linear'] and q.offset==saved['offset']
        assert sorted([[i,j,c]for(i,j),c in q.quadratic.items()])==saved['quadratic']
        result=json.loads(path.read_text())
        circuit=qasm2.loads(result['qasm']).remove_final_measurements(inplace=False)
        compiled=transpile(circuit,basis_gates=['rz','sx','x','cx'],optimization_level=1,seed_transpiler=7)
        label='-'.join(path.relative_to(campaign).parts).replace('.json','')
        exported=output/(label+'-compiled.qasm');exported.write_text(qasm2.dumps(compiled))
        row=dict(source=str(path),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                 qubits=circuit.num_qubits,gates=dict(compiled.count_ops()),depth=compiled.depth(),
                 compiled_sha256=hashlib.sha256(exported.read_bytes()).hexdigest(),full_hilbert_replayed=False)
        if circuit.num_qubits<=18:
            sector=AssignmentSector.build(q)
            opt=result['optimization']
            expected=np.abs(sector.evolve(opt['gammas'],opt['betas'],opt['scale']))**2
            indices=np.array([sum(bit<<i for i,bit in enumerate(sector.bits(k)))for k in range(len(expected))],dtype=np.int64)
            observed=Statevector.from_instruction(circuit).probabilities()
            after=Statevector.from_instruction(compiled).probabilities()
            error=float(np.max(np.abs(observed[indices]-expected)))
            leakage=float(max(0,observed.sum()-observed[indices].sum()))
            compiler_error=float(np.max(np.abs(after-observed)))
            row.update(full_hilbert_replayed=True,probability_error=error,outside_sector_probability=leakage,
                       compiler_probability_error=compiler_error,valid=max(error,leakage,compiler_error)<1e-10)
            if not row['valid']:raise AssertionError(row)
        rows.append(row)
    report=dict(rows=rows,valid=all(row.get('valid',True)for row in rows),
                full_hilbert_replayed=sum(row['full_hilbert_replayed']for row in rows),
                logical_only=sum(not row['full_hilbert_replayed']for row in rows),
                qiskit_version=qiskit.__version__,wall_seconds=time.perf_counter()-began,
                source_stable=all(hashlib.sha256((root/'stage2'/n).read_bytes()).hexdigest()==h for n,h in hashes.items()),
                physical_qpu_calls=0,veloxq_calls=0)
    save(output/'report.json',report)
    save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in output.rglob('*')if p.is_file()})
    print(json.dumps({k:v for k,v in report.items()if k!='rows'}),flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(args.campaign,args.output)
