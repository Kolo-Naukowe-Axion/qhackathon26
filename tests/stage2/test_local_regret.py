from copy import deepcopy
import unittest

from stage2 import dispatch
from stage2.local_regret import (_factory,_checked,digest,execute,feasible_subsets,
    force_boundary,independently_feasible,pool_sha,prefix_payload)
from stage2.spec import build


class FullModelLocalRegretTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.instance=build(3,seed=0)
        cls.weights=dict(wip_limit=3,mode='standard',lease_calibration=True,selector='exact',worker_calendar=True,preposition=False,policy_seed=0)
        cls.baseline=_factory(cls.instance,cls.weights).run()
        assert _checked(cls.baseline)['valid']
        cls.boundary=next(d for d in cls.baseline['qubo_decisions'] if d['result']['qubo']['couplers']>0 and
            2<=d['result']['qubo']['core_variables']<=4 and d['result']['qubo']['variables']<=5)
        cls.prefix=digest(prefix_payload(cls.baseline,cls.boundary['tick']))

    def test_independent_original_constraints_include_empty_and_reject_resource_excess(self):
        pool=dict(candidates=[dict(id='A',resources={'power':6}),dict(id='B',resources={'power':4})],
            conflicts=[('A','B')],capacities={'power':5})
        self.assertEqual(feasible_subsets(pool),[[],['B']])
        self.assertFalse(independently_feasible(pool,['A']))
        self.assertFalse(independently_feasible(pool,['B','B']))
        self.assertFalse(independently_feasible(pool,['not-a-candidate']))

    def test_forcing_exact_action_reproduces_whole_physical_baseline(self):
        original=dispatch.choose
        row,trace=execute(self.instance,self.weights,boundary=self.boundary,
            selected=self.boundary['result']['selected'],expected_prefix=self.prefix)
        self.assertTrue(row['valid'],row)
        self.assertEqual(row['forced_boundary']['hits'],1)
        self.assertEqual(row['forced_boundary']['reconstructed_pool_sha256'],pool_sha(self.boundary))
        for key in ('operations','moves','worker_moves','events','energy','metrics'):
            self.assertEqual(self.baseline[key],trace[key],key)
        self.assertIs(dispatch.choose,original)

    def test_all_feasible_sets_retain_prefix_and_real_commit_including_empty(self):
        subsets=feasible_subsets(self.boundary);self.assertIn([],subsets)
        for selected in subsets:
            row,trace=execute(self.instance,self.weights,boundary=self.boundary,selected=selected,expected_prefix=self.prefix)
            self.assertTrue(row['valid'],(selected,row))
            actual=next(d for d in trace['qubo_decisions'] if d['tick']==self.boundary['tick'])
            self.assertEqual(sorted(actual['committed']),sorted(selected))
            self.assertEqual(actual['result']['method'],'forced_offline_counterfactual')

    def test_changed_full_pool_invalid_force_and_body_exception_restore_wrapper(self):
        original=dispatch.choose;bad=deepcopy(self.boundary);bad['candidates'][0]['reward']+=1
        row,_=execute(self.instance,self.weights,boundary=bad,selected=[])
        self.assertFalse(row['valid']);self.assertIn('full candidate pool differs',row['error']['message'])
        self.assertIs(dispatch.choose,original)
        row,_=execute(self.instance,self.weights,boundary=self.boundary,selected=['missing'])
        self.assertFalse(row['valid']);self.assertIn('original candidate/resource',row['error']['message'])
        self.assertIs(dispatch.choose,original)
        with self.assertRaisesRegex(RuntimeError,'body failure'):
            with force_boundary(self.boundary,[]):raise RuntimeError('body failure')
        self.assertIs(dispatch.choose,original)

    def test_wrong_physical_prefix_is_retained_as_invalid(self):
        altered=prefix_payload(self.baseline,self.boundary['tick']);altered['energy'][0]['grid_kw']+=1
        row,_=execute(self.instance,self.weights,boundary=self.boundary,selected=[],expected_prefix=digest(altered))
        self.assertFalse(row['valid'])
        self.assertTrue(any(issue['code']=='frozen_prefix_mismatch' for issue in row['issues']))


if __name__=='__main__':unittest.main()
