from copy import deepcopy
import itertools
import unittest
from stage2.window_experiments import tiny_problem,encode_plan
from stage2.window_qubo import compile_qubo,solve_cp,check_plan


class WindowSetupTests(unittest.TestCase):
    def problem(self):
        p=tiny_problem();p['horizon']=12;p['machines']['M']['available']=[[0,12]];p['workers']['W']['available']=[[0,12]]
        p['operations']=[dict(id=str(i),durations={'M':2},skill='cut',attendance='full',release=0,due=12,
            predecessors=[str(i-1)]if i else[],family=('A','B','A')[i])for i in range(3)]
        p['machine_setups']={'A':{'A':0,'B':2},'B':{'A':2,'B':0}}
        return p

    def test_machine_only_metric_setups_need_no_extra_variables(self):
        p=self.problem();q=compile_qubo(p);plain=deepcopy(p);del plain['machine_setups'];baseline=compile_qubo(plain)
        self.assertEqual(q.variables,baseline.variables);self.assertGreater(q.metadata()['interaction_counts']['machine_family_changeover'],0)
        cp=solve_cp(p,3,1);self.assertTrue(cp['optimal']);self.assertEqual(cp['objective'],10)
        self.assertTrue(q.decode(encode_plan(q,cp['plan']))['valid'])
        for options in itertools.product(*(q.groups[str(i)]for i in range(3))):
            plan=[q.variables[i]for i in options];end=max(r['end']for r in plan)
            bits=[int(i in options or(i in q.groups['@makespan']and q.variables[i]['start']==end))for i in range(len(q.linear))]
            if check_plan(p,plan)['valid']:self.assertEqual(q.energy(bits),end)
            else:self.assertGreaterEqual(q.energy(bits),q.penalty)

    def test_nonmetric_changeovers_rejected_instead_of_overconstrained(self):
        p=self.problem();p['machine_setups']={a:{b:0 if a==b else 2 for b in 'ABC'}for a in 'ABC'}
        p['machine_setups']['A']['B']=10
        with self.assertRaisesRegex(ValueError,'triangle'):compile_qubo(p)

    def test_initial_setup_cannot_be_skipped(self):
        p=self.problem();p['machine_initial_family']={'M':'B'};q=compile_qubo(p);cp=solve_cp(p,3,1)
        self.assertEqual(cp['objective'],12);self.assertTrue(q.decode(encode_plan(q,cp['plan']))['valid'])


if __name__=='__main__':unittest.main()
