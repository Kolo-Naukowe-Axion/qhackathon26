"""Exact order-preserving QUBOs for two or three jobs on a common route.

This deliberately tiny formulation tabulates ALL n! earliest-start permutation
costs. It does not scale to arbitrary n, encode idle times, or preserve arbitrary
independent machine orders. No optimum or reference horizon is an input.
"""

import itertools

from .stage1 import operations


def schedule_order(instance, order):
    operations(instance)
    jobs = {job["id"]: job for job in instance["jobs"]}
    if len(order) != len(jobs) or set(order) != set(jobs):
        raise ValueError("Order must include every job exactly once")
    ends = [0] * len(next(iter(jobs.values()))["operations"])
    schedule = []
    for job in order:
        previous = 0
        for machine, op in enumerate(jobs[job]["operations"]):
            start = max(ends[machine], previous)
            ends[machine] = previous = start + op["duration"]
            schedule.append(dict(job=job, machine=op["machine"], start=start, end=previous))
    return schedule


def order_from_bits(jobs, bits):
    """Topological sort of the tournament; cycles are rejected, never repaired."""
    predecessors = {job: set() for job in jobs}
    for (a, b), bit in zip(itertools.combinations(jobs, 2), bits):
        first, second = (a, b) if bit else (b, a)
        predecessors[second].add(first)
    order = []
    while len(order) < len(jobs):
        ready = [job for job in jobs if job not in order and predecessors[job] <= set(order)]
        if len(ready) != 1:
            raise ValueError("Cyclic pairwise job order")
        order.append(ready[0])
    return order


def build_sequence_qubo(instance):
    operations(instance)
    jobs = [job["id"] for job in instance["jobs"]]
    if len(jobs) not in (2, 3):
        raise ValueError("Sequence interpolation supports exactly two or three jobs")
    pairs = list(itertools.combinations(jobs, 2))
    n = len(pairs)
    costs, table = {}, []
    for order in itertools.permutations(jobs):
        bits = tuple(int(order.index(a) < order.index(b)) for a, b in pairs)
        schedule = schedule_order(instance, order)
        cost = max(row["end"] for row in schedule)
        costs[bits] = cost
        table.append(dict(order=list(order), bits=list(bits), makespan=cost))
    if n == 3:
        # The cubic coefficient is alternating parity over the truth table.
        # The two cycles 010 and 101 have opposite signs; increasing the
        # appropriate one cancels it while BOTH remain worse than every order.
        ceiling = max(costs.values()) + 1
        costs[(0, 1, 0)] = costs[(1, 0, 1)] = ceiling
        cubic = sum((-1) ** (3 - sum(bits)) * cost for bits, cost in costs.items())
        costs[(0, 1, 0)] += max(0, -cubic)
        costs[(1, 0, 1)] += max(0, cubic)
    # Boolean Mobius transform, computed with integer arithmetic.
    coefficients = [costs[tuple((mask >> i) & 1 for i in range(n))] for mask in range(1 << n)]
    for i in range(n):
        for mask in range(1 << n):
            if mask & (1 << i):
                coefficients[mask] -= coefficients[mask ^ (1 << i)]
    if n == 3 and coefficients[7] != 0:
        raise AssertionError("Cubic cancellation failed")
    return dict(schema="stage1-qubo.v1", encoding="pairwise-order", objective="makespan",
                variables=[dict(before=a, after=b) for a, b in pairs],
                linear=[coefficients[1 << i] for i in range(n)], offset=coefficients[0],
                quadratic=[[i, j, coefficients[(1 << i) | (1 << j)]]
                           for i, j in itertools.combinations(range(n), 2)
                           if coefficients[(1 << i) | (1 << j)]],
                # Serial processing is a safe bound, not a known-optimum horizon.
                horizon=sum(op["duration"] for job in instance["jobs"] for op in job["operations"]),
                instance=instance, order_costs=table,
                scope="All earliest-start common job permutations; not all feasible timed schedules",
                provenance="offline exhaustive n! cost construction; no reference answer or service execution")


def decode_sequence(model, bits):
    instance = model["instance"]
    order = order_from_bits([job["id"] for job in instance["jobs"]], bits)
    return schedule_order(instance, order)
