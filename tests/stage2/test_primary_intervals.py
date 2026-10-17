import unittest

from stage2.primary_intervals import mean_interval


class PrimaryMeanIntervalsTests(unittest.TestCase):
    def test_stratified_paired_constant_difference_keeps_actor_clusters(self):
        protocol=dict(leaves=[dict(seeds=[0,1],per_tape_weight=.125),dict(seeds=[2,3],per_tape_weight=.375)])
        left=[dict(seed=seed,policy_seed=actor,valid=True,value=seed+actor) for seed in range(4) for actor in (1,2)]
        right=[dict(row,value=row['value']+1) for row in left]
        result=mean_interval(left,right,protocol,lambda row:row['value'],bootstrap=1000)
        self.assertEqual(result['mean_difference'],1)
        self.assertEqual(result['percentile_interval'],[1,1])
        self.assertEqual(result['individual_nominal_coverage'],.975)
        self.assertEqual(result['environment_tapes'],4)
        self.assertEqual(result['actor_replicas_right'],8)
        with self.assertRaisesRegex(ValueError,'Missing or extra'):
            mean_interval(left,right[:-2],protocol,lambda row:row['value'],bootstrap=1000)
        with self.assertRaisesRegex(ValueError,'At least1000'):
            mean_interval(left,right,protocol,lambda row:row['value'],bootstrap=999)


if __name__=='__main__':unittest.main()
