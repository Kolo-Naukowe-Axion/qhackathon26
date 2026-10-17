import unittest
from copy import deepcopy
import json
from pathlib import Path
import tempfile

from stage2.static_control import policies,hashes
from stage2.static_control_validation import validate_tasks,prepare


class StaticValidationProtocolTests(unittest.TestCase):
    def rows(self):
        policy=policies((12,))[0];result=[]
        for seed in range(100,116):
            row=deepcopy(policy);row['config']['seed']=seed;row['seed_role']='REUSED_VALIDATION100–115';row['selection_provenance']={'training_source_hashes':hashes()};result.append(row)
        return result

    def test_guarded_grid_candidate_has_balanced_reused_validation(self):validate_tasks(self.rows())

    def test_final_source_guard_and_partial_protocol_rejected(self):
        for mutation in ('final','source','guard','partial'):
            rows=self.rows()
            if mutation=='final':rows[0]['config']['seed']=10000
            elif mutation=='source':rows[0]['selection_provenance']['training_source_hashes']={}
            elif mutation=='guard':rows[0]['solver_options']['maintenance_outage_guard']=False
            else:rows.pop()
            with self.assertRaises(ValueError):validate_tasks(rows)

    def test_train_candidates_deduplicated_and_invalid_prior_retained(self):
        choices=policies((12,));prior=next(p for p in choices if p['original_prior'])
        def summary(p,missing):return dict(deepcopy(p),orders=12,eligible=True,missing=missing,total_tardiness=100,total_cost=100)
        top=[summary(next(p for p in choices if p['solver_options']['completion_policy']['credit_minutes']==270 and p['weights']['wip_limit']==wip),i)
             for i,wip in enumerate((4,6))]
        matched=summary(choices[0],10)
        prior=dict(deepcopy(prior),eligible=False,all_observed_invalid=1)
        report=dict(source_hashes=hashes(),selected_train_tapes=32,
                    summary=top+[matched,dict(prior,orders=12)],
                    candidates=[dict(orders=12,top3=top,original_priors=[prior])])
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'train.json';p.write_text(json.dumps(report))
            tasks=prepare([p])
            self.assertEqual(len(tasks),64)
            self.assertEqual(sum(not t['eligible_from_training'] for t in tasks),16)
            self.assertTrue(all(t['selection_provenance']['training_report_sha256'] for t in tasks))
            selected=[t for t in tasks if 'matched_18action_TRAIN_winner' in t['selection_provenance']['selection_roles']]
            self.assertEqual(len(selected),16)
            self.assertTrue(all(t['selection_provenance']['global_train_rank']==3 for t in selected))
            report['candidates'][0]['original_priors']=[top[0]]
            p.write_text(json.dumps(report));self.assertEqual(len(prepare([p])),48)
            report['selected_train_tapes']=0;p.write_text(json.dumps(report))
            with self.assertRaises(ValueError):prepare([p])


if __name__=='__main__':unittest.main()
