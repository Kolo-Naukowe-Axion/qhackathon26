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


def run(source, output, workers=4, evaluations=256, depths=(2, 4, 8, 12), starts=4, resume=False):
    if workers < 1 or starts < 2 or sorted(set(depths)) != list(depths) or depths[0] != 2:
        raise ValueError('Positive workers, >=2 starts, and increasing depths beginning at2 required')
    source, output = source.resolve(), output.resolve()
    output.mkdir(parents=True, exist_ok=resume)
    root = Path(__file__).resolve().parents[1]
    sources = {}
    names = ['qaoa_training.py', 'qaoa_campaign.py', 'assignment_qaoa.py', 'column_qubo.py',
             'window_qubo.py', 'trajectory_qubo.py', 'column_parents.py', 'recipe_bridge.py']
    original = json.loads((output / 'protocol.json').read_text()) if resume else None
    if resume:
        expected = (str(source), workers, evaluations, list(depths), starts)
        actual = (original['source_campaign'], original['workers'],
                  original['max_adjoint_evaluations_per_start'], original['depths'], original['starts_per_depth'])
        if expected != actual:
            raise ValueError('Resume requires the exact original configuration')
        for name, sha in original['source_hashes'].items():
            if name != 'qaoa_campaign.py' and hashlib.sha256((root / 'stage2' / name).read_bytes()).hexdigest() != sha:
                raise ValueError('Training/model source changed since interruption: ' + name)
        resume_index = len(list(output.glob('resume-*.json'))) + 1
        runner = output / f'resume-{resume_index}-runner.py'
        runner.write_bytes(Path(__file__).read_bytes())
        save(output / f'resume-{resume_index}.json', dict(runner_sha256=hashlib.sha256(runner.read_bytes()).hexdigest(),
             model_and_training_sources_unchanged=True,
             interrupted_inflight_cpu_unmeasured=True,
             prior_progress=json.loads((output / 'progress.json').read_text())))
    for name in names:
        path = root / 'stage2' / name
        target = output / 'sources' / 'stage2' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not resume:
            target.write_bytes(path.read_bytes())
        sources[name] = hashlib.sha256(target.read_bytes()).hexdigest()
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
    if resume:
        protocol = original
    else:
        save(output / 'protocol.json', protocol)
    began = time.perf_counter()
    selected, rows = {}, []
    for case in cases:
        directory = output / case
        directory.mkdir(exist_ok=resume)
        for filename, path in [('problem.json', source / case / 'problem.json'),
                               ('columns.json', source / case / 'cap-4' / 'columns.json')]:
            if resume:
                if (directory / filename).read_bytes() != path.read_bytes():
                    raise ValueError('Frozen input changed: ' + str(path))
            else:
                (directory / filename).write_bytes(path.read_bytes())
        baseline = json.loads((source / case / 'cap-4' / 'qaoa_xy-7.json').read_text())
        if not resume:
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
            batch = []
            pending = []
            for job in jobs:
                saved = Path(job['target']).with_suffix('.json')
                if resume and saved.exists():
                    batch.append(json.loads(saved.read_text()))
                else:
                    pending.append(executor.submit(worker, job))
            def completed():
                yield from batch[:]
                for future in as_completed(pending):
                    result = future.result()
                    batch.append(result)
                    yield result
            for result in completed():
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
                saved = output / case / f'selected-p-{depth}.json'
                if resume and saved.exists():
                    best = json.loads(saved.read_text())
                else:
                    save(saved, best)
                selected[case] = best['fit']
    report = dict(protocol=protocol, rows=rows, wall_seconds=time.perf_counter() - began,
                  training_cpu_seconds=sum(json.loads(path.read_text())['process_cpu_seconds']
                                           for path in output.glob('*/p-*/*.fit.json')),
                  selected={case: dict(layers=fit['layers'], seed=fit['seed'],
                                       scaled_training_value=fit['scaled_training_value'])
                            for case, fit in selected.items()},
                  source_stable=all(hashlib.sha256((root / 'stage2' / name).read_bytes()).hexdigest() == value
                                    for name, value in sources.items()),
                  model_and_training_source_stable=all(hashlib.sha256((root / 'stage2' / name).read_bytes()).hexdigest() == value
                                    for name, value in sources.items() if name != 'qaoa_campaign.py'),
                  resumed=resume, timings_scope='This invocation wall time; retained completed fit CPU only. '
                  'Interrupted in-flight CPU is unmeasured. Prior invocation progress retained in resume receipt.')
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
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    run(args.source, args.output, args.workers, args.evaluations, tuple(args.depths), args.starts, args.resume)
