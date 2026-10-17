import unittest
from unittest.mock import patch

from stage2.check import check_trace,check_paired_causality
from stage2.kitting import run as kit_run
from stage2.routing import RoutingFactory,run
from stage2.spec import build
from stage2.tooling import ToolingMixin


class ScopedRoutingTests(unittest.TestCase):
    weights=dict(wip_limit=3,mode='standard',lease_calibration=True,worker_calendar=True,
        preposition=False,qa_guard_threshold=0,admission_rule='family')

    def test_disabled_scope_preserves_existing_physical_policy_even_global_flags(self):
        weights=dict(self.weights,routing_estimate_finish=True,routing_free_buffers=True)
        instance=build(2,seed=0);policy=dict(mode='hard')
        expected=kit_run(instance,weights,tool_policy=policy,specialist=True,admission=True)
        actual=run(instance,weights,tool_policy=policy,admission=True,routing_policy=None)
        for key in ('operations','moves','worker_moves','events','energy','metrics'):
            self.assertEqual(expected[key],actual[key],key)
        self.assertTrue(check_trace(actual)['valid'])

    def test_QA_only_scope_and_exception_restore_original_weight_identity(self):
        factory=RoutingFactory(build(2,seed=0),dict(self.weights,routing_estimate_finish=True),
            routing_policy=dict(eta_processes=['QA'],free_buffer_processes=['QA']),tool_policy=dict(mode='hard'))
        part=next(iter(factory.parts.values()));original=factory.weights;before=dict(original);seen=[]
        def observe(obj,unit):
            process=obj.next_step(unit)['process'];seen.append((process,obj.weights['routing_estimate_finish'],obj.weights['routing_free_buffers']))
            self.assertIsNot(obj.weights,original)
            if process=='QA':raise RuntimeError('deliberate route failure')
        with patch.object(ToolingMixin,'choose_machine',observe):
            factory.choose_machine(part)
            part['step']=next(i for i,s in enumerate(factory.i['recipes'][part['recipe']]) if s['process']=='QA')
            with self.assertRaisesRegex(RuntimeError,'deliberate'):factory.choose_machine(part)
        self.assertEqual(seen,[('T',False,False),('QA',True,True)])
        self.assertIs(factory.weights,original);self.assertEqual(factory.weights,before)

    def test_three_actual_tapes_are_physically_checked_and_prefix_causal(self):
        policy=dict(eta_processes=['QA'],free_buffer_processes=['QA'])
        traces=[run(build(2,seed=seed),self.weights,tool_policy=dict(mode='hard'),
            admission=True,routing_policy=policy) for seed in (0,1,16)]
        for trace in traces:
            self.assertTrue(check_trace(trace)['valid'])
            audit=trace['algorithm_audit']['scoped_routing']
            self.assertGreater(audit['eta_calls'].get('QA',0),0)
            self.assertEqual(set(audit['eta_calls']),{'QA'})
        report=check_paired_causality(traces)
        self.assertTrue(report['valid'],report)


if __name__=='__main__':unittest.main()
