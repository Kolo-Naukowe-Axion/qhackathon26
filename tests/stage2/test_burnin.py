"""Reachability, immutable-prefix and public-boundary corruption regressions."""
from copy import deepcopy
from contextlib import redirect_stdout
import gzip
import io
import json
from pathlib import Path
import tempfile
import unittest

from stage2.burnin import run,verify,common_prefix,digest,main,source_hashes
from stage2.check import check_paired_causality
from stage2.spec import build


class BurninTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        instance=build(orders=3,horizon=2880,seed=20)
        cls.bundles=[run(instance,weights,method_id=name) for name,weights in (
            ('retain',{}),('turbo',dict(mode='turbo')),('eta',dict(routing_free_buffers=True,routing_estimate_finish=True)))]

    def refresh_digests(self,bundle):
        prefix=bundle['prefix'];prefix['sha256']=digest({k:v for k,v in prefix.items() if k!='sha256'})
        bundle['public_snapshot']['prefix_sha256']=prefix['sha256']
        bundle['snapshot_sha256']=digest(bundle['public_snapshot'])

    def test_reachable_midproduction_snapshot_retains_real_active_work_and_transport(self):
        b=self.bundles[0];s=b['public_snapshot']
        self.assertTrue(b['verification']['valid'],b['verification']['issues'])
        self.assertTrue(s['active_operations'])
        self.assertTrue(s['active_moves'])
        self.assertTrue(any(p['step']>0 for p in s['parts']))
        self.assertFalse(s['semantics']['standalone_restart_checkpoint'])
        self.assertEqual(len(b['prefix']['records']['energy']),480)

    def test_all_methods_share_exact_actual_prefix_and_snapshot(self):
        self.assertTrue(common_prefix(self.bundles)['valid'])
        for b in self.bundles:
            self.assertTrue(b['verification']['valid'])
            self.assertEqual(b['trace']['operations'][:len(b['prefix']['records']['operations'])],b['prefix']['records']['operations'])
            self.assertEqual(b['trace']['moves'][:len(b['prefix']['records']['moves'])],b['prefix']['records']['moves'])

    def test_controller_only_runs_after_boundary_and_receives_no_private_tape(self):
        observations=[]
        def controller(obs):
            observations.append(deepcopy(obs));obs['tick']=-999
            return dict(weights=dict(mode='eco'),action_id='causal-test')
        b=run(build(orders=1,horizon=1200,seed=123),controller=controller)
        self.assertTrue(b['verification']['valid'],b['verification']['issues'])
        self.assertEqual(observations[0]['tick'],480)
        self.assertTrue(all(480<=o['tick']<1200 and 'seed' not in o for o in observations))
        self.assertTrue(all(d['observation']['tick']==d['tick'] for d in b['trace']['decisions']))
        self.assertTrue(all(d['weights']['mode']=='standard' for d in b['trace']['decisions'] if d['tick']<480))
        self.assertTrue(all(d['weights']['mode']=='eco' for d in b['trace']['decisions'] if d['tick']>=480))

    def test_public_snapshot_excludes_actual_seed_and_future_events(self):
        snapshot=self.bundles[0]['public_snapshot'];serialized=json.dumps(snapshot)
        self.assertNotIn('"seed"',serialized);self.assertNotIn('keyed_uniform',serialized)
        self.assertNotIn('realized_stages',serialized);self.assertNotIn('run_id',serialized)
        self.assertTrue(all(e['tick']<=480 for e in snapshot['observed_events']))
        self.assertFalse(any(e['type']=='reveal' for e in snapshot['observed_events']))
        self.assertIn('reservation_destination',snapshot['agv_reservation_cache'][0])

    def test_static_boundary_overrides_can_initialize_a_suffix_controller(self):
        b=run(build(orders=1,horizon=1200),dict(mode='eco'),controller=lambda obs:
            dict(weights=dict(remaining=-12),action_id='partial-controller'))
        self.assertTrue(b['verification']['valid'])
        self.assertTrue(all(d['weights']['mode']=='eco' and d['weights']['remaining']==-12
            for d in b['trace']['decisions'] if d['tick']>=480))

    def test_prefix_corruption_is_rejected_even_with_recomputed_digests(self):
        b=deepcopy(self.bundles[0]);b['prefix']['records']['operations'][0]['end']+=1
        self.refresh_digests(b)
        r=verify(b)
        self.assertFalse(r['valid'])
        self.assertIn('immutable_prefix',{i['code'] for i in r['issues']})

    def test_boundary_reservation_corruption_is_independently_reconstructed(self):
        b=deepcopy(self.bundles[0]);b['public_snapshot']['reserved_inputs']['F1']=99
        b['snapshot_sha256']=digest(b['public_snapshot']);r=verify(b)
        self.assertFalse(r['valid'])
        self.assertTrue(any(i['code']=='snapshot_reconstruction' and i['field']=='reserved_inputs' for i in r['issues']))

    def test_blocked_outputs_and_shipped_state_are_reconstructed(self):
        for field,value in [('blocked_outputs',{'F1':['invented']}),('shipped_at',{'P01':1})]:
            with self.subTest(field=field):
                b=deepcopy(self.bundles[0]);b['public_snapshot'][field]=value
                b['snapshot_sha256']=digest(b['public_snapshot']);r=verify(b)
                self.assertTrue(any(i['code']=='snapshot_reconstruction' and i['field']==field for i in r['issues']))

    def test_boundary_completion_cannot_be_omitted_from_prefix(self):
        b=deepcopy(self.bundles[0]);events=b['prefix']['records']['events']
        self.assertTrue(any(e['type']=='lease_delivery' and e['tick']==480 for e in events))
        self.assertEqual(events[-1]['tick'],480)
        events.pop();self.refresh_digests(b);r=verify(b)
        self.assertIn('prefix_boundary_events',{i['code'] for i in r['issues']})

    def test_private_fields_are_rejected_even_if_snapshot_digest_matches(self):
        b=deepcopy(self.bundles[0]);b['public_snapshot']['seed']=20
        b['snapshot_sha256']=digest(b['public_snapshot']);r=verify(b)
        self.assertIn('snapshot_private_fields',{i['code'] for i in r['issues']})

    def test_public_snapshot_cannot_add_a_future_revealed_outcome(self):
        b=deepcopy(self.bundles[0])
        b['public_snapshot']['observed_events'].append(dict(type='reveal',tick=720,outcome='future'))
        b['snapshot_sha256']=digest(b['public_snapshot']);r=verify(b)
        self.assertTrue(any(i['code']=='snapshot_reconstruction' and i['field']=='observed_events' for i in r['issues']))

    def test_full_witness_physical_corruption_is_not_hidden_by_prefix_validity(self):
        b=deepcopy(self.bundles[0]);b['trace']['energy'][-1]['grid_kw']+=100
        r=verify(b);self.assertFalse(r['valid']);self.assertFalse(r['physical']['valid'])

    def test_incomplete_commit_prefix_is_rejected(self):
        b=deepcopy(self.bundles[0]);b['prefix']['records']['energy'].pop()
        self.refresh_digests(b);r=verify(b)
        self.assertIn('prefix_incomplete',{i['code'] for i in r['issues']})

    def test_different_prefix_policies_are_not_treated_as_paired_methods(self):
        b=run(build(orders=3,horizon=2880,seed=20),prefix_weights=dict(wip_limit=1))
        self.assertFalse(common_prefix([self.bundles[0],b])['valid'])

    def test_paired_actual_tapes_preserve_observation_prefix_causality(self):
        bundles=[run(build(orders=3,horizon=2880,seed=s),dict(mode='turbo'),method_id='turbo') for s in range(4)]
        r=check_paired_causality([b['trace'] for b in bundles]);self.assertTrue(r['valid'],r['issues'])
        self.assertTrue(all(b['verification']['valid'] for b in bundles))

    def test_existing_physical_sources_are_not_modified(self):
        before=source_hashes();run(build(orders=1,horizon=1200));self.assertEqual(before,source_hashes())

    def test_active_zero_power_tool_service_is_a_real_boundary_commitment(self):
        # The engine excludes zero-power servicing from its power-load cache,
        # but the checkpoint must retain its worker/tool occupation.
        b=run(build(orders=8,horizon=2880,seed=20),boundary_tick=780)
        self.assertTrue(b['verification']['valid'],b['verification']['issues'])
        self.assertTrue(any(op['kind']=='tool_service' for op in b['public_snapshot']['active_operations']))

    def test_invalid_boundary_is_rejected(self):
        instance=build(orders=1,horizon=1200)
        for boundary in (0,1,481,1200,1201):
            with self.subTest(boundary=boundary):
                with self.assertRaises(ValueError):run(instance,boundary_tick=boundary)

    def test_cli_can_verify_a_saved_compressed_reachability_witness(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'witness.json.gz';path.write_bytes(gzip.compress(json.dumps(self.bundles[0]).encode()))
            with redirect_stdout(io.StringIO()):self.assertEqual(main(['verify',str(path)]),0)


if __name__=='__main__':unittest.main()
