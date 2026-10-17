"""Synthetic bookkeeping corruption fixtures; no factory outcomes are generated."""
from copy import deepcopy
import hashlib,json
from pathlib import Path
import tempfile,unittest
from tests.stage2.test_compare_evaluations import payload,reseal
from stage2 import final_report as r

class FinalReportingTests(unittest.TestCase):
    def fixture(self,root):
        m,e=payload();p=m['protocol']['payload'];p['schema']='stage2-stratified-final-protocol.v1';p['seed_role']='FINAL'
        for leaf in p['leaves']:leaf['seeds']=[s+10000 for s in leaf['seeds']]
        p.pop('protocol_sha256');p['protocol_sha256']=hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest();m['evaluation_role']=e['evaluation_role']='final';e['protocol_sha256']=p['protocol_sha256'];e['missing_or_invalid']=0
        for row in e['rows']:
            row['seed']+=10000;row['tape_id']=f"leaf-{row['leaf']}:seed-{row['seed']}";row['protocol_sha256']=p['protocol_sha256'];row['qubo_telemetry']={}
        reseal(m,e);directory=root/'evidence';directory.mkdir();(directory/'manifest.json').write_text(json.dumps(m));(directory/'evaluation.json').write_text(json.dumps(e));(directory/'rows.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in e['rows']));index=root/'index.json';index.write_text(json.dumps({'mpc-12':str(directory)}));return e,directory,index
    def test_cached_summary_cannot_drop_group_or_forge_mean(self):
        for cached in ([],[dict(method_id='left',config=dict(orders=2,horizon=5760,profile='full'),metrics=dict(unfulfilled=dict(mean=999))) ]):
            with tempfile.TemporaryDirectory() as td:
                root=Path(td);e,d,index=self.fixture(root);e['summary']=cached;(d/'evaluation.json').write_text(json.dumps(e))
                result=r.report(index,root/'report',include_comparisons=False,allow_partial=True)
                groups=json.loads((root/'report/all-groups.json').read_text());self.assertEqual(len(groups),1);self.assertAlmostEqual(groups[0]['summary']['metrics']['unfulfilled']['mean'],.375)
                self.assertEqual(result['cohort_scope'],'partial');self.assertEqual(result['expected_comparison_count'],41);self.assertIn('frontier',result['missing_cohorts'])
    def test_missing_group_and_invalid_rows_cannot_be_hidden_by_empty_summary(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);e,d,index=self.fixture(root)
            with self.assertRaisesRegex(ValueError,'Missing final cohorts'):r.report(index,root/'incomplete',include_comparisons=False)
            e['summary']=[];e['rows'][0]['valid']=False;(d/'evaluation.json').write_text(json.dumps(e));(d/'rows.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in e['rows']))
            with self.assertRaisesRegex(ValueError,'failed/invalid'):r.report(index,root/'invalid',include_comparisons=False,allow_partial=True)

if __name__=='__main__':unittest.main()

class BoundaryProbabilityTests(unittest.TestCase):
    def test_zero_events_do_not_produce_false_zero_width_probability_interval(self):
        m,e=payload(actors=(91,))
        result=r.mean_uncertainty(e['rows'],m['protocol']['payload'],lambda row:0.,bootstrap=40,probability=True)
        self.assertIsNone(result['percentile_interval_95'])
        self.assertGreater(result['boundary_probability_bound']['interval'][1],0)
        # Equal weights reduce the conservative boundary expression to the
        # ordinary one-sided all-zero binomial bound.
        for leaf in m['protocol']['payload']['leaves']:leaf['per_tape_weight']=.25
        equal=r.mean_uncertainty(e['rows'],m['protocol']['payload'],lambda row:1.,bootstrap=40,probability=True)
        self.assertAlmostEqual(equal['boundary_probability_bound']['interval'][0],.05**.25)
        self.assertEqual(equal['boundary_probability_bound']['interval'][1],1.)
