"""Paired X/XY/strong-uniform controls for saved complete-trajectory masters."""
import argparse
import hashlib
import json
from pathlib import Path
import time

from .window_campaign import sources,save
from .trajectory_qubo import compile_trajectory_qubo
from .planning_quantum import sample_block
from .trajectory_mixer import sample


def run(campaign,output):
    campaign=Path(campaign);output=Path(output);output.mkdir(parents=True,exist_ok=False);root,hashes=sources(output)
    for file in('trajectory_qubo.py','trajectory_mixer.py','trajectory_mixer_experiments.py'):
        name='stage2/'+file;data=(root/name).read_bytes();(output/'sources'/name).write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
    protocol=dict(schema='stage2-trajectory-mixer-comparison.v1',source_campaign=str(campaign),seeds=[7,13,29],layers=[1,2],shots=32,angle_evaluations=64,
        methods=['uniform_all_bits','uniform_onehot','qaoa_x','qaoa_xy'],source_hashes=hashes,
        scope='Same restricted pool and objective; uniform_onehot is the stronger classical sampling control. No classical runtime advantage claim. Training uses64 simulated EXACT expectation values, not64 physical shots. Final32 Born samples per run. All classical statevector/energy-table work counted.')
    save(output/'protocol.json',protocol);began=time.perf_counter();cpu=time.process_time();rows=[]
    for folder in sorted(campaign.glob('case*')):
        if not(folder/'columns.json').exists():continue
        problem=json.loads((folder/'problem.json').read_text());columns=json.loads((folder/'columns.json').read_text());q=compile_trajectory_qubo(problem,columns)
        destination=output/folder.name;destination.mkdir();save(destination/'problem.json',problem);save(destination/'columns.json',columns)
        results=[]
        for seed in protocol['seeds']:
            results.append(sample_block(q,list(range(len(q.linear))),{},'uniform',seed,32,64));results[-1]['label']='uniform_all_bits'
            results.append(sample(q,seed,shots=32,method='uniform_onehot'));results[-1]['label']='uniform_onehot'
            for layers in protocol['layers']:
                results.append(sample_block(q,list(range(len(q.linear))),{},'qaoa',seed,32,64,layers));results[-1].update(label='qaoa_x',layers=layers)
                results.append(sample(q,seed,layers,64,32));results[-1]['label']='qaoa_xy'
        report=dict(master=q.metadata(),results=results,source_pool_sha256=hashlib.sha256((folder/'columns.json').read_bytes()).hexdigest())
        save(destination/'report.json',report);rows.append(report)
        print(json.dumps(dict(case=folder.name,qubits=len(q.linear),runs=[dict(method=r['label'],layers=r.get('layers'),seed=r['seed'],energy=r['energy'],valid=r['decoded']['valid'],hit_probability=r['exact_hit_probability'],seconds=r['wall_seconds'])for r in results])),flush=True)
    stable=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    summary=dict(rows=rows,source_stable=stable,wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu);save(output/'summary.json',summary)
    save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()})
    return {k:v for k,v in summary.items()if k!='rows'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--campaign',required=True);p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(run(a.campaign,a.output),indent=2))
