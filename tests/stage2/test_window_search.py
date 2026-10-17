import itertools
import unittest

from stage2.window_experiments import tiny_problem, factory_cell
from stage2.window_qubo import compile_qubo
from stage2.window_search import constructive, anneal, block_search
from stage2.planning_quantum import neighborhood


class WindowSearchTests(unittest.TestCase):
    def test_constructive_and_annealer_keep_exact_energy(self):
        q=compile_qubo(tiny_problem());start=constructive(q)
        self.assertTrue(start['valid'])
        for seed in range(4):
            result=anneal(q,seed,proposals=6001,restarts=2,initial=start['bits'])
            self.assertEqual(result['energy'],q.energy(result['bits']))
            self.assertTrue(result['decoded']['valid']);self.assertEqual(result['energy'],4)

    def test_neighborhood_retains_all_minimal_makespans(self):
        q=compile_qubo(factory_cell(2,3,480,30));start=constructive(q)
        self.assertTrue(start['valid'])
        for seed in range(8):
            free,fixed=neighborhood(q,start['bits'],seed,groups=3,alternatives=1)
            self.assertLessEqual(len(free),16)
            self.assertEqual(set(free)|set(fixed),set(range(len(q.linear))))
            choices=[];fixedends=[]
            for name,g in q.groups.items():
                if name=='@makespan':continue
                options=[i for i in g if i in free]
                if options:choices.append(options)
                else:fixedends.extend(q.variables[i]['end']for i in g if start['bits'][i])
            retained={q.variables[i]['start']for i in q.groups['@makespan']if i in free}
            for combination in itertools.product(*choices):
                self.assertIn(max(fixedends+[q.variables[i]['end']for i in combination]),retained)

    def test_exact_blocks_never_worsen_valid_start(self):
        q=compile_qubo(tiny_problem());start=constructive(q)
        result=block_search(q,start['bits'],'exact',iterations=4,shots=1)
        self.assertLessEqual(result['energy'],start['energy']);self.assertTrue(result['decoded']['valid'])


if __name__=='__main__':unittest.main()
