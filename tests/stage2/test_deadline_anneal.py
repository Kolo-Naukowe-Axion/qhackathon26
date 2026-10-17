import random
import unittest

from stage2.deadline_anneal import apply_swap, checked_samples, fields_and_neighbors, onehot_anneal, swap_delta
from stage2.deadline_qubo import compile_deadline
from stage2.window_experiments import tiny_problem
from stage2.window_qubo import compile_qubo


class DeadlineAnnealTests(unittest.TestCase):
    def test_incremental_swap_matches_literal_energy_and_fields(self):
        rng = random.Random(73)
        for model in [compile_deadline(tiny_problem(), support_pruning=False), compile_qubo(tiny_problem())]:
            groups = list(model.groups.values())
            bits = [0] * len(model.linear)
            for group in groups:
                bits[rng.choice(group)] = 1
            fields, neighbors = fields_and_neighbors(model, bits)
            for _ in range(80):
                group = rng.choice([g for g in groups if len(g) > 1])
                old = next(i for i in group if bits[i])
                new = rng.choice([i for i in group if i != old])
                previous = model.energy(bits)
                change = swap_delta(fields, neighbors, old, new)
                apply_swap(bits, fields, neighbors, old, new)
                self.assertEqual(model.energy(bits), previous + change)
                expected, _ = fields_and_neighbors(model, bits)
                self.assertEqual(fields, expected)

    def test_actual_sampler_returns_checked_onehot_states_without_enumeration(self):
        model = compile_deadline(tiny_problem(), support_pruning=False)
        samples = onehot_anneal(model, seed=101, reads=4, proposals=256)
        self.assertEqual(len(samples), 4)
        for record in checked_samples(model, samples, cap=6):
            self.assertEqual(record['energy'], model.energy(record['bits']))
            self.assertTrue(all(sum(record['bits'][i] for i in group) == 1 for group in model.groups.values()))
        self.assertEqual(samples, onehot_anneal(model, seed=101, reads=4, proposals=256))

    def test_wrong_returned_energy_is_rejected(self):
        model = compile_deadline(tiny_problem())
        with self.assertRaises(AssertionError):
            checked_samples(model, [dict(bits=[1] * len(model.linear), energy=999, count=1)], cap=6)

    def test_raw_target_is_independent_of_wrong_completion_register(self):
        model = compile_qubo(tiny_problem())
        bits = [0] * len(model.linear)
        for operation, start in [('a', 0), ('b', 2)]:
            index = next(i for i in model.groups[operation] if model.variables[i]['start'] == start)
            bits[index] = 1
        index = next(i for i in model.groups['@makespan'] if model.variables[i]['start'] == 2)
        bits[index] = 1
        self.assertFalse(model.decode(bits)['valid'])
        record = checked_samples(model, [dict(bits=bits, energy=model.energy(bits), count=1)], cap=4)[0]
        self.assertFalse(record['encoded_valid'])
        self.assertTrue(record['raw_valid'])
        self.assertTrue(record['target_satisfied'])
        # A missing completion-register choice must not hide the same raw plan.
        bits[index] = 0
        record = checked_samples(model, [dict(bits=bits, energy=model.energy(bits), count=1)], cap=4)[0]
        self.assertFalse(record['encoded_valid'])
        self.assertTrue(record['target_satisfied'])


if __name__ == '__main__':
    unittest.main()
