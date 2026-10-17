"""Frozen local probe of flexible component columns and their native reference."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

from .column_flexible import enrich_flexible
from .column_qubo import compile_columns
from .column_reference import solve_column_cp
from .window_campaign import save, sources


def run(campaign, output, cap=48, radius=120):
    campaign = Path(campaign)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    root, hashes = sources(output)
    for file in ('trajectory_qubo.py', 'column_qubo.py', 'column_reference.py',
                 'column_flexible.py', 'column_flexible_experiments.py'):
        name = 'stage2/' + file
        data = (root / name).read_bytes()
        (output / 'sources' / name).write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    protocol = dict(source_campaign=str(campaign), source_hashes=hashes,
                    per_group_cap=cap, radius=radius, native_pool_cp_seconds=20,
                    workers=4, cp_teacher_used=False, quantum_calls=0,
                    compute='Local Mac CPU only',
                    scope='Restricted column pool; full raw references inherited, not used to generate columns.')
    save(output / 'protocol.json', protocol)
    results = []
    began = time.perf_counter()
    cpu = time.process_time()
    for path in sorted(campaign.glob('case*/report.json')):
        prior = json.loads(path.read_text())
        problem = json.loads((path.parent / 'problem.json').read_text())
        columns = json.loads((path.parent / 'columns.json').read_text())
        parents = prior['parent_generation']['parents']
        initial = parents[min(range(len(parents)), key=lambda i: prior['parent_anchors'][i]['energy'])]
        folder = output / path.parent.name
        folder.mkdir()
        pool, preparation = enrich_flexible(problem, columns, cap, radius)
        save(folder / 'problem.json', problem)
        save(folder / 'columns.json', pool)
        build = time.perf_counter()
        q = compile_columns(problem, pool)
        compile_seconds = time.perf_counter() - build
        reference = solve_column_cp(problem, pool, 20, 4, initial)
        if 'plan' in reference:
            bits = q.encode(reference['plan'])
            assert q.decode(bits)['valid'] and q.energy(bits) == reference['objective']
        save(folder / 'qubo.json', dict(linear=q.linear,
             quadratic=[[i,j,v] for (i,j),v in sorted(q.quadratic.items())],
             offset=q.offset, groups=q.groups, variables=q.variables, metadata=q.metadata()))
        row = dict(case=prior['case'], master=q.metadata(), preparation=preparation,
                   compile_wall_seconds=compile_seconds, native_pool_cp=reference,
                   best_parent_objective=prior['best_parent_objective'],
                   native_raw_cp=prior['native_raw_cp'], initial_parent_plan=initial,
                   source_report_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        if 'objective' in reference:
            row['improvement_over_best_parent'] = prior['best_parent_objective'] - reference['objective']
        save(folder / 'report.json', row)
        results.append(row)
        print(json.dumps(dict(case=path.parent.name, operations=len(problem['operations']),
              bits=len(q.linear), couplers=len(q.quadratic), pool_status=reference['status'],
              objective=reference.get('objective'), bound=reference['bound'],
              parent=prior['best_parent_objective'], improvement=row.get('improvement_over_best_parent'))), flush=True)
    stable = all(hashlib.sha256((root/name).read_bytes()).hexdigest() == value for name,value in hashes.items())
    summary = dict(results=results, source_stable=stable,
                   wall_seconds=time.perf_counter()-began, process_cpu_seconds=time.process_time()-cpu,
                   peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024))
    save(output/'summary.json', summary)
    save(output/'manifest.json', {str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted(output.rglob('*')) if p.is_file()})
    return {k:v for k,v in summary.items() if k != 'results'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaign', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--cap', type=int, default=48)
    p.add_argument('--radius', type=int, default=120)
    a = p.parse_args()
    print(json.dumps(run(a.campaign, a.output, a.cap, a.radius), indent=2))
