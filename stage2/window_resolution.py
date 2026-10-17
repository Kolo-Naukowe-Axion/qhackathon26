"""Fine-grid raw CP references without constructing a huge time-indexed QUBO."""
import argparse
import hashlib
from pathlib import Path
import resource
import sys
import time
import json

from .window_campaign import sources,save
from .window_pump import pump_cell
from .window_qubo import solve_cp,digest,assignments


def run(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False);root,hashes=sources(output)
    name='stage2/window_resolution.py';data=(root/name).read_bytes();(output/'sources'/name).write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
    protocol=dict(cases=[dict(jobs=2,horizon=1440,grid=grid,metric_setups=True)for grid in(5,1)],
        source_hashes=hashes,solver_workers=4,seconds_per_solver=45,
        scope='Raw same-family model at finer integer start resolution; no QUBO constructed, no quantum/GPU calls. Machine-only setups, no human setup crews.')
    save(output/'protocol.json',protocol);rows=[];began=time.perf_counter();cpu=time.process_time()
    for index,case in enumerate(protocol['cases']):
        p=pump_cell(**case);folder=output/f'case{index}';folder.mkdir();save(folder/'problem.json',p)
        count=sum(len(assignments(p,op))for op in p['operations']);cp=solve_cp(p,45,4)
        row=dict(case=case,problem_sha256=digest(p),unary_assignment_bits_before_support=count,native_cp=cp);rows.append(row);save(folder/'report.json',row)
        print(json.dumps(dict(case=case,unary_assignment_bits=count,status=cp['status'],objective=cp.get('objective'),bound=cp.get('bound'),seconds=cp['wall_seconds'])),flush=True)
    stable=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    summary=dict(rows=rows,source_stable=stable,wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin'else 1024));save(output/'summary.json',summary)
    save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()})
    return {k:v for k,v in summary.items()if k!='rows'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(run(a.output),indent=2))
