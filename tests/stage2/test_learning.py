"""Safety of evaluation boundaries and the learning reward hierarchy."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from stage2.learning import (ACTIONS, Config, TRAIN_SEEDS, VALIDATION_SEEDS,
                            TEST_SEEDS, context_features, score, summarize)


class LearningProtocolTests(unittest.TestCase):
    def test_seed_splits_are_disjoint(self):
        for a, b in ((TRAIN_SEEDS, VALIDATION_SEEDS), (TRAIN_SEEDS, TEST_SEEDS),
                     (VALIDATION_SEEDS, TEST_SEEDS)):
            self.assertFalse(set(a) & set(b))

    def test_one_additional_fulfilled_order_beats_all_minor_terms(self):
        worst = dict(orders=26, shipped=25, total_tardiness_ticks=26*384,
                     horizon_ticks=384, energy_cost=1e9, terminal_soc_satisfied=True)
        best = dict(worst, shipped=24, total_tardiness_ticks=0, energy_cost=0)
        self.assertGreater(score(worst, True), score(best, True))
        self.assertLess(score(worst, False, 1), score(best, True))

    def test_context_is_finite_and_has_no_random_seed(self):
        context = context_features(Config(24, 384))
        self.assertEqual(len(context), 8)
        self.assertTrue(all(math.isfinite(value) for value in context))
        self.assertEqual(context, context_features(Config(24, 384)))

    def test_actions_are_distinct_and_interpretable(self):
        self.assertEqual(len(ACTIONS), 48)
        self.assertEqual(len({a['id'] for a in ACTIONS}), 48)
        self.assertEqual({a['weights']['mode'] for a in ACTIONS}, {'eco','standard', 'turbo'})
        self.assertEqual({a['weights']['lease_calibration'] for a in ACTIONS},{False,True})


if __name__ == '__main__':
    unittest.main()
