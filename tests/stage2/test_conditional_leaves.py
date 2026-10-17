"""Tests for the reporting-only conditional summary helper; no factories."""
from fractions import Fraction as Q
import importlib.util
from pathlib import Path
import unittest

PATH=Path(__file__).resolve().parents[2]/'output/stage2-search/final-conditional-leaves/build.py'
SPEC=importlib.util.spec_from_file_location('conditional_leaf_evidence',PATH)
MODULE=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MODULE)


class ConditionalLeafTests(unittest.TestCase):
    def test_actors_are_averaged_within_two_environment_tapes(self):
        rows=[dict(valid=True,seed=s,policy_seed=a,loss=value) for s,a,value in
              ((1,10,0),(1,11,2),(2,10,8),(2,11,10))]
        mean,values=MODULE.actor_nested(rows,lambda r:r['loss'],[1,2],[10,11])
        self.assertEqual(values,{1:Q(1),2:Q(9)});self.assertEqual(mean,Q(5))
        with self.assertRaisesRegex(ValueError,'actor replica'):
            MODULE.actor_nested(rows[:-1],lambda r:r['loss'],[1,2],[10,11])
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            MODULE.actor_nested(rows+[rows[0]],lambda r:r['loss'],[1,2],[10,11])

    def test_true_probabilities_recover_weighted_mean_exactly(self):
        self.assertEqual(MODULE.reweight([Q(1,3),Q(5,2)],[Q(3,5),Q(2,5)]),Q(6,5))
        with self.assertRaisesRegex(ValueError,'normalized'):
            MODULE.reweight([Q(1),Q(2)],[Q(1,3),Q(1,3)])

    def test_missing_tapes_and_invalid_rows_are_rejected(self):
        row=dict(valid=True,seed=1,policy_seed=10,loss=0)
        with self.assertRaisesRegex(ValueError,'environment'):
            MODULE.actor_nested([row],lambda r:r['loss'],[1,2],[10])
        with self.assertRaisesRegex(ValueError,'Invalid'):
            MODULE.actor_nested([dict(row,valid=False)],lambda r:r['loss'],[1],[10])


if __name__=='__main__':unittest.main()
