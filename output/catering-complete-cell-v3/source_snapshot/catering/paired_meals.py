"""Complete two-course meals: component reservations are not handovers.

One meal lot needs one main-component lot and one side-component lot. The
physical scheduler checks each component; this module checks assembly/service
and records unpaired component waste at the fixed handover time.
"""
from collections import Counter

PROFILE = "paired-course-contiguous.v3"


def validate_service(instance):
    service = instance.get("service_model",{})
    if set(service) != {"kind","meals"} or service["kind"] != "two-course-unit.v1":
        raise ValueError("Explicit two-course unit service model required")
    groups = {d["id"]:d for d in instance["demand_groups"]+instance["urgent_groups"]}
    used, ids = set(),set()
    for meal in service["meals"]:
        if set(meal) != {"id","main","side","priority"} or meal["id"] in ids:
            raise ValueError("Unique complete-meal identity required")
        ids.add(meal["id"])
        if type(meal["priority"]) is not int or meal["priority"]<1:
            raise ValueError("Positive integer whole-meal priority required")
        a,b = meal["main"],meal["side"]
        if a==b or a not in groups or b not in groups or a in used or b in used:
            raise ValueError("Each component group belongs to exactly one meal")
        x,y = groups[a],groups[b]
        if x["lots"]!=1 or y["lots"]!=1 or x["menu"]==y["menu"]:
            raise ValueError("Two distinct-menu unit component groups required")
        if x["departure"]!=y["departure"] or x["revealed"]!=y["revealed"]:
            raise ValueError("Both courses have the same fixed handover and reveal")
        used.update((a,b))
    if used != set(groups):
        raise ValueError("Every component group must belong to a declared meal")


def active_meals(instance,state):
    groups = {d["id"] for d in state["demand_groups"]}
    result = []
    for meal in instance["service_model"]["meals"]:
        if (meal["main"] in groups) != (meal["side"] in groups):
            raise ValueError("Partly revealed meal is not supported")
        if meal["main"] in groups:
            result.append(meal)
    return result


def service_records(instance,allocations):
    """Renderer only. The checker independently reconstructs these records."""
    groups = {d["id"]:d for d in instance["demand_groups"]+instance["urgent_groups"]}
    covered = {a["demand_group"]:a for a in allocations}
    handed,orphan = [],[]
    for meal in instance["service_model"]["meals"]:
        a,b = meal["main"],meal["side"]
        if a in covered and b in covered:
            handed.append(dict(meal_id=meal["id"],lots=1,time=groups[a]["departure"],components=[a,b]))
        elif a in covered or b in covered:
            g = a if a in covered else b
            orphan.append(dict(meal_id=meal["id"],batch_id=covered[g]["batch_id"],component_group=g,
                               lots=1,time=groups[g]["departure"],reason="incomplete_meal"))
    return handed,orphan


def check_service(instance,state,plan,physical):
    if not physical["valid"]:
        return physical
    groups = {d["id"]:d for d in state["demand_groups"]}
    reservations = {a["demand_group"]:a for a in plan["allocations"]}
    handed,orphan = [],[]
    missing = completed = 0
    for meal in active_meals(instance,state):
        main,side = meal["main"],meal["side"]
        if main in reservations and side in reservations:
            completed += 1
            handed.append(dict(meal_id=meal["id"],lots=1,time=groups[main]["departure"],components=[main,side]))
        else:
            missing += meal["priority"]
            for group in (main,side):
                if group in reservations:
                    orphan.append(dict(meal_id=meal["id"],batch_id=reservations[group]["batch_id"],
                                       component_group=group,lots=1,time=groups[group]["departure"],reason="incomplete_meal"))
    errors = []
    if plan.get("meal_handovers") != handed:errors.append("Complete-meal handovers changed or missing")
    if plan.get("unpaired_disposals") != orphan:errors.append("Unpaired reserved food disposal changed or missing")
    # Independent per-batch ledger: yielded components become delivered courses,
    # unallocated surplus, or reserved-but-unpaired waste. Never count both.
    supplied = Counter(a["batch_id"] for a in plan["allocations"]
                       if any(a["demand_group"] in h["components"] for h in handed))
    discarded = Counter()
    for d in plan["disposals"]+orphan:discarded[d["batch_id"]] += d["lots"]
    if any(supplied[b["id"]]+discarded[b["id"]] != b["yield_lots"] for b in plan["batches"]):
        errors.append("Complete-meal component material balance")
    result = dict(physical)
    result["component_metrics"] = physical["metrics"]
    result["metrics"] = dict(U=missing,W=physical["metrics"]["W"]+len(orphan),
                            B=physical["metrics"]["B"],R=physical["metrics"]["R"])
    result.update(valid=not errors,violations=errors,completed_meal_lots=completed,
                  unpaired_component_lots=len(orphan),discarded_lots=sum(discarded.values()),
                  quantity_units=dict(U="priority-weighted complete meal lots",W="component lots",lot_size=instance["lot_size"]))
    return result
