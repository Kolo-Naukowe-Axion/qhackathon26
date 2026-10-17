import unittest
import numpy as np
from stage2.window_experiments import tiny_problem
from stage2.window_qubo import compile_qubo
from stage2.trajectory_qubo import columns_from_parents,compile_trajectory_qubo
from stage2.planning_quantum import energy_table
from stage2.trajectory_mixer import initial_state,invariant_block,evolve,sample


def model():
    p=tiny_problem();p['operations'][0].update(id='P1/a');p['operations'][1].update(id='P2/b',predecessors=[])
    raw=compile_qubo(p)
    def row(name,start):return next(v for v in raw.variables if v['operation']==name and v['start']==start)
    parents=[[row('P1/a',0),row('P2/b',2)],[row('P1/a',2),row('P2/b',0)]]
    return compile_trajectory_qubo(p,columns_from_parents(p,parents))


class TrajectoryMixerTests(unittest.TestCase):
    def test_one_hot_invariant_and_phase_removal_are_exact(self):
        q=model();original=energy_table(dict(linear=q.linear,quadratic=q.quadratic,offset=q.offset));reduced=energy_table(invariant_block(q))
        support=np.flatnonzero(np.abs(initial_state(q))>0)
        self.assertTrue(np.array_equal(original[support],reduced[support]))
        for layers in(1,2):
            state=evolve(q,original,[.37]*layers,[.83]*layers,max(map(abs,q.linear)))
            outside=np.ones(len(state),dtype=bool);outside[support]=False
            self.assertLess(float(np.sum(np.abs(state[outside])**2)),1e-15)
            self.assertAlmostEqual(float(np.sum(np.abs(state)**2)),1,places=12)

    def test_uniform_control_and_qaoa_do_not_leak(self):
        q=model()
        for method in('uniform_onehot','qaoa_xy'):
            row=sample(q,method=method,evaluations=16,shots=64)
            self.assertLess(row['makespan_invariant_leakage'],1e-15)
            self.assertEqual(sum(row['observed_counts'].values()),64)
            self.assertEqual(sum(row['bits'][len(q.columns):]),1)
            self.assertEqual(row['energy'],q.energy(row['bits']))


if __name__=='__main__':unittest.main()
