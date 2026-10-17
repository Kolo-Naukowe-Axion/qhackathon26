"""Physical/causal audit of calendar filling and early empty repositioning."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from stage2.advanced import AdvancedFactory, run
from stage2.engine import Factory
from stage2.check import check_trace, check_paired_causality
from stage2.reference import make_tiny
from stage2.spec import build
from stage2.dispatch import choose


class CalendarTests(unittest.TestCase):
    def factory_with_future_booking(self):
        factory=AdvancedFactory(make_tiny(15),dict(worker_calendar=True,preposition_ticks=0))
        factory.t=10
        worker=factory.workers["W1"];worker["busy"]=100
        factory.trace["operations"].append(dict(id="future",start=80,end=100,worker_ids=["W1"],
            worker_intervals=[dict(worker_id="W1",start=80,end=100)]))
        return factory,worker

    def test_same_hall_gap_before_future_appointment_can_be_used(self):
        factory,worker=self.factory_with_future_booking()
        self.assertIs(factory.available_worker("machining","A",5),worker)
        self.assertTrue(factory.fits(worker,75,5))
        self.assertFalse(factory.fits(worker,79,2))
        self.assertTrue(factory.fits(worker,100,5))

    def test_gap_filling_does_not_walk_away_from_a_future_hall_commitment(self):
        factory,worker=self.factory_with_future_booking()
        self.assertIsNone(factory.available_worker("machining","B",5))
        self.assertEqual(factory.trace["worker_moves"],[])
        self.assertEqual(worker["hall"],"A")

    def test_breaks_shifts_and_actual_walking_still_block_attendance(self):
        factory,worker=self.factory_with_future_booking()
        worker["breaks"]=[[14,16]]
        self.assertFalse(factory.fits(worker,13,2))
        worker["daily_shift"]=[0,32]
        self.assertFalse(factory.fits(worker,31,2))
        factory.trace["worker_moves"].append(dict(worker_id="W1",start=10,end=12,from_hall="A",to_hall="B"))
        self.assertFalse(factory.fits(worker,10,1))

    def test_disabled_calendar_preserves_baseline_observation_semantics(self):
        factory,_=self.factory_with_future_booking()
        factory.weights["worker_calendar"]=False
        self.assertEqual(factory.observation()["workers_free"],Factory.observation(factory)["workers_free"])
        factory.weights["worker_calendar"]=True
        self.assertEqual(factory.observation()["workers_free"],1)

    def test_one_worker_filling_two_roles_keeps_both_in_exported_metadata(self):
        factory=AdvancedFactory(build(orders=1),dict(worker_calendar=True,preposition_ticks=0))
        factory.t=10
        worker=factory.workers["W01"];worker["busy"]=210
        factory.trace["operations"].append(dict(id="future",start=200,end=210,worker_ids=["W01"],
            worker_intervals=[dict(worker_id="W01",start=200,end=210)]))
        part=factory.parts["P01/housing/1"];part.update(location="F1",step=1,status="waiting",busy=False)
        factory.machines["F1"]["family"]="alloy_B"
        factory.tools["mill1"]["location"]="F1"
        offer=factory.process(factory.machines["F1"],[part],preview=True)
        self.assertTrue(offer)
        self.assertEqual(offer["worker_ids"],["W01"])
        self.assertEqual(offer["worker_roles"]["W01"],["machining","setup"])
        self.assertTrue(offer["worker_calendar_aware"])

    def test_calendar_dispatch_can_combine_disjoint_worker_attendance(self):
        instance=make_tiny()
        def offer(mid,start,end):
            return dict(machine_id=mid,unit_ids=[mid],tool_ids=[],worker_ids=["W1"],
                worker_intervals=[dict(worker_id="W1",start=start,end=end)],end=20,power_kw=1)
        offers=[offer("T1",0,5),offer("F1",5,10)]
        chosen,_=choose(offers,instance,[],0,1000,[0,0],method="greedy")
        self.assertEqual(len(chosen),1)
        for op in offers:op["worker_calendar_aware"]=True
        chosen,_=choose(offers,instance,[],0,1000,[0,0],method="greedy")
        self.assertEqual(len(chosen),2)
        offers[1]["worker_intervals"][0]["start"]=4
        chosen,_=choose(offers,instance,[],0,1000,[0,0],method="greedy")
        self.assertEqual(len(chosen),1)


class RoutingAndBOMTests(unittest.TestCase):
    def factory(self,**weights):
        return AdvancedFactory(build(orders=2),dict(worker_calendar=True,preposition=False,
            due=0,remaining=0,noise=0,family=0,tool_distance=0,**weights))

    def test_free_buffer_routing_is_opt_in_and_uses_second_ranked_machine(self):
        f=self.factory();p=f.parts["P01/housing/1"];p.update(step=1,location="T1",status="waiting")
        f.machines["F2"]["busy"]=20;f.machines["F3"]["busy"]=30
        f.reserved["F1"]=f.machines["F1"]["input_capacity"]
        self.assertEqual(f.choose_machine(p)["id"],"F1")
        before=deepcopy((f.machines,f.parts,f.tools,f.reserved))
        f.weights["routing_free_buffers"]=True
        self.assertEqual(f.choose_machine(p)["id"],"F2")
        self.assertEqual((f.machines,f.parts,f.tools,f.reserved),before)
        for mid in ("F2","F3"):f.reserved[mid]=f.machines[mid]["input_capacity"]
        self.assertIsNone(f.choose_machine(p))

    def test_finish_estimate_uses_machine_speed_and_known_crew_calendar(self):
        f=self.factory(routing_estimate_finish=True)
        p=f.parts["P01/housing/1"];p.update(step=1,location="T1",status="waiting")
        f.machines["F1"]["duration_factor"]=[5,1]
        f.machines["F2"]["duration_factor"]=[1,1]
        f.machines["F3"]["duration_factor"]=[8,1]
        f.tools["mill1"]["location"]="F1";f.tools["mill2"]["location"]="F2"
        self.assertEqual(f.choose_machine(p)["id"],"F2")
        f.t=10;w=f.workers["W01"];w["daily_shift"]=[0,1000];w["breaks"]=[[30,40]]
        f.trace["operations"].append(dict(worker_ids=[w["id"]],start=50,end=80,
            worker_intervals=[dict(worker_id=w["id"],start=50,end=80)]))
        self.assertEqual(f.next_worker_interval(w,27,5),40)
        self.assertEqual(f.next_worker_interval(w,48,5),80)

    def test_critical_remaining_includes_component_tail_and_pump_join(self):
        f=self.factory(bom_priority="critical")
        housing=f.parts["P01/housing/1"];rotor=f.parts["P01/rotor/1"]
        self.assertEqual(f.remaining_processing(housing),345)
        self.assertEqual(f.remaining_processing(rotor),330)
        info=f.bom_orders()["P01"]
        self.assertEqual(info["pump_remaining"],105)
        self.assertEqual(info["critical_remaining"],450)
        self.assertLess(f.priority(housing),f.priority(rotor))

    def test_join_priority_prefers_last_missing_component_of_nearly_complete_bom(self):
        f=self.factory(bom_priority="join")
        for recipe in ("housing","rotor"):
            f.parts[f"P01/{recipe}/1"].update(accepted=True,step=5,status="waiting")
        first=f.parts["P01/flange/1"];second=f.parts["P02/flange/1"]
        self.assertLess(f.priority(first),f.priority(second))
        # A replacement is ranked from its own route, never from the scrapped
        # predecessor's apparent recipe progress.
        old=f.parts["P01/housing/1"];old["status"]="scrap"
        new=dict(old,id="P01/housing/1~r1",step=0,accepted=False,status="waiting")
        f.parts[new["id"]]=new;f.t+=1
        self.assertEqual(f.bom_orders()["P01"]["components"]["housing"]["id"],new["id"])
        self.assertEqual(f.bom_orders()["P01"]["components"]["housing"]["remaining"],345)

    def test_processing_and_repair_estimates_use_observed_remaining_work(self):
        f=self.factory(bom_priority="critical");p=f.parts["P01/housing/1"]
        p.update(status="processing",step=0);f.t=20
        f.active=[dict(unit_ids=[p["id"]],end=60)]
        self.assertEqual(f.remaining_processing(p),325)
        p["rework"]=[dict(process="T",base_ticks=45),dict(process="QA",base_ticks=45)]
        self.assertEqual(f.remaining_processing(p),85)
        p.update(status="waiting",accepted=True)
        self.assertEqual(f.remaining_processing(p),0)

    def test_remaining_duration_respects_precision_certification_under_turbo_policy(self):
        f=AdvancedFactory(build(orders=4),dict(mode="turbo",bom_priority="critical"))
        self.assertEqual(f.selected_mode("T","P04"),"standard")
        self.assertEqual(f.selected_mode("F","P04"),"standard")
        self.assertEqual(f.selected_mode("QA","P04"),"precision")
        p=f.parts["P04/housing/1"]
        self.assertEqual(f.remaining_processing(p),368+p["release_tick"])
        p["status"]="waiting"
        self.assertEqual(f.remaining_processing(p),368)

    def test_bom_scores_do_not_read_future_shock_or_quality_tape(self):
        factories=[AdvancedFactory(build(orders=2,seed=s),dict(bom_priority="slack")) for s in (0,1)]
        self.assertEqual([f.priority(f.parts["P01/housing/1"]) for f in factories],
                         [factories[0].priority(factories[0].parts["P01/housing/1"])]*2)


class PrepositionTests(unittest.TestCase):
    def prepared_factory(self,process="T"):
        factory=AdvancedFactory(build(orders=1,horizon=200,profile="coarse"),dict(preposition_ticks=10))
        factory.t=0;factory.admitted={"P01"}
        part=factory.parts["P01/housing/1"]
        part.update(step=0 if process=="T" else 4,status="processing",busy=True,location="T1" if process=="T" else "QA1")
        factory.active=[dict(id="active",process=process,start=0,end=5,unit_ids=[part["id"]])]
        for vehicle in factory.agvs.values():vehicle.update(busy=200)
        return factory,part

    def test_inspection_outcomes_are_not_prepositioned(self):
        factory,_=self.prepared_factory("QA")
        vehicle=factory.agvs["AGV1"];vehicle.update(busy=0,soc=120)
        self.assertFalse(factory.charge(vehicle))
        self.assertEqual(factory.trace["moves"],[])

    def test_explicit_preposition_toggle_disables_future_dispatch(self):
        factory,_=self.prepared_factory()
        factory.weights["preposition"]=False
        vehicle=factory.agvs["AGV1"];vehicle.update(busy=0,soc=120)
        self.assertFalse(factory.charge(vehicle))
        self.assertEqual(factory.trace["moves"],[])

    def test_failed_future_move_restores_busy_flag_and_ready_override(self):
        factory,part=self.prepared_factory()
        self.assertFalse(factory.future_move(part,part["location"],5))
        self.assertIs(part["busy"],True)
        self.assertIsNone(factory._ready_tick)

    def test_temporary_busy_override_is_restored_if_choice_raises(self):
        factory,part=self.prepared_factory()
        with patch.object(Factory,"move",side_effect=ValueError("synthetic route failure")):
            with self.assertRaises(ValueError):factory.future_move(part,"F1",5)
        self.assertIs(part["busy"],True)
        self.assertIsNone(factory._ready_tick)

    def test_charging_one_vehicle_does_not_silently_assign_another(self):
        factory,part=self.prepared_factory()
        low=factory.agvs["AGV1"];low.update(busy=0,soc=1,location="CHARGE_A")
        other=factory.agvs["AGV2"];other.update(busy=0,soc=120,location="RAW_A")
        self.assertTrue(factory.charge(low))
        self.assertEqual(factory.trace["moves"][0]["agv_id"],"AGV1")
        self.assertEqual(factory.trace["moves"][0]["kind"],"charge")
        self.assertFalse(part.get("moving"))
        self.assertEqual(other["busy"],0)
        self.assertEqual(len(factory.agvs),4)
        self.assertTrue(factory.charge(other))
        move=factory.trace["moves"][-1]
        self.assertEqual(move["agv_id"],"AGV2")
        self.assertTrue(move["preposition"])
        self.assertGreaterEqual(move["pickup_tick"],5)


class PhysicalAndCausalIntegrationTests(unittest.TestCase):
    def test_disabled_features_match_baseline_actions_and_leave_instance_unchanged(self):
        instance=make_tiny();before=deepcopy(instance)
        weights=dict(worker_calendar=False,preposition_ticks=0,wip_limit=1)
        baseline=Factory(instance,weights).run();advanced=run(instance,weights)
        for field in ("operations","moves","worker_moves","events","energy","metrics"):
            self.assertEqual(baseline[field],advanced[field],field)
        self.assertEqual(instance,before)
        self.assertTrue(check_trace(advanced)["valid"])

    def test_prepositioned_full_trace_waits_for_completion_and_skips_qa(self):
        trace=run(make_tiny(15),dict(wip_limit=1,worker_calendar=True,preposition_ticks=10))
        result=check_trace(trace)
        self.assertTrue(result["valid"],result["issues"])
        moves=[move for move in trace["moves"] if move.get("preposition")]
        self.assertTrue(moves)
        for move in moves:
            sources=[op for op in trace["operations"] if move["unit_id"] in op["unit_ids"] and
                     op["machine_id"]==move["from"] and op["end"]==move["source_ready_tick"]]
            self.assertEqual(len(sources),1)
            self.assertNotEqual(sources[0]["process"],"QA")
            self.assertLess(move["start"],move["source_ready_tick"])
            self.assertGreaterEqual(move["pickup_tick"],move["source_ready_tick"])

    def test_separate_ablations_are_physically_valid_and_causal_on_paired_tapes(self):
        for calendar,lookahead in ((True,0),(False,10),(True,10)):
            with self.subTest(calendar=calendar,lookahead=lookahead):
                traces=[run(build(orders=3,horizon=2880,seed=seed),dict(wip_limit=2,lease_calibration=True,
                    worker_calendar=calendar,preposition_ticks=lookahead)) for seed in range(4)]
                for trace in traces:
                    result=check_trace(trace)
                    self.assertTrue(result["valid"],result["issues"])
                    if not lookahead:self.assertFalse(any(move.get("preposition") for move in trace["moves"]))
                causal=check_paired_causality(traces)
                self.assertTrue(causal["valid"],causal["issues"])

    def test_routing_and_bom_variants_preserve_full_physics_and_reveal_prefixes(self):
        for routing,estimate,rule in ((True,False,"join"),(True,True,"critical"),(False,True,"slack")):
            with self.subTest(routing=routing,estimate=estimate,rule=rule):
                weights=dict(wip_limit=2,lease_calibration=True,routing_free_buffers=routing,
                    routing_estimate_finish=estimate,bom_priority=rule)
                traces=[run(build(orders=3,horizon=2880,seed=s),weights) for s in range(4)]
                for trace in traces:
                    report=check_trace(trace)
                    self.assertTrue(report["valid"],report["issues"])
                report=check_paired_causality(traces)
                self.assertTrue(report["valid"],report["issues"])


if __name__=="__main__":unittest.main()
