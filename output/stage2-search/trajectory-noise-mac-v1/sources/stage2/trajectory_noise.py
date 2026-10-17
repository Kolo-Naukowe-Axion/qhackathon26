"""Generic logical noise sensitivity, NOT an ODRA/device calibration model."""
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
import qiskit_aer
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel,depolarizing_error

from .trajectory_qubo import compile_trajectory_qubo
from .planning_quantum import energy_table


def readout(probabilities,rate):
    p=np.array(probabilities,dtype=float,copy=True);n=int(round(np.log2(len(p))))
    if len(p)!=(1<<n)or not 0<=rate<=1:raise ValueError('Power-of-two probabilities and valid rate required')
    indices=np.arange(len(p))
    for bit in range(n):p=(1-rate)*p+rate*p[indices^(1<<bit)]
    return p


def run(campaign,output):
    campaign=Path(campaign);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[1];names=('trajectory_noise.py','trajectory_qubo.py','window_qubo.py','planning_quantum.py')
    hashes={}
    for name in names:
        data=(root/'stage2'/name).read_bytes();target=output/'sources/stage2'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);hashes['stage2/'+name]=hashlib.sha256(data).hexdigest()
    # lambda is the Aer depolarizing CHANNEL PARAMETER, not average gate infidelity.
    settings=[dict(name='ideal',p1=0,p2=0,readout=0),dict(name='lambda1e-3',p1=.0001,p2=.001,readout=.01),
              dict(name='lambda5e-3',p1=.0005,p2=.005,readout=.01),dict(name='lambda1e-2',p1=.001,p2=.01,readout=.02)]
    protocol=dict(schema='stage2-trajectory-generic-noise.v1',settings=settings,source_campaign=str(campaign),source_hashes=hashes,
        basis=['rz','sx','x','cx'],virtual_rz_noise=0,compiled_optimization_level=3,transpiler_seed=19,solver_threads=4,
        scope='Frozen ideal-trained angles, all actor seeds7/13/29 and p1/p2. Generic depolarizing channels after sx/x and CX plus independent symmetric readout bit flips. No relaxation/crosstalk/routing/calibration model or hardware prediction; physical QPU calls0.')
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[];began=time.perf_counter();cpu=time.process_time()
    for path in sorted(campaign.glob('case*/report.json')):
        p=json.loads((path.parent/'problem.json').read_text());columns=json.loads((path.parent/'columns.json').read_text());q=compile_trajectory_qubo(p,columns)
        energies=energy_table(dict(linear=q.linear,quadratic=q.quadratic,offset=q.offset));ground=energies==energies.min();feasible=energies<q.penalty
        for r in json.loads(path.read_text())['results']:
            if not r.get('qasm'):continue
            logical=qasm2.loads(r['qasm']).remove_final_measurements(inplace=False);circuit=transpile(logical,basis_gates=protocol['basis'],optimization_level=3,seed_transpiler=19)
            reference=Statevector.from_instruction(circuit).probabilities()
            for setting in settings:
                noise=NoiseModel()
                if setting['p1']:noise.add_all_qubit_quantum_error(depolarizing_error(setting['p1'],1),['sx','x'])
                if setting['p2']:noise.add_all_qubit_quantum_error(depolarizing_error(setting['p2'],2),['cx'])
                backend=AerSimulator(method='density_matrix',noise_model=noise,max_parallel_threads=4,max_parallel_experiments=1)
                executed=circuit.copy();executed.save_probabilities();result=backend.run(executed,shots=1,seed_simulator=2026).result()
                if not result.success:raise RuntimeError(result.status)
                probabilities=readout(result.data(0)['probabilities'],setting['readout']);probabilities/=probabilities.sum()
                if setting['name']=='ideal'and np.max(np.abs(probabilities-reference))>1e-10:raise AssertionError('Ideal density matrix differs from independent statevector')
                hit=float(probabilities[ground].sum());valid=float(probabilities[feasible].sum())
                row=dict(case=path.parent.name,method=r['label'],layers=r['layers'],seed=r['seed'],setting=setting,qubits=circuit.num_qubits,
                    cx=circuit.count_ops().get('cx',0),depth=circuit.depth(),single_shot_optimum_probability=hit,
                    success_probability_32_shots=1-(1-hit)**32,feasible_probability=valid,
                    qasm_sha256=hashlib.sha256(r['qasm'].encode()).hexdigest())
                rows.append(row)
        (output/(path.parent.name+'.json')).write_text(json.dumps([r for r in rows if r['case']==path.parent.name],indent=2)+'\n')
        print(json.dumps(dict(case=path.parent.name,noise_experiments=sum(r['case']==path.parent.name for r in rows))),flush=True)
    stable=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    report=dict(rows=rows,source_stable=stable,qiskit=qiskit.__version__,aer=qiskit_aer.__version__,wall_seconds=time.perf_counter()-began,
        process_cpu_seconds=time.process_time()-cpu,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024))
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'manifest.json').write_text(json.dumps({str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()},indent=2)+'\n')
    return {k:v for k,v in report.items()if k!='rows'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--campaign',required=True);p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(run(a.campaign,a.output),indent=2))
