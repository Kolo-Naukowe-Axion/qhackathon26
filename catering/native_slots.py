"""Direct raw batch-slot CP-SAT reference for the frozen core semantics.

No option enumeration, QUBO, conflict graph or encoded reference is imported.
Every new batch serves at least one residual lot, giving an exact slot bound.
"""
from collections import defaultdict,Counter
import argparse
import json
import math
from pathlib import Path
import platform
import time

from .check import check_plan
from .domain import fixture, snapshot, validate_instance, residual_demand, make_plan, program_id, digest
from .paired_meals import PROFILE as PAIRED_PROFILE,active_meals


def _union(intervals):
    result = []
    for start, end in sorted(intervals):
        if result and start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return result


def _closed_intervals(instance, state, resource):
    horizon = instance["horizon_minutes"]
    opened = _union(instance["calendars"][resource])
    closed, last = [], 0
    for start, end in opened:
        if last < start:
            closed.append([last, start])
        last = max(last, end)
    if last < horizon:
        closed.append([last, horizon])
    closed += [[o["start"], o["end"]] for o in state["outages"] if o["resource"] == resource]
    return _union(closed)


def solve_native(instance, state, budget=None, config=None, output_dir=None):
    from ortools.sat.python import cp_model
    start_time = time.monotonic()
    validate_instance(instance)
    budget, config = budget or {}, config or {}
    seconds = float(budget.get("wall_time_limit_s", 10))
    workers = int(config.get("workers", 1))
    sharing = config.get("allow_sharing", True)
    if not math.isfinite(seconds) or seconds <= 0 or workers < 1 or type(sharing) is not bool:
        raise ValueError("Positive time/workers and boolean sharing required")
    fixed_plan = make_plan(instance, state["fixed_batches"],state.get("recovery_operations",[]))
    if not check_plan(instance, state, fixed_plan)["valid"]:
        raise ValueError("Invalid committed boundary")
    step = instance["grid_minutes"]
    horizon, current = instance["horizon_minutes"]//step, state["current_time"]//step
    remaining = residual_demand(state)
    groups = {d["id"]:d for d in state["demand_groups"] if remaining.get(d["id"], 0)}
    model = cp_model.CpModel()
    occupancy = defaultdict(list)
    slots, assignments = [], defaultdict(list)
    prior = {p["id"]:p for p in state["previous_unstarted"]}
    matched_prior = defaultdict(list)
    fixed_waste = sum(b["yield_lots"]-len(b["allocation_order"]) for b in state["fixed_batches"])

    def integer(name, low=0, high=horizon):
        v = model.NewIntVar(low, high, name)
        model.AddHint(v, 0 if low <= 0 <= high else low)
        return v

    def boolean(name):
        b = model.NewBoolVar(name)
        model.AddHint(b, 0)
        return b

    def equals(var, value, name):
        b = boolean(name)
        model.Add(var == value).OnlyEnforceIf(b)
        model.Add(var != value).OnlyEnforceIf(b.Not())
        return b

    def within_calendar(resource, begin, end, conditions, label):
        # The raw checker requires each individual operation to fit one declared
        # window, even when two windows touch. Closures alone lose that detail.
        windows = []
        for j, (a, b) in enumerate(instance["calendars"][resource]):
            w = model.NewBoolVar(label+f":calendar:{j}")
            model.Add(begin >= a//step).OnlyEnforceIf(w)
            model.Add(end <= b//step).OnlyEnforceIf(w)
            windows.append(w)
        model.AddBoolOr(windows).OnlyEnforceIf(conditions)

    for resource in sum(instance["equipment"].values(), []) + list(instance["workers"]):
        for j, (a, b) in enumerate(_closed_intervals(instance, state, resource)):
            occupancy[resource].append(model.NewIntervalVar(a//step, (b-a)//step, b//step, f"closed:{resource}:{j}"))
    for op in fixed_plan["operations"]:
        for resource, end in [(op["resource"],op["end"]),(op["worker"],op["attended_end"])]:
            occupancy[resource].append(model.NewIntervalVar(op["start"]//step,
                                      (end-op["start"])//step, end//step,
                                      "fixed:"+op["id"]+":"+resource))
    for op in state.get("recovery_operations",[]):
        for resource in (op["resource"],op["worker"]):
            occupancy[resource].append(model.NewIntervalVar(op["start"]//step,(op["end"]-op["start"])//step,
                                      op["end"]//step,op["id"]+":"+resource))
        if op["repair_end"] < op["start"]:
            occupancy[op["resource"]].append(model.NewIntervalVar(op["repair_end"]//step,
                (op["start"]-op["repair_end"])//step,op["start"]//step,op["id"]+":await-clean"))

    for menu_id, recipe in sorted(instance["menus"].items()):
        menu_groups = {g:d for g,d in groups.items() if d["menu"] == menu_id}
        count = sum(remaining[g] for g in menu_groups)
        # Exact: each active new batch serves >=1 lot of this menu.
        previous_slot = None
        max_yield = max(recipe["yields"])
        for k in range(count):
            label = f"{menu_id}/{k}"
            active = boolean(label+":active")
            y = integer(label+":yield", 0, max_yield)
            cook_duration = integer(label+":cook-duration", 0, max(recipe["cooking"].values())//step)
            model.AddAllowedAssignments([active,y,cook_duration],
                                        [[0,0,0]]+[[1,q,recipe["cooking"][str(q)]//step] for q in recipe["yields"]])
            ps, cs, ks = (integer(label+":"+phase) for phase in ("prep-start","cook-start","pack-start"))
            pe, ce, clean_end, pack_end = (integer(label+":"+phase) for phase in ("prep-end","cook-end","clean-end","pack-end"))
            model.Add(pe == ps + recipe["prepare"]//step*active)
            model.Add(ce == cs + cook_duration)
            model.Add(clean_end == ce + recipe["clean"]//step*active)
            model.Add(cs >= pe)
            model.Add(ks >= ce)
            for v in (ps,cs,ks):
                model.Add(v >= current).OnlyEnforceIf(active)
                model.Add(v == 0).OnlyEnforceIf(active.Not())
            served = integer(label+":served", 0, max_yield)
            waste = integer(label+":waste", 0, max_yield)
            model.Add(served >= active)
            model.Add(served <= y)
            model.Add(waste == y-served)
            model.Add(pack_end == ks + recipe["pack_per_lot"]//step*served)
            choices_by_position = []
            used_positions = []
            for position in range(max_yield):
                used = boolean(label+f":position:{position}")
                used_positions.append(used)
                if position == 0:
                    model.Add(used == active)
                else:
                    model.Add(used <= used_positions[position-1])
                choices = {}
                for group, demand in menu_groups.items():
                    a = boolean(label+f":allocation:{position}:{group}")
                    choices[group] = a
                    assignments[group].append(a)
                    model.Add(ks+(position+1)*(recipe["pack_per_lot"]//step) <= demand["departure"]//step).OnlyEnforceIf(a)
                    model.Add(ks+position*(recipe["pack_per_lot"]//step) >= demand["revealed"]//step).OnlyEnforceIf(a)
                    model.Add(ce <= demand["departure"]//step).OnlyEnforceIf(a)
                    model.Add(ce >= (demand["departure"]-recipe["max_age"])//step).OnlyEnforceIf(a)
                model.Add(sum(choices.values()) == used)
                choices_by_position.append(choices)
            model.Add(served == sum(used_positions))
            if not sharing:
                group_used = {g:boolean(label+":single-customer:"+g) for g in menu_groups}
                model.Add(sum(group_used.values()) == active)
                for choices in choices_by_position:
                    for g,a in choices.items():
                        model.Add(a <= group_used[g])

            prep_choices, cooker_choices = {}, {}
            for r in instance["equipment"]["prepare"]:
                b = boolean(label+":prep-resource:"+r);prep_choices[r] = b
                occupancy[r].append(model.NewOptionalIntervalVar(ps,recipe["prepare"]//step,pe,b,label+":prep:"+r))
                within_calendar(r,ps,pe,[b],label+":prep:"+r)
            for r in instance["equipment"]["cook"]:
                b = boolean(label+":cooker:"+r);cooker_choices[r] = b
                size = integer(label+":cooker-size:"+r,0,horizon)
                model.Add(size == cook_duration + recipe["clean"]//step*active)
                occupancy[r].append(model.NewOptionalIntervalVar(cs,size,clean_end,b,label+":cook-and-clean:"+r))
                within_calendar(r,cs,ce,[b],label+":cook:"+r)
                within_calendar(r,ce,clean_end,[b],label+":clean:"+r)
            model.Add(sum(prep_choices.values()) == active)
            model.Add(sum(cooker_choices.values()) == active)
            pack_size = integer(label+":pack-size",0,horizon)
            model.Add(pack_size == recipe["pack_per_lot"]//step*served)
            occupancy[instance["equipment"]["pack"][0]].append(
                model.NewOptionalIntervalVar(ks,pack_size,pack_end,active,label+":packing"))
            for position, used in enumerate(used_positions):
                a = ks+position*(recipe["pack_per_lot"]//step)
                within_calendar(instance["equipment"]["pack"][0],a,a+recipe["pack_per_lot"]//step,
                                [used],label+f":pack-calendar:{position}")

            worker_choices = {}
            role_intervals = {
                "prepare":(ps,recipe["prepare"]//step,pe),
                "cook":(cs,recipe["cook_attendance"]//step,None),
                "pack":(ks,pack_size,pack_end),
                "clean":(ce,recipe["clean"]//step,clean_end)}
            for role,(begin,duration,end) in role_intervals.items():
                if end is None:
                    end = integer(label+":attendance-end")
                    model.Add(end == begin + duration*active)
                role_choices = {}
                for worker, skills in instance["workers"].items():
                    if role in skills:
                        b = boolean(label+":"+role+":worker:"+worker)
                        role_choices[worker] = b
                        occupancy[worker].append(model.NewOptionalIntervalVar(
                            begin,duration,end,b,label+":"+role+":"+worker))
                        if role == "pack":
                            for position, used in enumerate(used_positions):
                                a = ks+position*(recipe["pack_per_lot"]//step)
                                within_calendar(worker,a,a+recipe["pack_per_lot"]//step,[b,used],
                                                label+f":pack-worker:{worker}:{position}")
                        else:
                            within_calendar(worker,begin,end,[b],label+":"+role+":"+worker)
                model.Add(sum(role_choices.values()) == active)
                worker_choices[role] = role_choices

            slot = dict(menu=menu_id, active=active, y=y, ps=ps, cs=cs, ks=ks, served=served, waste=waste,
                        prep_choices=prep_choices,cooker_choices=cooker_choices,workers=worker_choices,
                        allocation=choices_by_position)
            slots.append(slot)
            if previous_slot:
                model.Add(previous_slot["active"] >= active)
                model.Add(previous_slot["ps"] <= ps).OnlyEnforceIf(active)
            previous_slot = slot

            for pid,p in prior.items():
                if p["menu"] != menu_id or p["prep_station"] not in prep_choices or p["cooker"] not in cooker_choices:
                    continue
                if any(p["workers"][r] not in worker_choices[r] for r in worker_choices):
                    continue
                order = p["allocation_order"]
                if len(order)>max_yield or any(g not in menu_groups for g in order):
                    continue
                standard = {"id","menu","yield_lots","prep_station","cooker","prep_start","cook_start","pack_start","workers","allocation_order"}
                if set(p) != standard:
                    continue
                conditions = [active,prep_choices[p["prep_station"]],cooker_choices[p["cooker"]],
                              equals(y,p["yield_lots"],label+":prior-y:"+pid),
                              equals(ps,p["prep_start"]//step,label+":prior-ps:"+pid),
                              equals(cs,p["cook_start"]//step,label+":prior-cs:"+pid),
                              equals(ks,p["pack_start"]//step,label+":prior-ks:"+pid),
                              equals(served,len(order),label+":prior-served:"+pid)]
                conditions += [worker_choices[r][p["workers"][r]] for r in worker_choices]
                conditions += [choices_by_position[j][g] for j,g in enumerate(order)]
                matched = boolean(label+":matches-prior:"+pid)
                model.AddBoolAnd(conditions).OnlyEnforceIf(matched)
                model.AddBoolOr([c.Not() for c in conditions]+[matched])
                matched_prior[pid].append(matched)
    for intervals in occupancy.values():
        model.AddNoOverlap(intervals)
    for matches in matched_prior.values():
        model.Add(sum(matches) <= 1)
    missed = {}
    for group, demand in groups.items():
        u = integer("missed:"+group,0,remaining[group])
        model.Add(sum(assignments[group])+u == remaining[group])
        missed[group] = u
    components = dict(
        U=sum(groups[g]["priority"]*u for g,u in missed.items()),
        W=fixed_waste+sum(s["waste"] for s in slots),
        B=sum(s["active"] for s in slots),
        R=len(prior)+sum(s["active"] for s in slots)-2*sum(m for ms in matched_prior.values() for m in ms))
    bounds = dict(U=sum(groups[g]["priority"]*remaining[g] for g in groups),
                  W=fixed_waste+sum(max(instance["menus"][s["menu"]]["yields"]) for s in slots),
                  B=len(slots),R=len(prior)+len(slots))
    if instance["profile_id"] == PAIRED_PROFILE:
        fixed_coverage = Counter(g for b in state["fixed_batches"] for g in b["allocation_order"])
        completions,orphan = [],[]
        for meal in active_meals(instance,state):
            main = fixed_coverage[meal["main"]]+sum(assignments[meal["main"]])
            side = fixed_coverage[meal["side"]]+sum(assignments[meal["side"]])
            complete = boolean("complete-meal:"+meal["id"])
            model.Add(complete <= main);model.Add(complete <= side)
            model.Add(complete >= main+side-1)
            completions.append(meal["priority"]*(1-complete))
            orphan.append(main+side-2*complete)
        components["U"] = sum(completions)
        components["W"] += sum(orphan)
        bounds["U"] = sum(m["priority"] for m in active_meals(instance,state))
        bounds["W"] = sum(b["yield_lots"] for b in state["fixed_batches"])+sum(max(instance["menus"][s["menu"]]["yields"]) for s in slots)
    # Explicit nonnegative component domains strengthen the relaxation, notably
    # for the symmetric-difference expression B + |prior| - 2*matches.
    for key, expression in components.items():
        component = integer("component:"+key,0,bounds[key])
        model.Add(component == expression)
        components[key] = component
    weights = {}
    for key in reversed(("U","W","B","R")):
        weights[key] = 1+sum(weights[k]*bounds[k] for k in weights)
    objective = sum(weights[k]*components[k] for k in components)
    if sum(weights[k]*bounds[k] for k in weights) >= 2**62:
        raise ValueError("Objective bound exceeds conservative CP-SAT integer range")
    model.Minimize(objective)
    build_s = time.monotonic()-start_time
    proto = model.Proto()
    model_size = dict(variables=len(proto.variables),constraints=len(proto.constraints),batch_slots=len(slots))
    result = dict(schema_version="catering-native-slots.v1",method_id="native_cp_raw_slots",
                  profile_id=instance["profile_id"],instance_sha256=digest(instance),snapshot_sha256=digest(state),
                  execution_kind="classical",configuration=dict(allow_sharing=sharing,workers=workers,
                                                               seed=int(config.get("seed",2026)),
                                                               initialization="Partial zero-activity hints"),
                  model_size=model_size,objective_weights=weights,component_bounds=bounds,
                  objective_scope="Raw declared-profile lexicographic (U,W,B,R); weights differ from option QUBOs",
                  program_enumeration=False,qubo_construction=False,
                  reference_scope="Complete declared raw grid/contiguous packing/conservative boundary",
                  plan=None,check=None,status="timeout",reference_status="NOT_RUN",
                  physical_qpu_calls=0,veloxq_calls=0,environment=dict(python=platform.python_version(),machine=platform.machine()))
    remaining_s = seconds-build_s
    if remaining_s <= 0:
        result["timings"] = dict(build_s=build_s,solver_s=0,total_s=time.monotonic()-start_time)
        result["failure"] = "Build exhausted the end-to-end budget"
        return result
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = remaining_s
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = int(config.get("seed",2026))
    status = solver.Solve(model)
    name = solver.StatusName(status)
    result["reference_status"] = name
    result["timings"] = dict(build_s=build_s,solver_s=solver.WallTime(),total_s=time.monotonic()-start_time)
    result["work"] = dict(branches=solver.NumBranches(),conflicts=solver.NumConflicts())
    result["objective_bound"] = solver.BestObjectiveBound()
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        programs = []
        for s in slots:
            if not solver.Value(s["active"]):
                continue
            def selected(mapping):
                return next(k for k,b in mapping.items() if solver.Value(b))
            allocations = []
            for mapping in s["allocation"]:
                chosen = [g for g,b in mapping.items() if solver.Value(b)]
                allocations += chosen
            p = dict(menu=s["menu"],yield_lots=solver.Value(s["y"]),prep_station=selected(s["prep_choices"]),
                     cooker=selected(s["cooker_choices"]),prep_start=solver.Value(s["ps"])*step,
                     cook_start=solver.Value(s["cs"])*step,pack_start=solver.Value(s["ks"])*step,
                     workers={r:selected(m) for r,m in s["workers"].items()},allocation_order=allocations)
            p["id"] = program_id(p)
            programs.append(p)
        plan = make_plan(instance,state["fixed_batches"]+programs,state.get("recovery_operations",[]))
        checked = check_plan(instance,state,plan)
        if not checked["valid"]:
            raise AssertionError("Direct native result failed independent checker: "+str(checked["violations"]))
        measured = checked["metrics"]
        for key in components:
            if solver.Value(components[key]) != measured[key]:
                raise AssertionError("Raw model/checker metric mismatch: "+key)
        result.update(status="completed",plan=plan,check=checked,
                      objective=str(sum(weights[k]*measured[k] for k in weights)))
        if name == "OPTIMAL":
            result["objective_bound"] = result["objective"]
    elif status == cp_model.INFEASIBLE:
        result["status"] = "failed"
    elif status == cp_model.MODEL_INVALID:
        raise ValueError("Invalid CP-SAT model: "+solver.ResponseStats())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance",type=Path)
    parser.add_argument("--scenario",choices=("S0","S1","S2","S3"),default="S1")
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--seconds",type=float,default=10)
    parser.add_argument("--workers",type=int,default=1)
    parser.add_argument("--no-sharing",action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a fresh output file")
    instance = fixture() if args.instance is None else json.loads(args.instance.read_text())
    result = solve_native(instance,snapshot(instance,args.scenario),
                          dict(wall_time_limit_s=args.seconds),
                          dict(workers=args.workers,allow_sharing=not args.no_sharing))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(dict(status=result["reference_status"],metrics=(result["check"] or {}).get("metrics"),
                          model_size=result["model_size"],timings=result["timings"])))


if __name__=="__main__":
    main()
