"""Three-bit semantic decoder and proof-tampering tests; no QPU dependencies."""
from copy import deepcopy
from itertools import product
import json
from pathlib import Path
import unittest

from stage2.rank_three import structural_compile,verify,decode,derive_polynomial,four_penalties,add
from stage2.rank_probe import verify_unsat_proof

ROOT=Path(__file__).resolve().parents[2]


class ThreeBitStructuralTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=ROOT/'output/stage2-search/rank-probe/sat-only-final'
        cls.instance=json.loads((ROOT/'instances/instance_3x3.json').read_text())
        cls.four=json.loads((source/'structural-four-bit-model.json').read_text())
        cls.prior=json.loads((source/'report.json').read_text())
        cls.model,cls.proof=structural_compile(cls.instance,cls.four,cls.prior['minimal_nogoods'])

    def test_symbolic_factor_algebra_is_quadratic_and_nonnegative(self):
        polynomial,c,first,second=derive_polynomial()
        self.assertEqual(polynomial,{(0,):1,(2,):1,(0,1):1,(0,2):-2,(1,2):-1})
        def evaluate(p,bits):return sum(value*int(all(bits[i]for i in term))for term,value in p.items())
        for a,b,d in product((0,1),repeat=3):
            bits=[a,b,d]
            self.assertEqual(evaluate(c,bits),int(not a or b))
            self.assertGreaterEqual(evaluate(first,bits),0)
            self.assertGreaterEqual(evaluate(second,bits),0)
        for bits in product((0,1),repeat=4):
            for penalty in four_penalties():self.assertIn(evaluate(penalty,bits),(0,1))

    def test_every_implication_has_a_replayed_unsat_proof(self):
        self.assertEqual(len(self.proof['sat_implication_proofs']),14)
        relation=[]
        for row in self.proof['sat_implication_proofs']:
            self.assertFalse(row['satisfiable'])
            assumptions=dict(row['assumptions'])
            verify_unsat_proof(self.proof['clauses'],assumptions,row['unsat_proof'])
            if row['purpose']=='c = NOT a OR b':relation.append(assumptions)
        self.assertEqual(len(relation),4)

    def test_all_original_orders_checked_and_all_five_retained(self):
        report=verify(self.instance,self.model,self.four)
        self.assertEqual(report['original_order_bitstrings_checked'],512)
        self.assertEqual(report['official_schedules_validated'],216)
        self.assertEqual(report['retained_good_original_states'],[73,292,438,502,511])
        self.assertEqual(report['exact_minimum_bits_for_all_order_retaining_deterministic_basis_decoder'],3)
        self.assertEqual([row['energy']for row in report['basis']],[0,1,0,2,1,0,0,0])
        self.assertEqual(len({tuple(decode(bits))for bits in product((0,1),repeat=3)}),8)

    def test_constructor_does_not_read_the_answer_list(self):
        source=deepcopy(self.four)
        source['zero_energy_full_order_states']=['deliberately poisoned; must not be consumed']
        changed,proof=structural_compile(self.instance,source,self.prior['minimal_nogoods'])
        self.assertEqual(changed,self.model)
        self.assertEqual(proof['sat_implication_proofs'],self.proof['sat_implication_proofs'])

    def test_tampered_polynomial_or_physical_cut_cannot_be_certified(self):
        altered=deepcopy(self.four);altered['linear'][0]+=1
        with self.assertRaises(ValueError):structural_compile(self.instance,altered,self.prior['minimal_nogoods'])
        altered=deepcopy(self.prior['minimal_nogoods'])
        altered[0]['assignments']=[]
        with self.assertRaises(AssertionError):structural_compile(self.instance,self.four,altered)
        with self.assertRaises(ValueError):decode([1,0,2])


if __name__=='__main__':unittest.main()
