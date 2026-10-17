"""Causal portable-tool homes as explicit scheduling restrictions.

Homes do not mount tools or change their physical eligibility. All movement,
setup, service, life, worker and energy checks remain in the original factory.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import time

from .advanced import AdvancedFactory
from .specialist import SpecialistFactory
from .spec import build,duration
from .check import check_trace,check_paired_causality

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_HOMES=dict(mill1="F1",mill2="F2",weld1="S1",weld2="S2",calibration1="QA1",calibration_lease="QA2")


def source_hashes():
    names=("stage2/tooling.py","stage2/engine.py","stage2/spec.py","stage2/advanced.py",
           "stage2/specialist.py","stage2/check.py","stage2/dispatch.py","instances/stage2/metaltech_pressure.json")
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}


class ToolingMixin:
    def __init__(self,*args,tool_policy=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.tool_policy=dict(mode="soft",kinds=["mill","weld","calibration"],routing=False,home_penalty=12.)
        self.tool_policy.update(deepcopy(tool_policy or {}))
        if self.tool_policy["mode"] not in ("off","soft","hard"):raise ValueError("Unknown tool-home policy")
        if not set(self.tool_policy["kinds"])<={"mill","weld","calibration"}:raise ValueError("Unknown tool kind")
        self.tool_homes=dict(DEFAULT_HOMES);self.tool_homes.update(self.tool_policy.get("homes",{}))
        self.tool_homes={tid:mid for tid,mid in self.tool_homes.items() if mid in self.machines}
        self._home_demand_key=None;self._home_demands={};self.tool_home_filters=0;self.tool_home_borrows=0
        self.trace["provenance"]["tool_assignment"]=dict(self.tool_policy,homes=self.tool_homes,
            scope="Algorithm restrictions on portable resources; physical definition unchanged")

    def home_demand(self):
        key=(self.t,len(self.trace["operations"]),len(self.trace["moves"]),len(self.trace["events"]))
        if key==self._home_demand_key:return self._home_demands
        result={}
        for p in self.parts.values():
            if p["order_id"] not in self.admitted or p.get("accepted") or p["status"] in ("consumed","shipped","scrap","disposed","unreleased"):continue
            if p.get("moving"):
                mid=p.get("target_location")
                if mid in self.machines:result[mid]=result.get(mid,0)+1
            elif p["status"]=="waiting":
                mid=p["location"];step=self.next_step(p)
                if mid in self.machines and step and step["process"]==self.machines[mid]["process"] and p["id"] not in self.machines[mid]["output"]:
                    result[mid]=result.get(mid,0)+1
        self._home_demand_key=key;self._home_demands=result
        return result

    def tool_enabled(self,kind):
        return self.tool_policy["mode"]!="off" and kind in self.tool_policy["kinds"]

    def tool_allowed(self,tool,mid,p):
        home=self.tool_homes.get(tool["id"])
        # Honor a previously dispatched preparation rather than deadlock its
        # reserved part if a controller later changes the assignment policy.
        if tool.get("reserved_for")==p["id"]:return True
        if home in (None,mid):return True
        return self.tool_policy["mode"]=="soft" and not self.home_demand().get(home,0)

    def tool_view(self,m,parts,mode):
        p=parts[0];step=self.next_step(p);kind=self.i["process_tools"].get(step["process"])
        if not self.tool_enabled(kind):return self.tools
        dt=duration(self.i,step["process"],step["base_ticks"],m,mode)
        tools=[u for u in self.tools.values() if u["kind"]==kind and self.tool_allowed(u,m["id"],p)]
        usable=[u for u in tools if not u["moving"] and u["busy"]<=self.t and u["used"]+dt<=u["life"] and
            u.get("reserved_for") in (None,p["id"]) and (u["id"] not in self.preparation_tools or u["location"]==m["id"])]
        groups=([u for u in usable if u.get("reserved_for")==p["id"]],
            [u for u in usable if u["location"]==m["id"]],
            [u for u in usable if self.tool_homes.get(u["id"])==m["id"]],
            [u for u in usable if u["id"] not in self.tool_homes],usable)
        preferred=next((group for group in groups if group),[])
        ids={u["id"] for u in preferred}
        # Preserve the engine's in-flight preparation guard, including a
        # foreign tool already committed to this part/station.
        ids.update(u["id"] for u in self.tools.values() if u["kind"]==kind and u["moving"] and
            (u.get("reserved_for")==p["id"] or u.get("target_location")==m["id"]))
        return {tid:u for tid,u in self.tools.items() if u["kind"]!=kind or tid in ids}

    def process(self,m,parts,mode="standard",parents=None,kind="process",preview=False,prepare_only=False):
        original=self.tools;view=self.tool_view(m,parts,mode)
        if view is original:return super().process(m,parts,mode,parents,kind,preview,prepare_only)
        self.tool_home_filters+=1;self.tools=view
        try:
            result=super().process(m,parts,mode,parents,kind,preview,prepare_only)
            if result and not preview:
                self.tool_home_borrows+=sum(self.tool_homes.get(tid) not in (None,m["id"]) for tid in self.trace["operations"][-1]["tool_ids"])
            return result
        finally:self.tools=original

    def station_has_home(self,m,kind):
        if any(u["kind"]==kind and self.tool_homes.get(u["id"]) in (None,m["id"]) for u in self.tools.values()):return True
        # A paid, publicly known rental can be queued for before its arrival.
        if self.lease_requested:
            return any(option["resource"]["kind"]==kind and self.tool_homes.get(option["resource"]["id"])==m["id"]
                for option in self.i.get("lease_options",[]))
        return False

    def choose_machine(self,p):
        step=self.next_step(p)
        if not step:return None
        kind=self.i["process_tools"].get(step["process"])
        if not self.tool_enabled(kind):return super().choose_machine(p)
        if self.tool_policy["mode"]=="hard":
            original=self.machines
            self.machines={mid:m for mid,m in original.items() if m["process"]!=step["process"] or self.station_has_home(m,kind)}
            try:return super().choose_machine(p)
            finally:self.machines=original
        if not self.tool_policy["routing"]:return super().choose_machine(p)
        eligible=[m for m in self.machines.values() if m["process"]==step["process"]]
        if self.weights.get("routing_free_buffers",False):
            eligible=[m for m in eligible if self.input_count(m["id"])+self.reserved[m["id"]]<m["input_capacity"]]
        score=self.estimated_machine_finish if self.weights.get("routing_estimate_finish",False) else self.nominal_machine_score
        def ranked(m):
            penalty=0 if self.station_has_home(m,kind) else self.tool_policy["home_penalty"]
            return (score(p,m)+penalty,m["id"])
        return min(eligible,key=ranked) if eligible else None

    def finish(self):
        super().finish()
        self.trace.setdefault("algorithm_audit",{})["tool_assignment"]=dict(policy=self.tool_policy,
            tool_view_filters=self.tool_home_filters,foreign_home_uses=self.tool_home_borrows,
            scope="Algorithm-only homes; tools stay physically portable")


class ToolingFactory(ToolingMixin,AdvancedFactory):pass
class ToolingSpecialistFactory(ToolingMixin,SpecialistFactory):pass


def run(instance,weights=None,controller=None,*,tool_policy=None,specialist=False):
    cls=ToolingSpecialistFactory if specialist else ToolingFactory
    return cls(instance,weights,controller,tool_policy=tool_policy).run()


def tool_metrics(trace):
    from collections import Counter
    relocations=Counter(m["unit_id"] for m in trace["moves"] if m.get("entity_type")=="tool")
    uses=Counter((tid,op["machine_id"]) for op in trace["operations"] for tid in op["tool_ids"] if op["kind"]=="process")
    return dict(relocations=dict(relocations),uses=[dict(tool=tid,machine=mid,count=count) for (tid,mid),count in sorted(uses.items())],
        algorithm_audit=trace.get("algorithm_audit",{}))


VARIANTS={"off":dict(mode="off"),"soft-mill":dict(mode="soft",kinds=["mill"]),
    "hard-mill":dict(mode="hard",kinds=["mill"]),"soft-all":dict(mode="soft"),"hard-all":dict(mode="hard")}


def _group(task):
    n,seeds,horizon,weights,outdir,specialist,variants=task;out=Path(outdir);rows=[];causal=[]
    for variant in variants:
        traces=[]
        for seed in seeds:
            began=time.perf_counter();trace=run(build(orders=n,horizon=horizon,seed=seed),weights,
                tool_policy=VARIANTS[variant],specialist=specialist);checked=check_trace(trace);traces.append(trace)
            trace["validation"]=dict(checked,status="passed" if checked["valid"] else "failed")
            filename=f"n{n}-s{seed}-{variant}.json.gz";data=json.dumps(trace,separators=(",",":"),allow_nan=False).encode()
            (out/filename).write_bytes(gzip.compress(data,mtime=0))
            rows.append(dict(variant=variant,seed=seed,valid=checked["valid"],issues=checked["issues"],terminal=checked["terminal_requirements_met"],
                metrics=trace["metrics"],tool_metrics=tool_metrics(trace),trace_file=filename,trace_sha256=hashlib.sha256(data).hexdigest(),
                wall_seconds=time.perf_counter()-began))
        causal.append(dict(variant=variant,verification=check_paired_causality(traces)))
    return dict(orders=n,seeds=seeds,weights=weights,specialist=specialist,rows=rows,causality=causal)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--orders",type=int,nargs="+",default=[8,12])
    parser.add_argument("--seeds",type=int,nargs="+",default=[0,1,2,3]);parser.add_argument("--horizon",type=int,default=5760)
    parser.add_argument("--workers",type=int,default=2);parser.add_argument("--wip",type=int,default=4)
    parser.add_argument("--mode",choices=["standard","eco","turbo"],default="standard")
    parser.add_argument("--variants",nargs="+",choices=list(VARIANTS),default=list(VARIANTS));parser.add_argument("--specialist",type=int,default=0)
    parser.add_argument("--routing",action="store_true");parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(argv)
    if any(seed>=10000 for seed in args.seeds):raise ValueError("Final sealed seeds are prohibited in development runner")
    args.output.mkdir(parents=True,exist_ok=True);before=source_hashes()
    for name in before:(args.output/Path(name).name).write_bytes((ROOT/name).read_bytes())
    weights=dict(wip_limit=args.wip,mode=args.mode,lease_calibration=True,selector="priority",qa_guard_threshold=args.specialist)
    if args.routing:weights.update(routing_free_buffers=True,routing_estimate_finish=True)
    started=time.perf_counter();tasks=[(n,args.seeds,args.horizon,weights,str(args.output),bool(args.specialist),args.variants) for n in args.orders]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:groups=list(pool.map(_group,tasks))
    after=source_hashes();report=dict(scope="Training/development portable-tool assignment ablations",variants={v:VARIANTS[v] for v in args.variants},
        source_before=before,source_after=after,source_stable=before==after,groups=groups,wall_seconds=time.perf_counter()-started)
    report["valid"]=report["source_stable"] and all(all(row["valid"] and row["terminal"] for row in g["rows"]) and
        all(c["verification"]["valid"] for c in g["causality"]) for g in groups)
    (args.output/"report.json").write_text(json.dumps(report,indent=2));print(json.dumps(dict(valid=report["valid"],wall_seconds=report["wall_seconds"],output=str(args.output)),indent=2))
    return 0 if report["valid"] else 1


if __name__=="__main__":raise SystemExit(main())
