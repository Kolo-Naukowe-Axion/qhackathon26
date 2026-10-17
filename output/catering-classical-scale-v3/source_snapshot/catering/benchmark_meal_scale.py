"""Longer local references/SA on the frozen VeloxQ-track paired-meal inputs.

Separate from service execution. Preserve the initial five-second receipts.
Budgets/settings are declared before execution; do not overwrite evidence.
"""
import argparse
import json
from pathlib import Path
import time

from .build_meal_release import save, seal, result_summary
from .contracts import load_bundle
from .domain import digest
from .meal_reference import solve_bundle
from .methods.classical import solve_qubo
from .native_slots import solve_native


def run(output, source, seconds=30, sa_seconds=2):
    output,source=Path(output),Path(source)
    if output.exists():raise ValueError('Fresh output required')
    output.mkdir(parents=True)
    save(output/'experiment-plan.json',dict(source=str(source),widths=[512,1024,2048],
        reference_seconds=seconds,sa_seconds=sa_seconds,workers=1,seed=2026,
        sa=dict(restarts=4,sweeps=100,initializer='Seeded random raw bits',repair=False),
        physical_qpu_calls=0,veloxq_calls=0))
    instance=json.loads((source/'instance.json').read_text());state=json.loads((source/'snapshot.json').read_text())
    started=time.monotonic()
    raw=solve_native(instance,state,dict(wall_time_limit_s=seconds),dict(workers=1,seed=2026))
    raw_wall=time.monotonic()-started
    save(output/'raw-reference.json',raw)
    print(dict(method='raw',status=raw['reference_status'],metrics=(raw.get('check') or {}).get('metrics')),flush=True)
    rows=[]
    for width in (512,1024,2048):
        started=time.monotonic();bundle=load_bundle(source/f'scale-{width}-qubo.json');load_s=time.monotonic()-started
        started=time.monotonic();cp=solve_bundle(bundle,seconds=seconds,seed=2026);cp_wall=time.monotonic()-started
        save(output/f'scale-{width}-reference.json',cp)
        started=time.monotonic();sa=solve_qubo(bundle,dict(wall_time_limit_s=sa_seconds),dict(seed=2026,restarts=4,sweeps=100));sa_wall=time.monotonic()-started
        save(output/f'scale-{width}-sa.json',sa)
        row=dict(width=width,bundle_sha256=bundle['bundle_sha256'],load_s=load_s,
                 cp=result_summary(bundle,cp),sa=result_summary(bundle,sa),cp_call_wall_s=cp_wall,sa_call_wall_s=sa_wall)
        rows.append(row);print(dict(width=width,cp=row['cp']['reference']['status'],metrics=row['cp']['best_metrics'],sa_metrics=row['sa']['best_metrics']),flush=True)
    report=dict(profile_id=instance['profile_id'],instance_sha256=digest(instance),snapshot_sha256=digest(state),
        raw_reference_status=raw['reference_status'],raw_reference_metrics=(raw.get('check') or {}).get('metrics'),
        raw_call_wall_s=raw_wall,rows=rows,physical_qpu_calls=0,veloxq_calls=0,
        limitations=['One seed and one CPU configuration; not a timing distribution or intrinsic hardness claim',
           'CP uses one-hot/conflict constraints to solve the identical QUBO ground problem under the proved penalty bound',
           'Cold raw-bit SA has a different initializer/search space than one-hot quantum controls; returned-state validity is not all-visited-state validity',
           'Reference budgets and SDK/import/loading/pipeline timing are reported separately; caps have scheduler/presolve overhead'])
    save(output/'report.json',report);seal(output)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--source',type=Path,default=Path('output/catering-velox-scale-v3'))
    p.add_argument('--reference-seconds',type=float,default=30);p.add_argument('--sa-seconds',type=float,default=2)
    a=p.parse_args();run(a.output,a.source,a.reference_seconds,a.sa_seconds)
