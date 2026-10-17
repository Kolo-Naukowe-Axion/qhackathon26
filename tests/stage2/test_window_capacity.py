import itertools
import random
import unittest

from stage2.window_capacity import capacity_certificate
from stage2.window_experiments import tiny_problem
from stage2.window_qubo import assignments,check_plan,solve_cp


class WindowCapacityTests(unittest.TestCase):
    def test_calendar_packing_proves_overload_that_total_minutes_miss(self):
        p=tiny_problem()
        p.update(horizon=70,grid=5,worker_travel=0)
        p['machines']={'M':dict(hall='A',available=[[0,70]]),'N':dict(hall='A',available=[[0,70]]),'P':dict(hall='A',available=[[0,70]])}
        p['workers']={w:dict(skills=['cut'],initial_hall='A',available=[[0,70]])for w in('U','V')}
        p['operations']=[dict(id=str(i),durations={m:45 for m in p['machines']},skill='cut',attendance='full',release=0,due=70,predecessors=[])for i in range(3)]
        p['transport_lags']={a:{b:0 for b in p['machines']}for a in p['machines']}
        result=capacity_certificate(p)
        skill=result['skills'][0]
        self.assertEqual(skill['minimum_required_attendance'],135)
        self.assertEqual(skill['raw_capacity_upper_bound'],140)
        self.assertEqual(skill['packed_capacity_upper_bound'],90)
        self.assertTrue(result['infeasible'])
        self.assertEqual(solve_cp(p,3,1)['status'],'INFEASIBLE')
        p['operations']=p['operations'][:2]
        self.assertFalse(capacity_certificate(p)['infeasible'])
        self.assertTrue(solve_cp(p,3,1)['check']['valid'])

    def test_no_false_infeasibility_on_exhaustively_checked_small_dags(self):
        rng=random.Random(18371)
        for case in range(30):
            p=tiny_problem()
            p.update(horizon=6,grid=rng.choice((1,2)),worker_travel=0)
            p['machines']['M']['available']=[[0,6]]
            p['workers']={w:dict(skills=['cut'],initial_hall='A',available=rng.choice(([[0,6]],[[0,2],[3,6]])))for w in('U','V')}
            p['operations']=[dict(id=str(i),durations={'M':rng.choice((1,2,3))},skill='cut',attendance=rng.choice(('full','start')),start_attendance=1,
                                  release=rng.choice((0,1)),due=6,predecessors=[str(i-1)]if i and rng.random()<.5 else[])for i in range(3)]
            exists=any(check_plan(p,list(plan))['valid']for plan in itertools.product(*(assignments(p,op)for op in p['operations'])))
            if exists:self.assertFalse(capacity_certificate(p)['infeasible'],msg=f'case{case}')


if __name__=='__main__':unittest.main()
