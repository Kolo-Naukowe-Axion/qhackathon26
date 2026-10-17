import unittest

import numpy as np

from stage2.assignment_qaoa import AssignmentSector, sample
from stage2.entry_core import recovery_cell
from stage2.entry_campaign import packet
from stage2.window_experiments import tiny_problem
from stage2.window_qubo import compile_qubo, solve_cp


class AssignmentQAOATests(unittest.TestCase):
    def test_every_sector_energy_and_one_hot_assignment_are_preserved(self):
        q = compile_qubo(tiny_problem())
        sector = AssignmentSector.build(q)
        for index, energy in enumerate(sector.energies):
            bits = sector.bits(index)
            self.assertEqual(q.energy(bits), int(energy))
            self.assertTrue(all(sum(bits[i] for i in group) == 1 for group in q.groups.values()))
        self.assertEqual(len(set(tuple(sector.bits(i)) for i in range(len(sector.energies)))),
                         len(sector.energies))

    def test_sector_matches_independent_full_hilbert_pair_rotations(self):
        q = compile_qubo(tiny_problem())
        sector = AssignmentSector.build(q)
        n = len(q.linear)
        initial = np.zeros(1 << n, dtype=complex)
        for index in range(len(sector.energies)):
            mask = sum(b << i for i, b in enumerate(sector.bits(index)))
            initial[mask] = 1 / np.sqrt(len(sector.energies))
        values = np.array([q.energy([(mask >> j) & 1 for j in range(n)])
                           for mask in range(1 << n)])
        gammas, betas, scale = [.37, .62], [.24, .83], 19
        full = initial.copy()
        for gamma, beta in zip(gammas, betas):
            full *= np.exp(-1j * gamma * (values - values[0]) / scale)
            for group in sector.groups:
                for i, j in zip(group, group[1:]):
                    for mask in range(1 << n):
                        if (mask >> i) & 1 and not (mask >> j) & 1:
                            other = mask ^ ((1 << i) | (1 << j))
                            a, b = full[mask], full[other]
                            full[mask] = np.cos(beta) * a - 1j * np.sin(beta) * b
                            full[other] = np.cos(beta) * b - 1j * np.sin(beta) * a
        expected = sector.evolve(gammas, betas, scale)
        # Only probabilities are compared: the two diagonal origins differ by a
        # global phase, which cannot affect measurement outcomes.
        support = []
        for index in range(len(sector.energies)):
            mask = sum(b << i for i, b in enumerate(sector.bits(index)))
            support.append(mask)
            self.assertAlmostEqual(abs(full[mask]) ** 2, abs(expected[index]) ** 2, places=12)
        self.assertAlmostEqual(float(np.sum(abs(full) ** 2)), 1, places=12)
        self.assertLess(float(np.sum(abs(full) ** 2)) - float(np.sum(abs(full[support]) ** 2)), 1e-12)

    def test_complete_manufacturing_cases_have_matching_raw_cp_optima(self):
        for kwargs in [dict(horizon=120), dict(outage=True),
                       dict(outage=True, spare_mill=False), dict(cross_skill=False)]:
            with self.subTest(kwargs=kwargs):
                p = recovery_cell(**kwargs)
                q = compile_qubo(p, support_pruning=True)
                sector = AssignmentSector.build(q)
                reference = solve_cp(p, 5, 1)
                self.assertTrue(reference['optimal'])
                self.assertEqual(int(sector.energies.min()), reference['objective'])
                ground = np.flatnonzero(sector.energies == sector.energies.min())
                self.assertTrue(all(q.decode(sector.bits(i))['valid'] for i in ground))
                self.assertEqual(packet(q)['energy_roundtrip_states'], 64)

    def test_sampling_returns_a_measured_state_and_counts_all_work(self):
        sector = AssignmentSector.build(compile_qubo(tiny_problem()))
        for method in ['uniform_onehot', 'qaoa_xy', 'sa_onehot']:
            row = sample(sector, method=method, shots=32, evaluations=16, sweeps=8)
            self.assertEqual(sum(row['observed_counts'].values()), row['samples'])
            measured = [sector.bits(int(i)) for i in row['observed_counts']]
            self.assertIn(row['bits'], measured)
            self.assertEqual(row['energy'], sector.q.energy(row['bits']))
            self.assertEqual(row['physical_qpu_calls'], 0)

    def test_explicit_memory_guard(self):
        with self.assertRaises(ValueError):
            AssignmentSector.build(compile_qubo(tiny_problem()), max_states=1)


if __name__ == '__main__':
    unittest.main()
