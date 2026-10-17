"""Closed-loop continuation, controller memory and scenario-ranking regressions."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from stage2.engine import Factory,run as run_factory
from stage2.spec import build
from stage2.threshold import Controller,DEFAULT
from stage2.check import check_trace
from stage2.mpc import (RolloutController,candidates,check_future_physics,
    continuation,load_threshold_bank,resume,run,scenario_rank,source_hashes)


class MPCPolicyTests(unittest.TestCase):
    def test_bank_includes_lease_off(self):
        self.assertEqual({p['lease_calibration'] for p in candidates()},{False,True})

    def test_fulfillment_is_primary_for_any_scenario_count(self):
        a=[dict(orders=10,shipped=10,total_tardiness_ticks=0,total_cost=0) for _ in range(100)]
        a[0]['shipped']=9
        b=[dict(orders=10,shipped=10,total_tardiness_ticks=57600,total_cost=1e9) for _ in range(100)]
        self.assertLess(tuple(scenario_rank(b,[False]*100)),tuple(scenario_rank(a,[False]*100)))

    def test_actual_policy_follows_closed_loop_between_plans(self):
        p=dict(DEFAULT,heat_limit=99,grid_eco=False)
        instance=build(8,seed=0)
        direct=run_factory(instance,controller=Controller(p))
        planned=run(instance,actions=[],scenarios=1,interval=5760,
                    initial_policy=dict(kind='threshold',params=p),physical_check_futures=True)
        self.assertEqual(direct['metrics'],planned['metrics'])
        self.assertTrue(planned['validation']['valid'])
        self.assertEqual(len(planned['planning']['decisions']),1)
        self.assertTrue(planned['planning']['decisions'][0]['candidates'][0]['scenario_checks'][0]['valid'])

    def test_incumbent_hysteresis_and_memory_survive_new_planning(self):
        p=dict(DEFAULT,heat_limit=99,grid_eco=False)
        handler=Controller(p);snapshots=[]
        factory=Factory(build(8,seed=0))
        def observe(obs):
            downstream=obs['queue_QA']+obs['queue_ASSEMBLY']+max(0,obs['accepted_components']-3)/3
            if not snapshots and handler.congested and 2<=downstream<4:
                snapshots.append((continuation(factory,obs['tick'],{},0),deepcopy(handler),deepcopy(obs)))
            return handler(obs)
        factory.controller=observe;factory.run()
        self.assertTrue(snapshots,'Expected a real medium-backlog hysteresis boundary')
        state,incumbent,obs=snapshots[0]
        self.assertFalse(Controller(p)(obs)['weights']['wip_limit']==p['wip_low'])
        planner=RolloutController(state,actions=[],scenarios=1,interval=720,
                                  initial_policy=dict(kind='threshold',params=p))
        planner.active_handler=incumbent
        previous_count=incumbent.count
        result=planner(obs)
        self.assertIs(planner.active_handler,incumbent)
        self.assertTrue(incumbent.congested)
        self.assertEqual(incumbent.count,previous_count+1)
        self.assertEqual(result['weights']['wip_limit'],p['wip_low'])
        self.assertEqual(planner.history[0]['candidates'][0]['memory_source'],'preserved incumbent')

    def test_counterfactual_mixed_prefix_has_explicit_physical_only_audit(self):
        factory=Factory(build(3,seed=0),dict(wip_limit=3,lease_calibration=True));snapshots=[]
        def capture(obs):
            if obs['tick']==1440:snapshots.append(continuation(factory,1440,{},582))
            return dict(weights={})
        factory.controller=capture;factory.run()
        mixed=resume(snapshots[0])
        self.assertEqual(mixed['provenance']['kind'],'counterfactual_continuation')
        self.assertTrue(check_future_physics(mixed)['valid'])
        self.assertFalse(check_trace(mixed)['valid'],'Past tape must not be relabeled as the new planning seed')

    def test_threshold_bank_rejects_wrong_model_and_requires_version_opt_in(self):
        artifact=dict(source_hashes=source_hashes(True),configs=[dict(orders=3,horizon=5760,profile='full')],
                      params=[dict(DEFAULT)],base_weights={},policy_selection_role='validation_selected')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'bank.json'
            path.write_text(json.dumps(artifact))
            self.assertEqual(len(load_threshold_bank(path,build(3))),1)
            artifact['source_hashes']['stage2/threshold.py']='old-threshold-version'
            path.write_text(json.dumps(artifact))
            with self.assertRaisesRegex(ValueError,'explicit adapter required'):
                load_threshold_bank(path,build(3))
            self.assertEqual(len(load_threshold_bank(path,build(3),adapt=True)),1)
            artifact['source_hashes']['stage2/engine.py']='different-engine'
            path.write_text(json.dumps(artifact))
            with self.assertRaisesRegex(ValueError,'different physical source'):
                load_threshold_bank(path,build(3),adapt=True)

    def test_committed_lease_on_off_has_identical_futures_and_is_pruned(self):
        factory=Factory(build(2,seed=0),dict(lease_calibration=True));snapshots=[]
        def capture(obs):
            if obs['tick']==60:snapshots.append(continuation(factory,60,{},0))
            return dict(weights={})
        factory.controller=capture;factory.run();state=snapshots[0]
        self.assertTrue(state.lease_requested)
        off=resume(continuation(state,60,dict(lease_calibration=False),582))
        on=resume(continuation(state,60,dict(lease_calibration=True),582))
        for key in ('operations','moves','events','energy','metrics'):
            self.assertEqual(off[key],on[key],key)
        planner=RolloutController(state,actions=[dict(lease_calibration=False),dict(lease_calibration=True)],
                                  scenarios=1,interval=720)
        planner(state.observation())
        self.assertEqual(planner.history[0]['unique_policy_count'],1)


if __name__=='__main__':unittest.main()
