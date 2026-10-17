"""One bounded conditioned VeloxQ pilot; offline unless --allow-external.

Use .venv/bin/python, which contains the pinned SDK. This never trains QAOA/VQE,
changes frozen inputs, retries, or repairs solver output.
"""
import argparse
import json
import hashlib
import shutil
import os
from pathlib import Path

from .build_meal_release import save, result_summary
from .conditioning import condition_bundle, eliminate_idle, rescore_result
from .contracts import load_bundle
from .methods.veloxq import solve_qubo, DEFAULT_LEDGER


def load_local_token(path):
    """Read only the requested token field; never execute shell config or print it."""
    if os.environ.get('VELOX_TOKEN') or not path.exists():return
    for line in path.read_text().splitlines():
        if line.startswith('VELOX_TOKEN='):
            value=line.partition('=')[2].strip()
            if value:os.environ['VELOX_TOKEN']=value
            return


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',type=Path,default=Path('output/catering-velox-scale-v3/scale-512-qubo.json'))
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--allow-external',action='store_true')
    p.add_argument('--max-service-jobs',type=int,default=0,help='Total shared ledger count, including prior attempts')
    p.add_argument('--num-rep',type=int,default=512)
    p.add_argument('--num-steps',type=int,default=2000)
    p.add_argument('--timeout',type=float,default=60)
    p.add_argument('--formulation',choices=['deletion-bound','no-idle'],default='deletion-bound')
    p.add_argument('--initializer',choices=['cold','all-idle'],default='cold')
    p.add_argument('--env-file',type=Path,default=Path('.env.velox-local'))
    a=p.parse_args()
    if a.output.exists():p.error('Fresh output directory required')
    b=load_bundle(a.bundle);variant=(eliminate_idle(b) if a.formulation=='no-idle' else condition_bundle(b))
    initial=None
    if a.initializer=='all-idle':
        idle={g['idle_index'] for g in b['onehot_groups']}
        initial=([0]*len(variant['linear']) if a.formulation=='no-idle' else [int(i in idle) for i in range(len(b['linear']))])
    load_local_token(a.env_file)
    a.output.mkdir(parents=True)
    plan=dict(kind='One conditioned VeloxQ job; raw output independently checked',
        source_bundle=str(a.bundle),source_bundle_sha256=b['bundle_sha256'],
        sampling_bundle_sha256=variant['bundle_sha256'],conditioning=variant['conditioning'],
        formulation=a.formulation,initializer=a.initializer,num_rep=a.num_rep,num_steps=a.num_steps,
        wall_time_limit_s=a.timeout,max_service_jobs_total=a.max_service_jobs,
        shared_ledger=str(DEFAULT_LEDGER),repair=False,retries=False,
        allow_external=a.allow_external,physical_qpu_calls=0)
    root=Path(__file__).resolve().parents[1]
    plan['source_sha256']={}
    for name in ['catering/conditioning.py','catering/veloxq_pilot.py','catering/methods/veloxq.py']:
        plan['source_sha256'][name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
        target=a.output/'source_snapshot'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(root/name,target)
    save(a.output/'experiment-plan.json',plan)
    config=dict(num_rep=a.num_rep,num_steps=a.num_steps)
    if initial is not None:config['initial_bits']=initial
    result=solve_qubo(variant,dict(allow_external_execution=a.allow_external,
        max_service_jobs=a.max_service_jobs,wall_time_limit_s=a.timeout),config,a.output/'service')
    mapped=rescore_result(b,variant,result)
    save(a.output/'result.json',mapped)
    summary=result_summary(b,mapped)
    save(a.output/'evaluation.json',summary)
    print(json.dumps(dict(output=str(a.output),status=result['status'],failure=result['failure'],
        veloxq_calls=result['veloxq_calls'],evaluation=summary),indent=2))


if __name__=='__main__':main()
