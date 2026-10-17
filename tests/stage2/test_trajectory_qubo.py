import itertools
import unittest
from stage2.window_experiments import tiny_problem
from stage2.window_qubo import compile_qubo,check_plan
from stage2.trajectory_qubo import compile_trajectory_qubo,columns_from_parents


class TrajectoryQUBOTests(unittest.TestCase):
    def test_every_master_state_matches_raw_feasibility_and_objective(self):
        p=tiny_problem();p['operations'][0].update(id='P1/a');p['operations'][1].update(id='P2/b',predecessors=[])
        raw=compile_qubo(p)
        def row(oid,start):return next(v for v in raw.variables if v['operation']==oid and v['start']==start)
        parents=[[row('P1/a',0),row('P2/b',2)],[row('P1/a',2),row('P2/b',0)]]
        q=compile_trajectory_qubo(p,columns_from_parents(p,parents));best=None
        for bits in itertools.product((0,1),repeat=len(q.linear)):
            decoded=q.decode(bits);energy=q.energy(bits)
            if not decoded['valid']:self.assertGreaterEqual(energy,q.penalty)
            else:self.assertEqual(energy,decoded['objective'])
            best=energy if best is None else min(best,energy)
        self.assertEqual(best,4);self.assertEqual(len(q.linear),4)

    def test_bad_internal_trajectory_cannot_be_encoded(self):
        p=tiny_problem();raw=compile_qubo(p);plan=[raw.variables[raw.groups[name][0]]for name in ('a','b')]
        self.assertFalse(check_plan(p,plan)['valid'])
        with self.assertRaises(ValueError):compile_trajectory_qubo(p,{'one':[plan,plan]})


if __name__=='__main__':unittest.main()
