"""Integrity/aggregation tests only; no training or reserved tape execution."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from stage2 import adaptive_evidence as e

SMOKE=Path(__file__).resolve().parents[2]/'output/stage2-search/adaptive-recovery-ppo-smoke'


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        if not SMOKE.exists():self.skipTest('Retained development smoke unavailable')

    def copy_run(self,root):
        target=Path(root)/'run';shutil.copytree(SMOKE,target);return target

    def test_cost_counters_and_splits_recomputed_from_raw_rows(self):
        data=e.inspect_run(SMOKE);rows=data['rows'];cost=data['costs']
        self.assertEqual(cost['fit_rollouts'],72)
        self.assertEqual(cost['validation_rollouts'],48)
        self.assertAlmostEqual(cost['summed_rollout_cpu_seconds'],sum(r['cpu_seconds'] for r in rows))
        self.assertAlmostEqual(cost['summed_rollout_wall_seconds'],sum(r['wall_seconds'] for r in rows))
        self.assertNotEqual(cost['summed_rollout_cpu_seconds'],cost['summed_rollout_wall_seconds'])

    def test_new_readonly_seal_preserves_originals_selected_blobs_and_detects_tamper(self):
        before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in SMOKE.rglob('*') if p.is_file()}
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'seal'
            with self.assertRaisesRegex(ValueError,'attestation'):e.seal(SMOKE,out)
            result=e.seal(SMOKE,out,execution_complete=True)
            self.assertEqual(result['status'],'sealed_without_replay')
            self.assertEqual(result['replay_count'],0)
            self.assertTrue(e.verify_seal(out)['valid'])
            policy=result['selected_policies'][0];payload=json.loads((out/policy['path']).read_bytes())
            self.assertEqual(e.digest(e.canonical(payload)),policy['policy_sha256'])
            self.assertEqual((out/'original/episodes.jsonl').read_bytes(),(SMOKE/'episodes.jsonl').read_bytes())
            with self.assertRaisesRegex(ValueError,'new evidence'):e.seal(SMOKE,out,execution_complete=True)
            changed=out/'report.json';changed.chmod(0o644);changed.write_text('{}')
            with self.assertRaisesRegex(ValueError,'digest mismatch'):e.verify_seal(out)
        self.assertEqual(before,{p:hashlib.sha256(p.read_bytes()).hexdigest() for p in before})

    def test_rejects_incomplete_log_forbidden_tape_and_corrupt_source_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            run=self.copy_run(temp);rows=(run/'episodes.jsonl').read_text().splitlines()
            (run/'episodes.jsonl').write_text('\n'.join(rows[:-1])+'\n')
            with self.assertRaisesRegex(ValueError,'counters'):e.inspect_run(run)
        with tempfile.TemporaryDirectory() as temp:
            run=self.copy_run(temp);rows=(run/'episodes.jsonl').read_text().splitlines();r=json.loads(rows[0]);r['seed']=10000;rows[0]=json.dumps(r)
            (run/'episodes.jsonl').write_text('\n'.join(rows)+'\n')
            with self.assertRaisesRegex(ValueError,'Validation seed'):e.inspect_run(run)
        with tempfile.TemporaryDirectory() as temp:
            run=self.copy_run(temp);path=run/'source_snapshot/stage2/engine.py';path.chmod(0o644);path.write_text('# changed\n')
            with self.assertRaisesRegex(ValueError,'snapshot digest'):e.inspect_run(run)

    def test_mocked_replay_aggregation_requires_all_declared_context_validation_tapes(self):
        inspected=e.inspect_run(SMOKE);baseline={r['seed']:r for r in inspected['baseline_validation']}
        seen=[]
        def fake(task):
            seen.append(task['seed']);r=baseline[task['seed']]
            return dict(context_id=0,seed=task['seed'],valid=r['valid'],metrics=r['metrics'],cpu_seconds=.01,wall_seconds=.02)
        with tempfile.TemporaryDirectory() as temp,patch.object(e,'_replay',side_effect=fake):
            report=e.seal(SMOKE,Path(temp)/'seal',execution_complete=True,replay=True,workers=1)
            self.assertEqual(seen,list(range(100,116)))
            self.assertEqual(report['status'],'replayed_and_matched')
            self.assertTrue(report['comparisons'][0]['key_exactly_equal'])
            self.assertTrue(e.verify_seal(Path(temp)/'seal')['valid'])
        def wrong(task):
            row=fake(task);row['metrics']=deepcopy(row['metrics']);row['metrics']['shipped']-=1;return row
        with tempfile.TemporaryDirectory() as temp,patch.object(e,'_replay',side_effect=wrong):
            report=e.seal(SMOKE,Path(temp)/'seal',execution_complete=True,replay=True)
            self.assertEqual(report['status'],'replay_mismatch')

    def test_key_and_path_contract(self):
        self.assertTrue(e.keys_agree([0,2,100,23.],[0,2,100,23.+1e-10]))
        self.assertFalse(e.keys_agree([0,2,101,23.],[0,2,100,23.]))
        with self.assertRaises(ValueError):e._safe_snapshot_path(Path('/tmp'),'../../etc/passwd')
        with self.assertRaises(ValueError):e._safe_snapshot_path(Path('/tmp'),'/etc/passwd')
        row=e._replay(dict(context_id=0,seed=100,policy_sha256='none',source_hashes={}))
        self.assertFalse(row['valid']);self.assertIn('source differs',row['error']['message'])


if __name__=='__main__':unittest.main()
