"""Causal thresholds, exact static embedding and held-out boundaries."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from stage2.threshold import (Controller,DEFAULT,Measurements,canonical,config,
    empirical_cvar90,hashes,rank,static_params,adapt_checkpoint)
from stage2.engine import Factory,run
from stage2.spec import build
from stage2.check import check_trace


class ThresholdTests(unittest.TestCase):
    def setUp(self):
        self.obs=Factory(build(orders=3,seed=0)).observation()

    def test_hidden_fields_do_not_affect_decisions(self):
        a=Controller(DEFAULT)(self.obs)
        b=Controller(DEFAULT)(dict(self.obs,seed=999,future_outage=True,hidden_defect=.01))
        self.assertEqual(a,b)

    def test_queue_hysteresis_prevents_chatter(self):
        controller=Controller(DEFAULT)
        a=controller(dict(self.obs,queue_QA=4))
        b=controller(dict(self.obs,queue_QA=3))
        c=controller(dict(self.obs,queue_QA=1))
        self.assertEqual(a['weights']['wip_limit'],3)
        self.assertEqual(b['weights']['wip_limit'],3)
        self.assertEqual(c['weights']['wip_limit'],6)

    def test_revealed_grid_drop_changes_mode(self):
        p=dict(DEFAULT,free_mode='turbo')
        controller=Controller(p)
        self.assertEqual(controller(self.obs)['weights']['mode'],'turbo')
        self.assertEqual(controller(dict(self.obs,grid_cap_kw=45))['weights']['mode'],'eco')

    def test_lease_schedule_is_causal(self):
        controller=Controller(dict(DEFAULT,lease_fraction=.125))
        self.assertFalse(controller(dict(self.obs,tick=719))['weights']['lease_calibration'])
        self.assertTrue(controller(dict(self.obs,tick=720))['weights']['lease_calibration'])

    def test_static_embedding_matches_actual_factory_execution(self):
        instance=build(orders=3,seed=0)
        weights=dict(wip_limit=3,mode='standard',lease_calibration=True,
                     due=1.,remaining=-4.,family=0.,setup=3.,selector='priority',policy_seed=0)
        fixed=run(instance,weights)
        threshold=run(instance,controller=Controller(static_params(weights)))
        self.assertEqual(fixed['metrics'],threshold['metrics'])
        self.assertTrue(check_trace(threshold)['valid'])

    def test_training_cache_rejects_validation_seed(self):
        with tempfile.TemporaryDirectory() as folder:
            cache=Measurements([config(3)],hashes(),folder)
            with self.assertRaisesRegex(ValueError,'split violation'):
                cache.collect(0,[DEFAULT],(100,),'training')

    def test_exact_empirical_cvar_uses_fractional_tail_boundary(self):
        self.assertAlmostEqual(empirical_cvar90(list(range(1,17))),15.625)
        self.assertAlmostEqual(empirical_cvar90([1,2,3]),3.)

    def test_canonical_admission_and_unsupported_teacher(self):
        p=canonical(dict(DEFAULT,wip_low=8,wip_high=1))
        self.assertEqual((p['wip_low'],p['wip_high']),(1,8))
        with self.assertRaises(ValueError):static_params(dict(wip_limit=3,noise=1))

    def test_reason_label_change_does_not_inflate_control_changes(self):
        p=static_params(dict(wip_limit=3,mode='standard'))
        p['late_fraction']=.5
        controller=Controller(p)
        controller(self.obs)
        controller(dict(self.obs,tick=4000,overdue_orders=1))
        self.assertEqual(controller.changes,0)
        self.assertEqual(controller.reason_changes,1)

    def test_routing_knobs_change_scores_without_changing_physics(self):
        controller=Controller(dict(DEFAULT,tool_distance=0,setup_weight=30))
        answer=controller(self.obs)
        self.assertEqual(answer['weights']['tool_distance'],0)
        self.assertEqual(answer['weights']['setup'],30)
        trace=run(build(orders=3,seed=0),controller=controller)
        self.assertTrue(check_trace(trace)['valid'])

    def test_old_controller_adapter_is_explicit_and_rejects_physical_drift(self):
        old=dict(DEFAULT)
        old.pop('tool_distance');old.pop('setup_weight')
        artifact=dict(params=[old],source_hashes=hashes())
        artifact['source_hashes']['stage2/threshold.py']='frozen-old-controller'
        adapted=adapt_checkpoint(artifact)
        self.assertEqual(adapted['params'][0]['tool_distance'],4)
        self.assertEqual(adapted['params'][0]['setup_weight'],10)
        self.assertEqual(adapted['controller_adapter']['original_params'],[old])
        artifact['source_hashes']['stage2/engine.py']='changed-physics'
        with self.assertRaisesRegex(ValueError,'changed physical source'):
            adapt_checkpoint(artifact)


if __name__=='__main__':unittest.main()
