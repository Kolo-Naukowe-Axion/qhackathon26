"""Copied-source local compact raw CP reference, largest declared cell first."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

from .window_campaign import save, sources
from .window_interval_reference import solve_interval_cp


def run(campaign, output):
    campaign, output = Path(campaign), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    root, hashes = sources(output)
    for file in ('window_interval_reference.py','window_interval_experiments.py'):
        name = 'stage2/'+file
        data = (root/name).read_bytes()
        (output/'sources'/name).write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    save(output/'protocol.json', dict(source_campaign=str(campaign), source_hashes=hashes,
         workers=4, seconds_128ops=120, seconds_smaller=20, quantum_calls=0,
         compute='Local Apple M5 Pro CPU only; memory up to48GiB authorized',
         scope='Native complete deterministic raw cells, exact calendar mode domains; all reference and heuristic failures retained.'))
    began, cpu = time.perf_counter(), time.process_time()
    results = []
    for path in sorted(campaign.glob('case*/report.json')):
        prior = json.loads(path.read_text())
        problem = json.loads((path.parent/'problem.json').read_text())
        parents = prior['parent_generation']['parents']
        index = min(range(len(parents)), key=lambda i:prior['parent_anchors'][i]['energy'])
        folder = output/path.parent.name
        folder.mkdir()
        save(folder/'problem.json', problem)
        save(folder/'initial-plan.json', parents[index])
        seconds = 120 if len(problem['operations'])>64 else 20
        result = solve_interval_cp(problem, seconds, 4, parents[index])
        row = dict(case=prior['case'], operations=len(problem['operations']), solve_budget_seconds=seconds,
                   best_parent_objective=prior['best_parent_objective'], result=result,
                   prior_native_raw_cp=prior['native_raw_cp'], source_report_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        save(folder/'report.json', row)
        results.append(row)
        print(json.dumps(dict(case=path.parent.name, operations=len(problem['operations']),
             status=result['status'], objective=result.get('objective'), bound=result.get('bound'),
             seconds=result.get('wall_seconds'), build_seconds=result.get('model_build_seconds'),
             variables=result.get('model_variables'))), flush=True)
    stable = all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    summary = dict(results=results, source_stable=stable, wall_seconds=time.perf_counter()-began,
                   process_cpu_seconds=time.process_time()-cpu,
                   peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024))
    save(output/'summary.json', summary)
    save(output/'manifest.json', {str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted(output.rglob('*')) if p.is_file()})
    return {k:v for k,v in summary.items() if k!='results'}


if __name__=='__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaign', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    print(json.dumps(run(a.campaign,a.output),indent=2))
