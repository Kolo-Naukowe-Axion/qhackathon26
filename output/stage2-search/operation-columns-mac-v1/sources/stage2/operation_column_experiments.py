"""Local operation-pool QUBO experiment with independent same-pool reference."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

from .operation_columns import operation_columns
from .column_qubo import compile_columns
from .column_reference import solve_column_cp
from .window_campaign import save,sources


def run(campaign,output,cap=48):
    campaign,output=Path(campaign),Path(output)
    output.mkdir(parents=True,exist_ok=False)
    root,hashes=sources(output)
    for file in('operation_columns.py','operation_column_experiments.py','trajectory_qubo.py','column_qubo.py','column_reference.py'):
        name='stage2/'+file
        data=(root/name).read_bytes()
        (output/'sources'/name).write_bytes(data)
        hashes[name]=hashlib.sha256(data).hexdigest()
    save(output/'protocol.json',dict(source_campaign=str(campaign),source_hashes=hashes,per_operation_cap=cap,radius=180,
         native_pool_cp_seconds=30,workers=4,quantum_calls=0,cp_teacher_used=False,compute='Local Mac CPU only',
         scope='Independent operation columns, exact QUBO within deliberately restricted raw assignment domain. Original raw references inherited for quality comparison only.'))
    began,cpu=time.perf_counter(),time.process_time()
    results=[]
    for path in sorted(campaign.glob('case*/report.json')):
        prior=json.loads(path.read_text())
        problem=json.loads((path.parent/'problem.json').read_text())
        parents=prior['parent_generation']['parents']
        index=min(range(len(parents)),key=lambda i:prior['parent_anchors'][i]['energy'])
        folder=output/path.parent.name
        folder.mkdir()
        preparation_start=time.perf_counter()
        pool,preparation=operation_columns(problem,parents,cap)
        preparation['wall_seconds']=time.perf_counter()-preparation_start
        save(folder/'problem.json',problem)
        save(folder/'columns.json',pool)
        build=time.perf_counter()
        q=compile_columns(problem,pool)
        compile_seconds=time.perf_counter()-build
        reference=solve_column_cp(problem,pool,30,4,parents[index])
        if 'plan'in reference:
            bits=q.encode(reference['plan'])
            assert q.decode(bits)['valid']and q.energy(bits)==reference['objective']
        save(folder/'qubo.json',dict(linear=q.linear,quadratic=[[i,j,v]for(i,j),v in sorted(q.quadratic.items())],
             offset=q.offset,groups=q.groups,variables=q.variables,metadata=q.metadata()))
        row=dict(case=prior['case'],operations=len(problem['operations']),master=q.metadata(),preparation=preparation,
                 compile_wall_seconds=compile_seconds,native_pool_cp=reference,best_parent_objective=prior['best_parent_objective'],
                 native_raw_cp=prior['native_raw_cp'],initial_parent_plan=parents[index],
                 source_report_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        if 'objective'in reference:
            row['improvement_over_best_parent']=prior['best_parent_objective']-reference['objective']
        save(folder/'report.json',row)
        results.append(row)
        print(json.dumps(dict(case=path.parent.name,operations=len(problem['operations']),bits=len(q.linear),couplers=len(q.quadratic),
             status=reference['status'],objective=reference.get('objective'),bound=reference.get('bound'),
             parent=prior['best_parent_objective'],improvement=row.get('improvement_over_best_parent'))),flush=True)
    stable=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    summary=dict(results=results,source_stable=stable,wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,
                 peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin'else 1024))
    save(output/'summary.json',summary)
    save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()})
    return{k:v for k,v in summary.items()if k!='results'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaign',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--cap',type=int,default=48)
    a=p.parse_args()
    print(json.dumps(run(a.campaign,a.output,a.cap),indent=2))
