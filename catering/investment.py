"""What should the kitchen invest in? Classical what-if on the raw 12-customer case.

Each variant changes one resource of the frozen S3 lunch (outage plus urgent
order) and reruns the raw-input CP reference (native slots, not the QUBO) with the
same physical checker. The program count is the size of the complete program register,
i.e. the QUBO variables that variant would cost before any portfolio cut.
No quantum training, no service calls.
"""
import argparse
import copy
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from .build_meal_release import save
from .domain import digest, snapshot
from .meal_blocks import meal_fixture
from .native_slots import solve_native
from .options import enumerate_options


def add_resource(kind, name):
    def change(instance):
        instance['equipment'][kind].append(name)
        instance['calendars'][name] = [[0, instance['horizon_minutes']]]
    return change


def add_worker(name, skills):
    def change(instance):
        instance['workers'][name] = list(skills)
        instance['calendars'][name] = [[0, instance['horizon_minutes']]]
    return change


# (name, description, instance change, scenario). S1 is S3 without the outage.
VARIANTS = [
    ('baseline', 'Current kitchen: C2 outage plus urgent order (S3)', None, 'S3'),
    ('repair-c2', 'C2 repaired, no outage (S1)', None, 'S1'),
    ('third-cooker', 'Add cooker C3', add_resource('cook', 'C3'), 'S3'),
    ('second-prep', 'Add prep station P2', add_resource('prepare', 'P2'), 'S3'),
    ('second-pack', 'Add packing station K2', add_resource('pack', 'K2'), 'S3'),
    ('second-cook-worker', 'Hire worker W4 who can cook', add_worker('W4', ['cook']), 'S3'),
    ('flexible-worker', 'Hire worker W4 for prepare, cook and pack', add_worker('W4', ['prepare', 'cook', 'pack']), 'S3'),
]


def run_variant(args):
    name, customers, seconds, workers, seed = args
    _, description, change, scenario = next(v for v in VARIANTS if v[0] == name)
    instance = meal_fixture(customers)
    if change:
        change(instance)
    try:
        state = snapshot(instance, scenario)
        start = time.monotonic()
        programs = enumerate_options(instance, state)
    except ValueError as error:
        # The declared core profile refuses this resource; report it, do not approximate it.
        return dict(variant=name, description=description, scenario=scenario, status='unsupported by profile',
                    reason=str(error), metrics=None), None
    enumerate_s = time.monotonic()-start
    result = solve_native(instance, state, dict(wall_time_limit_s=seconds), dict(workers=workers, seed=seed))
    check = result.get('check') or {}
    metrics = check.get('metrics')
    return dict(variant=name, description=description, scenario=scenario, instance_sha256=digest(instance),
                programs=len(programs), enumerate_s=round(enumerate_s, 2), status=result['reference_status'],
                valid=bool(check.get('valid')), metrics={k: metrics[k] for k in 'UWBR'} if metrics else None,
                objective=result.get('objective'), bound=result.get('objective_bound')), result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--customers', type=int, default=12)
    p.add_argument('--seconds', type=float, default=60)
    p.add_argument('--workers', type=int, default=4)
    p.add_argument('--seed', type=int, default=2026)
    p.add_argument('--parallel', type=int, default=3)
    a = p.parse_args()
    if a.output.exists():
        p.error('Fresh output directory required')
    a.output.mkdir(parents=True)
    save(a.output/'experiment-plan.json', dict(kind=__doc__.splitlines()[0], customers=a.customers, seconds=a.seconds,
         workers=a.workers, seed=a.seed, variants=[dict(name=v[0], description=v[1], scenario=v[3]) for v in VARIANTS],
         quantum_training=0, veloxq_calls=0, physical_qpu_calls=0))
    jobs = [(v[0], a.customers, a.seconds, a.workers, a.seed) for v in VARIANTS]
    rows = []
    with ProcessPoolExecutor(a.parallel) as pool:
        for row, result in pool.map(run_variant, jobs):
            if result is not None:
                save(a.output/f'{row["variant"]}-result.json', result)
            rows.append(row)
            print(json.dumps(row), flush=True)
    save(a.output/'report.json', dict(rows=rows, note='U = missed complete meal lots (10 meals each); lower is better. '
         'FEASIBLE means the time limit ended before optimality was proven.'))


if __name__ == '__main__':
    main()
