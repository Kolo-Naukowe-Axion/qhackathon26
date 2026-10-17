"""Boundary-frozen, explicitly restricted concurrent-start scheduling QUBOs."""
from .qubo import select


def overlap(a,b):
    return a["start"]<b["end"] and b["start"]<a["end"]


def choose(offers,instance,active,tick,grid_cap,priorities,method="greedy",seed=0):
    candidates=[];conflicts=[];capacities={};base=instance["energy"]["base_load_kw"]
    times={tick}
    future_caps={tick:grid_cap}
    for stage in instance["uncertainty_stages"]:
        for outcome in stage["outcomes"]:
            for ev in outcome["events"]:
                if ev["type"]=="grid_derating" and tick<ev["start"]:
                    times.add(ev["start"]);future_caps[ev["start"]]=min(future_caps.get(ev["start"],float("inf")),ev["grid_cap_kw"])
    for t in sorted(times):
        if t>max((op["end"] for op in offers),default=tick):continue
        occupied=base+8+sum(op["power_kw"] for op in active if op["end"]>t)
        capacities[f"power@{t}"]=max(0,round(100*(future_caps[t]-occupied)))
    lo=min(priorities,default=0);hi=max(priorities,default=0)
    for j,op in enumerate(offers):
        reward=(1+len(op["unit_ids"]))*100+(hi-priorities[j])/(1+hi-lo)*100
        candidates.append(dict(id=f"C{j}",reward=reward,
            resources={name:round(op["power_kw"]*100) if op["end"]>int(name.split("@")[1]) else 0 for name in capacities}))
    for j,a in enumerate(offers):
        for k in range(j):
            b=offers[k];bad=a["machine_id"]==b["machine_id"] or bool(set(a["unit_ids"])&set(b["unit_ids"])) or bool(set(a["tool_ids"])&set(b["tool_ids"])) or bool(set(a["worker_ids"])&set(b["worker_ids"]))
            for x in a["worker_intervals"]:
                for y in b["worker_intervals"]:
                    if x["worker_id"]==y["worker_id"] and overlap(x,y):bad=True
            if bad:conflicts.append((f"C{k}",f"C{j}"))
    result=select(candidates,conflicts,capacities,method=method,seed=seed,
                  sweeps=100,restarts=4)
    indices=[int(cid[1:]) for cid in result["selected"]]
    return indices,dict(candidates=candidates,conflicts=conflicts,capacities=capacities,result=result)
