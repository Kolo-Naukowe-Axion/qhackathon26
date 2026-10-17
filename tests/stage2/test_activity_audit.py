"""Boundary and physical-accounting tests for observed mechanism reports."""
from copy import deepcopy
import unittest

from stage2.activity_audit import audit, machine_windows, buffer_activity, union_length
from stage2.check import check_trace
from stage2.spec import build
from stage2.advanced import AdvancedFactory


class ActivityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trace = AdvancedFactory(build(orders=3, horizon=2880, seed=0),
            dict(wip_limit=4, mode='standard', lease_calibration=True, worker_calendar=True, preposition=False)).run()

    def test_union_is_not_sum_and_boundary_touch_is_disjoint(self):
        self.assertEqual(union_length([(0,5),(2,8),(8,10),(20,20),(25,24)]),10)

    def test_batch_blocks_until_last_physical_pickup_and_missing_pickup_until_horizon(self):
        trace = dict(horizon_ticks=20, operations=[dict(kind='process', machine_id='H1', start=1,end=5,unit_ids=['a','b']),
            dict(kind='process',machine_id='H2',start=7,end=10,unit_ids=['c'])], moves=[
            dict(kind='transport',entity_type='part',unit_id='a',**{'from':'H1'},pickup_tick=6),
            dict(kind='transport',entity_type='part',unit_id='b',**{'from':'H1'},pickup_tick=9),
            dict(kind='transport',entity_type='tool',unit_id='c',**{'from':'H2'},pickup_tick=11)])
        processing,blocked=machine_windows(trace)
        self.assertEqual(blocked['H1'],[(5,9)])
        self.assertEqual(blocked['H2'],[(10,20)])
        self.assertEqual(processing['H1'],[(1,5)])

    def test_commitments_beyond_execution_are_clipped_without_premature_output(self):
        trace=dict(horizon_ticks=8,operations=[dict(kind='process',machine_id='T1',start=4,end=12,unit_ids=['a'])],moves=[])
        processing,blocked=machine_windows(trace)
        self.assertEqual(processing['T1'],[(4,8)])
        self.assertEqual(blocked['T1'],[])

    def test_buffer_reserved_from_dispatch_not_physical_arrival_and_assembly_consumes_parents(self):
        trace=dict(horizon_ticks=20,instance=dict(machines=[dict(id='A1',input_capacity=3)]),
            operations=[dict(kind='process',machine_id='A1',unit_ids=['pump'],parent_unit_ids=['a','b','c'],start=12)],
            moves=[dict(kind='transport',entity_type='part',unit_id=uid,to='A1',start=start,drop_tick=start+4)
                   for uid,start in [('a',0),('b',2),('c',4)]])
        result=buffer_activity(trace)['A1']
        self.assertEqual(result,dict(capacity=3,max_reserved_or_present=3,full_ticks=8))

    def test_real_trace_worker_attendance_matches_explicit_intervals_and_excludes_walks(self):
        result=audit(self.trace)
        for worker in self.trace['instance']['workers']:
            wid=worker['id']
            intervals=[(row['start'],min(row['end'],self.trace['horizon_ticks'])) for op in self.trace['operations']
                       for row in op.get('worker_intervals', [dict(worker_id=w,start=op['start'],end=op['end'])
                                                              for w in op['worker_ids']]) if row['worker_id']==wid]
            self.assertEqual(result['worker_attendance_ticks'][wid],sum(b-a for a,b in intervals))
            self.assertEqual(result['worker_occupied_ticks'][wid],
                result['worker_attendance_ticks'][wid]+result['worker_walk_ticks'][wid])
        self.assertTrue(all(row['output_blocking_overlap_ticks']==0 for row in result['machine_activity'].values()))
        self.assertTrue(all(row['max_reserved_or_present']<=row['capacity'] for row in result['buffer_activity'].values()))
        self.assertGreater(result['worker_walks'],0)

    def test_invalid_direct_same_machine_continuation_is_rejected_not_reported_as_waiting(self):
        trace=deepcopy(self.trace)
        first=trace['operations'][0]
        # Force another operation to start while the first output is still held.
        duplicate=deepcopy(first);duplicate.update(id='ILLEGAL',start=first['end'],end=first['end']+first['processing_ticks'])
        duplicate['worker_intervals']=[dict(v,start=v['start']+first['processing_ticks'],end=v['end']+first['processing_ticks'])
                                      for v in duplicate['worker_intervals']]
        trace['operations'].append(duplicate)
        checked=check_trace(trace)
        self.assertFalse(checked['valid'])
        self.assertIn('machine_blocking',{issue['code'] for issue in checked['issues']})
        with self.assertRaises(ValueError):audit(trace)

    def test_inventory_minimum_uses_releases_and_real_delivery_not_requested_orders(self):
        result=audit(self.trace)
        stock=dict(self.trace['instance']['raw_stock_units']);minimum=dict(stock)
        for event in self.trace['events']:
            if event['type']=='release':
                stock[event['recipe']]-=1;minimum[event['recipe']]=min(minimum[event['recipe']],stock[event['recipe']])
            if event['type']=='delivery':
                for recipe,count in event['contents'].items():stock[recipe]+=count
        self.assertEqual(result['minimum_observed_raw_stock'],minimum)
        self.assertEqual(result['terminal_raw_stock'],stock)

    def test_checked_partial_trace_uses_execution_horizon_and_committed_attendance(self):
        trace=deepcopy(self.trace);horizon=200
        trace['horizon_ticks']=horizon;trace.pop('metrics',None)
        for key in ('operations','moves','worker_moves'):
            trace[key]=[row for row in trace[key] if row['start']<horizon]
        trace['events']=[row for row in trace['events'] if row['tick']<=horizon]
        trace['energy']=trace['energy'][:horizon]
        result=audit(trace)
        self.assertEqual(result['horizon_ticks'],horizon)
        self.assertGreater(result['production_operations'],result['completed_production_operations'])
        self.assertTrue(all(row['production_ticks']+row['output_blocked_ticks']<=horizon
                            for row in result['machine_activity'].values()))
        self.assertTrue(all(ticks<=horizon for ticks in result['worker_occupied_ticks'].values()))


if __name__=='__main__':unittest.main()
