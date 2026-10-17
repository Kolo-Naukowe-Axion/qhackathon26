from copy import deepcopy
import unittest
from unittest.mock import patch

from stage2.deadline_reference import solve_deadline_cp
from stage2.window_experiments import tiny_problem


class DeadlineReferenceTests(unittest.TestCase):
    def test_cap_and_due_are_both_hard_and_input_is_preserved(self):
        problem = tiny_problem()
        problem['operations'][-1]['due'] = 4
        original = deepcopy(problem)
        yes = solve_deadline_cp(problem, cap=4, seconds=2)
        no = solve_deadline_cp(problem, cap=3, seconds=2)
        self.assertTrue(yes['target_feasible'])
        self.assertTrue(yes['check']['valid'])
        self.assertFalse(no['target_feasible'])
        self.assertEqual(no['status'], 'INFEASIBLE')
        problem['operations'][-1]['due'] = 3
        self.assertFalse(solve_deadline_cp(problem, cap=6, seconds=2)['target_feasible'])
        problem['operations'][-1]['due'] = 4
        self.assertEqual(problem, original)
        self.assertNotEqual(yes['query_sha256'], no['query_sha256'])

    def test_travel_must_fit_within_worker_calendar(self):
        problem = tiny_problem()
        problem.update(horizon=8, grid=2, worker_travel=2)
        problem['machines'] = {m: dict(hall=m, available=[[0, 8]]) for m in ['A', 'B']}
        problem['workers']['W']['available'] = [[0, 2], [4, 8]]
        problem['transport_lags'] = {a: {b: 0 for b in ['A', 'B']} for a in ['A', 'B']}
        problem['operations'][0].update(durations={'A': 2}, due=8)
        problem['operations'][1].update(durations={'B': 2}, release=4, due=8)
        self.assertFalse(solve_deadline_cp(problem, cap=6, seconds=2)['target_feasible'])
        yes = solve_deadline_cp(problem, cap=8, seconds=2)
        self.assertTrue(yes['target_feasible'])
        self.assertEqual(next(r['start'] for r in yes['plan'] if r['operation'] == 'b'), 6)

    def test_machine_setup_and_initial_release_remain_enforced(self):
        problem = tiny_problem()
        problem['operations'][0]['family'] = 'first'
        problem['operations'][1]['family'] = 'second'
        problem['operations'][1]['due'] = 6
        problem['machine_setups'] = {'first': {'first': 0, 'second': 1},
                                   'second': {'first': 1, 'second': 0}}
        self.assertFalse(solve_deadline_cp(problem, cap=4, seconds=2)['target_feasible'])
        self.assertTrue(solve_deadline_cp(problem, cap=6, seconds=2)['target_feasible'])
        problem['operations'][0]['machine_release'] = {'M': 4}
        self.assertFalse(solve_deadline_cp(problem, cap=6, seconds=2)['target_feasible'])

    def test_compiler_domains_and_conflicts_are_not_used(self):
        with patch('stage2.window_qubo.assignments', side_effect=AssertionError('compiler used')), \
             patch('stage2.window_qubo.conflict_reasons', side_effect=AssertionError('compiler used')):
            self.assertTrue(solve_deadline_cp(tiny_problem(), seconds=2)['target_feasible'])

    def test_unknown_has_no_infeasibility_claim(self):
        from ortools.sat.python import cp_model
        with patch.object(cp_model.CpSolver, 'solve', return_value=cp_model.UNKNOWN):
            result = solve_deadline_cp(tiny_problem(), seconds=2)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertIsNone(result['target_feasible'])
        self.assertNotIn('plan', result)

    def test_invalid_parameters_do_not_become_infeasible(self):
        for kwargs in [dict(cap=-1), dict(cap=7), dict(seconds=0), dict(workers=0)]:
            with self.assertRaises(ValueError):
                solve_deadline_cp(tiny_problem(), **kwargs)


if __name__ == '__main__':
    unittest.main()
