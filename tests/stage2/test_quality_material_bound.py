import unittest
from fractions import Fraction
from itertools import combinations

from stage2.quality_material_bound import certificate,keyed_uniform,material_relaxation,risk_floors
from stage2.spec import build


class NecessaryQualityMaterialBoundTests(unittest.TestCase):
    def test_actual_training_tape_requires_an_extra_housing_blank(self):
        report=certificate(build(32,horizon=14400,seed=6))
        self.assertEqual(report['observed_realized_orders'],34)
        self.assertEqual(report['available_raw_blanks']['housing'],34)
        self.assertEqual(report['necessary_blank_demands']['P05'],(2,1,1))
        self.assertEqual(report['maximum_shipped_upper_bound'],33)
        self.assertEqual(report['unfulfilled_lower_bound'],1)
        self.assertEqual(report['unavoidable_quality_evidence'][0]['unit_id'],'P05/housing/1')

    def test_tape_and_floor_are_independent_of_policy_and_do_not_read_a_trace(self):
        instance=build(12,seed=15);floors,repair=risk_floors(instance)
        self.assertLess(floors['pump'],Fraction(1,100))
        self.assertLess(repair,Fraction(1,50))
        self.assertGreater(keyed_uniform(15,'quality:P11/pump/1:0'),floors['pump'])
        # The standard-mode P11 scrap is avoidable in principle; do not turn
        # a bad realized policy outcome into a global lower bound.
        report=certificate(instance)
        self.assertIsNotNone(report['necessary_blank_demands']['P11'])
        self.assertEqual(report['unfulfilled_lower_bound'],0)

    def test_exact_relaxation_matches_brute_force_and_excludes_impossible_orders(self):
        needs=dict(A=(2,1,1),B=(1,2,1),C=(1,1,2),D=(1,1,1),E=None)
        stock=dict(housing=4,rotor=3,flange=3)
        report=material_relaxation(needs,stock)
        best=0
        for size in range(6):
            for subset in combinations(needs,size):
                if any(needs[o] is None for o in subset):continue
                if all(sum(needs[o][r] for o in subset)<=list(stock.values())[r] for r in range(3)):best=max(best,size)
        self.assertEqual(report['maximum_shipped_upper_bound'],best)
        self.assertEqual(report['unfulfilled_lower_bound'],len(needs)-best)

    def test_extra_legal_mode_reduces_bound_and_unsupported_negative_risk_is_rejected(self):
        instance=build(32,horizon=14400,seed=6)
        for process in ('T','F','WASH','HEAT'):
            instance['modes'][process]['perfect']=dict(instance['modes'][process]['standard'])
            instance['quality']['manufacturing_defect_probabilities'][process]['perfect']=0
        self.assertEqual(certificate(instance)['unfulfilled_lower_bound'],0)
        instance['quality']['wear_risk_coefficient']=-1
        with self.assertRaises(ValueError):certificate(instance)

    def test_changed_repair_birth_and_risk_contracts_are_rejected(self):
        from copy import deepcopy
        original=build(32,horizon=14400,seed=6)
        for key in ('max_replacements_per_original_component','max_repairs_per_component_attempt'):
            changed=deepcopy(original);changed['quality'][key]=2
            with self.assertRaises(ValueError):certificate(changed)
        for variant in ('accepted','location','extra','pump-recipe','risk','intermediate-QA','negative-wear'):
            changed=deepcopy(original)
            if variant=='accepted':changed['units'][0]['accepted']=True
            elif variant=='location':changed['units'][0]['initial_location']='A1'
            elif variant=='extra':changed['units'].append(dict(changed['units'][0],id='extra'))
            elif variant=='pump-recipe':changed['recipes']['pump'].pop(0)
            elif variant=='risk':changed['quality']['wear_risk_coefficient']=1
            elif variant=='intermediate-QA':changed['recipes']['housing'].insert(1,dict(process='QA',base_ticks=45))
            elif variant=='negative-wear':changed['modes']['T']['eco']['wear']=-1
            with self.assertRaises(ValueError):certificate(changed)


if __name__=='__main__':unittest.main()
