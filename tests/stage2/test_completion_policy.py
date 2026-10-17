import unittest
from copy import deepcopy
from unittest.mock import patch

from stage2.admission import AdmissionSet
from stage2.check import check_trace,check_paired_causality
from stage2.completion_policy import AdmissionCompletionFactory,ReclaimAdmissionSet,diagnostic_tasks,run
from stage2.recovery_routing import BASE_WEIGHTS,run as frozen_run
from stage2.spec import build


class CompletionPolicyTests(unittest.TestCase):
    def test_off_exact_physical_equivalence(self):
        instance=build(2,seed=0);options=dict(admission=True,tool_policy={'mode':'hard'},recovery_policy={'enabled':True})
        expected=frozen_run(instance,BASE_WEIGHTS,**options);actual=run(instance,BASE_WEIGHTS,**options)
        for key in ('operations','moves','worker_moves','events','energy','metrics'):self.assertEqual(expected[key],actual[key],key)

    def test_credit_follows_only_actual_consumed_lineage_and_public_time_units(self):
        factory=AdmissionCompletionFactory(build(2,seed=0),BASE_WEIGHTS,completion_policy={'credit_minutes':270})
        factory.run();pump=factory.parts['P01/pump/1'];pump['status']='waiting'
        self.assertEqual(factory.completion_credit(pump),4.5)
        factory.i['seed']=987654;self.assertEqual(factory.completion_credit(pump),4.5)
        fake=deepcopy(pump);fake['id']='P01/fake-pump/1';self.assertEqual(factory.completion_credit(fake),0)
        uid=factory.pump_lineage()[pump['id']][0];factory.parts[uid]['status']='waiting'
        self.assertEqual(factory.completion_credit(pump),0)

    def test_reclaim_releases_only_virtual_slot_and_never_readmits_dead_order(self):
        factory=AdmissionCompletionFactory(build(2,seed=0),dict(BASE_WEIGHTS,wip_limit=1),
            completion_policy={'reclaim_dead_slots':True})
        factory.t=120;set.add(factory.admitted,'P01')
        factory.parts['P01/pump/1']=dict(id='P01/pump/1',order_id='P01',recipe='pump',status='scrap')
        original_orders=factory.orders;original_parts=set(factory.parts)
        factory.admitted.difference_update([]);self.assertNotIn('P01',factory.admitted)
        self.assertTrue(factory.retired_orders['P01']['blocked_admission_evidence'])
        factory.admitted.update(['P01']);self.assertEqual(set(factory.admitted),{'P02'})
        self.assertIs(factory.orders,original_orders);self.assertIn('P01',factory.orders);self.assertEqual(set(factory.parts),original_parts)
        copied=deepcopy(factory);self.assertIs(copied.admitted.factory,copied);self.assertIsInstance(copied.admitted,ReclaimAdmissionSet)
        copied.retired_orders['P01']['tick']=-1;self.assertEqual(factory.retired_orders['P01']['tick'],120)

    def test_exhausted_replacement_requires_observed_failure_and_no_live_pump(self):
        factory=AdmissionCompletionFactory(build(2,seed=0),BASE_WEIGHTS,completion_policy={'reclaim_dead_slots':True})
        original=factory.parts['P01/housing/1'];original['status']='scrap'
        replacement=deepcopy(original);replacement.update(id=original['id']+'~r1',status='unreleased',replacement=1)
        factory.parts[replacement['id']]=replacement
        self.assertNotIn('P01',factory.observed_unrecoverable_orders())
        replacement['status']='scrap';factory._dead_key=None
        self.assertIn('P01',factory.observed_unrecoverable_orders())
        factory.parts['P01/pump/1']=dict(id='P01/pump/1',order_id='P01',recipe='pump',status='waiting')
        self.assertNotIn('P01',factory.observed_unrecoverable_orders())

    def test_temporary_admission_filter_restores_orders_on_exception(self):
        factory=AdmissionCompletionFactory(build(2,seed=0),BASE_WEIGHTS,completion_policy={'reclaim_dead_slots':True})
        original=factory.orders
        with patch.object(AdmissionSet,'update',side_effect=RuntimeError('injected')):
            with self.assertRaises(RuntimeError):factory.admitted.update([])
        self.assertIs(factory.orders,original)

    def test_actual_credit_reclaim_physical_and_causal(self):
        traces=[]
        for seed in (0,1,16):
            trace=run(build(2,seed=seed),BASE_WEIGHTS,admission=True,tool_policy={'mode':'hard'},
                recovery_policy={'enabled':True},completion_policy={'credit_minutes':270,'reclaim_dead_slots':True})
            self.assertTrue(check_trace(trace)['valid']);traces.append(trace)
        self.assertTrue(check_paired_causality(traces)['valid'])

    def test_real_seed15_reclaim_has_no_blocked_slot_and_keeps_debt(self):
        instance=build(12,seed=15);options=dict(admission=True,tool_policy={'mode':'hard'},recovery_policy={'enabled':True})
        original=frozen_run(instance,BASE_WEIGHTS,**options)
        actual=run(instance,BASE_WEIGHTS,**options,completion_policy={'reclaim_dead_slots':True})
        self.assertTrue(check_trace(actual)['valid']);self.assertEqual(actual['metrics']['orders'],14)
        for key in ('operations','moves','worker_moves','events','energy','metrics'):self.assertEqual(original[key],actual[key],key)
        retired=actual['algorithm_audit']['completion_policy']['retired_orders']['P11']
        self.assertFalse(retired['blocked_admission_evidence']);self.assertEqual(retired['occupied_before'],3)

    def test_bounded_declared_structural_ablation(self):
        tasks=diagnostic_tasks();self.assertEqual(len(tasks),100)
        self.assertEqual({t['solver_options']['completion_policy']['credit_minutes'] for t in tasks},{0,270})
        self.assertTrue(all(t['config']['seed'] in set(range(8))|{15} for t in tasks))
        self.assertTrue(all(t['config']['orders']==12 for t in tasks if t['config']['seed']==15))


if __name__=='__main__':unittest.main()
