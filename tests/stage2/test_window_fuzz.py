"""Small randomized exhaustive cross-check against raw checker and native CP."""
import itertools
import random
import unittest

from stage2.window_qubo import assignments,compile_qubo,check_plan,solve_cp


class WindowFuzzTests(unittest.TestCase):
    def test_small_dags_calendars_crews_and_metric_setups(self):
        rng=random.Random(827461)
        for case in range(30):
            h=6;grid=rng.choice((1,2));machines={m:dict(hall=m,available=[[0,h]])for m in('A','B')}
            workers={w:dict(skills=['cut'],initial_hall=rng.choice(('A','B')),available=rng.choice(([[0,h]],[[0,2],[3,h]])))for w in('U','V')}
            ops=[]
            for i in range(3):
                eligible=rng.sample(list(machines),rng.choice((1,2)))
                ops.append(dict(id=str(i),durations={m:rng.choice((1,2))for m in eligible},skill='cut',attendance=rng.choice(('full','start')),start_attendance=1,
                    release=rng.choice((0,1)),due=rng.choice((2,4,6)),weight=rng.choice((1,2)),predecessors=[str(i-1)]if i and rng.random()<.6 else[],family=rng.choice(('X','Y'))))
            p=dict(name='fuzz'+str(case),horizon=h,grid=grid,machines=machines,workers=workers,operations=ops,
                worker_travel=rng.choice((0,1,2)),transport_lags={a:{b:0 if a==b else rng.choice((0,1,2))for b in machines}for a in machines})
            if case%2:p['machine_setups']={'X':{'X':0,'Y':1},'Y':{'X':2,'Y':0}}
            domains=[assignments(p,o)for o in ops];best=None;valid_plans=[]
            for rows in itertools.product(*domains):
                result=check_plan(p,list(rows))
                if result['valid']:
                    best=result['objective']if best is None else min(best,result['objective']);valid_plans.append(list(rows))
            cp=solve_cp(p,3,1)
            if best is None:
                self.assertEqual(cp['status'],'INFEASIBLE',msg=f'case{case}')
            else:
                self.assertTrue(cp['optimal'],msg=f'case{case}');self.assertEqual(cp['objective'],best,msg=f'case{case}')
                q=compile_qubo(p,support_pruning=True)
                for plan in valid_plans:
                    # Every feasible raw assignment survives pruning, not merely optimum.
                    for row in plan:self.assertIn(row,q.variables)


if __name__=='__main__':unittest.main()
