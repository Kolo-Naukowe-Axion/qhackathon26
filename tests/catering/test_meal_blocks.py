import copy
import itertools
import unittest

import numpy as np

from catering.domain import snapshot,make_plan
from catering.check import check_plan
from catering.options import enumerate_options,bounded_allocations
from catering.meal_blocks import meal_fixture,compile_meal_blocks,sector_data,sector_bits,xy_mix
from catering.meal_search import portfolio,warm_state
from catering.qubo import energy,objective_energy,ising
from catering.decode import decode
from catering.native_slots import solve_native
from catering.audit import audit_bundle
from catering.meal_reference import solve_bundle
from catering.meal_cell import cell_fixture


class MealBlockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=meal_fixture(1);cls.s=snapshot(cls.p,"S0")
        cls.programs=enumerate_options(cls.p,cls.s)
        cls.pool=portfolio(cls.programs,[],3,np.random.default_rng(1))
        cls.bundle=compile_meal_blocks(cls.p,cls.s,cls.pool)
        cls.sector=sector_data(cls.bundle)

    def test_one_prepared_course_is_not_a_complete_meal(self):
        p=next(p for p in self.programs if p["allocation_order"]==["customer-0/main"] and p["yield_lots"]==1)
        plan=make_plan(self.p,self.s["fixed_batches"]+[p])
        checked=check_plan(self.p,self.s,plan)
        self.assertTrue(checked["valid"])
        self.assertEqual(checked["completed_meal_lots"],0)
        self.assertEqual(checked["metrics"],dict(U=2,W=2,B=1,R=1))
        self.assertEqual(len(plan["unpaired_disposals"]),2)
        plan["unpaired_disposals"]=[]
        self.assertFalse(check_plan(self.p,self.s,plan)["valid"])

    def test_both_courses_form_one_meal_and_balance_material(self):
        p=next(p for p in self.programs if p["allocation_order"]==["committed/side"])
        plan=make_plan(self.p,self.s["fixed_batches"]+[p])
        checked=check_plan(self.p,self.s,plan)
        self.assertTrue(checked["valid"])
        self.assertEqual(checked["completed_meal_lots"],1)
        self.assertEqual(checked["metrics"],dict(U=1,W=0,B=1,R=1))
        self.assertEqual(plan["meal_handovers"][0]["time"],80)
        plan["meal_handovers"]=[]
        self.assertFalse(check_plan(self.p,self.s,plan)["valid"])

    def test_all_hilbert_bitstrings_have_the_correct_zero_penalty_set(self):
        b=self.bundle;n=b["size"]["binary_variables"]
        self.assertLessEqual(n,10)
        valid_energy=[];invalid_energy=[]
        for mask in range(1<<n):
            bits=[(mask>>i)&1 for i in range(n)]
            d=decode(b,bits);onehot=all(sum(bits[i] for i in g["indices"])==1 for g in b["onehot_groups"])
            literal=energy(b,bits);objective=objective_energy(b,bits)
            self.assertEqual(literal==objective,d["physical_valid"] and onehot)
            if d["valid"]:
                valid_energy.append(literal)
                expected=sum(b["objective"]["weights"][k]*d["check"]["metrics"][k] for k in ("U","W","B","R"))
                self.assertEqual(literal,expected)
            else:invalid_energy.append(literal)
        self.assertGreater(min(invalid_energy),max(valid_energy))

    def test_sector_cost_equals_literal_qubo_and_ising(self):
        b=self.bundle;zmodel=ising(b)
        for i in range(self.sector["states"]):
            bits=sector_bits(b,self.sector,i);literal=energy(b,bits)
            self.assertEqual(literal,int(self.sector["energy"][i]))
            z=[1-2*x for x in bits]
            spin=int(zmodel["constant"])+sum(int(c)*x for c,x in zip(zmodel["linear"],z))
            spin+=sum(int(t["value"])*z[t["i"]]*z[t["j"]] for t in zmodel["quadratic"])
            self.assertEqual(spin,4*literal)

    def test_shared_independent_audit_supports_the_quadratic_service_objective(self):
        result=audit_bundle(self.bundle)
        self.assertTrue(result["valid"])
        self.assertEqual(result["all_bitstrings_checked"],1<<self.bundle["size"]["binary_variables"])

    def test_sector_xy_simulation_matches_full_hilbert_circuit(self):
        b=self.bundle;sec=self.sector;n=b["size"]["binary_variables"]
        small=warm_state(b,sec,set());full=np.zeros(1<<n,dtype=complex)
        masks=np.array([sum(x<<j for j,x in enumerate(sector_bits(b,sec,i))) for i in range(sec["states"])])
        full[masks]=small
        gamma,beta=0.27,0.39
        scale=max(1,b["objective"]["weights"]["U"])
        values=np.array([energy(b,[(m>>i)&1 for i in range(n)]) for m in range(1<<n)])
        full*=np.exp(-1j*gamma*values/scale)
        small=xy_mix(small*np.exp(-1j*gamma*sec["energy"]/scale),sec["dims"],beta)
        indices=np.arange(1<<n)
        for g in b["onehot_groups"]:
            q=g["indices"];edges=list(zip(q[:-1],q[1:]))+([(q[-1],q[0])] if len(q)>2 else [])
            for a,c in edges:
                left=indices[((indices&(1<<a))!=0)&((indices&(1<<c))==0)]
                right=left^(1<<a)^(1<<c)
                x,y=full[left].copy(),full[right].copy()
                full[left]=np.cos(beta)*x-1j*np.sin(beta)*y
                full[right]=-1j*np.sin(beta)*x+np.cos(beta)*y
        np.testing.assert_allclose(full[masks],small,atol=1e-13)
        self.assertAlmostEqual(float(np.vdot(full,full).real),1)
        self.assertAlmostEqual(float(np.sum(abs(full)**2)-np.sum(abs(full[masks])**2)),0)

    def test_incumbent_remains_in_every_new_portfolio(self):
        best=decode(self.bundle,sector_bits(self.bundle,self.sector,int(self.sector["energy"].argmin())))
        fixed_ids={p["id"] for p in self.s["fixed_batches"]}
        incumbent=[p for p in best["plan"]["batches"] if p["id"] not in fixed_ids]
        new=portfolio(self.programs,incumbent,3,np.random.default_rng(17))
        self.assertTrue({p["id"] for p in incumbent}<={p["id"] for p in new})

    def test_bounded_allocation_generator_matches_cartesian_definition(self):
        demands=[dict(id="a"),dict(id="b"),dict(id="c")];remaining=dict(a=2,b=1,c=2)
        for cap in range(1,5):
            expected={tuple(g for d,q in zip(demands,qs) for g in [d["id"]]*q)
                      for qs in itertools.product(range(3),range(2),range(3)) if 0<sum(qs)<=cap}
            self.assertEqual({tuple(x) for x in bounded_allocations(demands,remaining,cap)},expected)

    def test_offered_domain_reference_matches_full_sector_optimum(self):
        result=solve_bundle(self.bundle,seconds=3)
        self.assertEqual(result["reference"]["status"],"OPTIMAL")
        self.assertEqual(int(result["reference"]["objective"]),int(self.sector["energy"].min()))
        self.assertTrue(result["check"]["valid"])

    def test_complete_cell_keeps_every_program_and_matches_raw_optimum(self):
        instance=cell_fixture();state=snapshot(instance,"S0")
        programs=enumerate_options(instance,state)
        bundle=compile_meal_blocks(instance,state,programs,complete_domain=True)
        self.assertEqual(bundle["size"]["binary_variables"],35)
        self.assertEqual(bundle["representation_kind"],"complete_declared_grid")
        sector=sector_data(bundle)
        optimum=decode(bundle,sector_bits(bundle,sector,int(sector["energy"].argmin())))
        raw=solve_native(instance,state,dict(wall_time_limit_s=3))
        self.assertEqual(raw["reference_status"],"OPTIMAL")
        self.assertEqual(optimum["check"]["metrics"],raw["check"]["metrics"])
        self.assertEqual(raw["check"]["metrics"],dict(U=0,W=0,B=2,R=2))

    def test_raw_reference_optimizes_complete_meals_and_runs_mandatory_clean(self):
        normal=solve_native(self.p,self.s,dict(wall_time_limit_s=3))
        self.assertEqual(normal["reference_status"],"OPTIMAL")
        self.assertEqual(normal["check"]["metrics"],dict(U=0,W=0,B=2,R=2))
        disrupted=snapshot(self.p,"S3")
        r=solve_native(self.p,disrupted,dict(wall_time_limit_s=3))
        self.assertEqual(r["reference_status"],"OPTIMAL")
        self.assertEqual(r["plan"]["recovery_operations"][0]["start"],70)
        self.assertEqual(r["plan"]["recovery_operations"][0]["end"],80)
        self.assertTrue(r["check"]["valid"])


if __name__=="__main__":unittest.main()
