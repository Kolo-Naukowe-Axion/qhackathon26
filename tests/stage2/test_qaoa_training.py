import unittest
from types import SimpleNamespace

import numpy as np

from stage2.assignment_qaoa import AssignmentSector
from stage2.qaoa_training import AdjointObjective, train


def fixture():
    q = SimpleNamespace(groups={'a': [0, 1], 'b': [2, 3, 4]},
                        linear=[-10, -7, -9, -6, -8],
                        quadratic={(0, 1): 20, (2, 3): 20, (2, 4): 20, (3, 4): 20,
                                   (0, 3): 10, (1, 2): 10}, offset=20, penalty=10)
    return AssignmentSector.build(q)


class AdjointTests(unittest.TestCase):
    def test_gradients_match_central_differences_at_multiple_depths(self):
        sector = fixture()
        for p in (1, 2, 4):
            angles = np.random.default_rng(8).uniform(-2, 2, 2 * p)
            for alpha in (1, .7, .25):
                with self.subTest(p=p, alpha=alpha):
                    objective = AdjointObjective(sector, p, alpha)
                    value, gradient = objective(angles)
                    h = 1e-6
                    numerical = []
                    for axis in range(len(angles)):
                        direction = np.eye(len(angles))[axis] * h
                        plus = objective(angles + direction)[0]
                        minus = objective(angles - direction)[0]
                        numerical.append((plus - minus) / (2 * h))
                    np.testing.assert_allclose(gradient, numerical, rtol=2e-6, atol=1e-8)
                    probability = abs(sector.evolve(angles[:p].tolist(), angles[p:].tolist(), objective.scale)) ** 2
                    order = np.argsort(sector.energies)
                    weight = np.clip(alpha - np.cumsum(probability[order]) + probability[order],
                                     0, probability[order])
                    expected = np.dot(weight, objective.diagonal[order]) / alpha
                    self.assertAlmostEqual(value, expected, places=12)

    def test_large_gamma_does_not_wrap_and_budget_is_hard(self):
        sector = fixture()
        objective = AdjointObjective(sector, 1)
        self.assertNotAlmostEqual(objective([.7, .35])[0], objective([.7 + 2 * np.pi, .35])[0])
        try:
            import scipy  # noqa: F401
        except ImportError:
            self.skipTest('Optional SciPy fit dependency absent')
        fit = train(sector, layers=2, evaluations=3, seed=7)
        self.assertLessEqual(fit['evaluations'], 3)
        self.assertEqual(fit['evaluations'], len(fit['history']))
        self.assertFalse(fit['exact_reference_used_for_training'])

    def test_degenerate_quantile_has_zero_tail_gradient(self):
        sector = fixture()
        sector.energies[:] = 12
        for alpha in (1, .5, .1):
            objective = AdjointObjective(sector, 2, alpha)
            value, gradient = objective([.3, .7, .4, -.2])
            self.assertAlmostEqual(value, 0)
            np.testing.assert_allclose(gradient, 0, atol=1e-12)

    def test_checkpoint_selection_retains_best_observed_training_value(self):
        objective = AdjointObjective(fixture(), 1, .7)
        angles = [[.2, .3], [2.1, -.7], [.9, .4]]
        values = [objective(a)[0] for a in angles]
        self.assertEqual(objective.calls, 3)
        self.assertEqual(objective.best[0], min(values))
        np.testing.assert_array_equal(objective.best[1], angles[int(np.argmin(values))])


if __name__ == '__main__':
    unittest.main()
