"""Paired local master search; saved CP optima are references, never teachers."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

from .column_qubo import ColumnQUBO
from .column_blocks import search
from .window_campaign import save,sources
from .window_qubo import digest


def load_master(case):
    case=Path(case)
    problem=json.loads((case/'problem.json').read_text())
    columns=json.loads((case/'columns.json').read_text())
    raw=json.loads((case/'qubo.json').read_text())
    metadata=raw['metadata']
    if digest(problem)!=metadata['problem_sha256']or digest(columns)!=metadata['pool_sha256']:
        raise ValueError('Saved master problem/pool hash mismatch')
    quad={(i,j):v for i,j,v in raw['quadratic']}
    conflicts=[[i,j]for(i,j),v in quad.items()
               if raw['variables'][i]['group']!=raw['variables'][j]['group']
               and '@makespan'not in(raw['variables'][i]['group'],raw['variables'][j]['group'])]
    q=ColumnQUBO(problem,columns,raw['groups'],raw['variables'],raw['linear'],quad,raw['offset'],
                 metadata['penalty'],metadata['feasible_objective_upper_bound'],conflicts)
    if q.metadata()!=metadata:
        raise ValueError('Saved master metadata reconstruction mismatch')
    return q


def run(case,output,iterations=32,width=5,proposal='legacy',engine='statevector'):
    case,output=Path(case),Path(output)
    output.mkdir(parents=True,exist_ok=False)
    root,hashes=sources(output)
    for file in('column_blocks.py','column_closure.py','sector_mixer.py','column_search_experiments.py','column_qubo.py','trajectory_qubo.py','trajectory_mixer.py'):
        name='stage2/'+file
        data=(root/name).read_bytes()
        (output/'sources'/name).write_bytes(data)
        hashes[name]=hashlib.sha256(data).hexdigest()
    protocol=dict(source_case=str(case),source_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in case.glob('*.json')},
          source_hashes=hashes,seeds=[7,13,29],methods=['proposal_only','exact','uniform_onehot','qaoa_xy'],
          iterations=iterations,shots=32,layers=2,expectation_evaluations=64,max_component_choices_per_block=width,
          proposal=proposal,engine=engine,max_qubits=64 if engine=='sector'else 16,max_sector_amplitudes=16777216 if engine=='sector'else None,
          compute='Local Mac CPU exact statevector simulator; no GPU, remote or physical quantum calls',
          comparisons='Paired initial heuristic parent/seeds/proposal algorithm. Adaptive neighborhoods can diverge. Quantum training has extra exact-expectation cost; no runtime advantage implied.',
          cp_teacher_used=False,scope='Exact conditional energies of the supplied restricted master, not lossless reduction of the raw full cell.')
    save(output/'protocol.json',protocol)
    began,cpu=time.perf_counter(),time.process_time()
    q=load_master(case)
    prior=json.loads((case/'report.json').read_text())
    initial=q.encode(prior['initial_parent_plan'])
    if q.energy(initial)!=prior['best_parent_objective']:
        raise AssertionError('Declared heuristic initializer does not match saved master')
    runs=[]
    for seed in protocol['seeds']:
        for method in protocol['methods']:
            row=search(q,initial,method,seed,iterations,32,64,2,width,proposal,engine)
            save(output/f'{method}-{seed}.json',row)
            compact={k:v for k,v in row.items()if k not in('history','bits','decoded')}
            compact.update(raw_check=row['decoded']['valid'],qubits_max=max((r['sample']['qubits']for r in row['history']if'sample'in r),default=0),
                           accepted=sum(r.get('accepted',False)for r in row['history']),
                           strict_improvement=q.energy(initial)-row['energy'])
            runs.append(compact)
            print(json.dumps(compact),flush=True)
    stable=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    summary=dict(master=q.metadata(),best_parent_objective=q.energy(initial),native_pool_reference=prior['native_pool_cp'],
                 native_raw_reference=prior['native_raw_cp'],runs=runs,source_stable=stable,
                 wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,
                 peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin'else 1024))
    save(output/'summary.json',summary)
    save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()})
    return{k:v for k,v in summary.items()if k not in('runs','native_pool_reference','native_raw_reference','master')}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--iterations',type=int,default=32)
    p.add_argument('--width',type=int,default=5)
    p.add_argument('--proposal',choices=['legacy','closure'],default='legacy')
    p.add_argument('--engine',choices=['statevector','sector'],default='statevector')
    a=p.parse_args()
    print(json.dumps(run(a.case,a.output,a.iterations,a.width,a.proposal,a.engine),indent=2))
