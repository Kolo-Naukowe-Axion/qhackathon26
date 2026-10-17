"""Falsify the standalone arithmetic bound without changing frozen CP code."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

from stage2.reference_multi import make_multi
from stage2.engine import run
from stage2.check import check_trace

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('multi_bound_certificate',ROOT/'output/stage2-search/multi-reference-bounds/build.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class MultiBoundTests(unittest.TestCase):
    def test_bound_sums_disjoint_intervals_for_all_counts_and_scales(self):
        for n in (1,2,3,4):
            for scale in (1,15):
                result=module.certificate(make_multi(n,scale,automatic_attendance=False))
                self.assertEqual(result['lower_bound_ticks'],65*scale*n+20)
                self.assertEqual(result['components']['four_forced_worker_hall_walks'],8)
                self.assertFalse(result['changes_saved_cp_bound'])

    def test_proof_conditions_reject_automatic_attendance_and_changed_halls(self):
        with self.assertRaisesRegex(ValueError,'throughout'):
            module.certificate(make_multi(2,1))
        instance=make_multi(2,1,automatic_attendance=False)
        instance['machines'][2]['hall']='A'
        with self.assertRaisesRegex(ValueError,'station placement'):
            module.certificate(instance)

    def test_route_and_walk_terms_follow_numerical_instance(self):
        instance=make_multi(2,1,automatic_attendance=False,bridge_ticks=6)
        instance['worker_travel_ticks']=3
        result=module.certificate(instance)
        self.assertEqual(result['components']['last_pump_QA_shipping'],10)
        self.assertEqual(result['components']['four_forced_worker_hall_walks'],12)
        self.assertEqual(result['lower_bound_ticks'],156)

    def test_complete_physical_witnesses_do_not_violate_bound(self):
        for n in (1,2,3,4):
            instance=make_multi(n,15,automatic_attendance=False)
            trace=run(deepcopy(instance),dict(wip_limit=1,mode='standard'))
            checked=check_trace(trace)
            self.assertTrue(checked['valid']);self.assertTrue(checked['all_orders_fulfilled'])
            self.assertGreaterEqual(max(checked['metrics']['delivery_ticks'].values()),module.certificate(instance)['lower_bound_ticks'])

    def test_automatic_prefix_certificate_retains_disjoint_components(self):
        for n in (1,2,3,4):
            instance=make_multi(n,15);result=module.automatic_certificate(instance)
            self.assertEqual(result['lower_bound_ticks'],350*n+68)
            self.assertEqual(result['components']['initial_prefix_without_mandatory_attendance'],54)
            self.assertEqual(result['components']['three_forced_worker_walks_after_first_completion'],6)
            self.assertEqual(result['components']['last_pump_QA_shipping'],8)
            self.assertIn('The first A-to-B walk, which may overlap prefix non-attendance',result['deliberately_excluded'])

    def test_automatic_prefix_assumptions_fail_closed(self):
        changes=[lambda i:i['recipes']['housing'][0].update(base_ticks=59),
            lambda i:i['attendance']['T'].update(ticks=6),
            lambda i:i['attendance']['QA'].update(kind='start',ticks=5),
            lambda i:i['units'][0].update(initial_location='T1'),
            lambda i:i['machines'].append(dict(i['machines'][0],id='T2')),
            lambda i:next(edge for edge in i['graph_edges']if edge['a']=='T1').update(b='RAW_A'),
            lambda i:i['setup_matrix']['alloy_A'].update(alloy_A=1),
            lambda i:i['maintenance'].update(wear_limit=1)]
        for change in changes:
            instance=make_multi(2,15);change(instance)
            with self.assertRaises(ValueError):module.automatic_certificate(instance)
        with self.assertRaises(ValueError):module.automatic_certificate(make_multi(2,1))
        with self.assertRaises(ValueError):module.automatic_certificate(make_multi(2,15,automatic_attendance=False))

    def test_automatic_bound_is_below_retained_exact_and_complete_schedules(self):
        import json
        cases=[('output/stage2-search/tiny-reference-final/automatic/optimal-trace.json',1),
            ('output/stage2-search/multi-reference-600/n2/automatic/cp-trace.json',2),
            ('output/stage2-search/multi-reference-600/n3/automatic/cp-trace.json',3),
            ('output/stage2-search/multi-reference-constructive/n4/trace.json',4)]
        for relative,n in cases:
            trace=json.loads((ROOT/relative).read_text());checked=check_trace(trace)
            self.assertTrue(checked['valid']);self.assertTrue(checked['all_orders_fulfilled'])
            self.assertGreaterEqual(max(checked['metrics']['delivery_ticks'].values()),350*n+68)

    def test_buffer_bom_certificate_counts_one_assembly_per_B_visit(self):
        for n in (1,2,3,4):
            for full in (False,True):
                instance=make_multi(n,15,automatic_attendance=not full);result=module.buffer_bom_certificate(instance)
                self.assertEqual(result['lower_bound_ticks'],975*n+4*n+16 if full else 354*n+64)
                self.assertEqual(result['productive_B_visits_at_least'],n+1)
                self.assertEqual(result['accepted_unconsumed_components_at_most'],4)
                self.assertEqual(result['components_needed_for_two_assemblies'],6)
                self.assertFalse(result['changes_saved_cp_bound'])

    def test_buffer_bom_certificate_rejects_accepted_storage_and_worker_changes(self):
        changes=[lambda i:next(m for m in i['machines']if m['process']=='ASSEMBLY').update(input_capacity=4),
            lambda i:i['machines'].append(dict(next(m for m in i['machines']if m['process']=='QA'),id='QA2')),
            lambda i:next(m for m in i['machines']if m['process']=='QA').update(output_capacity=2),
            lambda i:i['attendance']['QA'].update(kind='start',ticks=5),
            lambda i:i['attendance']['ASSEMBLY'].update(kind='start',ticks=5),
            lambda i:i['units'][0].update(accepted=True),
            lambda i:i.update(initial_accepted_units=['P01/housing/1']),
            lambda i:i['transport'].update(part_routing='arbitrary_temporary_warehousing'),
            lambda i:next(m for m in i['machines']if m['process']=='QA').update(hall='B'),
            lambda i:i.update(output_blocking=False)]
        for full in (False,True):
            for change in changes:
                instance=make_multi(2,15,automatic_attendance=not full);change(instance)
                with self.assertRaises(ValueError):module.buffer_bom_certificate(instance)

    def test_previous_prefix_certificate_history_is_byte_preserved(self):
        import hashlib,json
        history=ROOT/'output/stage2-search/multi-reference-bounds/history-prefix'
        manifest=json.loads((history/'manifest.json').read_text())
        for name,digest in manifest.items():
            self.assertEqual(hashlib.sha256((history/name).read_bytes()).hexdigest(),digest)
        old=json.loads((history/'n4-automatic.json').read_text())
        self.assertEqual(old['lower_bound_ticks'],1468)
        self.assertEqual(old['construction_source_sha256'],manifest['build.py'])


if __name__=='__main__':unittest.main()
