import itertools
from copy import deepcopy
import unittest

from stage2.window_qubo import compile_qubo,check_plan,conditional_qubo,solve_cp,solve_literal_qubo
from stage2.window_experiments import tiny_problem,encode_plan


class WindowQUBOTests(unittest.TestCase):
    def test_exhaustive_ground_states_and_penalty_certificate(self):
        q=compile_qubo(tiny_problem());self.assertEqual(len(q.variables),9)
        best=None;ground=[]
        for mask in range(1<<len(q.variables)):
            bits=[(mask>>i)&1 for i in range(len(q.variables))];e=q.energy(bits)
            if best is None or e<best:best=e;ground=[bits]
            elif e==best:ground.append(bits)
            decoded=q.decode(bits)
            if not decoded['valid']:self.assertGreaterEqual(e,q.penalty)
        self.assertEqual(best,4)
        self.assertTrue(all(q.decode(b)['valid']and q.decode(b)['objective']==4 for b in ground))

    def test_raw_native_cp_and_literal_energy_minimum_match(self):
        p=tiny_problem();q=compile_qubo(p)
        cp=solve_cp(p,3,1);literal=solve_literal_qubo(q,3,1)
        self.assertTrue(cp['optimal']);self.assertTrue(literal['optimal'])
        self.assertEqual(cp['objective'],literal['energy']);self.assertEqual(literal['energy'],4)
        self.assertTrue(literal['decoded']['valid'])
        self.assertEqual(q.energy(encode_plan(q,cp['plan'])),4)

    def test_worker_walk_cannot_happen_during_break(self):
        p=tiny_problem();p['horizon']=8;p['grid']=2
        p['machines']={'A':dict(hall='A',available=[[0,8]]),'B':dict(hall='B',available=[[0,8]])}
        p['workers']['W']['available']=[[0,2],[4,8]];p['worker_travel']=2
        p['operations'][0].update(durations={'A':2},due=8)
        p['operations'][1].update(durations={'B':2},release=4,due=8)
        p['transport_lags']={a:{b:0 for b in p['machines']}for a in p['machines']}
        q=compile_qubo(p);cp=solve_cp(p,3,1);self.assertTrue(cp['optimal']);self.assertEqual(cp['check']['makespan'],8)
        b=next(r for r in cp['plan']if r['operation']=='b');self.assertEqual(b['start'],6)
        self.assertTrue(q.decode(encode_plan(q,cp['plan']))['valid'])
        bad=deepcopy(cp['plan']);bad[1].update(start=4,end=6,attended_end=6)
        self.assertFalse(check_plan(p,bad)['valid'])

    def test_conditioning_preserves_every_full_energy(self):
        q=compile_qubo(tiny_problem());free=[0,2,5,7];fixed={i:(i%3==1)*1 for i in range(len(q.variables))if i not in free}
        c=conditional_qubo(q,free,fixed)
        for values in itertools.product((0,1),repeat=len(free)):
            full=[fixed.get(i,0)for i in range(len(q.variables))]
            for i,v in zip(free,values):full[i]=v
            e=c['offset']+sum(a*x for a,x in zip(c['linear'],values))+sum(v*values[i]*values[j]for(i,j),v in c['quadratic'].items())
            self.assertEqual(e,q.energy(full))

    def test_alternative_machines_skills_and_dag_validation(self):
        p=tiny_problem();p['machines']['N']=dict(hall='B',available=[[0,6]])
        p['workers']['wrong']=dict(skills=['weld'],initial_hall='B',available=[[0,6]])
        p['operations'][0]['durations']['N']=1
        p['transport_lags']={a:{b:0 for b in p['machines']}for a in p['machines']}
        q=compile_qubo(p)
        self.assertTrue(all(v.get('worker')!='wrong'for v in q.variables))
        cp=solve_cp(p,3,1);self.assertTrue(cp['check']['valid']);self.assertTrue(q.decode(encode_plan(q,cp['plan']))['valid'])
        p['operations'][0]['predecessors']=['b']
        with self.assertRaises(ValueError):compile_qubo(p)


if __name__=='__main__':unittest.main()
