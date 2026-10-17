"""Correctness checks for the cluster-entangled VQE simulator (solver/cluster_vqe.py)."""
import itertools
import json
import unittest

import numpy as np

from solver.cluster_vqe import (ClusterVQE, DenseQubo, all_valid_codewords, factory_clusters,
                                instance_b_setup, random_like)
from solver.stage1 import ROOT, build_qubo, decode, energy, validate


def load(size):
    return json.loads((ROOT / "instances" / f"instance_{size}.json").read_text())


class ClusterVQETests(unittest.TestCase):
    def test_dense_energy_matches_stage1_energy(self):
        model = build_qubo(load("3x3"), 8, "domain-wall")
        q = DenseQubo(model)
        rng = np.random.default_rng(0)
        X = rng.integers(0, 2, (200, q.n))
        ref = [energy(model, list(map(int, x))) for x in X]
        np.testing.assert_allclose(q.energies(X), ref)

    def test_instance_b_has_13_optimal_codewords_all_valid_8h(self):
        inst = load("3x3")
        model, q, optimal, _ = instance_b_setup(inst, 8)
        self.assertEqual(q.n, 30)
        self.assertEqual(len(all_valid_codewords(model)), 512000)
        self.assertEqual(len(optimal), 13)
        for x in optimal:
            s = decode(model, list(map(int, x)))
            self.assertEqual(validate(inst, s, 8), [])

    def test_exact_expectation_by_full_enumeration(self):
        # Instance A, H=5 domain wall: small enough to enumerate every bitstring.
        model = build_qubo(load("2x2"), 5, "domain-wall")
        q = DenseQubo(model)
        allx = np.array(list(itertools.product([0, 1], repeat=q.n)))
        rng = np.random.default_rng(3)
        for clusters in (factory_clusters(model)["per-operation"], [list(range(q.n))],
                         random_like([[0, 1, 2], [3, 4], [5, 6, 7]], q.n, rng)):
            vqe = ClusterVQE(q, clusters, 2)
            th = rng.uniform(-np.pi, np.pi, vqe.npar)
            p = vqe.prob_of(th, allx)
            self.assertAlmostEqual(p.sum(), 1.0, places=12)
            self.assertAlmostEqual(vqe.loss_grad(th, grad=False), p @ q.energies(allx), places=10)

    def test_adjoint_gradient_matches_finite_differences(self):
        model = build_qubo(load("3x3"), 8, "domain-wall")
        q = DenseQubo(model)
        rng = np.random.default_rng(1)
        vqe = ClusterVQE(q, random_like([[0] * 7, [0] * 12, [0] * 11], q.n, rng), 2)
        th = rng.uniform(-np.pi, np.pi, vqe.npar)
        _, G = vqe.loss_grad(th)
        eps = 1e-6
        fd = [(vqe.loss_grad(th + eps * e, False) - vqe.loss_grad(th - eps * e, False)) / (2 * eps)
              for e in np.eye(vqe.npar)]
        np.testing.assert_allclose(G, fd, atol=1e-6)

    def test_random_like_keeps_sizes_and_partitions(self):
        clusters = factory_clusters(build_qubo(load("3x3"), 8, "domain-wall"))["per-machine"]
        r = random_like(clusters, 30, np.random.default_rng(5))
        self.assertEqual(sorted(map(len, r)), sorted(map(len, clusters)))
        self.assertEqual(sorted(i for c in r for i in c), list(range(30)))


if __name__ == "__main__":
    unittest.main()
