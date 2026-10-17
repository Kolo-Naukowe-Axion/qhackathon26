"""Independent verification of Stage 2 execution artifacts.

This module deliberately imports no simulation or scheduling code.  A checker
must reconstruct resource use from the executed records rather than believe a
simulator's cached feasibility flag or objective value.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
from math import ceil, isclose, pi, sin
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class Interval:
    """A half-open resource occupation [start, end)."""

    start: int
    end: int
    amount: int = 1
    source: str = ""


def interval_violations(
    intervals: Iterable[Interval], capacity: int = 1
) -> list[dict[str, Any]]:
    """Find overloads without relying on simulator resource calendars.

    All departures at a boundary precede arrivals.  Keeping the interval source
    in the report makes a collision actionable without dumping a whole trace.
    """
    changes: dict[int, list[tuple[int, str]]] = defaultdict(list)
    issues: list[dict[str, Any]] = []
    if type(capacity) is not int or capacity < 0:
        return [{"code": "capacity", "message": "Capacity must be a nonnegative integer"}]
    for row in intervals:
        if any(type(value) is not int for value in (row.start, row.end, row.amount)):
            issues.append({"code": "interval", "message": "Noninteger interval", "event_id": row.source})
            continue
        if row.start < 0 or row.end <= row.start or row.amount <= 0:
            issues.append({"code": "interval", "message": "Invalid half-open interval", "event_id": row.source})
            continue
        changes[row.start].append((row.amount, row.source))
        changes[row.end].append((-row.amount, row.source))
    load = 0
    active: dict[str, int] = defaultdict(int)
    for tick, updates in sorted(changes.items()):
        # Negative deltas first: a job ending at t can release a resource for a
        # job starting at t.  Test only the post-boundary load.
        for delta, source in sorted(updates):
            load += delta
            active[source] += delta
            if not active[source]:
                del active[source]
        if load > capacity:
            issues.append({"code": "resource_capacity", "message": f"Load {load} exceeds capacity {capacity}",
                           "tick": tick, "event_ids": sorted(active)})
    return issues


def _issue(code: str, message: str, tick: int | None = None, **details: Any) -> dict[str, Any]:
    row: dict[str, Any] = {"code": code, "message": message}
    if tick is not None:
        row["tick"] = tick
    row.update(details)
    return row


def _integer(value: Any, minimum: int = 0) -> bool:
    return type(value) is int and value >= minimum


def check_trace(trace: dict[str, Any], instance: dict[str, Any] | None = None) -> dict[str, Any]:
    """Reconstruct physical constraints from interval records and primitive events.

    ``valid`` means no violation of the checks listed under ``coverage``.  It
    does not mean every order was delivered or that an unsupported mechanism
    has been verified.  Incomplete horizons retain this distinction.
    """
    issues: list[dict[str, Any]] = []
    if trace.get("schema") != "metaltech-stage2-trace.v1":
        return dict(valid=False, issues=[_issue("schema", "Unsupported trace schema")], coverage=[], metrics={})
    spec = instance or trace.get("instance")
    if not isinstance(spec, dict):
        return dict(valid=False, issues=[_issue("instance", "Complete numerical instance required")], coverage=[], metrics={})
    horizon = trace.get("horizon_ticks", spec.get("horizon_ticks"))
    if not _integer(horizon, 1):
        return dict(valid=False, issues=[_issue("horizon", "Positive integer horizon required")], coverage=[], metrics={})
    if trace.get("tick_minutes") != spec.get("tick_minutes"):
        issues.append(_issue("tick_units", "Trace and numerical instance disagree on tick duration"))
    if horizon > spec.get("horizon_ticks", horizon):
        issues.append(_issue("horizon", "Execution trace extends beyond the declared instance horizon"))
    machines = {x["id"]: x for x in spec.get("machines", [])}
    workers = {x["id"]: x for x in spec.get("workers", [])}
    tools = {x["id"]: x for x in spec.get("tools", [])}
    initial_tool_ids = set(tools)
    lease_options = {x["id"]: x for x in spec.get("lease_options", [])}
    for option in lease_options.values():
        resource = option.get("resource", {})
        if resource.get("id") not in tools:
            tools[resource.get("id")] = resource
    agvs = {x["id"]: x for x in spec.get("agvs", [])}
    orders = {x["id"]: x for x in spec.get("orders", [])}
    units = {x["id"]: dict(x) for x in spec.get("units", [])}
    ops = trace.get("operations", [])
    moves = trace.get("moves", [])
    events = trace.get("events", [])
    calendars: dict[tuple[str, str], list[Interval]] = defaultdict(list)
    operations_by_unit: dict[str, list[dict]] = defaultdict(list)
    move_by_unit: dict[str, list[dict]] = defaultdict(list)
    valid_ops: list[dict] = []
    valid_moves: list[dict] = []
    worker_activities: dict[str, list[dict]] = defaultdict(list)
    seen_ids: set[str] = set()
    period = spec.get("day_ticks", 24 * 60 // spec.get("tick_minutes", 15))

    def report(code: str, message: str, row: dict | None = None, **details: Any) -> None:
        tick = row.get("start", row.get("tick")) if row else None
        if row and "id" in row:
            details.setdefault("event_id", row["id"])
        issues.append(_issue(code, message, tick, **details))

    def known_interval(row: dict) -> bool:
        if not _integer(row.get("start")) or not _integer(row.get("end"), 1) or row["start"] >= row["end"]:
            report("interval", "Invalid activity interval", row)
            return False
        if row["start"] >= horizon:
            report("horizon", "Activity begins outside execution horizon", row)
        identity = str(row.get("id", ""))
        if not identity or identity in seen_ids:
            report("activity_id", "Missing or duplicate activity id", row)
        seen_ids.add(identity)
        return True

    # Audit the realized exogenous tape after execution.  This information is
    # unavailable to the policy, but must be independently reproducible here.
    if "seed" in spec and "uncertainty_stages" in spec:
        expected_events: list[tuple[str, int, dict]] = []
        expected_urgent_count = 0
        for index, stage in enumerate(spec["uncertainty_stages"]):
            tick = stage["reveal_tick"]
            if tick > horizon:
                continue
            raw = hashlib.sha256(f'{spec["seed"]}:stage:{index}'.encode()).digest()
            draw = int.from_bytes(raw[:8], "big") / 2**64
            cumulative = 0.0
            selected = None
            for outcome in stage["outcomes"]:
                numerator, denominator = outcome["probability"]
                cumulative += numerator / denominator
                if draw < cumulative:
                    selected = outcome
                    break
            if selected is None:
                report("exogenous_distribution", "Exogenous probabilities do not cover the keyed draw", dict(tick=tick))
                continue
            expected_events.append(("reveal", tick, {"outcome": selected["id"]}))
            for payload in selected["events"]:
                kind = payload["type"]
                if kind == "urgent_orders":
                    expected_urgent_count += payload["count"]
                else:
                    expected_events.append(("outage" if kind == "machine_outage" else kind, tick,
                                            {k: v for k, v in payload.items() if k != "type"}))
        expected_counts: dict[str, int] = defaultdict(int)
        for kind, tick, payload in expected_events:
            expected_counts[kind] += 1
            matches = [event for event in events if event.get("type") == kind and event.get("tick") == tick and
                       all(event.get(key) == value for key, value in payload.items())]
            if len(matches) != 1:
                report("exogenous_tape", "Realized external event differs from the immutable keyed scenario tape", dict(tick=tick), event_type=kind)
        for kind in ("reveal", "outage", "grid_derating", "delivery_delay"):
            if sum(event.get("type") == kind for event in events) != expected_counts[kind]:
                report("exogenous_event_count", "Missing, duplicated or fabricated external event", event_type=kind)
        if sum(event.get("type") == "urgent_order" for event in events) != expected_urgent_count:
            report("urgent_count", "Revealed urgent-order count differs from realized scenario tape")

    # Basic process, mode, crew and shared-resource reservations.
    for op in ops:
        if not known_interval(op):
            continue
        valid_ops.append(op)
        kind = op.get("kind", "process")
        machine_id = op.get("machine_id")
        machine = machines.get(machine_id)
        if machine is None and kind != "tool_service":
            report("machine", "Unknown machine", op)
            continue
        if machine is not None:
            calendars["machine", machine_id].append(Interval(op["start"], op["end"], source=op["id"]))
        process = op.get("process")
        if kind == "process" and process != machine["process"]:
            report("machine_process", "Machine cannot perform this process", op)
        if kind == "process" and op.get("mode") not in spec.get("modes", {}).get(process, {}):
            report("mode", "Unknown processing mode", op)
        if kind not in ("process", "maintenance", "tool_service", "repair"):
            report("operation_kind", "Unsupported operation kind", op)
        for event in events:
            if event.get("type") == "outage" and event.get("machine", event.get("resource_id")) == machine_id:
                start, end = event.get("start", event.get("tick", horizon)), event.get("end", horizon)
                if op["start"] < end and start < op["end"]:
                    report("machine_outage", "Reserved processing overlaps physical machine outage without interruption segments", op, outage_start=start, outage_end=end)
        if len(op.get("worker_ids", [])) != len(set(op.get("worker_ids", []))):
            report("worker_duplicate", "Worker assigned twice to one operation", op)
        needed_skill = (spec.get("maintenance", {}).get("skill") if kind == "maintenance" else
                        spec.get("quality", {}).get("repair_skill") if kind == "repair" else
                        "setup" if kind == "tool_service" else
                        spec.get("process_skills", {}).get(process))
        if needed_skill and not op.get("worker_ids"):
            report("worker_missing", "Required attendance has no worker", op)
        assignments = op.get("worker_intervals")
        if assignments is None:
            assignments = [dict(worker_id=wid, start=op["start"], end=op["end"], role="combined",
                                skills=[s for s in (needed_skill, "setup" if op.get("setup_ticks", 0) else None)
                                        if s and s in workers.get(wid, {}).get("skills", [])]) for wid in op.get("worker_ids", [])]
        if {x.get("worker_id") for x in assignments} != set(op.get("worker_ids", [])):
            report("worker_manifest", "Worker interval assignments differ from worker_ids", op)
        for assignment in assignments:
            worker_id = assignment.get("worker_id")
            worker = workers.get(worker_id)
            if worker is None:
                report("worker", "Unknown worker", op, resource_id=worker_id)
                continue
            start, end = assignment.get("start"), assignment.get("end")
            if not _integer(start) or not _integer(end, 1) or not op["start"] <= start < end <= op["end"]:
                report("worker_interval", "Attendance interval lies outside its operation", op, resource_id=worker_id)
                continue
            for skill in assignment.get("skills", []):
                if skill not in worker.get("skills", []):
                    report("worker_skill", f"Worker lacks assigned {skill} skill", op, resource_id=worker_id)
            worker_activities[worker_id].append(dict(op, start=start, end=end))
            a, b = worker["daily_shift"]
            for tick in range(start, end):
                day_tick = tick % period
                if not a <= day_tick < b or any(x <= day_tick < y for x, y in worker.get("breaks", [])):
                    report("worker_calendar", "Attendance crosses shift or break", op, resource_id=worker_id, offending_tick=tick)
                    break
        # Merge overlapping roles on the same operation: one qualified worker
        # can perform setup and then tend the same automatic machine.
        for wid in op.get("worker_ids", []):
            spans = sorted((a["start"], a["end"]) for a in assignments if a.get("worker_id") == wid and _integer(a.get("start")) and _integer(a.get("end"), 1))
            merged: list[list[int]] = []
            for start, end in spans:
                if merged and start <= merged[-1][1]:
                    merged[-1][1] = max(merged[-1][1], end)
                else:
                    merged.append([start, end])
            for start, end in merged:
                calendars["worker", wid].append(Interval(start, end, source=op["id"]))
        process_start = op["start"] + op.get("setup_ticks", 0)
        attendance = spec.get("attendance", {}).get(process, {"kind": "full"})
        process_end = op["end"] if attendance.get("kind") == "full" or kind != "process" else min(op["end"], process_start + attendance.get("ticks", 0))
        requirements = [(needed_skill, process_start, process_end)]
        if op.get("setup_ticks", 0):
            requirements.append(("setup", op["start"], process_start))
        for skill, start, end in requirements:
            if not skill:
                continue
            for tick in range(start, end):
                if not any(a.get("start", horizon) <= tick < a.get("end", 0) and skill in a.get("skills", []) and skill in workers.get(a.get("worker_id"), {}).get("skills", []) for a in assignments):
                    report("worker_attendance", f"Required {skill} attendance is uncovered", op, offending_tick=tick)
                    if not any(skill in workers.get(wid, {}).get("skills", []) for wid in op.get("worker_ids", [])):
                        report("worker_skill", f"No assigned worker has {skill} skill", op)
                    break
        required_tool = spec.get("process_tools", {}).get(process) if kind == "process" else None
        if required_tool and not any(tools.get(x, {}).get("kind") == required_tool for x in op.get("tool_ids", [])):
            report("tool_missing", f"Process requires {required_tool} tool", op)
        for tool_id in op.get("tool_ids", []):
            if tool_id not in tools:
                report("tool", "Unknown tool", op, resource_id=tool_id)
            calendars["tool", tool_id].append(Interval(op["start"], op["end"], source=op["id"]))
        ids = op.get("unit_ids", [op.get("unit_id")])
        if kind == "process" and not ids:
            report("unit_missing", "Process has no physical unit", op)
        if len(ids) != len(set(ids)):
            report("unit_duplicate", "Batch repeats one physical unit", op)
        if process == "HEAT" and len(ids) > machine.get("batch_capacity", 1):
            report("batch_capacity", "Heat batch exceeds machine capacity", op)
        if process != "HEAT" and kind == "process" and len(ids) > 1:
            report("batch_process", "Only heat permits multi-unit batches", op)
        for uid in ids:
            if uid is not None:
                operations_by_unit[uid].append(op)

    # Workers spend real time walking between halls.  This remains separate from
    # occupancy intervals so simultaneous endpoint release is handled correctly.
    for wid, worker in workers.items():
        sequence = [(op["start"], "work", op) for op in worker_activities[wid]]
        sequence += [(walk["start"], "walk", walk) for walk in trace.get("worker_moves", []) if walk.get("worker_id") == wid]
        hall = worker.get("initial_hall", "A")
        for _, activity, row in sorted(sequence, key=lambda x: (x[0], x[1])):
            if activity == "walk":
                calendars["worker", wid].append(Interval(row["start"], row["end"], source=f"walk:{wid}:{row['start']}"))
                if row.get("from_hall") != hall or row.get("to_hall") == hall or row["end"] - row["start"] != spec.get("worker_travel_ticks", 0):
                    report("worker_travel", "Worker walk disagrees with position or travel-time table", row, resource_id=wid)
                a, b = worker["daily_shift"]
                if any(not a <= tick % period < b or any(x <= tick % period < y for x, y in worker.get("breaks", [])) for tick in range(row["start"], row["end"])):
                    report("worker_walk_calendar", "Required worker travel crosses shift or break", row, resource_id=wid)
                hall = row.get("to_hall")
            elif (machines.get(row.get("machine_id"), {}).get("hall") if row.get("kind") != "tool_service" else
                  machines.get(row.get("station"), {}).get("hall", str(row.get("station", ""))[-1:])) != hall:
                report("worker_location", "Worker is assigned in a hall they have not reached", row, resource_id=wid)

    # Physical AGV paths, traction energy, payload and lane conflicts.
    edges = {frozenset((e["a"], e["b"])): e["ticks"] for e in spec.get("graph_edges", [])}
    for move in moves:
        if not known_interval(move):
            continue
        valid_moves.append(move)
        aid = move.get("agv_id")
        if aid not in agvs:
            report("agv", "Unknown AGV", move)
            continue
        calendars["agv", aid].append(Interval(move["start"], move["end"], source=move["id"]))
        uid = move.get("unit_id")
        if uid:
            move_by_unit[uid].append(move)
        legs = move.get("legs", [])
        last_end = move["start"]
        last_node = None
        for index, leg in enumerate(legs):
            edge = frozenset((leg.get("from"), leg.get("to")))
            if edge not in edges or leg.get("end", 0) - leg.get("start", 0) != edges.get(edge):
                report("agv_path", "Leg is not a declared graph edge of its declared duration", move, leg=index)
            if not _integer(leg.get("start")) or not _integer(leg.get("end"), 1) or leg["end"] <= leg["start"]:
                report("agv_leg", "Invalid AGV leg interval", move, leg=index)
                continue
            if leg["start"] < last_end or leg["start"] < move["start"] or leg["end"] > move["end"]:
                report("agv_path_time", "Leg lies outside its move or overlaps the preceding leg", move, leg=index)
            if last_node is not None and leg.get("from") != last_node:
                report("agv_teleport", "AGV path is disconnected", move, leg=index)
            last_end, last_node = leg["end"], leg.get("to")
            calendars["lane", "|".join(sorted(str(x) for x in edge))].append(
                Interval(leg["start"], leg["end"], source=move["id"]))
        if move.get("kind", "transport") == "transport":
            pickup, drop = move.get("pickup_tick"), move.get("drop_tick")
            if not _integer(pickup) or not _integer(drop) or not move["start"] <= pickup < drop <= move["end"]:
                report("transport_boundaries", "Invalid pickup/drop boundaries", move)
            loaded = [x for x in legs if x.get("loaded")]
            empty = [x for x in legs if not x.get("loaded")]
            if not uid or not loaded:
                report("transport_payload", "Part/tool transport must carry one entity on a loaded path", move)
            elif loaded[0]["from"] != move.get("from") or loaded[-1]["to"] != move.get("to"):
                report("transport_payload_path", "Loaded route does not connect pickup to drop destination", move)
            elif _integer(pickup) and _integer(drop):
                if loaded[0]["start"] < pickup + spec["transport"].get("load_ticks", 1) or drop != loaded[-1]["end"] + spec["transport"].get("unload_ticks", 1) or move["end"] != drop:
                    report("transport_handling", "Pickup/loading/unloading boundaries do not match physical handling times", move)
                if any(leg["end"] > pickup for leg in empty) or empty and empty[-1]["to"] != move.get("from"):
                    report("transport_empty_path", "Empty repositioning must reach pickup before loading", move)
                if any(leg.get("loaded") and any(not later.get("loaded") for later in legs[index + 1:]) for index, leg in enumerate(legs)):
                    report("transport_payload_order", "Empty travel cannot follow loaded travel in a single delivery", move)
            if move.get("entity_type") not in ("part", "tool"):
                report("transport_entity", "Payload must be exactly one part or tool", move)
        elif move.get("kind") == "charge":
            if uid is not None or any(x.get("loaded") for x in legs):
                report("charge_payload", "Charging action cannot transport payload", move)
            charge_start = move.get("charge_start", last_end)
            calendars["charger", move.get("to", "")].append(Interval(charge_start, move["end"], source=move["id"]))
        else:
            report("move_kind", "Unsupported movement kind", move)

    for aid, agv in agvs.items():
        location, soc, prior_end = agv["initial_location"], agv["initial_soc"], 0
        for move in sorted((x for x in valid_moves if x.get("agv_id") == aid), key=lambda x: x["start"]):
            legs = move.get("legs", [])
            if legs and legs[0].get("from") != location:
                report("agv_origin", "Empty repositioning does not start at AGV's physical location", move)
            if not legs and (move.get("from") != location or move.get("kind") == "charge" and move.get("to") != location):
                report("agv_origin", "AGV changes physical location without travel", move)
            if legs and legs[-1].get("to") != move.get("to"):
                report("agv_destination", "AGV final path node differs from its claimed destination", move)
            if not isclose(move.get("soc_before", -1), soc, abs_tol=1e-6):
                report("agv_soc_before", "Reported AGV SOC disagrees with reconstructed history", move)
            for leg in legs:
                soc -= (leg["end"] - leg["start"]) * (spec["transport"]["loaded_soc_per_tick"] if leg.get("loaded") else spec["transport"]["empty_soc_per_tick"])
                if soc < -1e-6:
                    report("agv_soc", "AGV runs out of energy in transit", move)
            if move.get("kind") == "charge":
                charge_start = move.get("charge_start", legs[-1]["end"] if legs else move["start"])
                # The charger delivers up to its rate and shuts off its battery
                # output at full SOC; wall power remains reserved for that tick.
                soc = min(agv["capacity"], soc + (move["end"] - charge_start) * spec["transport"]["charge_rate"])
            if not isclose(move.get("soc_after", -1), soc, abs_tol=1e-6):
                report("agv_soc_after", "Reported AGV SOC violates traction/charge equation", move)
            if not -1e-6 <= soc <= agv["capacity"] + 1e-6:
                report("agv_soc_bounds", "AGV SOC outside capacity", move)
            location = move.get("to", legs[-1]["to"] if legs else location)
            prior_end = move["end"]

    for (kind, resource), rows in calendars.items():
        capacity = spec["transport"].get("charger_capacity", 1) if kind == "charger" else 1
        for violation in interval_violations(rows, capacity):
            violation.update(resource_type=kind, resource_id=resource)
            issues.append(violation)

    # Independent event sweep: the simulator's position snapshots are ignored.
    positions = {uid: u.get("initial_location", "RAW_A") for uid, u in units.items()}
    states = {uid: "unreleased" for uid in units}
    progress = {uid: 0 for uid in units}
    accepted: set[str] = set()
    consumed: set[str] = set()
    shipped: dict[str, int] = {}
    tool_positions = {tid: t["initial_location"] if tid in initial_tool_ids else None for tid, t in tools.items()}
    tool_life = {tid: t["life"] if tid in initial_tool_ids else 0 for tid, t in tools.items()}
    machine_wear = {mid: m.get("initial_wear", 0) for mid, m in machines.items()}
    machine_family = {mid: m.get("initial_family") for mid, m in machines.items()}
    attempts = {uid: 0 for uid in units}
    quality_risk = {uid: 0.0 for uid in units}
    processing_start_wear: dict[str, float] = {}
    repair_progress: dict[str, int] = {}
    replacement_count: dict[str, int] = defaultdict(int)
    authorized_replacements: dict[str, tuple[str, int]] = {}
    discarded: set[str] = set()
    last_qa_failed: dict[str, bool] = {}
    stock = dict(spec.get("raw_stock_units", {}))
    investment_cost = 0
    lease_requests: dict[str, list[dict]] = defaultdict(list)
    lease_deliveries: dict[str, int] = defaultdict(int)
    material_deliveries = 0
    released: set[str] = set()
    output: dict[str, set[str]] = {mid: set() for mid in machines}
    reservations: dict[str, tuple[str, str]] = {}
    sweep: list[tuple[int, int, str, dict]] = []
    for op in valid_ops:
        sweep.extend(((op["end"], 0, "complete", op), (op["start"], 6, "start", op)))
    for move in valid_moves:
        if move.get("kind", "transport") == "transport" and _integer(move.get("pickup_tick")) and _integer(move.get("drop_tick")):
            sweep.extend(((move["start"], 4, "reserve", move), (move["pickup_tick"], 3, "pickup", move), (move["drop_tick"], 1, "drop", move)))
    for event in events:
        if not _integer(event.get("tick")):
            report("event_tick", "Event has invalid tick", event)
        elif event.get("type") in ("qa_result", "scrap", "replacement", "ship", "urgent_order", "new_unit", "repair", "release", "delivery", "lease_request", "lease_delivery"):
            sweep.append((event["tick"], 2, "event", event))

    def input_count(mid: str) -> int:
        physical = sum(positions.get(uid) == mid and state == "input" for uid, state in states.items())
        reserved = sum(destination == mid for _, destination in reservations.values())
        return physical + reserved

    ordered_sweep = sorted(sweep, key=lambda x: (x[0], x[1], str(x[3].get("id", ""))))
    for sweep_index, (tick, _, action, row) in enumerate(ordered_sweep):
        if tick > horizon:
            continue
        uid = row.get("unit_id")
        mid = row.get("machine_id")
        ids = row.get("unit_ids", [uid])
        kind = row.get("kind", "process")
        if action == "start" and kind == "tool_service":
            expected_durations = {tools.get(tid, {}).get("service_ticks") for tid in row.get("tool_ids", [])}
            if not row.get("tool_ids") or expected_durations != {row["end"] - row["start"]}:
                report("tool_service_duration", "Tool service does not match its numerical duration", row)
            for tid in row.get("tool_ids", []):
                if tool_positions.get(tid) != row.get("station"):
                    report("tool_service_location", "Tool is not physically at its service station", row, resource_id=tid)
        elif action == "complete" and kind == "tool_service":
            for tid in row.get("tool_ids", []):
                tool_life[tid] = tools.get(tid, {}).get("life", 0)
        elif action == "reserve":
            if row.get("entity_type", "part") == "part" and row.get("to") in machines:
                reservations[row["id"]] = (uid, row["to"])
        elif action == "pickup":
            if row.get("entity_type", "part") == "tool":
                if tool_positions.get(uid) != row.get("from"):
                    report("tool_pickup_location", "Tool is not at pickup location", row, unit_id=uid)
                tool_positions[uid] = "@" + row["id"]
            else:
                if uid not in units:
                    report("part_unknown", "Move names a nonexistent physical unit", row)
                elif positions.get(uid) != row.get("from") or states.get(uid) in ("unreleased", "processing", "transit", "consumed", "scrapped"):
                    report("part_pickup_location", "Part is unavailable at pickup location", row, actual_location=positions.get(uid), actual_state=states.get(uid))
                elif tick < units[uid].get("release_tick", 0):
                    report("part_release", "Part dispatched before order release", row)
                if uid in discarded and row.get("to") != "SCRAP_B":
                    report("scrap_destination", "Rejected scrap must be transported to its physical scrap dock", row)
                if row.get("from") in output:
                    output[row["from"]].discard(uid)
                positions[uid], states[uid] = "@" + row["id"], "transit"
        elif action == "drop":
            if row.get("entity_type", "part") == "tool":
                if tool_positions.get(uid) != "@" + row["id"]:
                    report("tool_drop_location", "Tool drop has no matching pickup", row)
                tool_positions[uid] = row["to"]
            else:
                if positions.get(uid) != "@" + row["id"]:
                    report("part_drop_location", "Part drop has no matching pickup", row)
                positions[uid], states[uid] = row["to"], "input"
                if row["to"] == "SCRAP_B":
                    states[uid] = "scrapped"
                reservations.pop(row["id"], None)
        elif action == "start" and mid in machines:
            if output[mid]:
                report("machine_blocking", "Machine starts before finished output is picked up", row, blocking_units=sorted(output[mid]))
            if kind == "maintenance":
                if row["end"] - row["start"] != spec["maintenance"]["duration"] or row.get("processing_ticks") != spec["maintenance"]["duration"]:
                    report("maintenance_duration", "Maintenance duration differs from numerical table", row)
                if row.get("power_kw") != spec["maintenance"]["power_kw"]:
                    report("maintenance_power", "Maintenance power differs from numerical table", row)
                continue
            process = row.get("process")
            mode = spec.get("modes", {}).get(process, {}).get(row.get("mode"), {})
            processing_start_wear[row["id"]] = machine_wear[mid]
            if "wear_before" in row and not isclose(row["wear_before"], machine_wear[mid], abs_tol=1e-6):
                report("machine_wear_history", "Reported pre-operation wear disagrees with completed physical workload", row)
            for part in ids:
                order = orders.get(units.get(part, {}).get("order_id", row.get("order_id")), {})
                certified = spec.get("certification_modes", {}).get("precision", {}).get(process)
                if order.get("precision_required") and certified is not None and row.get("mode") not in certified:
                    report("mode_certification", "Selected mode is not certified for this precision order", row, unit_id=part)
            if row.get("is_rework"):
                repair_step = row.get("repair_step")
                if repair_progress.get(uid) != repair_step or repair_step not in (0, 1):
                    report("repair_precedence", "Rework does not follow a revealed bounded repair route", row)
                expected_process = "QA" if repair_step == 1 else "ASSEMBLY" if units.get(uid, {}).get("recipe") == "pump" else "T"
                if process != expected_process:
                    report("repair_process", "Rework uses an undeclared process", row)
                repair_base = (spec.get("quality", {}).get("repair_ticks", 3) if repair_step != 1 else
                               spec.get("recipes", {}).get("pump", [{"base_ticks": spec.get("quality", {}).get("repair_ticks", 3)}])[-1]["base_ticks"])
                mode_factor = mode.get("duration_factor", [1, 1])
                machine_factor = machines[mid].get("duration_factor", [1, 1])
                expected_processing = ceil(repair_base * mode_factor[0] * machine_factor[0] / (mode_factor[1] * machine_factor[1]))
            elif kind == "repair":
                expected_processing = spec.get("quality", {}).get("repair_ticks")
            else:
                base = []
                if process == "ASSEMBLY":
                    base = [spec["recipes"]["pump"][0]["base_ticks"]]
                else:
                    for part in ids:
                        if part not in units:
                            report("part_unknown", "Process names a nonexistent unit", row, unit_id=part)
                            continue
                        recipe = spec["recipes"][units[part]["recipe"]]
                        index = row.get("recipe_steps", {}).get(part, row.get("recipe_step", progress.get(part, 0)) if part == uid else progress.get(part, 0))
                        if index != progress.get(part, 0) or index >= len(recipe) or recipe[index]["process"] != process:
                            report("recipe_precedence", "Process is not the next required recipe step", row, unit_id=part, expected_step=progress.get(part, 0))
                        if 0 <= index < len(recipe):
                            base.append(recipe[index]["base_ticks"])
                factor = mode.get("duration_factor", [1, 1])
                mfactor = machines[mid].get("duration_factor", [1, 1])
                expected_processing = ceil(max(base, default=0) * factor[0] * mfactor[0] / (factor[1] * mfactor[1]))
            if row.get("processing_ticks") != expected_processing:
                report("processing_duration", "Duration does not match numerical recipe/machine/mode table", row, expected=expected_processing)
            family = row.get("family")
            previous_family = machine_family[mid]
            expected_setup = 0 if previous_family is None else spec.get("setup_matrix", {}).get(previous_family, {}).get(family)
            if row.get("setup_ticks", 0) != expected_setup:
                report("setup_sequence", "Setup is not determined by immediately preceding machine family", row, expected=expected_setup)
            if row["end"] - row["start"] != row.get("processing_ticks", 0) + row.get("setup_ticks", 0):
                report("operation_duration", "Operation interval must equal setup plus processing", row)
            if mode and not isclose(row.get("power_kw", -1), mode["power_kw"], abs_tol=1e-6):
                report("operation_power", "Operation power differs from selected mode", row)
            if machine_wear[mid] + row.get("processing_ticks", 0) * mode.get("wear", 1) > spec.get("maintenance", {}).get("wear_limit", float("inf")) + 1e-6:
                report("machine_wear", "Processing would exceed hard wear limit", row)
            for tid in row.get("tool_ids", []):
                if tool_positions.get(tid) != mid:
                    report("tool_location", "Tool is not physically at its assigned machine", row, resource_id=tid, actual_location=tool_positions.get(tid))
                if tool_life.get(tid, 0) < row.get("processing_ticks", 0):
                    report("tool_life", "Tool has insufficient remaining life", row, resource_id=tid)
            if row.get("attempt", 0) != attempts.get(uid, 0):
                report("quality_attempt", "Operation attempt disagrees with bounded repair history", row)
            if process == "ASSEMBLY" and not row.get("is_rework"):
                parents = row.get("parent_unit_ids", [])
                expected = {"housing": 1, "rotor": 1, "flange": 1}
                actual: dict[str, int] = defaultdict(int)
                for parent in parents:
                    if parent not in units:
                        report("bom_parent", "Assembly parent does not exist", row, unit_id=parent)
                        continue
                    actual[units[parent]["recipe"]] += 1
                    if units[parent]["order_id"] != row.get("order_id"):
                        report("bom_genealogy", "Assembly consumes a component from another order", row, unit_id=parent)
                    if parent not in accepted or progress.get(parent) != len(spec["recipes"][units[parent]["recipe"]]):
                        report("bom_acceptance", "Assembly parent is not a completed accepted component", row, unit_id=parent)
                    if parent in consumed or positions.get(parent) != mid or states.get(parent) != "input":
                        report("bom_consumption", "Assembly parent unavailable or consumed twice", row, unit_id=parent)
                    consumed.add(parent)
                    states[parent], positions[parent] = "consumed", None
                if dict(actual) != expected or len(parents) != len(set(parents)):
                    report("bom_quantity", "Assembly must consume one distinct housing, rotor and flange", row)
                if uid in units:
                    report("bom_output", "Assembly output unit already exists", row)
                units[uid] = dict(id=uid, recipe="pump", order_id=row.get("order_id"), family=family, release_tick=tick, parent_unit_ids=parents)
                positions[uid], states[uid], progress[uid] = mid, "processing", 0
                quality_risk[uid] = 0.0
            else:
                families = set()
                for part in ids:
                    if part in units:
                        families.add(units[part].get("family"))
                        if positions.get(part) != mid or states.get(part) != "input" or part in consumed:
                            report("part_process_location", "Process input is not in the machine's physical input buffer", row, unit_id=part, actual_location=positions.get(part), actual_state=states.get(part))
                        if part in discarded:
                            report("scrap_processing", "Permanently scrapped unit cannot reenter production", row, unit_id=part)
                        if tick < units[part].get("release_tick", 0):
                            report("part_release", "Processing before release", row, unit_id=part)
                        states[part] = "processing"
                if len(families) > 1 or families and family not in families:
                    report("batch_family", "Batch and operation family are incompatible", row)
            machine_family[mid] = family
        elif action == "complete" and mid in machines:
            if kind == "maintenance":
                machine_wear[mid] = 0
                if spec.get("maintenance", {}).get("reset_family", False):
                    machine_family[mid] = None
            elif kind == "tool_service":
                for tid in row.get("tool_ids", []):
                    tool_life[tid] = tools.get(tid, {}).get("life", 0)
            else:
                mode = spec.get("modes", {}).get(row.get("process"), {}).get(row.get("mode"), {})
                machine_wear[mid] += row.get("processing_ticks", 0) * mode.get("wear", 1)
                for tid in row.get("tool_ids", []):
                    tool_life[tid] = tool_life.get(tid, 0) - row.get("processing_ticks", 0)
                for part in ids:
                    if part not in units:
                        continue
                    if row.get("is_rework"):
                        repair_progress[part] = repair_progress.get(part, 0) + 1
                    elif kind != "repair":
                        progress[part] = progress.get(part, 0) + 1
                    states[part], positions[part] = "output", mid
                    output[mid].add(part)
                    quality = spec.get("quality", {})
                    if row.get("process") != "QA" and quality.get("risk_model") == "manufacturing_mode_history":
                        if row.get("is_rework"):
                            quality_risk[part] = quality["repair_residual_probability"]
                        else:
                            probability = quality["manufacturing_defect_probabilities"][row["process"]][row["mode"]]
                            probability += quality["wear_risk_coefficient"] * processing_start_wear.get(row["id"], 0) / spec["maintenance"]["wear_limit"]
                            quality_risk[part] = 1 - (1 - quality_risk.get(part, 0)) * (1 - probability)
        elif action == "event":
            event_type = row.get("type")
            if event_type == "lease_request":
                option_id = row.get("option_id")
                option = lease_options.get(option_id)
                if option is None:
                    report("lease_option", "Lease request names an undeclared option", row)
                else:
                    lease_requests[option_id].append(row)
                    if len(lease_requests[option_id]) > option["max_count"]:
                        report("lease_count", "Lease requests exceed the resource option count", row)
                    if row.get("cost") != option["cost"] or row.get("arrival_tick") != tick + option["lead_ticks"]:
                        report("lease_terms", "Lease request changes its fixed cost or delivery lead time", row)
                    investment_cost += option["cost"]
                    if investment_cost > spec.get("investment_budget", 0):
                        report("investment_budget", "Resource investment exceeds the hard cash budget", row)
            elif event_type == "lease_delivery":
                option_id = row.get("option_id")
                option = lease_options.get(option_id)
                delivered_tool = row.get("tool", {})
                lease_deliveries[option_id] += 1
                if option is None or delivered_tool != option.get("resource"):
                    report("lease_resource", "Delivered lease resource differs from its declared physical template", row)
                elif lease_deliveries[option_id] > len(lease_requests[option_id]) or not any(request.get("arrival_tick") == tick for request in lease_requests[option_id]):
                    report("lease_birth", "Leased resource appears without a matching matured request", row)
                elif delivered_tool["id"] in initial_tool_ids or tool_positions.get(delivered_tool["id"]) is not None:
                    report("lease_duplicate_resource", "Lease delivery duplicates an existing physical tool", row)
                else:
                    tool_positions[delivered_tool["id"]] = delivered_tool["initial_location"]
                    tool_life[delivered_tool["id"]] = delivered_tool["life"]
            elif event_type == "urgent_order":
                order = row.get("order", {})
                if order.get("id") in orders or order.get("release_tick") != tick:
                    report("urgent_release", "Urgent order is duplicated or released at another boundary", row)
                orders[order.get("id")] = order
            elif event_type == "new_unit":
                unit = row.get("unit", {})
                new_id = unit.get("id")
                if new_id in units or unit.get("order_id") not in orders:
                    report("unit_creation", "New unit duplicates existing lineage or has no known order", row)
                order = orders.get(unit.get("order_id"), {})
                replacement = authorized_replacements.get(new_id)
                if replacement is not None:
                    original, release_tick = replacement
                    original_unit = units[original]
                    if any(unit.get(key) != original_unit.get(key) for key in ("order_id", "recipe", "family")) or unit.get("release_tick") != release_tick:
                        report("replacement_template", "Replacement changes immutable genealogy, recipe or procurement release", row)
                elif not (order.get("urgent") and unit.get("recipe") in ("housing", "rotor", "flange") and
                          new_id == f'{order.get("id")}/{unit.get("recipe")}/1' and unit.get("family") == order.get("family") and unit.get("release_tick") == order.get("release_tick")):
                    report("unit_birth_authorization", "A new component must come from a revealed urgent order or bounded replacement", row)
                units[new_id] = dict(unit)
                positions[new_id], states[new_id], progress[new_id] = unit.get("initial_location", "RAW_A"), "unreleased", 0
                attempts[new_id] = 0
                quality_risk[new_id] = 0.0
            elif event_type == "release":
                if uid not in units or uid in released or tick < units.get(uid, {}).get("release_tick", 0):
                    report("raw_release", "Material release is duplicated, premature or has no unit lineage", row)
                elif units[uid].get("recipe") != row.get("recipe"):
                    report("raw_recipe", "Material release names the wrong blank type", row)
                else:
                    recipe = row["recipe"]
                    if recipe in stock:
                        stock[recipe] -= 1
                        if stock[recipe] < 0:
                            report("raw_stock", "Released material exceeds physically available stock", row)
                    released.add(uid)
                    states[uid] = "input"
            elif event_type == "delivery":
                material_deliveries += 1
                delivery_spec = spec.get("delivery", {})
                expected_tick = delivery_spec.get("normal_tick")
                for announcement in events:
                    if announcement.get("type") == "delivery_delay" and announcement.get("delivery_id") == delivery_spec.get("id") and announcement.get("tick", horizon) <= tick:
                        expected_tick = announcement.get("new_tick")
                if row.get("delivery_id") != delivery_spec.get("id") or row.get("contents") != delivery_spec.get("contents") or tick != expected_tick or material_deliveries > 1:
                    report("material_delivery", "Material delivery changes its fixed contents, identity or revealed arrival time", row, expected_tick=expected_tick)
                for recipe, count in row.get("contents", {}).items():
                    if not _integer(count):
                        report("delivery_quantity", "Delivery has a negative/noninteger quantity", row)
                    else:
                        stock[recipe] = stock.get(recipe, 0) + count
            elif event_type == "qa_result":
                matching = [op for op in operations_by_unit.get(uid, []) if op.get("process") == "QA" and op["end"] == tick]
                if not matching:
                    report("qa_boundary", "QA outcome has no matching completed inspection", row)
                if type(row.get("passed")) is not bool:
                    report("qa_outcome", "QA result must state a boolean outcome", row)
                elif row["passed"]:
                    accepted.add(uid)
                else:
                    accepted.discard(uid)
                last_qa_failed[uid] = row.get("passed") is False
                if matching and "seed" in spec:
                    op = matching[0]
                    key = f'{spec["seed"]}:quality:{uid}:{op.get("attempt", 0)}'
                    expected_draw = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big") / 2**64
                    quality = spec.get("quality", {})
                    threshold = quality.get("final_defect_probability") if units.get(uid, {}).get("recipe") == "pump" else quality.get("component_defect_probability", {}).get(op.get("mode"))
                    if quality.get("risk_model") == "manufacturing_mode_history":
                        threshold = quality_risk.get(uid, 0)
                    if not isclose(row.get("keyed_uniform", -1), expected_draw, abs_tol=1e-15):
                        report("quality_tape", "Inspection draw differs from immutable keyed random tape", row)
                    if threshold is None or not isclose(row.get("defect_probability", -1), threshold, abs_tol=1e-12) or row.get("passed") != (expected_draw >= threshold):
                        report("quality_threshold", "Inspection outcome disagrees with frozen quality table and tape", row)
            elif event_type == "repair":
                if uid not in units or not last_qa_failed.get(uid) or row.get("attempt") != attempts.get(uid, 0) + 1 or row.get("attempt", 0) > spec.get("quality", {}).get("max_repairs_per_component_attempt", 1):
                    report("repair_bound", "Repair exceeds the bounded attempt budget", row)
                else:
                    attempts[uid] = row["attempt"]
                    repair_progress[uid] = 0
            elif event_type == "scrap":
                if uid in consumed or states.get(uid) == "scrapped":
                    report("scrap_conservation", "Cannot scrap consumed or already scrapped unit", row)
                discarded.add(uid)
                states[uid] = "scrap_output"
                accepted.discard(uid)
            elif event_type == "replacement":
                replacement_id = row.get("replacement_unit_id", row.get("replacement_id"))
                original = row.get("original_unit_id", uid)
                replacement_count[original] += 1
                if replacement_id in units or original not in units or replacement_count[original] > spec.get("quality", {}).get("max_replacements_per_original_component", 1) or "~r" in str(original) or original not in discarded or attempts.get(original) != 1:
                    report("replacement_genealogy", "Replacement must create a distinct descendant of an existing unit", row)
                elif replacement_id != f"{original}~r1":
                    report("replacement_genealogy", "Replacement id must preserve the bounded original lineage", row)
                else:
                    authorized_replacements[replacement_id] = (original, row.get("release_tick", tick))
                if row.get("release_tick", tick) < tick + spec.get("quality", {}).get("replacement_lead_ticks", 0):
                    report("replacement_lead", "Replacement skips physical procurement lead time", row)
            elif event_type == "ship":
                if uid not in accepted or positions.get(uid) != "SHIP_B" or units.get(uid, {}).get("recipe") != "pump":
                    report("shipping", "Only an accepted final pump physically at shipping counts as delivery", row)
                elif units[uid]["order_id"] in shipped:
                    report("shipping_duplicate", "Order delivered more than once", row)
                else:
                    shipped[units[uid]["order_id"]] = tick
        if sweep_index + 1 == len(ordered_sweep) or ordered_sweep[sweep_index + 1][0] != tick:
            for machine_id, machine in machines.items():
                occupancy = input_count(machine_id)
                if occupancy > machine["input_capacity"]:
                    report("buffer_capacity", "Physical input plus destination reservations exceeds buffer", dict(tick=tick), resource_id=machine_id, occupancy=occupancy, capacity=machine["input_capacity"])

    # Per-tick electrical accounting is rebuilt from active reservations.  Solar
    # is the available profile; curtailment is subtracted before the bus balance.
    energy_spec = spec.get("energy", {})
    energy_rows = trace.get("energy", [])
    energy_by_tick = {row.get("tick"): row for row in energy_rows}
    if len(energy_by_tick) != len(energy_rows) or set(energy_by_tick) != set(range(horizon)):
        report("energy_ticks", "Exactly one energy row is required for every execution tick")
    stationary_soc = energy_spec.get("stationary_soc_initial", 0)
    table = {a["id"]: a for a in energy_spec.get("battery_actions", [])}
    grid_kwh = energy_cost = carbon = 0.0
    for tick in range(horizon):
        row = energy_by_tick.get(tick)
        if row is None:
            continue
        expected_load = energy_spec.get("base_load_kw", 0) + sum(op.get("power_kw", 0) for op in valid_ops if op["start"] <= tick < op["end"])
        expected_load += spec.get("transport", {}).get("charge_power_kw", 0) * sum(move.get("kind") == "charge" and move.get("charge_start", move["start"]) <= tick < move["end"] for move in valid_moves)
        if not isclose(row.get("load_kw", -1), expected_load, abs_tol=1e-5):
            report("energy_load", "Electrical demand disagrees with active physical activities", dict(tick=tick), expected=expected_load)
        cap = energy_spec.get("normal_grid_cap_kw", 0)
        for event in events:
            if event.get("type") == "grid_derating" and event.get("start", event.get("tick", horizon)) <= tick < event.get("end", horizon):
                cap = min(cap, event["grid_cap_kw"])
        if not isclose(row.get("cap_kw", -1), cap, abs_tol=1e-5) or not -1e-6 <= row.get("grid_kw", -1) <= cap + 1e-5:
            report("energy_grid_cap", "Grid import/cap violates the revealed physical capacity", dict(tick=tick), expected_cap=cap)
        expected_solar = round(energy_spec.get("solar_peak_kw", 0) * max(0, sin(pi * (tick % period - period / 4) / (period / 2))), 4)
        if not isclose(row.get("solar_kw", -1), expected_solar, abs_tol=1e-5) or not 0 <= row.get("curtailed_kw", -1) <= expected_solar + 1e-5:
            report("energy_solar", "Solar generation/curtailment violates available profile", dict(tick=tick))
        action = table.get(row.get("battery_action"))
        if action is None:
            report("battery_action", "Unknown stationary battery action", dict(tick=tick))
            continue
        if not isclose(row.get("soc_before", -1), stationary_soc, abs_tol=1e-5):
            report("battery_soc_before", "Battery SOC does not follow the preceding tick", dict(tick=tick))
        stationary_soc += action["soc_delta"]
        if not isclose(row.get("soc", -1), stationary_soc, abs_tol=1e-5) or not energy_spec.get("stationary_soc_min", 0) <= stationary_soc <= energy_spec.get("stationary_soc_capacity", 0):
            report("battery_soc", "Battery SOC violates action equation or bounds", dict(tick=tick))
        supply = row.get("grid_kw", 0) + row.get("solar_kw", 0) - row.get("curtailed_kw", 0) + action["discharge_kw"]
        demand = expected_load + action["charge_kw"]
        if not isclose(supply, demand, abs_tol=1e-5):
            report("energy_balance", "Electrical bus supply differs from physical demand", dict(tick=tick), supply=supply, demand=demand)
        day_tick = tick % period
        expected_tariff = energy_spec.get("tariff_peak") if period / 3 <= day_tick < period * 3 / 4 else energy_spec.get("tariff_low")
        expected_carbon = energy_spec.get("carbon_peak") if period / 3 <= day_tick < period * 3 / 4 else energy_spec.get("carbon_low")
        if row.get("tariff") != expected_tariff or row.get("carbon_intensity") != expected_carbon:
            report("energy_price", "Tariff/carbon does not follow the frozen profile", dict(tick=tick))
        imported_kwh = row.get("grid_kw", 0) * spec.get("tick_minutes", 15) / 60
        grid_kwh += imported_kwh
        energy_cost += imported_kwh * (expected_tariff or 0)
        carbon += imported_kwh * (expected_carbon or 0)

    delivery_spec = spec.get("delivery", {})
    expected_delivery_tick = delivery_spec.get("normal_tick", horizon + 1)
    for announcement in events:
        if announcement.get("type") == "delivery_delay" and announcement.get("delivery_id") == delivery_spec.get("id") and announcement.get("tick", horizon) <= horizon:
            expected_delivery_tick = announcement.get("new_tick", expected_delivery_tick)
    if expected_delivery_tick <= horizon and material_deliveries != 1:
        report("material_delivery_missing", "Declared external material shipment did not arrive at its realized delivery boundary")
    for option_id, requests in lease_requests.items():
        matured = sum(request.get("arrival_tick", horizon + 1) <= horizon for request in requests)
        if lease_deliveries[option_id] != matured:
            report("lease_delivery_missing", "A matured paid lease request has no unique physical resource delivery", resource_id=option_id)
    if "total_cost" in trace.get("metrics", {}) and not isclose(trace["metrics"]["total_cost"], energy_cost + investment_cost, abs_tol=1e-5):
        report("summary_total_cost", "Reported total cost omits energy or resource investment")

    coverage = ["half_open_resource_capacity", "machine_eligibility", "mode_domain", "worker_skills",
                "worker_shift_breaks_travel", "tool_assignment", "batch_capacity", "agv_path_continuity",
                "agv_traction_soc", "single_lane_conflicts", "charger_capacity", "part_and_tool_location_replay",
                "machine_output_blocking", "buffer_reservations", "bom_genealogy", "recipe_precedence_duration",
                "setups_wear_service", "qa_reveal_boundaries", "physical_shipping", "urgent_release_lineage",
                "grid_solar_balance", "stationary_battery_loss_bounds", "energy_cost_carbon", "bounded_quality_rework_replacement",
                "finite_raw_stock_release", "machine_outage_exclusion", "transport_handling_boundaries",
                "resource_lease_budget_leadtime_birth", "material_delivery_realized_arrival", "precision_mode_certification",
                "manufacturing_mode_wear_quality_history", "exogenous_keyed_scenario_tape", "bounded_component_birth"]
    return dict(valid=not issues, issues=issues, coverage=coverage,
                provenance=dict(checker="independent-replay.v1",
                    checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
                unsupported=["policy_nonanticipativity_proof", "optional_emergency_procurement", "leased_machine_footprint_power",
                             "reachable_burn_in", "committed_rolling_replanning", "interruption_resume_semantics"],
                all_orders_fulfilled=len(shipped) == len(orders),
                terminal_requirements_met=stationary_soc >= energy_spec.get("stationary_soc_terminal_min", 0),
                metrics={"operations": len(ops), "moves": len(moves), "horizon_ticks": horizon,
                         "delivered_orders": len(shipped), "unfulfilled_orders": len(orders) - len(shipped),
                         "delivery_ticks": shipped,
                         "tardiness_ticks": sum(max(0, tick - orders[oid]["due_tick"]) for oid, tick in shipped.items() if oid in orders),
                         "terminal_deadline_debt_ticks": sum(max(0, shipped.get(oid, horizon) - o["due_tick"]) for oid, o in orders.items()),
                         "grid_kwh": grid_kwh, "energy_cost": energy_cost, "carbon_kg": carbon,
                         "investment_cost": investment_cost, "total_cost": energy_cost + investment_cost,
                         "terminal_soc": stationary_soc})


def check_paired_causality(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Empirically test identical actions before paired tapes become observable.

    This is a falsification test on supplied executions, not a proof that a
    policy is measurable for every possible history.  A QA draw's numeric value
    is audit data; only its pass/fail result enters the observation signature.
    """
    def index(trace: dict) -> tuple[dict[int, list[str]], dict[int, list[str]]]:
        observations: dict[int, list[str]] = defaultdict(list)
        actions: dict[int, list[str]] = defaultdict(list)
        for event in trace.get("events", []):
            kind = event.get("type")
            if kind in ("lease_request", "procurement", "commit", "cancel_commitment"):
                value = dict(collection="decisions", **{k: v for k, v in event.items() if k not in ("tick", "description")})
                actions[event["tick"]].append(json.dumps(value, sort_keys=True))
            if kind == "qa_result":
                row = {k: event[k] for k in ("type", "unit_id", "passed") if k in event}
            elif kind in ("reveal", "outage", "grid_derating", "delivery_delay", "urgent_order", "delivery"):
                row = {k: v for k, v in event.items() if k not in ("tick", "description", "keyed_uniform")}
            else:
                continue
            observations[event["tick"]].append(json.dumps(row, sort_keys=True))
        for collection in ("operations", "moves", "worker_moves"):
            for row in trace.get(collection, []):
                value = dict(collection=collection, **{k: v for k, v in row.items() if k not in ("id", "soc_before", "soc_after")})
                actions[row["start"]].append(json.dumps(value, sort_keys=True))
        for row in trace.get("energy", []):
            actions[row["tick"]].append(json.dumps(dict(collection="battery", action=row.get("battery_action")), sort_keys=True))
        return ({tick: sorted(rows) for tick, rows in observations.items()},
                {tick: sorted(rows) for tick, rows in actions.items()})

    issues = []
    prefixes = []
    indexes = [index(trace) for trace in traces]
    for left_index, left in enumerate(traces):
        for right_index in range(left_index + 1, len(traces)):
            right = traces[right_index]
            horizon = min(left.get("horizon_ticks", 0), right.get("horizon_ticks", 0))
            first_observation_difference = horizon
            for tick in range(horizon):
                if indexes[left_index][0].get(tick, []) != indexes[right_index][0].get(tick, []):
                    first_observation_difference = tick
                    break
                if indexes[left_index][1].get(tick, []) != indexes[right_index][1].get(tick, []):
                    issues.append(_issue("causality_prefix", "Paired executions differ before any observed tape outcome differs", tick,
                                         left=left_index, right=right_index))
                    break
            prefixes.append(dict(left=left_index, right=right_index, shared_observation_prefix=first_observation_difference))
    return dict(valid=not issues, issues=issues, pairs=prefixes,
                scope="Empirical paired-prefix test only; does not prove nonanticipativity over all histories")


def main() -> int:
    """Verify a saved trace and optionally retain the complete independent report."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    raw = args.trace.read_bytes()
    result = check_trace(json.loads(raw))
    result.setdefault("provenance", {})["trace_sha256"] = hashlib.sha256(raw).hexdigest()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
