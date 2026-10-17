"""Longer local raw reference, warm-started from a retained feasible reference."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

from .window_campaign import save,sources
from .window_interval_reference import solve_interval_cp
from .window_qubo import check_plan,digest


def run(case,output,seconds=600):
    case,output=Path(case),Path(output)
    output.mkdir(parents=True,exist_ok=False)
    root,hashes=sources(output)
    for file in('window_interval_reference.py','window_reference_refine.py'):
        name='stage2/'+file
        data=(root/name).read_bytes()
        (output/'sources'/name).write_bytes(data)
        hashes[name]=hashlib.sha256(data).hexdigest()
    prior=json.loads((case/'report.json').read_text())
    problem=json.loads((case/'problem.json').read_text())
    initial=prior['result']['plan']
    checked=check_plan(problem,initial)
    if not checked['valid']:
        raise ValueError('Retained feasible raw hint required')
    protocol=dict(source_case=str(case),source_report_sha256=hashlib.sha256((case/'report.json').read_bytes()).hexdigest(),
                  problem_sha256=digest(problem),source_hashes=hashes,solve_seconds=seconds,workers=4,
                  initial_objective=checked['objective'],inherited_bound=prior['result']['bound'],
                  compute='Local Mac CPU only',
                  scope='Continuation of complete raw deterministic reference with its own feasible hint. No CP solution supplies quantum candidates or initializer.')
    save(output/'protocol.json',protocol)
    save(output/'problem.json',problem)
    save(output/'initial-plan.json',initial)
    began,cpu=time.perf_counter(),time.process_time()
    result=solve_interval_cp(problem,seconds,4,initial)
    stable=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    report=dict(protocol=protocol,result=result,source_stable=stable,wall_seconds=time.perf_counter()-began,
                process_cpu_seconds=time.process_time()-cpu,
                peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin'else 1024))
    save(output/'report.json',report)
    save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()})
    return dict(status=result['status'],objective=result.get('objective'),bound=result.get('bound'),
                seconds=report['wall_seconds'],process_cpu_seconds=report['process_cpu_seconds'],source_stable=stable)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--seconds',type=int,default=600)
    a=p.parse_args()
    print(json.dumps(run(a.case,a.output,a.seconds),indent=2))
