import json
from pathlib import Path
import tempfile
import unittest

from stage2.schedule_neighborhood_audit import load_checkpoint,neighborhood,declare,construct,simulate,hashes,digest,summarize,ACTOR_SEED
from stage2.adaptive_recovery import Controller
from stage2.maintenance_guard import AdmissionMaintenanceGuardFactory
from stage2.spec import build
from stage2.check import check_trace,check_paired_causality

CHECKPOINT=Path(__file__).resolve().parents[2]/'output/stage2-search/final-preparation/checkpoints/strong-cem6-2026.json'

class ScheduleNeighborhoodTests(unittest.TestCase):
    def test_complete_finite_domain_counts_no_duplicates_and_train_only(self):
        a=load_checkpoint(CHECKPOINT);contexts,tasks=declare(a)
        self.assertEqual([len(c['variants']) for c in contexts],[41,741,741]);self.assertEqual(len(tasks),12184)
        self.assertEqual(sum(t['retain_trace'] for t in tasks),3);self.assertEqual({t['config']['seed'] for t in tasks},set(range(8)))
        for c in contexts:
            schedules=[tuple(v['schedule']) for v in c['variants']];self.assertEqual(schedules,sorted(set(schedules)))
            self.assertEqual(sum(v['hamming_distance']==0 for v in c['variants']),1)
            self.assertTrue(all(v['hamming_distance']<=c['radius'] for v in c['variants']))
        with self.assertRaises(ValueError):neighborhood([0]*7,2)

    def test_original_matches_direct_guarded_original_priority_and_causal(self):
        a=load_checkpoint(CHECKPOINT);context=a['contexts'][0];traces=[]
        for seed in (0,1,2):
            instance=build(12,seed=seed);factory,controller=construct(instance,a,0,a['policies_by_context'][0]['schedule']);trace=factory.run()
            self.assertTrue(check_trace(trace,instance)['valid']);traces.append(trace)
            self.assertTrue(all(d['weights']['selector']=='priority' and d['weights']['policy_seed']==ACTOR_SEED for d in trace['decisions']))
            if seed==0:
                weights=dict(context['weights'],selector='priority',policy_seed=ACTOR_SEED);options=dict(context['solver_options']);options.pop('admission')
                direct=Controller(a['policies_by_context'][0],weights,ACTOR_SEED,True,a['interval'])
                expected=AdmissionMaintenanceGuardFactory(instance,weights,direct,maintenance_outage_guard=True,**options).run()
                fields=('operations','moves','worker_moves','events','energy','metrics','decisions')
                self.assertEqual(digest({k:trace[k] for k in fields}),digest({k:expected[k] for k in fields}))
        self.assertTrue(check_paired_causality(traces)['valid'])

    def test_actual_worker_identity_source_guards_and_invalid_preservation(self):
        a=load_checkpoint(CHECKPOINT);contexts,tasks=declare(a);task=next(t for t in tasks if t['retain_trace'])
        with tempfile.TemporaryDirectory() as tmp:
            task=dict(task,checkpoint=str(CHECKPOINT),output=tmp,source_hashes=hashes());row=simulate(task)
            self.assertTrue(row['valid'],row.get('error'));self.assertTrue(row['identity_audit']['valid']);self.assertEqual(row['decode_mismatches'],0)
            self.assertTrue(Path(row['trace_path']).exists());self.assertEqual(len(row['physical_trace_sha256']),64)
            task['source_hashes']={};failed=simulate(task);self.assertFalse(failed['valid']);self.assertIn('Source drift',failed['error']['message'])
        self.assertFalse(summarize(contexts,[row])[0]['complete_checked_neighborhood'])
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'changed.json';p.write_bytes(CHECKPOINT.read_bytes()+b' ')
            with self.assertRaises(ValueError):load_checkpoint(p)

    def test_invalid_neighborhood_never_gets_valid_only_envelope(self):
        c=dict(context_id=0,config=dict(orders=12),variants=[dict(variant_id=0,schedule=[0]*8)],original_variant_id=0)
        rows=[dict(context_id=0,phase='TRAIN-finite-neighborhood',variant_id=0,config=dict(seed=s),valid=s!=7,physical_instance_sha256=str(s)) for s in range(8)]
        result=summarize([c],rows)[0];self.assertFalse(result['complete_checked_neighborhood']);self.assertNotIn('per_tape',result)

    def test_common_policy_and_offline_per_tape_oracle_are_distinct(self):
        c=dict(context_id=0,config=dict(orders=12),variants=[dict(variant_id=v,schedule=[v]*8) for v in range(2)],original_variant_id=0)
        rows=[]
        for v in range(2):
            for seed in range(8):
                metrics=dict(orders=12,shipped=12-int(seed%2!=v),total_tardiness_ticks=seed+v,total_cost=10)
                rows.append(dict(task_id=len(rows),context_id=0,phase='TRAIN-finite-neighborhood',variant_id=v,schedule=[v]*8,
                    config=dict(seed=seed),valid=True,physical_instance_sha256=str(seed),metrics=metrics,
                    physical_trace_sha256=f'{seed}-{v}',metrics_sha256=digest(metrics)))
        result=summarize([c],rows)[0];self.assertTrue(result['complete_checked_neighborhood'])
        self.assertEqual(result['best_common_fixed_variant']['aggregate_key'][0],4)
        self.assertEqual(result['offline_per_tape_oracle_aggregate_key'][0],0)
        self.assertEqual([t['first_lexicographic_minimum_variant_id'] for t in result['per_tape']],[s%2 for s in range(8)])
        self.assertTrue(all(t['distinct_physical_trajectories']==2 and t['original_physical_equivalent_variants']==1 for t in result['per_tape']))
        rows[-1]['physical_instance_sha256']='wrong-instance'
        self.assertFalse(summarize([c],rows)[0]['complete_checked_neighborhood'])

if __name__=='__main__':unittest.main()
