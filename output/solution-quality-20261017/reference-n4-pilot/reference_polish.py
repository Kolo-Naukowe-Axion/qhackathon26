"""Supplemental CP formulation for the frozen deterministic reference domain.

The original reference solver and final campaign stay byte-preserved. This
formulation replaces the worker circuit by chronological pairwise hall travel,
adds redundant AGV intervals, and removes only precedence-impossible AGV arcs.
It is not a solver or lower bound for the stochastic full factory.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import platform
import time

from .reference_multi import activities, resource_bounds, schedule_from_trace, to_trace, validate_scope
from .reference import shortest_path
from .check import check_trace
from .identity_audit import audit_trace

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ('stage2/reference_polish.py', 'stage2/reference_multi.py', 'stage2/reference.py',
           'stage2/engine.py', 'stage2/check.py', 'stage2/identity_audit.py')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def source_hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}


def precedence(operations, movements):
    """Operation ancestors, including all three incoming matched BOM branches."""
    parents = {op['id']: set() for op in operations}
    for move in movements:
        if move['source_op'] and move['target_op']:
            parents[move['target_op']].add(move['source_op'])
    ancestors = {}
    def visit(name, visiting):
        if name in ancestors:
            return ancestors[name]
        if name in visiting:
            raise ValueError('Cyclic recipe/BOM graph')
        found = set(parents[name])
        for parent in parents[name]:
            found.update(visit(parent, visiting | {name}))
        ancestors[name] = found
        return found
    for name in parents:
        visit(name, set())
    return ancestors


def checked_witness(instance, trace):
    physical = check_trace(trace, deepcopy(instance))
    identity = audit_trace(trace, instance)
    if trace['instance'] != instance or not (physical['valid'] and identity['valid']
            and physical['all_orders_fulfilled'] and physical['terminal_requirements_met']):
        raise ValueError('A complete, physical/identity-valid identical-instance witness is required')
    return physical, identity


def normalize_future_reservations(trace):
    """Delay only future-pump empty dispatch if physical timing permits it.

    The resulting COPY is checked by both unchanged auditors. Original solver
    output remains separate. Loaded legs, pickup/drop and operations never change.
    """
    result = deepcopy(trace)
    births = {op['unit_id']: op['start'] for op in trace['operations'] if op['process'] == 'ASSEMBLY'}
    changes = []
    for move in result['moves']:
        birth = births.get(move['unit_id'], 0)
        if move['start'] < birth:
            first_leg = min((leg['start'] for leg in move['legs']), default=move['pickup_tick'])
            if first_leg < birth:
                raise ValueError('Physical prebirth travel cannot be repaired by delaying a parked reservation')
            changes.append(dict(move_id=move['id'], old_start=move['start'], new_start=birth))
            move['start'] = birth
    return result, changes


def build_model(instance, incumbent=None):
    from ortools.sat.python import cp_model
    validate_scope(instance)
    operations, moves = activities(instance)
    ancestors = precedence(operations, moves)
    bound = instance['horizon_ticks']
    hint_schedule = None
    if incumbent is not None:
        physical, _ = checked_witness(instance, incumbent)
        bound = max(physical['metrics']['delivery_ticks'].values())
        hint_schedule = schedule_from_trace(instance, operations, moves, incumbent)
    model = cp_model.CpModel()
    starts, ends, attended_ends = {}, {}, {}
    for op in operations:
        name, duration = op['id'], op['duration']
        starts[name] = model.new_int_var(0, max(0, bound-duration), 'start:'+name)
        ends[name] = starts[name] + duration
        model.add(ends[name] <= bound)
        rule = instance['attendance'][op['process']]
        attended_ends[name] = starts[name] + (duration if rule['kind'] == 'full' else min(duration, rule['ticks']))
    distance = lambda a, b: sum(d for _, _, d in shortest_path(instance, a, b))
    dispatch, pickup, drop = {}, {}, {}
    incoming, outgoing = defaultdict(list), {}
    agv_intervals = []
    for move in moves:
        name = move['id']
        dispatch[name] = model.new_int_var(0, bound, 'dispatch:'+name)
        pickup[name] = model.new_int_var(0, bound, 'pickup:'+name)
        drop[name] = model.new_int_var(0, bound, 'drop:'+name)
        model.add(drop[name] == pickup[name] + 2 + distance(move['from'], move['to']))
        span = model.new_int_var(0, bound, 'agv_span:'+name)
        model.add(span == drop[name] - dispatch[name])
        agv_intervals.append(model.new_interval_var(dispatch[name], span, drop[name], 'agv:'+name))
        if move['source_op']:
            model.add(pickup[name] >= ends[move['source_op']])
            if instance['reference_scope']['dispatch_after_source_completion']:
                model.add(dispatch[name] >= ends[move['source_op']])
            outgoing[move['source_op']] = name
        if move['target_op']:
            model.add(drop[name] <= starts[move['target_op']])
            incoming[move['target_op']].append(name)
    model.add_no_overlap(agv_intervals)
    machines = {m['id']: m for m in instance['machines']}
    machine_intervals, buffers = defaultdict(list), defaultdict(list)
    worker_intervals = []
    for op in operations:
        name, station = op['id'], op['machine_id']
        release = pickup[outgoing[name]]
        span = model.new_int_var(op['duration'], bound, 'machine_span:'+name)
        model.add(span == release-starts[name])
        machine_intervals[station].append(model.new_interval_var(starts[name], span, release, 'machine:'+name))
        worker_intervals.append(model.new_interval_var(starts[name], attended_ends[name]-starts[name], attended_ends[name], 'worker:'+name))
        for mid in incoming[name]:
            size = model.new_int_var(0, bound, 'buffer_span:'+mid)
            model.add(size == starts[name]-dispatch[mid])
            buffers[station].append(model.new_interval_var(dispatch[mid], size, starts[name], 'buffer:'+mid))
    for intervals in machine_intervals.values():
        model.add_no_overlap(intervals)
    for station, intervals in buffers.items():
        model.add_cumulative(intervals, [1]*len(intervals), machines[station]['input_capacity'])
    model.add_no_overlap(worker_intervals)
    # Every pair in different halls needs a hall transition between attendances.
    # Together with NoOverlap this is equivalent to the original worker path:
    # chronological adjacent tasks satisfy the required walk; nonadjacent pairs
    # cannot forbid a path since intermediate work/walks take nonnegative time.
    walk = instance['worker_travel_ticks']
    worker_orders = {}
    for j, a in enumerate(operations):
        if a['hall'] != instance['workers'][0]['initial_hall']:
            model.add(starts[a['id']] >= walk)
        for b in operations[j+1:]:
            if a['hall'] == b['hall']:
                continue
            if a['id'] in ancestors[b['id']]:
                model.add(starts[b['id']] >= attended_ends[a['id']] + walk)
            elif b['id'] in ancestors[a['id']]:
                model.add(starts[a['id']] >= attended_ends[b['id']] + walk)
            else:
                order = model.new_bool_var('worker_before:'+a['id']+':'+b['id'])
                worker_orders[a['id'], b['id']] = order
                model.add(starts[b['id']] >= attended_ends[a['id']] + walk).only_enforce_if(order)
                model.add(starts[a['id']] >= attended_ends[b['id']] + walk).only_enforce_if(order.Not())
    arcs = {}
    pruned = 0
    for a in range(len(moves)+1):
        for b in range(len(moves)+1):
            if a == b:
                continue
            # A move delivering into an operation must precede every transfer
            # sourcing that operation or any of its recipe/BOM descendants.
            if a and b:
                ma, mb = moves[a-1], moves[b-1]
                target, source = mb['target_op'], ma['source_op']
                if target and source and (target == source or target in ancestors[source]):
                    pruned += 1
                    continue
            literal = model.new_bool_var(f'agv_arc:{a}:{b}')
            arcs[a, b] = literal
            if b:
                move = moves[b-1]
                prior = instance['agvs'][0]['initial_location'] if not a else moves[a-1]['to']
                if a:
                    model.add(dispatch[move['id']] >= drop[moves[a-1]['id']]).only_enforce_if(literal)
                model.add(pickup[move['id']] >= dispatch[move['id']]+distance(prior, move['from'])).only_enforce_if(literal)
    model.add_circuit([(a, b, lit) for (a, b), lit in arcs.items()])
    ids = [o['id'] for o in instance['orders']]
    for a, b in zip(ids, ids[1:]):
        model.add(starts[f'{a}/housing/1/op0'] <= starts[f'{b}/housing/1/op0'])
    makespan = model.new_int_var(0, bound, 'last_shipment')
    model.add_max_equality(makespan, [drop[m['id']] for m in moves if m['to'] == 'SHIP_B'])
    model.add(makespan >= resource_bounds(instance)['makespan_lower_bound_ticks'])
    if hint_schedule:
        for name, var in starts.items():
            model.add_hint(var, hint_schedule['operations'][name])
        for name in dispatch:
            hint = hint_schedule['moves'][name]
            for variables, key in ((dispatch, 'start'), (pickup, 'pickup'), (drop, 'drop')):
                model.add_hint(variables[name], hint[key])
        for (a, b), literal in arcs.items():
            model.add_hint(literal, int(hint_schedule['agv_successors'].get(a) == b))
        for (a, b), literal in worker_orders.items():
            model.add_hint(literal, int(hint_schedule['operations'][a] < hint_schedule['operations'][b]))
        model.add_hint(makespan, bound)
    model.minimize(makespan)
    return model, dict(operations=operations, movements=moves, starts=starts, dispatch=dispatch,
                      pickup=pickup, drop=drop, arcs=arcs, makespan=makespan,
                      pruned_agv_arcs=pruned, worker_order_bits=len(worker_orders), upper_bound=bound)


def solve(instance, incumbent=None, wall_limit=60, workers=8, seed=2026, log_path=None):
    import ortools
    from ortools.sat.python import cp_model
    if not math.isfinite(wall_limit) or wall_limit <= 0 or type(workers) is not int or workers < 1:
        raise ValueError('Positive finite wall budget and integer worker count required')
    before = source_hashes()
    started, cpu = time.perf_counter(), time.process_time()
    model, variables = build_model(instance, incumbent)
    error = model.validate()
    if error:
        raise ValueError(error)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = wall_limit
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    history = []
    class Incumbents(cp_model.CpSolverSolutionCallback):
        def on_solution_callback(self):
            entry = dict(wall_seconds=self.wall_time, objective=self.objective_value, lower_bound=self.best_objective_bound)
            history.append(entry)
            if log_path:
                with Path(log_path).open('a') as handle:
                    handle.write(json.dumps(entry)+'\n')
    status = solver.solve(model, Incumbents())
    report = dict(schema='stage2-polished-deterministic-reference.v1', status=solver.status_name(status),
        optimal=status == cp_model.OPTIMAL, objective_ticks=None, best_bound_ticks=solver.best_objective_bound,
        solver='OR-Tools CP-SAT', solver_version=ortools.__version__, python=platform.python_version(),
        instance_sha256=digest(instance), source_sha256=before, workers=workers, seed=seed,
        wall_limit_seconds=wall_limit, solver_wall_seconds=solver.wall_time,
        build_and_solve_wall_seconds=time.perf_counter()-started, process_cpu_seconds=time.process_time()-cpu,
        counts=dict(operations=len(variables['operations']), moves=len(variables['movements']),
            agv_arc_bits=len(variables['arcs']), pruned_agv_arcs=variables['pruned_agv_arcs'],
            worker_order_bits=variables['worker_order_bits']),
        incumbent_history=history, solver_response=solver.response_stats(), model_stats=model.model_stats(),
        scope=deepcopy(instance['reference_scope']), flagship_global_gap=None, final_heldout_tapes_used=0,
        physical_quantum_calls=0, veloxq_calls=0)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        starts = {name: solver.value(var) for name, var in variables['starts'].items()}
        ordered = sorted(range(1, len(variables['operations'])+1), key=lambda n: starts[variables['operations'][n-1]['id']])
        path = [0]+ordered+[0]
        schedule = dict(operations=starts, moves={m['id']:dict(start=solver.value(variables['dispatch'][m['id']]),
            pickup=solver.value(variables['pickup'][m['id']]), drop=solver.value(variables['drop'][m['id']])) for m in variables['movements']},
            agv_successors={a:b for (a,b),lit in variables['arcs'].items() if solver.value(lit)},
            worker_successors=dict(zip(path,path[1:])))
        raw = to_trace(instance, variables['operations'], variables['movements'], schedule)
        trace, changes = normalize_future_reservations(raw)
        physical, identity = checked_witness(instance, trace)
        report.update(objective_ticks=solver.value(variables['makespan']), raw_trace=raw, trace=trace,
                      normalization_changes=changes, physical_check=physical, identity_check=identity)
    report['sources_stable_during_run'] = before == source_hashes()
    if not report['sources_stable_during_run']:
        raise RuntimeError('Reference sources changed during search')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--incumbent', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--wall-limit', type=float, default=300)
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--seed', type=int, default=2026)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    instance = json.loads(args.instance.read_text())
    incumbent = json.loads(args.incumbent.read_text()) if args.incumbent else None
    (args.output/'instance.json').write_text(json.dumps(instance, indent=2)+'\n')
    result = solve(instance, incumbent, args.wall_limit, args.workers, args.seed, args.output/'incumbents.jsonl')
    for key in ('raw_trace', 'trace'):
        if key in result:
            (args.output/(key+'.json')).write_text(json.dumps(result.pop(key), indent=2)+'\n')
    (args.output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status', 'optimal', 'objective_ticks', 'best_bound_ticks', 'process_cpu_seconds', 'sources_stable_during_run')}))


if __name__ == '__main__':
    main()
