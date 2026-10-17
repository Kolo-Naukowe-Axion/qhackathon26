"""Equivalent resource orders, known exact values, and source-domain guards."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from stage2.reference_multi import make_multi, activities, solve as original_solve
from stage2.reference_polish import build_model, checked_witness, normalize_future_reservations, precedence, solve

ROOT = Path(__file__).resolve().parents[2]


class PolishedReferenceTests(unittest.TestCase):
    def test_bom_ancestry_contains_all_parents_but_not_other_orders(self):
        ops, moves = activities(make_multi(2, 1))
        before = precedence(ops, moves)
        assembly = before['P01/pump/1/op0']
        self.assertTrue(all(f'P01/{r}/1/op0' in assembly for r in ('housing','rotor','flange')))
        self.assertFalse(any(name.startswith('P02/') for name in assembly))

    def test_preserved_1541_witness_fits_all_new_constraints(self):
        from ortools.sat.python import cp_model
        path = ROOT/'output/stage2-search/final-independent-audit/reference-2h-6117555/derived-normalized-witness.json'
        trace = json.loads(path.read_text())
        instance = trace['instance']
        model, v = build_model(instance, trace)
        for op in trace['operations']:
            model.add(v['starts'][op['id']] == op['start'])
        # Match movement IDs semantically; exporters may order their rows by path.
        lookup = {(m['unit_id'],m['from'],m['to']):m for m in trace['moves']}
        for move in v['movements']:
            row = lookup[move['unit_id'],move['from'],move['to']]
            for variables, field in ((v['dispatch'],'start'), (v['pickup'],'pickup_tick'), (v['drop'],'drop_tick')):
                model.add(variables[move['id']] == row[field])
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10
        solver.parameters.num_search_workers = 1
        status = solver.solve(model)
        self.assertEqual(status, cp_model.OPTIMAL)
        self.assertEqual(solver.objective_value, 1541)
        self.assertGreater(v['pruned_agv_arcs'], 0)

    def test_independent_formulations_agree_on_compressed_one_pump(self):
        instance = make_multi(1,1)
        original = original_solve(instance, wall_limit=15,deterministic_limit=15,workers=1)
        polished = solve(instance,wall_limit=15,workers=1)
        self.assertTrue(original['optimal'])
        self.assertTrue(polished['optimal'])
        self.assertEqual(polished['objective_ticks'], original['objective_ticks'])
        self.assertTrue(polished['physical_check']['valid'])
        self.assertTrue(polished['identity_check']['valid'])

    def test_infeasible_horizon_never_emits_a_witness(self):
        result = solve(make_multi(2,15,horizon=120),wall_limit=2,workers=1)
        self.assertEqual(result['status'], 'INFEASIBLE')
        self.assertNotIn('trace', result)
        self.assertIsNone(result['flagship_global_gap'])

    def test_worker_neighborhood_bound_is_not_a_global_bound(self):
        path = ROOT/'output/stage2-search/final-independent-audit/reference-2h-6117555/derived-normalized-witness.json'
        trace=json.loads(path.read_text())
        result=solve(trace['instance'],incumbent=trace,wall_limit=5,workers=1,worker_block_size=1)
        self.assertFalse(result['optimal'])
        self.assertIsNone(result['best_bound_ticks'])
        self.assertTrue(result['neighborhood_optimal'])
        self.assertEqual(result['objective_ticks'],1541)
        self.assertEqual(result['neighborhood_lower_bound_ticks'],1541)

    def test_parked_birth_normalization_changes_no_physical_leg(self):
        path = ROOT/'output/stage2-search/final-independent-audit/reference-2h-6117555/derived-normalized-witness.json'
        trace = json.loads(path.read_text())
        original = deepcopy(trace)
        move = next(m for m in trace['moves'] if m['id']=='move74')
        move['start'] = 1382
        result, changes = normalize_future_reservations(trace)
        self.assertEqual(result, original)
        self.assertEqual(len(changes), 1)
        self.assertEqual(move['start'], 1382)
        checked_witness(trace['instance'], result)

    def test_changed_instance_and_nonparked_prebirth_action_fail_closed(self):
        path = ROOT/'output/stage2-search/final-independent-audit/reference-2h-6117555/derived-normalized-witness.json'
        trace = json.loads(path.read_text())
        instance = deepcopy(trace['instance']);instance['raw_stock_units']['housing'] += 1
        with self.assertRaises(ValueError):
            checked_witness(instance, trace)
        move = next(m for m in trace['moves'] if m['id']=='move74')
        move['start']=1382;move['legs'][0]['start']=1382
        with self.assertRaises(ValueError):
            normalize_future_reservations(trace)


if __name__ == '__main__':
    unittest.main()
