import unittest
from copy import deepcopy

from stage2.check import check_trace,check_paired_causality
from stage2.static_control import GuardedCompletionFactory,policies,tasks,validate_tasks,summarize
from stage2.recovery_routing import BASE_WEIGHTS
from stage2.spec import build


class StrongStaticControlTests(unittest.TestCase):
    def test_exact_factorial_and_guarded_no_reward_domain(self):
        ps=policies();self.assertEqual(len(ps),288)
        self.assertEqual([sum(p['config']['orders']==n for p in ps) for n in (12,16,24)],[72,72,144])
        self.assertEqual(sum(p['original_prior'] for p in ps),3)
        for p in ps:
            self.assertTrue(p['solver_options']['maintenance_outage_guard'])
            self.assertFalse(p['solver_options']['completion_policy']['reclaim_dead_slots'])
            self.assertEqual(p['weights']['selector'],'priority')
            self.assertNotIn('reward_mode',p['solver_options'])
            if p['config']['orders']!=24:self.assertFalse(p['weights']['bom_priority'])
        declared=tasks();self.assertEqual(len(declared),9216);validate_tasks(declared)

    def test_protocol_rejects_final_missing_tapes_and_guard_off(self):
        declared=tasks((12,));validate_tasks(declared)
        for mutation in ('final','guard','incomplete'):
            bad=deepcopy(declared)
            if mutation=='final':bad[0]['config']['seed']=10000
            elif mutation=='guard':bad[0]['solver_options']['maintenance_outage_guard']=False
            else:bad.pop()
            with self.assertRaises(ValueError):validate_tasks(bad)

    def test_missing_before_debt_and_known_invalid_not_hidden_by_fallback(self):
        def rows(policy,shipped,tardy):return [dict(config={'orders':12,'seed':seed},policy_id=policy,
            original_prior=policy=='prior',valid=True,weights={},solver_options={},
            metrics={'orders':12,'shipped':shipped,'all_orders_fulfilled':shipped==12,'total_tardiness_ticks':tardy,'total_cost':1}) for seed in range(16)]
        records=rows('prior',12,100)+rows('low-debt',11,0)
        summary,candidates=summarize(records,16);self.assertEqual(candidates[0]['best']['policy_id'],'prior')
        extra=deepcopy(records[0]);extra['config']['seed']=16;extra['valid']=False;records.append(extra)
        summary,candidates=summarize(records,16);self.assertEqual(candidates[0]['best']['policy_id'],'low-debt')
        self.assertFalse(next(x for x in summary if x['policy_id']=='prior')['eligible'])
        self.assertEqual(candidates[0]['original_priors'][0]['all_observed_invalid'],1)

    def test_actual_guarded_completion_composition_and_causality(self):
        traces=[]
        for seed in (0,1,16):
            f=GuardedCompletionFactory(build(2,seed=seed),BASE_WEIGHTS,tool_policy={'mode':'hard'},
                recovery_policy={'enabled':True},maintenance_outage_guard=True,completion_policy={'credit_minutes':270})
            trace=f.run();self.assertTrue(check_trace(trace)['valid']);traces.append(trace)
            self.assertTrue(trace['algorithm_audit']['maintenance_outage_guard']['enabled'])
            self.assertEqual(trace['algorithm_audit']['completion_policy']['policy']['credit_minutes'],270)
        self.assertTrue(check_paired_causality(traces)['valid'])
        p=next(p for p in policies((24,)) if p['weights']['wip_limit']==6 and p['weights']['mode']=='turbo' and
            p['weights']['qa_guard_threshold']==0 and p['solver_options']['completion_policy']['credit_minutes']==270 and
            p['weights']['bom_priority']=='join')
        trace=GuardedCompletionFactory(build(24,seed=4),p['weights'],**p['solver_options']).run()
        self.assertTrue(check_trace(trace)['valid']);self.assertGreater(trace['algorithm_audit']['maintenance_outage_guard']['blocked_eligible_calls'],0)


if __name__=='__main__':unittest.main()
