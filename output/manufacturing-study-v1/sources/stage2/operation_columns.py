"""Break rigid trajectories into independently selectable operation columns.

Each retained row is a raw unary-feasible machine/crew/start assignment. Complete
heuristic parents are retained. Additional rows are selected by timing distance
and round-robin machine/worker diversity, never by a CP optimum or objective.
Cross-operation feasibility remains the master's job.
"""
from collections import defaultdict

from .window_qubo import assignments, digest


def operation_columns(problem, parents, cap=48, radius=180):
    columns = {}
    statistics = {}
    for op in problem['operations']:
        oid = op['id']
        anchors = [next(r for r in plan if r['operation']==oid) for plan in parents]
        pool = {digest([r]):[r] for r in anchors}
        if len(pool)>cap:
            raise ValueError('Cap must retain every parent assignment')
        starts = {r['start'] for r in anchors}
        by_mode = defaultdict(list)
        raw = assignments(problem,op)
        for row in raw:
            distance = min(abs(row['start']-start) for start in starts)
            if distance<=radius:
                by_mode[row['machine'],row['worker']].append((distance,row['start'],row))
        for key in by_mode:
            by_mode[key].sort(key=lambda t:(t[0],t[1]))
        # One next-nearest row per eligible mode per round. No mode can consume
        # the whole cap before other machine/worker alternatives are considered.
        round_index = 0
        while len(pool)<cap:
            added = False
            for mode in sorted(by_mode):
                if round_index>=len(by_mode[mode]):
                    continue
                row = by_mode[mode][round_index][2]
                pool[digest([row])] = [row]
                added = True
                if len(pool)>=cap:
                    break
            if not added:
                break
            round_index += 1
        columns[oid] = list(pool.values())
        statistics[oid] = dict(raw_rows=len(raw),parent_rows=len({digest([r]) for r in anchors}),
                               retained=len(pool),eligible_modes=len(by_mode))
    return columns,dict(method='Unary operation rows with parent retention and round-robin mode/timing diversity',
                        per_operation_cap=cap,radius=radius,groups=statistics,cp_teacher_used=False,
                        scope='Lossy finite unary-domain restriction. Precedence, resource, travel, setup and Cmax constraints remain global. No component route frozen.')
