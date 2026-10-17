import itertools
import unittest
from copy import deepcopy

from stage2.deadline_qubo import DeadlineInfeasible, compile_deadline
from stage2.window_experiments import tiny_problem
from stage2.window_qubo import assignments, check_plan
from stage2.deadline_reference import solve_deadline_cp


class DeadlineQUBOTests(unittest.TestCase):
    def test_every_bitstring_zero_iff_independent_schedule_and_query_valid(self):
        p = tiny_problem()
        q = compile_deadline(p, support_pruning=False)
        for bits in itertools.product((0, 1), repeat=len(q.linear)):
            plan = [row for row, bit in zip(q.variables, bits) if bit]
            checked = check_plan(p, plan)
            expected = checked['valid'] and checked['weighted_terminal_tardiness'] == 0
            self.assertEqual(q.energy(bits) == 0, expected)
            self.assertEqual(q.decode(bits)['valid'], expected)
            self.assertGreaterEqual(q.energy(bits), 0)

    def test_exact_pruning_preserves_all_feasible_query_plans(self):
        p = tiny_problem()
        q = compile_deadline(p, cap=4, support_pruning=True)
        count = 0
        for plan in itertools.product(*(assignments(p, op) for op in p['operations'])):
            checked = check_plan(p, list(plan))
            if checked['valid'] and checked['makespan'] <= 4 and checked['weighted_terminal_tardiness'] == 0:
                count += 1
                bits = q.encode(list(plan))
                self.assertEqual(q.energy(bits), 0)
                self.assertTrue(q.decode(bits)['valid'])
        self.assertGreater(count, 0)
        self.assertNotIn('@makespan', q.groups)
        self.assertEqual(set(q.linear), {-1})
        self.assertLessEqual(set(q.quadratic.values()), {1, 2})

    def test_infeasibility_certificate_and_guard_have_distinct_semantics(self):
        p = tiny_problem()
        with self.assertRaises(DeadlineInfeasible):
            compile_deadline(p, cap=2)
        with self.assertRaises(ValueError) as error:
            compile_deadline(p, max_variables=1)
        self.assertNotIsInstance(error.exception, DeadlineInfeasible)
        for kwargs in (dict(max_pair_checks=1), dict(max_couplers=1)):
            with self.assertRaises(ValueError) as error:
                compile_deadline(p, support_pruning=False, **kwargs)
            self.assertNotIsInstance(error.exception, DeadlineInfeasible)

    def test_due_date_pruning_changes_query_not_original_problem(self):
        p = tiny_problem()
        original = deepcopy(p)
        q = compile_deadline(p)
        self.assertEqual(p, original)
        p['operations'][-1]['due'] = 0
        self.assertEqual(q.problem, original)
        p = original
        q2 = compile_deadline(p, cap=4)
        self.assertNotEqual(q.metadata()['query_sha256'], q2.metadata()['query_sha256'])
        # Optional non-grid-aligned cap still means an exact integer-time query.
        with self.assertRaises(DeadlineInfeasible):
            compile_deadline(p, cap=3)

    def test_native_query_equivalence_with_calendars_travel_setups_and_releases(self):
        travel = tiny_problem()
        travel.update(horizon=8, grid=2, worker_travel=2)
        travel['machines'] = {m: dict(hall=m, available=[[0, 8]]) for m in ['A', 'B']}
        travel['workers']['W']['available'] = [[0, 2], [4, 8]]
        travel['transport_lags'] = {a: {b: 0 for b in ['A', 'B']} for a in ['A', 'B']}
        travel['operations'][0].update(durations={'A': 2}, due=8)
        travel['operations'][1].update(durations={'B': 2}, release=4, due=8)
        setup = tiny_problem()
        setup['operations'][0]['family'] = 'first'
        setup['operations'][1].update(family='second', due=6)
        setup['machine_setups'] = {'first': {'first': 0, 'second': 1},
                                   'second': {'first': 1, 'second': 0}}
        for p, cap in [(travel, 6), (travel, 8), (setup, 4), (setup, 6)]:
            with self.subTest(cap=cap, setups=bool(p.get('machine_setups'))):
                reference = solve_deadline_cp(p, cap, seconds=2)
                self.assertIsNotNone(reference['target_feasible'])
                try:
                    q = compile_deadline(p, cap)
                except DeadlineInfeasible:
                    self.assertFalse(reference['target_feasible'])
                    continue
                self.assertEqual(q.metadata()['query_sha256'], reference['query_sha256'])
                zero_exists = any(q.energy([int(i in choices) for i in range(len(q.linear))]) == 0
                    for choices in itertools.product(*q.groups.values()))
                self.assertEqual(zero_exists, reference['target_feasible'])
                if reference['target_feasible']:
                    self.assertEqual(q.energy(q.encode(reference['plan'])), 0)


if __name__ == '__main__':
    unittest.main()
