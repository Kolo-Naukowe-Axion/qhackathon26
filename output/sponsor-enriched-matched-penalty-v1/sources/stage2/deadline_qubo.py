"""Exact decision QUBO: can the declared manufacturing cell meet every deadline?

This changes the question, not its answer: no makespan register, soft objective,
candidate cap, reference plan, or heuristic witness is needed. Zero energy is
equivalent to raw schedule feasibility plus the hard terminal due dates and an
optional completion cap. A nonzero heuristic return is not an infeasibility proof.
"""
from dataclasses import dataclass
from copy import deepcopy

from .window_qubo import assignments, check_plan, conflict_reasons, digest, validate
from .window_reduction import arc_prune


class DeadlineInfeasible(ValueError):
    """Exact preprocessing certificate; never used for guards or solver failures."""

    def __init__(self, certificate):
        self.certificate = certificate
        super().__init__(certificate['reason'])


def query_record(problem, cap=None):
    cap = problem['horizon'] if cap is None else cap
    if type(cap) is not int or not 0 <= cap <= problem['horizon']:
        raise ValueError('Completion cap must be an integer within the original horizon')
    predecessors = {p for op in problem['operations'] for p in op['predecessors']}
    deadlines = {op['id']: op['due'] for op in problem['operations']
                 if op['id'] not in predecessors}
    return dict(problem_sha256=digest(problem), completion_cap=cap,
                terminal_deadlines=deadlines,
                semantics='All original operations mandatory; original calendars/grid; hard terminal deadlines')


@dataclass
class DeadlineQUBO:
    problem: dict
    query: dict
    variables: list
    groups: dict
    linear: list
    quadratic: dict
    offset: int
    reduction: dict
    incompatibilities: int
    penalty: int = 1

    def energy(self, bits):
        if len(bits) != len(self.linear) or any(x not in (0, 1) for x in bits):
            raise ValueError('One binary value per variable required')
        return self.offset + sum(c*x for c, x in zip(self.linear, bits)) + sum(
            c*bits[i]*bits[j] for (i, j), c in self.quadratic.items())

    def decode(self, bits):
        energy = self.energy(bits)
        if any(sum(bits[i] for i in group) != 1 for group in self.groups.values()):
            return dict(valid=False, query_feasible=False, issues=['one_hot_domain'], energy=energy)
        plan = [row for row, bit in zip(self.variables, bits) if bit]
        checked = check_plan(self.problem, plan)
        issues = list(checked['issues'])
        if max(row['end'] for row in plan) > self.query['completion_cap']:
            issues.append('query_completion_cap')
        for row in plan:
            due = self.query['terminal_deadlines'].get(row['operation'])
            if due is not None and row['end'] > due:
                issues.append('query_terminal_deadline')
        return dict(checked, raw_valid=checked['valid'], valid=not issues,
                    query_feasible=not issues, issues=issues, energy=energy, plan=plan)

    def encode(self, plan):
        by_operation = {row['operation']: row for row in plan}
        if len(by_operation) != len(plan) or set(by_operation) != set(self.groups):
            raise ValueError('Exactly one row per required operation expected')
        keys = ('operation', 'machine', 'worker', 'start', 'end', 'attended_end', 'hall')
        bits = [0] * len(self.linear)
        for name, group in self.groups.items():
            row = by_operation[name]
            matches = [i for i in group if all(self.variables[i][k] == row[k] for k in keys)]
            if len(matches) != 1:
                raise ValueError('Plan assignment is outside the exact query domain')
            bits[matches[0]] = 1
        return bits

    def metadata(self):
        coefficients = self.linear + list(self.quadratic.values())
        return dict(schema='qfactoria-deadline-decision-qubo.v1', query=self.query,
                    query_sha256=digest(self.query), variables=len(self.linear),
                    couplers=len(self.quadratic), one_hot_groups={k: len(v) for k, v in self.groups.items()},
                    incompatible_pairs=self.incompatibilities, coefficient_min=min(coefficients),
                    coefficient_max=max(coefficients), makespan_register_variables=0,
                    reduction=self.reduction, objective='Unit feasibility penalties only; zero iff query feasible',
                    proof='Sum of integer squares and binary conflict products is nonnegative. '
                          'It is zero iff exactly one legal assignment is selected per operation, '
                          'with no original constraint conflict and all hard query limits satisfied.',
                    qualification='Preserves query-feasible schedules, not the original soft-objective landscape. '
                                  'A nonzero heuristic return does not prove infeasibility.')


def compile_deadline(problem, cap=None, support_pruning=True, max_variables=12000,
                     max_pair_checks=10_000_000, max_couplers=1_000_000):
    validate(problem)
    for limit in (max_variables, max_pair_checks, max_couplers):
        if type(limit) is not int or limit < 1:
            raise ValueError('Positive integer construction limits required')
    query = query_record(problem, cap)
    domains = {}
    unary_count = 0
    for op in problem['operations']:
        raw = assignments(problem, op)
        unary_count += len(raw)
        domains[op['id']] = [row for row in raw
            if row['end'] <= query['completion_cap']
            and row['end'] <= query['terminal_deadlines'].get(op['id'], problem['horizon'])]
    empty = [name for name, rows in domains.items() if not rows]
    if empty:
        raise DeadlineInfeasible(dict(reason='Empty exact query domain', groups=empty,
                                      query=query, proof='A mandatory operation has no unary query-legal assignment'))
    before_count = sum(map(len, domains.values()))
    if before_count > max_variables:
        raise ValueError('Deadline compiler variable guard exceeded before pairwise processing')
    if before_count * (before_count-1) // 2 > max_pair_checks:
        raise ValueError('Deadline compiler pair-check guard exceeded before support processing')
    reduction = dict(method='query_unary_only', before=sum(map(len, domains.values())),
                     after=sum(map(len, domains.values())))
    if support_pruning:
        try:
            domains, reduction = arc_prune(problem, domains)
        except ValueError as error:
            if not str(error).startswith('Support pruning proved infeasible mandatory group:'):
                raise
            raise DeadlineInfeasible(dict(reason=str(error), query=query,
                proof='Exact binary support propagation empties a mandatory domain')) from error
    reduction = dict(reduction, original_unary_assignments=unary_count)
    variables, groups = [], {}
    for name, rows in domains.items():
        groups[name] = list(range(len(variables), len(variables)+len(rows)))
        variables.extend(rows)
    quadratic = {}
    for group in groups.values():
        for k, i in enumerate(group):
            for j in group[k+1:]:
                quadratic[i, j] = 2
                if len(quadratic) > max_couplers:
                    raise ValueError('Deadline compiler coupler guard exceeded')
    operations = {op['id']: op for op in problem['operations']}
    incompatible = 0
    for i, row in enumerate(variables):
        for j in range(i+1, len(variables)):
            if row['operation'] != variables[j]['operation'] and conflict_reasons(
                    problem, row, variables[j], operations):
                quadratic[i, j] = 1
                incompatible += 1
                if len(quadratic) > max_couplers:
                    raise ValueError('Deadline compiler coupler guard exceeded')
    return DeadlineQUBO(deepcopy(problem), query, variables, groups, [-1]*len(variables),
                        quadratic, len(groups), reduction, incompatible)
