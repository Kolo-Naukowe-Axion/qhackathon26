"""Prepare/test a proven conditioned VeloxQ input without spending service quota.

No SDK, token, network or training. Original frozen files are read-only.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
import time

from .build_meal_release import save, result_summary
from .conditioning import condition_bundle, rescore_result
from .contracts import load_bundle
from .methods.classical import solve_qubo
from .qubo import energy


def prepare(output, source, widths=(512,1024,2048), seeds=(2026,2027,2028), seconds=2):
    import math
    if not math.isfinite(seconds) or seconds<=0 or not widths or not seeds:
        raise ValueError('Positive finite budget and nonempty widths/seeds required')
    output,source=Path(output),Path(source)
    if output.exists():raise ValueError('Fresh output directory required')
    output.mkdir(parents=True)
    plan=dict(kind='Local conditioning ablation, not VeloxQ service performance',
        source=str(source),widths=list(widths),seeds=list(seeds),seconds_per_sa=seconds,
        restarts=4,sweeps=100,initializer='Seeded random raw bits',repair=False,
        selection='All declared tiers/seeds retained; no parameter selection from these results',
        veloxq_calls=0,physical_qpu_calls=0)
    root=Path(__file__).resolve().parents[1]
    source_paths=['catering/conditioning.py','catering/tune_veloxq.py','catering/methods/classical.py','catering/decode.py']
    sources={}
    for name in source_paths:
        sources[name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
        target=output/'source_snapshot'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(root/name,target)
    save(output/'experiment-plan.json',plan)
    rows=[]
    for width in widths:
        start=time.monotonic()
        bundle=load_bundle(source/f'scale-{width}-qubo.json')
        load_s=time.monotonic()-start
        start=time.monotonic()
        variant=condition_bundle(bundle)
        conditioning_s=time.monotonic()-start
        # Frozen matrix can be regenerated exactly; avoid a second large JSON archive.
        idle=[int(i in {g['idle_index'] for g in bundle['onehot_groups']}) for i in range(width)]
        assert energy(bundle,idle)==energy(variant,idle)
        row=dict(width=width,load_s=load_s,conditioning_s=conditioning_s,source_bundle_sha256=bundle['bundle_sha256'],sampling_bundle_sha256=variant['bundle_sha256'],
            source_penalty=bundle['penalty'],conditioned_penalty=variant['penalty'],
            penalty_reduction=int(bundle['penalty'])/int(variant['penalty']),
            idle_energy=str(energy(bundle,idle)),trials=[])
        for seed in seeds:
            trial=dict(seed=seed)
            # Alternate order across seeds; each solver includes its own wall timer.
            order=[('original',bundle),('conditioned',variant)]
            if seed%2:order.reverse()
            for name,matrix in order:
                start=time.monotonic()
                result=solve_qubo(matrix,dict(wall_time_limit_s=seconds),dict(seed=seed,restarts=4,sweeps=100))
                measured=time.monotonic()-start
                sampling_hash=matrix['bundle_sha256']
                if name=='conditioned':result=rescore_result(bundle,variant,result)
                save(output/f'scale-{width}-{name}-seed{seed}.json',result)
                trial[name]=dict(**result_summary(bundle,result),whole_call_s=measured,sampling_bundle_sha256=sampling_hash)
            row['trials'].append(trial)
            print(json.dumps(dict(width=width,seed=seed,results={name:dict(valid=t['valid_returns'],best=t['best_metrics']) for name,t in trial.items() if name!='seed'})),flush=True)
        rows.append(row)
    report=dict(**plan,rows=rows,limitations=[
        'Local SA ablation does not establish a VeloxQ improvement',
        'Invalid energies differ; feasible schedules, objective, priorities, bits and ground optima agree',
        'Same-seed trajectories differ after changed acceptance decisions; elapsed budgets are approximate',
        'Preprocessing is recorded separately from the per-solver search budget'])
    save(output/'report.json',report)
    save(output/'manifest.json',dict(sources=sources,files={str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest() for p in output.rglob('*') if p.is_file()}))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source',type=Path,default=Path('output/catering-velox-scale-v3'))
    parser.add_argument('--widths',type=int,nargs='+',default=[512,1024,2048])
    parser.add_argument('--seeds',type=int,nargs='+',default=[2026,2027,2028])
    parser.add_argument('--seconds',type=float,default=2)
    parser.add_argument('--export-bundle',type=Path,help='Write one conditioned matrix instead of running SA')
    args=parser.parse_args()
    if args.export_bundle:
        if args.export_bundle.exists():parser.error('Choose a fresh export path')
        if len(args.widths)!=1:parser.error('Export requires exactly one width')
        bundle=load_bundle(args.source/f'scale-{args.widths[0]}-qubo.json')
        save(args.export_bundle,condition_bundle(bundle))
    else:prepare(args.output,args.source,args.widths,args.seeds,args.seconds)
