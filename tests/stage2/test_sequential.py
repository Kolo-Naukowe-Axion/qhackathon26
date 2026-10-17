"""Causality, return equivalence and callback integration for sequential RL."""
from pathlib import Path
import sys
import json
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from stage2.sequential import (ACTIONS, FEATURE_NAMES, Controller, Config, TRAIN,
    VALIDATION, TEST, features, terminal_reward, trajectory_rewards,
    make_network, export_network, validation_key, evaluation_tasks, fingerprints,
    load_teacher, adapt_evaluation_checkpoint)
from stage2.engine import Factory
from stage2.spec import build


class SequentialProtocolTests(unittest.TestCase):
    def setUp(self):
        self.observation = Factory(build(orders=3, seed=0)).observation()

    def test_public_feature_contract_and_hidden_fields_are_ignored(self):
        baseline = features(self.observation)
        modified = dict(self.observation, seed=9999, future_defect=True, unrevealed_outage=1)
        self.assertEqual(baseline, features(modified))
        self.assertEqual(len(baseline), 32)
        self.assertEqual(len(FEATURE_NAMES), 32)

    def test_potential_shaping_preserves_terminal_objective(self):
        for potentials in ([0., .1, .07, .13], [0.], [.02, .5], [-1., 2., 0.]):
            rewards = trajectory_rewards(potentials, -3.125)
            self.assertAlmostEqual(sum(rewards), -3.125)
            self.assertEqual(len(rewards), len(potentials))

    def test_fulfillment_dominates_tardiness_and_investment_cost(self):
        a = dict(orders=26, shipped=25, terminal_soc_satisfied=True,
                 total_tardiness_ticks=26*5760, total_cost=1e9)
        b = dict(a, shipped=24, total_tardiness_ticks=0, total_cost=0)
        self.assertGreater(terminal_reward(a, True, 5760), terminal_reward(b, True, 5760))
        self.assertLess(terminal_reward(a, False, 5760), terminal_reward(b, True, 5760))

    def test_actions_cover_requested_physical_decisions(self):
        self.assertEqual(len(ACTIONS), 48)
        self.assertEqual({a['weights']['wip_limit'] for a in ACTIONS}, {1, 2, 3, 4, 6, 8})
        self.assertEqual({a['weights']['mode'] for a in ACTIONS}, {'eco', 'standard', 'turbo'})
        self.assertEqual({a['weights']['lease_calibration'] for a in ACTIONS}, {False, True})

    def test_callback_uses_fixed_solver_seed_separate_from_action_rng(self):
        callback = Controller(dict(kind='static', action=0), policy_seed=2026,
                              base_weights={'selector':'priority', 'policy_seed':17})
        answer = callback(self.observation)
        self.assertEqual(answer['weights']['policy_seed'], 17)
        self.assertEqual(answer['action_id'], ACTIONS[0]['id'])
        self.assertEqual(len(callback.trajectory), 1)

    def test_seed_partitions_disjoint(self):
        self.assertFalse(set(TRAIN) & set(VALIDATION))
        self.assertFalse(set(TRAIN) & set(TEST))
        self.assertFalse(set(VALIDATION) & set(TEST))

    def test_numpy_worker_matches_torch_policy_probabilities(self):
        try:
            import torch
        except ImportError:
            self.skipTest('PyTorch training dependency unavailable')
        torch.manual_seed(713)
        network = make_network(torch)
        callback = Controller(dict(kind='ppo', network=export_network(network)))
        x = features(self.observation)
        probabilities, value = callback.infer(x)
        with torch.no_grad():
            logits, values = network(torch.tensor([x], dtype=torch.float32))
            expected = torch.softmax(logits, dim=-1)[0].tolist()
        for actual, target in zip(probabilities, expected):
            self.assertAlmostEqual(actual, target, places=6)
        self.assertAlmostEqual(value, float(values[0]), places=6)

    def test_validation_checkpoint_selection_prioritizes_physical_validity(self):
        good = dict(summary=dict(episodes=16, valid=16, mean_unfulfilled=1.,
                                 mean_tardiness_ticks=5000, mean_total_cost=1000))
        invalid = dict(summary=dict(episodes=16, valid=15, mean_unfulfilled=0.,
                                    mean_tardiness_ticks=0, mean_total_cost=0))
        self.assertLess(validation_key(good), validation_key(invalid))

    def test_actor_replication_keeps_environment_tapes_separate(self):
        artifact = dict(source_hashes=fingerprints(), policy=dict(kind='static', action=0),
                        configs=[], base_weights={'policy_seed':17})
        tasks = evaluation_tasks(artifact, [Config(3)], (100,101),
                                 deterministic=False, policy_seeds=(900,901))
        self.assertEqual({(t['seed'],t['policy_seed']) for t in tasks},
                         {(100,900),(100,901),(101,900),(101,901)})
        self.assertTrue(all(t['base_weights']['policy_seed']==17 for t in tasks))
        self.assertTrue(all(not t['deterministic'] for t in tasks))

    def test_training_only_teacher_rejects_validation_selection(self):
        teacher = dict(policy={'kind':'context_static'}, selected_validation={})
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'teacher.json'
            path.write_text(json.dumps(teacher))
            with self.assertRaisesRegex(ValueError, 'validation-selected teacher'):
                load_teacher(path, [Config(3)], fingerprints())

    def test_eval_adapter_preserves_policy_but_rejects_physical_drift(self):
        artifact = dict(feature_names=list(FEATURE_NAMES), actions=list(ACTIONS),
                        source_hashes=fingerprints(), policy={'kind':'static','action':0})
        artifact['source_hashes']['stage2/sequential.py']='previous-learner'
        adapted = adapt_evaluation_checkpoint(artifact)
        self.assertEqual(adapted['policy'], artifact['policy'])
        self.assertEqual(adapted['evaluation_adapter']['original_source_hashes'], artifact['source_hashes'])
        artifact['source_hashes']['stage2/engine.py']='changed-physics'
        with self.assertRaisesRegex(ValueError, 'changed physical source'):
            adapt_evaluation_checkpoint(artifact)


if __name__ == '__main__':
    unittest.main()
