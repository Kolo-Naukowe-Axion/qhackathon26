"""Independent raw-record validation. No compiler/conflict-list imports."""
from collections import Counter, defaultdict
from .domain import PROFILE, LEGACY_PROFILE, program_id


def _check_plan(instance, state, plan):
    errors, claims = [], defaultdict(list)
    horizon, step = instance["horizon_minutes"], instance["grid_minutes"]
    if instance.get("profile_id") not in (PROFILE,LEGACY_PROFILE):
        return dict(valid=False, violations=["Unsupported profile"], metrics=None)
    recovery = state.get("recovery_operations",[])
    if plan.get("recovery_operations",[]) != recovery:
        errors.append("Mandatory post-repair clean changed or missing")
    if instance["profile_id"] == PROFILE:
        if len(recovery) != len(state["outages"]):
            errors.append("Missing mandatory post-repair clean in state")
        for outage in state["outages"]:
            tasks = [op for op in recovery if op["resource"] == outage["resource"]]
            if len(tasks) != 1:
                errors.append("Invalid recovery clean identity")
                continue
            op = tasks[0]
            if (op["kind"] != "recovery_clean" or op["start"] < outage["end"]
                    or op["end"]-op["start"] != instance["repair_clean_minutes"]
                    or op["repair_end"] != outage["end"] or "clean" not in instance["workers"].get(op["worker"],[])
                    or not 0 <= op["start"] < op["end"] <= horizon or op["start"]%step or op["end"]%step):
                errors.append("Invalid mandatory recovery clean")
            for r in (op["resource"],op["worker"]):
                if not any(a <= op["start"] and op["end"] <= b for a,b in instance["calendars"][r]):
                    errors.append("Recovery clean calendar violation")
                if any(o["resource"] == r and op["start"] < o["end"] and o["start"] < op["end"] for o in state["outages"]):
                    errors.append("Recovery clean outage violation")
                claims[r].append((op["start"],op["end"],op["id"]))
    batches = {b["id"]: b for b in plan.get("batches", [])}
    if len(batches) != len(plan.get("batches", [])):
        errors.append("Duplicate batch")
    fixed_ids = {b["id"] for b in state["fixed_batches"]}
    for fixed in state["fixed_batches"]:
        if batches.get(fixed["id"]) != fixed:
            errors.append("Committed batch changed or missing")
    groups = {d["id"]: d for d in state["demand_groups"]}
    ops, by_batch = {}, defaultdict(lambda: defaultdict(list))
    for op in plan.get("operations", []):
        oid, kind, bid = op.get("id"), op.get("kind"), op.get("batch_id")
        if oid in ops or bid not in batches or kind not in ("prepare", "cook", "pack", "clean"):
            errors.append("Invalid operation identity/kind")
            continue
        ops[oid] = op
        by_batch[bid][kind].append(op)
        a, b, c = op.get("start"), op.get("end"), op.get("attended_end")
        if any(type(v) is not int for v in (a, b, c)) or not 0 <= a < c <= b <= horizon or a % step or b % step or c % step:
            errors.append("Invalid operation timing")
            continue
        if bid not in fixed_ids and a < state["current_time"]:
            errors.append("New work starts in the past")
        resource, worker = op.get("resource"), op.get("worker")
        if kind == "cook" and a >= state["current_time"] and any(task["resource"] == resource and a < task["end"] for task in recovery):
            errors.append("Cooking before post-repair clean finishes")
        role = "cook" if kind == "clean" else kind
        if resource not in instance["equipment"].get(role, []) or kind not in instance["workers"].get(worker, []):
            errors.append("Resource eligibility/qualification")
            continue
        for r, start, end in [(resource, a, b), (worker, a, c)]:
            if not any(left <= start and end <= right for left, right in instance["calendars"][r]):
                errors.append("Calendar violation")
            if any(o["resource"] == r and start < o["end"] and o["start"] < end for o in state["outages"]):
                errors.append("Outage violation")
            claims[r].append((start, end, oid))
    for resource, intervals in claims.items():
        intervals.sort()
        for first, second in zip(intervals, intervals[1:]):
            if first[1] > second[0]:
                errors.append("Overlap: " + resource)
    coverage, allocated, packing_used = Counter(), Counter(), set()
    for a in plan.get("allocations", []):
        d, packing, bid = groups.get(a.get("demand_group")), ops.get(a.get("packing_operation")), a.get("batch_id")
        if (d is None or packing is None or packing["kind"] != "pack" or packing["batch_id"] != bid
                or bid not in batches or a.get("lots") != 1 or packing["id"] in packing_used):
            errors.append("Invalid or duplicate allocation")
            continue
        packing_used.add(packing["id"])
        if d["menu"] != batches[bid]["menu"] or packing["end"] > d["departure"]:
            errors.append("Wrong menu/late allocation")
        if packing["start"] < d["revealed"]:
            errors.append("Allocation before demand reveal")
        cooks = by_batch[bid]["cook"]
        if len(cooks) == 1 and not 0 <= d["departure"] - cooks[0]["end"] <= instance["menus"][d["menu"]]["max_age"]:
            errors.append("Stale handover")
        coverage[d["id"]] += 1
        allocated[bid] += 1
    waste = Counter()
    for d in plan.get("disposals", []):
        bid = d.get("batch_id")
        cooks = by_batch[bid]["cook"]
        if bid not in batches or type(d.get("lots")) is not int or d["lots"] <= 0 or len(cooks) != 1:
            errors.append("Invalid disposal")
            continue
        if d.get("time") != cooks[0]["end"] or d.get("reason") != "unallocated_output":
            errors.append("Invalid disposal policy")
        waste[bid] += d["lots"]
    for bid, b in batches.items():
        recipe = instance["menus"].get(b.get("menu"))
        y = b.get("yield_lots")
        if recipe is None or type(y) is not int or y not in recipe["yields"] or bid != program_id(b):
            errors.append("Invalid recipe/yield/program identity")
            continue
        if bid not in fixed_ids and not b["allocation_order"]:
            errors.append("New batch must serve at least one lot in this core profile")
        parts = by_batch[bid]
        if any(len(parts[k]) != 1 for k in ("prepare", "cook", "clean")):
            errors.append("Missing/duplicate recipe operation")
            continue
        prep, cook, clean = (parts[k][0] for k in ("prepare", "cook", "clean"))
        if (prep["end"] - prep["start"] != recipe["prepare"]
                or cook["end"] - cook["start"] != recipe["cooking"][str(y)]
                or clean["end"] - clean["start"] != recipe["clean"]
                or cook["attended_end"] - cook["start"] != recipe["cook_attendance"]
                or prep["end"] > cook["start"] or clean["start"] != cook["end"]
                or clean["resource"] != cook["resource"]):
            errors.append("Recipe duration/precedence/cleaning")
        if (prep["start"] != b["prep_start"] or cook["start"] != b["cook_start"]
                or prep["resource"] != b["prep_station"] or cook["resource"] != b["cooker"]):
            errors.append("Program/operation mismatch")
        packs = sorted(parts["pack"], key=lambda p: p["start"])
        if len(packs) != allocated[bid] or len(packs) != len(b["allocation_order"]):
            errors.append("Packing/coverage mismatch")
        expected_order = []
        allocations = {a["packing_operation"]: a["demand_group"] for a in plan.get("allocations", [])
                       if a.get("batch_id") == bid}
        for j, p in enumerate(packs):
            expected_order.append(allocations.get(p["id"]))
            if (p["start"] < cook["end"] or p["end"] - p["start"] != recipe["pack_per_lot"]
                    or p["start"] != b["pack_start"] + j * recipe["pack_per_lot"]):
                errors.append("Packing duration/precedence/contiguity")
        if expected_order != b["allocation_order"]:
            errors.append("Allocation identity order")
        for kind in ("prepare", "cook", "clean", "pack"):
            for op in parts[kind]:
                if op["worker"] != b["workers"][kind] or (kind != "cook" and op["attended_end"] != op["end"]):
                    errors.append("Attendance/program mismatch")
        if allocated[bid] + waste[bid] != y:
            errors.append("Material balance")
    for d in groups.values():
        if coverage[d["id"]] > d["lots"]:
            errors.append("Demand served twice")
    chosen = set(batches) - fixed_ids
    previous = {b["id"] for b in state["previous_unstarted"]}
    metrics = dict(U=sum(d["priority"] * (d["lots"] - coverage[d["id"]]) for d in groups.values()),
                   W=sum(waste.values()), B=len(chosen), R=len(chosen ^ previous))
    return dict(valid=not errors, violations=sorted(set(errors)), metrics=metrics,
                covered_lots=dict(coverage), operations=len(ops), discarded_lots=sum(waste.values()))


def check_plan(instance, state, plan):
    try:
        return _check_plan(instance, state, plan)
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        return dict(valid=False, violations=["Malformed raw plan: " + type(exc).__name__],
                    metrics=None)
