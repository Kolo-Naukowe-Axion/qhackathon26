from copy import deepcopy
import gzip,hashlib,json
from pathlib import Path
import tempfile
import unittest
from stage2 import adaptive_modes as a
from stage2 import sequential as seq
from stage2.spec import build
from stage2.maintenance_guard import run,AdmissionMaintenanceGuardFactory
from stage2.check import check_trace
from stage2.identity_audit import audit_trace


def context(n=1):
    return dict(config=dict(orders=n,horizon=5760,profile='full'),weights=dict(wip_limit=4,qa_guard_threshold=4,mode='standard',worker_calendar=True,preposition=False,lease_calibration=True,selector='priority',admission_rule='family',family=24.,due=.25,remaining=-4.,setup=10.,tool_distance=0.),solver_options=dict(tool_policy=dict(mode='hard'),admission=True,kit_reservation=True,recovery_policy=dict(enabled=True),routing_policy=dict(eta_processes=[])),selection_provenance=dict(role='DEVELOPMENT smoke; no teacher fit',prior_cost=0))


class ModeTests(unittest.TestCase):
    def test_eighteen_action_domain_public_causality_and_torch_inference(self):
        self.assertEqual(len(a.ACTIONS),18)
        self.assertEqual({tuple(sorted(x.items())) for x in a.ACTIONS},{tuple(sorted(dict(wip_limit=w,qa_guard_threshold=g,mode=m).items())) for w in (4,6,8) for g in (0,4) for m in ('eco','standard','turbo')})
        c=context();obs=AdmissionMaintenanceGuardFactory(build(1),c['weights'],maintenance_outage_guard=True).observation()
        for action in range(18):
            left=a.Controller(dict(kind='static',action=action),c['weights'],17)
            right=a.Controller(dict(kind='static',action=action),c['weights'],17)
            self.assertEqual(left(obs),right(dict(obs,hidden_seed=10000,future_quality=.001)))
            self.assertEqual(left(obs)['weights']['policy_seed'],17)
        import torch
        torch.set_num_threads(1);torch.manual_seed(7);net=a.make_network(torch)
        controller=a.Controller(dict(kind='ppo',network=seq.export_network(net)),c['weights'],0,True)
        controller(obs);x=torch.tensor([controller.trajectory[0]['features']],dtype=torch.float32)
        logits,_=net(x);self.assertEqual(logits.shape[-1],18)
        self.assertEqual(controller.trajectory[0]['action'],int(logits.argmax(-1)[0]))

    def test_static_mode_preview_commit_certification_and_guarded_direct_equivalence(self):
        c=context(4);instance=build(**c['config'],seed=4)
        for mode in ('eco','standard','turbo'):
            weights=dict(c['weights'],mode=mode,policy_seed=19)
            action=next(i for i,w in enumerate(a.ACTIONS) if all(weights[k]==v for k,v in w.items()))
            controller=a.Controller(dict(kind='static',action=action),weights,19,True)
            direct=run(instance,weights,**c['solver_options'],maintenance_outage_guard=True)
            actual=run(instance,weights,controller,**c['solver_options'],maintenance_outage_guard=True)
            for key in ('operations','moves','worker_moves','events','energy','metrics','admission_history'):self.assertEqual(actual[key],direct[key],(mode,key))
            self.assertTrue(check_trace(actual,instance)['valid']);self.assertTrue(audit_trace(actual,instance)['valid'])
            self.assertTrue(actual['algorithm_audit']['maintenance_outage_guard']['enabled'])
            self.assertEqual([r['tick'] for r in controller.trajectory],list(range(0,5760,720)))
            for op in actual['operations']:
                if op.get('order_id')=='P04' and op['process'] in ('T','F'):self.assertNotEqual(op['mode'],'turbo')

    def test_source_guard_rejects_before_execution_and_corrected_cpu_summary(self):
        task=dict(source_hashes={})
        with self.assertRaisesRegex(RuntimeError,'source changed'):a.rollout(task)
        row=dict(valid=True,reward=0,metrics=dict(total_tardiness_ticks=3,all_orders_fulfilled=True,orders=1,shipped=1,total_cost=2),wall_seconds=5,cpu_seconds=2,action_changes=0)
        summary=a.summary([row]);self.assertNotIn('simulation_cpu_seconds',summary)
        self.assertEqual(summary['summed_rollout_cpu_seconds'],2);self.assertEqual(summary['summed_rollout_wall_seconds'],5)

    def test_one_update_cem_preserves_each_validation_policy_trajectory_and_trace(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'fit';artifact=a.train([context()],output,method='cem',seconds=60,workers=2,seed=8,max_updates=1)
            self.assertEqual(artifact['schema'],'stage2-adaptive-modes-policy.v1')
            self.assertEqual(artifact['actions'],list(a.ACTIONS));self.assertEqual(artifact['final_tapes'],0)
            self.assertTrue(artifact['maintenance_outage_guard']);self.assertEqual(artifact['validation_sweeps'],2)
            for path in output.glob('validation-sweep*.jsonl'):
                rows=[json.loads(line) for line in path.read_text().splitlines()];self.assertEqual(len(rows),16)
                for row in rows:
                    self.assertIn(row['seed'],range(100,116));self.assertTrue(row['valid']);self.assertTrue(row['metric_reconciliation'])
                    blob=json.loads((output/'policies'/(row['policy_sha256']+'.json')).read_bytes())
                    self.assertEqual(hashlib.sha256(json.dumps(blob,sort_keys=True,separators=(',',':')).encode()).hexdigest(),row['policy_sha256'])
                    self.assertEqual(hashlib.sha256(json.dumps(row['trajectory'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),row['trajectory_sha256'])
                    raw=gzip.decompress(Path(row['trace_path']).read_bytes());self.assertEqual(hashlib.sha256(raw).hexdigest(),row['trace_sha256'])
            self.assertEqual(artifact['source_hashes'],a.hashes())


if __name__=='__main__':unittest.main()
