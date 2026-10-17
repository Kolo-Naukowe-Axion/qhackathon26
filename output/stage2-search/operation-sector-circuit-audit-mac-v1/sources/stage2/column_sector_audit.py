"""Independently replay conditional W/XY QASM against invariant-sector samples."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

import numpy as np
import qiskit
from qiskit import qasm2,transpile
from qiskit.quantum_info import Statevector

from .column_blocks import conditional_master
from .column_search_experiments import load_master
from .sector_mixer import sector_energies,evolve_sector
from .window_campaign import save,sources


def run(campaign,output):
    campaign,output=Path(campaign),Path(output)
    output.mkdir(parents=True,exist_ok=False)
    root,hashes=sources(output)
    for file in('column_sector_audit.py','sector_mixer.py','column_blocks.py','column_closure.py',
                 'column_search_experiments.py','column_qubo.py','trajectory_qubo.py','trajectory_mixer.py'):
        name='stage2/'+file
        data=(root/name).read_bytes()
        (output/'sources'/name).write_bytes(data)
        hashes[name]=hashlib.sha256(data).hexdigest()
    protocol=json.loads((campaign/'protocol.json').read_text())
    case=Path(protocol['source_case'])
    q=load_master(case)
    prior=json.loads((case/'report.json').read_text())
    save(output/'protocol.json',dict(source_campaign=str(campaign),source_hashes=hashes,
         campaign_protocol_sha256=hashlib.sha256((campaign/'protocol.json').read_bytes()).hexdigest(),
         basis=['rz','sx','x','cx'],optimization_level=3,transpiler_seed=19,
         exact_qiskit_statevector_guard=20,connectivity='logical all-to-all, no device routing or calibration',
         scope='Independent Qiskit full Hilbert-space simulation, including preparation, against sector simulation for every saved QAOA circuit within guard.'))
    rows=[]
    began,cpu=time.perf_counter(),time.process_time()
    for path in sorted(campaign.glob('qaoa_xy-*.json')):
        run_data=json.loads(path.read_text())
        incumbent=q.encode(prior['initial_parent_plan'])
        for step in run_data['history']:
            if 'sample'not in step:continue
            sampled=step['sample']
            local=conditional_master(q,incumbent,step['alternatives'],64)
            if local.free!=step['free']or sorted(local.fixed.items())!=[tuple(v)for v in step['fixed']]:
                raise AssertionError('Saved conditional block does not match raw reconstruction')
            label=f'{path.stem}-iteration{step["iteration"]}'
            if sampled.get('qasm'):
                circuit=qasm2.loads(sampled['qasm']).remove_final_measurements(inplace=False)
                (output/(label+'.qasm')).write_text(sampled['qasm'])
                row=dict(label=label,qubits=circuit.num_qubits,
                         qasm_sha256=hashlib.sha256(sampled['qasm'].encode()).hexdigest(),
                         source_report_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                if circuit.num_qubits<=20:
                    energies=sector_energies(local)
                    sector=evolve_sector(local,energies,sampled['gammas'],sampled['betas'],sampled['cost_scale'])
                    expected=np.zeros(1<<circuit.num_qubits)
                    n,k=len(local.columns),len(local.makespans)
                    patterns=np.arange(1<<n,dtype=np.int64)
                    for register in range(k):expected[patterns|(1<<(n+register))]=np.abs(sector[register])**2
                    observed=Statevector.from_instruction(circuit).probabilities()
                    compiled=transpile(circuit,basis_gates=['rz','sx','x','cx'],optimization_level=3,seed_transpiler=19)
                    after=Statevector.from_instruction(compiled).probabilities()
                    error=float(np.max(np.abs(observed-expected)))
                    compiler_error=float(np.max(np.abs(after-observed)))
                    row.update(valid=error<1e-10 and compiler_error<1e-10,
                               probability_error=error,transpilation_probability_error=compiler_error,
                               compiled_gates=dict(compiled.count_ops()),compiled_depth=compiled.depth(),
                               sector_amplitudes=energies.size,full_amplitudes=len(expected))
                else:
                    row.update(valid=None,skipped='Independent full-statevector audit guard20qubits')
                rows.append(row)
            if step.get('accepted'):
                incumbent=local.full_bits(sampled['bits'])
        if incumbent!=run_data['bits']:
            raise AssertionError('Replayed accepted search does not match final saved incumbent')
    stable=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    audited=[r for r in rows if r['valid']is not None]
    report=dict(valid=bool(audited)and all(r['valid']for r in audited),source_stable=stable,
                circuits=len(rows),audited=len(audited),skipped=len(rows)-len(audited),rows=rows,
                max_probability_error=max((r['probability_error']for r in audited),default=None),
                max_transpilation_probability_error=max((r['transpilation_probability_error']for r in audited),default=None),
                qiskit_version=qiskit.__version__,physical_qpu_calls=0,
                wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,
                peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin'else 1024))
    save(output/'report.json',report)
    save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()})
    return{k:v for k,v in report.items()if k!='rows'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaign',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    print(json.dumps(run(a.campaign,a.output),indent=2))
