import unittest

from stage2.statistics import weighted_cvar,weighted_mean,stratified_protocol,branch,paired_report
from stage2.spec import build


class StratifiedStatisticsTests(unittest.TestCase):
    def test_fractional_tail_boundary_is_exact(self):
        self.assertAlmostEqual(weighted_cvar([100,10,0],[.05,.1,.85]),55.)
        self.assertEqual(weighted_cvar([2,9],[.8,.2],0),weighted_mean([2,9],[.8,.2]))

    def test_protocol_uses_declared_leaf_probabilities_and_no_solver_scores(self):
        stages=build()['uncertainty_stages'];p=stratified_protocol(stages,3)
        self.assertEqual(p,stratified_protocol(stages,3))
        self.assertEqual(p['total_tapes'],24)
        self.assertAlmostEqual(sum(leaf['per_tape_weight']*3 for leaf in p['leaves']),1)
        for leaf in p['leaves']:
            for seed in leaf['seeds']:self.assertEqual(branch(seed,stages),tuple(leaf['outcomes']))

    def test_paired_bootstrap_preserves_differences_and_clusters_actor_replicas(self):
        p=stratified_protocol(build()['uncertainty_stages'],2);a=[];b=[]
        for leaf in p['leaves']:
            for s in leaf['seeds']:
                for actor in (1,2,3):
                    a.append(dict(seed=s,policy_seed=actor,valid=True,loss=s%7+actor))
                    b.append(dict(seed=s,policy_seed=actor,valid=True,loss=s%7+actor-2))
        r=paired_report(a,b,p,lambda row:row['loss'],100)
        self.assertEqual(r['environment_tapes'],16)
        self.assertEqual(r['actor_replicas_left'],48)
        self.assertAlmostEqual(r['mean_difference'],-2)
        for endpoint in r['mean_difference_percentile_bootstrap_95']:self.assertAlmostEqual(endpoint,-2)
        for endpoint in r['cvar90_difference_percentile_bootstrap_95']:self.assertAlmostEqual(endpoint,-2)
        with self.assertRaises(ValueError):paired_report(a,b[:-1],p,lambda row:row['loss'],10)

    def test_joint_actor_risk_retains_actor_variation_without_extra_factories(self):
        p=dict(leaves=[dict(seeds=[0,1],per_tape_weight=.5)])
        left=[dict(seed=s,policy_seed=a,valid=True,loss=loss) for s in (0,1) for a,loss in ((11,0),(12,10))]
        right=[dict(row,loss=row['loss']-1) for row in left]
        result=paired_report(left,right,p,lambda r:r['loss'],bootstrap=30)
        self.assertEqual(result['environment_tapes'],2)
        self.assertAlmostEqual(result['left_cvar90'],5)
        self.assertAlmostEqual(result['left_joint_actor_environment_cvar90'],10)
        self.assertAlmostEqual(result['joint_actor_environment_cvar90_difference'],-1)
        for endpoint in result['joint_actor_environment_cvar90_difference_percentile_bootstrap_95']:
            self.assertAlmostEqual(endpoint,-1)


if __name__=='__main__':unittest.main()
