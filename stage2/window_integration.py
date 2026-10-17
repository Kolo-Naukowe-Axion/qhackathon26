"""Paired DEVELOPMENT integration runs; prior frozen tapes never evaluated."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time
import traceback

from . import final_eval as evaluation
from .spec import build
from .check import check_trace
from .identity_audit import audit_trace
from .window_qubo import digest
from .window_factory import attach_planner
from .window_campaign import save,sources


def run(output,orders=12,seeds=(0,1),methods=('baseline','constructive','anneal','compressed_uniform','compressed_qaoa','cp'),advice_mode='soft',seed_role='development'):
    output=Path(output);output.mkdir(parents=True,exist_ok=False);root,hashes=sources(output)
    for name,value in evaluation.source_hashes().items():
        data=(root/name).read_bytes();target=output/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
    for name in ('window_factory.py','window_integration.py'):
        relative='stage2/'+name;data=(root/relative).read_bytes();(output/'sources'/relative).write_bytes(data);hashes[relative]=hashlib.sha256(data).hexdigest()
    selection=root/'output/stage2-search/final-frozen-bundle-v20p2/strong-cheap-selection.json'
    method=next(m for m in json.loads(selection.read_text())['methods']if m['id']=='static-grid-12')
    protocol=dict(schema='stage2-window-integration-development.v1',orders=orders,horizon=5760,seeds=seeds,methods=methods,
        interval=240,max_parts=4,prefix_depth=2,window_horizon=480,grid=15,iterations=8,shots=256,angle_evaluations=24,advice_mode=advice_mode,
        frozen_baseline_method=method,baseline_selection_sha256=hashlib.sha256(selection.read_bytes()).hexdigest(),
        source_hashes=hashes,seed_role=seed_role,
        predeclared_quality_order=['mean missing orders (including revealed urgent orders)','mean terminal deadline debt','measured total wall time'],
        scope='New planning research, separate from frozen final campaign. Strong static recovery factory with advisory priority. Fresh-seed runs are small validation only; reused0/1 runs are diagnosis. No quantum advantage claim.',
        final_tapes_used=0,physical_qpu_calls=0,gpu_hours=0)
    save(output/'protocol.json',protocol);began=time.perf_counter();cpu=time.process_time();rows=[]
    for seed in seeds:
        for planner in methods:
            start=time.perf_counter();row=dict(seed=seed,method=planner,valid=False)
            try:
                config=dict(orders=orders,horizon=5760,profile='full');instance=build(**config,seed=seed);anchor=deepcopy(instance)
                weights,controller,_=evaluation._controller(method,config,900000)
                factory=evaluation._dispatch_factory(instance,weights,controller,method,config)
                if planner!='baseline':factory=attach_planner(factory,planner,advice_mode=advice_mode)
                trace=factory.run();checked=check_trace(trace,anchor);identity=audit_trace(trace,anchor)
                row.update(valid=checked['valid']and identity['valid']and checked.get('terminal_requirements_met',False),
                    metrics=trace['metrics'],independent_metrics=checked.get('metrics'),physical_check=checked,identity_check=identity,
                    planning_scope=trace.get('planning_scope'),instance_sha256=digest(anchor))
                save(output/f'{planner}-seed{seed}-trace.json',trace)
            except Exception as exc:row.update(error=str(exc),traceback=traceback.format_exc())
            row['wall_seconds']=time.perf_counter()-start;rows.append(row);save(output/'rows.json',rows)
            print(json.dumps(dict(seed=seed,method=planner,valid=row['valid'],shipped=row.get('metrics',{}).get('shipped'),
                tardiness=row.get('metrics',{}).get('total_tardiness_ticks'),planning=row.get('planning_scope'),error=row.get('error'),seconds=row['wall_seconds'])),flush=True)
    stable=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    summary=dict(rows=rows,source_stable=stable,wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu)
    save(output/'summary.json',summary);save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()})
    return dict(output=str(output),valid=sum(r['valid']for r in rows),runs=len(rows),source_stable=stable,wall_seconds=summary['wall_seconds'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--orders',type=int,default=12);a=p.parse_args()
    print(json.dumps(run(a.output,a.orders),indent=2))
