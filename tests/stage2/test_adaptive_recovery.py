from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from stage2 import adaptive_recovery as a
from stage2 import sequential as seq
from stage2.spec import build
from stage2.recovery_routing import run
from stage2.check import check_trace


class AdaptiveRecoveryTests(unittest.TestCase):
    def context(self):
        return dict(config=dict(orders=1,horizon=5760,profile='full'),
            weights=dict(wip_limit=4,qa_guard_threshold=4,worker_calendar=True,preposition=False,
                lease_calibration=True,selector='priority',admission_rule='family',family=24.,due=.25,remaining=-4.,setup=10.,tool_distance=0.),
            solver_options=dict(tool_policy=dict(mode='hard'),admission=True,kit_reservation=True,
                recovery_policy=dict(enabled=True),routing_policy=dict(eta_processes=[])),
            selection_provenance=dict(data='DEVELOPMENT smoke only',prior_fit_cost=0))

    def test_exact_static_fallback_reproduces_strong_factory_and_caches_only_own_decision(self):
        context=self.context();instance=build(**context['config'],seed=0)
        action=a.ACTIONS.index(dict(wip_limit=4,qa_guard_threshold=4))
        controller=a.Controller(dict(kind='static',action=action),context['weights'],91,True)
        direct=run(instance,dict(context['weights'],policy_seed=91),**context['solver_options'])
        actual=run(instance,context['weights'],controller,**context['solver_options'])
        for key in ('operations','moves','worker_moves','events','energy','metrics'):
            self.assertEqual(direct[key],actual[key],key)
        self.assertEqual(len(controller.trajectory),8)
        self.assertTrue(check_trace(actual)['valid'])

    def test_six_action_domain_uses_only_public_features_and_source_guard(self):
        from stage2.kit_recovery import AdmissionRecoveryFactory
        context=self.context();factory=AdmissionRecoveryFactory(build(1,seed=0),context['weights'])
        obs=factory.observation();perturbed=dict(obs,hidden_seed=123456,future_draw=.0001)
        for action in range(6):
            first=a.Controller(dict(kind='static',action=action),context['weights'],17)
            second=a.Controller(dict(kind='static',action=action),context['weights'],17)
            self.assertEqual(first(obs),second(perturbed))
            self.assertEqual(first(obs)['weights']['policy_seed'],17)
        task=dict(context_id=0,context=context,policy=dict(kind='static',action=0),seed=0,actor_seed=0,phase='TRAIN',source_hashes={})
        with self.assertRaisesRegex(RuntimeError,'source changed'):a.rollout(task)

    def test_numpy_inference_matches_torch_and_reward_is_terminal_compensated(self):
        try:import torch
        except ImportError:self.skipTest('Optional Torch training runtime unavailable')
        context=self.context();torch.manual_seed(4);network=a.make_network(torch)
        policy=dict(kind='ppo',network=seq.export_network(network));controller=a.Controller(policy,context['weights'],19,True)
        from stage2.kit_recovery import AdmissionRecoveryFactory
        obs=AdmissionRecoveryFactory(build(1,seed=0),context['weights']).observation()
        x=seq.features(obs);logits,_=network(torch.tensor([x],dtype=torch.float32))
        controller(obs);self.assertEqual(controller.trajectory[0]['action'],int(logits.argmax(-1)[0]))
        rewards=seq.trajectory_rewards([.1,.3,.2],-4.2)
        self.assertAlmostEqual(sum(rewards),-4.2)

    def test_development_only_training_keeps_static_baseline_eligible(self):
        with tempfile.TemporaryDirectory() as temporary:
            artifact=a.train([self.context()],Path(temporary)/'fit',method='cem',seconds=30,workers=2,seed=5,max_updates=1)
            self.assertEqual(artifact['final_tapes'],0)
            self.assertEqual(artifact['train_seeds'],list(range(32)))
            self.assertEqual(artifact['validation_seeds'],list(range(100,116)))
            self.assertLessEqual(artifact['selection'][0]['key'][0],0)
            self.assertIn(artifact['policies_by_context'][0]['kind'],('static','schedule'))
            self.assertEqual(artifact['source_hashes'],a.hashes())


if __name__=='__main__':unittest.main()
