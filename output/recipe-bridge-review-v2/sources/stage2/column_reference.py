"""Native optional-interval reference for the identical component-column pool.

Reads raw operations/columns only: no QUBO coefficients, penalty values or
compiler conflict list. Static machine/worker interval occupation is native CP;
fixed-time travel, metric setups and BOM joins are separately derived from raw
resource definitions. This proves a RESTRICTED-pool bound, never a full-model
bound merely because the pool is small.
"""
from collections import defaultdict
import time

from .window_qubo import validate,check_plan
from .column_qubo import subproblem


def solve_column_cp(problem,columns,seconds=30,workers=4,initial_plan=None):
    from ortools.sat.python import cp_model
    validate(problem);began=time.perf_counter();model=cp_model.CpModel();ops={o['id']:o for o in problem['operations']}
    owner={};uses={};rows={};machine_intervals=defaultdict(list);worker_intervals=defaultdict(list);objective=[]
    terminal=set(ops)-{p for o in ops.values()for p in o['predecessors']};h=problem['horizon'];makespan=model.new_int_var(0,h,'makespan')
    for name,options in columns.items():
        ids={r['operation']for r in options[0]}
        if set(owner)&ids:raise ValueError('Columns must partition raw operations')
        owner.update({oid:name for oid in ids});members=[]
        for choice,plan in enumerate(options):
            use=model.new_bool_var(f'column:{name}:{choice}');uses[name,choice]=use;members.append(use);rows[name,choice]={r['operation']:r for r in plan}
            if {r['operation']for r in plan}!=ids or not check_plan(subproblem(problem,ids),plan)['valid']:
                model.add(use==0);continue
            cost=0
            for r in plan:
                oid=r['operation'];machine_intervals[r['machine']].append(model.new_optional_fixed_size_interval_var(r['start'],r['end']-r['start'],use,f'm:{name}:{choice}:{oid}'))
                worker_intervals[r['worker']].append(model.new_optional_fixed_size_interval_var(r['start'],r['attended_end']-r['start'],use,f'w:{name}:{choice}:{oid}'))
                if oid in terminal:cost+=ops[oid].get('weight',1)*max(0,r['end']-ops[oid]['due'])
                model.add(makespan>=r['end']).only_enforce_if(use)
            objective.append((h+1)*cost*use)
        model.add_exactly_one(members)
    if set(owner)!=set(ops):raise ValueError('Every operation must have a trajectory group')
    for intervals in [*machine_intervals.values(),*worker_intervals.values()]:model.add_no_overlap(intervals)
    # Build non-occupation constraints from raw fixed event times, independently.
    names=list(columns);forbidden=0
    for ai,a in enumerate(names):
        for b in names[ai+1:]:
            for ca,first in enumerate(columns[a]):
                for cb,second in enumerate(columns[b]):
                    incompatible=False
                    for x in first:
                        for y in second:
                            if x['machine']==y['machine']and problem.get('machine_setups'):
                                before,after=(x,y)if x['start']<=y['start']else(y,x)
                                change=problem['machine_setups'][ops[before['operation']]['family']][ops[after['operation']]['family']]
                                if before['end']+change>after['start']:incompatible=True
                            if x['worker']==y['worker']and x['hall']!=y['hall']:
                                before,after=(x,y)if x['start']<=y['start']else(y,x);travel=problem['worker_travel']
                                if travel and not any(max(before['attended_end'],lo)+travel<=min(after['start'],hi)for lo,hi in problem['workers'][x['worker']]['available']):incompatible=True
                            for prior,following in((x,y),(y,x)):
                                if prior['operation']in ops[following['operation']]['predecessors']:
                                    lag=problem['transport_lags'][prior['machine']][following['machine']]
                                    if prior['end']+lag>following['start']:incompatible=True
                    if incompatible:model.add(uses[a,ca]+uses[b,cb]<=1);forbidden+=1
    model.minimize(sum(objective)+makespan)
    if initial_plan is not None:
        original={r['operation']:r for r in initial_plan}
        for(name,choice),use in uses.items():model.add_hint(use,int(all(original.get(oid)==row for oid,row in rows[name,choice].items())))
    solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=seconds;solver.parameters.num_search_workers=workers;solver.parameters.random_seed=19
    status=solver.solve(model);result=dict(status=solver.status_name(status),optimal=status==cp_model.OPTIMAL,bound=solver.best_objective_bound,
        wall_seconds=time.perf_counter()-began,derived_nonoccupation_forbidden_pairs=forbidden,uses_qubo_coefficients=False,
        scope='Native raw-column-pool reference. Bound applies to this supplied restricted pool only.')
    if status not in(cp_model.FEASIBLE,cp_model.OPTIMAL):return result
    selected={name:next(choice for choice in range(len(options))if solver.value(uses[name,choice]))for name,options in columns.items()}
    plan=[r for name,choice in selected.items()for r in columns[name][choice]];checked=check_plan(problem,plan)
    if not checked['valid']or checked['objective']!=round(solver.objective_value):raise AssertionError('Native column CP did not decode to independently checked raw objective')
    return dict(result,objective=round(solver.objective_value),choices=selected,plan=plan,check=checked)
