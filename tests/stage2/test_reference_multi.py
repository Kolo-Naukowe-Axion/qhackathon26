"""Matched BOM, aggregate scope and exported multi-pump witness falsification."""
from copy import deepcopy
import importlib.util
import unittest

from stage2.reference_multi import make_multi,activities,validate_scope,to_trace,schedule_from_trace,resource_bounds,compare,solve
from stage2.engine import run
from stage2.check import check_trace


class MultiReferenceScopeTests(unittest.TestCase):
    def test_activity_graph_has_each_orders_own_three_parent_join(self):
        for n in (1,2,3,4):
            instance=make_multi(n,1);validate_scope(instance);ops,moves=activities(instance)
            self.assertEqual((len(ops),len(moves)),(16*n,19*n))
            self.assertEqual(len({op['id']for op in ops}),16*n)
            self.assertEqual(len({move['id']for move in moves}),19*n)
            for order in instance['orders']:
                incoming=[m for m in moves if m['target_op']==f'{order["id"]}/pump/1/op0']
                self.assertEqual(len(incoming),3)
                self.assertEqual({m['unit_id']for m in incoming},{f'{order["id"]}/{r}/1'for r in ('housing','rotor','flange')})
            self.assertGreater(instance['day_ticks'],instance['horizon_ticks'])

    def test_aggregate_omitted_resource_limits_and_bom_changes_are_rejected(self):
        changes=[lambda i:i['tools'][2].update(life=15),
            lambda i:i['maintenance'].update(wear_limit=70),
            lambda i:i['raw_stock_units'].update(housing=1),
            lambda i:i['units'][0].update(order_id='P02'),
            lambda i:i['orders'][1].update(family='alloy_B'),
            lambda i:i.update(day_ticks=300),
            lambda i:i['reference_scope'].update(standalone_empty_agv_actions=True),
            lambda i:i['quality'].update(wear_risk_coefficient=.01),
            lambda i:i['transport'].update(load_ticks=2)]
        for change in changes:
            with self.subTest(change=change):
                instance=make_multi(2,1);change(instance)
                with self.assertRaises(ValueError):validate_scope(instance)
        for n in (0,5,True):
            with self.assertRaises(ValueError):make_multi(n)

    def test_physical_export_preserves_all_orders_and_rejects_parent_swaps(self):
        instance=make_multi(3,1);ops,moves=activities(instance)
        heuristic=run(instance,{'wip_limit':1,'mode':'standard'})
        exported=to_trace(instance,ops,moves,schedule_from_trace(instance,ops,moves,heuristic))
        validation=check_trace(exported)
        self.assertTrue(validation['valid'],validation['issues'])
        self.assertTrue(validation['all_orders_fulfilled'])
        self.assertEqual(len(validation['metrics']['delivery_ticks']),3)
        self.assertEqual(len([event for event in exported['events']if event['type']=='consume']),9)
        assemblies=[op for op in exported['operations']if op['process']=='ASSEMBLY']
        for op in assemblies:
            self.assertEqual({uid.split('/')[0]for uid in op['parent_unit_ids']},{op['order_id']})
        broken=deepcopy(exported)
        first=next(op for op in broken['operations']if op['process']=='ASSEMBLY')
        first['parent_unit_ids'][0]='P02/housing/1'
        self.assertFalse(check_trace(broken)['valid'])

    def test_bounds_are_resource_necessary_conditions_not_an_optimality_claim(self):
        n=4;instance=make_multi(n,1,automatic_attendance=False)
        bound=resource_bounds(instance)
        self.assertEqual(bound['worker_attendance_ticks'],65*n)
        self.assertGreater(bound['loaded_transport_and_handling_ticks'],0)
        self.assertIsNone(instance['reference_scope']['flagship_global_gap'])


@unittest.skipUnless(importlib.util.find_spec('ortools'),'OR-Tools is installed in .venv-stage2')
class MultiReferenceCpTests(unittest.TestCase):
    def test_bounded_two_pump_search_keeps_real_status_bound_and_checked_witness(self):
        result=compare(make_multi(2,1),wall_limit=3,deterministic_limit=2,workers=1)
        exact=result['exact']
        self.assertIn(exact['status'],('OPTIMAL','FEASIBLE','UNKNOWN'))
        self.assertEqual(exact['counts']['operations'],32)
        self.assertEqual(exact['counts']['moves'],38)
        self.assertFalse(exact['global_infeasibility_proven'])
        self.assertIsNone(exact['flagship_global_gap'])
        self.assertTrue(exact['incumbent']['complete_operation_move_arc_hint'])
        if exact['status']in ('OPTIMAL','FEASIBLE'):
            self.assertTrue(exact['validation']['valid'],exact['validation']['issues'])
            self.assertEqual(exact['validation']['metrics']['delivered_orders'],2)
            self.assertGreaterEqual(exact['objective_ticks'],exact['best_bound_ticks'])
        if not exact['optimal']:self.assertIsNone(result['comparison']['heuristic_makespan_gap'])

    def test_short_horizon_proves_only_declared_model_infeasible(self):
        result=solve(make_multi(2,15,horizon=120),wall_limit=2,deterministic_limit=1)
        self.assertEqual(result['status'],'INFEASIBLE')
        self.assertTrue(result['model_infeasibility_proven'])
        self.assertFalse(result['global_infeasibility_proven'])
        self.assertIsNone(result['objective_ticks'])


if __name__=='__main__':unittest.main()
