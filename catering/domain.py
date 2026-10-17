"""Raw core profile, public synthetic fixture and explicit event boundaries.

This first executable profile commits whole started batches and withdraws an
idle cooker. It does not implement the ambitious phase-aware failure profile.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from .paired_meals import PROFILE as PAIRED_PROFILE,validate_service,service_records

LEGACY_PROFILE = "core-contiguous-conservative.v1"
PROFILE = "core-contiguous-repair-clean.v2"
SCENARIOS = ("S0", "S1", "S2", "S3")
ROLES = ("prepare", "cook", "pack", "clean")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name}: integer >= {minimum} required")
    return value


def fixture():
    """A small declared grid domain; not the proposed 240-meal flagship."""
    instance = dict(
        schema_version="catering-instance.v1", instance_id="shared-lunch-core-v2",
        profile_id=PROFILE, time_origin="10:30", horizon_minutes=110,
        grid_minutes=10, lot_size=10, event_time=20,
        menus={
            "A": dict(yields=[1], prepare=10, cooking={"1": 50},
                      cook_attendance=10, pack_per_lot=10, clean=10, max_age=30),
            "B": dict(yields=[1, 2], prepare=10, cooking={"1": 20, "2": 20},
                      cook_attendance=10, pack_per_lot=10, clean=10, max_age=40)},
        equipment=dict(prepare=["P1"], cook=["C1", "C2"], pack=["K1"]),
        workers={"W1": ["prepare", "pack"], "W2": ["clean"], "W3": ["cook"]},
        calendars={r: [[0, 110]] for r in ("P1", "C1", "C2", "K1", "W1", "W2", "W3")},
        demand_groups=[
            dict(id="A/11:50", menu="A", lots=1, departure=80, revealed=0, priority=1),
            dict(id="B/12:00", menu="B", lots=1, departure=90, revealed=0, priority=1)],
        urgent_groups=[
            dict(id="B/12:10-urgent", menu="B", lots=1, departure=100,
                 revealed=20, priority=1)],
        outage=dict(resource="C2", start=20, end=60),
        policies=dict(continuation="whole_started_batch",
                      outage="idle_capacity_withdrawal", packing="contiguous",
                      surplus="discard_at_cook_end", objective=["U", "W", "B", "R"]),
        capacities=dict(ingredients=False, holding=False, power=False),
        repair_clean_minutes=10,
    )
    fixed = dict(menu="A", yield_lots=1, prep_station="P1", cooker="C1",
                 prep_start=0, cook_start=10, pack_start=60,
                 workers=dict(prepare="W1", cook="W3", pack="W1", clean="W2"),
                 allocation_order=["A/11:50"])
    fixed["id"] = program_id(fixed)
    prior = dict(menu="B", yield_lots=1, prep_station="P1", cooker="C2",
                 prep_start=20, cook_start=30, pack_start=50,
                 workers=dict(prepare="W1", cook="W3", pack="W1", clean="W2"),
                 allocation_order=["B/12:00"])
    prior["id"] = program_id(prior)
    instance["fixed_batches"] = [fixed]
    instance["previous_unstarted"] = [prior]
    validate_instance(instance)
    return instance


def program_id(program):
    return "batch-" + digest({k: v for k, v in program.items() if k != "id"})[:20]


def validate_instance(instance):
    if instance.get("profile_id") not in (PROFILE,LEGACY_PROFILE,PAIRED_PROFILE):
        raise ValueError("Unsupported profile; ambitious mechanisms are not silently ignored")
    step = integer(instance["grid_minutes"], "grid", 1)
    end = integer(instance["horizon_minutes"], "horizon", step)
    event = integer(instance["event_time"], "event time")
    if end % step or event % step or event >= end:
        raise ValueError("Grid-aligned calendar required")
    if instance["profile_id"] != LEGACY_PROFILE:
        duration = integer(instance["repair_clean_minutes"],"repair clean",1)
        if duration % step:
            raise ValueError("Grid-aligned repair clean required")
    if instance["policies"] != dict(continuation="whole_started_batch",
                                   outage="idle_capacity_withdrawal",
                                   packing="contiguous", surplus="discard_at_cook_end",
                                   objective=["U", "W", "B", "R"]):
        raise ValueError("Unknown core policies")
    if instance["capacities"] != dict(ingredients=False, holding=False, power=False):
        raise ValueError("Aggregate capacities are not implemented in this core")
    ids = set()
    for d in instance["demand_groups"] + instance["urgent_groups"]:
        if d["id"] in ids:
            raise ValueError("Duplicate demand identity")
        ids.add(d["id"])
        for name in ("lots", "departure", "revealed", "priority"):
            integer(d[name], name, 1 if name in ("lots", "priority") else 0)
        if d["departure"] > end or d["departure"] % step or d["revealed"] % step:
            raise ValueError("Demand boundary outside the grid/horizon")
        if d["menu"] not in instance["menus"] or d["revealed"] > d["departure"]:
            raise ValueError("Invalid demand menu/reveal")
    for menu in instance["menus"].values():
        if not menu["yields"] or len(set(menu["yields"])) != len(menu["yields"]):
            raise ValueError("Nonempty unique yields required")
        for y in menu["yields"]:
            integer(y, "yield", 1)
            if str(y) not in menu["cooking"]:
                raise ValueError("Missing cooking duration")
        values = [menu[k] for k in ("prepare", "cook_attendance", "pack_per_lot", "clean", "max_age")]
        values += [menu["cooking"][str(y)] for y in menu["yields"]]
        if any(type(v) is not int or v <= 0 or v % step for v in values):
            raise ValueError("Positive grid-aligned recipe times required")
        if menu["cook_attendance"] > min(menu["cooking"].values()):
            raise ValueError("Attendance exceeds cooking")
    resources = sum(instance["equipment"].values(), [])
    if len(instance["equipment"]["pack"]) != 1:
        raise ValueError("This core profile requires exactly one packing line")
    if len(resources) != len(set(resources)) or set(resources) & set(instance["workers"]):
        raise ValueError("Resource identities must be distinct")
    outage = instance.get("outage")
    if not isinstance(outage, dict) or set(outage) != {"resource", "start", "end"}:
        raise ValueError("Explicit observed cooker outage required")
    start = integer(outage["start"], "outage start")
    stop = integer(outage["end"], "outage end", 1)
    if (outage["resource"] not in instance["equipment"]["cook"]
            or start % step or stop % step or not start <= event < stop <= end):
        raise ValueError("Outage must be a grid-aligned ongoing observed cooker withdrawal")
    for resource in resources + list(instance["workers"]):
        intervals = instance["calendars"].get(resource, [])
        if not intervals:
            raise ValueError("Missing resource calendar")
        for start, stop in intervals:
            if (type(start) is not int or type(stop) is not int or
                    not 0 <= start < stop <= end or start % step or stop % step):
                raise ValueError("Invalid resource calendar")
    for b in instance["fixed_batches"] + instance["previous_unstarted"]:
        if b["id"] != program_id(b):
            raise ValueError("Invalid semantic program ID")
    if instance["profile_id"] == PAIRED_PROFILE:
        validate_service(instance)
    elif "service_model" in instance:
        raise ValueError("Service extension requires its own declared profile")
    return instance


def snapshot(instance, scenario):
    validate_instance(instance)
    if scenario not in SCENARIOS:
        raise ValueError("Scenario must be S0/S1/S2/S3")
    demands = copy.deepcopy(instance["demand_groups"])
    if scenario in ("S1", "S3"):
        demands += copy.deepcopy(instance["urgent_groups"])
    if any(d["revealed"] > instance["event_time"] for d in demands):
        raise ValueError("Snapshot contains demand not yet revealed at the event time")
    fixed = copy.deepcopy(instance["fixed_batches"])
    result = dict(schema_version="catering-snapshot.v1", scenario_id=scenario,
                  current_time=instance["event_time"], demand_groups=demands,
                  fixed_batches=fixed, previous_unstarted=copy.deepcopy(instance["previous_unstarted"]),
                  outages=[copy.deepcopy(instance["outage"])] if scenario in ("S2", "S3") else [],
                  common_prefix_sha256=digest(dict(time=instance["event_time"], fixed_batches=fixed)))
    # Idle withdrawal must be compatible with every already committed occupation.
    for b in fixed:
        for op in make_plan(instance, [b])["operations"]:
            for outage in result["outages"]:
                if op["resource"] == outage["resource"] and overlap(op["start"], op["end"], outage["start"], outage["end"]):
                    raise ValueError("Outage interrupts committed work; phase-aware profile required")
    if instance["profile_id"] != LEGACY_PROFILE:
        result["recovery_policy"] = "earliest_fixed_compatible_clean"
        result["recovery_operations"] = []
        # Conservative core policy: reserve a mandatory clean at the earliest
        # grid time compatible with the committed prefix and qualified crew.
        # This is explicit preprocessing, not an optimized recovery-task domain.
        committed = make_plan(instance,fixed)["operations"]
        for outage in result["outages"]:
            duration = instance["repair_clean_minutes"]
            chosen = None
            for start in range(outage["end"],instance["horizon_minutes"]-duration+1,instance["grid_minutes"]):
                for worker,skills in sorted(instance["workers"].items()):
                    if "clean" not in skills:
                        continue
                    resources = (outage["resource"],worker)
                    if not all(available(instance,result,r,start,start+duration) for r in resources):
                        continue
                    occupied = [(op["resource"],op["start"],op["end"]) for op in committed]
                    occupied += [(op["worker"],op["start"],op["attended_end"]) for op in committed]
                    occupied += [(op[r],op["start"],op["end"]) for op in result["recovery_operations"] for r in ("resource","worker")]
                    if any(r in resources and overlap(start,start+duration,a,b) for r,a,b in occupied):
                        continue
                    chosen = dict(id="repair-clean:"+outage["resource"],kind="recovery_clean",
                                  resource=outage["resource"],worker=worker,start=start,end=start+duration,
                                  repair_end=outage["end"])
                    break
                if chosen is not None:
                    break
            if chosen is None:
                raise ValueError("Mandatory post-repair clean cannot fit the committed boundary")
            result["recovery_operations"].append(chosen)
    return result


def overlap(a, b, c, d):
    return a < d and c < b


def available(instance, state, resource, start, end):
    return (any(a <= start and end <= b for a, b in instance["calendars"][resource])
            and not any(o["resource"] == resource and overlap(start, end, o["start"], o["end"])
                        for o in state["outages"]))


def make_plan(instance, programs, recovery_operations=()):
    """Emit explicit raw records. The separate checker validates their rules."""
    operations, allocations, disposals = [], [], []
    for b in programs:
        recipe = instance["menus"][b["menu"]]
        cook_end = b["cook_start"] + recipe["cooking"][str(b["yield_lots"])]
        def op(kind, start, end, resource, worker, attended_end=None, suffix=""):
            oid = b["id"] + "/" + kind + suffix
            operations.append(dict(id=oid, batch_id=b["id"], kind=kind, start=start, end=end,
                                   resource=resource, worker=worker,
                                   attended_end=end if attended_end is None else attended_end))
            return oid
        op("prepare", b["prep_start"], b["prep_start"] + recipe["prepare"], b["prep_station"], b["workers"]["prepare"])
        op("cook", b["cook_start"], cook_end, b["cooker"], b["workers"]["cook"],
           b["cook_start"] + recipe["cook_attendance"])
        op("clean", cook_end, cook_end + recipe["clean"], b["cooker"], b["workers"]["clean"])
        for j, group in enumerate(b["allocation_order"]):
            start = b["pack_start"] + j * recipe["pack_per_lot"]
            oid = op("pack", start, start + recipe["pack_per_lot"], instance["equipment"]["pack"][0],
                     b["workers"]["pack"], suffix=f"-{j}")
            allocations.append(dict(batch_id=b["id"], demand_group=group, lots=1, packing_operation=oid))
        waste = b["yield_lots"] - len(b["allocation_order"])
        if waste:
            disposals.append(dict(batch_id=b["id"], lots=waste, time=cook_end, reason="unallocated_output"))
    plan = dict(schema_version="catering-plan.v1", batches=copy.deepcopy(programs),
                operations=operations, allocations=allocations, disposals=disposals)
    if recovery_operations:
        plan["recovery_operations"] = copy.deepcopy(list(recovery_operations))
    if instance["profile_id"] == PAIRED_PROFILE:
        plan["meal_handovers"],plan["unpaired_disposals"] = service_records(instance,allocations)
    return plan


def residual_demand(state):
    committed = Counter(g for b in state["fixed_batches"] for g in b["allocation_order"])
    result = {}
    for d in state["demand_groups"]:
        remaining = d["lots"] - committed[d["id"]]
        if remaining < 0:
            raise ValueError("Committed production over-serves demand")
        if remaining:
            result[d["id"]] = remaining
    return result
