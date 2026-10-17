"""Exact CP-SAT reference for a declared deterministic one-pump factory.

The complete flagship is not encoded here.  This module uses the same public
instance and trace contracts on a deliberately small, fully specified instance.
Its exactness scope and every nonbinding resource are retained in the report.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import hashlib
import heapq
import json
from pathlib import Path
import time
from typing import Any


def make_tiny(processing_scale: int = 1, horizon: int | None = None,
              automatic_attendance: bool = True, bridge_ticks: int = 4,
              input_capacity: int = 1, dispatch_after_ready: bool = False) -> dict[str, Any]:
    """One pump, seven stations, singleton furnace, one worker and one AGV.

    ``processing_scale=15`` retains the flagship's manufacturing minutes;
    ``1`` is a compact, independently checked regression fixture.
    """
    if any(type(x) is not int or x < 1 for x in (processing_scale, bridge_ticks, input_capacity)):
        raise ValueError("Scale, bridge duration and input capacity must be positive integers")
    horizon = horizon or 160 * processing_scale + 200
    if type(horizon) is not int or horizon < 1:
        raise ValueError("Positive integer horizon required")
    recipes = {
        "housing": [("T", 4), ("F", 6), ("WASH", 2), ("HEAT", 8), ("QA", 3)],
        "rotor": [("T", 4), ("HEAT", 8), ("F", 5), ("WASH", 2), ("QA", 3)],
        "flange": [("F", 4), ("S", 4), ("WASH", 2), ("QA", 3)],
        "pump": [("ASSEMBLY", 4), ("QA", 3)],
    }
    stations = [("T1", "T", "A"), ("F1", "F", "A"), ("S1", "S", "B"),
                ("WASH1", "WASH", "A"), ("H1", "HEAT", "A"), ("QA1", "QA", "A"), ("A1", "ASSEMBLY", "B")]
    powers = dict(T=9, F=12, S=10, WASH=4, HEAT=16, QA=3, ASSEMBLY=4)
    skills = dict(T="machining", F="machining", S="welding", WASH="setup", HEAT="setup", QA="qa", ASSEMBLY="assembly")
    edges = [dict(a=mid, b=f"HUB_{hall}", ticks=1) for mid, _, hall in stations]
    edges += [dict(a=node, b=f"HUB_{hall}", ticks=1) for node, hall in
              (("RAW_A", "A"), ("SHIP_B", "B"), ("CHARGE_A", "A"), ("CHARGE_B", "B"), ("SCRAP_B", "B"))]
    edges.append(dict(a="HUB_A", b="HUB_B", ticks=bridge_ticks))
    result = dict(
        schema="metaltech-stage2-instance.v1", name="Exact deterministic one-pump reference", profile="tiny-reference",
        seed=0, tick_minutes=1, horizon_ticks=horizon, day_ticks=1440, replan_ticks=60, time_scale=1,
        orders=[dict(id="P01", family="alloy_A", release_tick=0, due_tick=horizon, precision_required=False, urgent=False)],
        units=[dict(id=f"P01/{recipe}/1", order_id="P01", recipe=recipe, family="alloy_A", release_tick=0, initial_location="RAW_A")
               for recipe in ("housing", "rotor", "flange")],
        recipes={name: [dict(process=process, base_ticks=duration*processing_scale) for process, duration in route]
                 for name, route in recipes.items()},
        machines=[dict(id=mid, process=process, hall=hall, duration_factor=[1, 1],
                       input_capacity=3 if process == "ASSEMBLY" else input_capacity,
                       **({"batch_capacity": 1} if process == "HEAT" else {})) for mid, process, hall in stations],
        modes={process: {"standard": dict(duration_factor=[1, 1], power_kw=power, wear=1, defect_probability=0)}
               for process, power in powers.items()},
        setup_matrix={"alloy_A": {"alloy_A": 0}}, process_skills=skills,
        workers=[dict(id="W1", skills=sorted(set(skills.values()) | {"maintenance"}), daily_shift=[0, 1440], breaks=[], initial_hall="A")],
        worker_travel_ticks=2,
        attendance={process: dict(kind="start" if automatic_attendance and process in ("T", "F", "WASH", "HEAT") else "full",
                                  ticks=max(1, processing_scale//3)) for process in powers},
        tools=[dict(id=tid, kind=kind, initial_location=station, life=1_000_000, service_ticks=1,portable=False)
               for tid, kind, station in (("mill1", "mill", "F1"), ("weld1", "weld", "S1"), ("calibration1", "calibration", "QA1"))],
        process_tools={"F": "mill", "S": "weld", "QA": "calibration"},
        maintenance=dict(wear_limit=1_000_000, duration=1, skill="maintenance", power_kw=2, reset_family=False),
        agvs=[dict(id="AGV1", initial_location="RAW_A", initial_soc=1_000_000, capacity=1_000_000)],
        graph_edges=edges,
        transport=dict(agv_count=1, agv_payload_units=1, chargers=["CHARGE_A", "CHARGE_B"],
            load_ticks=1, unload_ticks=1, empty_soc_per_tick=1, loaded_soc_per_tick=2, charge_rate=12,
            charge_power_kw=4, charger_capacity=1, offlane_agv_capacity=4, charge_saturates=True, soc_unit_kwh=.005,
            part_routing="next_required_station_or_accepted_bom_join_or_accepted_shipping_or_scrap"),
        energy=dict(base_load_kw=12, normal_grid_cap_kw=1000, stationary_soc_unit_kwh=1/60,
            stationary_soc_capacity=40, stationary_soc_initial=40, stationary_soc_min=8, stationary_soc_terminal_min=40,
            battery_actions=[dict(id="idle", charge_kw=0, discharge_kw=0, soc_delta=0),
                            dict(id="charge", charge_kw=10, discharge_kw=0, soc_delta=9),
                            dict(id="discharge", charge_kw=0, discharge_kw=9, soc_delta=-10)],
            tariff_low=.1, tariff_peak=.1, carbon_low=.2, carbon_peak=.2, solar_peak_kw=0, no_export=True),
        quality=dict(risk_model="manufacturing_mode_history", manufacturing_defect_probabilities={p: {"standard": 0} for p in powers},
            wear_risk_coefficient=0, repair_residual_probability=0, repair_ticks=3*processing_scale,
            repair_skill="machining", repair_power_kw=8, replacement_lead_ticks=12,
            max_repairs_per_component_attempt=1, max_replacements_per_original_component=1,
            final_defect_probability=0, component_defect_probability={"standard": 0}),
        raw_stock_units={recipe: 1 for recipe in ("housing", "rotor", "flange")},
        delivery=dict(id="D1", normal_tick=horizon+1, delayed_tick=horizon+2, contents={}),
        uncertainty_stages=[], lease_options=[], investment_budget=0, certification_modes={}, feature_status={},
        reference_scope=dict(kind="deterministic parameterized instance", singleton_heat_batches=True,
            dispatch_after_source_completion=dispatch_after_ready, fixed_shortest_tree_paths=True,
            early_empty_preposition=not dispatch_after_ready,
            nonbinding=["tool life/service", "machine wear/maintenance", "AGV battery/charging", "grid cap",
                        "stationary battery", "worker shifts/breaks", "quality/rework", "exogenous disruptions", "investment"],
            binding=["recipe precedence", "machine processing and output blocking", "finite reserved input buffers",
                     "physical loaded and empty AGV travel", "one AGV", "one worker attendance and hall travel", "BOM join"],
            flagship_global_gap=None))
    return result


def shortest_path(instance: dict, origin: str, destination: str) -> list[tuple[str, str, int]]:
    graph: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for edge in instance["graph_edges"]:
        graph[edge["a"]].append((edge["b"], edge["ticks"]))
        graph[edge["b"]].append((edge["a"], edge["ticks"]))
    queue = [(0, origin, [])]
    visited = set()
    while queue:
        distance, node, path = heapq.heappop(queue)
        if node in visited:
            continue
        if node == destination:
            return path
        visited.add(node)
        for neighbor, duration in graph[node]:
            if neighbor not in visited:
                heapq.heappush(queue, (distance+duration, neighbor, path+[(node, neighbor, duration)]))
    raise ValueError(f"No physical path from {origin} to {destination}")


def activities(instance: dict) -> tuple[list[dict], list[dict]]:
    """Fixed recipe paths; these are model data, not a proposed schedule."""
    if len(instance["orders"]) != 1 or len(instance["agvs"]) != 1 or len(instance["workers"]) != 1:
        raise ValueError("Exact reference supports one order, one AGV and one worker only")
    oid = instance["orders"][0]["id"]
    machines = {}
    for machine in instance["machines"]:
        if machine["process"] in machines:
            raise ValueError("Reference requires one fixed station per process")
        machines[machine["process"]] = machine
    operations, moves = [], []
    assembly_id = f"{oid}/pump/1/op0"
    for recipe in ("housing", "rotor", "flange", "pump"):
        uid = f"{oid}/{recipe}/1"
        previous_op = None
        previous_location = "RAW_A"
        for index, step in enumerate(instance["recipes"][recipe]):
            machine = machines[step["process"]]
            op_id = f"{uid}/op{index}"
            operations.append(dict(id=op_id, unit_id=uid, recipe=recipe, recipe_step=index,
                machine_id=machine["id"], process=step["process"], duration=step["base_ticks"], hall=machine["hall"]))
            if recipe != "pump" or index:
                moves.append(dict(id=f"move{len(moves)}", unit_id=uid, source_op=previous_op, target_op=op_id,
                                  **{"from":previous_location, "to":machine["id"]}))
            previous_op, previous_location = op_id, machine["id"]
        moves.append(dict(id=f"move{len(moves)}", unit_id=uid, source_op=previous_op,
                          target_op=None if recipe == "pump" else assembly_id,
                          **{"from":previous_location, "to":"SHIP_B" if recipe == "pump" else machines["ASSEMBLY"]["id"]}))
    return operations, moves


def validate_scope(instance: dict) -> None:
    """Reject changed parameters that would invalidate omitted constraints.

    An exact reference must not silently become an optimistic relaxation when a
    caller makes energy, quality, tooling or calendars binding.
    """
    operations, movements = activities(instance)
    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ValueError("Outside exact tiny scope: " + message)
    require(instance.get("reference_scope",{}).get("kind")=="deterministic parameterized instance", "undeclared reference scope")
    expected_routes={"housing":["T","F","WASH","HEAT","QA"],"rotor":["T","HEAT","F","WASH","QA"],
                     "flange":["F","S","WASH","QA"],"pump":["ASSEMBLY","QA"]}
    require({recipe:[step["process"] for step in route] for recipe,route in instance["recipes"].items()}==expected_routes,
            "changed process routes")
    require(all(type(op["duration"]) is int and op["duration"]>0 for op in operations), "nonpositive/noninteger processing duration")
    order=instance["orders"][0];worker=instance["workers"][0];agv=instance["agvs"][0]
    require(order["release_tick"]==0 and order["due_tick"]>=instance["horizon_ticks"] and not order.get("precision_required"), "order release/deadline/certification")
    require(len(instance["units"])==3 and {u["recipe"] for u in instance["units"]}=={"housing","rotor","flange"}, "one component per BOM type")
    require(all(u["initial_location"]=="RAW_A" and u["release_tick"]==0 and u["family"]=="alloy_A" for u in instance["units"]), "initial WIP or multiple families")
    require(instance["setup_matrix"]=={"alloy_A":{"alloy_A":0}}, "nonzero family setup")
    require(all(set(modes)=={"standard"} and modes["standard"]["duration_factor"]==[1,1] and modes["standard"]["wear"]==1 for modes in instance["modes"].values()), "alternative modes or duration/wear multipliers")
    require(all(m["duration_factor"]==[1,1] and m.get("initial_wear",0)==0 and m.get("initial_family") is None for m in instance["machines"]), "machine speed/warm start")
    require(all(m.get("batch_capacity",1)==1 for m in instance["machines"] if m["process"]=="HEAT"), "multi-member heat batches")
    require(all(m["input_capacity"]>=1 for m in instance["machines"]), "missing input capacity")
    require(next(m for m in instance["machines"] if m["process"]=="ASSEMBLY")["input_capacity"]>=3, "BOM cannot fit assembly input")
    require(instance["maintenance"]["wear_limit"]>=sum(op["duration"] for op in operations), "binding machine wear")
    required_skills=set(instance["process_skills"].values())
    require(required_skills<=set(worker["skills"]) and worker["daily_shift"]==[0,instance["day_ticks"]] and not worker.get("breaks"), "worker skill/calendar restrictions")
    for op in operations:
        kind=instance["process_tools"].get(op["process"])
        if not kind:continue
        matches=[tool for tool in instance["tools"] if tool["kind"]==kind]
        workload=sum(other["duration"] for other in operations if instance["process_tools"].get(other["process"])==kind)
        require(len(matches)==1 and matches[0]["initial_location"]==op["machine_id"] and matches[0]["life"]>=workload, "binding or nonmounted tool")
    quality=instance["quality"]
    require(quality.get("risk_model")=="manufacturing_mode_history" and quality["wear_risk_coefficient"]==0 and all(probability==0 for modes in quality["manufacturing_defect_probabilities"].values() for probability in modes.values()), "nonzero quality risk")
    require(not instance["uncertainty_stages"] and not instance["lease_options"], "hidden events or investment options")
    require(all(instance["raw_stock_units"].get(recipe,0)>=1 for recipe in ("housing","rotor","flange")), "insufficient raw stock")
    require(instance["delivery"]["normal_tick"]>instance["horizon_ticks"], "in-horizon material delivery")
    e=instance["energy"]
    require(e["solar_peak_kw"]==0 and e["tariff_low"]==e["tariff_peak"] and e["tariff_low"]>0 and e["carbon_low"]==e["carbon_peak"], "variable energy/carbon profile")
    require(e["stationary_soc_initial"]==e["stationary_soc_capacity"]==e["stationary_soc_terminal_min"], "free terminal stationary-battery draw")
    require(e["battery_actions"]==[dict(id="idle",charge_kw=0,discharge_kw=0,soc_delta=0),
                                 dict(id="charge",charge_kw=10,discharge_kw=0,soc_delta=9),
                                 dict(id="discharge",charge_kw=0,discharge_kw=9,soc_delta=-10)], "changed battery conversion law")
    require(e["normal_grid_cap_kw"]>=e["base_load_kw"]+sum(modes["standard"]["power_kw"] for modes in instance["modes"].values()), "binding electrical cap")
    nodes={edge[key] for edge in instance["graph_edges"] for key in ("a","b")}
    require(len(instance["graph_edges"])==len(nodes)-1 and all(edge["ticks"]>0 for edge in instance["graph_edges"]), "transport graph must be a positive tree")
    distances=[sum(d for _,_,d in shortest_path(instance,a,b)) for a in nodes for b in nodes]
    loaded=sum(sum(d for _,_,d in shortest_path(instance,m["from"],m["to"])) for m in movements)
    require(agv["initial_soc"]>=2*loaded+len(movements)*max(distances) and agv["capacity"]>=agv["initial_soc"], "binding AGV battery")
    require(instance["transport"]["offlane_agv_capacity"]>=1 and instance["transport"]["agv_payload_units"]==1, "holding/payload rule")
    require(instance["transport"].get("part_routing")=="next_required_station_or_accepted_bom_join_or_accepted_shipping_or_scrap", "arbitrary temporary WIP warehousing")
    require(all(tool.get("portable") is False for tool in instance["tools"]), "optional tool-transfer preposition actions")


def full_attendance_lower_bound(instance: dict) -> dict[str, Any]:
    """Independent resource/critical-join bound; no CP variables are used.

    The only worker must perform all processing.  Its welding round trip occurs
    before final component acceptance.  Two later, unavoidable loaded transfers
    leave no other processing available, so those join gaps cannot overlap any
    of that worker's processing minutes.
    """
    validate_scope(instance)
    if any(rule["kind"]!="full" for rule in instance["attendance"].values()):
        raise ValueError("Analytic bound requires full attendance at every operation")
    stations={machine["process"]:machine for machine in instance["machines"]}
    if any(stations[p]["hall"]!="A" for p in ("T","F","WASH","HEAT","QA")) or any(stations[p]["hall"]!="B" for p in ("S","ASSEMBLY")) or instance["workers"][0]["initial_hall"]!="A":
        raise ValueError("Analytic bound requires the declared two-hall reference layout")
    handling=instance["transport"]["load_ticks"]+instance["transport"]["unload_ticks"]
    loaded=lambda a,b:sum(d for _,_,d in shortest_path(instance,a,b))+handling
    processing=sum(step["base_ticks"] for recipe in instance["recipes"].values() for step in recipe)
    pieces=dict(processing_ticks=processing,
        first_material_delivery=min(loaded("RAW_A",stations[instance["recipes"][r][0]["process"]]["id"]) for r in ("housing","rotor","flange")),
        last_component_to_assembly=loaded(stations["QA"]["id"],stations["ASSEMBLY"]["id"]),
        assembly_to_final_inspection=loaded(stations["ASSEMBLY"]["id"],stations["QA"]["id"]),
        final_shipping=loaded(stations["QA"]["id"],"SHIP_B"),
        earlier_welding_worker_round_trip=2*instance["worker_travel_ticks"])
    return dict(lower_bound_ticks=sum(pieces.values()),components=pieces,
                assumptions="One fully attending worker; initial hall A; welding/assembly in B; other stations in A; direct required transfers")


def solve(instance: dict, deterministic_limit: float = 30, wall_limit: float = 60,
          seed: int = 0) -> dict:
    """Optimize the complete declared tiny instance, retaining proof status/bound."""
    import ortools
    from ortools.sat.python import cp_model
    from .check import check_trace

    started = time.perf_counter()
    validate_scope(instance)
    operations, movements = activities(instance)
    horizon = instance["horizon_ticks"]
    model = cp_model.CpModel()
    op_start, op_end, attended_end = {}, {}, {}
    for op in operations:
        name, duration = op["id"], op["duration"]
        op_start[name] = model.new_int_var(0, horizon-duration, f"start:{name}")
        op_end[name] = model.new_int_var(duration, horizon, f"end:{name}")
        model.add(op_end[name] == op_start[name] + duration)
        rule = instance["attendance"][op["process"]]
        attendance = duration if rule["kind"] == "full" else min(duration, rule["ticks"])
        attended_end[name] = op_start[name] + attendance
    dispatch, pickup, drop = {}, {}, {}
    incoming, outgoing = defaultdict(list), {}
    distance = lambda a,b: sum(d for _,_,d in shortest_path(instance,a,b))
    for move in movements:
        name = move["id"]
        dispatch[name] = model.new_int_var(0, horizon, f"dispatch:{name}")
        pickup[name] = model.new_int_var(0, horizon, f"pickup:{name}")
        drop[name] = model.new_int_var(0, horizon, f"drop:{name}")
        model.add(drop[name] == pickup[name] + instance["transport"]["load_ticks"] + distance(move["from"],move["to"]) + instance["transport"]["unload_ticks"])
        if move["source_op"]:
            if instance["reference_scope"].get("dispatch_after_source_completion"):
                model.add(dispatch[name] >= op_end[move["source_op"]])
            model.add(pickup[name] >= op_end[move["source_op"]])
            outgoing[move["source_op"]] = name
        if move["target_op"]:
            model.add(drop[name] <= op_start[move["target_op"]])
            incoming[move["target_op"]].append(name)
    machine_intervals, input_intervals = defaultdict(list), defaultdict(list)
    worker_intervals = []
    machine_table = {m["id"]: m for m in instance["machines"]}
    for op in operations:
        name, machine = op["id"], op["machine_id"]
        output_release = pickup[outgoing[name]]
        model.add(output_release >= op_end[name])
        span = model.new_int_var(op["duration"], horizon, f"occupied_size:{name}")
        model.add(span == output_release-op_start[name])
        machine_intervals[machine].append(model.new_interval_var(op_start[name], span, output_release, f"machine:{name}"))
        rule = instance["attendance"][op["process"]]
        amount = op["duration"] if rule["kind"] == "full" else min(op["duration"],rule["ticks"])
        worker_intervals.append(model.new_interval_var(op_start[name],amount,attended_end[name],f"worker:{name}"))
        for move_id in incoming[name]:
            size = model.new_int_var(0,horizon,f"buffer_size:{move_id}")
            model.add(size == op_start[name]-dispatch[move_id])
            input_intervals[machine].append(model.new_interval_var(dispatch[move_id],size,op_start[name],f"buffer:{move_id}"))
    for rows in machine_intervals.values():
        model.add_no_overlap(rows)
    for machine, rows in input_intervals.items():
        model.add_cumulative(rows,[1]*len(rows),machine_table[machine]["input_capacity"])
    model.add_no_overlap(worker_intervals)

    # A Hamiltonian circuit through a dummy node is a path through all mandatory
    # deliveries.  No return-to-depot travel is required at the end of the day.
    agv_arcs = []
    selected_agv_arcs = {}
    for a in range(len(movements)+1):
        for b in range(len(movements)+1):
            if a == b:
                continue
            literal = model.new_bool_var(f"agv_arc:{a}:{b}")
            agv_arcs.append((a,b,literal));selected_agv_arcs[a,b]=literal
            if b:
                current = movements[b-1];mid=current["id"]
                prior_location = instance["agvs"][0]["initial_location"] if not a else movements[a-1]["to"]
                if a:
                    model.add(dispatch[mid] >= drop[movements[a-1]["id"]]).only_enforce_if(literal)
                model.add(pickup[mid] >= dispatch[mid] + distance(prior_location,current["from"])).only_enforce_if(literal)
    model.add_circuit(agv_arcs)

    worker_arcs = [];selected_worker_arcs={}
    for a in range(len(operations)+1):
        for b in range(len(operations)+1):
            if a == b:
                continue
            literal = model.new_bool_var(f"worker_arc:{a}:{b}")
            worker_arcs.append((a,b,literal));selected_worker_arcs[a,b]=literal
            if b:
                current=operations[b-1];prior_hall=instance["workers"][0]["initial_hall"] if not a else operations[a-1]["hall"]
                travel = instance["worker_travel_ticks"] if prior_hall != current["hall"] else 0
                model.add(op_start[current["id"]] >= (0 if not a else attended_end[operations[a-1]["id"]]) + travel).only_enforce_if(literal)
    model.add_circuit(worker_arcs)
    shipping = next(move for move in movements if move["to"] == "SHIP_B")
    model.minimize(drop[shipping["id"]])
    error = model.validate()
    if error:
        raise ValueError(error)
    solver = cp_model.CpSolver()
    solver.parameters.max_deterministic_time = deterministic_limit
    solver.parameters.max_time_in_seconds = wall_limit
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = seed
    status = solver.solve(model)
    result = dict(schema="metaltech-stage2-tiny-reference.v1", solver="OR-Tools CP-SAT", solver_version=ortools.__version__,
        status=solver.status_name(status), optimal=status == cp_model.OPTIMAL,
        best_bound_ticks=solver.best_objective_bound, objective_ticks=None,
        deterministic_limit=deterministic_limit, wall_limit_seconds=wall_limit, search_workers=1, seed=seed,
        build_and_solve_seconds=time.perf_counter()-started, solver_wall_seconds=solver.wall_time,
        solver_response=solver.response_stats(), model_stats=model.model_stats(),
        counts=dict(operations=len(operations), moves=len(movements), machines=len(instance["machines"])),
        scope=deepcopy(instance["reference_scope"]), flagship_global_gap=None,
        optimality_scope="Minimum-grid-cost, all-fulfilled schedules of the declared direct-transfer deterministic tiny instance",
        global_infeasibility_proven=False)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return result
    schedule = dict(operations={op["id"]:solver.value(op_start[op["id"]]) for op in operations},
        moves={m["id"]:dict(start=solver.value(dispatch[m["id"]]),pickup=solver.value(pickup[m["id"]]),drop=solver.value(drop[m["id"]])) for m in movements},
        agv_successors={a:b for (a,b),literal in selected_agv_arcs.items() if solver.value(literal)},
        worker_successors={a:b for (a,b),literal in selected_worker_arcs.items() if solver.value(literal)})
    trace = to_trace(instance,operations,movements,schedule)
    validation = check_trace(trace)
    result.update(objective_ticks=solver.value(drop[shipping["id"]]),trace=trace,validation=validation)
    if not validation["valid"] or not validation["all_orders_fulfilled"]:
        result["status"]="INVALID_EXPORTED_SOLUTION";result["optimal"]=False
    return result


def to_trace(instance: dict, operations: list[dict], movements: list[dict], schedule: dict) -> dict:
    """Expand interval variables into independently checkable physical events."""
    trace = dict(schema="metaltech-stage2-trace.v1",run_id="tiny-cp-reference",tick_minutes=instance["tick_minutes"],
        horizon_ticks=instance["horizon_ticks"],instance=deepcopy(instance),
        resources={k:deepcopy(instance[k]) for k in ("machines","workers","tools","agvs")},
        provenance=dict(kind="measured",solver="OR-Tools CP-SAT tiny exact reference"),operations=[],moves=[],worker_moves=[],events=[],energy=[],metrics={})
    oid=instance["orders"][0]["id"];wid=instance["workers"][0]["id"]
    for unit in instance["units"]:
        trace["events"].append(dict(tick=unit["release_tick"],type="release",unit_id=unit["id"],recipe=unit["recipe"]))
    wear=defaultdict(float)
    for op in sorted(operations,key=lambda x:(schedule["operations"][x["id"]],x["id"])):
        start=schedule["operations"][op["id"]];end=start+op["duration"]
        rule=instance["attendance"][op["process"]];attend=op["duration"] if rule["kind"]=="full" else min(op["duration"],rule["ticks"])
        tools=[t["id"] for t in instance["tools"] if t["kind"]==instance["process_tools"].get(op["process"])]
        parents=[u["id"] for u in instance["units"]] if op["process"]=="ASSEMBLY" else []
        trace["operations"].append(dict(id=op["id"],unit_ids=[op["unit_id"]],unit_id=op["unit_id"],order_id=oid,
            process=op["process"],machine_id=op["machine_id"],start=start,end=end,mode="standard",worker_ids=[wid],tool_ids=tools,
            worker_intervals=[dict(worker_id=wid,start=start,end=start+attend,role="process",skills=[instance["process_skills"][op["process"]]])],
            worker_roles={wid:[instance["process_skills"][op["process"]]]},parent_unit_ids=parents,setup_ticks=0,
            processing_ticks=op["duration"],power_kw=instance["modes"][op["process"]]["standard"]["power_kw"],
            family="alloy_A",kind="process",recipe_step=op["recipe_step"],recipe_steps={op["unit_id"]:op["recipe_step"]},
            attempt=0,is_rework=False,repair_step=None,wear_before=wear[op["machine_id"]]))
        wear[op["machine_id"]]+=op["duration"]
        trace["events"].append(dict(tick=end,type="process_complete",unit_id=op["unit_id"],operation_id=op["id"]))
        if parents:
            trace["events"] += [dict(tick=start,type="consume",unit_id=uid,parent_operation=op["id"],order_id=oid) for uid in parents]
        if op["process"]=="QA":
            raw=hashlib.sha256(f'{instance["seed"]}:quality:{op["unit_id"]}:0'.encode()).digest()
            draw=int.from_bytes(raw[:8],"big")/2**64
            trace["events"].append(dict(tick=end,type="qa_result",unit_id=op["unit_id"],operation_id=op["id"],passed=True,keyed_uniform=draw,defect_probability=0))
    location=instance["agvs"][0]["initial_location"];soc=instance["agvs"][0]["initial_soc"]
    successor=schedule["agv_successors"];index=successor[0]
    while index:
        move=movements[index-1];times=schedule["moves"][move["id"]];legs=[];tick=times["start"]
        for origin,dest,duration in shortest_path(instance,location,move["from"]):
            legs.append(dict(**{"from":origin,"to":dest},start=tick,end=tick+duration,loaded=False));tick+=duration
        tick=times["pickup"]+instance["transport"]["load_ticks"]
        for origin,dest,duration in shortest_path(instance,move["from"],move["to"]):
            legs.append(dict(**{"from":origin,"to":dest},start=tick,end=tick+duration,loaded=True));tick+=duration
        cost=sum((leg["end"]-leg["start"])*(2 if leg["loaded"] else 1) for leg in legs)
        trace["moves"].append(dict(id=move["id"],unit_id=move["unit_id"],entity_type="part",agv_id=instance["agvs"][0]["id"],
            start=times["start"],pickup_tick=times["pickup"],drop_tick=times["drop"],end=times["drop"],
            **{"from":move["from"],"to":move["to"]},legs=legs,soc_before=soc,soc_after=soc-cost,kind="transport"))
        soc-=cost;location=move["to"]
        if location=="SHIP_B":trace["events"].append(dict(tick=times["drop"],type="ship",unit_id=move["unit_id"],order_id=oid))
        index=successor[index]
    hall=instance["workers"][0]["initial_hall"];successor=schedule["worker_successors"];index=successor[0]
    while index:
        op=operations[index-1]
        if hall!=op["hall"]:
            end=schedule["operations"][op["id"]]
            trace["worker_moves"].append(dict(worker_id=wid,start=end-instance["worker_travel_ticks"],end=end,from_hall=hall,to_hall=op["hall"]))
        hall=op["hall"];index=successor[index]
    e=instance["energy"]
    for tick in range(instance["horizon_ticks"]):
        load=e["base_load_kw"]+sum(op["power_kw"] for op in trace["operations"] if op["start"]<=tick<op["end"])
        trace["energy"].append(dict(tick=tick,load_kw=load,grid_kw=load,cap_kw=e["normal_grid_cap_kw"],solar_kw=0,curtailed_kw=0,
            soc_before=e["stationary_soc_initial"],soc=e["stationary_soc_initial"],battery_action="idle",tariff=e["tariff_low"],carbon_intensity=e["carbon_low"]))
    trace["events"].sort(key=lambda event:event["tick"])
    return trace


def compare(instance: dict, **solve_kwargs: Any) -> dict:
    from .engine import run
    from .check import check_trace
    root=Path(__file__).resolve().parents[1]
    source_names=("stage2/reference.py","stage2/check.py","stage2/engine.py")
    source_before={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in source_names}
    exact=solve(instance,**solve_kwargs)
    heuristic=run(deepcopy(instance),dict(wip_limit=1,mode="standard"))
    validation=check_trace(heuristic)
    delivered=validation["metrics"]["delivery_ticks"].get(instance["orders"][0]["id"])
    gap=None
    earlier_tiers_match=(validation["valid"] and validation["all_orders_fulfilled"] and validation["terminal_requirements_met"] and
                         abs(validation["metrics"]["total_cost"]-exact.get("validation",{}).get("metrics",{}).get("total_cost",float("inf")))<1e-5)
    if exact["optimal"] and earlier_tiers_match:
        gap=(delivered-exact["objective_ticks"])/exact["objective_ticks"]
    canonical=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    instance_hash=canonical(instance)
    source_after={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in source_names}
    return dict(exact=exact,heuristic_trace=heuristic,heuristic_validation=validation,
        provenance=dict(instance_sha256=instance_hash,source_sha256=source_before,sources_stable_during_run=source_before==source_after),
        comparison=dict(same_canonical_instance=instance_hash==canonical(heuristic["instance"]),same_earlier_objective_tiers=earlier_tiers_match,
            cp_status=exact["status"],heuristic_makespan_ticks=delivered,
            optimum_makespan_ticks=exact["objective_ticks"] if exact["optimal"] else None,
            heuristic_makespan_gap=gap,flagship_global_gap=None))


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processing-scale",type=int,default=15)
    parser.add_argument("--full-attendance",action="store_true")
    parser.add_argument("--bridge-ticks",type=int,default=4)
    parser.add_argument("--input-capacity",type=int,default=1)
    parser.add_argument("--dispatch-after-ready",action="store_true",help="Restrict AGV dispatch to completed source operations (heuristic action-domain ablation)")
    parser.add_argument("--deterministic-limit",type=float,default=30)
    parser.add_argument("--wall-limit",type=float,default=60)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    instance=make_tiny(args.processing_scale,automatic_attendance=not args.full_attendance,
                       bridge_ticks=args.bridge_ticks,input_capacity=args.input_capacity,dispatch_after_ready=args.dispatch_after_ready)
    result=compare(instance,deterministic_limit=args.deterministic_limit,wall_limit=args.wall_limit)
    if args.output:
        args.output.mkdir(parents=True,exist_ok=True)
        artifacts={"instance.json":instance,"heuristic-trace.json":result.pop("heuristic_trace")}
        if "trace" in result["exact"]:artifacts["optimal-trace.json"]=result["exact"].pop("trace")
        for name,value in artifacts.items():
            (args.output/name).write_text(json.dumps(value,indent=2)+"\n")
        result["artifacts_sha256"]={name:hashlib.sha256((args.output/name).read_bytes()).hexdigest() for name in artifacts}
        (args.output/"report.json").write_text(json.dumps(result,indent=2)+"\n")
    display={k:v for k,v in result.items() if k!="heuristic_trace"}
    display["exact"]={k:v for k,v in result["exact"].items() if k!="trace"}
    print(json.dumps(display,indent=2))
    return 0 if result["exact"].get("optimal") and result["exact"].get("validation",{}).get("valid") else 1


if __name__=="__main__":raise SystemExit(main())
