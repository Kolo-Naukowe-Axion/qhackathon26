"""Falsify weighting, row coverage, and interpretation of primary-gap intervals."""
from copy import deepcopy
import unittest

from stage2.quality_gap_audit import config_key, summarize


def fixture():
    config=dict(orders=2,horizon=5760,profile='full')
    bounds={}
    rows=[]
    for seed,weight,lb in ((1,.25,0),(2,.75,1)):
        bounds[config_key(config),seed]=dict(instance_sha256=f'hash{seed}',unfulfilled_lower_bound=lb,observed_realized_orders=2)
        for method,values in (('a',[lb,lb+1]),('b',[lb,lb])):
            for actor,missing in enumerate(values):
                rows.append(dict(cohort='x',method_id=method,config=config,seed=seed,policy_seed=actor,
                    tape_weight=weight,leaf_outcomes=[str(seed)],physical_instance_sha256=f'hash{seed}',
                    valid=True,terminal_requirements_met=True,identity_audit=dict(valid=True),issues=[],
                    metrics=dict(orders=2,shipped=2-missing),checker_metrics=dict(unfulfilled_orders=missing)))
    return rows,bounds


class GapAuditTests(unittest.TestCase):
    def test_actors_are_nested_and_intervals_use_same_tape_best_witness(self):
        rows,bounds=fixture()
        groups=summarize(rows,bounds)
        a,b=groups
        self.assertEqual(a['mean_missing'],1.25)
        self.assertEqual(a['realized_optimum_mean_interval'],[.75,.75])
        self.assertEqual(a['mean_excess_missing_interval'],[.5,.5])
        self.assertEqual(a['probability_primary_optimum_certified'],.5)
        self.assertEqual(b['mean_excess_missing_interval'],[0.,0.])

    def test_nonmatching_bounds_yield_interval_not_false_exact_gap(self):
        rows,bounds=fixture()
        for row in rows:
            row['metrics']['orders']=3;row['metrics']['shipped']+=0
            row['checker_metrics']['unfulfilled_orders']+=1
        for bound in bounds.values():bound['observed_realized_orders']=3
        groups=summarize(rows,bounds)
        self.assertEqual(groups[0]['mean_excess_missing_interval'],[.5,1.5])
        self.assertEqual(groups[0]['probability_primary_optimum_certified'],0)

    def test_invalid_rows_are_rejected_instead_of_dropped(self):
        for field in ('valid','terminal_requirements_met'):
            rows,bounds=fixture();rows[0][field]=False
            with self.assertRaises(ValueError):summarize(rows,bounds)
        rows,bounds=fixture();rows[0]['issues']=['bad']
        with self.assertRaises(ValueError):summarize(rows,bounds)

    def test_duplicate_actors_incomplete_groups_and_wrong_weights_fail(self):
        rows,bounds=fixture();rows.append(deepcopy(rows[0]))
        with self.assertRaises(ValueError):summarize(rows,bounds)
        rows,bounds=fixture();rows.pop()
        with self.assertRaises(ValueError):summarize(rows,bounds)
        rows,bounds=fixture()
        for row in rows:row['tape_weight']=.25
        with self.assertRaises(ValueError):summarize(rows,bounds)

    def test_wrong_instance_and_contradictory_outcomes_fail(self):
        rows,bounds=fixture();rows[0]['physical_instance_sha256']='other'
        with self.assertRaises(ValueError):summarize(rows,bounds)
        rows,bounds=fixture();rows[0]['checker_metrics']['unfulfilled_orders']=2
        with self.assertRaises(ValueError):summarize(rows,bounds)
        rows,bounds=fixture();bounds[config_key(rows[0]['config']),1]['unfulfilled_lower_bound']=1
        with self.assertRaises(ValueError):summarize(rows,bounds)


if __name__=='__main__':unittest.main()
