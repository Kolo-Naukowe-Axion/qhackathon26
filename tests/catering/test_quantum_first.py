import copy
import unittest
import numpy as np

from catering.audit import audit_bundle
from catering.domain import fixture,snapshot
from catering.options import enumerate_options,restricted_pool
from catering.qubo import energy,objective_energy
from catering.quantum_first import compile_unit_qubo,neighbor_masks,apply_conflict_mixer,compatibility_pool
from catering.build_quantum_first import quantum_fixture


class QuantumFirstTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p = fixture();s = snapshot(p,"S1")
        cls.bundle = compile_unit_qubo(p,s,restricted_pool(enumerate_options(p,s),s,8),
                                      representation="unit-test-cap8",parent_sha256="declared-restriction")

    def test_literal_penalty_and_minimum_agree_with_independent_raw_enumeration(self):
        checked = audit_bundle(self.bundle)
        self.assertTrue(checked["valid"])
        self.assertEqual(checked["all_bitstrings_checked"],256)
        self.assertEqual(self.bundle["registers"],[])
        self.assertEqual(self.bundle["size"]["shortfall_bits"],0)

    def test_penalty_exceeds_full_objective_range_despite_negative_coverage_rewards(self):
        b = self.bundle
        self.assertTrue(any(int(c)<0 for c in b["objective"]["linear"]))
        self.assertGreater(int(b["penalty"]),int(b["objective"]["upper_bound"])-int(b["objective"]["lower_bound"]))
        neighbors = neighbor_masks(b)
        valid = []
        invalid = []
        for mask in range(256):
            bits = [(mask>>i)&1 for i in range(8)]
            value = energy(b,bits)
            if any(bits[i] and mask & neighbors[i] for i in range(8)):
                invalid.append(value)
            else:
                valid.append(value)
                self.assertEqual(value,objective_energy(b,bits))
        self.assertGreater(min(invalid),max(valid))

    def test_nonunit_demand_is_rejected_instead_of_silently_approximated(self):
        p = fixture();p["demand_groups"][1]["lots"] = 2
        with self.assertRaises(ValueError):compile_unit_qubo(p,snapshot(p,"S0"),[])

    def test_controlled_rotations_preserve_norm_and_independent_set_support(self):
        # Path graph has valid multi-batch states, so this is not only a clique.
        neighbors = [2,5,2]
        state = np.zeros(8,dtype=complex);state[0] = 1
        valid = np.array([not any((m>>i)&1 and m&n for i,n in enumerate(neighbors)) for m in range(8)])
        energies = np.array([sum((m>>i)&1 for i in range(3)) for m in range(8)])
        for beta,gamma in ((0.3,0.2),(0.6,-0.5),(-0.7,0.9)):
            state *= np.exp(-1j*gamma*energies)
            state = apply_conflict_mixer(state,neighbors,beta)
            self.assertAlmostEqual(float(np.vdot(state,state).real),1)
            self.assertAlmostEqual(float(np.sum(np.abs(state[~valid])**2)),0)
        self.assertGreater(abs(state[5]),0) # Two compatible selections.

    def test_mixer_is_a_unitary_on_all_basis_states(self):
        neighbors = [2,5,2]
        matrix = np.column_stack([apply_conflict_mixer(np.eye(8,dtype=complex)[:,i],neighbors,0.37) for i in range(8)])
        np.testing.assert_allclose(matrix.conj().T@matrix,np.eye(8),atol=1e-14)
        with self.assertRaises(ValueError):apply_conflict_mixer(np.ones(4),[2,0],0.3)

    def test_ordinary_transverse_field_does_not_have_this_support_guarantee(self):
        # RX(2 beta) on both ends of one conflict edge populates forbidden |11>.
        beta = 0.37
        forbidden_probability = np.sin(beta)**4
        self.assertGreater(forbidden_probability,0)
        state = np.zeros(4,dtype=complex);state[0] = 1
        mixed = apply_conflict_mixer(state,[2,1],beta)
        self.assertEqual(mixed[3],0)

    def test_quantum_pool_retains_compatible_batches_and_nested_choices(self):
        p=quantum_fixture();s=snapshot(p,"S0")
        programs=enumerate_options(p,s)
        small=compatibility_pool(p,programs,8)
        large=compatibility_pool(p,programs,12)
        self.assertTrue({b["id"] for b in small}<={b["id"] for b in large})
        bundle=compile_unit_qubo(p,s,small,representation="test-compatibility-cap8",parent_sha256="test-parent")
        self.assertLess(len(bundle["conflicts"]),8*7//2)
        self.assertTrue(audit_bundle(bundle)["valid"])


if __name__ == "__main__":
    unittest.main()
