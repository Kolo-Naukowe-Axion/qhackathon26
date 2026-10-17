import unittest

from stage2.column_flexible import enrich_flexible
from stage2.column_qubo import compile_columns, subproblem
from stage2.column_reference import solve_column_cp
from stage2.window_experiments import tiny_problem
from stage2.window_qubo import assignments, check_plan, solve_cp


class FlexibleColumnTests(unittest.TestCase):
    def test_enrichment_retains_parent_and_can_improve_without_cp_teacher(self):
        p = tiny_problem()
        rows = {op['id']: assignments(p, op) for op in p['operations']}
        parent = [next(r for r in rows['a'] if r['start'] == 0),
                  next(r for r in rows['b'] if r['start'] == 4)]
        pool, stats = enrich_flexible(p, {'whole': [parent]}, 12, 6)
        self.assertIn(parent, pool['whole'])
        self.assertFalse(stats['cp_teacher_used'])
        self.assertTrue(all(check_plan(p, plan)['valid'] for plan in pool['whole']))
        reference = solve_column_cp(p, pool, 3, 1, parent)
        self.assertEqual(reference['objective'], 4)
        self.assertLess(reference['objective'], check_plan(p, parent)['objective'])
        q = compile_columns(p, pool)
        self.assertEqual(q.energy(q.encode(reference['plan'])), 4)

    def test_native_feasible_hint_is_checked_and_does_not_restrict_search(self):
        p = tiny_problem()
        rows = {op['id']: assignments(p, op) for op in p['operations']}
        parent = [next(r for r in rows['a'] if r['start'] == 0),
                  next(r for r in rows['b'] if r['start'] == 4)]
        reference = solve_cp(p, 3, 1, parent)
        self.assertTrue(reference['optimal'])
        self.assertTrue(reference['feasible_hint_used'])
        self.assertEqual(reference['hint_objective'], check_plan(p, parent)['objective'])
        self.assertEqual(reference['objective'], 4)
        with self.assertRaises(ValueError):
            solve_cp(p, 3, 1, parent[:1])


if __name__ == '__main__':
    unittest.main()
