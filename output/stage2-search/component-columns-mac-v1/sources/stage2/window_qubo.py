"""Complete finite-window scheduling QUBO, separate from frozen dispatch evidence.

Every operation is assigned a machine, qualified worker and future start time.
Precedence, machine/worker occupation, worker hall travel and makespan linking
are quadratic penalties. Calendars and static eligibility prune individual
domains exactly. Part transport is an uncapacitated, machine-dependent minimum
lag; AGV contention, buffers, batching, quality and energy are outside
this bounded model. Optional metric family changeovers occupy machines only;
human setup crews remain outside it. It is not the complete flagship factory.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import random
import time


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def available(windows, start, end):
    return any(a <= start and end <= b for a, b in windows)


def can_walk(worker, start, end, duration):
    return duration == 0 or any(max(start, a) + duration <= min(end, b)
                                for a, b in worker['available'])


def validate(problem):
    h, grid = problem['horizon'], problem['grid']
    if type(h) is not int or type(grid) is not int or not 0 < grid <= h:
        raise ValueError('Positive integer horizon and start grid required')
    machines, workers = problem['machines'], problem['workers']
    ids = [op['id'] for op in problem['operations']]
    if not machines or not workers or not ids or len(set(ids)) != len(ids) or '@makespan' in ids:
        raise ValueError('Nonempty unique operation IDs required')
    reached = set()
    while len(reached) < len(ids):
        new = {o['id'] for o in problem['operations'] if set(o['predecessors']) <= reached}
        if not new - reached:
            raise ValueError('Precedence graph is cyclic or references an unknown operation')
        reached |= new
    for op in problem['operations']:
        if not op['durations'] or type(op['release']) is not int or op['release'] < 0 or type(op['due']) is not int or type(op.get('weight', 1)) is not int or op.get('weight', 1) < 1:
            raise ValueError('Operation domain/release/weight invalid')
        if op['attendance'] not in ('full', 'start') or type(op.get('start_attendance', 1)) is not int or op.get('start_attendance', 1) < 1:
            raise ValueError('Attendance must be full or positive start attendance')
        if any(m not in machines or type(d) is not int or d < 1 for m, d in op['durations'].items()):
            raise ValueError('Positive integer processing times on known machines required')
        if any(not isinstance(w['skills'], list) for w in workers.values()):
            raise ValueError('Worker skills must be lists')
        if any(m not in op['durations'] or type(t) is not int or t < 0 for m,t in op.get('machine_release',{}).items()):
            raise ValueError('Machine-dependent initial releases must name an eligible machine and integer time')
    for resource in [*machines.values(), *workers.values()]:
        if not resource['available'] or any(type(a) is not int or type(b) is not int or a < 0 or b <= a
                                             for a, b in resource['available']):
            raise ValueError('Resource calendars need positive half-open integer intervals')
        if any(b>=c for (a,b),(c,d)in zip(resource['available'],resource['available'][1:])):
            raise ValueError('Calendar windows must be sorted and disjoint; merge touching intervals')
    if any(type(problem['transport_lags'][a][b]) is not int or problem['transport_lags'][a][b]<0 for a in machines for b in machines):
        raise ValueError('Complete nonnegative integer transport-lag matrix required')
    if type(problem['worker_travel']) is not int or problem['worker_travel'] < 0:
        raise ValueError('Worker hall travel must be nonnegative integer')
    if problem.get('machine_setups'):
        setup=problem['machine_setups'];families=set(setup)
        if any(o.get('family')not in families for o in problem['operations']):raise ValueError('Setup family required for every operation')
        if any(type(setup[a].get(b))is not int or setup[a][b]<0 or(a==b and setup[a][b]!=0)for a in families for b in families):raise ValueError('Complete nonnegative setup matrix with zero diagonal required')
        if any(setup[a][c]>setup[a][b]+setup[b][c]for a in families for b in families for c in families):raise ValueError('Pairwise compact setup encoding requires directed triangle inequality')
        if any(m['available']!=[[0,h]]for m in machines.values()):raise ValueError('Compact machine-only setups currently require uninterrupted machine availability')
        if any(f not in families for f in problem.get('machine_initial_family',{}).values()):raise ValueError('Known initial setup family required')
    return problem


def setup_time(problem,first_family,second_family):
    return problem.get('machine_setups',{}).get(first_family,{}).get(second_family,0)


def assignments(problem, op):
    """Exact unary-domain pruning; no interaction between operations is removed."""
    out = []
    for machine, duration in sorted(op['durations'].items()):
        hall = problem['machines'][machine]['hall']
        for wid, worker in sorted(problem['workers'].items()):
            if op['skill'] not in worker['skills']:
                continue
            for start in range(0, problem['horizon'] + 1, problem['grid']):
                end = start + duration
                attended_end = end if op['attendance'] == 'full' else start + min(duration, op['start_attendance'])
                walk = problem['worker_travel'] if hall != worker['initial_hall'] else 0
                initial_setup=setup_time(problem,problem.get('machine_initial_family',{}).get(machine),op.get('family'))
                if start < max(op['release'], op.get('machine_release',{}).get(machine,0), worker.get('ready', 0),initial_setup) or end > problem['horizon']:
                    continue
                if not available(problem['machines'][machine]['available'], start, end):
                    continue
                if not available(worker['available'], start, attended_end):
                    continue
                if not can_walk(worker, worker.get('ready', 0), start, walk):
                    continue
                out.append(dict(operation=op['id'], machine=machine, worker=wid, start=start,
                                end=end, attended_end=attended_end, hall=hall))
    return out


def conflict_reasons(problem, a, b, operations):
    reasons = []
    if a['operation'] == b['operation']:
        return reasons
    if a['machine'] == b['machine'] and a['start'] < b['end'] and b['start'] < a['end']:
        reasons.append('machine_occupation')
    if a['machine']==b['machine']and problem.get('machine_setups'):
        first,second=sorted((a,b),key=lambda x:(x['start'],x['operation']))
        gap=setup_time(problem,operations[first['operation']]['family'],operations[second['operation']]['family'])
        if gap>0 and first['end']+gap>second['start']:reasons.append('machine_family_changeover')
    if a['worker'] == b['worker']:
        first, second = sorted((a, b), key=lambda x: (x['start'], x['operation']))
        if second['start'] < first['attended_end']:
            reasons.append('worker_occupation')
        elif first['hall'] != second['hall'] and not can_walk(
                problem['workers'][a['worker']], first['attended_end'], second['start'], problem['worker_travel']):
            reasons.append('worker_hall_travel')
    for prior, following in ((a, b), (b, a)):
        if prior['operation'] in operations[following['operation']]['predecessors']:
            lag = problem['transport_lags'][prior['machine']][following['machine']]
            if prior['end'] + lag > following['start']:
                reasons.append('precedence_and_transport_lag')
    return reasons


@dataclass
class WindowQUBO:
    problem: dict
    variables: list
    groups: dict
    linear: list
    quadratic: dict
    offset: int
    penalty: int
    objective_bound: int
    reasons: dict
    reduction: dict = field(default_factory=dict)

    def energy(self, bits):
        if len(bits) != len(self.variables) or any(x not in (0, 1) for x in bits):
            raise ValueError('One binary value per encoded variable required')
        return self.offset + sum(v*x for v, x in zip(self.linear, bits)) + sum(
            value*bits[i]*bits[j] for (i, j), value in self.quadratic.items())

    def decode(self, bits):
        selected = [i for i, x in enumerate(bits) if x]
        if any(sum(bits[i] for i in group) != 1 for group in self.groups.values()):
            return dict(valid=False, issues=['one_hot_domain'], selected=selected)
        plan = [self.variables[i] for i in selected if self.variables[i]['operation'] != '@makespan']
        end = next(self.variables[i]['start'] for i in selected if self.variables[i]['operation'] == '@makespan')
        checked = check_plan(self.problem, plan)
        if checked['valid'] and end < checked['makespan']:
            checked = dict(checked, valid=False, issues=['makespan_link'])
        return dict(checked, plan=plan, encoded_makespan=end,
                    energy=self.energy(bits), selected=selected)

    def metadata(self):
        counts = defaultdict(int)
        for labels in self.reasons.values():
            for label in labels:
                counts[label] += 1
        return dict(schema='stage2-planning-window-qubo.v1', problem_sha256=digest(self.problem),
                    variables=len(self.variables), assignment_variables=sum(len(g) for k, g in self.groups.items() if k != '@makespan'),
                    makespan_variables=len(self.groups['@makespan']), couplers=len(self.quadratic),
                    penalty=self.penalty, feasible_objective_upper_bound=self.objective_bound, reduction=self.reduction,
                    interaction_counts=dict(counts), one_hot_groups={k: len(v) for k, v in self.groups.items()},
                    convention='upper_triangular_once', domain='complete_declared_discrete_window',
                    setup_scope='machine-only directed-metric family changeovers; no human setup crew'if self.problem.get('machine_setups')else'no changeovers',
                    proof='If feasible, nonnegative objective <=B and P=B+1 force every ground state to satisfy all one-hot, resource, precedence and makespan constraints.')


def compile_qubo(problem, max_variables=2500, support_pruning=False):
    validate(problem)
    operations = {o['id']: o for o in problem['operations']}
    variables, groups = [], {}
    successors = {p for o in operations.values() for p in o['predecessors']}
    cost, bound = [], 0
    domains={oid:assignments(problem,op)for oid,op in operations.items()};reduction={}
    if support_pruning:
        from .window_reduction import arc_prune
        domains,reduction=arc_prune(problem,domains)
    for oid, op in operations.items():
        domain = domains[oid]
        if not domain:
            raise ValueError('Empty unary domain: ' + oid)
        groups[oid] = list(range(len(variables), len(variables)+len(domain)))
        variables.extend(domain)
        values = [(problem['horizon']+1)*op.get('weight', 1)*max(0, a['end']-op['due'])
                  if oid not in successors else 0 for a in domain]
        cost.extend(values); bound += max(values)
    ends = sorted({a['end'] for a in variables})
    groups['@makespan'] = list(range(len(variables), len(variables)+len(ends)))
    variables.extend(dict(operation='@makespan', start=t) for t in ends)
    cost.extend(ends); bound += max(ends)
    if len(variables) > max_variables:
        raise ValueError(f'Explicit local memory guard: {len(variables)} > {max_variables} variables')
    penalty = bound+1
    linear = list(cost); quadratic = {}; reasons = {}; offset = penalty*len(groups)
    for indices in groups.values():
        for k, i in enumerate(indices):
            linear[i] -= penalty
            for j in indices[k+1:]:
                quadratic[i, j] = 2*penalty
    real = sum(len(g) for k, g in groups.items() if k != '@makespan')
    for i in range(real):
        for j in range(i+1, real):
            labels = conflict_reasons(problem, variables[i], variables[j], operations)
            if labels:
                quadratic[i, j] = quadratic.get((i, j), 0) + penalty*len(labels)
                reasons[i, j] = labels
        for j in groups['@makespan']:
            if variables[i]['end'] > variables[j]['start']:
                quadratic[i, j] = penalty
                reasons[i, j] = ['makespan_link']
    return WindowQUBO(problem, variables, groups, linear, quadratic, offset, penalty, bound, reasons,reduction)


def check_plan(problem, plan):
    """Independent raw-operation schedule checks; never consult QUBO coefficients."""
    issues = []
    expected = {o['id']: o for o in problem['operations']}
    by_id = {a.get('operation'): a for a in plan}
    if len(by_id) != len(plan) or set(by_id) != set(expected):
        return dict(valid=False, issues=['operation_set'])
    for oid, row in by_id.items():
        op = expected[oid]; machine = problem['machines'].get(row.get('machine')); worker = problem['workers'].get(row.get('worker'))
        if machine is None or worker is None or row.get('machine') not in op['durations']:
            return dict(valid=False,issues=['unknown_assignment:'+oid])
        s, e = row['start'], row['end']; attended = e if op['attendance'] == 'full' else s+min(op['durations'][row['machine']], op['start_attendance'])
        if type(s) is not int or s % problem['grid'] or s < max(op['release'],op.get('machine_release',{}).get(row['machine'],0)) or e != s+op['durations'][row['machine']] or e > problem['horizon']:
            issues.append('time_domain:' + oid)
        if op['skill'] not in worker['skills'] or row['attended_end'] != attended or row['hall'] != machine['hall']:
            issues.append('skill_or_attendance:' + oid)
        if not available(machine['available'], s, e) or not available(worker['available'], s, attended):
            issues.append('calendar:' + oid)
        for prior in op['predecessors']:
            p = by_id[prior]
            if p['end'] + problem['transport_lags'][p['machine']][row['machine']] > s:
                issues.append('precedence:' + oid)
    for mid in problem['machines']:
        rows = sorted((r for r in plan if r['machine'] == mid), key=lambda r: r['start'])
        if any(a['end'] > b['start'] for a, b in zip(rows, rows[1:])):
            issues.append('machine_overlap:' + mid)
        previous_end=0;family=problem.get('machine_initial_family',{}).get(mid)
        for row in rows:
            nextfamily=expected[row['operation']].get('family');gap=setup_time(problem,family,nextfamily)
            if previous_end+gap>row['start']:issues.append('machine_changeover:'+mid)
            family=nextfamily;previous_end=row['end']
    for wid, worker in problem['workers'].items():
        rows = sorted((r for r in plan if r['worker'] == wid), key=lambda r: r['start'])
        end, hall = worker.get('ready', 0), worker['initial_hall']
        for row in rows:
            walk = problem['worker_travel'] if hall != row['hall'] else 0
            if end > row['start'] or not can_walk(worker, end, row['start'], walk):
                issues.append('worker_path:' + wid)
            end, hall = row['attended_end'], row['hall']
    successors = {p for o in expected.values() for p in o['predecessors']}
    tardy = sum(expected[oid].get('weight', 1)*max(0, a['end']-expected[oid]['due'])
                for oid, a in by_id.items() if oid not in successors)
    makespan = max(a['end'] for a in plan)
    return dict(valid=not issues, issues=issues, weighted_terminal_tardiness=tardy,
                makespan=makespan, objective=(problem['horizon']+1)*tardy+makespan)


def solve_cp(problem, seconds=20, workers=4):
    """Native interval CP model of the RAW problem, no compiled QUBO/conflict list."""
    from ortools.sat.python import cp_model
    validate(problem); began = time.perf_counter(); model = cp_model.CpModel()
    machines, workforce = list(problem['machines']), list(problem['workers'])
    halls = sorted({m['hall'] for m in problem['machines'].values()}); h = problem['horizon']
    starts, ends, attended, mids, wids, hallvars, m_use, w_use = {}, {}, {}, {}, {}, {}, {}, {}
    machine_intervals, worker_intervals = defaultdict(list), defaultdict(list)
    for op in problem['operations']:
        oid = op['id']; starts[oid] = model.new_int_var_from_domain(cp_model.Domain.from_values(list(range(0, h+1, problem['grid']))), 'start:'+oid)
        ends[oid] = model.new_int_var(1, h, 'end:'+oid); attended[oid] = model.new_int_var(1, h, 'attend:'+oid)
        mids[oid] = model.new_int_var(0, len(machines)-1, 'machine:'+oid); wids[oid] = model.new_int_var(0, len(workforce)-1, 'worker:'+oid)
        hallvars[oid] = model.new_int_var(0, len(halls)-1, 'hall:'+oid)
        # Independent table construction from raw calendars/skills, not compiler assignments.
        table = []
        for mi, mid in enumerate(machines):
            if mid not in op['durations']: continue
            d = op['durations'][mid]; mhall = problem['machines'][mid]['hall']
            for wi, wid in enumerate(workforce):
                worker = problem['workers'][wid]
                if op['skill'] not in worker['skills']: continue
                for s in range(0, h+1, problem['grid']):
                    e = s+d; a = e if op['attendance']=='full' else s+min(d, op['start_attendance'])
                    travel = problem['worker_travel'] if mhall!=worker['initial_hall'] else 0
                    initial_setup=problem.get('machine_setups',{}).get(problem.get('machine_initial_family',{}).get(mid),{}).get(op.get('family'),0)
                    if s < max(op['release'],op.get('machine_release',{}).get(mid,0),initial_setup) or s < worker.get('ready',0) or e>h: continue
                    if not any(lo<=s and e<=hi for lo,hi in problem['machines'][mid]['available']): continue
                    if not any(lo<=s and a<=hi for lo,hi in worker['available']): continue
                    if travel and not any(max(worker.get('ready',0),lo)+travel<=min(s,hi)for lo,hi in worker['available']): continue
                    table.append((s,e,a,mi,wi,halls.index(mhall)))
        if not table: return dict(status='INFEASIBLE', valid=False, scope='Empty raw unary domain')
        model.add_allowed_assignments([starts[oid],ends[oid],attended[oid],mids[oid],wids[oid],hallvars[oid]],table)
        duration=model.new_int_var(1,h,'duration:'+oid);model.add(duration==ends[oid]-starts[oid])
        ad=model.new_int_var(1,h,'attend_duration:'+oid);model.add(ad==attended[oid]-starts[oid])
        for mi,mid in enumerate(machines):
            use=model.new_bool_var('use:'+oid+':'+mid);m_use[oid,mid]=use
            model.add(mids[oid]==mi).only_enforce_if(use);model.add(mids[oid]!=mi).only_enforce_if(use.Not())
            machine_intervals[mid].append(model.new_optional_interval_var(starts[oid],duration,ends[oid],use,'m:'+oid+mid))
        for wi,wid in enumerate(workforce):
            use=model.new_bool_var('use:'+oid+':'+wid);w_use[oid,wid]=use
            model.add(wids[oid]==wi).only_enforce_if(use);model.add(wids[oid]!=wi).only_enforce_if(use.Not())
            worker_intervals[wid].append(model.new_optional_interval_var(starts[oid],ad,attended[oid],use,'w:'+oid+wid))
    for intervals in [*machine_intervals.values(),*worker_intervals.values()]:model.add_no_overlap(intervals)
    ids=list(starts)
    operations={op['id']:op for op in problem['operations']}
    for ai,a in enumerate(ids):
        for b in ids[ai+1:]:
            if problem.get('machine_setups'):
                for mid in machines:
                    before_setup=model.new_bool_var('machine_setup_order:'+a+b+mid)
                    for first,second,order in((a,b,before_setup),(b,a,before_setup.Not())):
                        gap=problem['machine_setups'][operations[first]['family']][operations[second]['family']]
                        model.add(starts[second]>=ends[first]+gap).only_enforce_if([m_use[a,mid],m_use[b,mid],order])
            different=model.new_bool_var('different_hall:'+a+b);model.add(hallvars[a]!=hallvars[b]).only_enforce_if(different);model.add(hallvars[a]==hallvars[b]).only_enforce_if(different.Not())
            for wid,worker in problem['workers'].items():
                before=model.new_bool_var('before:'+a+b+wid)
                for first,second,order in ((a,b,before),(b,a,before.Not())):
                    active=[w_use[a,wid],w_use[b,wid],order]
                    model.add(starts[second]>=attended[first]).only_enforce_if(active)
                    if problem['worker_travel']==0:continue
                    slots=[];travel=problem['worker_travel']
                    for lo,hi in worker['available']:
                        if hi-lo<travel:continue
                        slot=model.new_bool_var('walk:'+first+second+wid+str(lo));slots.append(slot)
                        model.add(attended[first]+travel<=starts[second]).only_enforce_if(slot)
                        model.add(attended[first]+travel<=hi).only_enforce_if(slot)
                        model.add(lo+travel<=starts[second]).only_enforce_if(slot)
                    model.add_bool_or([*slots,*(u.Not()for u in active),different.Not()])
    for op in problem['operations']:
        for prior in op['predecessors']:
            lag=model.new_int_var(0,h,'lag:'+prior+op['id'])
            model.add_allowed_assignments([mids[prior],mids[op['id']],lag],[(i,j,problem['transport_lags'][a][b])for i,a in enumerate(machines)for j,b in enumerate(machines)])
            model.add(starts[op['id']]>=ends[prior]+lag)
    makespan=model.new_int_var(0,h,'makespan');model.add_max_equality(makespan,list(ends.values()))
    successors={p for op in problem['operations']for p in op['predecessors']};tardies=[]
    for op in problem['operations']:
        if op['id'] in successors:continue
        late=model.new_int_var(0,h+max(0,-op['due']),'late:'+op['id']);model.add_max_equality(late,[0,ends[op['id']]-op['due']]);tardies.append(op.get('weight',1)*late)
    model.minimize((h+1)*sum(tardies)+makespan)
    solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=seconds;solver.parameters.num_search_workers=workers;solver.parameters.random_seed=19
    status=solver.solve(model);result=dict(status=solver.status_name(status),optimal=status==cp_model.OPTIMAL,bound=solver.best_objective_bound,wall_seconds=time.perf_counter()-began)
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):return result
    plan=[dict(operation=oid,machine=machines[solver.value(mids[oid])],worker=workforce[solver.value(wids[oid])],start=solver.value(starts[oid]),end=solver.value(ends[oid]),attended_end=solver.value(attended[oid]),hall=halls[solver.value(hallvars[oid])])for oid in ids]
    return dict(result,plan=plan,check=check_plan(problem,plan),objective=round(solver.objective_value))


def solve_literal_qubo(q, seconds=20, workers=4):
    """Generic energy minimization; CP sees coefficients, NOT schedule constraints."""
    from ortools.sat.python import cp_model
    if len(q.quadratic)>150000:raise ValueError('Literal-QUBO CP linearization guard:150000 couplers')
    began=time.perf_counter();model=cp_model.CpModel();bits=[model.new_bool_var(f'x{i}')for i in range(len(q.linear))]
    terms=[c*x for c,x in zip(q.linear,bits)if c]
    for (i,j),value in q.quadratic.items():
        both=model.new_bool_var(f'z{i}_{j}');model.add(both<=bits[i]);model.add(both<=bits[j]);model.add(both>=bits[i]+bits[j]-1);terms.append(value*both)
    model.minimize(q.offset+sum(terms));solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=seconds;solver.parameters.num_search_workers=workers;solver.parameters.random_seed=23
    status=solver.solve(model);result=dict(status=solver.status_name(status),optimal=status==cp_model.OPTIMAL,bound=solver.best_objective_bound,wall_seconds=time.perf_counter()-began,uses_schedule_constraints=False)
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):return result
    values=[solver.value(x)for x in bits];energy=q.energy(values)
    if not math.isclose(energy,solver.objective_value,abs_tol=1e-5):raise AssertionError('Literal QUBO energy disagreement')
    return dict(result,bits=values,energy=energy,decoded=q.decode(values))


def conditional_qubo(q, free, fixed):
    """Exact substitution, not reward redesign: E(x)=constant+E_conditional(x_F)."""
    free=list(free)
    if len(set(free))!=len(free)or set(free)|set(fixed)!=set(range(len(q.linear)))or set(free)&set(fixed):raise ValueError('Exact disjoint free/fixed partition required')
    if any(x not in (0,1)for x in fixed.values()):raise ValueError('Fixed values must be binary')
    remap={old:new for new,old in enumerate(free)};linear=[q.linear[i]for i in free];offset=q.offset+sum(q.linear[i]*x for i,x in fixed.items());quadratic={}
    for (i,j),v in q.quadratic.items():
        if i in remap and j in remap:quadratic[tuple(sorted((remap[i],remap[j])))]=v
        elif i in remap:linear[remap[i]]+=v*fixed[j]
        elif j in remap:linear[remap[j]]+=v*fixed[i]
        else:offset+=v*fixed[i]*fixed[j]
    return dict(linear=linear,quadratic=quadratic,offset=offset,free=free)
