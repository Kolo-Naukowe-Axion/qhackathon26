"""Independent same-pool native scheduling references for retained column runs."""
import argparse
import hashlib
import json
from pathlib import Path
import time

from .window_campaign import save,sources
from .column_reference import solve_column_cp
from .column_qubo import compile_columns


def run(campaign,output):
    campaign=Path(campaign);output=Path(output);output.mkdir(parents=True,exist_ok=False);root,hashes=sources(output)
    for file in('trajectory_qubo.py','column_qubo.py','column_reference.py','column_reference_experiments.py'):
        name='stage2/'+file;data=(root/name).read_bytes();(output/'sources'/name).write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
    protocol=dict(source_campaign=str(campaign),source_hashes=hashes,seconds=30,workers=4,
        initializer='Best retained heuristic parent, not a raw-model optimal teacher',scope='Independent raw optional-interval/precedence/crew/setup reference for identical supplied trajectory pools. Bounds are pool-only.')
    save(output/'protocol.json',protocol);results=[];began=time.perf_counter();cpu=time.process_time()
    for path in sorted(campaign.glob('case*/report.json')):
        prior=json.loads(path.read_text());problem=json.loads((path.parent/'problem.json').read_text())
        if not(path.parent/'columns.json').exists():continue
        columns=json.loads((path.parent/'columns.json').read_text());parents=prior['parent_generation']['parents']
        initial=min(parents,key=lambda plan:next(r['energy']for r,p in zip(prior['parent_anchors'],parents)if p==plan))
        reference=solve_column_cp(problem,columns,30,4,initial);q=compile_columns(problem,columns)
        if 'plan'in reference:
            bits=q.encode(reference['plan']);assert q.decode(bits)['valid']and q.energy(bits)==reference['objective']
        row=dict(case=prior['case'],master=q.metadata(),native_pool_cp=reference,best_parent_objective=prior['best_parent_objective'],
            original_literal_energy=prior['literal_master'].get('energy'),original_literal_status=prior['literal_master']['status'],native_raw_cp=prior['native_raw_cp'],
            source_report_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        if 'objective'in reference:row['improvement_over_best_parent']=prior['best_parent_objective']-reference['objective']
        results.append(row);save(output/(path.parent.name+'.json'),row)
        print(json.dumps(dict(case=path.parent.name,ops=len(problem['operations']),pool_status=reference['status'],pool_objective=reference.get('objective'),pool_bound=reference['bound'],
            best_parent=prior['best_parent_objective'],improvement=row.get('improvement_over_best_parent'),seconds=reference['wall_seconds'])),flush=True)
    stable=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    summary=dict(results=results,source_stable=stable,wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu);save(output/'summary.json',summary)
    save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()})
    return {k:v for k,v in summary.items()if k!='results'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--campaign',required=True);p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(run(a.campaign,a.output),indent=2))
