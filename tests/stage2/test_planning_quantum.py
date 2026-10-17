import unittest
import numpy as np

from stage2.window_experiments import tiny_problem
from stage2.window_qubo import compile_qubo,conditional_qubo
from stage2.planning_quantum import energy_table,evolve,sample_block
from stage2.quantum import _evolve as independent_stdlib_evolve


class PlanningQuantumTests(unittest.TestCase):
    def test_numpy_statevector_agrees_with_independent_frozen_stdlib(self):
        block={'linear':[3,-7,4,1],'quadratic':{(0,1):5,(1,3):-3,(0,2):8},'offset':19}
        values=energy_table(block)
        for layers in (1,2):
            gammas=[.37,1.1][:layers];betas=[.21,.63][:layers]
            a=evolve(values,4,gammas,betas,8)
            b=np.asarray(independent_stdlib_evolve(values.tolist(),4,gammas,betas,8,values[0]))
            self.assertLess(float(np.max(np.abs(a-b))),1e-12)
            self.assertAlmostEqual(float(np.sum(np.abs(a)**2)),1,places=12)

    def test_table_is_exact_full_planning_energy_after_substitution(self):
        q=compile_qubo(tiny_problem());free=[0,1,3,5,7];fixed={i:i%2 for i in range(len(q.linear))if i not in free}
        block=conditional_qubo(q,free,fixed);table=energy_table(block)
        for mask,e in enumerate(table):
            bits=[fixed.get(i,0)for i in range(len(q.linear))]
            for j,i in enumerate(free):bits[i]=(mask>>j)&1
            self.assertEqual(q.energy(bits),int(e))

    def test_single_uniform_shot_does_not_borrow_exact_solution(self):
        q=compile_qubo(tiny_problem());free=list(range(len(q.linear)))
        result=sample_block(q,free,{},method='uniform',seed=0,shots=1)
        self.assertEqual(sum(result['observed_counts'].values()),1)
        self.assertGreater(result['energy'],result['conditional_exact_energy'])
        chosen=int(next(iter(result['observed_counts'])))
        self.assertEqual(result['bits'],[(chosen>>i)&1 for i in free])
        self.assertFalse(result['quantum_algorithm_simulated'])

    def test_qaoa_budget_counts_normalization_and_real_sample(self):
        q=compile_qubo(tiny_problem());free=list(range(len(q.linear)))
        result=sample_block(q,free,{},method='qaoa',seed=13,shots=64,evaluations=16)
        self.assertTrue(result['quantum_algorithm_simulated']);self.assertEqual(result['physical_qpu_calls'],0)
        self.assertLessEqual(result['optimization']['angle_evaluations'],16)
        self.assertEqual(sum(result['observed_counts'].values()),64)
        self.assertEqual(result['energy'],q.energy(result['bits']))
        self.assertIn('qreg q[9]',result['qasm'])


if __name__=='__main__':unittest.main()
