"""Portable-home restrictions, reservation preservation and replay audits."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from stage2.tooling import ToolingFactory,run,source_hashes
from stage2.advanced import AdvancedFactory
from stage2.check import check_trace,check_paired_causality
from stage2.spec import build


class ToolingTests(unittest.TestCase):
    def factory(self,mode='soft',**kwargs):
        f=ToolingFactory(build(orders=2),dict(wip_limit=4,lease_calibration=True),
            tool_policy=dict(mode=mode,**kwargs));f.admitted={'P01','P02'}
        return f

    def place(self,f,uid,mid,step):
        p=f.parts[uid];p.update(status='waiting',location=mid,step=step,busy=False);return p

    def test_off_exactly_matches_existing_advanced_actions(self):
        i=build(orders=3,horizon=2880,seed=0);before=deepcopy(i);weights=dict(wip_limit=4,lease_calibration=True)
        original=AdvancedFactory(i,weights).run();trace=run(i,weights,tool_policy=dict(mode='off'))
        for field in ['operations','moves','worker_moves','events','energy','metrics']:
            self.assertEqual(trace[field],original[field],field)
        self.assertEqual(i,before)

    def test_soft_home_refuses_to_steal_tool_from_waiting_home_input(self):
        f=self.factory();p=self.place(f,'P01/housing/1','F1',1)
        self.place(f,'P02/housing/1','F2',1)
        f.tools['mill1'].update(location='F1',busy=100)
        f.tools['mill2'].update(location='F2',busy=0)
        self.assertNotIn('mill2',f.tool_view(f.machines['F1'],[p],'standard'))
        self.assertFalse(f.process(f.machines['F1'],[p],prepare_only=True))
        self.assertFalse(f.trace['moves'])
        self.assertIn('mill2',f.tools)

    def test_soft_home_can_borrow_when_home_has_no_known_demand(self):
        f=self.factory();p=self.place(f,'P01/housing/1','F1',1)
        f.tools['mill1'].update(location='F1',busy=100)
        f.tools['mill2'].update(location='F2',busy=0)
        self.assertIn('mill2',f.tool_view(f.machines['F1'],[p],'standard'))
        self.assertFalse(f.process(f.machines['F1'],[p],prepare_only=True))
        self.assertEqual(f.trace['moves'][-1]['unit_id'],'mill2')
        self.assertEqual(f.trace['moves'][-1]['to'],'F1')
        self.assertEqual(len(f.tools),5)

    def test_existing_reserved_foreign_delivery_is_honored(self):
        f=self.factory('hard');p=self.place(f,'P01/housing/1','F1',1)
        f.tools['mill2'].update(location='F1',reserved_for=p['id'])
        f.tools['mill1']['busy']=100
        self.assertIn('mill2',f.tool_view(f.machines['F1'],[p],'standard'))
        offer=f.process(f.machines['F1'],[p],preview=True)
        self.assertTrue(offer);self.assertEqual(offer['tool_ids'],['mill2'])

    def test_incoming_preposition_reservation_protects_home(self):
        f=self.factory();p=self.place(f,'P01/housing/1','F1',1)
        incoming=f.parts['P02/housing/1'];incoming.update(status='processing',location='T1',step=0,
            moving=True,target_location='F2')
        f.tools['mill1']['busy']=100;f.tools['mill2']['location']='F2'
        self.assertNotIn('mill2',f.tool_view(f.machines['F1'],[p],'standard'))

    def test_exceptions_restore_tool_and_machine_membership(self):
        f=self.factory('hard');p=self.place(f,'P01/housing/1','F1',1)
        tools=f.tools;machines=f.machines
        with patch.object(AdvancedFactory,'process',side_effect=RuntimeError('synthetic')):
            with self.assertRaises(RuntimeError):f.process(f.machines['F1'],[p],preview=True)
        self.assertIs(f.tools,tools);self.assertEqual(len(f.tools),5)
        with patch.object(AdvancedFactory,'choose_machine',side_effect=RuntimeError('synthetic')):
            with self.assertRaises(RuntimeError):f.choose_machine(p)
        self.assertIs(f.machines,machines);self.assertEqual(len(f.machines),15)

    def test_hard_routing_does_not_send_parts_to_station_without_any_tool(self):
        f=self.factory('hard',kinds=['mill']);p=self.place(f,'P01/housing/1','T1',1)
        f.machines['F1']['busy']=1000;f.machines['F2']['busy']=1000
        self.assertIn(f.choose_machine(p)['id'],['F1','F2'])
        f.tool_policy['mode']='off';self.assertEqual(f.choose_machine(p)['id'],'F3')

    def test_hard_homes_are_algorithm_restrictions_not_mounted_resources(self):
        i=build(orders=3,horizon=2880,seed=1);before=deepcopy(i)
        trace=run(i,dict(wip_limit=4,lease_calibration=True),tool_policy=dict(mode='hard'))
        self.assertEqual(i,before);self.assertEqual(trace['instance'],before)
        self.assertTrue(any(m.get('entity_type')=='tool' for m in trace['moves']))
        self.assertTrue(check_trace(trace)['valid'])
        homes=trace['provenance']['tool_assignment']['homes']
        for op in trace['operations']:
            if op['kind']=='process':
                for tid in op['tool_ids']:self.assertEqual(op['machine_id'],homes[tid])

    def test_paid_rental_home_can_receive_parts_before_delivery(self):
        f=self.factory('hard');f.lease_requested=False
        self.assertFalse(f.station_has_home(f.machines['QA2'],'calibration'))
        f.lease_requested=True
        self.assertTrue(f.station_has_home(f.machines['QA2'],'calibration'))
        self.assertNotIn('calibration_lease',f.tools)

    def test_separate_tool_kinds_leave_other_process_choices_unchanged(self):
        f=self.factory('hard',kinds=['mill']);p=self.place(f,'P01/flange/1','S1',1)
        self.assertIs(f.tool_view(f.machines['S1'],[p],'standard'),f.tools)

    def test_paired_tapes_and_specialist_combination_are_independently_valid(self):
        for mode,specialist in [('soft',False),('hard',False),('soft',True)]:
            with self.subTest(mode=mode,specialist=specialist):
                traces=[run(build(orders=3,horizon=2880,seed=seed),dict(wip_limit=4,
                    lease_calibration=True,qa_guard_threshold=2),tool_policy=dict(mode=mode),specialist=specialist) for seed in range(4)]
                for trace in traces:
                    checked=check_trace(trace);self.assertTrue(checked['valid'],checked['issues'])
                causal=check_paired_causality(traces);self.assertTrue(causal['valid'],causal['issues'])

    def test_sources_remain_unchanged(self):
        before=source_hashes();run(build(orders=1,horizon=1200));self.assertEqual(before,source_hashes())


if __name__=='__main__':unittest.main()
