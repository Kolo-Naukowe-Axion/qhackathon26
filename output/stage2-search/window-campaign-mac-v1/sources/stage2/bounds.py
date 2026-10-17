"""Necessary resource bounds for the nominal Stage 2 factory (stdlib only).

These certificates relax setups, maintenance, quality failures, disruptions,
empty repositioning and temporal conflicts. They never use a greedy route as
a lower bound. The transport DP minimizes over all process-machine choices,
with the same assembly machine shared by its component streams.

Run: python3 -m stage2.bounds --orders 24 --profile full
Original coarse model: python3 -m stage2.bounds --profile coarse --horizon 384
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from fractions import Fraction
import hashlib
from heapq import heappop, heappush
from itertools import combinations
import json
from math import ceil
from pathlib import Path
from typing import Callable


def _ceil(value: Fraction | int) -> int:
    return ceil(value)


def _scalar(value: Fraction | int) -> int | float:
    value = Fraction(value)
    return value.numerator if value.denominator == 1 else float(value)


def _duration(instance: dict, process: str, base: int, machine: dict, mode: dict) -> int:
    """Independently reconstruct tabulated integer duration, without engine code."""
    a, b = mode["duration_factor"]
    c, d = machine["duration_factor"]
    return _ceil(Fraction(base * a * c, b * d))


def _modes(instance: dict, order: dict, process: str) -> list[dict]:
    modes = instance["modes"][process]
    allowed = instance.get("certification_modes", {}).get("precision", {}).get(process) if order.get("precision_required") else None
    names = list(modes) if allowed is None else allowed
    if not names or any(name not in modes for name in names):
        raise ValueError(f"Missing/invalid certified modes for {order['id']} {process}")
    return [modes[name] for name in names]


def worker_available(worker: dict, horizon: int, period: int) -> int:
    """Total calendar capacity, relaxing task indivisibility and hall travel."""
    start, end = worker["daily_shift"]
    daily = [start <= t < end and not any(a <= t < z for a, z in worker.get("breaks", []))
             for t in range(period)]
    days, tail = divmod(horizon, period)
    return days * sum(daily) + sum(daily[:tail])


def attended_server_capacity(instance: dict, skills: set[str], servers: int, horizon: int) -> int:
    """Upper bound for servers needing one worker from a union of skill pools.

    A service worker and a processing worker need not have the same skill.
    Using their *union* avoids adding idle intervals already usable for service.
    """
    period = 24 * 60 // instance["tick_minutes"]
    daily = []
    for t in range(period):
        workers = sum(bool(skills.intersection(w["skills"])) and
                      w["daily_shift"][0] <= t < w["daily_shift"][1] and
                      not any(a <= t < z for a, z in w.get("breaks", []))
                      for w in instance["workers"])
        daily.append(min(servers, workers))
    days, tail = divmod(horizon, period)
    return days * sum(daily) + sum(daily[:tail])


def shortest_costs(instance: dict, edge_cost: Callable[[dict], int]) -> dict:
    """All-pairs nonnegative shortest paths for the selected relaxed objective."""
    graph = defaultdict(list)
    for edge in instance["graph_edges"]:
        cost = edge_cost(edge)
        if cost < 0 or edge["ticks"] <= 0:
            raise ValueError("Travel durations must be positive and objective costs nonnegative")
        graph[edge["a"]].append((edge["b"], cost))
        graph[edge["b"]].append((edge["a"], cost))
    result = {}
    for source in graph:
        distance = {source: 0}
        queue = [(0, source)]
        while queue:
            cost, at = heappop(queue)
            if cost != distance[at]:
                continue
            for dest, weight in graph[at]:
                candidate = cost + weight
                if candidate < distance.get(dest, float("inf")):
                    distance[dest] = candidate
                    heappush(queue, (candidate, dest))
        result[source] = distance
    return result


def _chain(instance: dict, source: str, recipe: list, cost: Callable[[str, str], int],
           endpoint: str) -> tuple[int, list[str]]:
    """Exact shortest layered path through eligible machine sets."""
    states = {source: (0, [source])}
    for step in recipe:
        eligible = sorted(m["id"] for m in instance["machines"] if m["process"] == step["process"])
        if not eligible:
            raise ValueError(f"No eligible machine for {step['process']}")
        states = {dest: min((value + cost(at, dest), path + [dest])
                            for at, (value, path) in states.items()) for dest in eligible}
    return min((value + cost(at, endpoint), path + [endpoint])
               for at, (value, path) in states.items())


def transport_minimum(instance: dict, cost: Callable[[str, str], int], shipping="SHIP_B") -> dict:
    """Minimize every order's DAG at its shared assembly join, independently.

    Relaxing all interactions between orders can only reduce required resource
    use. Every component still ends at the very same assembler for that order.
    """
    pump_recipe = instance["recipes"]["pump"]
    if not pump_recipe or pump_recipe[0]["process"] != "ASSEMBLY":
        raise ValueError("Bounds expect a pump recipe starting with ASSEMBLY")
    assemblers = sorted(m["id"] for m in instance["machines"] if m["process"] == "ASSEMBLY")
    if not assemblers:
        raise ValueError("No assembly machine")
    units = defaultdict(list)
    for unit in instance["units"]:
        if unit["recipe"] != "pump":
            units[unit["order_id"]].append(unit)
    per_order = []
    for order in instance["orders"]:
        components = units[order["id"]]
        if sorted(u["recipe"] for u in components) != ["flange", "housing", "rotor"]:
            raise ValueError("Nominal bounds require exactly one housing, rotor and flange per order")
        choices = []
        for assembler in assemblers:
            paths = []
            total = 0
            for unit in sorted(components, key=lambda u: u["id"]):
                value, path = _chain(instance, unit["initial_location"],
                                     instance["recipes"][unit["recipe"]], cost, assembler)
                total += value
                paths.append(dict(unit_id=unit["id"], cost=value, route=path))
            value, path = _chain(instance, assembler, pump_recipe[1:], cost, shipping)
            total += value
            paths.append(dict(unit_id=f'{order["id"]}/pump', cost=value, route=path))
            choices.append((total, assembler, paths))
        value, assembler, paths = min(choices)
        per_order.append(dict(order_id=order["id"], minimum=value, assembly_machine=assembler,
                              relaxed_witness_paths=paths))
    return dict(minimum=sum(row["minimum"] for row in per_order), per_order=per_order)


def labor_and_tools(instance: dict) -> dict:
    """Minimum processing occupancy with ideal batches and zero setups.

    For batch process p of capacity B, each actual batch duration d is at least
    every member's independently minimized duration; hence B*d >= sum minima.
    Grouping by family is valid for the declared same-family heat batches.
    """
    orders = {o["id"]: o for o in instance["orders"]}
    groups = defaultdict(Fraction)
    attendance_groups = defaultdict(Fraction)
    counts = defaultdict(int)
    for unit in instance["units"]:
        if unit["recipe"] == "pump":
            continue
        family = unit.get("family", orders[unit["order_id"]].get("family", ""))
        for step in instance["recipes"][unit["recipe"]]:
            p = step["process"]
            eligible = [m for m in instance["machines"] if m["process"] == p]
            minimum = min(_duration(instance, p, step["base_ticks"], m, mode)
                          for m in eligible for mode in _modes(instance, orders[unit["order_id"]], p))
            batch = max(m.get("batch_capacity", 1) for m in eligible)
            key = (p, family if batch > 1 else "")
            groups[key] += Fraction(minimum, batch)
            attendance = instance.get("attendance", {}).get(p, {"kind": "full"})
            attended = minimum if attendance["kind"] == "full" else min(minimum, attendance["ticks"])
            attendance_groups[key] += Fraction(attended, batch)
            counts[p] += 1
    for order in instance["orders"]:
        for step in instance["recipes"]["pump"]:
            p = step["process"]
            eligible = [m for m in instance["machines"] if m["process"] == p]
            minimum = min(_duration(instance, p, step["base_ticks"], m, mode)
                          for m in eligible for mode in _modes(instance, order, p))
            # No batching on assembly or final QA in this schema.
            groups[(p, "")] += minimum
            attendance = instance.get("attendance", {}).get(p, {"kind": "full"})
            attended = minimum if attendance["kind"] == "full" else min(minimum, attendance["ticks"])
            attendance_groups[(p, "")] += attended
            counts[p] += 1
    processing = defaultdict(int)
    for (process, _family), work in groups.items():
        processing[process] += _ceil(work)
    attended_work = defaultdict(int)
    for (process, _family), work in attendance_groups.items():
        attended_work[process] += _ceil(work)
    skill_work = defaultdict(int)
    for process, work in attended_work.items():
        skill_work[instance["process_skills"][process]] += work
    horizon = instance["horizon_ticks"]
    period = 24 * 60 // instance["tick_minutes"]
    capacity = {w["id"]: worker_available(w, horizon, period) for w in instance["workers"]}
    # Hall-type conditions characterize the fractional assignment relaxation:
    # demand(S) <= capacity(all workers eligible for at least one skill in S).
    skills = sorted(skill_work)
    cuts = []
    for size in range(1, len(skills) + 1):
        for chosen in combinations(skills, size):
            eligible = [w["id"] for w in instance["workers"] if set(chosen).intersection(w["skills"])]
            demand = sum(skill_work[skill] for skill in chosen)
            available = sum(capacity[worker] for worker in eligible)
            cuts.append(dict(skills=list(chosen), required_ticks=demand, available_ticks=available,
                             deficit_ticks=max(0, demand - available), workers=eligible))
    tools = []
    service_labor = 0
    for kind in sorted({tool["kind"] for tool in instance["tools"]}):
        pool = [tool for tool in instance["tools"] if tool["kind"] == kind]
        work = sum(processing[p] for p, tool_kind in instance["process_tools"].items() if tool_kind == kind)
        initial_life = sum(tool["life"] for tool in pool)
        max_life = max(tool["life"] for tool in pool)
        services = _ceil(Fraction(max(0, work - initial_life), max_life))
        service_ticks = services * min(tool["service_ticks"] for tool in pool)
        service_labor += service_ticks
        processes = [p for p, tool_kind in instance["process_tools"].items() if tool_kind == kind]
        fully_attended = all(instance.get("attendance", {}).get(p, {"kind": "full"})["kind"] == "full"
                             for p in processes)
        skills = {instance["process_skills"][p] for p in processes} | {"setup"}
        physical_capacity = len(pool) * horizon
        calendar_capacity = attended_server_capacity(instance, skills, len(pool), horizon) if fully_attended else physical_capacity
        tools.append(dict(kind=kind, count=len(pool), minimum_processing_ticks=work,
                          minimum_services=services, minimum_service_ticks=service_ticks,
                          minimum_total_tool_ticks=work + service_ticks,
                          available_tool_ticks=physical_capacity,
                          full_attendance_calendar_applies=fully_attended,
                          processing_or_service_skills=sorted(skills),
                          available_tool_ticks_with_required_worker=calendar_capacity,
                          minimum_forced_idle_tool_ticks=physical_capacity-calendar_capacity,
                          effective_capacity_ticks=min(physical_capacity, calendar_capacity),
                          deficit_ticks=max(0, work + service_ticks - min(physical_capacity, calendar_capacity))))
    total = sum(attended_work.values())
    full_total = sum(processing.values())
    return dict(assumption="Declared per-process attendance table; ideal batching; zero setups and worker travel",
                process_operations=dict(sorted(counts.items())), processing_ticks=dict(sorted(processing.items())),
                machine_capacity_bounds=[dict(process=p, minimum_processing_ticks=work,
                    available_machine_ticks=horizon * sum(m["process"] == p for m in instance["machines"]))
                    for p, work in sorted(processing.items())],
                declared_attendance_ticks=dict(sorted(attended_work.items())),
                fully_attended_counterfactual_worker_ticks=full_total,
                fully_attended_counterfactual_deficit_ticks=max(0, full_total - sum(capacity.values())),
                total_processing_worker_ticks=total, skill_processing_ticks=dict(sorted(skill_work.items())),
                worker_available_ticks=capacity, total_available_worker_ticks=sum(capacity.values()),
                processing_deficit_ticks=max(0, total - sum(capacity.values())),
                minimum_tool_service_worker_ticks=service_labor,
                total_worker_ticks_including_necessary_tool_service=total + service_labor,
                skill_cuts=cuts, violated_skill_cuts=[cut for cut in cuts if cut["deficit_ticks"]], tools=tools)


def analyze(instance: dict) -> dict:
    horizon = instance["horizon_ticks"]
    handling = instance["transport"]["load_ticks"] + instance["transport"]["unload_ticks"]
    if instance["transport"].get("agv_payload_units", 1) != 1:
        raise ValueError("This certificate requires payload-one AGVs; multi-part batching needs another relaxation")
    distances = shortest_costs(instance, lambda edge: edge["ticks"])
    travel = transport_minimum(instance, lambda a, b: distances[a][b])
    moves = transport_minimum(instance, lambda a, b: int(a != b))
    occupied = transport_minimum(instance, lambda a, b: 0 if a == b else distances[a][b] + handling)
    machines = {m["id"]: m for m in instance["machines"]}

    def hall(node):
        return machines[node]["hall"] if node in machines else node.rsplit("_", 1)[-1] if "_" in node else None

    interhall = [edge for edge in instance["graph_edges"] if hall(edge["a"]) and hall(edge["b"])
                 and hall(edge["a"]) != hall(edge["b"])]
    crossing_set = {frozenset((edge["a"], edge["b"])) for edge in interhall}
    crossing_distances = shortest_costs(instance, lambda edge: int(frozenset((edge["a"], edge["b"])) in crossing_set))
    crossings = transport_minimum(instance, lambda a, b: crossing_distances[a][b])
    bridge_bounds = []
    for edge in interhall:
        key = frozenset((edge["a"], edge["b"]))
        individual = shortest_costs(instance, lambda item: int(frozenset((item["a"], item["b"])) == key))
        count = transport_minimum(instance, lambda a, b: individual[a][b])["minimum"]
        bridge_bounds.append(dict(edge=[edge["a"], edge["b"]], minimum_loaded_crossings=count,
                                  minimum_occupied_ticks=count * edge["ticks"], available_ticks=horizon * edge.get("capacity", instance["transport"].get("bridge_capacity", 1))))
    agvs = len(instance["agvs"])
    if agvs <= 0:
        raise ValueError("At least one AGV required")
    initial_soc = sum(a["initial_soc"] for a in instance["agvs"])
    traction = travel["minimum"] * instance["transport"]["loaded_soc_per_tick"]
    charge_ticks = _ceil(Fraction(max(0, traction - initial_soc), instance["transport"]["charge_rate"]))
    agv_with_charging = occupied["minimum"] + charge_ticks
    labor = labor_and_tools(instance)
    nominal_stock = defaultdict(int)
    for unit in instance["units"]:
        if unit["recipe"] != "pump":
            nominal_stock[unit["recipe"]] += 1
    stock = {kind: dict(required=count, initial=instance["raw_stock_units"].get(kind, 0),
                        initial_shortfall=max(0, count - instance["raw_stock_units"].get(kind, 0)))
             for kind, count in sorted(nominal_stock.items())}
    certificates = []
    if occupied["minimum"] > agvs * horizon:
        certificates.append("AGV mandatory loaded transport plus handling exceeds fleet time capacity")
    if agv_with_charging > agvs * horizon:
        certificates.append("AGV mandatory transport plus unavoidable traction recharge exceeds fleet time capacity")
    if labor["violated_skill_cuts"]:
        certificates.append("Declared processing attendance violates qualified worker calendar capacity")
    for tool in labor["tools"]:
        if tool["deficit_ticks"]:
            certificates.append(f"Mandatory processing plus service exceeds {tool['kind']} tool/eligible-worker calendar capacity")
    for machine in labor["machine_capacity_bounds"]:
        if machine["minimum_processing_ticks"] > machine["available_machine_ticks"]:
            certificates.append(f"Mandatory processing exceeds {machine['process']} machine capacity")
    for bridge in bridge_bounds:
        if bridge["minimum_occupied_ticks"] > bridge["available_ticks"]:
            certificates.append(f"Mandatory loaded use exceeds single-lane capacity on {bridge['edge']}")
    digest = hashlib.sha256(json.dumps(instance, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return dict(schema="metaltech-stage2-capacity-bounds.v1", instance_sha256=digest,
                profile=instance.get("profile", "not supplied"), orders=len(instance["orders"]),
                horizon_ticks=horizon, tick_minutes=instance["tick_minutes"],
                scope="All nominal orders fulfilled with fixed initial capacity; no leases, shocks, rework, urgent arrivals or initial WIP",
                transport=dict(agvs=agvs, available_agv_ticks=agvs * horizon,
                    mandatory_part_moves=moves["minimum"], minimum_loaded_travel_ticks=travel["minimum"],
                    minimum_transport_agv_ticks=occupied["minimum"], handling_ticks_per_move=handling,
                    initial_soc_granted_free=initial_soc, minimum_loaded_traction_soc=traction,
                    minimum_recharge_agv_ticks=charge_ticks, minimum_agv_ticks_with_recharge=agv_with_charging,
                    minimum_horizon_ticks_transport_only=_ceil(Fraction(occupied["minimum"], agvs)),
                    minimum_horizon_ticks_with_recharge=_ceil(Fraction(agv_with_charging, agvs)),
                    minimum_interhall_loaded_crossings=crossings["minimum"], bridges=bridge_bounds,
                    per_order_transport_minima=occupied["per_order"]),
                labor=labor, raw_stock=stock,
                nominal_completion_impossible_with_initial_capacity=bool(certificates),
                lease_options_present=bool(instance.get("lease_options")),
                full_model_infeasibility_proven=bool(certificates) and not instance.get("lease_options"),
                infeasibility_certificates=certificates,
                limitations=["Passing these necessary conditions never proves schedule feasibility.",
                    "The labor certificate applies to the supplied attendance table; a separate full-attendance counterfactual is reported.",
                    "All explicitly certified modes and eligible machines are allowed; controller preferences are not additional restrictions.",
                    "Transport excludes empty repositioning, tool moves, charging travel, congestion and waiting.",
                    "Tool service bounds grant full initial tool life and ignore maintenance.",
                    "Reusable machine/tool capacity is fixed to the supplied instance; extra capacity purchases require a revised certificate.",
                    "Raw-stock shortfall alone is not an infeasibility certificate when procurement is permitted.",
                    "Relaxed witness routes minimize the stated resource objective, and are not feasible schedules."])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orders", type=int, default=24)
    parser.add_argument("--horizon", type=int, default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--profile", choices=("full", "coarse"), default="full")
    parser.add_argument("--instance", type=Path, help="Numerical instance JSON, or a trace containing instance")
    args = parser.parse_args()
    if args.instance:
        data = json.loads(args.instance.read_text())
        instance = data.get("instance", data)
    else:
        from .spec import build
        instance = build(orders=args.orders, horizon=args.horizon, seed=args.seed, profile=args.profile)
    print(json.dumps(analyze(instance), indent=2))


if __name__ == "__main__":
    main()
