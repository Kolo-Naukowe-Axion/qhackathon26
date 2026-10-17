import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from stage2 import final_eval as f


class FrozenEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.config=dict(orders=1,horizon=5760,profile='full')

    def tearDown(self):self.temp.cleanup()

    def write(self,name,value):
        path=self.root/name;path.write_text(json.dumps(value));return path

    def selected(self,methods=None,actors=None):
        selection=dict(schema='stage2-selected-policy-spec.v1',configs=[self.config],actor_seeds=actors or [91],
            selection_provenance=dict(data='DEVELOPMENT only',training_wall_seconds=0),
            methods=methods or [dict(id='fixed',kind='static',weights=dict(wip_limit=3,lease_calibration=True),
                selection_provenance=dict(data='hand-written development smoke',training_wall_seconds=0))])
        return self.write('selection.json',selection)

    def freeze(self,methods=None,actors=None,seeds=(0,),trace_policy=None):
        protocol=self.write('protocol.json',f.development_protocol(seeds))
        selection=self.selected(methods,actors)
        if trace_policy is not None:
            spec=json.loads(selection.read_text());spec['trace_policy']=trace_policy;selection.write_text(json.dumps(spec))
        return f.freeze(selection,protocol,self.root/'frozen.json',development=True)

    def test_development_protocol_refuses_reserved_or_undeclared_tapes(self):
        for seeds in ([10000],[32],[1000],[0,0]):
            with self.assertRaises(ValueError):f.development_protocol(seeds)
        with self.assertRaises(ValueError):f.validate_protocol(f.development_protocol([0]),False)

    def test_final_protocol_is_bound_to_model_probabilities_and_exogenous_tapes(self):
        from stage2.spec import build
        from stage2.statistics import stratified_protocol
        from copy import deepcopy
        protocol=stratified_protocol(build()['uncertainty_stages'],per_leaf=1)
        f.validate_model_protocol(protocol,[self.config])
        wrong=deepcopy(protocol)
        a,b=next((i,j) for i,x in enumerate(wrong['leaves']) for j,y in enumerate(wrong['leaves'])
            if x['probability']!=y['probability'])
        wrong['leaves'][a]['probability'],wrong['leaves'][b]['probability']=wrong['leaves'][b]['probability'],wrong['leaves'][a]['probability']
        with self.assertRaisesRegex(ValueError,'probability map'):f.validate_model_protocol(wrong,[self.config])
        wrong=deepcopy(protocol)
        wrong['leaves'][0]['seeds'],wrong['leaves'][1]['seeds']=wrong['leaves'][1]['seeds'],wrong['leaves'][0]['seeds']
        with self.assertRaisesRegex(ValueError,'wrong exogenous leaf'):f.validate_model_protocol(wrong,[self.config])

    def test_static_rows_keep_actor_clusters_and_deterministic_trace_rule(self):
        manifest=self.freeze(actors=[91,92],seeds=(0,1))
        result=f.evaluate(self.root/'frozen.json',self.root/'evaluation',workers=1)
        self.assertEqual(result['actual_rows'],4)
        self.assertEqual(result['missing_or_invalid'],0)
        self.assertEqual(result['summary'][0]['unique_environment_tapes'],2)
        self.assertEqual(sum('trace_path' in r for r in result['rows']),1)
        for row in result['rows']:
            self.assertEqual(row['checker_sha256'],manifest['source_hashes']['stage2/check.py'])
            self.assertEqual(len(row['physical_instance_sha256']),64)
        self.assertEqual(len((self.root/'evaluation'/'rows.jsonl').read_text().splitlines()),4)
        with self.assertRaises(FileExistsError):f.evaluate(self.root/'frozen.json',self.root/'evaluation',workers=1)

    def test_changed_selection_source_and_final_execution_require_explicit_act(self):
        manifest=self.freeze()
        final=json.loads(json.dumps(manifest));final['evaluation_role']='final'
        final['manifest_sha256']=f._sealed(final,'manifest_sha256')
        with self.assertRaisesRegex(ValueError,'execute-final'):f.verify_manifest(final)
        with patch.object(f,'source_hashes',return_value={}):
            with self.assertRaisesRegex(ValueError,'source changed'):f.verify_manifest(manifest)
        (self.root/'selection.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'specification changed'):f.verify_manifest(manifest)

    def test_artifact_contracts_adapters_and_all_policy_backends(self):
        from stage2.threshold import hashes,static_params
        from stage2.sequential import fingerprints,FEATURE_NAMES,ACTIONS
        weights=dict(wip_limit=3,mode='eco',lease_calibration=True)
        threshold=dict(configs=[self.config],params=[static_params(weights)],base_weights={},source_hashes=hashes())
        threshold['params'][0].pop('tool_distance');threshold['params'][0].pop('setup_weight')
        threshold['source_hashes']['stage2/threshold.py']='explicit-old-threshold'
        self.write('threshold.json',threshold)
        sequential=dict(configs=[self.config],policy=dict(kind='context_static',actions=[0]),base_weights={},
            source_hashes=fingerprints(),feature_names=list(FEATURE_NAMES),actions=list(ACTIONS))
        sequential['source_hashes']['stage2/sequential.py']='explicit-old-learner'
        self.write('sequential.json',sequential)
        context=dict(configs=[self.config],policy=dict(kind='context_static',actions=[0]),base_weights={},
            source_hashes={k:f.file_hash(f.ROOT/k) for k in f.CORE},actions=[dict(weights=weights)])
        self.write('teacher.json',context)
        methods=[dict(id='context',kind='context_static',checkpoint='teacher.json'),
            dict(id='threshold',kind='threshold',checkpoint='threshold.json',adapt_threshold=True),
            dict(id='sequential',kind='sequential',checkpoint='sequential.json',adapt_learner=True),
            dict(id='advanced',kind='advanced',weights=weights),dict(id='specialist',kind='specialist',weights=weights),
            dict(id='energy',kind='static',backend='energy',weights=weights,energy_policy=dict(strategy='baseline')),
            dict(id='burnin',kind='static',backend='burnin',weights=weights,boundary_tick=480),
            dict(id='mpc',kind='mpc',weights=weights,mpc=dict(actions=[],scenarios=1,interval=5760))]
        for method in methods:method['selection_provenance']=dict(data='synthetic DEVELOPMENT artifact',training_wall_seconds=0)
        manifest=self.freeze(methods)
        result=f.evaluate(self.root/'frozen.json',self.root/'evaluation',workers=1)
        self.assertEqual(result['actual_rows'],8)
        self.assertEqual(result['missing_or_invalid'],0,[(r['method_id'],r.get('error'),r.get('issues')) for r in result['rows']])
        adapted=[r for r in result['rows'] if r['method_id'] in ('threshold','sequential')]
        self.assertTrue(all(r['adapters'] for r in adapted))
        (self.root/'teacher.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'checkpoint changed'):f.verify_manifest(manifest)

    def test_failures_are_retained_and_suppress_valid_only_performance(self):
        methods=[dict(id='broken',kind='static',weights=dict(selector='not-a-solver'),
            selection_provenance=dict(data='deliberate development failure',training_wall_seconds=0))]
        self.freeze(methods,seeds=(0,1))
        result=f.evaluate(self.root/'frozen.json',self.root/'evaluation',workers=1)
        self.assertEqual(result['actual_rows'],2)
        self.assertEqual(result['missing_or_invalid'],2)
        self.assertTrue(all(r.get('error') for r in result['rows']))
        self.assertIn('performance_suppressed',result['summary'][0])
        self.assertNotIn('metrics',result['summary'][0])

    def test_parallel_execution_and_per_context_weight_selection(self):
        methods=[dict(id='selected',kind='static',weights_by_config=[dict(config=self.config,
            weights=dict(wip_limit=2,lease_calibration=True))],
            selection_provenance=dict(data='explicit DEVELOPMENT choice',training_wall_seconds=0))]
        self.freeze(methods,seeds=(0,1))
        result=f.evaluate(self.root/'frozen.json',self.root/'parallel',workers=2)
        self.assertEqual(result['actual_rows'],2)
        self.assertEqual(result['missing_or_invalid'],0)

    def test_hard_tool_homes_qa_guard_and_due_admission_match_direct_policies(self):
        from stage2.tooling import run
        from stage2.spec import build
        from stage2.check import check_trace
        weights=dict(wip_limit=3,mode='standard',lease_calibration=True,qa_guard_threshold=2,admission_rule='due')
        method=dict(kind='static',backend='tooling',specialist=True,tool_policy=dict(mode='hard'))
        instance=build(**self.config,seed=0)
        direct=run(instance,weights,tool_policy=dict(mode='hard'),specialist=True)
        baseline=f._dispatch_factory(instance,weights,None,method,self.config).run()
        composed=f._dispatch_factory(instance,weights,None,dict(method,admission=True),self.config).run()
        for key in ('operations','moves','worker_moves','events','energy','metrics'):
            self.assertEqual(direct[key],baseline[key],key)
            self.assertEqual(direct[key],composed[key],key)
        self.assertTrue(check_trace(composed)['valid'])

    def test_combined_tooling_admission_backend_is_sealed_and_independently_checked(self):
        method=dict(id='hard-home-guard-admission',kind='tooling',specialist=True,admission=True,
            weights=dict(wip_limit=3,mode='standard',lease_calibration=True,qa_guard_threshold=2,admission_rule='family'),
            tool_policy_by_config=[dict(config=self.config,tool_policy=dict(mode='hard'))],
            selection_provenance=dict(data='DEVELOPMENT API integration only',training_wall_seconds=0))
        manifest=self.freeze([method])
        self.assertIn('stage2/tooling.py',manifest['source_hashes'])
        self.assertIn('stage2/admission.py',manifest['source_hashes'])
        result=f.evaluate(self.root/'frozen.json',self.root/'combined',workers=1)
        self.assertEqual(result['missing_or_invalid'],0,result['rows'])
        trace=json.loads(Path(result['rows'][0]['trace_path']).read_text())
        self.assertTrue(trace['admission_history'])
        self.assertEqual(trace['algorithm_audit']['threshold'],2)
        self.assertEqual(trace['algorithm_audit']['tool_assignment']['policy']['mode'],'hard')

    def test_kitting_direct_due_admission_composition_and_off_equivalence(self):
        from stage2.kitting import run as kit_run
        from stage2.tooling import run as tool_run
        from stage2.spec import build
        weights=dict(wip_limit=3,mode='standard',lease_calibration=True,qa_guard_threshold=2,admission_rule='due')
        method=dict(kind='static',backend='kitting',specialist=True,admission=True,tool_policy=dict(mode='hard'))
        instance=build(**self.config,seed=0)
        expected=kit_run(instance,weights,tool_policy=dict(mode='hard'),specialist=True,admission=True)
        actual=f._dispatch_factory(instance,weights,None,method,self.config).run()
        off=f._dispatch_factory(instance,weights,None,dict(method,kit_reservation=False),self.config).run()
        old=tool_run(instance,weights,tool_policy=dict(mode='hard'),specialist=True)
        for key in ('operations','moves','worker_moves','events','energy','metrics'):
            self.assertEqual(expected[key],actual[key],key)
            self.assertEqual(old[key],off[key],key)

    def test_kitting_manifest_and_actual_paired_causality(self):
        from stage2.check import check_paired_causality
        method=dict(id='explicit-kitting',kind='kitting',specialist=True,admission=True,
            tool_policy=dict(mode='hard'),weights_by_config=[dict(config=self.config,
            weights=dict(wip_limit=3,mode='standard',lease_calibration=True,qa_guard_threshold=2,admission_rule='due'))],
            selection_provenance=dict(data='DEVELOPMENT integration only',training_wall_seconds=0))
        self.freeze([method],seeds=(0,1),trace_policy='all')
        manifest=json.loads((self.root/'frozen.json').read_text())
        self.assertIn('stage2/kitting.py',manifest['source_hashes'])
        self.assertTrue(manifest['methods'][0]['kit_reservation'])
        # Retention was predeclared before either tape's outcomes.
        result=f.evaluate(self.root/'frozen.json',self.root/'kitting',workers=1)
        self.assertEqual(result['missing_or_invalid'],0,result['rows'])
        traces=[json.loads(Path(row['trace_path']).read_text()) for row in result['rows']]
        self.assertTrue(all(t['algorithm_audit']['kit_reservation']['enabled'] for t in traces))
        self.assertTrue(check_paired_causality(traces)['valid'])

    def test_kitting_cannot_silently_change_other_backends_or_battery(self):
        method=dict(id='unsupported-composition',kind='static',kit_reservation=True,
            selection_provenance=dict(data='DEVELOPMENT rejection',training_wall_seconds=0))
        with self.assertRaisesRegex(ValueError,'explicitly selected kitting'):self.freeze([method])
        (self.root/'selection.json').unlink();(self.root/'protocol.json').unlink()
        method.update(kind='kitting',energy_policy=dict(strategy='solar-tariff'))
        with self.assertRaisesRegex(ValueError,'baseline battery'):self.freeze([method])

    def test_recovery_matches_direct_composition_and_requires_explicit_options(self):
        from stage2.kit_recovery import run
        from stage2.spec import build
        from stage2.check import check_trace
        weights=dict(wip_limit=3,lease_calibration=True,qa_guard_threshold=4,admission_rule='family')
        method=dict(kind='static',backend='recovery',specialist=True,admission=True,
            tool_policy=dict(mode='hard'),kit_reservation=True,recovery_policy=dict(enabled=True))
        instance=build(**self.config,seed=0)
        direct=run(instance,weights,tool_policy=method['tool_policy'],kit_reservation=True,
            admission=True,recovery_policy=method['recovery_policy'])
        composed=f._dispatch_factory(instance,weights,None,method,self.config).run()
        for key in ('operations','moves','worker_moves','events','energy','metrics'):
            self.assertEqual(direct[key],composed[key],key)
        self.assertTrue(check_trace(composed)['valid'])
        selected=dict(method,id='recovery',selection_provenance=dict(data='DEVELOPMENT integration only'))
        manifest=self.freeze([selected])
        self.assertIn('stage2/kit_recovery.py',manifest['source_hashes'])
        result=f.evaluate(self.root/'frozen.json',self.root/'recovery',workers=1)
        self.assertEqual(result['missing_or_invalid'],0,result['rows'])

    def test_scoped_recovery_and_mpc_are_explicit_checked_and_match_direct_execution(self):
        from stage2.recovery_mpc import run
        from stage2.spec import build
        weights=dict(wip_limit=3,lease_calibration=True,qa_guard_threshold=4,admission_rule='family')
        method=dict(id='recovery-planner',kind='recovery_mpc',specialist=True,admission=True,weights=weights,
            tool_policy=dict(mode='hard'),recovery_policy=dict(enabled=True),
            routing_policy=dict(eta_processes=['QA']),mpc=dict(actions=[],scenarios=1,interval=5760,seed=39,
                physical_check_futures=True),selection_provenance=dict(data='DEVELOPMENT integration only'))
        self.freeze([method]);result=f.evaluate(self.root/'frozen.json',self.root/'recovery-mpc',workers=1)
        self.assertEqual(result['missing_or_invalid'],0,result['rows'])
        row=result['rows'][0];trace=json.loads(Path(row['trace_path']).read_text())
        expected=run(build(**self.config,seed=0),dict(weights,policy_seed=91),tool_policy=dict(mode='hard'),
            recovery_policy=dict(enabled=True),routing_policy=method['routing_policy'],**method['mpc'])
        for key in ('operations','moves','worker_moves','events','energy','metrics'):
            self.assertEqual(expected[key],trace[key],key)
        self.assertGreater(row['planning_wall_seconds'],0)
        self.assertIn('stage2/recovery_mpc.py',result['source_hashes'])

    def test_actor_seed_overrides_inherited_initial_and_callback_seeds(self):
        from stage2.threshold import hashes,static_params
        artifact=dict(configs=[self.config],params=[static_params(dict(wip_limit=3))],
            base_weights=dict(policy_seed=0),source_hashes=hashes())
        checkpoint=self.write('actor-threshold.json',artifact)
        context=self.write('actor-context.json',dict(configs=[self.config],policy=dict(kind='context_static',actions=[0]),
            base_weights=dict(wip_limit=3,policy_seed=0),actions=[dict(weights=dict(wip_limit=4,policy_seed=0))],
            source_hashes={name:f.file_hash(f.ROOT/name) for name in f.CORE}))
        for kind in ('static','threshold','context_static'):
            method=dict(kind=kind,weights=dict(policy_seed=0))
            if kind=='threshold':method['checkpoint']=str(checkpoint)
            if kind=='context_static':method.update(checkpoint=str(context),weights=dict(wip_limit=8,policy_seed=0))
            weights,controller,_=f._controller(method,self.config,917)
            self.assertEqual(weights['policy_seed'],917)
            if kind=='context_static':self.assertEqual(weights['wip_limit'],8)
            if controller is not None:self.assertEqual(controller.base['policy_seed'],917)

    def test_reward_backend_preserves_corrected_direct_execution_and_actual_telemetry(self):
        from stage2.selector_reward import run
        from stage2.spec import build
        weights=dict(wip_limit=4,selector='qaoa',lease_calibration=True,qa_guard_threshold=4,admission_rule='family')
        method=dict(id='corrected',kind='recovery',specialist=True,admission=True,weights=weights,
            tool_policy=dict(mode='hard'),recovery_policy=dict(enabled=True),reward_mode='no-batch',
            selection_provenance=dict(data='DEVELOPMENT reward composition'))
        self.freeze([method]);result=f.evaluate(self.root/'frozen.json',self.root/'reward',workers=1)
        self.assertEqual(result['missing_or_invalid'],0,result['rows'])
        row=result['rows'][0];trace=json.loads(Path(row['trace_path']).read_text())
        direct=run(build(**self.config,seed=0),dict(weights,policy_seed=91),admission=True,
            tool_policy=dict(mode='hard'),recovery_policy=dict(enabled=True),reward_mode='no-batch')
        for key in ('operations','moves','worker_moves','events','energy','metrics'):
            self.assertEqual(direct[key],trace[key],key)
        self.assertEqual(trace['algorithm_audit']['selector_reward']['mode'],'no-batch')
        self.assertGreater(row['qubo_telemetry']['qaoa_calls'],0)
        self.assertEqual(row['qubo_telemetry']['decode_mismatches'],0)

    def test_adaptive_checkpoint_owns_decoder_and_matches_direct_inference(self):
        from copy import deepcopy
        from stage2 import adaptive_recovery as a
        from stage2.spec import build
        from stage2.sequential import FEATURE_NAMES
        weights=dict(wip_limit=4,mode='standard',selector='priority',lease_calibration=True,
            qa_guard_threshold=4,admission_rule='family',worker_calendar=True)
        options=dict(tool_policy=dict(mode='hard'),recovery_policy=dict(enabled=True),admission=True,
            kit_reservation=True,routing_policy=dict(eta_processes=['QA'],free_buffer_processes=[]))
        context=dict(config=self.config,weights=weights,solver_options=options)
        policy=dict(kind='schedule',schedule=[1,3,1,3,1,3,1,3])
        artifact=dict(schema='stage2-adaptive-recovery-policy.v1',source_hashes=a.hashes(),configs=[self.config],
            contexts=[context],policies_by_context=[policy],actions=deepcopy(list(a.ACTIONS)),feature_names=list(FEATURE_NAMES),interval=720)
        checkpoint=self.write('adaptive.json',artifact)
        method=dict(id='adaptive',kind='adaptive_recovery',checkpoint=str(checkpoint),
            maintenance_outage_guard=True,
            selection_provenance=dict(data='DEVELOPMENT contract fixture'))
        self.freeze([method]);result=f.evaluate(self.root/'frozen.json',self.root/'adaptive',workers=1)
        self.assertEqual(result['missing_or_invalid'],0,result['rows'])
        trace=json.loads(Path(result['rows'][0]['trace_path']).read_text())
        from stage2.maintenance_guard import run as guarded_run
        direct=guarded_run(build(**self.config,seed=0),dict(weights,policy_seed=91),
            a.Controller(policy,weights,91,True,720),maintenance_outage_guard=True,**options)
        for key in ('operations','moves','worker_moves','events','energy','metrics'):
            self.assertEqual(direct[key],trace[key],key)
        with self.assertRaisesRegex(ValueError,'options must come'):
            f._normalize_adaptive(dict(method,weights=dict(wip_limit=8)))
        artifact['actions'][0]['wip_limit']=999;checkpoint.write_text(json.dumps(artifact))
        with self.assertRaisesRegex(ValueError,'action/feature'):f._adaptive_artifact(checkpoint)

    def test_reward_mpc_composition_cannot_silently_diverge_from_planned_futures(self):
        method=dict(id='unsupported-reward-planner',kind='mpc',reward_mode='no-batch',
            selection_provenance=dict(data='DEVELOPMENT rejection'))
        with self.assertRaisesRegex(ValueError,'non-MPC dispatch'):self.freeze([method])

    def test_eighteen_action_artifact_preserves_mode_inference_and_required_guard(self):
        from copy import deepcopy
        from stage2 import adaptive_modes as a
        from stage2.sequential import FEATURE_NAMES
        from stage2.maintenance_guard import run
        from stage2.spec import build
        weights=dict(wip_limit=4,mode='standard',selector='priority',lease_calibration=True,
            qa_guard_threshold=4,admission_rule='family',worker_calendar=True)
        options=dict(tool_policy=dict(mode='hard'),recovery_policy=dict(enabled=True),admission=True,
            kit_reservation=True,routing_policy=dict(eta_processes=[],free_buffer_processes=[]))
        policy=dict(kind='schedule',schedule=[0,17,0,17,0,17,0,17])
        artifact=dict(schema='stage2-adaptive-modes-policy.v1',source_hashes=a.hashes(),configs=[self.config],
            contexts=[dict(config=self.config,weights=weights,solver_options=options)],
            policies_by_context=[policy],actions=deepcopy(list(a.ACTIONS)),feature_names=list(FEATURE_NAMES),
            interval=720,maintenance_outage_guard=True,identity_supplement=True)
        checkpoint=self.write('adaptive-modes.json',artifact)
        method=dict(id='eighteen',kind='adaptive_modes',checkpoint=str(checkpoint),
            selection_provenance=dict(data='DEVELOPMENT eighteen-action contract'))
        manifest=self.freeze([method]);self.assertTrue(manifest['methods'][0]['maintenance_outage_guard'])
        result=f.evaluate(self.root/'frozen.json',self.root/'eighteen',workers=1)
        self.assertEqual(result['missing_or_invalid'],0,result['rows'])
        trace=json.loads(Path(result['rows'][0]['trace_path']).read_text())
        direct=run(build(**self.config,seed=0),dict(weights,policy_seed=91),a.Controller(policy,weights,91,True,720),
            maintenance_outage_guard=True,**options)
        for key in ('operations','moves','worker_moves','events','energy','metrics'):
            self.assertEqual(direct[key],trace[key],key)
        with self.assertRaisesRegex(ValueError,'cannot disable'):
            f._normalize_adaptive(dict(method,maintenance_outage_guard=False))
        with self.assertRaisesRegex(ValueError,'Matching adaptive'):
            f._adaptive_artifact(checkpoint,'adaptive_recovery')

    def test_completion_composition_preserves_direct_physical_execution_and_objective(self):
        from stage2.completion_policy import run
        from stage2.spec import build
        weights=dict(wip_limit=4,mode='standard',selector='priority',lease_calibration=True,
            qa_guard_threshold=4,admission_rule='family',worker_calendar=True)
        options=dict(tool_policy=dict(mode='hard'),recovery_policy=dict(enabled=True),admission=True,
            kit_reservation=True,routing_policy=dict(eta_processes=['QA'],free_buffer_processes=[]),
            completion_policy=dict(credit_minutes=270,reclaim_dead_slots=False))
        method=dict(id='completion',kind='recovery',specialist=True,weights=weights,**options,
            selection_provenance=dict(data='DEVELOPMENT completion integration'))
        self.freeze([method]);result=f.evaluate(self.root/'frozen.json',self.root/'completion',workers=1)
        self.assertEqual(result['missing_or_invalid'],0,result['rows'])
        trace=json.loads(Path(result['rows'][0]['trace_path']).read_text())
        direct=run(build(**self.config,seed=0),dict(weights,policy_seed=91),**options)
        for key in ('operations','moves','worker_moves','events','energy','metrics'):
            self.assertEqual(direct[key],trace[key],key)
        self.assertEqual(trace['algorithm_audit']['completion_policy']['policy']['credit_minutes'],270)

    def test_replicated_fixed_seed_mpc_is_rejected(self):
        method=dict(id='fixed-planner',kind='mpc',mpc=dict(seed=42),
            selection_provenance=dict(data='DEVELOPMENT rejection'))
        with self.assertRaisesRegex(ValueError,'actor-controlled planning seeds'):
            self.freeze([method],actors=[91,92])

    def test_changed_instance_shortened_execution_and_terminal_failure_are_not_scored(self):
        from copy import deepcopy
        from stage2.engine import run
        from stage2.spec import build
        from stage2.check import check_trace
        base=run(build(**self.config,seed=0),dict(wip_limit=3,lease_calibration=True))
        self.freeze()
        class WitnessFactory:
            def __init__(self,trace):self.trace=trace
            def run(self):return deepcopy(self.trace)
        for variant in ('instance','horizon','terminal','metrics'):
            trace=deepcopy(base)
            if variant=='instance':trace['instance']['machines'][0]['input_capacity']+=1
            if variant=='horizon':trace['horizon_ticks']-=1
            if variant=='metrics':trace['metrics']['shipped']+=1
            checked=check_trace(trace)
            if variant=='terminal':checked['terminal_requirements_met']=False
            with patch.object(f,'_dispatch_factory',return_value=WitnessFactory(trace)),\
                 patch('stage2.check.check_trace',return_value=checked):
                result=f.evaluate(self.root/'frozen.json',self.root/variant,workers=1)
            self.assertEqual(result['missing_or_invalid'],1,variant)
            self.assertIn('performance_suppressed',result['summary'][0])

    def test_actual_selector_telemetry_separates_coupled_simulation_and_oversize_fallback(self):
        from stage2.qubo import select
        single=select([dict(id='C0',reward=2)],method='qaoa',seed=3)
        coupled=select([dict(id='C0',reward=2,resources={'power':2}),
            dict(id='C1',reward=3,resources={'power':3})],capacities={'power':3},method='qaoa',seed=3)
        many=[dict(id='C'+str(i),reward=i+1) for i in range(6)]
        conflicts=[('C'+str(i),'C'+str(j)) for i in range(6) for j in range(i)]
        fallback=select(many,conflicts,method='qaoa',seed=3)
        results=[single,coupled,fallback]
        trace=dict(qubo_decisions=[dict(tick=i,result=r,committed=r['selected']) for i,r in enumerate(results)])
        evidence=f.qubo_telemetry(trace)
        self.assertEqual(evidence['calls'],3)
        self.assertEqual(evidence['coupled_calls'],2)
        self.assertEqual(evidence['qaoa_requested_calls'],3)
        self.assertEqual(evidence['qaoa_calls'],2)
        self.assertEqual(evidence['coupled_qaoa_calls'],1)
        self.assertEqual(evidence['uncoupled_qaoa_calls'],1)
        self.assertEqual(evidence['trivial_1bit_qaoa_calls'],1)
        self.assertEqual(evidence['fallback_calls'],1)
        self.assertEqual(evidence['qaoa_oversize_classical_fallback_calls'],1)
        self.assertEqual(evidence['max_total_bits'],6)
        self.assertEqual(evidence['max_core_bits'],6)
        self.assertEqual(evidence['max_slack_bits'],2)
        self.assertEqual(evidence['max_actual_simulated_quantum_bits'],4)
        self.assertEqual(evidence['physical_quantum_calls'],0)
        self.assertEqual(evidence['decode_mismatches'],0)
        timing=evidence['time_breakdown_seconds']
        self.assertEqual(timing['result_elapsed_observed_calls'],3)
        self.assertEqual(timing['qaoa_angle_optimization_observed_calls'],2)
        self.assertIsNone(timing['encoding_seconds'])
        self.assertIsNone(timing['decoding_seconds'])

    def test_decode_mismatch_invalidates_row_without_becoming_solver_repair(self):
        from copy import deepcopy
        from stage2.engine import run
        from stage2.spec import build
        from stage2.qubo import select
        trace=run(build(**self.config,seed=0),dict(wip_limit=3,lease_calibration=True))
        chosen=select([dict(id='C0',reward=2)],method='greedy')
        self.assertFalse(chosen['repaired'])
        trace['qubo_decisions']=[dict(tick=0,result=chosen,committed=[])]
        self.freeze()
        class WitnessFactory:
            def run(self):return deepcopy(trace)
        with patch.object(f,'_dispatch_factory',return_value=WitnessFactory()):
            result=f.evaluate(self.root/'frozen.json',self.root/'decode-failure',workers=1)
        row=result['rows'][0]
        self.assertFalse(row['valid'])
        self.assertEqual(row['qubo_telemetry']['decode_mismatches'],1)
        self.assertEqual(row['qubo_telemetry']['repairs'],0)
        self.assertTrue(any(issue['code']=='qubo_decode_commit_mismatch' for issue in row['issues']))
        saved=json.loads(Path(row['trace_path']).read_text())
        self.assertFalse(saved['qubo_decisions'][0]['result']['repaired'])


if __name__=='__main__':unittest.main()
