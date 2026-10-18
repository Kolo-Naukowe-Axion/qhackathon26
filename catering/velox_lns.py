"""One large-neighbourhood step: VeloxQ solves a sub-QUBO of a classical plan.

A classical incumbent fixes every block except a few freed ones. Freed program
bits form an exact sub-QUBO of the no-idle sampling matrix: for every freed
assignment y, E_sub(y) equals the full sampling energy with the rest fixed.
Exact enumeration of the freed blocks certifies the sub-optimum offline.
Offline unless --allow-external; one service job per call; no repair.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

from .build_meal_release import save
from .conditioning import eliminate_idle, lift_bits
from .contracts import load_bundle, method_result
from .decode import decode
from .domain import digest
from .qubo import energy
from .veloxq_pilot import incumbent_start


def subproblem(variant, fixed, free):
    """Exact sub-QUBO over sampling indices `free`, others held at `fixed`."""
    free = sorted(free)
    pos = {i: k for k, i in enumerate(free)}
    linear = [int(variant['linear'][i]) for i in free]
    constant = int(variant['constant'])
    for i, c in enumerate(variant['linear']):
        if i not in pos and fixed[i]:
            constant += int(c)
    quadratic = {}
    for t in variant['quadratic']:
        i, j, value = t['i'], t['j'], int(t['value'])
        if i in pos and j in pos:
            quadratic[(pos[i], pos[j])] = quadratic.get((pos[i], pos[j]), 0)+value
        elif i in pos:
            linear[pos[i]] += value*fixed[j]
        elif j in pos:
            linear[pos[j]] += value*fixed[i]
        else:
            constant += value*fixed[i]*fixed[j]
    sub = dict(kind='lns-subqubo.v1', parent_sampling_bundle_sha256=variant['bundle_sha256'],
               free_indices=free, fixed_bits_sha256=hashlib.sha256(json.dumps(fixed).encode()).hexdigest(),
               variable_order=[variant['variable_order'][i] for i in free],
               constant=str(constant), linear=[str(c) for c in linear],
               quadratic=[dict(i=i, j=j, value=str(v)) for (i, j), v in sorted(quadratic.items()) if v])
    sub['bundle_sha256'] = digest(sub)
    return sub


def sub_energy(sub, y):
    return (int(sub['constant'])+sum(int(c)*x for c, x in zip(sub['linear'], y))
            + sum(int(t['value'])*y[t['i']]*y[t['j']] for t in sub['quadratic']))


def merge(fixed, sub, y):
    bits = list(fixed)
    for i, x in zip(sub['free_indices'], y):
        bits[i] = x
    return bits


def exact_block_optimum(sub, groups):
    """Enumerate none-or-one program per freed block (the proven feasible set)."""
    pos = {i: k for k, i in enumerate(sub['free_indices'])}
    choices = [[None]+[pos[i] for i in g] for g in groups]
    best = None
    for combo in itertools.product(*choices):
        y = [0]*len(pos)
        for c in combo:
            if c is not None:
                y[c] = 1
        e = sub_energy(sub, y)
        if best is None or e < best[0]:
            best = (e, y)
    return best


def checked(source, variant, bits):
    full = lift_bits(source, variant, bits)
    result = decode(source, full)
    metrics = result['check']['metrics'] if result['valid'] else None
    return full, result['valid'], metrics


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--incumbent-result', type=Path, required=True)
    p.add_argument('--blocks', required=True, help='Comma-separated one-hot block indices to free')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--allow-external', action='store_true')
    p.add_argument('--max-service-jobs', type=int, default=0, help='Total shared ledger count, including prior attempts')
    p.add_argument('--num-rep', type=int, default=512)
    p.add_argument('--num-steps', type=int, default=2000)
    p.add_argument('--timeout', type=float, default=120)
    a = p.parse_args()
    if a.output.exists():
        p.error('Fresh output directory required')
    source = load_bundle(a.bundle)
    variant = eliminate_idle(source)
    fixed, incumbent = incumbent_start(source, variant, a.incumbent_result)
    blocks = [int(b) for b in a.blocks.split(',')]
    groups = [source['onehot_groups'][b]['program_indices'] for b in blocks]
    sub = subproblem(variant, fixed, [i for g in groups for i in g])
    keep = [fixed[i] for i in sub['free_indices']]
    if sub_energy(sub, keep) != energy(variant, fixed):
        raise AssertionError('Sub-QUBO does not reproduce the incumbent energy')
    exact_e, exact_y = exact_block_optimum(sub, groups)
    if sub_energy(sub, exact_y) != energy(variant, merge(fixed, sub, exact_y)):
        raise AssertionError('Sub-QUBO energy differs from the full sampling energy')
    _, exact_valid, exact_metrics = checked(source, variant, merge(fixed, sub, exact_y))
    a.output.mkdir(parents=True)
    plan = dict(kind='One LNS step: classical incumbent, VeloxQ on freed blocks, exact sub-optimum check',
                source_bundle=str(a.bundle), source_bundle_sha256=source['bundle_sha256'],
                sampling_bundle_sha256=variant['bundle_sha256'], incumbent=incumbent, freed_blocks=blocks,
                sub_bundle_sha256=sub['bundle_sha256'], sub_variables=len(sub['linear']),
                sub_couplers=len(sub['quadratic']), incumbent_sub_energy=str(sub_energy(sub, keep)),
                exact_sub_energy=str(exact_e), exact_plan=dict(valid=exact_valid, metrics=exact_metrics),
                num_rep=a.num_rep, num_steps=a.num_steps, wall_time_limit_s=a.timeout,
                max_service_jobs_total=a.max_service_jobs, allow_external=a.allow_external,
                initializer='cold', repair=False, retries=False, physical_qpu_calls=0)
    save(a.output/'experiment-plan.json', plan)
    save(a.output/'sub-qubo.json', sub)
    from .methods.veloxq import solve_qubo
    result = solve_qubo(sub, dict(allow_external_execution=a.allow_external, max_service_jobs=a.max_service_jobs,
                                  wall_time_limit_s=a.timeout),
                        dict(num_rep=a.num_rep, num_steps=a.num_steps), a.output/'service')
    rows, samples = [], []
    for s in result['samples']:
        if int(s['reported_energy']) != sub_energy(sub, s['bits']):
            raise AssertionError('Returned energy differs from the sub-QUBO energy')
        full, valid, metrics = checked(source, variant, merge(fixed, sub, s['bits']))
        rows.append(dict(count=s['count'], sub_energy=s['reported_energy'], valid=valid, metrics=metrics))
        samples.append(dict(bits=full, count=s['count'], reported_energy=str(energy(source, full))))
    valid = [r for r in rows if r['valid']]
    best = min(valid, key=lambda r: int(r['sub_energy'])) if valid else None
    summary = dict(status=result['status'], failure=result.get('failure'), veloxq_calls=result['veloxq_calls'],
                   returned_shots=sum(r['count'] for r in rows), valid_shots=sum(r['count'] for r in valid),
                   exact_hits=sum(r['count'] for r in rows if int(r['sub_energy']) == exact_e),
                   best=best, incumbent_metrics=incumbent['metrics'], exact_metrics=exact_metrics,
                   reached_exact_sub_optimum=best is not None and int(best['sub_energy']) == exact_e,
                   timings=result['timings'], backend_statistics=result.get('backend_statistics'))
    lifted = method_result(source, 'veloxq_lns_step', samples, timings=result['timings'])
    lifted.update(execution_kind=result['execution_kind'], veloxq_calls=result['veloxq_calls'], status=result['status'],
                  configuration=dict(plan=plan, sub_bundle_sha256=sub['bundle_sha256']))
    save(a.output/'result.json', lifted)
    save(a.output/'evaluation.json', summary)
    print(json.dumps(dict(output=str(a.output), plan={k: plan[k] for k in ('sub_variables', 'sub_couplers',
          'exact_plan', 'incumbent')}, evaluation={k: v for k, v in summary.items() if k != 'backend_statistics'}), indent=2))


if __name__ == '__main__':
    main()
