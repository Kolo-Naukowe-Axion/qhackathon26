import itertools
import unittest

from stage2.operation_columns import operation_columns
from stage2.column_qubo import compile_columns
from stage2.column_reference import solve_column_cp
from stage2.window_experiments import tiny_problem
from stage2.window_qubo import assignments,check_plan
from stage2.operation_qubo import compile_operations


class OperationColumnTests(unittest.TestCase):
    def test_parent_retention_raw_domains_and_new_route_combination(self):
        p=tiny_problem()
        rows={o['id']:assignments(p,o)for o in p['operations']}
        parent=[next(r for r in rows['a']if r['start']==2),next(r for r in rows['b']if r['start']==4)]
        columns,stats=operation_columns(p,[parent],12,6)
        self.assertFalse(stats['cp_teacher_used'])
        for name,options in columns.items():
            self.assertIn([next(r for r in parent if r['operation']==name)],options)
            self.assertTrue(all(plan[0]in rows[name]for plan in options))
        q=compile_columns(p,columns)
        fast=compile_operations(p,columns)
        self.assertEqual(q.linear,fast.linear)
        self.assertEqual(q.quadratic,fast.quadratic)
        self.assertEqual(q.offset,fast.offset)
        self.assertEqual(q.pair_conflicts,fast.pair_conflicts)
        self.assertTrue(q.decode(q.encode(parent))['valid'])
        reference=solve_column_cp(p,columns,3,1,parent)
        self.assertEqual(reference['objective'],4)
        self.assertEqual(q.energy(q.encode(reference['plan'])),4)

    def test_specialized_compiler_matches_independent_pair_checker_with_setups_and_walks(self):
        p=tiny_problem()
        p['horizon']=8
        p['grid']=1
        p['machines']={m:dict(hall=m,available=[[0,8]])for m in('M','N')}
        p['workers']={w:dict(skills=['cut'],initial_hall=hall,ready=0,
                            available=[[0,3],[4,8]])for w,hall in(('W','M'),('V','N'))}
        p['worker_travel']=2
        p['transport_lags']={a:{b:0 if a==b else 1 for b in p['machines']}for a in p['machines']}
        p['machine_setups']={'X':{'X':0,'Y':1},'Y':{'X':2,'Y':0}}
        for i,op in enumerate(p['operations']):
            op.update(durations={'M':2,'N':3},family='X'if i==0 else'Y',
                      attendance='start'if i==0 else'full',start_attendance=1)
        columns={op['id']:[[r]for r in assignments(p,op)]for op in p['operations']}
        general=compile_columns(p,columns)
        fast=compile_operations(p,columns)
        self.assertEqual(general.linear,fast.linear)
        self.assertEqual(general.quadratic,fast.quadratic)
        self.assertEqual(general.offset,fast.offset)
        self.assertEqual(general.variables,fast.variables)
        self.assertEqual(general.pair_conflicts,fast.pair_conflicts)


if __name__=='__main__':unittest.main()
