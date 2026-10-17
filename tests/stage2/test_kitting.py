"""Algorithm restrictions only: accepted QA output is never teleported."""
import unittest
from unittest.mock import patch

from stage2.advanced import AdvancedFactory
from stage2.check import check_paired_causality,check_trace
from stage2.kitting import KitFactory,KitToolingFactory,run
from stage2.spec import build
from stage2.tooling import run as tool_run


class KitReservationTests(unittest.TestCase):
    weights=dict(wip_limit=3,mode='standard',lease_calibration=True)

    def test_off_matches_direct_tooling_physics_exactly(self):
        instance=build(2,seed=0);policy=dict(mode='hard')
        expected=tool_run(instance,self.weights,tool_policy=policy)
        actual=run(instance,self.weights,tool_policy=policy,kit_reservation=False)
        for key in ('operations','moves','worker_moves','events','energy','metrics'):
            self.assertEqual(expected[key],actual[key],key)
        self.assertTrue(check_trace(actual)['valid'])

    def ready_factory(self):
        factory=KitFactory(build(5,seed=0),self.weights)
        for part in factory.parts.values():
            if part['recipe']=='housing':part.update(accepted=True,status='waiting',location='QA1',busy=False)
        return factory

    def test_whole_kit_reservations_spread_and_release_only_after_consumption(self):
        factory=self.ready_factory()
        # Isolate the allocation decision from transport/processing. Five first
        # accepted components compete for four complete three-place kit slots.
        with patch.object(AdvancedFactory,'assembly',return_value=None):factory.assembly()
        assignments=factory.pending_kit_assignments()
        self.assertEqual(len(assignments),4)
        for machine in ('A1','A2'):
            self.assertEqual(sum(mid==machine for mid in assignments.values()),2)
        deferred=set(factory.orders)-set(assignments);self.assertEqual(len(deferred),1)
        before=dict(assignments)
        with patch.object(AdvancedFactory,'assembly',return_value=None):factory.assembly()
        self.assertEqual(before,factory.pending_kit_assignments())
        # Successful parent consumption creates a real pump and frees the kit
        # reservation; an earlier unsuccessful assembly must not free it.
        oid=next(iter(assignments));target=assignments[oid]
        for part in factory.parts.values():
            if part['order_id']==oid:part.update(status='consumed',location='CONSUMED',busy=True)
        exemplar=dict(next(p for p in factory.parts.values() if p['order_id']==oid))
        pump_id=oid+'/pump/1';factory.parts[pump_id]=dict(exemplar,id=pump_id,recipe='pump',accepted=False,status='processing',location=target)
        with patch.object(AdvancedFactory,'assembly',return_value=None):factory.assembly()
        after=factory.pending_kit_assignments()
        self.assertNotIn(oid,after)
        self.assertIn(next(iter(deferred)),after)
        self.assertEqual(len(after),4)

    def test_exception_restores_complete_order_dictionary(self):
        factory=self.ready_factory();original=factory.orders
        with patch.object(AdvancedFactory,'assembly',side_effect=RuntimeError('deliberate scheduling failure')):
            with self.assertRaisesRegex(RuntimeError,'deliberate'):factory.assembly()
        self.assertIs(factory.orders,original)
        self.assertEqual(len(factory.orders),5)
        self.assertEqual(len(factory.i['orders']),5)

    def test_full_checker_and_paired_causality(self):
        traces=[run(build(2,seed=seed),self.weights,tool_policy=dict(mode='hard')) for seed in (0,1)]
        for trace in traces:
            self.assertTrue(check_trace(trace)['valid'])
            self.assertTrue(trace['algorithm_audit']['kit_reservation']['history'])
        report=check_paired_causality(traces)
        self.assertTrue(report['valid'],report)

    def test_returned_pump_uses_original_physical_input_capacity(self):
        factory=KitToolingFactory(build(2,seed=16),self.weights,tool_policy=dict(mode='hard'))
        # Six physically waiting components fill A1. Virtual reservations cannot
        # authorize a seventh physical arrival, including a repaired pump.
        for part in factory.parts.values():part.update(status='waiting',location='A1',busy=False,accepted=True)
        original=next(iter(factory.parts.values()))
        pump=dict(original,id='P01/pump/1',recipe='pump',location='QA1',accepted=False,busy=False)
        factory.parts[pump['id']]=pump
        self.assertEqual(factory.input_count('A1'),6)
        self.assertFalse(factory.move(pump['id'],'A1'))
        self.assertEqual(factory.reserved['A1'],0)
        self.assertEqual(factory.trace['moves'],[])
        # A genuine development tape exercises final-pump QA failure, physical
        # return transport and repair rather than relying on this unit fixture.
        trace=run(build(2,seed=16),self.weights,tool_policy=dict(mode='hard'))
        self.assertTrue(any(e['type']=='repair' and e['unit_id']=='P01/pump/1' for e in trace['events']))
        self.assertTrue(any(m.get('unit_id')=='P01/pump/1' and m['from'].startswith('QA') and m['to'] in ('A1','A2') for m in trace['moves']))
        self.assertTrue(check_trace(trace)['valid'])


if __name__=='__main__':unittest.main()
