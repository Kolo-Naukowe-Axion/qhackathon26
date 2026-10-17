"""Lift the CVaR tail fraction after local depth search, retaining every start."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from .qaoa_campaign import save, worker


def run(campaign, output, workers=4, evaluations=384):
    campaign, output = campaign.resolve(), output.resolve()
    if not (campaign / 'report.json').exists():
        raise ValueError('The depth campaign must finish before polishing')
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    hashes = {}
    for name in ['qaoa_polish.py', 'qaoa_training.py', 'qaoa_campaign.py', 'assignment_qaoa.py',
                 'column_qubo.py', 'window_qubo.py', 'trajectory_qubo.py']:
        data = (root / 'stage2' / name).read_bytes()
        target = output / 'sources' / 'stage2' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    protocol = dict(source_campaign=str(campaign), alpha_schedule=[.5, .75, 1.0],
                    starts_per_case_per_alpha=2, evaluations=evaluations, workers=workers,
                    initial_selection='Minimum alpha.25 CVaR; prefer shallowest within1e-9 of best',
                    selection='Minimum current-alpha training objective, also considering the unmodified prior circuit',
                    initialization='Prior selected angles; second start adds seed-fixed Gaussian perturbations sigma.15',
                    source_hashes=hashes, physical_qpu_calls=0, remote_calls=0)
    save(output / 'protocol.json', protocol)
    selected = {}
    for case in ['heat-outage-32', 'heat-lease-32']:
        choices = [json.loads(path.read_text()) for path in (campaign / case).glob('selected-p-*.json')]
        best_value = min(row['fit']['scaled_training_value'] for row in choices)
        best = min((row for row in choices if row['fit']['scaled_training_value'] <= best_value + 1e-9),
                   key=lambda row: row['fit']['layers'])
        selected[case] = best
        target = output / case
        target.mkdir()
        for name in ['problem.json', 'columns.json']:
            (target / name).write_bytes((campaign / case / name).read_bytes())
        save(target / 'initial-selection.json', best)
    began = time.perf_counter()
    rows = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for alpha in protocol['alpha_schedule']:
            jobs = []
            for case, prior in selected.items():
                angles = prior['fit']['gammas'] + prior['fit']['betas']
                for start in range(2):
                    seed = 19001 + int(alpha * 1000) + start * 1009
                    initial = angles if start == 0 else (np.array(angles) + np.random.default_rng(seed).normal(0, .15, len(angles))).tolist()
                    jobs.append(dict(case=case, layers=prior['fit']['layers'], seed=seed, alpha=alpha,
                                     evaluations=evaluations, initial=initial,
                                     problem=str(output / case / 'problem.json'), columns=str(output / case / 'columns.json'),
                                     target=str(output / case / f'alpha-{alpha}-start-{start}')))
            futures = [executor.submit(polish_worker, job) for job in jobs]
            batch = []
            for future in as_completed(futures):
                row = future.result()
                batch.append(row)
                compact = dict(case=row['job']['case'], alpha=alpha, layers=row['fit']['layers'],
                               value=row['fit']['scaled_training_value'], hit=row['assessment']['exact_hit_probability'],
                               feasible=row['assessment']['feasible_probability'], evaluations=row['fit']['evaluations'],
                               seconds=row['fit']['wall_seconds'])
                rows.append(compact)
                save(output / 'progress.json', rows)
                print(json.dumps(compact), flush=True)
            for case in selected:
                options = [row for row in batch if row['job']['case'] == case]
                # The first unperturbed start records its initial loss, so retaining
                # that prior is already guaranteed by train's best-observed rule.
                selected[case] = min(options, key=lambda row: row['fit']['scaled_training_value'])
                save(output / case / f'selected-alpha-{alpha}.json', selected[case])
    report = dict(protocol=protocol, rows=rows, wall_seconds=time.perf_counter() - began,
                  source_stable=all(hashlib.sha256((root / 'stage2' / name).read_bytes()).hexdigest() == sha
                                    for name, sha in hashes.items()))
    save(output / 'report.json', report)
    save(output / 'manifest.json', {str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
                                    for path in output.rglob('*') if path.is_file()})
    return report


def polish_worker(job):
    from .assignment_qaoa import AssignmentSector
    from .column_qubo import compile_columns
    from .qaoa_training import assess, train
    sector = AssignmentSector.build(compile_columns(json.loads(Path(job['problem']).read_text()),
                                                    json.loads(Path(job['columns']).read_text())))
    fit = train(sector, job['layers'], job['seed'], job['evaluations'], job['alpha'], job['initial'])
    target = Path(job['target'])
    # Names contain decimal alphas, so append suffixes instead of replacing them.
    save(Path(str(target) + '.fit.json'), fit)
    row = dict(job=job, fit=fit, assessment=assess(sector, fit, seeds=tuple(range(101, 111))))
    save(Path(str(target) + '.json'), row)
    return row


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--evaluations', type=int, default=384)
    args = parser.parse_args()
    run(args.campaign, args.output, args.workers, args.evaluations)
