"""Independent Qiskit replay of actual emitted planning QAOA circuits."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import qiskit
from qiskit import qasm2
from qiskit.quantum_info import Statevector

from .planning_quantum import energy_table,evolve


def audit(campaign,output,per_method=8):
    campaign=Path(campaign);output=Path(output);output.mkdir(parents=True,exist_ok=False);rows=[]
    reports=sorted(campaign.glob('case*/report.json'))
    for report in reports:
        data=json.loads(report.read_text())
        for method in data['methods']:
            if method.get('seed')!=7 or 'qaoa'not in method['method']:continue
            for index,blockrow in enumerate(method['history'][:per_method]):
                block=blockrow['conditional_block'];energy=energy_table(dict(linear=block['linear'],quadratic={(i,j):v for i,j,v in block['quadratic']},offset=block['offset']))
                opt=blockrow['optimization'];expected=np.abs(evolve(energy,len(block['linear']),opt['gammas'],opt['betas'],opt['cost_scale']))**2
                circuit=qasm2.loads(blockrow['qasm']).remove_final_measurements(inplace=False)
                actual=Statevector.from_instruction(circuit).probabilities();error=float(np.max(np.abs(actual-expected)))
                label=f'{report.parent.name}-{method["method"]}-{index}';(output/f'{label}.qasm').write_text(blockrow['qasm'])
                row=dict(case=data['case'],method=method['method'],block_index=index,qubits=circuit.num_qubits,
                    gates=dict(circuit.count_ops()),depth=circuit.depth(),max_probability_error=error,valid=error<1e-10,
                    source_report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),qasm_sha256=hashlib.sha256(blockrow['qasm'].encode()).hexdigest(),
                    conditional_exact_energy=blockrow['conditional_exact_energy'],exact_hit_probability=blockrow['exact_hit_probability'])
                rows.append(row)
    result=dict(schema='stage2-planning-qasm-independent-audit.v1',qiskit_version=qiskit.__version__,circuits=len(rows),valid=bool(rows)and all(r['valid']for r in rows),
        max_probability_error=max((r['max_probability_error']for r in rows),default=None),rows=rows,physical_qpu_calls=0)
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--campaign',required=True);p.add_argument('--output',required=True);a=p.parse_args();r=audit(a.campaign,a.output)
    print(json.dumps({k:v for k,v in r.items()if k!='rows'},indent=2))
