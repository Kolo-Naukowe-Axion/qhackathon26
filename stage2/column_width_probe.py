"""Classical ceiling probe for larger conditional neighborhoods before QAOA."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

from .column_blocks import search
from .column_search_experiments import load_master
from .window_campaign import save,sources


def run(case,output,proposal='legacy'):
    case,output=Path(case),Path(output)
    output.mkdir(parents=True,exist_ok=False)
    root,hashes=sources(output)
    for file in('column_blocks.py','column_closure.py','column_width_probe.py','column_search_experiments.py','column_qubo.py','trajectory_qubo.py','trajectory_mixer.py'):
        name='stage2/'+file
        data=(root/name).read_bytes()
        (output/'sources'/name).write_bytes(data)
        hashes[name]=hashlib.sha256(data).hexdigest()
    protocol=dict(source_case=str(case),source_hashes=hashes,widths=[5,8,12,16],seeds=[7,13],iterations=16,
                  local_literal_cp_seconds=.5,workers=1,max_conditional_bits=64,proposal=proposal,
                  source_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in case.glob('*.json')},
                  scope='Classical-only diagnostic of supplied finite-pool QUBO. Local CP sees only quadratic energy, never native schedule constraints. No quantum claims or CP-supplied quantum initializer.')
    save(output/'protocol.json',protocol)
    q=load_master(case)
    prior=json.loads((case/'report.json').read_text())
    initial=q.encode(prior['initial_parent_plan'])
    began,cpu=time.perf_counter(),time.process_time()
    runs=[]
    for width in protocol['widths']:
        for seed in protocol['seeds']:
            row=search(q,initial,'literal_cp',seed,16,width=width,proposal=proposal)
            save(output/f'width{width}-seed{seed}.json',row)
            compact={k:v for k,v in row.items()if k not in('history','bits','decoded')}
            compact.update(valid=row['decoded']['valid'],max_bits=max((r['sample']['qubits']for r in row['history']if'sample'in r),default=0),
                           strict_improvement=q.energy(initial)-row['energy'])
            runs.append(compact)
            print(json.dumps(compact),flush=True)
    stable=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    summary=dict(runs=runs,source_stable=stable,master=q.metadata(),native_pool_reference=prior['native_pool_cp'],
                 wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,
                 peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin'else 1024))
    save(output/'summary.json',summary)
    save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()})
    return{k:v for k,v in summary.items()if k not in('runs','master','native_pool_reference')}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--proposal',choices=['legacy','closure'],default='legacy')
    a=p.parse_args()
    print(json.dumps(run(a.case,a.output,a.proposal),indent=2))
