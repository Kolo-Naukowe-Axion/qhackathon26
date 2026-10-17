from copy import deepcopy
import unittest

from stage2.manufacturing_realism import domain_counts, feature_variants
from stage2.manufacturing_cases import production_case
from stage2.window_qubo import assignments, digest


class ManufacturingRealismTests(unittest.TestCase):
    def test_feature_removals_keep_horizon_grid_operations_and_original_immutable(self):
        original = production_case(2, 'heat-lease')
        before = deepcopy(original)
        variants = feature_variants(original)
        self.assertEqual(original, before)
        for variant in variants.values():
            self.assertEqual(variant['horizon'], original['horizon'])
            self.assertEqual(variant['grid'], original['grid'])
            self.assertEqual([op['id'] for op in variant['operations']], [op['id'] for op in original['operations']])
            self.assertEqual(set(variant['machines']), set(original['machines']))
            self.assertEqual(set(variant['workers']), set(original['workers']))
        self.assertNotIn('machine_setups', variants['no_machine_setups'])
        self.assertTrue(all(value == 0 for row in variants['zero_transfer_lags']['transport_lags'].values() for value in row.values()))
        self.assertTrue(all(op['due'] == original['horizon'] for op in variants['no_deadline_cost']['operations']))

    def test_objective_and_pair_only_ablations_keep_unary_domains(self):
        original = production_case(2, 'heat-lease')
        variants = feature_variants(original)
        domains = {op['id']: digest(assignments(original, op)) for op in original['operations']}
        for name in ['zero_transfer_lags', 'no_deadline_cost']:
            self.assertEqual(domains, {op['id']: digest(assignments(variants[name], op)) for op in variants[name]['operations']})
        counts = domain_counts(original)
        self.assertGreaterEqual(counts['naive_assignment_product'], counts['unary_assignment_variables'])
        self.assertGreater(counts['cross_operation_pair_checks'], 0)


if __name__ == '__main__':
    unittest.main()
