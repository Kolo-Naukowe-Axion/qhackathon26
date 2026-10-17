"""Compare conservative compounded floors with all legal mode histories."""
from copy import deepcopy
from fractions import Fraction
from itertools import product
import unittest

from stage2.spec import build
from stage2.quality_material_bound import risk_floors
from stage2.quality_compound_bound import certificate, compound_floors


class CompoundQualityTests(unittest.TestCase):
    def test_floor_below_every_zero_wear_legal_history_and_above_max_step(self):
        instance=build(12,seed=0)
        _,floors,_=compound_floors(instance)
        original,_=risk_floors(instance)
        for recipe,route in instance['recipes'].items():
            probabilities=[]
            for step in route:
                p=step['process']
                if p!='QA':
                    probabilities.append([instance['quality']['manufacturing_defect_probabilities'][p][mode] for mode in instance['modes'][p]])
            self.assertGreaterEqual(floors[recipe], original[recipe])
            for chosen in product(*probabilities):
                risk=0.
                for p in chosen:risk=1-(1-risk)*(1-p)
                self.assertLess(float(floors[recipe]),risk)
        self.assertGreater(float(floors['housing']),.049)

    def test_real_nonzero_proof_preserved_and_monotone_against_original(self):
        for seed in range(32):
            c=certificate(build(32,horizon=14400,seed=seed))
            self.assertGreaterEqual(c['unfulfilled_lower_bound'],c['original_max_step_lower_bound'])
        c=certificate(build(32,horizon=14400,seed=6))
        self.assertEqual(c['unfulfilled_lower_bound'],1)
        self.assertIsNone(c['secondary_optimality_gap'])

    def test_original_source_and_domain_guards_remain_mandatory(self):
        for mutate in (lambda i:i['quality'].update(max_replacements_per_original_component=2),
                       lambda i:i['units'][0].update(accepted=True),
                       lambda i:i['quality'].update(wear_risk_coefficient=-1)):
            instance=build(12,seed=0);mutate(instance)
            with self.assertRaises(ValueError):certificate(instance)


if __name__=='__main__':unittest.main()
