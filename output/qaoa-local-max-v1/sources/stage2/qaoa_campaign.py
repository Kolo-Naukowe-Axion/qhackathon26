"""Bounded, resumable local QAOA depth/multistart study on frozen recipe pools."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import platform
import time

import numpy as np

from .assignment_qaoa import AssignmentSector
from .column_qubo import compile_columns
from .qaoa_training import assess, train


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def worker(job):
    problem = json.loads(Path(job['problem']).read_text())
    columns = json.loads(Path(job['columns']).read_text())
    began = time.perf_counter()
    sector = AssignmentSector.build(compile_columns(problem, columns))
    preparation = time.perf_counter() - began
    fit = train(sector, layers=job['layers'], seed=job['seed'], evaluations=job['evaluations'],
                alpha=.25, initial=job['initial'])
    # Fit is retained before reference reporting/measurement.
    target = Path(job['target'])
    save(target.with_suffix('.fit.json'), fit)
    result = dict(job=job, fit=fit, preparation_seconds=preparation,
                  assessment=assess(sector, fit, seeds=tuple(range(101, 111)), shots=512))
    save(target.with_suffix('.json'), result)
    return result


def run(source, output, workers=4, evaluations=256, depths=(2, 4, 8, 12), starts=4):
    if workers < 1 or starts < 2 or sorted(set(depths)) != list(depths) or depths[0] != 2:
        raise ValueError('Positive workers, >=2 starts, and increasing depths beginning at2 required')
    source, output = source.resolve(), output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    sources = {}
    names = ['qaoa_training.py', 'qaoa_campaign.py', 'assignment_qaoa.py', 'column_qubo.py',
             'window_qubo.py', 'trajectory_qubo.py', 'column_parents.py', 'recipe_bridge.py']
    for name in names:
        path = root / 'stage2' / name
        target = output / 'sources' / 'stage2' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
        sources[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    cases = ['heat-outage-32', 'heat-lease-32']
    protocol = dict(schema='stage2-local-qaoa-training.v1', source_campaign=str(source),
                    cases=cases, cap=4, depths=list(depths), starts_per_depth=starts,
                    max_adjoint_evaluations_per_start=evaluations, alpha=.25, workers=workers,
                    selection='Minimum CVaR training objective; no exact-hit/optimum-based selection',
                    initialization='First start: historical p2 angles; later depths: trained lower-depth angles '
                    'plus small-angle layers; second start perturbs that circuit; remaining starts random',
                    sampling_seeds=list(range(101, 111)), shots_per_replica=512,
                    source_hashes=sources, platform=platform.platform(), cpu_count=os.cpu_count(),
                    physical_memory_bytes=os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES'),
                    remote_calls=0, physical_qpu_calls=0,
                    limitations=['Known development instances and previously frozen restricted pools',
                                 'Reused candidate construction; its historical cost is not new search work',
                                 'Exact sector energies and exact simulated gradients, not hardware-shot training',
                                 'Ten Born replicas per trained distribution are not ten independent problems',
                                 'Adjoint calls include a forward and reverse pass, unlike a value-only evaluation',
                                 'Historical64-evaluation baseline has a smaller compute budget'])
    save(output / 'protocol.json', protocol)
    began = time.perf_counter()
    selected, rows = {}, []
    for case in cases:
        directory = output / case
        directory.mkdir()
        for filename, path in [('problem.json', source / case / 'problem.json'),
                               ('columns.json', source / case / 'cap-4' / 'columns.json')]:
            (directory / filename).write_bytes(path.read_bytes())
        baseline = json.loads((source / case / 'cap-4' / 'qaoa_xy-7.json').read_text())
        save(directory / 'historical-baseline.json', baseline)
        selected[case] = baseline['optimization']
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for depth in depths:
            jobs = []
            for case in cases:
                prior = selected[case]
                extra = depth - len(prior['gammas'])
                warm = prior['gammas'] + [.05] * extra + prior['betas'] + [.05] * extra
                for start in range(starts):
                    seed = 17041 + 1009 * start + 97 * depth
                    rng = np.random.default_rng(seed)
                    initial = warm if start == 0 else (np.array(warm) + rng.normal(0, .25, 2 * depth)).tolist() if start == 1 else None
                    directory = output / case / f'p-{depth}'
                    directory.mkdir(exist_ok=True)
                    jobs.append(dict(case=case, layers=depth, seed=seed, evaluations=evaluations,
                                     initial=initial, problem=str(output / case / 'problem.json'),
                                     columns=str(output / case / 'columns.json'),
                                     target=str(directory / f'start-{start}')))
            futures = [executor.submit(worker, job) for job in jobs]
            batch = []
            for future in as_completed(futures):
                result = future.result()
                batch.append(result)
                compact = dict(case=result['job']['case'], layers=depth, seed=result['fit']['seed'],
                               value=result['fit']['scaled_training_value'], evaluations=result['fit']['evaluations'],
                               hit=result['assessment']['exact_hit_probability'],
                               feasible=result['assessment']['feasible_probability'], seconds=result['fit']['wall_seconds'])
                rows.append(compact)
                save(output / 'progress.json', dict(rows=rows, elapsed_seconds=time.perf_counter() - began))
                print(json.dumps(compact), flush=True)
            for case in cases:
                best = min((r for r in batch if r['job']['case'] == case),
                           key=lambda r: r['fit']['scaled_training_value'])
                selected[case] = best['fit']
                save(output / case / f'selected-p-{depth}.json', best)
    report = dict(protocol=protocol, rows=rows, wall_seconds=time.perf_counter() - began,
                  training_cpu_seconds=sum(json.loads(path.read_text())['process_cpu_seconds']
                                           for path in output.glob('*/p-*/*.fit.json')),
                  selected={case: dict(layers=fit['layers'], seed=fit['seed'],
                                       scaled_training_value=fit['scaled_training_value'])
                            for case, fit in selected.items()},
                  source_stable=all(hashlib.sha256((root / 'stage2' / name).read_bytes()).hexdigest() == value
                                    for name, value in sources.items()))
    save(output / 'report.json', report)
    save(output / 'manifest.json', {str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
                                    for path in output.rglob('*') if path.is_file()})
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('output/recipe-bridge-review-v2'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--evaluations', type=int, default=256)
    parser.add_argument('--depths', type=int, nargs='+', default=[2, 4, 8, 12])
    parser.add_argument('--starts', type=int, default=4)
    args = parser.parse_args()
    run(args.source, args.output, args.workers, args.evaluations, tuple(args.depths), args.starts)
