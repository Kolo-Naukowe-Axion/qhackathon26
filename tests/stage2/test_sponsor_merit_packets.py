import itertools
import unittest

from stage2.sponsor_merit_packets import ising4, verify_inverse


class SponsorMeritPacketTests(unittest.TestCase):
    def test_every_bitstring_including_negative_coefficients_and_offset(self):
        linear = [-3, 7, 0]
        quadratic = {(0, 1): -2, (0, 2): 5, (1, 2): 1}
        offset = -11
        fields, edges, constant = ising4(linear, quadratic, offset)
        self.assertTrue(verify_inverse(linear, quadratic, offset, fields, edges, constant)['all_state_coefficient_identity'])
        for bits in itertools.product([0, 1], repeat=3):
            spins = [2 * bit - 1 for bit in bits]
            qubo = offset + sum(a * x for a, x in zip(linear, bits)) + sum(value * bits[i] * bits[j] for (i, j), value in quadratic.items())
            ising = constant + sum(a * x for a, x in zip(fields, spins)) + sum(value * spins[i] * spins[j] for (i, j), value in edges.items())
            self.assertEqual(ising, 4 * qubo)

    def test_each_kind_of_corrupted_coefficient_fails_inverse_audit(self):
        fields, edges, constant = ising4([-1, 3], {(0, 1): 2}, 4)
        for h, j, c in [([fields[0] + 1, fields[1]], edges, constant),
                        (fields, {(0, 1): 3}, constant), (fields, edges, constant + 1)]:
            with self.assertRaises(AssertionError):
                verify_inverse([-1, 3], {(0, 1): 2}, 4, h, j, c)


if __name__ == '__main__':
    unittest.main()
