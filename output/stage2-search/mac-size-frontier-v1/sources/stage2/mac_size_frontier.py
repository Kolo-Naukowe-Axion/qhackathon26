"""Mac-only size frontier, largest first, with unchanged grid/resources/horizon."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import traceback

from .column_parents import generate
from .window_campaign import save,sources
from .window_interval_reference import solve_interval_cp
from .window_pump import pump_cell
from .window_qubo import check_plan,digest


def run(output,jobs=(32,24,16,8),seconds=120):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    root,hashes=sources(output)
    for file in('column_parents.py','window_interval_reference.py','mac_size_frontier.py'):
        name='stage2/'+file
        data=(root/name).read_bytes()
        (output/'sources'/name).write_bytes(data)
        hashes[name]=hashlib.sha256(data).hexdigest()
    protocol=dict(schema='stage2-mac-size-frontier.v1',jobs=list(jobs),horizon=5760,grid=15,origin=2160,
                  metric_setups=True,native_cp_seconds=seconds,workers=4,parent_attempts=16,parent_seconds=30,
                  wanted_parents=1,max_raw_candidates=2000000,source_hashes=hashes,
                  compute='Local Mac CPU only; all48GiB authorized; no remote or QPU calls',
                  scope='Same deterministic cell features and96h horizon at every size. Fixed15machines/10workers; more orders increase congestion. No global time-indexed QUBO matrix or quantum circuit is built in this classical size/quality probe. AGV capacity, shipping, buffers, tools, energy and stochastic quality remain excluded.',
                  timing='Parent time limit checked between attempts, not a hard per-attempt interrupt. Native CP budget excludes model build.')
    save(output/'protocol.json',protocol)
    began,cpu=time.perf_counter(),time.process_time()
    results=[]
    for size in jobs:
        folder=output/f'pumps{size}'
        folder.mkdir()
        case_start,case_cpu=time.perf_counter(),time.process_time()
        row=dict(jobs=size,operations=16*size)
        try:
            problem=pump_cell(size,5760,15,2160,True)
            save(folder/'problem.json',problem)
            row['problem_sha256']=digest(problem)
            print(json.dumps(dict(jobs=size,operations=len(problem['operations']),phase='raw heuristic initialization')),flush=True)
            parents=generate(problem,16,1,7001,30,max_candidates=2000000)
            row['parent_generation']=parents
            save(folder/'parent-generation.json',parents)
            initial=min(parents['parents'],key=lambda plan:check_plan(problem,plan)['objective'])if parents['parents']else None
            row['initial_objective']=check_plan(problem,initial)['objective']if initial else None
            save(folder/'report.json',row)
            print(json.dumps(dict(jobs=size,phase='native raw CP',initial_objective=row['initial_objective'],raw_candidates=parents['raw_assignment_candidates'])),flush=True)
            result=solve_interval_cp(problem,seconds,4,initial)
            row['result']=result
            # UNKNOWN does not erase an independently checked heuristic witness.
            candidates=parents['parents']+([result['plan']]if'plan'in result else[])
            if candidates:
                best=min(candidates,key=lambda plan:check_plan(problem,plan)['objective'])
                checked=check_plan(problem,best)
                if not checked['valid']:raise AssertionError('Size-frontier incumbent failed raw checker')
                row['best_feasible_objective']=checked['objective']
                row['best_plan_check']=checked
                save(folder/'best-plan.json',best)
            row['certified_lower_bound']=result.get('bound',0)
        except Exception as exc:
            row.update(error=str(exc),traceback=traceback.format_exc())
        row.update(wall_seconds=time.perf_counter()-case_start,process_cpu_seconds=time.process_time()-case_cpu,
                   process_peak_rss_so_far_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin'else 1024))
        save(folder/'report.json',row)
        results.append(row)
        print(json.dumps({k:v for k,v in row.items()if k not in('parent_generation','result','traceback')}|dict(status=row.get('result',{}).get('status'))),flush=True)
    stable=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    summary=dict(results=results,source_stable=stable,wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,
                 peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin'else 1024))
    save(output/'summary.json',summary)
    save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()})
    return{k:v for k,v in summary.items()if k!='results'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True)
    p.add_argument('--jobs',type=int,nargs='+',default=[32,24,16,8])
    p.add_argument('--seconds',type=int,default=120)
    a=p.parse_args()
    print(json.dumps(run(a.output,a.jobs,a.seconds),indent=2))
