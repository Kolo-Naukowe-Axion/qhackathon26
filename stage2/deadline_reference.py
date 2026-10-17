"""Independent raw CP reference for a hard deadline/makespan decision query.

The native model follows ``window_qubo.solve_cp``'s raw-calendar formulation,
with no QUBO domains, conflict lists or coefficients. The original horizon and
resource calendars stay intact. This is satisfaction, not cost optimization.
"""
from collections import defaultdict
import math
import time

from .window_qubo import check_plan, digest, validate


def solve_deadline_cp(problem, cap=None, seconds=10, workers=1):
    """Decide whether all terminal deadlines and the supplied cap can be met.

    ``target_feasible`` is True for a checked witness, False only for a CP proof
    of infeasibility, and None for an unresolved solve. ``seconds`` limits solver
    search; construction and complete elapsed time are reported separately.
    """
    from ortools.sat.python import cp_model

    began = time.perf_counter()
    validate(problem)
    horizon = problem['horizon']
    cap = horizon if cap is None else cap
    if type(cap) is not int or not 0 <= cap <= horizon:
        raise ValueError('Cap must be an integer between zero and the original horizon')
    if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds <= 0:
        raise ValueError('A positive finite solver time limit is required')
    if type(workers) is not int or workers < 1:
        raise ValueError('A positive integer worker count is required')
    terminals = set(o['id'] for o in problem['operations']) - {
        prior for o in problem['operations'] for prior in o['predecessors']}
    query = dict(problem_sha256=digest(problem), completion_cap=cap,
                 terminal_deadlines={o['id']: o['due'] for o in problem['operations']
                                     if o['id'] in terminals},
                 semantics='All original operations mandatory; original calendars/grid; hard terminal deadlines')
    common = dict(query=query, query_sha256=digest(query),
                  scope='Independent raw CP satisfaction: all mandatory operations, terminal deadlines and makespan cap; original horizon/calendars retained',
                  uses_qubo=False, seconds_limit=seconds, workers=workers)
    model = cp_model.CpModel()
    machines, workforce = list(problem['machines']), list(problem['workers'])
    halls = sorted({m['hall'] for m in problem['machines'].values()})
    starts, ends, attended, mids, wids, hallvars = {}, {}, {}, {}, {}, {}
    m_use, w_use = {}, {}
    machine_intervals, worker_intervals = defaultdict(list), defaultdict(list)
    eligible_machines, eligible_workers = {}, {}
    operations = {o['id']: o for o in problem['operations']}

    for oid, op in operations.items():
        starts[oid] = model.new_int_var_from_domain(
            cp_model.Domain.from_values(list(range(0, horizon + 1, problem['grid']))), 'start:' + oid)
        ends[oid] = model.new_int_var(1, horizon, 'end:' + oid)
        attended[oid] = model.new_int_var(1, horizon, 'attend:' + oid)
        mids[oid] = model.new_int_var(0, len(machines) - 1, 'machine:' + oid)
        wids[oid] = model.new_int_var(0, len(workforce) - 1, 'worker:' + oid)
        hallvars[oid] = model.new_int_var(0, len(halls) - 1, 'hall:' + oid)
        table = []
        for mi, mid in enumerate(machines):
            if mid not in op['durations']:
                continue
            duration = op['durations'][mid]
            hall = problem['machines'][mid]['hall']
            for wi, wid in enumerate(workforce):
                worker = problem['workers'][wid]
                if op['skill'] not in worker['skills']:
                    continue
                for start in range(0, horizon + 1, problem['grid']):
                    end = start + duration
                    attend = end if op['attendance'] == 'full' else start + min(duration, op['start_attendance'])
                    walk = problem['worker_travel'] if hall != worker['initial_hall'] else 0
                    initial_setup = problem.get('machine_setups', {}).get(
                        problem.get('machine_initial_family', {}).get(mid), {}).get(op.get('family'), 0)
                    if start < max(op['release'], op.get('machine_release', {}).get(mid, 0),
                                   worker.get('ready', 0), initial_setup) or end > horizon:
                        continue
                    if not any(lo <= start and end <= hi for lo, hi in problem['machines'][mid]['available']):
                        continue
                    if not any(lo <= start and attend <= hi for lo, hi in worker['available']):
                        continue
                    if walk and not any(max(worker.get('ready', 0), lo) + walk <= min(start, hi)
                                        for lo, hi in worker['available']):
                        continue
                    table.append((start, end, attend, mi, wi, halls.index(hall)))
        if not table:
            return dict(common, status='INFEASIBLE', target_feasible=False,
                        reason='Empty raw unary assignment domain', build_seconds=time.perf_counter() - began,
                        solver_seconds=0, wall_seconds=time.perf_counter() - began)
        model.add_allowed_assignments(
            [starts[oid], ends[oid], attended[oid], mids[oid], wids[oid], hallvars[oid]], table)
        duration_var = model.new_int_var(1, horizon, 'duration:' + oid)
        model.add(duration_var == ends[oid] - starts[oid])
        attendance_var = model.new_int_var(1, horizon, 'attend_duration:' + oid)
        model.add(attendance_var == attended[oid] - starts[oid])
        # Only raw-eligible resources receive intervals; no compiler pruning is used.
        eligible_machines[oid] = {machines[row[3]] for row in table}
        eligible_workers[oid] = {workforce[row[4]] for row in table}
        for mid in sorted(eligible_machines[oid]):
            use = model.new_bool_var('use:' + oid + ':' + mid)
            m_use[oid, mid] = use
            model.add(mids[oid] == machines.index(mid)).only_enforce_if(use)
            model.add(mids[oid] != machines.index(mid)).only_enforce_if(use.Not())
            machine_intervals[mid].append(model.new_optional_interval_var(
                starts[oid], duration_var, ends[oid], use, 'm:' + oid + mid))
        for wid in sorted(eligible_workers[oid]):
            use = model.new_bool_var('use:' + oid + ':' + wid)
            w_use[oid, wid] = use
            model.add(wids[oid] == workforce.index(wid)).only_enforce_if(use)
            model.add(wids[oid] != workforce.index(wid)).only_enforce_if(use.Not())
            worker_intervals[wid].append(model.new_optional_interval_var(
                starts[oid], attendance_var, attended[oid], use, 'w:' + oid + wid))
        model.add(ends[oid] <= cap)
        if oid in terminals:
            model.add(ends[oid] <= op['due'])

    for intervals in [*machine_intervals.values(), *worker_intervals.values()]:
        model.add_no_overlap(intervals)
    ids = list(operations)
    for ai, a in enumerate(ids):
        for b in ids[ai + 1:]:
            if problem.get('machine_setups'):
                for mid in sorted(eligible_machines[a] & eligible_machines[b]):
                    before = model.new_bool_var('machine_setup_order:' + a + b + mid)
                    for first, second, order in ((a, b, before), (b, a, before.Not())):
                        gap = problem['machine_setups'][operations[first]['family']][operations[second]['family']]
                        model.add(starts[second] >= ends[first] + gap).only_enforce_if(
                            [m_use[a, mid], m_use[b, mid], order])
            common_workers = eligible_workers[a] & eligible_workers[b]
            if not common_workers:
                continue
            different = model.new_bool_var('different_hall:' + a + b)
            model.add(hallvars[a] != hallvars[b]).only_enforce_if(different)
            model.add(hallvars[a] == hallvars[b]).only_enforce_if(different.Not())
            for wid in sorted(common_workers):
                before = model.new_bool_var('before:' + a + b + wid)
                for first, second, order in ((a, b, before), (b, a, before.Not())):
                    active = [w_use[a, wid], w_use[b, wid], order]
                    model.add(starts[second] >= attended[first]).only_enforce_if(active)
                    travel = problem['worker_travel']
                    if not travel:
                        continue
                    slots = []
                    for lo, hi in problem['workers'][wid]['available']:
                        if hi - lo < travel:
                            continue
                        slot = model.new_bool_var('walk:' + first + second + wid + str(lo))
                        slots.append(slot)
                        model.add(attended[first] + travel <= starts[second]).only_enforce_if(slot)
                        model.add(attended[first] + travel <= hi).only_enforce_if(slot)
                        model.add(lo + travel <= starts[second]).only_enforce_if(slot)
                    model.add_bool_or([*slots, *(u.Not() for u in active), different.Not()])
    for oid, op in operations.items():
        for prior in op['predecessors']:
            lag = model.new_int_var(0, horizon, 'lag:' + prior + oid)
            model.add_allowed_assignments([mids[prior], mids[oid], lag], [
                (i, j, problem['transport_lags'][a][b])
                for i, a in enumerate(machines) for j, b in enumerate(machines)])
            model.add(starts[oid] >= ends[prior] + lag)
    build_seconds = time.perf_counter() - began
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = 19
    solve_began = time.perf_counter()
    status = solver.solve(model)
    result = dict(common, status=solver.status_name(status),
                  target_feasible=False if status == cp_model.INFEASIBLE else None,
                  build_seconds=build_seconds, solver_seconds=time.perf_counter() - solve_began,
                  wall_seconds=time.perf_counter() - began)
    if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        return result
    plan = [dict(operation=oid, machine=machines[solver.value(mids[oid])],
                 worker=workforce[solver.value(wids[oid])], start=solver.value(starts[oid]),
                 end=solver.value(ends[oid]), attended_end=solver.value(attended[oid]),
                 hall=halls[solver.value(hallvars[oid])]) for oid in ids]
    checked = check_plan(problem, plan)
    if not checked['valid'] or checked['weighted_terminal_tardiness'] != 0 or checked['makespan'] > cap:
        raise AssertionError('Independent raw CP witness failed the original-model deadline query')
    return dict(result, target_feasible=True, plan=plan, check=checked,
                wall_seconds=time.perf_counter() - began)
