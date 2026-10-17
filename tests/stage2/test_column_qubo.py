import itertools
import unittest

from stage2.window_experiments import tiny_problem
from stage2.window_qubo import compile_qubo,check_plan,solve_literal_qubo
from stage2.column_qubo import compile_columns


class ColumnQUBOTests(unittest.TestCase):
    def test_cross_column_precedence_is_retained(self):
        p=tiny_problem();raw=compile_qubo(p)
        def row(name,start):return next(v for v in raw.variables if v['operation']==name and v['start']==start)
        q=compile_columns(p,{'first':[[row('a',0)],[row('a',2)]],'second':[[row('b',2)],[row('b',4)]]})
        self.assertEqual(q.metadata()['unconstrained_pattern_combinations'],'4')
        for a,b in itertools.product((0,1),repeat=2):
            plan=[q.columns['first'][a][0],q.columns['second'][b][0]];end=max(r['end']for r in plan)
            bits=[0]*len(q.linear);bits[q.groups['first'][a]]=1;bits[q.groups['second'][b]]=1;bits[next(i for i in q.groups['@makespan']if q.variables[i]['end']==end)]=1
            if check_plan(p,plan)['valid']:self.assertEqual(q.energy(bits),check_plan(p,plan)['objective']);self.assertTrue(q.decode(bits)['valid'])
            else:self.assertGreaterEqual(q.energy(bits),q.penalty);self.assertFalse(q.decode(bits)['valid'])
        optimum=solve_literal_qubo(q,3,1);self.assertTrue(optimum['optimal']);self.assertEqual(optimum['energy'],4)

    def test_every_global_ground_state_is_a_checked_raw_schedule(self):
        p=tiny_problem();raw=compile_qubo(p)
        def row(name,start):return next(v for v in raw.variables if v['operation']==name and v['start']==start)
        q=compile_columns(p,{'first':[[row('a',0)],[row('a',2)]],'second':[[row('b',2)],[row('b',4)]]})
        allstates=list(itertools.product((0,1),repeat=len(q.linear)));best=min(q.energy(b)for b in allstates)
        for bits in allstates:
            if q.energy(bits)==best:self.assertTrue(q.decode(bits)['valid']);self.assertEqual(q.decode(bits)['objective'],4)
            if not q.decode(bits)['valid']:self.assertGreaterEqual(q.energy(bits),q.penalty)


if __name__=='__main__':unittest.main()
