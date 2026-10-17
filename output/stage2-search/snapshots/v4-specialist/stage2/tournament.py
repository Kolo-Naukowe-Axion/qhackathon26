"""Budgeted, paired factory-policy measurements on explicitly declared tapes."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import hashlib
import itertools
import json
import math
from pathlib import Path
import statistics
import time


def evaluate(task):
    from .spec import build
    from .engine import run
    from .check import check_trace
    if task.get("solver_variant")=="advanced":
        from .advanced import run
    elif task.get("solver_variant")=="mpc":
        from .mpc import run
    elif task.get("solver_variant")=="specialist":
        from .specialist import run
    start=time.perf_counter();config=task["config"];weights=task["weights"]
    trace=run(build(**config),weights,**task.get("planning",{}));check=check_trace(trace)
    decisions=trace["qubo_decisions"]
    return dict(task_id=task["task_id"],policy_id=task["policy_id"],config=config,weights=weights,
        valid=check["valid"],issues=check["issues"][:10],metrics=trace["metrics"],
        qubo=dict(calls=len(decisions),coupled_calls=sum(d["result"]["qubo"]["couplers"]>0 for d in decisions),
            max_bits=max((d["result"]["qubo"]["variables"] for d in decisions),default=0),
            qaoa_calls=sum(d["result"].get("quantum_algorithm_simulated",False) for d in decisions),
            repairs=sum(d["result"].get("repaired",False) for d in decisions),
            decode_mismatches=sum(set(d["committed"])!=set(d["result"]["selected"]) for d in decisions)),
        planning_wall_seconds=trace.get("planning",{}).get("wall_seconds",0),
        planning=task.get("planning"),solver_variant=task.get("solver_variant","base"),
        wall_seconds=time.perf_counter()-start)


def summarize(rows):
    groups={}
    for r in rows:groups.setdefault((r["policy_id"],r["config"]["orders"]),[]).append(r)
    summaries=[]
    for (pid,n),rs in groups.items():
        valid=[r for r in rs if r["valid"]]
        summaries.append(dict(policy_id=pid,orders=n,runs=len(rs),valid=len(valid),weights=rs[0]["weights"],
            mean_shipped=statistics.mean(r["metrics"]["shipped"] for r in rs),
            complete_runs=sum(r["metrics"]["all_orders_fulfilled"] and r["valid"] for r in rs),
            mean_unfulfilled=statistics.mean(r["metrics"]["orders"]-r["metrics"]["shipped"] for r in rs),
            mean_tardiness_minutes=statistics.mean(r["metrics"]["total_tardiness_ticks"]*(1 if r["config"].get("profile","full")!="coarse" else 15) for r in rs),
            mean_total_cost=statistics.mean(r["metrics"]["total_cost"] for r in rs),
            max_qubo_bits=max(r["qubo"]["max_bits"] for r in rs),
            cpu_simulation_seconds=sum(r["wall_seconds"] for r in rs)))
    return sorted(summaries,key=lambda r:(r["orders"],r["runs"]-r["valid"],r["mean_unfulfilled"],r["mean_tardiness_minutes"],r["mean_total_cost"]))


def grid(orders,seeds,wips,modes,leases,selectors):
    policies=[]
    for w,m,l,s in itertools.product(wips,modes,leases,selectors):
        policies.append(dict(id=f"w{w}-{m}-lease{l}-{s}",weights=dict(wip_limit=w,mode=m,lease_calibration=bool(l),selector=s)))
    tasks=[]
    for n,p,seed in itertools.product(orders,policies,seeds):
        tasks.append(dict(task_id=len(tasks),policy_id=p["id"],weights=p["weights"],config=dict(orders=n,seed=seed,profile="full",horizon=5760)))
    return tasks


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--orders",default="3,8,12,16,24")
    p.add_argument("--seeds",default="0,1,2,3")
    p.add_argument("--wips",default="1,2,3,4,6,8")
    p.add_argument("--modes",default="eco,standard,turbo")
    p.add_argument("--leases",default="0,1")
    p.add_argument("--selectors",default="priority")
    p.add_argument("--workers",type=int,default=4)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--tasks",type=Path)
    p.add_argument("--max-seconds",type=float,default=3600)
    p.add_argument("--solver-variant",choices=("base","advanced","mpc","specialist"),default="base")
    a=p.parse_args();ints=lambda x:list(map(int,x.split(",")))
    tasks=json.loads(a.tasks.read_text()) if a.tasks else grid(ints(a.orders),ints(a.seeds),ints(a.wips),a.modes.split(","),ints(a.leases),a.selectors.split(","))
    if a.solver_variant!="base":
        for task in tasks:task.update(solver_variant=a.solver_variant,policy_id=a.solver_variant+"/"+task["policy_id"])
    a.output.mkdir(parents=True,exist_ok=True)
    if (a.output/"measurements.jsonl").exists():raise ValueError("Choose a new output directory to preserve measurements")
    protocol=dict(schema="stage2-tournament.v1",tasks=tasks,workers=a.workers,wall_limit_seconds=a.max_seconds,
        seed_role="training unless explicitly declared otherwise in task file",source_snapshot=str(Path(__file__).resolve().parents[1]))
    protocol["tasks_sha256"]=hashlib.sha256(json.dumps(tasks,sort_keys=True).encode()).hexdigest()
    (a.output/"protocol.json").write_text(json.dumps(protocol,indent=2)+"\n")
    start=time.perf_counter();rows=[]
    with (a.output/"measurements.jsonl").open("w") as stream,ProcessPoolExecutor(max_workers=a.workers) as pool:
        futures={pool.submit(evaluate,t):t for t in tasks}
        for f in as_completed(futures):
            row=f.result();rows.append(row);stream.write(json.dumps(row)+"\n");stream.flush()
            if len(rows)%max(1,a.workers)==0:
                print(json.dumps(dict(done=len(rows),total=len(tasks),invalid=sum(not r["valid"] for r in rows),elapsed=round(time.perf_counter()-start,2))),flush=True)
            if time.perf_counter()-start>a.max_seconds:
                for pending in futures:pending.cancel()
                # Already running bounded simulations finish before the executor exits.
                break
    summaries=summarize(rows)
    (a.output/"summary.json").write_text(json.dumps(dict(rows=summaries,completed=len(rows),requested=len(tasks),
        wall_seconds=time.perf_counter()-start),indent=2)+"\n")
    print(json.dumps(dict(completed=len(rows),requested=len(tasks),elapsed=time.perf_counter()-start,best_by_load=[r for j,r in enumerate(summaries) if j==0 or summaries[j-1]["orders"]!=r["orders"]]),indent=2))


if __name__=="__main__":main()
