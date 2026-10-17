"""Structural boundary-release gate on a saved full-recipe deadline query."""
import argparse
from copy import deepcopy
import hashlib
import itertools
import json
import math
from pathlib import Path
import time

from .deadline_qubo import compile_deadline
from .window_qubo import check_plan, digest


def graph_of(q):
    graph = [set() for _ in q.linear]
    for (i, j), value in q.quadratic.items():
        if value == 1:
            graph[i].add(j)
            graph[j].add(i)
    return graph


def boundary_domains(q, parent, free, graph):
    """Exact outside-occupation filtering, then free-domain arc consistency."""
    fixed = {name: next(i for i in group if q.variables[i] == parent[name])
             for name, group in q.groups.items() if name not in free}
    occupied = set(fixed.values())
    domains = {name: [i for i in q.groups[name] if not graph[i] & occupied]
               for name in sorted(free)}
    if any(not values for values in domains.values()):
        return domains, fixed
    changed = True
    while changed:
        changed = False
        masks = {name: set(rows) for name, rows in domains.items()}
        for a in sorted(domains):
            alive = [i for i in domains[a] if all(masks[b] - graph[i] for b in domains if a != b)]
            if alive != domains[a]:
                changed = True
                domains[a] = alive
                if not alive:
                    return domains, fixed
    return domains, fixed


def structural_ladder(q, plan, max_free=12):
    """No reference/energy minimizer: release by arc-support deficit only."""
    parent = {r['operation']: r for r in plan}
    graph = graph_of(q)
    free = {name for name, group in q.groups.items()
            if not any(q.variables[i] == parent[name] for i in group)}
    rows = []
    while len(free) <= max_free:
        domains, fixed = boundary_domains(q, parent, free, graph)
        counts = {name: len(values) for name, values in domains.items()}
        rows.append(dict(free=sorted(free), counts=counts, logical_qubits=sum(counts.values()),
                         sector_states=math.prod(counts.values()), arc_consistent=all(counts.values()),
                         domains=domains, fixed=fixed))
        if all(counts.values()) or len(free) == max_free:
            break
        candidates = []
        for release in sorted(set(q.groups) - free):
            trial, _ = boundary_domains(q, parent, free | {release}, graph)
            # Prefer surviving mandatory groups, then retained support, then ID.
            score = (sum(not trial[name] for name in free),
                     -sum(len(trial[name]) for name in free), release)
            candidates.append((score, release))
        if not candidates:
            break
        free.add(min(candidates)[1])
    return rows


class ConditionedQuery:
    penalty = 1

    def __init__(self, parent, domains, fixed):
        self.parent = parent
        old = [i for name in sorted(domains) for i in domains[name]]
        self.old = old
        self.fixed = set(fixed.values())
        mapping = {i: k for k, i in enumerate(old)}
        self.variables = [parent.variables[i] for i in old]
        self.groups = {name: [mapping[i] for i in domains[name]] for name in sorted(domains)}
        self.linear = [parent.linear[i] for i in old]
        self.quadratic = {}
        self.offset = parent.offset + sum(parent.linear[i] for i in self.fixed)
        for (i, j), value in parent.quadratic.items():
            if i in mapping and j in mapping:
                self.quadratic[mapping[i], mapping[j]] = value
            elif i in mapping and j in self.fixed:
                self.linear[mapping[i]] += value
            elif j in mapping and i in self.fixed:
                self.linear[mapping[j]] += value
            elif i in self.fixed and j in self.fixed:
                self.offset += value

    def expand(self, bits):
        values = [int(i in self.fixed) for i in range(len(self.parent.linear))]
        for i, bit in zip(self.old, bits):
            values[i] = bit
        return values

    def energy(self, bits):
        return self.offset + sum(c*x for c, x in zip(self.linear, bits)) + sum(
            c*bits[i]*bits[j] for (i, j), c in self.quadratic.items())

    def decode(self, bits):
        full = self.expand(bits)
        if self.energy(bits) != self.parent.energy(full):
            raise AssertionError('Conditional substitution lost full energy')
        return self.parent.decode(full)


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def run(source, output):
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    names = ['deadline_boundary.py', 'deadline_qubo.py', 'window_qubo.py',
             'window_reduction.py', 'assignment_qaoa.py']
    hashes = {}
    for name in names:
        src = root / 'stage2' / name
        dst = output / 'sources' / 'stage2' / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        hashes[name] = hashlib.sha256(src.read_bytes()).hexdigest()
    protocol = dict(case='heat-lease-32', cap=900, parent='First saved heuristic parent; no best-parent selection',
        max_free=12, max_logical_qubits=24, max_sector_states=1_000_000,
        release='Minimize empty arc-supported groups, then maximize surviving rows, then lexical operation ID',
        quantum=dict(layers=1, evaluations=32, shots=256, seeds=[7, 13, 29], alpha=.25),
        gate='All supported groups nonempty; <=24 logical bits; <=1M product states; zero-energy local assignment exists',
        scope='Exploratory known recovery fixture; actual outside parent assignments fixed; no CP answer input',
        source_hashes=hashes, remote_calls=0)
    save(output / 'protocol.json', protocol)
    p = json.loads((source / 'problem.json').read_text())
    plan = json.loads((source / 'parents.json').read_text())['parents'][0]
    save(output / 'problem.json', p)
    save(output / 'parent.json', plan)
    began = time.perf_counter()
    assert check_plan(p, plan)['valid']
    q = compile_deadline(p, cap=900)
    ladder = structural_ladder(q, plan, max_free=12)
    save(output / 'ladder.json', ladder)
    last = ladder[-1]
    failures = []
    if not last['arc_consistent']:
        failures.append('No arc-consistent boundary block within12 free operations')
    if last['logical_qubits'] > 24:
        failures.append('Logical qubit guard exceeded')
    if last['sector_states'] > 1_000_000:
        failures.append('Invariant-sector memory guard exceeded')
    result = dict(protocol=protocol, full_query=q.metadata(), parent_check=check_plan(p, plan),
                  ladder=ladder, gate_failures=failures, quantum_runs=[])
    if not failures:
        local = ConditionedQuery(q, last['domains'], last['fixed'])
        # The frozen structural block is now audited exactly before sampling.
        from .assignment_qaoa import AssignmentSector, sample
        sector = AssignmentSector.build(local, max_states=1_000_000)
        result['local_exact_minimum'] = int(sector.energies.min())
        if sector.energies.min() != 0:
            result['gate_failures'].append('Exact conditional block has no zero-energy recovery')
        else:
            result['local_model'] = dict(linear=local.linear, quadratic=[[i,j,c]for(i,j),c in local.quadratic.items()],
                                         offset=local.offset, groups=local.groups, variables=local.variables)
            for method in ['qaoa_xy', 'uniform_onehot', 'sa_onehot']:
                for seed in [7,13,29]:
                    row = sample(sector, method=method, seed=seed, layers=1, evaluations=32, shots=256, alpha=.25, sweeps=256)
                    row['scope'] = 'Exact full-query conditioned block with original heuristic outside commitments fixed'
                    save(output / f'{method}-{seed}.json', row)
                    result['quantum_runs'].append({k:v for k,v in row.items() if k!='qasm'})
    result['wall_seconds'] = time.perf_counter() - began
    result['source_stable'] = all(hashlib.sha256((root/'stage2'/n).read_bytes()).hexdigest()==h for n,h in hashes.items())
    save(output / 'report.json', result)
    save(output / 'manifest.json', {str(path.relative_to(output)):hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in output.rglob('*') if path.is_file()})
    print(json.dumps(dict(gate_failures=result['gate_failures'], ladder=[{k:r[k]for k in ['free','logical_qubits','sector_states','arc_consistent']}for r in ladder], wall_seconds=result['wall_seconds'])),flush=True)
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path('output/manufacturing-recovery-v2/heat-lease-32'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    run(args.source,args.output)
