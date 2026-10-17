import unittest
from unittest.mock import patch

from stage2.capacity_frontier import nested_pools
from stage2.window_experiments import tiny_problem
from stage2.window_qubo import assignments, digest


class CapacityFrontierTests(unittest.TestCase):
    def test_nested_unary_legal_deterministic_and_complete(self):
        p = tiny_problem()
        raw = {op['id']: assignments(p, op) for op in p['operations']}
        original = {oid: [[rows[-1]]] for oid, rows in raw.items()}
        before = digest(original)
        with patch('stage2.column_reference.solve_column_cp', side_effect=AssertionError('No teacher')):
            pools = nested_pools(p, original, (1, 2, 3, None))
        self.assertEqual(before, digest(original))
        self.assertEqual(pools, nested_pools(p, original, (1, 2, 3, None)))
        for oid, rows in raw.items():
            previous = set()
            for cap, columns in pools:
                kept = {digest(c[0]) for c in columns[oid]}
                self.assertTrue(previous <= kept)
                self.assertIn(digest(original[oid][0][0]), kept)
                self.assertTrue(kept <= {digest(r) for r in rows})
                previous = kept
            self.assertEqual(previous, {digest(r) for r in rows})

    def test_rejects_unary_invalid_baseline_and_bad_caps(self):
        p = tiny_problem()
        original = {op['id']: [[assignments(p, op)[0]]] for op in p['operations']}
        with self.assertRaises(ValueError):
            nested_pools(p, original, (2, 1, None))
        bad = {oid: [[dict(cols[0][0], start=-1)]] for oid, cols in original.items()}
        with self.assertRaises(ValueError):
            nested_pools(p, bad, (1, None))


if __name__ == '__main__':
    unittest.main()
