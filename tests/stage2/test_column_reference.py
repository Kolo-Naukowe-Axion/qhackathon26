import itertools
import unittest
from stage2.window_experiments import tiny_problem
from stage2.window_qubo import compile_qubo,check_plan,solve_literal_qubo
from stage2.column_qubo import compile_columns
from stage2.column_reference import solve_column_cp


class ColumnReferenceTests(unittest.TestCase):
    def test_native_raw_pool_reference_matches_exhaustive_and_literal(self):
        p=tiny_problem();raw=compile_qubo(p)
        def row(name,start):return next(v for v in raw.variables if v['operation']==name and v['start']==start)
        columns={'first':[[row('a',0)],[row('a',2)]],'second':[[row('b',2)],[row('b',4)]]}
        candidates=[first+second for first,second in itertools.product(columns['first'],columns['second'])]
        expected=min(check_plan(p,plan)['objective']for plan in candidates if check_plan(p,plan)['valid'])
        cp=solve_column_cp(p,columns,3,1,initial_plan=candidates[0]);q=compile_columns(p,columns);literal=solve_literal_qubo(q,3,1)
        self.assertTrue(cp['optimal']);self.assertTrue(literal['optimal']);self.assertEqual(cp['objective'],expected);self.assertEqual(cp['objective'],literal['energy'])
        self.assertEqual(q.energy(q.encode(cp['plan'])),expected);self.assertFalse(cp['uses_qubo_coefficients'])


if __name__=='__main__':unittest.main()
