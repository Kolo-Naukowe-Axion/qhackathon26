from copy import deepcopy
import unittest
from unittest.mock import patch

from stage2 import mpc,recovery_mpc
from stage2.kit_recovery import AdmissionRecoveryFactory
from stage2.check import check_trace
from stage2.spec import build

WEIGHTS=dict(wip_limit=8,mode='standard',due=.25,remaining=-4.,family=24.,setup=10,
    lease_calibration=True,selector='priority',policy_seed=0,tool_distance=0,
    qa_guard_threshold=4,worker_calendar=True,preposition=False,admission_rule='family')


class RecoveryMPCTests(unittest.TestCase):
    def test_maintenance_guard_and_history_survive_continuation(self):
        from stage2.maintenance_guard import AdmissionMaintenanceGuardFactory
        factory=AdmissionMaintenanceGuardFactory(build(1,seed=0),WEIGHTS,tool_policy=dict(mode='hard'),
            recovery_policy=dict(enabled=True),maintenance_outage_guard=True)
        factory.maintenance_guard_spans.append(dict(machine_id='F2',first_tick=1,last_tick=3))
        future=mpc.continuation(factory,0,{},19,boundary_processed=False)
        self.assertTrue(future.maintenance_outage_guard)
        self.assertIs(future.admitted.factory,future)
        future.maintenance_guard_spans[0]['last_tick']=4
        self.assertEqual(factory.maintenance_guard_spans[0]['last_tick'],3)

    def test_actual_guarded_rollout_rejects_maintenance_during_revealed_outage(self):
        from stage2.maintenance_guard import run
        instance=build(24,seed=4);weights=dict(WEIGHTS,wip_limit=6,mode='turbo',qa_guard_threshold=0,
            due=1.,family=0.,tool_distance=8)
        options=dict(tool_policy=dict(mode='hard'),recovery_policy=dict(enabled=True),
            kit_reservation=False,routing_policy=dict(eta_processes=[],free_buffer_processes=[]),
            maintenance_outage_guard=True)
        expected=run(instance,weights,admission=True,**options)
        actual=recovery_mpc.run(instance,weights,actions=[],scenarios=1,interval=5760,
            physical_check_futures=True,**options)
        self.assertTrue(actual['validation']['valid'],actual['validation']['issues'])
        self.assertTrue(actual['algorithm_audit']['maintenance_outage_guard']['enabled'])
        self.assertTrue(actual['planning']['maintenance_outage_guard'])
        for key in ('operations','moves','worker_moves','events','energy','metrics'):
            self.assertEqual(actual[key],expected[key],key)
        self.assertTrue(all(c['valid'] for r in actual['planning']['decisions'][0]['candidates'] for c in r['scenario_checks']))

    def test_identical_tape_continuation_reproduces_original_factory_and_keeps_admission_link(self):
        factory=AdmissionRecoveryFactory(build(2,seed=0),WEIGHTS,tool_policy=dict(mode='hard'),
            recovery_policy=dict(enabled=True))
        # This boundary has not processed tick zero; no duplicate completion or
        # revelation processing is omitted in this identity regression.
        future=mpc.continuation(factory,0,{},0,boundary_processed=False)
        self.assertIsInstance(future,AdmissionRecoveryFactory)
        self.assertIs(future.admitted.factory,future)
        expected=factory.run();actual=mpc.resume(future)
        for key in ('operations','moves','worker_moves','events','energy','metrics'):
            self.assertEqual(expected[key],actual[key],key)
        self.assertTrue(check_trace(actual)['valid'])

    def test_recovery_lock_and_commitments_are_deep_copied(self):
        factory=AdmissionRecoveryFactory(build(2,seed=0),WEIGHTS,tool_policy=dict(mode='hard'),
            recovery_policy=dict(enabled=True))
        factory.recovery_active=dict(order_id='P01',started_tick=0,plan=[],executed_legs=[])
        factory.reserved['A1']=2
        future=mpc.continuation(factory,0,{},912)
        self.assertEqual(future.recovery_active,factory.recovery_active)
        self.assertEqual(future.reserved['A1'],2)
        future.recovery_active['executed_legs'].append(dict(unit_id='probe'))
        self.assertEqual(factory.recovery_active['executed_legs'],[])
        self.assertEqual(factory.i['seed'],0);self.assertEqual(future.i['seed'],912)

    def test_explicit_scoped_routing_continuations_keep_runtime_class_and_policy(self):
        from stage2.recovery_routing import AdmissionRecoveryRoutingFactory
        factory=AdmissionRecoveryRoutingFactory(build(1,seed=0),WEIGHTS,tool_policy=dict(mode='hard'),
            routing_policy=dict(eta_processes=['QA']),recovery_policy=dict(enabled=True))
        future=mpc.continuation(factory,0,{},19,boundary_processed=False)
        self.assertIsInstance(future,AdmissionRecoveryRoutingFactory)
        self.assertEqual(future.routing_policy['eta_processes'],['QA'])
        future.routing_policy['eta_processes'].append('F')
        self.assertEqual(factory.routing_policy['eta_processes'],['QA'])

    def test_actual_rollout_is_checked_and_extended_sources_are_guarded(self):
        instance=build(1,seed=0)
        trace=recovery_mpc.run(instance,WEIGHTS,actions=[],scenarios=1,interval=5760,
            tool_policy=dict(mode='hard'),recovery_policy=dict(enabled=True),physical_check_futures=True)
        self.assertTrue(trace['validation']['valid'],trace['validation'])
        self.assertTrue(trace['metrics']['all_orders_fulfilled'])
        plan=trace['planning'];self.assertEqual(len(plan['decisions']),1)
        self.assertIn('stage2/kit_recovery.py',plan['source_hashes'])
        self.assertTrue(all(c['valid'] for r in plan['decisions'][0]['candidates'] for c in r['scenario_checks']))
        self.assertNotIn(instance['seed'],plan['decisions'][0]['scenario_seeds'])
        factory=AdmissionRecoveryFactory(instance,WEIGHTS,tool_policy=dict(mode='hard'))
        controller=recovery_mpc.GuardedRolloutController(factory,actions=[],scenarios=1)
        with patch.object(recovery_mpc,'hashes',return_value={}):
            with self.assertRaisesRegex(RuntimeError,'source changed'):controller({})


if __name__=='__main__':unittest.main()
