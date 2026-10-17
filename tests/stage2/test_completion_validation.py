import unittest
from copy import deepcopy

from stage2.completion_validation import validate_tasks


class CompletionValidationProtocolTests(unittest.TestCase):
    def task(self):return dict(config={'orders':12,'seed':100},policy_id='credit0',seed_role='REUSED_VALIDATION100–115',
        weights={'selector':'priority'},solver_options={'completion_policy':{'credit_minutes':0,'reclaim_dead_slots':False}})

    def test_reject_final_training_unlabeled_and_duplicate_tapes(self):
        validate_tasks([self.task()])
        for seed in (0,31,99,116,1000,10000):
            t=self.task();t['config']['seed']=seed
            with self.assertRaises(ValueError):validate_tasks([t])
        t=self.task();t['seed_role']='heldout final'
        with self.assertRaises(ValueError):validate_tasks([t])
        with self.assertRaises(ValueError):validate_tasks([self.task(),self.task()])

    def test_reject_untested_solver_reward_and_reclaim_combinations(self):
        t=self.task();t['weights']['selector']='qaoa'
        with self.assertRaises(ValueError):validate_tasks([t])
        t=self.task();t['solver_options']['reward_mode']='no-batch'
        with self.assertRaises(ValueError):validate_tasks([t])
        t=self.task();t['solver_options']['completion_policy']['reclaim_dead_slots']=True
        with self.assertRaises(ValueError):validate_tasks([t])


if __name__=='__main__':unittest.main()
