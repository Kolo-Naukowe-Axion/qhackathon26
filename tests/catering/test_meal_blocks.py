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

    def test_snapshot_and_checker_reject_unrevealed_future_meal_information(self):
        instance=copy.deepcopy(self.p)
        future={"customer-0/main","customer-0/side"}
        for group in instance["demand_groups"]:
            if group["id"] in future:group["revealed"]=80
        with self.assertRaisesRegex(ValueError,"not yet revealed"):
            snapshot(instance,"S0")
        # Bypassing the constructor must not bypass the independent checker.
        state=copy.deepcopy(self.s)
        for group in state["demand_groups"]:
            if group["id"] in future:group["revealed"]=80
        plan=make_plan(instance,state["fixed_batches"])
        result=check_plan(instance,state,plan)
        self.assertFalse(result["valid"])
        self.assertIn("Snapshot exposes demand before its information reveal",result["violations"])
        instance=copy.deepcopy(self.p)
        for group in instance["urgent_groups"]:group["revealed"]=80
        snapshot(instance,"S0")  # The unobserved urgent meal is not exposed.
        with self.assertRaisesRegex(ValueError,"not yet revealed"):
            snapshot(instance,"S1")

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

    def test_tighter_anchor_bounds_preserve_the_physical_optimum(self):
        bundle=compile_meal_blocks(self.p,self.s,self.bundle["options"],tight_bounds=True)
        sector=sector_data(bundle)
        best=decode(bundle,sector_bits(bundle,sector,int(sector["energy"].argmin())))
        old=decode(self.bundle,sector_bits(self.bundle,self.sector,int(self.sector["energy"].argmin())))
        self.assertEqual(best["check"]["metrics"],old["check"]["metrics"])
        self.assertLessEqual(bundle["objective"]["component_bounds"]["B"],len(bundle["onehot_groups"]))
        self.assertGreater(int(bundle["penalty"]),sum(abs(int(c)) for c in bundle["objective"]["linear"])+sum(abs(int(q["value"])) for q in bundle["objective"]["quadratic"]))
        # Every feasible one-hot schedule respects the new bounds, not just the optimum.
        for index in range(sector["states"]):
            if sector["valid"][index]:
                result=decode(bundle,sector_bits(bundle,sector,index))
                self.assertTrue(result["valid"])
                for key,value in result["check"]["metrics"].items():
                    self.assertLessEqual(value,bundle["objective"]["component_bounds"][key])

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

    def test_priority_and_nonempty_previous_plan_obey_the_full_lexicographic_proof(self):
        # Current demo fixtures have unit priorities and R=B. Exercise the
        # distinct priority and symmetric-difference terms on every bitstring.
        instance=copy.deepcopy(self.p)
        for priority,meal in zip((2,5,3),instance["service_model"]["meals"]):
            meal["priority"]=priority
        instance["previous_unstarted"]=[copy.deepcopy(self.pool[0])]
        state=snapshot(instance,"S0")
        bundle=compile_meal_blocks(instance,state,self.pool,tight_bounds=True)
        weights=bundle["objective"]["weights"]
        bounds=bundle["objective"]["component_bounds"]
        feasible=[];invalid=[]
        prior={self.pool[0]["id"]}
        for bits in itertools.product((0,1),repeat=bundle["size"]["binary_variables"]):
            bits=list(bits);result=decode(bundle,bits)
            if not result["valid"]:
                invalid.append(energy(bundle,bits));continue
            metrics=result["check"]["metrics"]
            produced=sum(p["yield_lots"] for p in result["plan"]["batches"])
            self.assertEqual(metrics["W"],produced-2*result["check"]["completed_meal_lots"])
            chosen={p["id"] for i,p in enumerate(bundle["options"]) if bits[i]}
            self.assertEqual(metrics["R"],len(chosen^prior))
            self.assertEqual(energy(bundle,bits),sum(weights[k]*metrics[k] for k in weights))
            self.assertTrue(all(0<=metrics[k]<=bounds[k] for k in bounds))
            feasible.append((tuple(metrics[k] for k in ("U","W","B","R")),energy(bundle,bits)))
        self.assertGreater(len(set(m for m,_ in feasible)),1)
        self.assertEqual(sorted(set(feasible)),sorted(set(feasible),key=lambda row:row[1]))
        self.assertGreater(min(invalid),max(value for _,value in feasible))

    def test_anchor_register_is_a_bijection_on_physically_feasible_subsets(self):
        # Begin with the physical checker, independently of anchor/conflict
        # constraints. Every compatible subset must have exactly one encoding.
        b=self.bundle;expected=set()
        for mask in range(1<<len(b["options"])):
            selected=[i for i in range(len(b["options"])) if mask>>i&1]
            plan=make_plan(self.p,self.s["fixed_batches"]+[b["options"][i] for i in selected])
            if not check_plan(self.p,self.s,plan)["valid"]:continue
            bits=[0]*b["size"]["binary_variables"]
            for group in b["onehot_groups"]:
                offered=[i for i in group["program_indices"] if i in selected]
                self.assertLessEqual(len(offered),1)
                bits[offered[0] if offered else group["idle_index"]]=1
            self.assertTrue(decode(b,bits)["valid"])
            expected.add(tuple(bits))
        observed={tuple(sector_bits(b,self.sector,i)) for i in range(self.sector["states"])
                  if decode(b,sector_bits(b,self.sector,i))["valid"]}
        self.assertEqual(observed,expected)

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
