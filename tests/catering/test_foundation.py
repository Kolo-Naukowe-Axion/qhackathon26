import copy
import itertools
import tempfile
import unittest
from pathlib import Path

from catering.domain import fixture, snapshot, make_plan, program_id, validate_instance, digest
from catering.check import check_plan
from catering.options import enumerate_options, restricted_pool
from catering.qubo import compile_qubo, energy, objective_energy, ising, bounded_weights, validate_bundle
from catering.native import bits_for_selection, solve_program_master, solve_native
from catering.decode import decode
from catering.audit import audit_bundle
from catering.methods.classical import solve_exact, solve_qubo
from catering.contracts import save_json
from catering.run import evaluate


class FoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.instance = fixture()
        cls.states = {s:snapshot(cls.instance,s) for s in ("S0","S1","S2","S3")}
        cls.programs = {s:enumerate_options(cls.instance,state) for s,state in cls.states.items()}
        cls.bundles = {s:compile_qubo(cls.instance, state, restricted_pool(cls.programs[s],state,8),
                                    representation="test-cap8", parent_sha256="unit-test-parent")
                       for s,state in cls.states.items()}

    def test_four_cases_share_committed_prefix_and_reveal_only_current_event(self):
        self.assertEqual(len({s["common_prefix_sha256"] for s in self.states.values()}),1)
        self.assertEqual([len(self.states[s]["demand_groups"]) for s in self.states],[2,3,2,3])
        self.assertEqual([len(self.states[s]["outages"]) for s in self.states],[0,0,1,1])
        self.assertEqual([len(self.programs[s]) for s in self.states],[26,89,0,8])

    def test_unsupported_capacities_and_interrupted_outage_fail_closed(self):
        p=copy.deepcopy(self.instance);p["capacities"]["holding"]=True
        with self.assertRaises(ValueError):validate_instance(p)
        p=copy.deepcopy(self.instance);p["outage"]["resource"]="C1"
        with self.assertRaises(ValueError):snapshot(p,"S2")

    def test_outage_domain_rejects_future_malformed_and_non_cooker_withdrawals(self):
        invalid=[dict(start=20,end=61),dict(start=20.5,end=60),
                 dict(start=70,end=60),dict(start=30,end=60),
                 dict(start=0,end=20),dict(start=20,end=120),
                 dict(resource="W2"),dict(start=True),dict(end=False)]
        for changes in invalid:
            with self.subTest(changes=changes):
                instance=copy.deepcopy(self.instance)
                instance["outage"].update(changes)
                with self.assertRaises(ValueError):validate_instance(instance)
        for event in (-10,20.0,True,110):
            with self.subTest(event=event):
                instance=copy.deepcopy(self.instance);instance["event_time"]=event
                with self.assertRaises(ValueError):validate_instance(instance)
        ongoing=copy.deepcopy(self.instance);ongoing["outage"]["start"]=10
        self.assertEqual(snapshot(ongoing,"S2")["outages"][0]["start"],10)

    def test_checker_rejects_forged_future_outage_even_with_valid_recovery_records(self):
        state=copy.deepcopy(self.states["S2"])
        state["outages"][0]["start"]=30
        plan=make_plan(self.instance,state["fixed_batches"],state["recovery_operations"])
        result=check_plan(self.instance,state,plan)
        self.assertFalse(result["valid"])
        self.assertIn("Invalid observed cooker outage in snapshot",result["violations"])

    def test_checker_rejects_forged_noninteger_or_out_of_grid_event_time(self):
        for event in (20.0,20.5,True,-10,110):
            with self.subTest(event=event):
                state=copy.deepcopy(self.states["S2"]);state["current_time"]=event
                plan=make_plan(self.instance,state["fixed_batches"],state["recovery_operations"])
                result=check_plan(self.instance,state,plan)
                self.assertFalse(result["valid"])
                self.assertIn("Invalid snapshot event time",result["violations"])

    def test_raw_full_plan_and_material_disposal(self):
        state=self.states["S0"]
        p=next(p for p in self.programs["S0"] if p["yield_lots"]==2)
        plan=make_plan(self.instance,state["fixed_batches"]+[p])
        checked=check_plan(self.instance,state,plan)
        self.assertTrue(checked["valid"])
        self.assertEqual(checked["metrics"]["W"],1)
        plan["disposals"]=[]
        self.assertIn("Material balance",check_plan(self.instance,state,plan)["violations"])

    def test_freshness_is_measured_at_departure(self):
        state=copy.deepcopy(self.states["S0"])
        plan=make_plan(self.instance,state["fixed_batches"]+state["previous_unstarted"])
        self.assertTrue(check_plan(self.instance,state,plan)["valid"])
        state["demand_groups"][1]["departure"]=110
        self.assertIn("Stale handover",check_plan(self.instance,state,plan)["violations"])

    def test_worker_double_booking_and_qualification_are_enforced(self):
        instance=copy.deepcopy(self.instance)
        instance["workers"]["W1"].append("clean")
        state=self.states["S0"]
        p=copy.deepcopy(state["previous_unstarted"][0])
        p["workers"]["clean"]="W1";p["id"]=program_id(p)
        plan=make_plan(instance,state["fixed_batches"]+[p])
        self.assertIn("Overlap: W1",check_plan(instance,state,plan)["violations"])

    def test_committed_work_missing_operations_and_double_delivery_are_rejected(self):
        state=self.states["S0"]
        plan=make_plan(self.instance,state["fixed_batches"]+state["previous_unstarted"])
        broken=copy.deepcopy(plan);broken["batches"]=broken["batches"][1:]
        self.assertFalse(check_plan(self.instance,state,broken)["valid"])
        broken=copy.deepcopy(plan);broken["operations"].pop()
        self.assertFalse(check_plan(self.instance,state,broken)["valid"])
        broken=copy.deepcopy(plan);broken["allocations"].append(copy.deepcopy(broken["allocations"][0]))
        self.assertFalse(check_plan(self.instance,state,broken)["valid"])

    def test_outage_requires_a_changed_future_plan(self):
        state=self.states["S2"]
        plan=make_plan(self.instance,state["fixed_batches"]+state["previous_unstarted"])
        self.assertIn("Outage violation",check_plan(self.instance,state,plan)["violations"])

    def test_post_repair_clean_is_mandatory_even_without_new_production(self):
        state=self.states["S2"]
        self.assertEqual(state["recovery_operations"][0]["start"],70)
        self.assertEqual(state["recovery_operations"][0]["end"],80)
        plan=make_plan(self.instance,state["fixed_batches"],state["recovery_operations"])
        self.assertTrue(check_plan(self.instance,state,plan)["valid"])
        plan.pop("recovery_operations")
        self.assertIn("Mandatory post-repair clean changed or missing",check_plan(self.instance,state,plan)["violations"])
        broken=copy.deepcopy(state);broken["recovery_operations"]=[]
        self.assertIn("Missing mandatory post-repair clean in state",check_plan(self.instance,broken,plan)["violations"])

    def test_cooking_at_repair_end_before_the_clean_is_rejected(self):
        state=self.states["S2"]
        p=copy.deepcopy(state["previous_unstarted"][0])
        p.update(prep_start=40,cook_start=60,pack_start=80)
        p["id"]=program_id(p)
        plan=make_plan(self.instance,state["fixed_batches"]+[p],state["recovery_operations"])
        self.assertIn("Cooking before post-repair clean finishes",check_plan(self.instance,state,plan)["violations"])

    def test_corrected_outage_metrics_include_the_lost_nominal_order(self):
        for scenario,metrics in (("S2",dict(U=1,W=0,B=0,R=1)),("S3",dict(U=1,W=0,B=1,R=2))):
            result=solve_native(self.instance,self.states[scenario],dict(wall_time_limit_s=3))
            self.assertEqual(result["reference"]["status"],"OPTIMAL")
            self.assertEqual(result["check"]["metrics"],metrics)
            if scenario=="S3":
                new=[b for b in result["plan"]["batches"] if b["menu"]=="B"]
                self.assertEqual(new[0]["cooker"],"C1")
                self.assertEqual(new[0]["allocation_order"],["B/12:10-urgent"])

    def test_bounded_registers_cover_exact_ranges(self):
        for bound in range(65):
            weights=bounded_weights(bound)
            self.assertEqual({sum(a*b for a,b in zip(bits,weights))
                              for bits in itertools.product((0,1),repeat=len(weights))},set(range(bound+1)))

    def test_literal_zero_penalty_and_ising_match_independent_raw_choices(self):
        for scenario,bundle in self.bundles.items():
            with self.subTest(scenario=scenario):
                audit=audit_bundle(bundle)
                self.assertTrue(audit["valid"])
                self.assertEqual(audit["all_bitstrings_checked"],1<<bundle["size"]["binary_variables"])
                exact=solve_exact(bundle)
                self.assertEqual(exact["reference"]["objective"],audit["raw_enumeration"]["exact_best_energy"])
                for sample in exact["samples"]:self.assertTrue(decode(bundle,sample["bits"])["valid"])

    def test_native_optional_intervals_agree_with_qubo_without_reading_conflict_list(self):
        for bundle in self.bundles.values():
            changed=copy.deepcopy(bundle);changed["conflicts"]=[[-99,-98]]
            native=solve_program_master(changed,dict(wall_time_limit_s=3))
            exact=solve_exact(bundle)
            self.assertEqual(native["reference"]["status"],"OPTIMAL")
            self.assertEqual(native["reference"]["objective"],exact["reference"]["objective"])
            self.assertFalse(native["reference"]["reads_qubo_conflict_list"])

    def test_urgent_sharing_and_core_reference(self):
        result=solve_native(self.instance,self.states["S1"],dict(wall_time_limit_s=3))
        self.assertEqual(result["reference"]["status"],"OPTIMAL")
        self.assertEqual(result["check"]["metrics"],dict(U=0,W=0,B=1,R=2))
        batches=[p for p in result["plan"]["batches"] if p["id"] not in {f["id"] for f in self.states["S1"]["fixed_batches"]}]
        self.assertEqual(len(batches),1)
        self.assertEqual(batches[0]["yield_lots"],2)
        self.assertEqual(len(set(batches[0]["allocation_order"])),2)

    def test_hash_integrity_order_and_normalized_bits(self):
        bundle=copy.deepcopy(self.bundles["S0"])
        validate_bundle(bundle)
        bundle["linear"][0]=str(int(bundle["linear"][0])+1)
        with self.assertRaises(ValueError):validate_bundle(bundle)
        bundle=self.bundles["S0"]
        for bits in ([],[0.0]*len(bundle["linear"]),[True]*len(bundle["linear"])):
            with self.assertRaises(ValueError):energy(bundle,bits)

    def test_physical_plan_can_be_valid_while_register_is_wrong(self):
        bundle=self.bundles["S0"]
        bits=bits_for_selection(bundle,[])
        self.assertTrue(decode(bundle,bits)["valid"])
        bits[bundle["registers"][0]["indices"][0]]=0
        checked=decode(bundle,bits)
        self.assertTrue(checked["physical_valid"])
        self.assertFalse(checked["register_valid"])
        self.assertFalse(checked["valid"])

    def test_sa_returns_exact_literal_energies_without_repair(self):
        bundle=self.bundles["S1"]
        result=solve_qubo(bundle,dict(wall_time_limit_s=2),dict(seed=4,restarts=3,sweeps=20))
        for sample in result["samples"]:
            self.assertEqual(int(sample["reported_energy"]),energy(bundle,sample["bits"]))
        self.assertFalse(result["configuration"]["repair"])

    def test_evaluator_requires_identity_energy_and_fresh_output(self):
        bundle=self.bundles["S0"]
        result=solve_exact(bundle)
        with tempfile.TemporaryDirectory() as name:
            root=Path(name)
            save_json(root/"bundle.json",bundle);save_json(root/"result.json",result)
            checks=evaluate(root/"bundle.json",root/"result.json",root/"checks.json")
            self.assertTrue(all(c["valid"] for c in checks))
            with self.assertRaises(ValueError):evaluate(root/"bundle.json",root/"result.json",root/"checks.json")
            result["samples"][0]["reported_energy"]="999999999"
            save_json(root/"bad.json",result)
            with self.assertRaises(ValueError):evaluate(root/"bundle.json",root/"bad.json",root/"bad-checks.json")


if __name__=="__main__":
    unittest.main()
