"""Audited cold offline packets for three manufacturing representations; no API."""
import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import time

from .deadline_qubo import DeadlineQUBO
from .operation_qubo import compile_operations
from .manufacturing_penalty import tighten
from .window_qubo import WindowQUBO, check_plan, digest


def ising4(linear, quadratic, offset):
    """4*Q(x)=C+sum(h*s)+sum(J*s*s), with s=2*x-1."""
    fields = [2 * value for value in linear]
    for (i, j), value in quadratic.items():
        fields[i] += value
        fields[j] += value
    return fields, dict(quadratic), 4 * offset + 2 * sum(linear) + sum(quadratic.values())


def verify_inverse(linear, quadratic, offset, fields, edges, constant):
    if len(fields) != len(linear) or edges != quadratic:
        raise AssertionError('Ising labels/edges differ from QUBO')
    recovered = list(fields)
    for (i, j), value in edges.items():
        recovered[i] -= value
        recovered[j] -= value
    if recovered != [2 * value for value in linear]:
        raise AssertionError('Inverse Ising substitution changed a linear coefficient')
    if constant - 2 * sum(linear) - sum(edges.values()) != 4 * offset:
        raise AssertionError('Inverse Ising substitution changed the constant')
    return dict(coefficients_checked=len(linear) + len(quadratic) + 1,
                all_state_coefficient_identity=True,
                proof='Inverse substitution recovers every original linear/quadratic coefficient and constant exactly; therefore equality holds for every bitstring')


def audit_hdf5(path, model):
    import h5py
    import numpy as np

    fields, edges, constant = ising4(model.linear, model.quadratic, model.offset)
    with h5py.File(path, 'r') as file:
        if set(file) != {'Ising'}:
            raise AssertionError('Cold packet must contain only Ising, no witness states')
        group = file['Ising']
        labels = [int(value.decode() if isinstance(value, bytes) else value) for value in group['labels'][:]]
        if labels != list(range(len(model.linear))) or group.attrs['var_type'] != 'SPIN':
            raise AssertionError('SDK label or variable convention changed')
        actual_fields = [int(value) for value in group['biases'][:]]
        if any(int(value) != value for value in group['biases'][:]):
            raise AssertionError('Nonintegral field value')
        couplings = group['couplings']
        if isinstance(couplings, h5py.Group):
            directed = {(int(i) - 1, int(j) - 1): int(value)
                for i, j, value in zip(couplings['I'][:], couplings['J'][:], couplings['V'][:])}
            if any(directed.get((j, i)) != value for (i, j), value in directed.items()):
                raise AssertionError('Sparse Ising coupling symmetry changed')
            actual_edges = {pair: value for pair, value in directed.items() if pair[0] < pair[1]}
        else:
            dense = couplings[:]
            if not np.array_equal(dense, dense.T):
                raise AssertionError('Dense Ising coupling symmetry changed')
            actual_edges = {(int(i), int(j)): int(dense[i, j]) for i, j in zip(*np.triu(dense, 1).nonzero())}
        actual_constant = int(group.attrs['offset'])
        if actual_constant != group.attrs['offset']:
            raise AssertionError('Offset was rounded')
        checked = verify_inverse(model.linear, model.quadratic, model.offset,
                                 actual_fields, actual_edges, actual_constant)
        if actual_fields != fields or actual_edges != edges or actual_constant != constant:
            raise AssertionError('SDK serialization changed the exact Hamiltonian')
        rng = random.Random(31017)
        states = [[0] * len(fields), [1] * len(fields)] + [
            [rng.randrange(2) for _ in fields] for _ in range(4)]
        for bits in states:
            spins = [2 * bit - 1 for bit in bits]
            energy = actual_constant + sum(h * spin for h, spin in zip(actual_fields, spins)) + sum(
                value * spins[i] * spins[j] for (i, j), value in actual_edges.items())
            if energy != 4 * model.energy(bits):
                raise AssertionError('Serialized Ising energy mismatch')
        return dict(checked, labels_exact=True, offset_exact=True, spin_convention='s=2x-1',
                    hdf5_energy_scale=4, checked_bitstrings=len(states),
                    bias_dtype=str(group['biases'].dtype), cold_only=True)


def load_models():
    deadline_path = Path('output/deadline-decision-review-v1/heat-lease-32-cap-900')
    problem = json.loads((deadline_path / 'problem.json').read_text())
    raw = json.loads((deadline_path / 'qubo.json').read_text())
    meta = raw['metadata']
    deadline = DeadlineQUBO(problem, meta['query'], raw['variables'], raw['groups'], raw['linear'],
        {(i, j): value for i, j, value in raw['quadratic']}, raw['offset'], meta['reduction'], meta['incompatible_pairs'])
    enriched_path = Path('output/capacity-frontier-review-v1/heat-lease-32')
    enriched_problem = json.loads((enriched_path / 'problem.json').read_text())
    columns = json.loads((enriched_path / 'cap-64/columns.json').read_text())
    enriched = compile_operations(enriched_problem, columns)
    complete_path = Path('output/manufacturing-full-recovery-v1/heat-lease-32')
    complete_problem = json.loads((complete_path / 'problem.json').read_text())
    raw = json.loads((complete_path / 'qubo.json').read_text())
    meta = raw['metadata']
    complete = WindowQUBO(complete_problem, raw['variables'], raw['groups'], raw['linear'],
        {(i, j): value for i, j, value in raw['quadratic']}, raw['offset'], meta['penalty'], meta['feasible_objective_upper_bound'], {})
    if len(deadline.linear) != 818 or len(enriched.linear) != 2078 or len(complete.linear) != 2499:
        raise AssertionError('Expected source representation identity changed')
    if len({digest(model.problem) for model in [deadline, enriched, complete]}) != 1:
        raise AssertionError('Packets must describe the same raw recovery input')
    return [('deadline-818', deadline), ('enriched-2078', enriched), ('complete-2499', complete)]


def run(output):
    # Empty before SDK import. Do not read, request, restore or use a token.
    os.environ['VELOX_TOKEN'] = ''
    import importlib.metadata
    from veloxq_sdk.api.problems import File

    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    names = ['sponsor_merit_packets.py', 'deadline_qubo.py', 'operation_qubo.py',
             'column_qubo.py', 'trajectory_qubo.py', 'window_qubo.py']
    hashes = {}
    for name in names:
        path = root / 'stage2' / name
        target = output / 'sources' / 'stage2' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    inputs = [Path(path) for path in [
        'output/deadline-decision-review-v1/heat-lease-32-cap-900/problem.json',
        'output/deadline-decision-review-v1/heat-lease-32-cap-900/qubo.json',
        'output/capacity-frontier-review-v1/heat-lease-32/problem.json',
        'output/capacity-frontier-review-v1/heat-lease-32/cap-64/columns.json',
        'output/manufacturing-full-recovery-v1/heat-lease-32/problem.json',
        'output/manufacturing-full-recovery-v1/heat-lease-32/qubo.json']]
    protocol = dict(schema='qfactoria-sponsor-merit-offline-packets.v1',
        source_hashes=hashes, input_sha256={str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs},
        representations=['deadline-818', 'enriched-2078', 'complete-2499'], cold_only=True,
        sdk_version=importlib.metadata.version('veloxq-sdk'), sdk_token_environment='Forced empty before SDK import; prior value never read',
        landscape='Deadline is a different exact decision query; enriched is a lossy nested cap64 pool; complete preserves full declared optimization domain',
        penalty='Deadline unit1; enriched original compiler bound; complete retained incumbent-tightened bound. Distinct infeasible-state energies explicitly retained.',
        service_acceptance=False, veloxq_calls=0, physical_qpu_calls=0)
    (output / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    start = time.perf_counter()
    rows = []
    for name, model in load_models():
        directory = output / name
        directory.mkdir()
        (directory / 'problem.json').write_text(json.dumps(model.problem, indent=2) + '\n')
        (directory / 'decoder.json').write_text(json.dumps(dict(variables=model.variables, groups=model.groups,
            columns=getattr(model, 'columns', None), query=getattr(model, 'query', None)), indent=2) + '\n')
        fields, edges, constant = ising4(model.linear, model.quadratic, model.offset)
        path = directory / 'cold.h5'
        File._write_ising_hdf5(path, dict(enumerate(fields)), edges, offset=int(constant), init_state=None)
        audit = audit_hdf5(path, model)
        absolute = [abs(value) for value in [*fields, *edges.values()] if value]
        row = dict(case=name, variables=len(model.linear), couplers=len(edges), penalty=model.penalty,
            problem_sha256=digest(model.problem), file=str(path.relative_to(output)), file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            bytes=path.stat().st_size, min_abs_ising_coefficient=min(absolute), max_abs_ising_coefficient=max(absolute),
            ising_dynamic_range=max(absolute) / min(absolute), ising_offset=constant, audit=audit,
            service_acceptance=False, warm_start=False)
        (directory / 'receipt.json').write_text(json.dumps(row, indent=2) + '\n')
        rows.append(row)
        print(json.dumps(dict(case=name, variables=len(model.linear), couplers=len(edges), audited=True)), flush=True)
    stable = all(hashlib.sha256((root / 'stage2' / name).read_bytes()).hexdigest() == expected for name, expected in hashes.items())
    if not stable:
        raise AssertionError('Packet source changed')
    report = dict(protocol=protocol, rows=rows, source_stable=stable, wall_seconds=time.perf_counter() - start,
                  veloxq_calls=0, physical_qpu_calls=0)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (output / 'manifest.json').write_text(json.dumps({str(path.relative_to(output)):
        hashlib.sha256(path.read_bytes()).hexdigest() for path in output.rglob('*') if path.is_file()}, indent=2) + '\n')
    return report


def run_matched_enriched(output):
    """Supplement the retained original-bound pool with its matched safe penalty."""
    os.environ['VELOX_TOKEN'] = ''
    import importlib.metadata
    from veloxq_sdk.api.problems import File

    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    names = ['sponsor_merit_packets.py', 'manufacturing_penalty.py', 'deadline_qubo.py',
             'operation_qubo.py', 'column_qubo.py', 'trajectory_qubo.py', 'window_qubo.py']
    hashes = {}
    for name in names:
        source = root / 'stage2' / name
        target = output / 'sources' / 'stage2' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        hashes[name] = hashlib.sha256(source.read_bytes()).hexdigest()
    parents_path = Path('output/manufacturing-recovery-v2/heat-lease-32/parents.json')
    protocol = dict(schema='qfactoria-matched-enriched-penalty-packet.v1', source_hashes=hashes,
        heuristic_parents=str(parents_path), heuristic_parents_sha256=hashlib.sha256(parents_path.read_bytes()).hexdigest(),
        prior_packet='output/sponsor-merit-packets-v1/enriched-2078/cold.h5',
        matched_complete_packet='output/sponsor-merit-packets-v1/complete-2499/cold.h5',
        sdk_version=importlib.metadata.version('veloxq-sdk'),
        initialization='Cold HDF5 with no Spectrum; heuristic witness certifies penalty only',
        solver_calls=0, veloxq_calls=0, physical_qpu_calls=0,
        landscape='Feasible objectives and global minima preserved; invalid-state energies change. Both enriched penalty variants retained; no empirical performance prediction.')
    (output / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    models = dict(load_models())
    enriched = models['enriched-2078']
    parents = json.loads(parents_path.read_text())
    if parents.get('cp_teacher_used') is not False:
        raise AssertionError('Penalty witness provenance is not pre-CP heuristic')
    best = min(parents['parents'], key=lambda plan: check_plan(enriched.problem, plan)['objective'])
    tightened, bits, certificate = tighten(enriched, best, 'Saved original pre-CP list heuristic; retained by nested pool; used for penalty proof only')
    if tightened.penalty != models['complete-2499'].penalty:
        raise AssertionError('Enriched and complete penalties do not match')
    fields, edges, constant = ising4(tightened.linear, tightened.quadratic, tightened.offset)
    path = output / 'cold.h5'
    File._write_ising_hdf5(path, dict(enumerate(fields)), edges, offset=int(constant), init_state=None)
    audited = audit_hdf5(path, tightened)
    (output / 'problem.json').write_text(json.dumps(tightened.problem, indent=2) + '\n')
    (output / 'columns.json').write_text(json.dumps(tightened.columns, indent=2) + '\n')
    (output / 'qubo.json').write_text(json.dumps(dict(linear=tightened.linear,
        quadratic=[(i, j, value) for (i, j), value in sorted(tightened.quadratic.items())],
        offset=tightened.offset, variables=tightened.variables, groups=tightened.groups,
        metadata=dict(tightened.metadata(), penalty_certificate=certificate)), indent=2) + '\n')
    (output / 'heuristic-penalty-witness.json').write_text(json.dumps(dict(plan=best,
        bits=bits, energy=tightened.energy(bits), check=check_plan(tightened.problem, best),
        source='Original pre-CP heuristic; not a cold sampler input'), indent=2) + '\n')
    absolute = [abs(value) for value in [*fields, *edges.values()] if value]
    stable = all(hashlib.sha256((root / 'stage2' / name).read_bytes()).hexdigest() == expected for name, expected in hashes.items())
    if not stable:
        raise AssertionError('Matched packet source changed')
    report = dict(protocol=protocol, source_stable=stable, variables=len(fields), couplers=len(edges),
        penalty=tightened.penalty, penalty_certificate=certificate,
        problem_sha256=digest(tightened.problem), file='cold.h5', bytes=path.stat().st_size,
        file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        min_abs_ising_coefficient=min(absolute), max_abs_ising_coefficient=max(absolute),
        ising_dynamic_range=max(absolute) / min(absolute), audit=audited,
        service_acceptance=False, veloxq_calls=0, physical_qpu_calls=0)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (output / 'manifest.json').write_text(json.dumps({str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in output.rglob('*') if path.is_file()}, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--matched-enriched', action='store_true')
    args = parser.parse_args()
    run_matched_enriched(args.output) if args.matched_enriched else run(args.output)
