"""Full raw128-operation reference using Mac compute and a heuristic hint."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

from .window_campaign import save,sources
from .window_qubo import solve_cp,digest


def run(case,output):
    case=Path(case);output=Path(output);output.mkdir(parents=True,exist_ok=False);root,hashes=sources(output)
    name='stage2/column_raw_reference.py';data=(root/name).read_bytes();(output/'sources'/name).write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
    source=json.loads((case/'report.json').read_text());problem=json.loads((case/'problem.json').read_text());parents=source['parent_generation']['parents']
    index=min(range(len(parents)),key=lambda i:source['parent_anchors'][i]['energy']);initial=parents[index]
    protocol=dict(schema='stage2-complete-raw-reference128.v1',source_case=str(case),source_report_sha256=hashlib.sha256((case/'report.json').read_bytes()).hexdigest(),
        problem_sha256=digest(problem),operations=len(problem['operations']),seconds=120,workers=4,initial_parent_index=index,initial_parent_objective=source['parent_anchors'][index]['energy'],
        source_hashes=hashes,compute='Local Apple M5 Pro; user authorized all available48GiB. No remote/GPU/QPU calls.',
        scope='Full SAME declared deterministic scheduling cell, all raw assignments allowed. This is not restricted to parent columns and is not the complete stochastic physical factory.')
    save(output/'protocol.json',protocol);save(output/'problem.json',problem);save(output/'initial-plan.json',initial);began=time.perf_counter();cpu=time.process_time()
    result=solve_cp(problem,120,4,initial)
    stable=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    report=dict(protocol=protocol,result=result,source_stable=stable,wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin'else 1024));save(output/'report.json',report)
    save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()})
    return dict(status=result['status'],objective=result.get('objective'),bound=result.get('bound'),seconds=report['wall_seconds'],peak_rss_bytes=report['peak_rss_bytes'],source_stable=stable)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',required=True);p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(run(a.case,a.output),indent=2))
