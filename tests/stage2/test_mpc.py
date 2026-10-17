import unittest

from stage2.engine import Factory
from stage2.spec import build
from stage2.check import check_trace,check_paired_causality
from stage2.mpc import continuation,resume,run


class CausalContinuationTests(unittest.TestCase):
    def test_resume_matches_original_physics_at_revelation_boundaries(self):
        for tick in (0,720,1440,2400):
            f=Factory(build(2,seed=0),dict(wip_limit=3,lease_calibration=True))
            snapshots=[]
            def capture(obs):
                if obs['tick']==tick:snapshots.append(continuation(f,tick,{},0))
                return dict(weights={})
            f.controller=capture
            actual=f.run();resumed=resume(snapshots[0])
            for key in ('operations','moves','events','energy','metrics'):
                self.assertEqual(actual[key],resumed[key],(tick,key))
            self.assertTrue(check_trace(resumed)['valid'])

    def test_planning_seed_replaces_actual_tape_before_future_execution(self):
        left=Factory(build(2,seed=0));right=Factory(build(2,seed=82))
        a=continuation(left,0,{},582,False);b=continuation(right,0,{},582,False)
        self.assertEqual(a.i['seed'],582)
        self.assertEqual(left.i['seed'],0)
        x=resume(a);y=resume(b)
        for key in ('operations','moves','events','energy','metrics'):
            self.assertEqual(x[key],y[key],key)

    def test_actual_rollout_controller_is_physically_valid_and_prefix_causal(self):
        options=[dict(wip_limit=2,mode='eco',lease_calibration=True),
                 dict(wip_limit=3,mode='standard',lease_calibration=True)]
        traces=[run(build(2,seed=seed),options[0],options,1,1440,seed=81)
                for seed in (0,1)]
        for trace in traces:
            self.assertTrue(check_trace(trace)['valid'])
            self.assertTrue(trace['planning']['decisions'])
        report=check_paired_causality(traces)
        self.assertTrue(report['valid'],report)


if __name__=='__main__':unittest.main()
