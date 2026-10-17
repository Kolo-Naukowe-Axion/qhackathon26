"""Corruptions and boundary cases for the independent Stage 2 checker."""

import unittest
from copy import deepcopy

from stage2.check import Interval, interval_violations, check_trace, check_paired_causality


def simple_trace():
    """One manual physical route; does not call the simulator under test."""
    spec = dict(tick_minutes=15, horizon_ticks=8,
        machines=[dict(id="T1", process="T", hall="A", duration_factor=[1, 1], input_capacity=1)],
        workers=[dict(id="W1", skills=["machining"], daily_shift=[0, 96], breaks=[], initial_hall="A")],
        tools=[], agvs=[dict(id="AGV1", initial_location="RAW_A", initial_soc=120, capacity=160)],
        orders=[dict(id="P1", release_tick=0, due_tick=6)],
        units=[dict(id="h1", recipe="housing", order_id="P1", family="a", initial_location="RAW_A", release_tick=0)],
        recipes={"housing": [dict(process="T", base_ticks=4)]},
        modes={"T": {"standard": dict(duration_factor=[1, 1], power_kw=9, wear=1)}},
        process_skills={"T": "machining"}, process_tools={}, setup_matrix={"a": {"a": 0, "b": 2}, "b": {"a": 2, "b": 0}},
        maintenance=dict(wear_limit=70), worker_travel_ticks=2,
        transport=dict(loaded_soc_per_tick=2, empty_soc_per_tick=1, charge_rate=12, charge_power_kw=4),
        graph_edges=[dict(a="RAW_A", b="HUB_A", ticks=1), dict(a="HUB_A", b="T1", ticks=1)],
        energy=dict(base_load_kw=12, normal_grid_cap_kw=90, stationary_soc_initial=40,
            stationary_soc_min=8, stationary_soc_capacity=160, stationary_soc_terminal_min=40,
            solar_peak_kw=0, tariff_low=.12, tariff_peak=.34, carbon_low=.25, carbon_peak=.65,
            battery_actions=[dict(id="idle", charge_kw=0, discharge_kw=0, soc_delta=0)]))
    return dict(schema="metaltech-stage2-trace.v1", instance=spec, horizon_ticks=8, tick_minutes=15,
        operations=[dict(id="O1", unit_id="h1", unit_ids=["h1"], order_id="P1", process="T", machine_id="T1",
            start=4, end=8, mode="standard", worker_ids=["W1"], tool_ids=[], parent_unit_ids=[],
            setup_ticks=0, processing_ticks=4, power_kw=9, family="a", kind="process", recipe_step=0, attempt=0)],
        moves=[dict(id="M1", unit_id="h1", entity_type="part", agv_id="AGV1", start=0, pickup_tick=0,
            drop_tick=4, end=4, **{"from": "RAW_A", "to": "T1"},
            legs=[dict(**{"from": "RAW_A", "to": "HUB_A"}, start=1, end=2, loaded=True),
                  dict(**{"from": "HUB_A", "to": "T1"}, start=2, end=3, loaded=True)],
            soc_before=120, soc_after=116, kind="transport")],
        events=[dict(tick=0, type="release", unit_id="h1", recipe="housing")], worker_moves=[], energy=[dict(tick=t, load_kw=12+(9 if t >= 4 else 0),
            grid_kw=12+(9 if t >= 4 else 0), cap_kw=90, solar_kw=0, curtailed_kw=0,
            soc_before=40, soc=40, battery_action="idle", tariff=.12, carbon_intensity=.25) for t in range(8)])


def assembly_trace():
    trace = simple_trace()
    spec = trace["instance"]
    spec["machines"] = [dict(id="QA1", process="QA", hall="B", duration_factor=[1, 1], input_capacity=3),
                        dict(id="A1", process="ASSEMBLY", hall="B", duration_factor=[1, 1], input_capacity=3)]
    spec["workers"][0].update(skills=["qa", "assembly"], initial_hall="B")
    spec["agvs"] = [dict(id=f"AGV{i+1}", initial_location="QA1", initial_soc=120, capacity=160) for i in range(3)]
    spec["units"] = [dict(id=recipe, recipe=recipe, order_id="P1", family="a", initial_location="QA1", release_tick=0)
                     for recipe in ("housing", "rotor", "flange")]
    spec["recipes"] = {recipe: [dict(process="QA", base_ticks=1)] for recipe in ("housing", "rotor", "flange")}
    spec["recipes"]["pump"] = [dict(process="ASSEMBLY", base_ticks=1), dict(process="QA", base_ticks=1)]
    spec["modes"] = {process: {"standard": dict(duration_factor=[1, 1], power_kw=power, wear=1)}
                     for process, power in (("QA", 3), ("ASSEMBLY", 4))}
    spec["process_skills"] = {"QA": "qa", "ASSEMBLY": "assembly"}
    spec["graph_edges"] = [dict(a="QA1", b="HUB_B", ticks=1), dict(a="HUB_B", b="A1", ticks=1)]
    trace["operations"], trace["moves"], trace["events"] = [], [], []
    for index, recipe in enumerate(("housing", "rotor", "flange")):
        trace["events"].append(dict(tick=0, type="release", unit_id=recipe, recipe=recipe))
        op = deepcopy(simple_trace()["operations"][0])
        op.update(id=f"Q{index}", unit_id=recipe, unit_ids=[recipe], process="QA", machine_id="QA1",
                  start=index, end=index+1, processing_ticks=1, power_kw=3)
        trace["operations"].append(op)
        trace["events"].append(dict(tick=index+1, type="qa_result", unit_id=recipe, passed=True))
        pickup=index+1
        trace["moves"].append(dict(id=f"M{index}", unit_id=recipe, entity_type="part", agv_id=f"AGV{index+1}",
            start=pickup, pickup_tick=pickup, drop_tick=pickup+4, end=pickup+4,
            **{"from":"QA1", "to":"A1"}, soc_before=120, soc_after=116, kind="transport",
            legs=[dict(**{"from":"QA1", "to":"HUB_B"}, start=pickup+1, end=pickup+2, loaded=True),
                  dict(**{"from":"HUB_B", "to":"A1"}, start=pickup+2, end=pickup+3, loaded=True)]))
    op = deepcopy(simple_trace()["operations"][0])
    op.update(id="A", unit_id="pump", unit_ids=["pump"], process="ASSEMBLY", machine_id="A1",
              start=7, end=8, processing_ticks=1, power_kw=4, parent_unit_ids=["housing", "rotor", "flange"])
    trace["operations"].append(op)
    for row in trace["energy"]:
        row["load_kw"] = row["grid_kw"] = 12 + (3 if row["tick"] < 3 else 4 if row["tick"] == 7 else 0)
    return trace


def leased_trace():
    trace = simple_trace()
    trace["instance"].update(investment_budget=250, lease_options=[dict(id="calibration-kit", cost=150,
        lead_ticks=2, max_count=1, resource=dict(id="leased", kind="calibration", initial_location="TOOL_B", life=40, service_ticks=4))])
    trace["events"].extend([dict(tick=0, type="lease_request", option_id="calibration-kit", cost=150, arrival_tick=2),
                            dict(tick=2, type="lease_delivery", option_id="calibration-kit", tool=deepcopy(trace["instance"]["lease_options"][0]["resource"]))])
    return trace


def history_quality_trace():
    trace = simple_trace(); spec = trace["instance"]
    trace["horizon_ticks"] = spec["horizon_ticks"] = 13
    spec.update(seed=0, quality=dict(risk_model="manufacturing_mode_history", manufacturing_defect_probabilities={"T":{"standard":.1}},
        wear_risk_coefficient=.01, repair_residual_probability=.02))
    spec["recipes"]["housing"].append(dict(process="QA", base_ticks=1))
    spec["machines"].append(dict(id="QA1", process="QA", hall="A", duration_factor=[1,1], input_capacity=1))
    spec["workers"][0]["skills"].append("qa")
    spec["modes"]["QA"] = {"standard":dict(duration_factor=[1,1],power_kw=3,wear=1)}
    spec["process_skills"]["QA"] = "qa"
    spec["graph_edges"].append(dict(a="HUB_A",b="QA1",ticks=1))
    trace["moves"].append(dict(id="M2",unit_id="h1",entity_type="part",agv_id="AGV1",start=8,pickup_tick=8,drop_tick=12,end=12,
        **{"from":"T1","to":"QA1"},soc_before=116,soc_after=112,kind="transport",
        legs=[dict(**{"from":"T1","to":"HUB_A"},start=9,end=10,loaded=True),
              dict(**{"from":"HUB_A","to":"QA1"},start=10,end=11,loaded=True)]))
    op=deepcopy(trace["operations"][0]);op.update(id="Q1",process="QA",machine_id="QA1",start=12,end=13,processing_ticks=1,power_kw=3,recipe_step=1)
    trace["operations"].append(op)
    trace["events"].append(dict(tick=13,type="qa_result",unit_id="h1",passed=True,keyed_uniform=.9331343081568929,defect_probability=.1))
    trace["energy"]=[]
    for t in range(13):
        load=12+(9 if 4<=t<8 else 3 if t==12 else 0)
        trace["energy"].append(dict(tick=t,load_kw=load,grid_kw=load,cap_kw=90,solar_kw=0,curtailed_kw=0,
            soc_before=40,soc=40,battery_action="idle",tariff=.12,carbon_intensity=.25))
    return trace


class ResourceCalendarTests(unittest.TestCase):
    def test_finish_before_start_at_boundary(self):
        self.assertEqual(interval_violations([Interval(0, 2, source="a"), Interval(2, 4, source="b")]), [])

    def test_true_overlap_is_found(self):
        issues = interval_violations([Interval(0, 3, source="a"), Interval(2, 4, source="b")])
        self.assertEqual(issues[0]["tick"], 2)
        self.assertEqual(issues[0]["event_ids"], ["a", "b"])

    def test_cumulative_resource(self):
        self.assertEqual(interval_violations([Interval(0, 3, 2), Interval(1, 2, 3)], capacity=5), [])
        self.assertTrue(interval_violations([Interval(0, 3, 2), Interval(1, 2, 3)], capacity=4))

    def test_bad_interval_does_not_hide_collision(self):
        issues = interval_violations([Interval(2, 1, source="bad"), Interval(0, 3), Interval(1, 4)])
        self.assertEqual({x["code"] for x in issues}, {"interval", "resource_capacity"})


class TraceCorruptionTests(unittest.TestCase):
    def assert_rejected(self, trace, code):
        result = check_trace(trace)
        self.assertFalse(result["valid"], result)
        self.assertIn(code, {x["code"] for x in result["issues"]}, result["issues"])

    def test_manual_partial_trace_passes_without_claiming_fulfillment(self):
        result = check_trace(simple_trace())
        self.assertTrue(result["valid"], result["issues"])
        self.assertFalse(result["all_orders_fulfilled"])
        self.assertEqual(result["metrics"]["terminal_deadline_debt_ticks"], 2)
        self.assertAlmostEqual(result["metrics"]["grid_kwh"], 33)

    def test_part_teleport(self):
        trace = simple_trace()
        trace["moves"][0]["from"] = "T1"
        self.assert_rejected(trace, "part_pickup_location")

    def test_process_before_physical_delivery(self):
        trace = simple_trace()
        trace["operations"][0].update(start=3, end=7)
        self.assert_rejected(trace, "part_process_location")

    def test_machine_worker_overlap(self):
        trace = simple_trace()
        duplicate = deepcopy(trace["operations"][0]); duplicate["id"] = "O2"
        trace["operations"].append(duplicate)
        self.assert_rejected(trace, "resource_capacity")

    def test_worker_break(self):
        trace = simple_trace()
        trace["instance"]["workers"][0]["breaks"] = [[6, 7]]
        self.assert_rejected(trace, "worker_calendar")

    def test_worker_skill(self):
        trace = simple_trace()
        trace["instance"]["workers"][0]["skills"] = ["qa"]
        self.assert_rejected(trace, "worker_skill")

    def test_mode_duration(self):
        trace = simple_trace()
        trace["operations"][0]["processing_ticks"] = 3
        self.assert_rejected(trace, "processing_duration")

    def test_setup_immediate_predecessor(self):
        trace = simple_trace()
        trace["instance"]["machines"][0]["initial_family"] = "b"
        self.assert_rejected(trace, "setup_sequence")

    def test_tool_location(self):
        trace = simple_trace()
        trace["instance"]["tools"] = [dict(id="mill1", kind="mill", initial_location="TOOL_A", life=40)]
        trace["instance"]["process_tools"] = {"T": "mill"}
        trace["operations"][0]["tool_ids"] = ["mill1"]
        self.assert_rejected(trace, "tool_location")

    def test_buffer_reservation(self):
        trace = simple_trace()
        trace["instance"]["machines"][0]["input_capacity"] = 0
        self.assert_rejected(trace, "buffer_capacity")

    def test_agv_path_and_soc(self):
        trace = simple_trace()
        trace["moves"][0]["legs"][0]["to"] = "SHIP_B"
        self.assert_rejected(trace, "agv_path")
        trace = simple_trace(); trace["moves"][0]["soc_after"] = 119
        self.assert_rejected(trace, "agv_soc_after")

    def test_fake_qa_and_shipping(self):
        trace = simple_trace()
        trace["events"] = [dict(tick=8, type="qa_result", unit_id="h1", passed=True), dict(tick=8, type="ship", unit_id="h1")]
        self.assert_rejected(trace, "qa_boundary")
        self.assert_rejected(trace, "shipping")

    def test_energy_hidden_demand_grid_and_battery(self):
        trace = simple_trace(); trace["energy"][5]["load_kw"] -= 9
        self.assert_rejected(trace, "energy_load")
        trace = simple_trace(); trace["energy"][5]["grid_kw"] = 99
        self.assert_rejected(trace, "energy_grid_cap")
        trace = simple_trace(); trace["energy"][5]["soc"] += 9
        self.assert_rejected(trace, "battery_soc")

    def test_reported_summary_cannot_fake_success(self):
        trace = simple_trace(); trace["metrics"] = {"shipped": 999, "grid_kwh": 0}
        result = check_trace(trace)
        self.assertTrue(result["valid"])
        self.assertEqual(result["metrics"]["delivered_orders"], 0)
        self.assertEqual(result["metrics"]["grid_kwh"], 33)

    def test_raw_stock_and_premature_release(self):
        trace = simple_trace(); trace["instance"]["raw_stock_units"] = {"housing": 0}
        self.assert_rejected(trace, "raw_stock")
        trace = simple_trace(); trace["events"][0]["tick"] = 1
        self.assert_rejected(trace, "part_pickup_location")

    def test_paired_causality_finds_hidden_tape_leak(self):
        left = simple_trace(); right = deepcopy(left)
        self.assertTrue(check_paired_causality([left, right])["valid"])
        right["operations"][0]["mode"] = "turbo"
        result = check_paired_causality([left, right])
        self.assertFalse(result["valid"])
        self.assertEqual(result["issues"][0]["tick"], 4)
        right["events"].append(dict(tick=4, type="reveal", outcome="different"))
        self.assertTrue(check_paired_causality([left, right])["valid"])

    def test_automatic_machine_can_run_unattended_during_break(self):
        trace = simple_trace()
        trace["instance"]["attendance"] = {"T":dict(kind="start", ticks=1)}
        trace["instance"]["workers"][0]["breaks"] = [[6, 7]]
        trace["operations"][0]["worker_intervals"] = [dict(worker_id="W1", start=4, end=5, role="process", skills=["machining"])]
        self.assertTrue(check_trace(trace)["valid"], check_trace(trace)["issues"])
        trace["operations"][0]["worker_intervals"][0]["start"] = 5
        self.assert_rejected(trace, "worker_attendance")

    def test_separate_setup_crew_has_its_own_skill_and_interval(self):
        trace = simple_trace()
        trace["instance"]["attendance"] = {"T":dict(kind="start", ticks=1)}
        trace["instance"]["machines"][0]["initial_family"] = "b"
        trace["instance"]["workers"].append(dict(id="W2", skills=["setup"], initial_hall="A", daily_shift=[0,96], breaks=[]))
        trace["operations"][0].update(end=10, setup_ticks=2, worker_ids=["W1","W2"],
            worker_intervals=[dict(worker_id="W1", start=6, end=7, role="process", skills=["machining"]),
                              dict(worker_id="W2", start=4, end=6, role="setup", skills=["setup"])])
        self.assertTrue(check_trace(trace)["valid"], check_trace(trace)["issues"])
        trace["instance"]["workers"][1]["skills"] = []
        self.assert_rejected(trace, "worker_attendance")

    def test_bom_join_passes_then_rejects_wrong_or_duplicate_parent(self):
        trace = assembly_trace()
        self.assertTrue(check_trace(trace)["valid"], check_trace(trace)["issues"])
        trace["instance"]["units"][0]["order_id"] = "OTHER"
        self.assert_rejected(trace, "bom_genealogy")
        trace = assembly_trace(); trace["operations"][-1]["parent_unit_ids"] = ["housing", "rotor", "rotor"]
        self.assert_rejected(trace, "bom_quantity")
        self.assert_rejected(trace, "bom_consumption")

    def test_machine_output_blocks_until_actual_pickup(self):
        trace = assembly_trace()
        trace["moves"][0]["pickup_tick"] = 2
        self.assert_rejected(trace, "machine_blocking")

    def test_outage_and_handling_times(self):
        trace = simple_trace(); trace["events"].append(dict(type="outage", tick=5, machine="T1", start=5, end=7))
        self.assert_rejected(trace, "machine_outage")
        trace = simple_trace(); trace["moves"][0]["drop_tick"] = 3
        self.assert_rejected(trace, "transport_handling")

    def test_lease_birth_budget_and_total_cost(self):
        trace = leased_trace(); result=check_trace(trace)
        self.assertTrue(result["valid"],result["issues"])
        self.assertEqual(result["metrics"]["investment_cost"],150)
        self.assertAlmostEqual(result["metrics"]["total_cost"],153.96)
        trace["events"][-1]["tick"]=1
        self.assert_rejected(trace,"lease_birth")
        trace=leased_trace();trace["instance"]["investment_budget"]=100
        self.assert_rejected(trace,"investment_budget")
        trace=leased_trace();trace["metrics"]={"total_cost":3.96}
        self.assert_rejected(trace,"summary_total_cost")

    def test_lease_cannot_appear_for_free_or_duplicate(self):
        trace=leased_trace();trace["events"][-2]["cost"]=0
        self.assert_rejected(trace,"lease_terms")
        trace=leased_trace();trace["events"].append(deepcopy(trace["events"][-2]))
        self.assert_rejected(trace,"lease_count")
        trace=leased_trace();trace["events"][-1]["tool"]["life"]=999
        self.assert_rejected(trace,"lease_resource")
        trace=leased_trace();trace["events"].pop()
        self.assert_rejected(trace,"lease_delivery_missing")

    def test_declared_material_delivery_and_delay(self):
        trace=simple_trace()
        trace["instance"]["delivery"]=dict(id="D1",normal_tick=2,delayed_tick=5,contents={"housing":4})
        trace["events"].append(dict(tick=2,type="delivery",delivery_id="D1",contents={"housing":4}))
        self.assertTrue(check_trace(trace)["valid"],check_trace(trace)["issues"])
        trace["events"][-1]["tick"]=5
        self.assert_rejected(trace,"material_delivery")
        trace["events"].append(dict(tick=1,type="delivery_delay",delivery_id="D1",original_tick=2,new_tick=5))
        self.assertTrue(check_trace(trace)["valid"],check_trace(trace)["issues"])
        trace["events"][-2]["contents"]["housing"]=400
        self.assert_rejected(trace,"material_delivery")

    def test_precision_mode_certification(self):
        trace=simple_trace()
        trace["instance"]["orders"][0]["precision_required"]=True
        trace["instance"]["certification_modes"]={"precision":{"T":["eco"]}}
        self.assert_rejected(trace,"mode_certification")

    def test_quality_is_rebuilt_from_mode_and_wear_history(self):
        trace=history_quality_trace();result=check_trace(trace)
        self.assertTrue(result["valid"],result["issues"])
        trace["events"][-1]["defect_probability"]=.01
        self.assert_rejected(trace,"quality_threshold")
        trace=history_quality_trace();trace["events"][-1]["keyed_uniform"]=.5
        self.assert_rejected(trace,"quality_tape")
        trace=history_quality_trace();trace["operations"][0]["wear_before"]=69
        self.assert_rejected(trace,"machine_wear_history")

    def test_external_shocks_are_fixed_by_the_keyed_scenario(self):
        trace=simple_trace()
        trace["instance"].update(seed=0,uncertainty_stages=[dict(reveal_tick=2,outcomes=[dict(id="ok",probability=[1,1],events=[])])])
        trace["events"].append(dict(tick=2,type="reveal",outcome="ok"))
        self.assertTrue(check_trace(trace)["valid"],check_trace(trace)["issues"])
        trace["events"][-1]["outcome"]="invented"
        self.assert_rejected(trace,"exogenous_tape")
        trace["events"][-1]["outcome"]="ok"
        trace["events"].append(dict(tick=3,type="outage",machine="T1",start=3,end=4))
        self.assert_rejected(trace,"exogenous_event_count")

    def test_free_component_birth_and_unearned_repair_are_rejected(self):
        trace=simple_trace()
        unit=deepcopy(trace["instance"]["units"][0]);unit["id"]="free-housing"
        trace["events"].append(dict(tick=1,type="new_unit",unit=unit))
        self.assert_rejected(trace,"unit_birth_authorization")
        trace=simple_trace();trace["events"].append(dict(tick=8,type="repair",unit_id="h1",attempt=1))
        self.assert_rejected(trace,"repair_bound")

    def test_causality_includes_capacity_purchases_and_battery_actions(self):
        left=leased_trace();right=deepcopy(left);right["events"][-2]["tick"]=1
        self.assertFalse(check_paired_causality([left,right])["valid"])
        left=simple_trace();right=deepcopy(left);right["energy"][1]["battery_action"]="charge"
        self.assertEqual(check_paired_causality([left,right])["issues"][0]["tick"],1)

    def test_unrelated_buffer_cannot_be_used_as_a_temporary_warehouse(self):
        trace=assembly_trace()
        trace["instance"]["graph_edges"].append(dict(a="HUB_B",b="RAW_A",ticks=1))
        move=trace["moves"][0]
        move["to"]="RAW_A";move["legs"][-1]["to"]="RAW_A"
        self.assert_rejected(trace,"part_destination")

    def test_permanently_mounted_tools_cannot_be_repositioned_as_cargo(self):
        trace=simple_trace()
        trace["instance"]["tools"]=[dict(id="mounted",kind="mill",initial_location="RAW_A",life=40,portable=False)]
        trace["moves"][0].update(unit_id="mounted",entity_type="tool")
        self.assert_rejected(trace,"tool_mobility")


if __name__ == "__main__":
    unittest.main()
