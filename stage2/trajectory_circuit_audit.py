"""Independent logical gate-resource and probability audit, including W prep."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import qiskit
from qiskit import qasm2,transpile
from qiskit.quantum_info import Statevector

from .trajectory_qubo import compile_trajectory_qubo
from .trajectory_mixer import evolve as xy_evolve
from .planning_quantum import energy_table,evolve as x_evolve


def run(campaign,output):
    campaign=Path(campaign);output=Path(output);output.mkdir(parents=True,exist_ok=False);rows=[];began=time.perf_counter();cpu=time.process_time()
    for path in sorted(campaign.glob('case*/report.json')):
        problem=json.loads((path.parent/'problem.json').read_text());columns=json.loads((path.parent/'columns.json').read_text());q=compile_trajectory_qubo(problem,columns)
        energies=energy_table(dict(linear=q.linear,quadratic=q.quadratic,offset=q.offset))
        for row in json.loads(path.read_text())['results']:
            if not row.get('qasm'):continue
            if row['label']=='qaoa_xy':expected=np.abs(xy_evolve(q,energies,row['gammas'],row['betas'],row['cost_scale']))**2
            else:
                opt=row['optimization'];expected=np.abs(x_evolve(energies,len(q.linear),opt['gammas'],opt['betas'],opt['cost_scale']))**2
            circuit=qasm2.loads(row['qasm']).remove_final_measurements(inplace=False);probabilities=Statevector.from_instruction(circuit).probabilities()
            compiled=transpile(circuit,basis_gates=['rz','sx','x','cx'],optimization_level=3,seed_transpiler=19)
            compiled_probability=Statevector.from_instruction(compiled).probabilities();error=float(np.max(np.abs(probabilities-expected)));compiler_error=float(np.max(np.abs(compiled_probability-probabilities)))
            label=f'{path.parent.name}-{row["label"]}-p{row["layers"]}-seed{row["seed"]}'
            (output/f'{label}.qasm').write_text(row['qasm'])
            out=dict(case=path.parent.name,method=row['label'],layers=row['layers'],seed=row['seed'],qubits=circuit.num_qubits,
                raw_gates=dict(circuit.count_ops()),compiled_gates=dict(compiled.count_ops()),compiled_depth=compiled.depth(),
                qubit_cx_product=circuit.num_qubits*compiled.count_ops().get('cx',0),probability_error=error,transpilation_probability_error=compiler_error,
                valid=error<1e-10 and compiler_error<1e-10,qasm_sha256=hashlib.sha256(row['qasm'].encode()).hexdigest(),source_report_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            rows.append(out)
    result=dict(schema='stage2-trajectory-circuit-audit.v1',valid=bool(rows)and all(r['valid']for r in rows),circuits=len(rows),rows=rows,
        qiskit_version=qiskit.__version__,basis=['rz','sx','x','cx'],optimization_level=3,seed_transpiler=19,connectivity='logical all-to-all; no device routing or native calibration',
        max_probability_error=max((r['probability_error']for r in rows),default=None),max_transpilation_error=max((r['transpilation_probability_error']for r in rows),default=None),
        wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,
        scope='Includes initial W-state construction, cost and mixer gates. CX-based score is our logical metric, not the referenced paper Toffoli metric or a physical hardware runtime. Physical QPU calls0.')
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');return {k:v for k,v in result.items()if k!='rows'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--campaign',required=True);p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(run(a.campaign,a.output),indent=2))
