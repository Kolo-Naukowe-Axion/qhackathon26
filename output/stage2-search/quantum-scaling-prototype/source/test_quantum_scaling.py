"""Independent circuit arithmetic and fixed-domain simulator contract checks."""
import math
import unittest

import numpy as np

from stage2.qubo import build_qubo
from stage2.quantum import statevector as scalar_statevector
from stage2.quantum_scaling import Budget,BudgetExceeded,Kernel,_classification,memory_estimate,select_qaoa,statevector


def fixture(n,slack=False):
    return build_qubo([dict(id=str(i),reward=i+1,resources={'power':1} if slack else {}) for i in range(n)],
        [(str(i),str(i+1)) for i in range(n-1)],{'power':max(1,n-1)} if slack else {})


class ScalingTests(unittest.TestCase):
    def test_scalar_amplitudes_at_all_one_to_five_bits_two_layers_and_slack(self):
        cases=[fixture(n) for n in range(1,6)]+[fixture(3,True)]
        self.assertEqual(cases[-1].size,5)
        for q in cases:
            for p in (1,2):
                gamma,beta=[.37,-.83][:p],[-.25,.41][:p]
                expected=np.array(scalar_statevector(q,gamma,beta))
                actual=statevector(q,gamma,beta,budget=Budget(chunk_states=2))
                np.testing.assert_allclose(actual,expected,rtol=1e-12,atol=1e-12)
                self.assertAlmostEqual(float(np.vdot(actual,actual).real),1,places=12)

    def test_independent_tensor_circuit_and_signs_with_nonzero_constant(self):
        q=fixture(3);q.offset=2.375
        q.linear=[1.2,-.8,2.3]
        q.quadratic={(0,1):-1.7,(0,2):.4,(1,2):2.5}
        gamma,beta=.71,-.36
        # Literal diagonal unitary and independently assembled Kronecker Rx matrix.
        expected=np.ones(8,dtype=complex)/math.sqrt(8)
        expected=np.diag([np.exp(-1j*gamma*q.energy([(s>>i)&1 for i in range(3)])/7.0) for s in range(8)])@expected
        rx=np.array([[math.cos(beta),-1j*math.sin(beta)],[-1j*math.sin(beta),math.cos(beta)]])
        expected=np.kron(np.kron(rx,rx),rx)@expected
        actual=statevector(q,[gamma],[beta],cost_scale=7)
        # Kernel drops q.offset; compare only the exactly known global phase.
        np.testing.assert_allclose(actual,expected*np.exp(1j*gamma*q.offset/7),atol=1e-12)

    def test_one_bit_analytic_probability_detects_wrong_gate_sign(self):
        q=fixture(1);gamma,beta=.9,.2
        vector=statevector(q,[gamma],[beta])
        # E(0)=0,E(1)=-1; alpha1=(cos(beta)*exp(i gamma)-i sin(beta))/sqrt(2).
        expected=(math.cos(beta)*np.exp(1j*gamma)-1j*math.sin(beta))/math.sqrt(2)
        self.assertAlmostEqual(abs(vector[1])**2,abs(expected)**2,places=13)

    def test_upper_triangular_energy_and_endian(self):
        q=fixture(7,True);kernel=Kernel(q,Budget(chunk_states=8))
        for s,value in enumerate(kernel.energies):
            self.assertAlmostEqual(value,q.energy([(s>>i)&1 for i in range(q.size)]),places=11)
        indices=np.arange(1<<q.size,dtype=np.uint32);valid,rewards=_classification(q,indices)
        for s in range(1<<q.size):
            chosen=[i for i in range(len(q.candidates)) if s>>i&1]
            self.assertEqual(valid[s],q.feasible(chosen))
            self.assertEqual(rewards[s],sum(q.candidates[i].reward for i in chosen))

    def test_budget_rejects_total_slack_not_just_core_and_preallocation(self):
        q=fixture(3,True)
        with self.assertRaises(BudgetExceeded):Kernel(q,Budget(max_bits=3))
        with self.assertRaises(BudgetExceeded):Kernel(q,Budget(memory_mib=1))
        with self.assertRaises(ValueError):Kernel(q,Budget(max_bits=25))
        with self.assertRaises(ValueError):Kernel(q,Budget(chunk_states=3))
        k=Kernel(q,Budget(evaluations=1));k.evolve([.2],[.3])
        with self.assertRaises(BudgetExceeded):k.evolve([.2],[.3])
        k.deadline=0
        with self.assertRaises(BudgetExceeded):k.evolve([.2],[.3],charge=False)
        self.assertGreater(memory_estimate(24),1024**3)

    def test_rejects_invalid_coefficients_angles_and_triangle(self):
        q=fixture(2);q.quadratic={(1,0):2}
        with self.assertRaises(ValueError):Kernel(q)
        q=fixture(1);q.linear=[float('nan')]
        with self.assertRaises(ValueError):Kernel(q)
        q=fixture(1)
        for gammas,betas,scale in [([1],[],None),([float('inf')],[1],None),([1],[1],0)]:
            with self.assertRaises(ValueError):statevector(q,gammas,betas,cost_scale=scale)

    def test_seeded_controls_counts_reference_and_telemetry(self):
        q=fixture(6,True);budget=Budget(evaluations=8,sa_sweeps=4,sa_restarts=1)
        a=select_qaoa(q,seed=31,shots=64,budget=budget)
        b=select_qaoa(q,seed=31,shots=64,budget=budget)
        self.assertEqual(a['raw_counts'],b['raw_counts'])
        self.assertEqual(a['selected'],b['selected'])
        self.assertEqual(sum(a['raw_counts'].values()),64)
        self.assertEqual(sum(a['uniform']['raw_counts'].values()),64)
        self.assertTrue(a['feasible'] and a['uniform']['feasible'] and a['sa']['feasible'])
        self.assertLessEqual(a['reward'],a['reference']['reward'])
        self.assertEqual(a['optimization']['evaluations'],8)
        self.assertEqual(a['optimization']['final_reconstruction_evolutions'],1)
        self.assertEqual(a['reference']['selections_examined'],64)
        self.assertFalse(a['quantum_executed'])
        self.assertTrue(a['quantum_algorithm_simulated'])
        self.assertEqual(a['source_sha256'],b['source_sha256'])
        self.assertLessEqual(sum(a['timings'].values()),a['elapsed_seconds'])
        self.assertAlmostEqual(a['ideal']['core_feasible_probability'],b['ideal']['core_feasible_probability'])

    def test_exact_reference_is_not_used_for_selection_and_can_be_skipped(self):
        q=fixture(5)
        for seed in range(20):
            a=select_qaoa(q,seed=seed,shots=1,angles=[0,0],budget=Budget(evaluations=1,sa_sweeps=1,sa_restarts=1))
            if not a['repaired'] and a['reward'] < a['reference']['reward']:break
        else:self.fail('Expected a sampled feasible suboptimal one-shot outcome')
        b=select_qaoa(q,seed=seed,shots=1,angles=[0,0],budget=Budget(evaluations=1,reference_core_bits=0,sa_sweeps=1,sa_restarts=1))
        self.assertEqual(a['selected'],b['selected'])
        self.assertEqual(b['reference']['status'],'skipped_core_budget')
        self.assertIsNone(b['ideal']['exact_reward_hit_probability'])

    def test_empty_pool_is_normalized_but_no_physical_execution(self):
        q=build_qubo([])
        a=select_qaoa(q,angles=[0,0],shots=3,budget=Budget(evaluations=1,sa_sweeps=1,sa_restarts=1))
        self.assertEqual(a['reward'],0)
        self.assertEqual(a['selected'],[])
        self.assertEqual(a['ideal']['core_feasible_probability'],1)
        self.assertFalse(a['quantum_algorithm_simulated'])


if __name__=='__main__':unittest.main()
