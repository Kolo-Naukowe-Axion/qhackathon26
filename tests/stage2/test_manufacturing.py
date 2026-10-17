import itertools
import unittest
from stage2.window_experiments import tiny_problem
from stage2.window_qubo import compile_qubo,solve_cp,assignments,validate
from stage2.manufacturing_cases import production_case
from stage2.manufacturing_penalty import tighten
from stage2.operation_qubo import compile_operations


class ManufacturingTests(unittest.TestCase):
    def test_all_binary_states_keep_feasible_energies_and_ground_states(self):
        p=tiny_problem();q=compile_qubo(p);plan=solve_cp(p,3,1)['plan']
        new,bits,cert=tighten(q,plan,'Native CP witness in exhaustive unit test only')
        minima=[None,None];grounds=[set(),set()]
        for values in itertools.product((0,1),repeat=len(q.linear)):
            valid=q.decode(values)['valid']
            if valid:self.assertEqual(q.energy(values),new.energy(values))
            else:self.assertGreaterEqual(new.energy(values),new.penalty)
            for j,model in enumerate([q,new]):
                e=model.energy(values)
                if minima[j]is None or e<minima[j]:minima[j]=e;grounds[j]={values}
                elif e==minima[j]:grounds[j].add(values)
        self.assertEqual(minima,[4,4]);self.assertEqual(grounds[0],grounds[1])
        self.assertEqual(new.penalty,cert['witness_objective']+1)

    def test_operation_pool_and_invalid_witness(self):
        p=tiny_problem();plan=solve_cp(p,3,1)['plan']
        columns={o['id']:[[a]for a in assignments(p,o)]for o in p['operations']}
        q=compile_operations(p,columns);new,bits,_=tighten(q,plan)
        self.assertTrue(new.decode(bits)['valid']);self.assertEqual(new.energy(bits),4)
        with self.assertRaises(ValueError):tighten(q,plan[:-1])

    def test_full_recipes_and_scenarios_have_explicit_boundaries(self):
        for n in [2,4,8]:
            p=production_case(n);validate(p);self.assertEqual(len(p['operations']),16*n)
            joins=[o for o in p['operations']if len(o['predecessors'])==3]
            self.assertEqual(len(joins),n)
        for scenario,machine,added in [('mill-down','F3',None),('lease-recovery','F3','F4'),('heat-outage','H2',None),('heat-lease','H2','H3')]:
            p=production_case(2,scenario);validate(p)
            self.assertNotIn(machine,p['machines'])
            self.assertTrue(all(machine not in o['durations']for o in p['operations']))
            if added:
                self.assertTrue(all(o['machine_release'][added]>=360 for o in p['operations']if added in o['durations']))


if __name__=='__main__':unittest.main()
