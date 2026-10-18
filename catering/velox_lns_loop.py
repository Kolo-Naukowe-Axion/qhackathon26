"""VeloxQ-driven large-neighbourhood search on a frozen scale QUBO.

Each sweep pairs the one-hot blocks (random matching, or every pair with
--pairing all). For every pair a sub-QUBO keeps
the current program and the best candidates by local field (at most --cap
variables), with everything else fixed. All pair sub-QUBOs of a sweep are
independent blocks of a few sampling QUBOs (at most --batch-max variables per
service job), so each job proposes moves for many pairs at once. Proposals are accepted one at a time only if the exact energy of
the whole plan falls, and every accepted plan is rechecked by the shared
decoder. --solver exact replaces VeloxQ by enumeration as the control.
No repair; offline unless --allow-external.
"""
import argparse
import itertools
import json
import random
import time
from pathlib import Path

from .build_meal_release import save
from .conditioning import eliminate_idle, lift_bits
from .contracts import load_bundle, method_result
from .decode import decode
from .domain import digest
from .methods.veloxq import DEFAULT_LEDGER, solve_qubo
from .qubo import energy
from .velox_lns import exact_block_optimum, merge, sub_energy, subproblem
from .veloxq_pilot import incumbent_start


def neighbours(variant):
    adj = [dict() for _ in variant['linear']]
    for t in variant['quadratic']:
        v = int(t['value'])
        adj[t['i']][t['j']] = adj[t['i']].get(t['j'], 0)+v
        adj[t['j']][t['i']] = adj[t['j']].get(t['i'], 0)+v
    return adj


def candidates(variant, adj, x, block, per_block):
    """Current program plus the best switches by exact single-block energy change."""
    current = [i for i in block if x[i]]
    base = [0 if i in block else b for i, b in enumerate(x)] if current else x
    field = lambda i: int(variant['linear'][i])+sum(v for j, v in adj[i].items() if base[j])
    ranked = sorted((i for i in block if i not in current), key=lambda i: (field(i), i))
    return sorted(current+ranked[:max(0, per_block-len(current))])


def pair_optimum(sub, groups):
    """Vectorized exact none-or-one choice for two freed blocks; same set as exact_block_optimum."""
    import numpy as np
    if len(groups) != 2:
        return exact_block_optimum(sub, groups)
    pos = {i: k for k, i in enumerate(sub['free_indices'])}
    a, b = ([None]+[pos[i] for i in g] for g in groups)
    lin = {k: int(c) for k, c in enumerate(sub['linear'])}
    quad = {(t['i'], t['j']): int(t['value']) for t in sub['quadratic']}
    la = np.array([0 if i is None else lin[i] for i in a], dtype=object)
    lb = np.array([0 if j is None else lin[j] for j in b], dtype=object)
    cross = np.array([[0 if i is None or j is None else quad.get((min(i, j), max(i, j)), 0) for j in b] for i in a], dtype=object)
    e = int(sub['constant'])+la[:, None]+lb[None, :]+cross
    ia, ib = divmod(int(np.argmin(e.astype(float))), len(b))
    # Recheck the float-located minimum exactly among ties.
    best = min(((e[i, j], i, j) for i in range(len(a)) for j in range(len(b)) if e[i, j] <= e[ia, ib]), key=lambda t: t[0])
    y = [0]*len(pos)
    for c in (a[best[1]], b[best[2]]):
        if c is not None:
            y[c] = 1
    if sub_energy(sub, y) != best[0]:
        raise AssertionError('Pair enumeration energy mismatch')
    return best[0], y


def combine(subs):
    """Independent sub-QUBOs as disjoint blocks of one sampling QUBO."""
    order, linear, quadratic, constant, offsets = [], [], [], 0, []
    for k, s in enumerate(subs):
        offsets.append(len(order))
        order += [f'pair{k}:{v}' for v in s['variable_order']]
        linear += s['linear']
        constant += int(s['constant'])
        quadratic += [dict(i=t['i']+offsets[-1], j=t['j']+offsets[-1], value=t['value']) for t in s['quadratic']]
    batch = dict(kind='lns-sweep-batch.v1', variable_order=order, linear=linear, quadratic=quadratic,
                 constant=str(constant), sub_bundle_sha256=[s['bundle_sha256'] for s in subs])
    batch['bundle_sha256'] = digest(batch)
    return batch, offsets


def ledger_count():
    return len(json.loads(Path(DEFAULT_LEDGER).read_text())['jobs'])


def sweep(source, variant, adj, x, rng, cap, solver, output, budget, pairing='random', batch_max=2000, pause=0):
    blocks = [g['program_indices'] for g in source['onehot_groups']]
    if pairing == 'all':
        pairs = [list(p) for p in itertools.combinations(range(len(blocks)), 2)]
    else:
        order = list(range(len(blocks)))
        rng.shuffle(order)
        pairs = [order[k:k+2] for k in range(0, len(order)-1, 2)]
    subs, groups = [], []
    for pair in pairs:
        per = max(1, cap//len(pair))
        chosen = [candidates(variant, adj, x, blocks[b], per) for b in pair]
        subs.append(subproblem(variant, x, [i for c in chosen for i in c]))
        groups.append(chosen)
    keep = [[x[i] for i in s['free_indices']] for s in subs]
    exact = [pair_optimum(s, g) for s, g in zip(subs, groups)]
    proposals = [dict(pair=p, variables=len(s['linear']), incumbent=sub_energy(s, k), exact=e[0])
                 for p, s, k, e in zip(pairs, subs, keep, exact)]
    services = []
    if solver == 'exact':
        best = [e[1] for e in exact]
    else:
        # Independent pair sub-QUBOs share a job until it reaches batch_max variables.
        chunks, current = [], []
        for k, s in enumerate(subs):
            if current and sum(len(subs[c]['linear']) for c in current)+len(s['linear']) > batch_max:
                chunks.append(current)
                current = []
            current.append(k)
        chunks.append(current)
        best = [None]*len(subs)
        for n, chunk in enumerate(chunks):
            batch, offsets = combine([subs[k] for k in chunk])
            out = output/f'job-{n:02d}'
            save(output/f'job-{n:02d}-qubo.json', batch)
            if n and pause:
                time.sleep(pause)  # spacing between submissions, not a retry
            job_budget = dict(budget, max_service_jobs=min(budget['max_service_jobs'], ledger_count()+1))
            result = solve_qubo(batch, job_budget, dict(num_rep=budget['num_rep'], num_steps=budget['num_steps']), out)
            services.append(dict(status=result['status'], failure=result.get('failure'), job_id=result['raw_artifacts'].get('job_id'),
                                 backend_running_s=(result.get('backend_statistics') or {}).get('running_time'),
                                 total_s=result['timings'].get('total_s'), variables=len(batch['linear']), pairs=len(chunk)))
            if result['status'] != 'completed':
                break  # pairs of this and later jobs keep the current plan
            for sample in result['samples']:
                for k, off in zip(chunk, offsets):
                    y = sample['bits'][off:off+len(subs[k]['linear'])]
                    if best[k] is None or sub_energy(subs[k], y) < sub_energy(subs[k], best[k]):
                        best[k] = y
    for k, s in enumerate(subs):
        if best[k] is None:
            best[k] = keep[k]
            proposals[k]['no_service_result'] = True
    for prop, s, y in zip(proposals, subs, best):
        prop['found'] = sub_energy(s, y)
        prop['hit_exact'] = prop['found'] == prop['exact']
    accepted = []
    current = energy(variant, x)
    for k in sorted(range(len(subs)), key=lambda k: proposals[k]['found']-proposals[k]['incumbent']):
        if proposals[k]['found'] >= proposals[k]['incumbent']:
            continue
        trial = merge(x, subs[k], best[k])
        e = energy(variant, trial)
        if e < current and decode(source, lift_bits(source, variant, trial))['valid']:
            x, current = trial, e
            accepted.append(dict(pair=proposals[k]['pair'], energy=e))
    return x, proposals, services, accepted


def metrics(source, variant, x):
    checked = decode(source, lift_bits(source, variant, x))
    if not checked['valid']:
        raise AssertionError('Accepted plan failed the shared checker')
    return {k: checked['check']['metrics'][k] for k in 'UWBR'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--incumbent-result', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--solver', choices=['veloxq', 'exact'], default='veloxq')
    p.add_argument('--cap', type=int, default=60, help='Maximum freed variables per block pair')
    p.add_argument('--seed', type=int, default=2026)
    p.add_argument('--pairing', choices=['random', 'all'], default='random')
    p.add_argument('--pause', type=float, default=0, help='Seconds between service submissions')
    p.add_argument('--batch-max', type=int, default=2000, help='Maximum variables in one service job')
    p.add_argument('--max-sweeps', type=int, default=12)
    p.add_argument('--patience', type=int, default=2)
    p.add_argument('--allow-external', action='store_true')
    p.add_argument('--max-service-jobs', type=int, default=0, help='Total shared ledger cap, including prior attempts')
    p.add_argument('--num-rep', type=int, default=512)
    p.add_argument('--num-steps', type=int, default=2000)
    p.add_argument('--timeout', type=float, default=120)
    a = p.parse_args()
    if a.output.exists():
        p.error('Fresh output directory required')
    source = load_bundle(a.bundle)
    variant = eliminate_idle(source)
    adj = neighbours(variant)
    x, incumbent = incumbent_start(source, variant, a.incumbent_result)
    rng = random.Random(a.seed)
    a.output.mkdir(parents=True)
    plan = dict(kind='VeloxQ-LNS loop' if a.solver == 'veloxq' else 'Exact-enumeration LNS control',
                source_bundle=str(a.bundle), source_bundle_sha256=source['bundle_sha256'],
                sampling_bundle_sha256=variant['bundle_sha256'], incumbent=incumbent, solver=a.solver, cap=a.cap,
                seed=a.seed, pause_s=a.pause, pairing=a.pairing, batch_max=a.batch_max, max_sweeps=a.max_sweeps, patience=a.patience, num_rep=a.num_rep, num_steps=a.num_steps,
                max_service_jobs_total=a.max_service_jobs, allow_external=a.allow_external,
                acceptance='sequential, exact full energy must fall, shared decoder must pass', repair=False)
    save(a.output/'experiment-plan.json', plan)
    history = [dict(sweep=0, metrics=metrics(source, variant, x), energy=energy(variant, x))]
    quiet = 0
    for k in range(1, a.max_sweeps+1):
        budget = dict(allow_external_execution=a.allow_external, wall_time_limit_s=a.timeout,
                      max_service_jobs=a.max_service_jobs, num_rep=a.num_rep, num_steps=a.num_steps)
        if a.solver == 'veloxq' and ledger_count() >= a.max_service_jobs:
            history.append(dict(sweep=k, stopped='service cap reached'))
            break
        out = a.output/f'sweep-{k:02d}'
        out.mkdir()
        x, proposals, services, accepted = sweep(source, variant, adj, x, rng, a.cap, a.solver, out, budget,
                                                 a.pairing, a.batch_max, a.pause)
        row = dict(sweep=k, metrics=metrics(source, variant, x), energy=energy(variant, x), accepted=accepted,
                   services=services, subproblems=len(proposals),
                   exact_hits=sum(p.get('hit_exact', False) for p in proposals),
                   improvable=sum(p['exact'] < p['incumbent'] for p in proposals))
        save(out/'sweep.json', dict(row, proposals=proposals))
        history.append(row)
        print(json.dumps({k2: row[k2] for k2 in ('sweep', 'metrics', 'exact_hits', 'improvable', 'subproblems')}
                         | dict(accepted=len(accepted), jobs=len(services))), flush=True)
        quiet = 0 if accepted else quiet+1
        if quiet >= a.patience:
            break
    full = lift_bits(source, variant, x)
    final = method_result(source, 'veloxq_lns_loop' if a.solver == 'veloxq' else 'exact_lns_loop',
                          [dict(bits=full, count=1, reported_energy=str(energy(source, full)))])
    final.update(configuration=dict(plan=plan), veloxq_calls=sum(len(h.get('services') or []) for h in history))
    save(a.output/'result.json', final)
    save(a.output/'history.json', history)
    print(json.dumps(dict(start=incumbent['metrics'], final=history[-1].get('metrics', history[-2]['metrics']),
                          sweeps=len(history)-1, veloxq_jobs=final['veloxq_calls'])))


if __name__ == '__main__':
    main()
