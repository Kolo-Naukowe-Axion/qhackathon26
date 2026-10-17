"""Adversarial audits using synthetic/training tapes only; no final evaluation."""
from copy import deepcopy
from fractions import Fraction
import unittest
from unittest.mock import patch

from stage2.engine import Factory,uniform
from stage2.spec import build
from stage2.mpc import continuation,resume,run as mpc_run
from stage2.check import check_trace,check_paired_causality
from stage2.statistics import branch,paired_report,weighted_cvar,weighted_mean,clustered_rows


PHYSICAL=('operations','moves','worker_moves','events','energy','metrics','audit')


class ContinuationBoundaryAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.states={}
        factory=Factory(build(6,seed=3),dict(wip_limit=4,lease_calibration=True))
        boundaries=(0,720,1440,2400,3000)
        def capture(observation):
            tick=observation['tick']
            if tick in boundaries:cls.states['after',tick]=continuation(factory,tick,{},3)
            return {'weights':{}}
        factory.controller=capture
        original_energy=Factory.energy_tick
        def energy_then_capture(current):
            original_energy(current)
            tick=current.t+1
            if current is factory and tick in (720,1440,2400):
                cls.states['before',tick]=continuation(current,tick,{},3,boundary_processed=False)
        with patch.object(Factory,'energy_tick',energy_then_capture):cls.actual=factory.run()

    def test_static_resumption_matches_before_and_after_shock_boundaries(self):
        self.assertTrue(any(event['type']=='repair'for event in self.actual['events']))
        for (side,tick),state in self.states.items():
            with self.subTest(side=side,tick=tick):
                result=resume(deepcopy(state))
                for field in PHYSICAL:self.assertEqual(result[field],self.actual[field],field)
                self.assertTrue(check_trace(result)['valid'])

    def test_poisoned_actual_hidden_seed_does_not_change_planning_futures(self):
        for tick in (1440,2400,3000):
            state=self.states['after',tick];poison=deepcopy(state)
            poison.i['seed']=9919  # Deliberately different, still a test/training seed.
            left=resume(continuation(state,tick,{},89))
            right=resume(continuation(poison,tick,{},89))
            for field in PHYSICAL:self.assertEqual(left[field],right[field],(tick,field))
            self.assertEqual(state.i['seed'],3)

    def test_future_quality_of_inflight_operation_is_resampled_and_past_is_kept(self):
        tick=3000;state=self.states['after',tick]
        operation=next(row for row in state.active if row['process']=='QA')
        uid=operation['unit_ids'][0];part=state.parts[uid]
        key=f'quality:{uid}:{part["attempt"]}'
        # Adversarial quality-edge fixture, not policy tuning or held-out testing.
        seed=next(seed for seed in range(1000)if seed!=3 and uniform(seed,key)<part['quality_risk'])
        result=resume(continuation(state,tick,{},seed))
        self.assertEqual(result['events'][:len(state.trace['events'])],state.trace['events'])
        future_qa=[event for event in result['events']if event['type']=='qa_result'and event['tick']>tick]
        self.assertTrue(future_qa)
        ops={row['id']:row for row in result['operations']}
        for event in future_qa:
            record=ops[event['operation_id']]
            self.assertEqual(event['keyed_uniform'],uniform(seed,f'quality:{event["unit_id"]}:{record["attempt"]}'))
        first=next(event for event in future_qa if event['operation_id']==operation['id'])
        self.assertFalse(first['passed'])
        self.assertTrue(any(event['type']=='repair'and event['unit_id']==uid and event['tick']>tick for event in result['events']))

    def test_rollout_decisions_share_prefix_through_later_revelations(self):
        template=build(2,horizon=2700)
        # Remove quality differences only for this branch-specific causality test.
        for probabilities in template['quality']['manufacturing_defect_probabilities'].values():
            for mode in probabilities:probabilities[mode]=0
        template['quality']['wear_risk_coefficient']=0
        options=[dict(wip_limit=2,mode='eco',lease_calibration=True),dict(wip_limit=3,mode='standard',lease_calibration=True)]
        stage_ids={seed:branch(seed,template['uncertainty_stages'])for seed in range(40)}
        for stage_index,tick in ((1,1440),(2,2400)):
            pair=next((a,b)for a in range(40)for b in range(a+1,40)
                      if stage_ids[a][:stage_index]==stage_ids[b][:stage_index]and stage_ids[a][stage_index]!=stage_ids[b][stage_index])
            traces=[]
            for seed in pair:
                instance=deepcopy(template);instance['seed']=seed
                traces.append(mpc_run(instance,options[0],options,scenarios=1,interval=480,seed=81))
            causality=check_paired_causality(traces)
            self.assertTrue(causality['valid'],causality)
            self.assertEqual(causality['pairs'][0]['shared_observation_prefix'],tick)
            for trace in traces:self.assertTrue(check_trace(trace)['valid'])
            def causal_evidence(value):
                if isinstance(value,dict):return {key:causal_evidence(item)for key,item in value.items()if key!='scenario_wall_seconds'}
                if isinstance(value,list):return [causal_evidence(item)for item in value]
                return value
            def planning_prefix(trace):
                return [causal_evidence({key:row[key]for key in ('tick','scenario_seeds','candidates','selected')})
                        for row in trace['planning']['decisions']if row['tick']<tick]
            self.assertEqual(planning_prefix(traces[0]),planning_prefix(traces[1]))


class WeightedStatisticsAudit(unittest.TestCase):
    def protocol(self):
        # Completely synthetic, deliberately unequal strata; no final tape IDs.
        return {'leaves':[{'seeds':[10,11],'probability':[9,10],'per_tape_weight':.45},
                          {'seeds':[12,13],'probability':[1,10],'per_tape_weight':.05}]}

    def test_unequal_leaf_weights_actor_clustering_and_paired_resampling(self):
        left=[];right=[]
        for seed,base in zip((10,11,12,13),(0,20,100,120)):
            for actor,noise in ((0,0),(1,20)):
                left.append(dict(seed=seed,policy_seed=actor,valid=True,loss=base+noise))
                right.append(dict(seed=seed,policy_seed=actor,valid=True,loss=base+noise-(100 if seed>=12 else 0)))
        report=paired_report(left,right,self.protocol(),lambda row:row['loss'],bootstrap=400,seed=6)
        self.assertEqual(report['environment_tapes'],4)
        self.assertEqual(report['actor_replicas_left'],8)
        self.assertAlmostEqual(report['left_mean'],30)
        self.assertAlmostEqual(report['right_mean'],20)
        self.assertAlmostEqual(report['left_cvar90'],120)
        self.assertAlmostEqual(report['right_cvar90'],30)
        # Pairing makes each resampled stratum's difference exactly known.
        for bound in report['mean_difference_percentile_bootstrap_95']:self.assertAlmostEqual(bound,-10)
        self.assertEqual(report,paired_report(left,right,self.protocol(),lambda row:row['loss'],bootstrap=400,seed=6))

    def test_fractional_cvar_tail_and_weight_scaling_match_closed_form(self):
        weights=[Fraction(83,100),Fraction(10,100),Fraction(7,100)]
        self.assertAlmostEqual(weighted_cvar([10,20,50],weights),41)
        self.assertAlmostEqual(weighted_cvar([10,20,50],[100*w for w in weights]),41)
        self.assertAlmostEqual(weighted_cvar([10,20,50],weights,alpha=0),weighted_mean([10,20,50],weights))

    def test_replica_missing_duplicate_and_invalid_trace_are_rejected(self):
        rows=[dict(seed=seed,policy_seed=actor,valid=True,loss=1)for seed in (10,11,12,13)for actor in (0,1)]
        for broken in (rows[:-1],rows+[rows[0]],rows+[dict(seed=99,valid=True,loss=1)]):
            with self.assertRaises(ValueError):clustered_rows(broken,self.protocol(),lambda row:row['loss'])
        invalid=deepcopy(rows);invalid[0]['valid']=False
        with self.assertRaises(ValueError):clustered_rows(invalid,self.protocol(),lambda row:row['loss'])


if __name__=='__main__':unittest.main()
