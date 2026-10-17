import itertools
import unittest
import numpy as np

from stage2.column_blocks import conditional_master
from stage2.column_qubo import compile_columns
from stage2.planning_quantum import energy_table
from stage2.sector_mixer import sector_energies,evolve_sector,sample_sector
from stage2.trajectory_mixer import evolve
from stage2.window_experiments import tiny_problem
from stage2.window_qubo import assignments


class SectorMixerTests(unittest.TestCase):
    def test_every_sector_energy_and_probability_match_full_statevector(self):
        p=tiny_problem()
        rows={op['id']:assignments(p,op)for op in p['operations']}
        def row(oid,start):return next(r for r in rows[oid]if r['start']==start)
        columns={'a':[[row('a',0)],[row('a',2)]],'b':[[row('b',2)],[row('b',4)]]}
        q=compile_columns(p,columns)
        initial=q.encode(columns['a'][0]+columns['b'][1])
        local=conditional_master(q,initial,{name:q.groups[name][1-int(initial[q.groups[name][1]])]for name in columns})
        energies=sector_energies(local)
        n,k=len(local.columns),len(local.makespans)
        full=energy_table(dict(linear=local.linear,quadratic=local.quadratic,offset=local.offset))
        for register,pattern in itertools.product(range(k),range(1<<n)):
            self.assertEqual(energies[register,pattern],full[pattern|(1<<(n+register))])
        for gammas,betas in (([.23],[.71]),([.13,1.45],[.66,.21])):
            scale=max(abs(int(e))for e in full)+1
            sector=evolve_sector(local,energies,gammas,betas,scale)
            conventional=evolve(local,full,gammas,betas,scale)
            for register,pattern in itertools.product(range(k),range(1<<n)):
                self.assertAlmostEqual(abs(sector[register,pattern])**2,abs(conventional[pattern|(1<<(n+register))])**2,places=13)
        sampled=sample_sector(local,7,2,32,32)
        self.assertIn('gate rxx',sampled['qasm'])
        self.assertEqual(local.energy(sampled['bits']),sampled['energy'])


if __name__=='__main__':unittest.main()
