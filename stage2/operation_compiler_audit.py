"""Compare specialized compiler coefficients against a frozen general compiler."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

from .operation_qubo import compile_operations
from .window_campaign import save,sources
from .window_qubo import digest


def run(case,output):
    case,output=Path(case),Path(output)
    output.mkdir(parents=True,exist_ok=False)
    root,hashes=sources(output)
    for file in('operation_qubo.py','operation_compiler_audit.py','column_qubo.py','trajectory_qubo.py'):
        name='stage2/'+file
        data=(root/name).read_bytes()
        (output/'sources'/name).write_bytes(data)
        hashes[name]=hashlib.sha256(data).hexdigest()
    save(output/'protocol.json',dict(source_case=str(case),source_hashes=hashes,
         source_files={name:hashlib.sha256((case/name).read_bytes()).hexdigest()for name in('problem.json','columns.json','qubo.json','report.json')},
         scope='Every saved coefficient, variable, group and pool metadata compared; not a performance/quality improvement experiment.'))
    problem=json.loads((case/'problem.json').read_text())
    columns=json.loads((case/'columns.json').read_text())
    baseline=json.loads((case/'qubo.json').read_text())
    prior=json.loads((case/'report.json').read_text())
    began,cpu=time.perf_counter(),time.process_time()
    q=compile_operations(problem,columns)
    seconds=time.perf_counter()-began
    candidate=dict(linear=q.linear,quadratic=[[i,j,v]for(i,j),v in sorted(q.quadratic.items())],
                   offset=q.offset,groups=q.groups,variables=q.variables,metadata=q.metadata())
    checks={name:candidate[name]==baseline[name]for name in candidate}
    stable=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    report=dict(valid=all(checks.values()),checks=checks,source_stable=stable,operations=len(problem['operations']),
                coefficients_sha256=digest(candidate),master=q.metadata(),
                general_compile_seconds=prior['compile_wall_seconds'],specialized_compile_seconds=seconds,
                process_cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-began,
                peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin'else 1024))
    save(output/'report.json',report)
    save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()})
    return{k:v for k,v in report.items()if k not in('master',)}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    print(json.dumps(run(a.case,a.output),indent=2))
