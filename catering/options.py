"""Complete local programs on the declared contiguous-packing core grid."""
import itertools
from collections import Counter
from .check import check_plan
from .domain import make_plan, program_id, residual_demand


def enumerate_options(instance, state):
    groups = state["demand_groups"]
    remaining = residual_demand(state)
    step, horizon = instance["grid_minutes"], instance["horizon_minutes"]
    workers = {role: sorted(w for w, skills in instance["workers"].items() if role in skills)
               for role in ("prepare", "cook", "pack", "clean")}
    programs = {}
    for menu_id, recipe in sorted(instance["menus"].items()):
        demands = [d for d in groups if d["menu"] == menu_id and remaining.get(d["id"], 0)]
        if not demands:
            continue
        for y in recipe["yields"]:
            for quantities in itertools.product(*(range(remaining[d["id"]] + 1) for d in demands)):
                served = sum(quantities)
                if not 0 < served <= y:
                    continue
                lots = [d["id"] for d, q in zip(demands, quantities) for _ in range(q)]
                orders = sorted(set(itertools.permutations(lots)))
                for order in orders:
                    for prep in range(state["current_time"], horizon, step):
                        for cook in range(prep + recipe["prepare"], horizon, step):
                            end = cook + recipe["cooking"][str(y)]
                            if end + recipe["clean"] > horizon:
                                continue
                            for pack in range(end, horizon - served * recipe["pack_per_lot"] + 1, step):
                                # Exact unary deadline/freshness filtering, prior to worker/equipment loops.
                                mapping = {d["id"]: d for d in demands}
                                if any(pack + (j + 1) * recipe["pack_per_lot"] > mapping[g]["departure"]
                                       or mapping[g]["departure"] - end > recipe["max_age"]
                                       or pack + j * recipe["pack_per_lot"] < mapping[g]["revealed"]
                                       for j, g in enumerate(order)):
                                    continue
                                for station, cooker, *crew in itertools.product(
                                        instance["equipment"]["prepare"], instance["equipment"]["cook"],
                                        *(workers[r] for r in ("prepare", "cook", "pack", "clean"))):
                                    p = dict(menu=menu_id, yield_lots=y, prep_station=station, cooker=cooker,
                                             prep_start=prep, cook_start=cook, pack_start=pack,
                                             workers=dict(zip(("prepare", "cook", "pack", "clean"), crew)),
                                             allocation_order=list(order))
                                    p["id"] = program_id(p)
                                    plan = make_plan(instance, state["fixed_batches"] + [p],state.get("recovery_operations",[]))
                                    if check_plan(instance, state, plan)["valid"]:
                                        programs[p["id"]] = p
    return [programs[k] for k in sorted(programs)]


def claims(instance, program):
    result = []
    for op in make_plan(instance, [program])["operations"]:
        result += [(op["resource"], op["start"], op["end"]),
                   (op["worker"], op["start"], op["attended_end"])]
    return result


def conflict(first_claims, second_claims):
    return any(r == s and a < d and c < b
               for r, a, b in first_claims for s, c, d in second_claims)


def restricted_pool(programs, state, cap):
    if type(cap) is not int or cap < 0:
        raise ValueError("Nonnegative option cap required")
    previous = {p["id"] for p in state["previous_unstarted"]}
    # No optimum/reference teacher. Known prior program is a declared initializer.
    ordered = sorted(programs, key=lambda p: (
        p["id"] not in previous,
        p["yield_lots"] - len(p["allocation_order"]),
        -len(p["allocation_order"]), p["cook_start"], p["pack_start"], p["id"]))
    return sorted(ordered[:cap], key=lambda p: p["id"])
