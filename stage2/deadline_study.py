"""Source-sealed local decision-formulation study; no SDK or network imports."""
import argparse
import hashlib
import json
from pathlib import Path
import time

from .deadline_qubo import DeadlineInfeasible, compile_deadline, query_record
from .deadline_reference import solve_deadline_cp
from .window_qubo import digest


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def run(source, output):
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    names = ['deadline_study.py', 'deadline_qubo.py', 'deadline_reference.py',
             'window_qubo.py', 'window_reduction.py']
    hashes = {}
    for name in names:
        path = root/'stage2'/name
        target = output/'sources'/'stage2'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    queries = [('heat-outage-32', 900), ('heat-lease-32', 900),
               ('heat-lease-32', 855), ('heat-lease-32', 854)]
    protocol = dict(queries=[dict(case=case, cap=cap) for case, cap in queries],
                    source_hashes=hashes, native_cp_seconds=10, native_cp_workers=1,
                    max_variables=12000, max_pair_checks=10_000_000, max_couplers=1_000_000,
                    compiler='Exact unary target filtering plus binary support consistency; no reference teacher',
                    scope='Development study on known recovery inputs; query satisfaction is not soft-objective optimization',
                    veloxq_calls=0, physical_qpu_calls=0)
    inputs = {}
    for case, _ in queries:
        path = source/case/'problem.json'
        inputs[case] = hashlib.sha256(path.read_bytes()).hexdigest()
    protocol['input_file_sha256'] = inputs
    save(output/'protocol.json', protocol)
    rows = []
    began = time.perf_counter()
    for case, cap in queries:
        directory = output/f'{case}-cap-{cap}'
        directory.mkdir()
        problem = json.loads((source/case/'problem.json').read_text())
        save(directory/'problem.json', problem)
        start = time.perf_counter()
        query = query_record(problem, cap)
        try:
            q = compile_deadline(problem, cap)
        except DeadlineInfeasible as error:
            q = None
            model = dict(status='PREPROCESSING_INFEASIBLE', certificate=error.certificate)
        else:
            model = dict(status='COMPILED', **q.metadata())
            save(directory/'qubo.json', dict(linear=q.linear,
                 quadratic=[[i,j,c] for (i,j), c in sorted(q.quadratic.items())],
                 offset=q.offset, variables=q.variables, groups=q.groups, metadata=model))
        compile_seconds = time.perf_counter()-start
        # Native reference receives the original problem, never compiler domains.
        reference = solve_deadline_cp(problem, cap, seconds=10, workers=1)
        assert reference['query_sha256'] == digest(query)
        if reference['target_feasible'] is True:
            if q is None:
                raise AssertionError('Exact preprocessing removed a native feasible query')
            bits = q.encode(reference['plan'])
            assert q.energy(bits) == 0 and q.decode(bits)['valid']
            save(directory/'reference-witness.json', dict(bits=bits, energy=0,
                 provenance='Native CP reporting/audit only; never a sampler initial state'))
        if q is None and reference['target_feasible'] is not False:
            raise AssertionError('Preprocessing certificate not independently confirmed')
        save(directory/'reference.json', reference)
        row = dict(case=case, cap=cap, problem_sha256=digest(problem), query_sha256=digest(query),
                   model=model, compile_seconds=compile_seconds, reference=reference)
        save(directory/'report.json', row)
        rows.append(row)
        print(json.dumps(dict(case=case, cap=cap, variables=model.get('variables'),
             couplers=model.get('couplers'), status=reference['status'],
             target_feasible=reference['target_feasible'])), flush=True)
    assert all(hashlib.sha256((root/'stage2'/n).read_bytes()).hexdigest() == h for n,h in hashes.items())
    report = dict(protocol=protocol, rows=rows, source_stable=True,
                  wall_seconds=time.perf_counter()-began, veloxq_calls=0, physical_qpu_calls=0)
    save(output/'report.json', report)
    save(output/'manifest.json', {str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in output.rglob('*') if p.is_file()})
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('output/manufacturing-recovery-v2'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.output)
