"""Causal stationary-battery dispatch and exact fixed-load battery references.

Physical generation, load, battery actions, losses, bounds, grid caps and terminal
requirements are inherited unchanged.  The offline DP sees a saved realized load
and is explicitly not a causal controller or a global factory optimum.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
import gzip
import hashlib
import json
import math
from pathlib import Path
import time

from .advanced import AdvancedFactory
from .engine import Factory
from .check import check_trace,check_paired_causality
from .spec import build

ROOT=Path(__file__).resolve().parents[1]


def source_hashes():
    names=("stage2/energy.py","stage2/engine.py","stage2/spec.py","stage2/advanced.py",
           "stage2/check.py","stage2/dispatch.py","instances/stage2/metaltech_pressure.json")
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}


def high_ticks_before(tick,period):
    start=period//3;end=period*3//4
    days,remainder=divmod(tick,period)
    return days*(end-start)+max(0,min(remainder,end)-start)


def row_for_action(tick,load,solar,cap,soc,action,energy,period):
    """Primitive electrical bus balance for a concrete unchanged battery action."""
    day=tick%period;peak=period/3<=day<period*3/4
    net=load-solar+action["charge_kw"]-action["discharge_kw"]
    return dict(tick=tick,load_kw=load,grid_kw=max(0,net),cap_kw=cap,solar_kw=solar,
        curtailed_kw=max(0,-net),soc_before=soc,soc=soc+action["soc_delta"],battery_action=action["id"],
        tariff=energy["tariff_peak"] if peak else energy["tariff_low"],
        carbon_intensity=energy["carbon_peak"] if peak else energy["carbon_low"])


def feasible_electrical(row,energy):
    return (energy["stationary_soc_min"]<=row["soc"]<=energy["stationary_soc_capacity"] and
        0<=row["grid_kw"]<=row["cap_kw"]+1e-9 and
        0<=row["curtailed_kw"]<=row["solar_kw"]+1e-9)


class EnergyMixin:
    def __init__(self,*args,energy_policy=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.energy_policy=dict(strategy="solar-tariff",objective="cost",reserve="terminal")
        self.energy_policy.update(energy_policy or {})
        if self.energy_policy["strategy"] not in ("baseline","solar-tariff"):raise ValueError("Unknown battery strategy")
        if self.energy_policy["objective"] not in ("cost","carbon"):raise ValueError("Unknown energy objective")
        if self.energy_policy["reserve"] not in ("terminal","recovery"):raise ValueError("Unknown reserve policy")
        self.trace["provenance"]["battery_dispatch"]=dict(self.energy_policy,
            scope="Causal observed load and public periodic profiles; unchanged physical action table")
        self._energy_table={a["id"]:a for a in self.i["energy"]["battery_actions"]}

    def battery_action(self,load,solar,cap):
        e=self.i["energy"];period=self.i.get("day_ticks",96);t=self.t;horizon=self.i["horizon_ticks"]
        table=self._energy_table;charge=table["charge"];discharge=table["discharge"]
        term=e["stationary_soc_terminal_min"];minimum=e["stationary_soc_min"]
        future_high=high_ticks_before(horizon,period)-high_ticks_before(t+1,period)
        future_low=horizon-t-1-future_high
        floor=max(minimum,term)
        # This variant is tested empirically: future low-tariff opportunities do
        # not guarantee physical charging headroom under every possible workload.
        if self.energy_policy["reserve"]=="recovery" and future_low>=math.ceil((term-minimum)/charge["soc_delta"]):floor=minimum
        options={name:row_for_action(t,load,solar,cap,self.soc,action,e,period) for name,action in table.items()}
        legal={name:feasible_electrical(row,e) for name,row in options.items()}
        net=load-solar
        if net>cap+1e-9:
            return "discharge" if legal["discharge"] and options["discharge"]["soc"]>=floor else "idle"
        # Repay a lower-reserve experiment once no future high-price period is
        # available. A missing physical opportunity remains a reported failure.
        if self.soc<term and not future_high and legal["charge"]:return "charge"
        peak=period/3<=t%period<period*3/4
        objective=self.energy_policy["objective"]
        current=e[("tariff_" if objective=="cost" else "carbon_")+("peak" if peak else "low")]
        future=e[("tariff_" if objective=="cost" else "carbon_")+("peak" if future_high else "low")]
        low_value=e["tariff_low" if objective=="cost" else "carbon_low"]
        recharge_input=charge["charge_kw"]*(-discharge["soc_delta"])/charge["soc_delta"]
        saved_grid=options["idle"]["grid_kw"]-options["discharge"]["grid_kw"]
        if (peak and saved_grid*current>recharge_input*low_value+1e-12 and legal["discharge"] and
            options["discharge"]["soc"]>=floor):
            return "discharge"
        # One charge tick creates deltaSOC/(-dischargeSOC) discharge ticks.
        # Compare marginal imported energy with that known future tariff value;
        # a partial solar surplus can make charging profitable even at peak.
        incremental=options["charge"]["grid_kw"]-options["idle"]["grid_kw"]
        stored_output=charge["soc_delta"]/-discharge["soc_delta"]*discharge["discharge_kw"]
        target=min(e["stationary_soc_capacity"],floor+future_high*(-discharge["soc_delta"]))
        if (future_high and legal["charge"] and options["charge"]["soc"]<=target and
            incremental*current<stored_output*future-1e-12):return "charge"
        return "idle"

    def energy_tick(self):
        if self.energy_policy["strategy"]=="baseline":return super().energy_tick()
        t=self.t;e=self.i["energy"];period=self.i.get("day_ticks",96)
        solar=round(e["solar_peak_kw"]*max(0,math.sin(math.pi*(t%period-period/4)/(period/2))),4)
        load=e["base_load_kw"]+sum(op["power_kw"] for op in self.active if op["start"]<=t<op["end"])
        load+=self.i["transport"]["charge_power_kw"]*sum(m["kind"]=="charge" and m["charge_start"]<=t<m["end"] for m in self.trace["moves"])
        action=self._energy_table[self.battery_action(load,solar,self.grid_cap)]
        row=row_for_action(t,load,solar,self.grid_cap,self.soc,action,e,period)
        self.soc=row["soc"];self.trace["energy"].append(row)
        self.energy_cost+=row["grid_kw"]*self.i["tick_minutes"]/60*row["tariff"]
        if not feasible_electrical(row,e):self.event("infeasibility",reason="battery_dispatch",grid_kw=row["grid_kw"],cap_kw=row["cap_kw"])


class EnergyFactory(EnergyMixin,Factory):pass
class EnergyAdvancedFactory(EnergyMixin,AdvancedFactory):pass


def run(instance,weights=None,controller=None,*,advanced=False,energy_policy=None):
    cls=EnergyAdvancedFactory if advanced else EnergyFactory
    return cls(instance,weights,controller,energy_policy=energy_policy).run()


def _update_energy_metrics(trace):
    rows=trace["energy"];hours=trace["tick_minutes"]/60;metrics=trace["metrics"];e=trace["instance"]["energy"]
    metrics.update(grid_kwh=sum(r["grid_kw"]*hours for r in rows),
        energy_cost=sum(r["grid_kw"]*hours*r["tariff"] for r in rows),
        carbon_kg=sum(r["grid_kw"]*hours*r["carbon_intensity"] for r in rows),
        terminal_soc=rows[-1]["soc"] if rows else e["stationary_soc_initial"])
    metrics["terminal_soc_satisfied"]=metrics["terminal_soc"]>=e["stationary_soc_terminal_min"]
    metrics["total_cost"]=metrics["energy_cost"]+metrics.get("investment_cost",0)


def apply_battery_plan(trace,actions):
    """Keep the complete saved physical schedule; replace only battery actions."""
    if len(actions)!=len(trace["energy"]):raise ValueError("One action per fixed-load tick required")
    answer=deepcopy(trace);e=trace["instance"]["energy"];table={a["id"]:a for a in e["battery_actions"]}
    soc=e["stationary_soc_initial"];rows=[];period=trace["instance"].get("day_ticks",96)
    for old,name in zip(trace["energy"],actions):
        row=row_for_action(old["tick"],old["load_kw"],old["solar_kw"],old["cap_kw"],soc,table[name],e,period)
        if not feasible_electrical(row,e):raise ValueError(f"Infeasible fixed-load action at tick {old['tick']}")
        rows.append(row);soc=row["soc"]
    answer["energy"]=rows;_update_energy_metrics(answer)
    return answer


def fixed_load_dp(trace,objective="cost"):
    """Exact SOC/action DP on the fixed realized electrical trajectory.

    kW and objective coefficients are represented at 1e-4 precision and checked
    before rounding. Integer costs avoid floating comparison/tie artifacts.
    This is a clairvoyant conditional reference, not a global factory bound.
    """
    import numpy as np
    if objective not in ("cost","carbon"):raise ValueError("Unknown fixed-load objective")
    started=time.perf_counter();e=trace["instance"]["energy"];rows=trace["energy"]
    low=e["stationary_soc_min"];capacity=e["stationary_soc_capacity"];initial=e["stationary_soc_initial"]
    terminal=e["stationary_soc_terminal_min"];table=e["battery_actions"];horizon=len(rows)
    if (any(type(v) is not int for v in (low,capacity,initial,terminal)) or
        not 0<=low<=initial<=capacity or not low<=terminal<=capacity):
        raise ValueError("Integer bounded SOC required")
    inf=np.iinfo(np.int64).max//4;values=np.full(capacity+1,inf,dtype=np.int64);values[initial]=0
    choices=np.full((horizon,capacity+1),-1,dtype=np.int8);scale=10000
    for tick,old in enumerate(rows):
        new=np.full(capacity+1,inf,dtype=np.int64)
        price=old["tariff" if objective=="cost" else "carbon_intensity"]
        price_integer=round(price*scale)
        if price<0 or not math.isclose(price,price_integer/scale,rel_tol=0,abs_tol=1e-9):raise ValueError("Unsupported objective precision")
        for j,action in enumerate(table):
            delta=action["soc_delta"]
            if type(delta) is not int:raise ValueError("Integer SOC actions required")
            raw=row_for_action(tick,old["load_kw"],old["solar_kw"],old["cap_kw"],initial,action,e,
                trace["instance"].get("day_ticks",96))
            if raw["grid_kw"]>old["cap_kw"]+1e-9 or raw["curtailed_kw"]>old["solar_kw"]+1e-9:continue
            grid_integer=round(raw["grid_kw"]*scale)
            if not math.isclose(raw["grid_kw"],grid_integer/scale,rel_tol=0,abs_tol=1e-9):raise ValueError("Unsupported load precision")
            start=max(low,low-delta);stop=min(capacity,capacity-delta)+1
            if start>=stop:continue
            source=slice(start,stop);destination=slice(start+delta,stop+delta)
            candidate=values[source]+grid_integer*price_integer
            better=candidate<new[destination]
            new[destination][better]=candidate[better]
            choices[tick,destination][better]=j
        values=new
    final=int(np.argmin(values[max(low,terminal):])+max(low,terminal))
    if values[final]>=inf:
        return dict(status="INFEASIBLE",objective=objective,scope="Fixed realized load, exact integer SOC/action DP",
            wall_seconds=time.perf_counter()-started)
    optimum=int(values[final]);state=final;actions=[]
    for tick in range(horizon-1,-1,-1):
        j=int(choices[tick,state])
        if j<0:raise RuntimeError("Broken DP predecessor")
        action=table[j];actions.append(action["id"]);state-=action["soc_delta"]
    if state!=initial:raise RuntimeError("DP path does not start at initial SOC")
    actions.reverse();optimized=apply_battery_plan(trace,actions)
    optimized["provenance"]["battery_dispatch"]=dict(strategy="offline-fixed-load-dp",objective=objective,
        scope="Clairvoyant conditional fixed-load optimum; not causal; full factory gap unknown")
    optimized["metrics"]["global_optimality_gap"]=None
    if optimized.get("decisions"):
        optimized["provenance"]["battery_dispatch"]["policy_observations"]="Historical source observations; this counterfactual battery plan is not a controller replay"
    checked=check_trace(optimized)
    optimized["validation"]=dict(checked,status="passed" if checked["valid"] else "failed")
    return dict(status="OPTIMAL",objective=objective,objective_value=optimum*trace["tick_minutes"]/60/(scale*scale),
        objective_integer=optimum,objective_scale_kw=scale,terminal_soc=final,actions=actions,
        wall_seconds=time.perf_counter()-started,states=horizon*(capacity-low+1),
        scope="Clairvoyant fixed realized load/cap/solar only; no global factory bound or causal policy claim",
        trace=optimized,verification=checked)


def battery_metrics(trace):
    from collections import Counter
    rows=trace["energy"];counts=Counter(r["battery_action"] for r in rows)
    return dict(action_counts=dict(counts),soc_min=min(r["soc"] for r in rows),soc_max=max(r["soc"] for r in rows),
        soc_terminal=rows[-1]["soc"],curtailed_kwh=sum(r["curtailed_kw"]*trace["tick_minutes"]/60 for r in rows),
        emergency_net_load_ticks=sum(r["load_kw"]-r["solar_kw"]>r["cap_kw"]+1e-9 for r in rows))


def mechanism_activation(trace):
    """Measured activity, distinguishing finite resources from actual scarcity."""
    from collections import Counter
    i=trace["instance"];horizon=trace["horizon_ticks"];events=trace["events"];ops=trace["operations"];moves=trace["moves"]
    stock=dict(i["raw_stock_units"]);stock_min=dict(stock)
    for event in events:
        if event["type"]=="release":stock[event["recipe"]]-=1
        elif event["type"]=="delivery":
            for recipe,n in event["contents"].items():stock[recipe]+=n
        for recipe,n in stock.items():stock_min[recipe]=min(stock_min[recipe],n)
    # Input reservation becomes physical occupancy at arrival, so its total
    # occupancy interval runs continuously from dispatch until process/consume.
    buffers={m["id"]:[] for m in i["machines"]};output_wait=Counter()
    for move in moves:
        if move.get("entity_type")!="part" or move["to"] not in buffers:continue
        consumers=[op["start"] for op in ops if op["machine_id"]==move["to"] and op["start"]>=move["drop_tick"] and
            move["unit_id"] in op["unit_ids"]+op.get("parent_unit_ids",[])]
        buffers[move["to"]].extend(((move["start"],1),(min(consumers,default=horizon),-1)))
    peaks={}
    for mid,changes in buffers.items():
        current=peak=0
        for tick,delta in sorted(changes):current+=delta;peak=max(peak,current)
        peaks[mid]=peak
    for op in ops:
        if not op["unit_ids"]:continue
        pickups=[]
        for uid in op["unit_ids"]:
            pickups.append(min((m["pickup_tick"] for m in moves if m.get("entity_type")=="part" and
                m.get("unit_id")==uid and m["from"]==op["machine_id"] and m["pickup_tick"]>=op["end"]),default=horizon))
        output_wait[op["machine_id"]]+=max(pickups)-op["end"]
    return dict(battery=battery_metrics(trace),raw_stock_minimum=stock_min,
        raw_stock_ever_exhausted=any(n==0 for n in stock_min.values()),
        buffer_peak_occupancy=peaks,full_buffer_stations=[m["id"] for m in i["machines"] if peaks[m["id"]]>=m["input_capacity"]],
        blocked_output_ticks=dict(output_wait),qa_operations=sum(o["process"]=="QA" for o in ops),
        failed_inspections=sum(e["type"]=="qa_result" and not e["passed"] for e in events),
        repairs=sum(e["type"]=="repair" for e in events),scraps=sum(e["type"]=="scrap" for e in events),
        family_setups=sum(o["setup_ticks"]>0 for o in ops),setup_ticks=sum(o["setup_ticks"] for o in ops),
        multiunit_batches=sum(len(o["unit_ids"])>1 for o in ops),worker_walks=len(trace["worker_moves"]),
        tool_transports=sum(m.get("entity_type")=="tool" for m in moves),
        tool_services=sum(o.get("kind")=="tool_service" for o in ops),maintenance=sum(o.get("kind")=="maintenance" for o in ops))


def _compare_group(task):
    n,seed,horizon,advanced,outdir,dp=task;out=Path(outdir);weights=dict(wip_limit=4,mode="standard",lease_calibration=True,selector="priority")
    rows=[];traces=[];baseline=None
    policies={"baseline":dict(strategy="baseline"),"terminal":dict(reserve="terminal"),"recovery":dict(reserve="recovery")}
    for name,policy in policies.items():
        began=time.perf_counter();trace=run(build(orders=n,horizon=horizon,seed=seed),weights,advanced=advanced,energy_policy=policy)
        checked=check_trace(trace);traces.append(trace)
        trace["validation"]=dict(checked,status="passed" if checked["valid"] else "failed")
        if baseline is None:baseline=trace
        same=all(trace[key]==baseline[key] for key in ("operations","moves","worker_moves","events","qubo_decisions"))
        data=json.dumps(trace,separators=(",",":"),allow_nan=False).encode();filename=f"n{n}-s{seed}-{name}-a{int(advanced)}.json.gz"
        (out/filename).write_bytes(gzip.compress(data,mtime=0))
        rows.append(dict(method=name,valid=checked["valid"],issues=checked["issues"],terminal=checked["terminal_requirements_met"],
            same_physical_actions=same,metrics=trace["metrics"],battery=battery_metrics(trace),trace_file=filename,
            trace_sha256=hashlib.sha256(data).hexdigest(),wall_seconds=time.perf_counter()-began))
    references=[]
    if dp:
        for objective in ("cost","carbon"):
            result=fixed_load_dp(baseline,objective);reference_trace=result.pop("trace",None);result.pop("actions",None)
            if reference_trace:
                filename=f"n{n}-s{seed}-offline-{objective}-a{int(advanced)}.json.gz"
                data=json.dumps(reference_trace,separators=(",",":"),allow_nan=False).encode();(out/filename).write_bytes(gzip.compress(data,mtime=0))
                result.update(metrics=reference_trace["metrics"],battery=battery_metrics(reference_trace),trace_file=filename,
                    trace_sha256=hashlib.sha256(data).hexdigest())
            references.append(result)
    return dict(orders=n,seed=seed,advanced=advanced,weights=weights,rows=rows,references=references,
        mechanism_activation=mechanism_activation(baseline))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest="command",required=True)
    compare=sub.add_parser("compare");compare.add_argument("--orders",type=int,nargs="+",default=[8,12,24]);compare.add_argument("--seeds",type=int,nargs="+",default=[20,21,22,23])
    compare.add_argument("--horizon",type=int,default=5760);compare.add_argument("--workers",type=int,default=4)
    compare.add_argument("--advanced",action="store_true");compare.add_argument("--dp",action="store_true");compare.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(argv);args.output.mkdir(parents=True,exist_ok=True);before=source_hashes()
    for name in before:(args.output/Path(name).name).write_bytes((ROOT/name).read_bytes())
    started=time.perf_counter();tasks=[(n,s,args.horizon,args.advanced,str(args.output),args.dp) for n in args.orders for s in args.seeds]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:groups=list(pool.map(_compare_group,tasks))
    causal=[]
    for n in args.orders:
        for method in ("baseline","terminal","recovery"):
            traces=[]
            for group in groups:
                if group["orders"]==n:
                    row=next(r for r in group["rows"] if r["method"]==method)
                    traces.append(json.loads(gzip.decompress((args.output/row["trace_file"]).read_bytes())))
            causal.append(dict(orders=n,method=method,verification=check_paired_causality(traces)))
    after=source_hashes();report=dict(scope="Development battery policies and scoped clairvoyant references",source_before=before,source_after=after,
        source_stable=before==after,horizon=args.horizon,orders=args.orders,seeds=args.seeds,advanced=args.advanced,groups=groups,causality=causal,wall_seconds=time.perf_counter()-started)
    report["valid"]=report["source_stable"] and all(all(r["valid"] and r["terminal"] and r["same_physical_actions"] for r in g["rows"]) and
        all(r["status"]=="OPTIMAL" and r["verification"]["valid"] and r["verification"]["terminal_requirements_met"] for r in g["references"]) for g in groups) and all(c["verification"]["valid"] for c in causal)
    (args.output/"report.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(dict(valid=report["valid"],groups=len(groups),wall_seconds=report["wall_seconds"],output=str(args.output)),indent=2));return 0 if report["valid"] else 1


if __name__=="__main__":raise SystemExit(main())
