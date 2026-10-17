"""QAOA in the exact product of all assignment one-hot sectors.

Every raw assignment/makespan bit remains a logical qubit. Sector simulation
reduces classical memory, not the quantum register or the declared domain.
Only one-hot constraints are invariant; resource conflicts retain penalties.
"""
from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass

import numpy as np

@dataclass
class AssignmentSector:
    q: object
    groups: list
    sizes: tuple
    choices: np.ndarray
    energies: np.ndarray
    phase: dict

    @classmethod
    def build(cls, q, max_states=1_000_000):
        groups = [list(v) for v in q.groups.values()]
        sizes = tuple(len(g) for g in groups)
        count = math.prod(sizes)
        if count > max_states:
            raise ValueError(f'Explicit invariant-sector memory cap: {count}>{max_states}')
        choices = np.array(np.unravel_index(np.arange(count), sizes)).T
        selected = np.zeros((count, len(q.linear)), dtype=np.int64)
        for axis, group in enumerate(groups):
            selected[np.arange(count), np.array(group)[choices[:, axis]]] = 1
        energies = np.full(count, q.offset, dtype=np.int64)
        for i, coefficient in enumerate(q.linear):
            energies += coefficient * selected[:, i]
        for (i, j), coefficient in q.quadratic.items():
            energies += coefficient * selected[:, i] * selected[:, j]
        linear, quadratic, offset = list(q.linear), dict(q.quadratic), q.offset
        for group in groups:
            offset -= q.penalty
            for i in group:
                linear[i] += q.penalty
            for k, i in enumerate(group):
                for j in group[k + 1:]:
                    pair = tuple(sorted((i, j)))
                    quadratic[pair] = quadratic.get(pair, 0) - 2 * q.penalty
                    if not quadratic[pair]:
                        del quadratic[pair]
        phase = dict(linear=linear, quadratic=quadratic, offset=offset)
        # Every removed term is P(sum group - 1)^2, identically zero here.
        values = np.full(count, offset, dtype=np.int64)
        for i, coefficient in enumerate(linear):
            values += coefficient * selected[:, i]
        for (i, j), coefficient in quadratic.items():
            values += coefficient * selected[:, i] * selected[:, j]
        if not np.array_equal(values, energies):
            raise AssertionError('Invariant phase simplification changed a sector energy')
        return cls(q, groups, sizes, choices, energies, phase)

    def bits(self, index):
        values = [0] * len(self.q.linear)
        for group, choice in zip(self.groups, self.choices[index]):
            values[group[int(choice)]] = 1
        return values

    def evolve(self, gammas, betas, scale):
        if len(gammas) != len(betas) or not gammas or scale <= 0:
            raise ValueError('Matched nonempty layers and positive scale required')
        state = np.full(len(self.energies), 1 / math.sqrt(len(self.energies)), dtype=complex)
        diagonal = (self.energies.astype(float) - float(self.energies[0])) / scale
        for gamma, beta in zip(gammas, betas):
            state *= np.exp(-1j * gamma * diagonal)
            tensor = state.reshape(self.sizes)
            for axis, size in enumerate(self.sizes):
                view = np.moveaxis(tensor, axis, -1)
                for j in range(size - 1):
                    a, b = view[..., j].copy(), view[..., j + 1].copy()
                    view[..., j] = math.cos(beta) * a - 1j * math.sin(beta) * b
                    view[..., j + 1] = math.cos(beta) * b - 1j * math.sin(beta) * a
        return state

    def circuit(self, gammas, betas, scale):
        n = len(self.q.linear)
        lines = ['OPENQASM 2.0;', 'include "qelib1.inc";', f'qreg q[{n}];', f'creg c[{n}];',
                 'gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }',
                 'gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }']
        for group in self.groups:
            lines.append(f'x q[{group[0]}];')
            for j in range(len(group) - 1):
                theta = math.acos(1 / math.sqrt(len(group) - j))
                i, k = group[j:j + 2]
                lines += [f'rxx({theta:.17g}) q[{i}],q[{k}];',
                          f'ryy({theta:.17g}) q[{i}],q[{k}];', f's q[{k}];']
        fields = [-v / 2 for v in self.phase['linear']]
        for (i, j), coefficient in self.phase['quadratic'].items():
            fields[i] -= coefficient / 4
            fields[j] -= coefficient / 4
        for gamma, beta in zip(gammas, betas):
            for i, field in enumerate(fields):
                if field:
                    lines.append(f'rz({2 * gamma * field / scale:.17g}) q[{i}];')
            for (i, j), coefficient in sorted(self.phase['quadratic'].items()):
                lines += [f'cx q[{i}],q[{j}];', f'rz({gamma * coefficient / (2 * scale):.17g}) q[{j}];',
                          f'cx q[{i}],q[{j}];']
            for group in self.groups:
                for i, j in zip(group, group[1:]):
                    lines += [f'rxx({beta:.17g}) q[{i}],q[{j}];', f'ryy({beta:.17g}) q[{i}],q[{j}];']
        return '\n'.join(lines + ['measure q -> c;']) + '\n'


def sample(sector, method='qaoa_xy', seed=7, layers=2, evaluations=128,
           shots=1024, alpha=1.0, sweeps=128):
    if layers < 1 or evaluations < 8 or shots < 1 or not 0 < alpha <= 1:
        raise ValueError('Positive layers/shots, >=8 evaluations and 0<alpha<=1 required')
    began, cpu = time.perf_counter(), time.process_time()
    energy = sector.energies
    rng = np.random.default_rng(seed)
    optimization = None
    counts = np.zeros(len(energy), dtype=np.int64)
    if method == 'qaoa_xy':
        scale = max([1] + [abs(v) for v in sector.phase['linear']] +
                    [abs(v) for v in sector.phase['quadratic'].values()])
        order = np.argsort(energy, kind='stable') if alpha < 1 else None
        angle_rng, best, calls = random.Random(seed), None, 0

        def evaluate(angles):
            nonlocal best, calls
            probability = np.abs(sector.evolve(angles[:layers], angles[layers:], scale)) ** 2
            if order is None:
                value = float(np.dot(probability, energy - energy[0]))
            else:
                cumulative = np.cumsum(probability[order])
                weight = np.maximum(0, np.minimum(probability[order], alpha - cumulative + probability[order]))
                value = float(np.dot(weight, energy[order] - energy[0]) / alpha)
            calls += 1
            if best is None or value < best[0]:
                best = (value, list(angles), probability)
            return value

        for restart in range(4):
            angles = ([.7] * layers + [.35] * layers if restart == 0 else
                      [angle_rng.uniform(0, 2 * math.pi) for _ in range(2 * layers)])
            value = evaluate(angles)
            limit = min(evaluations, (restart + 1) * evaluations // 4)
            step = .8
            while calls < limit:
                changed = False
                for axis in range(2 * layers):
                    for direction in (-1, 1):
                        if calls >= limit:
                            break
                        trial = list(angles)
                        trial[axis] = (trial[axis] + direction * step) % (2 * math.pi)
                        candidate = evaluate(trial)
                        if candidate < value:
                            value, angles, changed = candidate, trial, True
                if not changed:
                    step *= .5
        _, angles, probability = best
        probability /= probability.sum()
        counts = rng.multinomial(shots, probability)
        optimization = dict(gammas=angles[:layers], betas=angles[layers:], scale=scale,
                            evaluations=calls, objective='expectation' if alpha == 1 else 'CVaR', alpha=alpha,
                            exact_reference_used_for_training=False)
    elif method == 'uniform_onehot':
        probability = np.full(len(energy), 1 / len(energy))
        counts = rng.multinomial(shots, probability)
    elif method == 'sa_onehot':
        # A stronger control than uniform: multi-start Metropolis updates on the
        # same one-hot domain and exact energy. Every score evaluation is counted.
        probability = None
        replicas = min(shots, 32)
        proposals = 0
        for _ in range(replicas):
            choice = tuple(int(rng.integers(k)) for k in sector.sizes)
            current = int(np.ravel_multi_index(choice, sector.sizes))
            best_index = current
            for iteration in range(sweeps):
                proposed = list(choice)
                axis = int(rng.integers(len(proposed)))
                proposed[axis] = int(rng.integers(sector.sizes[axis]))
                candidate = int(np.ravel_multi_index(tuple(proposed), sector.sizes))
                delta = int(energy[candidate] - energy[current])
                temperature = max(1, sector.q.penalty * (1 - iteration / sweeps) ** 3)
                proposals += 1
                if delta <= 0 or rng.random() < math.exp(-delta / temperature):
                    choice, current = tuple(proposed), candidate
                if energy[current] < energy[best_index]:
                    best_index = current
            counts[best_index] += 1
        optimization = dict(replicas=replicas, sweeps=sweeps, score_evaluations=proposals)
    else:
        raise ValueError('Unknown method')
    seen = np.flatnonzero(counts)
    winner = min(seen, key=lambda i: (int(energy[i]), int(i)))
    bits = sector.bits(winner)
    decoded = sector.q.decode(bits)
    if sector.q.energy(bits) != int(energy[winner]):
        raise AssertionError('Sector sample energy mismatch')
    # Exact reference is evaluated only for reporting, after training/sampling.
    optimum = int(energy.min())
    result = dict(method=method, seed=seed, layers=layers, samples=int(counts.sum()),
                  requested_samples=shots, logical_qubits=len(sector.q.linear), sector_amplitudes=len(energy),
                  energy=int(energy[winner]), decoded=decoded, bits=bits, optimization=optimization,
                  sector_exact_energy=optimum, optimal_samples=int(counts[energy == optimum].sum()),
                  feasible_samples=int(counts[energy < sector.q.penalty].sum()),
                  exact_hit_probability=float(probability[energy == optimum].sum()) if probability is not None else None,
                  feasible_probability=float(probability[energy < sector.q.penalty].sum()) if probability is not None else None,
                  observed_counts={str(int(i)): int(counts[i]) for i in seen},
                  wall_seconds=time.perf_counter() - began, process_cpu_seconds=time.process_time() - cpu,
                  physical_qpu_calls=0,
                  scope='Complete declared one-hot assignment domain; no candidate cap or fixed outside bits. '
                        'All logical qubits retained. Exact classical simulation/training costs included separately.')
    if method == 'qaoa_xy':
        result['qasm'] = sector.circuit(angles[:layers], angles[layers:], scale)
    return result
