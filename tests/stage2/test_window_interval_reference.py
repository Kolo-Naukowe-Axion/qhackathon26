import itertools
import random
import unittest

from stage2.window_interval_reference import mode_intervals, solve_interval_cp, walk_segments
from stage2.window_qubo import assignments, check_plan, solve_cp


class IntervalReferenceTests(unittest.TestCase):
    def test_shared_walk_completion_matches_every_calendar_slot(self):
        for calendar in ([[0,3],[5,8]],[[2,4],[7,9]],[[0,2],[4,6],[9,10]]):
            for travel in range(1,5):
                segments=walk_segments(calendar,travel,12)
                for after in range(13):
                    values=[slope*after+intercept for lo,hi,slope,intercept in segments if lo<=after<=hi]
                    self.assertEqual(len(values),1)
                    for before in range(13):
                        raw=any(max(after,lo)+travel<=min(before,hi)for lo,hi in calendar)
                        self.assertEqual(values[0]<=before,raw)

    def test_raw_calendar_domains_and_optima_against_exhaustive_enumeration(self):
        rng = random.Random(145783)
        for case in range(40):
            h = 7
            machines = {m:dict(hall=m, available=[[0,h]]) for m in ('A','B')}
            if case % 2 == 0:
                machines['A']['available'] = [[0,3],[4,h]]
            workers = {w:dict(skills=['cut'], initial_hall=rng.choice(('A','B')),
                             ready=rng.choice((0,1)),
                             available=rng.choice(([[0,h]],[[0,3],[4,h]]))) for w in ('U','V')}
            ops = [dict(id=str(i), durations={m:rng.choice((1,2)) for m in rng.sample(['A','B'], rng.choice((1,2)))},
                        skill='cut', attendance=rng.choice(('full','start')), start_attendance=1,
                        release=rng.choice((0,1)), due=rng.choice((2,4,6)), weight=rng.choice((1,2)),
                        family=rng.choice(('X','Y')), predecessors=[str(i-1)] if i and rng.random()<.7 else [])
                   for i in range(3)]
            p = dict(name='interval-fuzz'+str(case), horizon=h, grid=rng.choice((1,2,3)),
                     machines=machines, workers=workers, operations=ops, worker_travel=rng.choice((0,1,2)),
                     transport_lags={a:{b:0 if a==b else rng.choice((0,1,2)) for b in machines} for a in machines})
            if case % 2:
                p['machine_setups'] = {'X':{'X':0,'Y':1},'Y':{'X':2,'Y':0}}
                p['machine_initial_family'] = {'A':rng.choice(('X','Y'))}
            for op in ops:
                if rng.random() < .5:
                    op['machine_release'] = {next(iter(op['durations'])):rng.choice((0,1,2))}
                rows = assignments(p, op)
                for mid in machines:
                    for wid in workers:
                        actual = {r['start'] for r in rows if r['machine']==mid and r['worker']==wid}
                        intervals = mode_intervals(p, op, mid, wid)
                        derived = {tick*p['grid'] for lo,hi in intervals for tick in range(lo,hi+1)}
                        self.assertEqual(actual, derived, msg=f'case{case} mode{mid}/{wid}')
            best = None
            witness = None
            for plan in itertools.product(*(assignments(p,op) for op in ops)):
                checked = check_plan(p,list(plan))
                if checked['valid'] and (best is None or checked['objective'] < best):
                    best, witness = checked['objective'], list(plan)
            compact = solve_interval_cp(p,3,1,witness)
            original = solve_cp(p,3,1,witness)
            if best is None:
                self.assertEqual(compact['status'],'INFEASIBLE',msg=f'case{case}')
                self.assertEqual(original['status'],'INFEASIBLE',msg=f'case{case}')
            else:
                self.assertTrue(compact['optimal'],msg=f'case{case}')
                self.assertEqual(compact['objective'],best,msg=f'case{case}')
                self.assertEqual(original['objective'],best,msg=f'case{case}')


if __name__=='__main__':
    unittest.main()
