"""Metadata corruption and paired-estimator tests; synthetic fixtures are not runs."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from stage2.compare_evaluations import compare_payloads,load_evidence,digest,PHYSICAL_SOURCES
from stage2.statistics import paired_report

CONFIG=dict(orders=2,horizon=5760,profile='full')


def reseal(manifest,evaluation):
    unsigned=deepcopy(manifest);unsigned.pop('manifest_sha256',None)
    manifest['manifest_sha256']=digest(unsigned)
    evaluation['manifest_sha256']=manifest['manifest_sha256']
    for row in evaluation['rows']:row['manifest_sha256']=manifest['manifest_sha256']


def payload(method_id='left',dispatch='old',actors=(91,92),delta=0):
    protocol=dict(schema='stage2-development-protocol.v1',seed_role='DEVELOPMENT',total_tapes=4,
        leaves=[dict(outcomes=['devA'],seeds=[0,1],probability=[1,4],per_tape_weight=.125),
                dict(outcomes=['devB'],seeds=[2,3],probability=[3,4],per_tape_weight=.375)])
    protocol['protocol_sha256']=hashlib.sha256(json.dumps(protocol,sort_keys=True).encode()).hexdigest()
    sources={name:digest(name) for name in PHYSICAL_SOURCES}
    sources['stage2/dispatch.py']=digest(dispatch)
    checkpoint='/remote/absolute/checkpoint.json'
    method=dict(id=method_id,kind='static',weights={},checkpoint=checkpoint)
    manifest=dict(schema='stage2-frozen-selected-policy-evaluation.v1',phase='frozen-selection',evaluation_role='development',
        configs=[CONFIG],actor_seeds=list(actors),actor_seed_policy='Fixture declares actor override; no actual execution claim',
        methods=[method],protocol=dict(payload=protocol,path='/remote/absolute/protocol.json'),
        selection_spec=dict(path='/remote/absolute/selection.json'),artifacts={checkpoint:dict(sha256=digest('checkpoint'))},
        source_hashes=sources,runtime=dict(python='synthetic',platform='fixture'))
    rows=[]
    for leaf_index,leaf in enumerate(protocol['leaves']):
        for seed in leaf['seeds']:
            for actor in actors:
                missing=int(seed==3);debt=20+5*seed+actor%2*10+delta
                checked=dict(delivered_orders=2-missing,unfulfilled_orders=missing,terminal_deadline_debt_ticks=debt,
                    tardiness_ticks=debt-5*missing,total_cost=100.+seed+delta,carbon_kg=50.+seed+delta)
                rows.append(dict(method_id=method_id,config=CONFIG,seed=seed,policy_seed=actor,leaf=leaf_index,
                    leaf_outcomes=leaf['outcomes'],tape_id=f'leaf-{leaf_index}:seed-{seed}',tape_weight=leaf['per_tape_weight'],
                    protocol_sha256=protocol['protocol_sha256'],checker_sha256=sources['stage2/check.py'],
                    checkpoint_sha256={checkpoint:digest('checkpoint')},valid=True,issues=[],terminal_requirements_met=True,
                    physical_instance_sha256=digest(['instance',seed]),executed_instance_sha256=digest(['instance',seed]),
                    checker_metrics=checked,metrics=dict(orders=2,shipped=2-missing,total_tardiness_ticks=debt,
                    total_cost=checked['total_cost'],carbon_kg=checked['carbon_kg'],all_orders_fulfilled=missing==0,terminal_soc_satisfied=True)))
    evaluation=dict(schema=manifest['schema'],evaluation_role='development',protocol_sha256=protocol['protocol_sha256'],
        expected_rows=len(rows),actual_rows=len(rows),source_hashes=sources,rows=rows,runtime=manifest['runtime'])
    reseal(manifest,evaluation)
    return manifest,evaluation


class CrossReportTests(unittest.TestCase):
    def compare(self,left=None,right=None,**kwargs):
        lm,le=left or payload();rm,re=right or payload('right','new',delta=-2)
        return compare_payloads(lm,le,'left',rm,re,'right',CONFIG,bootstrap=40,**kwargs)

    def test_cross_dispatch_groups_use_same_instances_and_environment_clusters(self):
        result=self.compare()
        self.assertIn('stage2/dispatch.py',result['algorithm_source_differences'])
        self.assertEqual(result['metrics']['deadline_debt']['environment_tapes'],4)
        self.assertEqual(result['metrics']['deadline_debt']['actor_replicas_left'],8)
        self.assertAlmostEqual(result['metrics']['deadline_debt']['mean_difference'],-2)
        for endpoint in result['metrics']['deadline_debt']['mean_difference_percentile_bootstrap_95']:
            self.assertAlmostEqual(endpoint,-2)
        for endpoint in result['metrics']['deadline_debt']['cvar90_difference_percentile_bootstrap_95']:
            self.assertAlmostEqual(endpoint,-2)
        self.assertNotIn('wall_seconds',result['metrics'])

    def test_different_actor_replica_counts_remain_nested_not_extra_tapes(self):
        result=self.compare(right=payload('right','new',actors=(93,),delta=-2))
        self.assertEqual(result['metrics']['missing']['environment_tapes'],4)
        self.assertEqual(result['metrics']['missing']['actor_replicas_right'],4)
        self.assertEqual(result['metrics']['missing']['actor_replicas_left'],8)

    def test_declared_identity_supplement_is_required_and_equal_across_groups(self):
        left=payload();right=payload('right','new')
        for manifest,evaluation in (left,right):
            manifest['source_hashes']['stage2/identity_audit.py']=digest('identity auditor')
            evaluation['source_hashes']=deepcopy(manifest['source_hashes'])
            for row in evaluation['rows']:
                row['identity_audit']=dict(valid=True,issues=[],provenance=dict(
                    auditor_sha256=digest('identity auditor'),instance_anchor='supplied_instance'))
            reseal(manifest,evaluation)
        self.assertIn('stage2/identity_audit.py',self.compare(left,right)['supplemental_verifier_sources'])
        changed=deepcopy(right);changed[1]['rows'][0]['identity_audit']['valid']=False
        with self.assertRaisesRegex(ValueError,'identity supplement'):self.compare(left,changed)
        with self.assertRaisesRegex(ValueError,'Physical/verifier source'):self.compare(left,payload('right','new'))

    def test_low_level_statistics_accepts_mixed_physics_but_strict_wrapper_rejects(self):
        lm,le=payload();rm,re=payload('right','new',delta=-2)
        for row in re['rows']:
            if row['seed']==0:row.update(physical_instance_sha256=digest('different'),executed_instance_sha256=digest('different'))
        # Demonstrates the caller obligation of the deliberately low-level API.
        bare=paired_report(le['rows'],re['rows'],lm['protocol']['payload'],lambda row:row['checker_metrics']['total_cost'],10)
        self.assertEqual(bare['environment_tapes'],4)
        with self.assertRaisesRegex(ValueError,'Per-tape physical'):self.compare((lm,le),(rm,re))

    def test_physical_source_change_is_rejected_even_with_self_consistent_rows(self):
        rm,re=payload('right','new');rm['source_hashes']['stage2/engine.py']=digest('changed engine')
        re['source_hashes']=deepcopy(rm['source_hashes']);reseal(rm,re)
        with self.assertRaisesRegex(ValueError,'Physical/verifier source'):self.compare(right=(rm,re))

    def test_invalid_terminal_or_legacy_cached_rows_cannot_enter_comparison(self):
        for field,value in (('valid',False),('terminal_requirements_met',False),('executed_instance_sha256',digest('changed'))):
            rm,re=payload('right','new');re['rows'][0][field]=value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):self.compare(right=(rm,re))
        rm,re=payload('right','new');re['rows'][0].pop('checker_metrics')
        with self.assertRaisesRegex(ValueError,'independent checker metrics'):self.compare(right=(rm,re))

    def test_actor_override_contract_and_missing_replicas_are_required(self):
        rm,re=payload('right','new');rm.pop('actor_seed_policy');reseal(rm,re)
        with self.assertRaisesRegex(ValueError,'override contract'):self.compare(right=(rm,re))
        rm,re=payload('right','new');re['rows'].pop();re['actual_rows']-=1
        with self.assertRaisesRegex(ValueError,'Missing executions'):self.compare(right=(rm,re))

    def test_cached_metric_and_probability_weight_corruptions_are_rejected(self):
        for mutation in ('metric','weight','checkpoint','manifest'):
            rm,re=payload('right','new')
            if mutation=='metric':re['rows'][0]['metrics']['carbon_kg']+=1
            elif mutation=='weight':re['rows'][0]['tape_weight']=.5
            elif mutation=='checkpoint':re['rows'][0]['checkpoint_sha256']={}
            else:rm['configs']=[dict(CONFIG,orders=3)]
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):self.compare(right=(rm,re))

    def test_runtime_drift_is_disclosed_not_reinterpreted_as_speedup(self):
        rm,re=payload('right','new');re['runtime']=dict(python='different actual runtime')
        result=self.compare(right=(rm,re))
        self.assertFalse(result['execution_runtime_equal'])
        self.assertTrue(result['freeze_execution_runtime_drift']['right'])
        self.assertIn('no wall-time speedup',result['cost_scope'])

    def test_downloaded_remote_paths_are_opaque_but_rows_log_must_match(self):
        manifest,evaluation=payload()
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary)
            (folder/'manifest.json').write_text(json.dumps(manifest));(folder/'evaluation.json').write_text(json.dumps(evaluation))
            (folder/'rows.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in reversed(evaluation['rows'])))
            m,e,source=load_evidence(folder)
            self.assertEqual(m['selection_spec']['path'],'/remote/absolute/selection.json')
            self.assertEqual(len(source['files']),3)
            (folder/'rows.jsonl').write_text('')
            with self.assertRaisesRegex(ValueError,'disagree'):load_evidence(folder)


if __name__=='__main__':unittest.main()
