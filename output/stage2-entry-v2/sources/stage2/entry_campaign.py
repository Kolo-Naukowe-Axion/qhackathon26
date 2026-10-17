"""Reproducible local entry-core campaign; never calls remote services.

TRAIN-only parameter selection precedes the declared fresh TEST seed list.
Prior frozen factory cohorts are not changed or pooled with these results.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import resource
import sys
import time

from .assignment_qaoa import AssignmentSector, sample
from .entry_core import entry_cases, recovery_cell
from .window_qubo import compile_qubo, digest, solve_cp


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def packet(q):
    fields = [v / 2 for v in q.linear]
    offset = q.offset + sum(q.linear) / 2
    couplings = []
    for (i, j), coefficient in sorted(q.quadratic.items()):
        fields[i] += coefficient / 4
        fields[j] += coefficient / 4
        offset += coefficient / 4
        couplings.append([i, j, coefficient / 4])
    # Deterministic local energy equivalence, including the offset and label map.
    import random
    rng = random.Random(20261017)
    for _ in range(64):
        bits = [rng.randrange(2) for _ in fields]
        spins = [2 * b - 1 for b in bits]
        energy = offset + sum(h * s for h, s in zip(fields, spins)) + sum(
            j * spins[a] * spins[b] for a, b, j in couplings)
        if energy != q.energy(bits):
            raise AssertionError('Offline Ising conversion changed an energy')
    return dict(schema='qfactoria-offline-ising-packet.v1', vartype='SPIN',
                biases=fields, couplings=couplings, offset=offset,
                labels=list(range(len(fields))), problem_sha256=digest(q.problem),
                qubo_sha256=digest(dict(linear=q.linear, quadratic=[[i,j,v]for(i,j),v in sorted(q.quadratic.items())],offset=q.offset)),
                energy_roundtrip_states=64, remote_calls=0,
                status='Prepared offline; backend access, quotas and runtime unverified')


def source_snapshot(output):
    root = Path(__file__).resolve().parents[1]
    names = ['stage2/assignment_qaoa.py', 'stage2/entry_core.py',
             'stage2/entry_campaign.py', 'stage2/window_qubo.py',
             'stage2/window_reduction.py', 'stage2/__init__.py']
    hashes = {}
    for name in names:
        data = (root / name).read_bytes()
        target = output / 'sources' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    return root, hashes


def build_case(problem, directory):
    directory.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    raw = compile_qubo(problem, support_pruning=False)
    q = compile_qubo(problem, support_pruning=True)
    compiler_seconds = time.perf_counter() - start
    start = time.perf_counter()
    sector = AssignmentSector.build(q)
    simulation_preparation = time.perf_counter() - start
    reference = solve_cp(problem, seconds=10, workers=1)
    if not reference.get('optimal') or reference['objective'] != int(sector.energies.min()):
        raise AssertionError('Native raw CP does not certify the sector ground energy')
    save(directory / 'problem.json', problem)
    save(directory / 'qubo.json', dict(linear=q.linear,
         quadratic=[[i,j,v] for (i,j),v in sorted(q.quadratic.items())],
         offset=q.offset, variables=q.variables, groups=q.groups, metadata=q.metadata()))
    save(directory / 'offline-veloxq-ising.json', packet(q))
    save(directory / 'reference.json', reference)
    metadata = dict(raw_variables=len(raw.linear), raw_couplers=len(raw.quadratic),
                    pruned_variables=len(q.linear), pruned_couplers=len(q.quadratic),
                    sector_states=len(sector.energies), raw_groups=raw.metadata()['one_hot_groups'],
                    pruned_groups=q.metadata()['one_hot_groups'], compiler_seconds=compiler_seconds,
                    classical_statevector_preparation_seconds=simulation_preparation,
                    classical_preprocessing_scope='Safe unary/support pruning; no CP optimum or schedule enters compiler or initial state.',
                    simulation_scope='Exponential exact diagonal/sector preparation; not scalable quantum compilation or a logical-qubit reduction.')
    save(directory / 'model.json', metadata)
    return sector, reference, metadata


def compact(row):
    return {k:v for k,v in row.items() if k not in ('qasm','observed_counts','bits','decoded')}


def run(output, quick=False, seed=101):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    began, cpu = time.perf_counter(), time.process_time()
    root, sources = source_snapshot(output)
    train = [7,13,29]
    tests = [101,103,107,109,113,127,131,137,139,149]
    configurations = [dict(layers=1,alpha=1.0),dict(layers=2,alpha=1.0),dict(layers=2,alpha=.25)]
    protocol = dict(schema='qfactoria-entry-core-protocol.v1', train_seeds=train,
                    test_seeds=[seed] if quick else tests, configurations=configurations,
                    selection='Minimum aggregate TRAIN sampled-energy excess, then fewer layers, then expectation before CVaR.',
                    shots=8192, angle_evaluations=128, sa_replicas=32, sa_sweeps=256,
                    reference='Independent native interval CP-SAT, one worker, 10s cap; source separate from QUBO compiler.',
                    source_hashes=sources, quick=quick,
                    methods=['qaoa_xy','uniform_onehot','sa_onehot'],
                    budgets='All use the same full assignment domain. Budgets differ: quantum uses 128 exact simulated objective evaluations plus 8192 Born samples; uniform uses 8192 samples; SA uses 8192 proposals and returns 32 replica bests. No equal-compute or runtime-advantage claim.',
                    physical_qpu_calls=0, veloxq_calls=0,
                    status='Declared before TRAIN/TEST outcomes')
    save(output / 'protocol.json', protocol)
    models = {}
    problems = {'nominal-180':entry_cases()['nominal-180']} if quick else entry_cases()
    for name, problem in problems.items():
        models[name] = build_case(problem, output / name)
    training = []
    if quick:
        selected = dict(layers=2,alpha=1.0)
    else:
        for setting in configurations:
            excess = 0
            for name, (sector, reference, _) in models.items():
                for train_seed in train:
                    row = sample(sector, seed=train_seed, **setting, shots=8192, evaluations=128)
                    excess += row['energy'] - reference['objective']
                    label = f'train-p{setting["layers"]}-a{setting["alpha"]}-{train_seed}'
                    save(output/name/(label+'.json'),row)
            training.append(dict(**setting, aggregate_energy_excess=excess))
            print(json.dumps(dict(phase='train',**training[-1])),flush=True)
        selected = min(training,key=lambda r:(r['aggregate_energy_excess'],r['layers'],-r['alpha']))
        selected = {k:selected[k] for k in ('layers','alpha')}
    # This file is written before any TEST outcomes are generated or read.
    save(output / 'selection.json', dict(selected=selected, training=training,
         rule=protocol['selection'], test_results_used=False, source_hashes=sources))
    rows = []
    for name, (sector, reference, metadata) in models.items():
        case_rows = []
        for test_seed in protocol['test_seeds']:
            for method in protocol['methods']:
                row = sample(sector, method=method, seed=test_seed, **selected,
                             shots=8192,evaluations=128,sweeps=256)
                save(output/name/f'test-{method}-{test_seed}.json',row)
                if row.get('qasm'):
                    (output/name/f'test-{method}-{test_seed}.qasm').write_text(row['qasm'])
                out = dict(case=name, **compact(row), reference_objective=reference['objective'],
                           valid=row['decoded']['valid'], decoded_objective=row['decoded'].get('objective'),
                           weighted_terminal_tardiness=row['decoded'].get('weighted_terminal_tardiness'),
                           makespan=row['decoded'].get('makespan'),
                           encoded_energy_gap=row['energy']-reference['objective'],
                           decoded_objective_gap=row['decoded'].get('objective',reference['objective'])-reference['objective'] if row['decoded']['valid'] else None)
                case_rows.append(out)
                rows.append(out)
        save(output/name/'results.json',dict(model=metadata,reference=reference,rows=case_rows))
        print(json.dumps(dict(phase='test',case=name,valid=sum(r['valid']for r in case_rows),
                              runs=len(case_rows),quantum_optimal=sum(r['encoded_energy_gap']==0 for r in case_rows if r['method']=='qaoa_xy'))),flush=True)
    scaling = []
    if not quick:
        for pumps in [1,2,3,4]:
            p = recovery_cell(horizon=180+120*(pumps-1),pumps=pumps)
            t = time.perf_counter()
            q = compile_qubo(p,max_variables=10000,support_pruning=True)
            elapsed = time.perf_counter()-t
            ref = solve_cp(p,seconds=10,workers=1)
            scaling.append(dict(pumps=pumps,operations=len(p['operations']),horizon=p['horizon'],
                                variables=len(q.linear),couplers=len(q.quadratic),build_seconds=elapsed,
                                problem_sha256=digest(p),reference=ref,quantum_executed=False,
                                offline_packet_roundtrip_states=packet(q)['energy_roundtrip_states']))
    save(output/'scaling.json',scaling)
    stable = all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in sources.items())
    if not stable:
        raise AssertionError('Sources changed during campaign')
    summary = dict(schema='qfactoria-entry-core-results.v1',protocol=protocol,selection=selected,
                   rows=rows,scaling=scaling,sources_stable=True,wall_seconds=time.perf_counter()-began,
                   process_cpu_seconds=time.process_time()-cpu,
                   peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin'else 1024),
                   python=platform.python_version(),numpy=importlib.metadata.version('numpy'),
                   ortools=importlib.metadata.version('ortools'),physical_qpu_calls=0,veloxq_calls=0,
                   scope='New complete synthetic manufacturing recovery model; separate from frozen full-factory evidence. No quantum speedup or physical QPU claim.')
    save(output/'report.json',summary)
    files={str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
           for p in sorted(output.rglob('*')) if p.is_file()}
    save(output/'manifest.json',files)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--quick',action='store_true')
    parser.add_argument('--seed',type=int,default=101)
    args=parser.parse_args()
    report=run(args.output,args.quick,args.seed)
    print(json.dumps(dict(output=str(args.output),runs=len(report['rows']),
                          wall_seconds=report['wall_seconds'],sources_stable=report['sources_stable']),indent=2))
