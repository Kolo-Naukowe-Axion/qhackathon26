"""Solution-independent exact binary-CSP support pruning for scheduling domains.

Every mandatory operation must choose one candidate. A candidate without any
compatible candidate in another mandatory group cannot occur in a feasible
schedule. Repeating this rule preserves ALL feasible schedules, not just an
incumbent/optimum. It may prove infeasibility, but never solves the objective.
"""
from collections import deque
import time


def arc_prune(problem,domains):
    from .window_qubo import conflict_reasons
    began=time.perf_counter();names=list(domains);ops={o['id']:o for o in problem['operations']}
    support={};checks=0
    for ai,a in enumerate(names):
        for b in names[ai+1:]:
            ab=[0]*len(domains[a]);ba=[0]*len(domains[b])
            for i,x in enumerate(domains[a]):
                for j,y in enumerate(domains[b]):
                    checks+=1
                    if not conflict_reasons(problem,x,y,ops):ab[i]|=1<<j;ba[j]|=1<<i
            support[a,b]=ab;support[b,a]=ba
    live={a:(1<<len(domains[a]))-1 for a in names};queue=deque((a,b)for a in names for b in names if a!=b);removed=[]
    while queue:
        a,b=queue.popleft();before=live[a]
        for i,mask in enumerate(support[a,b]):
            if live[a]&(1<<i)and not mask&live[b]:
                live[a]&=~(1<<i);removed.append(dict(group=a,index=i,unsupported_group=b,remaining_support_mask=live[b]))
        if not live[a]:raise ValueError('Support pruning proved infeasible mandatory group:'+a)
        if before!=live[a]:queue.extend((other,a)for other in names if other!=a and other!=b)
    reduced={a:[row for i,row in enumerate(domains[a])if live[a]&(1<<i)]for a in names}
    return reduced,dict(method='binary_arc_consistency',before=sum(map(len,domains.values())),after=sum(map(len,reduced.values())),
        pair_checks=checks,removed=removed,wall_seconds=time.perf_counter()-began,
        objective_used=False,incumbent_used=False,scope='All feasible declared discrete schedules preserved. No infeasible-state energy preservation is claimed.')
