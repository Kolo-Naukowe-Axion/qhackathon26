"""Compact native raw CP reference using calendar domains, not time tables.

No QUBO coefficients, columns, pair conflict lists or assignment() calls enter
this model. Each eligible machine/worker mode has an exact union of start-grid
intervals derived analytically from raw calendars. Pairwise metric setup and
walking constraints retain the same declared model as window_qubo.solve_cp.
"""
from collections import defaultdict
import time

from .window_qubo import validate, check_plan


def mode_intervals(problem, op, machine, worker):
    """Inclusive grid-index intervals for one raw machine/worker combination."""
    m = problem['machines'][machine]
    w = problem['workers'][worker]
    if machine not in op['durations'] or op['skill'] not in w['skills']:
        return []
    duration = op['durations'][machine]
    attendance = duration if op['attendance'] == 'full' else min(duration, op['start_attendance'])
    travel = problem['worker_travel'] if m['hall'] != w['initial_hall'] else 0
    earliest_walk = 0
    if travel:
        ends = [max(w.get('ready', 0), lo) + travel for lo, hi in w['available']
                if max(w.get('ready', 0), lo) + travel <= hi]
        if not ends:
            return []
        earliest_walk = min(ends)
    setup = problem.get('machine_setups', {}).get(
        problem.get('machine_initial_family', {}).get(machine), {}).get(op.get('family'), 0)
    release = max(op['release'], op.get('machine_release', {}).get(machine, 0),
                  w.get('ready', 0), earliest_walk, setup)
    grid = problem['grid']
    result = []
    for ml, mh in m['available']:
        for wl, wh in w['available']:
            lo = max(ml, wl, release)
            hi = min(mh-duration, wh-attendance, problem['horizon']-duration)
            a, b = (lo+grid-1)//grid, hi//grid
            if a <= b:
                result.append([a, b])
    return result


def solve_interval_cp(problem, seconds=30, workers=4, initial_plan=None):
    from ortools.sat.python import cp_model
    validate(problem)
    began = time.perf_counter()
    cpu = time.process_time()
    model = cp_model.CpModel()
    machines, workforce = list(problem['machines']), list(problem['workers'])
    halls = sorted({m['hall'] for m in problem['machines'].values()})
    ops = {o['id']: o for o in problem['operations']}
    h, grid = problem['horizon'], problem['grid']
    starts, ends, attended, mids, wids, hallvars, ticks = {}, {}, {}, {}, {}, {}, {}
    machine_intervals, worker_intervals = defaultdict(list), defaultdict(list)
    machine_use, worker_use, modes = {}, {}, {}
    for oid, op in ops.items():
        starts[oid] = model.new_int_var(0, h, 'start:'+oid)
        ticks[oid] = model.new_int_var(0, h//grid, 'tick:'+oid)
        model.add(starts[oid] == grid*ticks[oid])
        ends[oid] = model.new_int_var(1, h, 'end:'+oid)
        attended[oid] = model.new_int_var(1, h, 'attended:'+oid)
        mids[oid] = model.new_int_var(0, len(machines)-1, 'machine:'+oid)
        wids[oid] = model.new_int_var(0, len(workforce)-1, 'worker:'+oid)
        hallvars[oid] = model.new_int_var(0, len(halls)-1, 'hall:'+oid)
        selected = []
        by_machine, by_worker = defaultdict(list), defaultdict(list)
        for mi, mid in enumerate(machines):
            for wi, wid in enumerate(workforce):
                intervals = mode_intervals(problem, op, mid, wid)
                if not intervals:
                    continue
                use = model.new_bool_var(f'mode:{oid}:{mid}:{wid}')
                modes[oid, mid, wid] = use
                selected.append(use)
                by_machine[mid].append(use)
                by_worker[wid].append(use)
                model.add_linear_expression_in_domain(ticks[oid], cp_model.Domain.from_intervals(intervals)).only_enforce_if(use)
                duration = op['durations'][mid]
                attention = duration if op['attendance'] == 'full' else min(duration, op['start_attendance'])
                for expression, value in ((mids[oid], mi), (wids[oid], wi),
                                          (hallvars[oid], halls.index(problem['machines'][mid]['hall']))):
                    model.add(expression == value).only_enforce_if(use)
                model.add(ends[oid] == starts[oid]+duration).only_enforce_if(use)
                model.add(attended[oid] == starts[oid]+attention).only_enforce_if(use)
        if not selected:
            return dict(status='INFEASIBLE', optimal=False, scope='Empty raw mode/calendar domain')
        model.add_exactly_one(selected)
        for mid, members in by_machine.items():
            use = model.new_bool_var('machine-use:'+oid+mid)
            model.add(use == sum(members))
            machine_use[oid, mid] = use
            machine_intervals[mid].append(model.new_optional_interval_var(
                starts[oid], op['durations'][mid], ends[oid], use, 'machine:'+oid+mid))
        for wid, members in by_worker.items():
            use = model.new_bool_var('worker-use:'+oid+wid)
            model.add(use == sum(members))
            worker_use[oid, wid] = use
            attention = model.new_int_var(1, h, 'attention:'+oid+wid)
            model.add(attention == attended[oid]-starts[oid])
            worker_intervals[wid].append(model.new_optional_interval_var(
                starts[oid], attention, attended[oid], use, 'worker:'+oid+wid))
    for intervals in [*machine_intervals.values(), *worker_intervals.values()]:
        model.add_no_overlap(intervals)
    ids = list(ops)
    for ai, a in enumerate(ids):
        for b in ids[ai+1:]:
            if problem.get('machine_setups'):
                ab = problem['machine_setups'][ops[a]['family']][ops[b]['family']]
                ba = problem['machine_setups'][ops[b]['family']][ops[a]['family']]
                if ab or ba:
                    for mid in machines:
                        if (a, mid) not in machine_use or (b, mid) not in machine_use:
                            continue
                        before = model.new_bool_var('setup-order:'+a+b+mid)
                        active = [machine_use[a, mid], machine_use[b, mid]]
                        model.add(starts[b] >= ends[a]+ab).only_enforce_if([*active, before])
                        model.add(starts[a] >= ends[b]+ba).only_enforce_if([*active, before.Not()])
            if not problem['worker_travel']:
                continue
            common = [wid for wid in workforce if (a, wid) in worker_use and (b, wid) in worker_use]
            if not common:
                continue
            different = model.new_bool_var('different-hall:'+a+b)
            model.add(hallvars[a] != hallvars[b]).only_enforce_if(different)
            model.add(hallvars[a] == hallvars[b]).only_enforce_if(different.Not())
            for wid in common:
                before = model.new_bool_var('walk-order:'+a+b+wid)
                for first, second, order in ((a,b,before), (b,a,before.Not())):
                    active = [worker_use[a,wid], worker_use[b,wid], different, order]
                    slots = []
                    travel = problem['worker_travel']
                    for lo, hi in problem['workers'][wid]['available']:
                        if hi-lo < travel:
                            continue
                        slot = model.new_bool_var(f'walk-slot:{first}:{second}:{wid}:{lo}')
                        slots.append(slot)
                        model.add(attended[first]+travel <= starts[second]).only_enforce_if(slot)
                        model.add(attended[first]+travel <= hi).only_enforce_if(slot)
                        model.add(lo+travel <= starts[second]).only_enforce_if(slot)
                    # NoOverlap supplies the occupation disjunction; this common
                    # ordering variable additionally enforces the required walk.
                    model.add_bool_or([*slots, *(u.Not() for u in active)])
    for oid, op in ops.items():
        for prior in op['predecessors']:
            lag = model.new_int_var(0, h, 'lag:'+prior+oid)
            model.add_allowed_assignments([mids[prior], mids[oid], lag], [
                (i,j,problem['transport_lags'][a][b])
                for i,a in enumerate(machines) for j,b in enumerate(machines)
                if (prior,a) in machine_use and (oid,b) in machine_use])
            model.add(starts[oid] >= ends[prior]+lag)
    makespan = model.new_int_var(0, h, 'makespan')
    model.add_max_equality(makespan, list(ends.values()))
    nonterminal = {p for op in ops.values() for p in op['predecessors']}
    tardies = []
    for oid, op in ops.items():
        if oid in nonterminal:
            continue
        late = model.new_int_var(0, h+max(0,-op['due']), 'late:'+oid)
        model.add_max_equality(late, [0, ends[oid]-op['due']])
        tardies.append(op.get('weight', 1)*late)
    model.minimize((h+1)*sum(tardies)+makespan)
    hint_check = None
    if initial_plan is not None:
        hint_check = check_plan(problem, initial_plan)
        if not hint_check['valid']:
            raise ValueError('Complete independently checked hint required')
        for r in initial_plan:
            oid = r['operation']
            for var, value in ((starts[oid],r['start']), (ticks[oid],r['start']//grid),
                               (ends[oid],r['end']), (attended[oid],r['attended_end']),
                               (mids[oid],machines.index(r['machine'])),
                               (wids[oid],workforce.index(r['worker'])), (hallvars[oid],halls.index(r['hall']))):
                model.add_hint(var, value)
            for (other, mid, wid), use in modes.items():
                if other == oid:
                    model.add_hint(use, int(mid == r['machine'] and wid == r['worker']))
        model.add_hint(makespan, hint_check['makespan'])
    proto = model.proto
    build_seconds = time.perf_counter()-began
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = 19
    status = solver.solve(model)
    result = dict(status=solver.status_name(status), optimal=status == cp_model.OPTIMAL,
                  bound=solver.best_objective_bound, model_build_seconds=build_seconds,
                  wall_seconds=time.perf_counter()-began, process_cpu_seconds=time.process_time()-cpu,
                  model_variables=len(proto.variables), model_constraints=len(proto.constraints),
                  raw_modes=len(modes), feasible_hint_used=initial_plan is not None,
                  hint_objective=hint_check['objective'] if hint_check else None,
                  scope='Complete declared raw cell; no time-indexed assignment table, no QUBO coefficients or restricted columns.')
    if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        return result
    plan = [dict(operation=oid, machine=machines[solver.value(mids[oid])],
                 worker=workforce[solver.value(wids[oid])], start=solver.value(starts[oid]),
                 end=solver.value(ends[oid]), attended_end=solver.value(attended[oid]),
                 hall=halls[solver.value(hallvars[oid])]) for oid in ids]
    checked = check_plan(problem, plan)
    if not checked['valid'] or checked['objective'] != round(solver.objective_value):
        raise AssertionError('Compact native reference violates independent raw checker/objective')
    return dict(result, plan=plan, check=checked, objective=round(solver.objective_value))
