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
from .conditioning import condition_bundle, eliminate_idle, lift_bits, rescore_result
from .contracts import load_bundle
from .decode import decode
from .methods.veloxq import solve_qubo, DEFAULT_LEDGER


def load_local_token(path):
    """Read only the requested token field; never execute shell config or print it."""
    if os.environ.get('VELOX_TOKEN') or not path.exists():return
    for line in path.read_text().splitlines():
        if line.startswith('VELOX_TOKEN='):
            value=line.partition('=')[2].strip()
            if value:os.environ['VELOX_TOKEN']=value
            return


def incumbent_start(source, variant, result_path):
    """Best checked sample of an earlier result, projected to the sampling variables.

    The start is a supplied classical plan; only strictly better returned plans
    count as improvement found by VeloxQ."""
    result=json.loads(Path(result_path).read_text())
    if result.get('bundle_sha256')!=source['bundle_sha256']:
        raise ValueError('Incumbent result refers to a different bundle')
    best=None
    for sample in result['samples']:
        checked=decode(source,sample['bits'])
        if checked['valid']:
            m=checked['check']['metrics'];key=tuple(m[k] for k in 'UWBR')
            if best is None or key<best[0]:best=(key,sample['bits'])
    if best is None:raise ValueError('Incumbent result has no valid sample')
    key,bits=best
    if variant['variable_order']==source['variable_order']:initial=list(bits)
    else:initial=list(bits[:len(variant['variable_order'])])
    if lift_bits(source,variant,initial)!=bits:
        raise ValueError('Incumbent does not map one-to-one to the sampling variables')
    return initial,dict(result=str(result_path),result_sha256=hashlib.sha256(Path(result_path).read_bytes()).hexdigest(),
        method_id=result.get('method_id'),metrics=dict(zip('UWBR',key)),source_bits_sha256=hashlib.sha256(json.dumps(bits).encode()).hexdigest())


def recover(output):
    """Download an already submitted job; never upload/submit or advance ledger."""
    import time
    import h5py
    from veloxq_sdk.api.core.http import RestClient
    from veloxq_sdk.api.jobs import Job,VeloxSampleSet
    from .methods.veloxq import load_qubo,qubo_to_spin,parse_samples,file_sha256,download_result
    output=Path(output)
    if (output/'recovered-result.json').exists():raise ValueError('Already recovered')
    plan=json.loads((output/'experiment-plan.json').read_text())
    bundle=load_bundle(plan['source_bundle'])
    variant=eliminate_idle(bundle) if plan.get('formulation')=='no-idle' else condition_bundle(bundle)
    if variant['bundle_sha256']!=plan['sampling_bundle_sha256']:
        raise ValueError('Sampling input changed since submission')
    result=json.loads((output/'service/result.json').read_text())
    job_id=result['raw_artifacts']['job_id']
    start=time.monotonic()
    with RestClient() as client:
        job=Job._from_response(client.get('jobs/'+job_id))
        raw=output/'recovered-raw-result.h5'
        if not raw.exists():download_result(job,raw)
        q=load_qubo(variant)
        with h5py.File(raw,'r') as f:
            samples,convention=parse_samples(VeloxSampleSet.from_result(f),q,qubo_to_spin(q))
        result.update(status='completed',failure=None,samples=samples)
        result['configuration']['returned']=convention
        if plan['initializer']!='cold':
            result['configuration']['initializer_service_acceptance']='job completed; backend use/effect not proven'
        result['work'].update(returned_rows=sum(s['count'] for s in samples),distinct_samples=len(samples))
        result['raw_artifacts']['recovered_result']=dict(path=str(raw),sha256=file_sha256(raw))
        result['recovery']=dict(download_only=True,new_jobs_submitted=0,download_and_parse_s=time.monotonic()-start)
        result['backend_statistics']=job.statistics.model_dump(mode='json')
        mapped=rescore_result(bundle,variant,result)
        save(output/'recovered-result.json',mapped)
        summary=result_summary(bundle,mapped);save(output/'recovered-evaluation.json',summary)
    print(json.dumps(dict(recovered_existing_job=job_id,new_jobs=0,evaluation=summary),indent=2))
    return mapped


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',type=Path,default=Path('output/catering-velox-scale-v3/scale-512-qubo.json'))
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--allow-external',action='store_true')
    p.add_argument('--resume',action='store_true',help='Download existing saved job only; never submit')
    p.add_argument('--max-service-jobs',type=int,default=0,help='Total shared ledger count, including prior attempts')
    p.add_argument('--num-rep',type=int,default=512)
    p.add_argument('--num-steps',type=int,default=2000)
    p.add_argument('--timeout',type=float,default=60)
    p.add_argument('--formulation',choices=['deletion-bound','no-idle'],default='deletion-bound')
    p.add_argument('--initializer',choices=['cold','all-idle','incumbent'],default='cold')
    p.add_argument('--incumbent-result',type=Path,help='Method result whose best checked sample starts every replica')
    p.add_argument('--env-file',type=Path,default=Path('.env.velox-local'))
    a=p.parse_args()
    if a.resume:
        load_local_token(a.env_file)
        recover(a.output)
        return
    if a.output.exists():p.error('Fresh output directory required')
    b=load_bundle(a.bundle);variant=(eliminate_idle(b) if a.formulation=='no-idle' else condition_bundle(b))
    initial=None;incumbent=None
    if (a.initializer=='incumbent')!=(a.incumbent_result is not None):
        p.error('--incumbent-result is required with, and only with, --initializer incumbent')
    if a.initializer=='incumbent':initial,incumbent=incumbent_start(b,variant,a.incumbent_result)
    if a.initializer=='all-idle':
        idle={g['idle_index'] for g in b['onehot_groups']}
        initial=([0]*len(variant['linear']) if a.formulation=='no-idle' else [int(i in idle) for i in range(len(b['linear']))])
    load_local_token(a.env_file)
    a.output.mkdir(parents=True)
    plan=dict(kind='One conditioned VeloxQ job; raw output independently checked',
        source_bundle=str(a.bundle),source_bundle_sha256=b['bundle_sha256'],
        sampling_bundle_sha256=variant['bundle_sha256'],conditioning=variant['conditioning'],
        formulation=a.formulation,initializer=a.initializer,incumbent=incumbent,num_rep=a.num_rep,num_steps=a.num_steps,
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
