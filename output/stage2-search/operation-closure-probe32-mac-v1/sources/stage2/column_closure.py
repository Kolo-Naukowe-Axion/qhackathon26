"""Minimal resource/BOM conflict closure instead of unrelated neighborhood fill."""


def propose_closure(q,incumbent,rng,graph,width=7):
    current={name:next(i for i in q.groups[name]if incumbent[i])for name in q.columns}
    owner={i:name for name,group in q.groups.items()if name!='@makespan'for i in group}
    selected_bits=set(current.values())
    names=list(current)
    rng.shuffle(names)
    if rng.random()<.7:
        names.sort(key=lambda name:-(q.linear[current[name]]+q.penalty))
    for root in names[:12]:
        targets=[i for i in q.groups[root]if i!=current[root]]
        rng.shuffle(targets)
        if rng.random()<.8:
            targets.sort(key=lambda i:(q.linear[i]+q.penalty,q.variables[i]['end']))
        for target in targets[:24]:
            chosen={root:target}
            pending={owner[i]for i in graph[target]&selected_bits}-{root}
            failed=False
            while pending:
                if len(chosen)+len(pending)>width:
                    failed=True
                    break
                name=min(pending)
                pending.remove(name)
                candidates=[i for i in q.groups[name]if i!=current[name]and target not in graph[i]]
                scored=[]
                for i in candidates:
                    blockers={owner[j]for j in graph[i]&selected_bits}-set(chosen)-{name}
                    if len(set(chosen)|pending|blockers|{name})>width:
                        continue
                    # First avoid contradictions with selected alternatives,
                    # then minimize further destruction and timing displacement.
                    score=(sum(j in graph[i]for j in chosen.values()),len(blockers-pending),
                           abs(q.variables[i]['end']-q.variables[current[name]]['end']))
                    scored.append((score,rng.random(),i,blockers))
                if not scored:
                    failed=True
                    break
                scored.sort()
                _,_,choice,blockers=scored[0]
                chosen[name]=choice
                pending.update(blockers-set(chosen))
            if not failed and len(chosen)<=width:
                return chosen
    return None
