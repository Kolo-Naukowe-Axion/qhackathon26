import unittest
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

from stage2 import dispatch
from stage2.check import check_trace,check_paired_causality
from stage2.kit_recovery import run as original_run
from stage2.recovery_routing import BASE_WEIGHTS
from stage2.selector_reward import reweight,reward_override,run,diagnostic_tasks
from stage2.spec import build


class SelectorRewardTests(unittest.TestCase):
    def test_original_is_exact_physical_equivalent(self):
        instance=build(2,seed=0);weights=dict(BASE_WEIGHTS,selector='exact')
        opts=dict(admission=True,tool_policy={'mode':'hard'},recovery_policy={'enabled':True})
        expected=original_run(instance,weights,**opts);actual=run(instance,weights,**opts)
        for key in ('operations','moves','worker_moves','events','energy','metrics'):self.assertEqual(expected[key],actual[key],key)

    def test_batch_bonus_can_overturn_priority_and_both_ablations_correct(self):
        instance=build(2);offers=[]
        for units in (['high'],['low1','low2']):
            offers.append(dict(unit_ids=units,machine_id='H2',worker_ids=['W02'],
                worker_intervals=[dict(worker_id='W02',start=0,end=5)],worker_calendar_aware=True,
                tool_ids=[],start=0,end=60,power_kw=1))
        _,original=dispatch.choose(offers,instance,[],0,100,[0,100],'exact')
        self.assertEqual(original['result']['selected'],['C1'])
        for mode in ('no-batch','priority-lex'):
            with reward_override(mode):_,actual=dispatch.choose(offers,instance,[],0,100,[0,100],'exact')
            self.assertEqual(actual['result']['selected'],['C0'])
            self.assertEqual(actual['conflicts'],original['conflicts']);self.assertEqual(actual['capacities'],original['capacities'])
            for old,new in zip(original['candidates'],actual['candidates']):
                self.assertEqual({k:v for k,v in old.items() if k!='reward'},{k:v for k,v in new.items() if k!='reward'})

    def test_lex_rank_dominates_all_lower_candidates_and_ties_are_stable(self):
        candidates=[dict(id=f'C{i}',reward=1,resources={'power':i}) for i in range(8)]
        frozen=deepcopy(candidates);priorities=[3,1,1,8,7,2,4,5];weighted=reweight(candidates,priorities,'priority-lex')
        order=sorted(range(8),key=lambda j:(priorities[j],j));self.assertEqual(order[:2],[1,2])
        for rank,j in enumerate(order):self.assertGreater(weighted[j]['reward'],sum(weighted[k]['reward'] for k in order[rank+1:]))
        self.assertEqual(frozen,candidates)

    def test_restoration_nested_and_cross_thread_guards(self):
        original=dispatch.choose
        with self.assertRaisesRegex(RuntimeError,'injected'):
            with reward_override('no-batch'):
                with self.assertRaises(RuntimeError):
                    with reward_override('priority-lex'):pass
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future=pool.submit(dispatch.choose,[],build(2),[],0,100,[],'exact')
                    with self.assertRaisesRegex(RuntimeError,'cross threads'):future.result()
                raise RuntimeError('injected')
        self.assertIs(original,dispatch.choose)

    def test_real_causal_traces_and_commit_identity(self):
        for mode in ('no-batch','priority-lex'):
            traces=[]
            for seed in (0,1,16):
                trace=run(build(2,seed=seed),dict(BASE_WEIGHTS,selector='exact'),admission=True,
                    tool_policy={'mode':'hard'},recovery_policy={'enabled':True},reward_mode=mode)
                self.assertTrue(check_trace(trace)['valid']);traces.append(trace)
                for decision in trace['qubo_decisions']:
                    self.assertEqual(sorted(decision['result']['selected']),sorted(decision['committed']))
            self.assertTrue(check_paired_causality(traces)['valid'])

    def test_predeclared_training_domain(self):
        tasks=diagnostic_tasks();self.assertEqual(len(tasks),48)
        self.assertEqual({t['config']['seed'] for t in tasks},set(range(8))|{15,23,25,26})
        self.assertTrue(all(t['seed_role'].startswith('TRAIN') for t in tasks))


if __name__=='__main__':unittest.main()
