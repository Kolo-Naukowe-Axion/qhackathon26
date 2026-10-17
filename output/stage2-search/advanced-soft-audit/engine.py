"""Causal, discrete-time physical factory; no solver sees the hidden random tape.

This is an executable research model. Feature coverage is exported, and partial
production is deliberately distinguishable from a complete feasible solution.
"""
from collections import defaultdict, deque
from copy import deepcopy
import hashlib
import json
import math
import time

from .spec import duration


def uniform(seed, key):
    return int.from_bytes(hashlib.sha256(f"{seed}:{key}".encode()).digest()[:8],"big")/2**64


class Factory:
    def __init__(self, instance, weights=None, controller=None):
        self.i=deepcopy(instance); self.t=0; self.weights=dict(weights or {});self.controller=controller
        self.orders={o["id"]:dict(o) for o in self.i["orders"]}
        self.parts={u["id"]:dict(u,location=u["initial_location"],step=0,status="unreleased",
            attempt=0,replacement=0,accepted=False,rework=[],busy=False,quality_risk=0) for u in self.i["units"]}
        self.machines={m["id"]:dict(m,busy=0,output=set(),family=None,wear=0) for m in self.i["machines"]}
        self.workers={w["id"]:dict(w,busy=0,hall=w["initial_hall"]) for w in self.i["workers"]}
        self.tools={u["id"]:dict(u,location=u["initial_location"],busy=0,used=0,moving=False) for u in self.i["tools"]}
        self.agvs={a["id"]:dict(a,location=a["initial_location"],busy=0,soc=a["initial_soc"]) for a in self.i["agvs"]}
        self.stock=dict(self.i["raw_stock_units"]); self.done=defaultdict(list)
        self.edges=defaultdict(list); self.edge_use=defaultdict(list); self.charger_use=defaultdict(list)
        for e in self.i["graph_edges"]:
            self.edges[e["a"]].append((e["b"],e["ticks"]));self.edges[e["b"]].append((e["a"],e["ticks"]))
        self.reserved=defaultdict(int);self.active=[];self.outages={};self.grid_cap=self.i["energy"]["normal_grid_cap_kw"]
        self.soc=self.i["energy"]["stationary_soc_initial"];self.shipped={};self.assembly_target={}
        self.completed_steps=0;self.energy_cost=0
        self.admitted=set()
        self.lease_requested=False;self.investment_cost=0;self.delivery_tick=self.i["delivery"]["normal_tick"]
        self.delivery_received=False
        self.preparation_workers=set();self.preparation_tools=set()
        self.trace=dict(schema="metaltech-stage2-trace.v1",run_id=f'seed-{self.i["seed"]}',
            tick_minutes=self.i["tick_minutes"],horizon_ticks=self.i["horizon_ticks"],instance=self.i,
            resources={k:deepcopy(self.i[k]) for k in ("machines","workers","tools","agvs")},
            provenance=dict(kind="measured",solver="causal-dispatch",instance=self.i["name"],
                generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),code_revision="working-tree"),
            operations=[],moves=[],worker_moves=[],events=[],energy=[],decisions=[],qubo_decisions=[],audit=dict(realized_stages=[]))

    def event(self,kind,**kw):
        self.trace["events"].append(dict(tick=self.t,type=kind,**kw))

    def hall(self,node):
        if node in self.machines:return self.machines[node]["hall"]
        return node[-1]

    def path(self,a,b):
        q=deque([(a,[])]); seen={a}
        while q:
            n,p=q.popleft()
            if n==b:return p
            for nxt,d in self.edges[n]:
                if nxt not in seen:seen.add(nxt);q.append((nxt,p+[(n,nxt,d)]))
        raise ValueError((a,b))

    def plan_legs(self,path,start,loaded):
        legs=[];t=start
        for a,b,d in path:
            key=tuple(sorted((a,b)))
            while any(t<z and s<t+d for s,z in self.edge_use[key]):t+=1
            legs.append(dict(**{"from":a,"to":b},start=t,end=t+d,loaded=loaded)); t+=d
        return legs,t

    def commit_legs(self,legs):
        for l in legs:self.edge_use[tuple(sorted((l["from"],l["to"])) )].append((l["start"],l["end"]))

    def input_count(self,dest):
        return sum(p["location"]==dest and p["status"]=="waiting" and
                   p["id"] not in self.machines[dest]["output"] for p in self.parts.values())

    def move(self,unit,dest,entity_type="part"):
        obj=self.parts[unit] if entity_type=="part" else self.tools[unit]
        if (obj.get("busy",0)>self.t if entity_type=="tool" else obj.get("busy")) or obj.get("moving") or obj["location"]==dest:return False
        if entity_type=="part" and dest in self.machines:
            if self.input_count(dest)+self.reserved[dest]>=self.machines[dest]["input_capacity"]:return False
        source=obj["location"];opts=[]
        for a in self.agvs.values():
            if a["busy"]>self.t:continue
            empty,pick=self.plan_legs(self.path(a["location"],source),self.t,False)
            loaded,end=self.plan_legs(self.path(source,dest),pick+1,True);end+=1
            cost=sum(l["end"]-l["start"] for l in empty)+2*sum(l["end"]-l["start"] for l in loaded)
            # Preserve enough traction to reach either charging bay afterwards.
            reserve=min(sum(d for _,_,d in self.path(dest,c)) for c in self.i["transport"]["chargers"])
            if a["soc"]>=cost+reserve:opts.append((end,cost,a["id"],pick,empty+loaded))
        if not opts:return False
        end,cost,aid,pick,legs=min(opts);a=self.agvs[aid]
        if end>self.i["horizon_ticks"]:return False
        record=dict(id=f'M{len(self.trace["moves"])}',unit_id=unit,entity_type=entity_type,agv_id=aid,
            start=self.t,pickup_tick=pick,drop_tick=end,end=end,**{"from":source,"to":dest},
            legs=legs,soc_before=a["soc"],soc_after=a["soc"]-cost,kind="transport")
        self.trace["moves"].append(record);self.commit_legs(legs)
        a.update(busy=end,soc=a["soc"]-cost,location=dest)
        obj["busy"]=True if entity_type=="part" else end;obj["moving"]=True
        obj["target_location"]=dest
        if entity_type=="part" and dest in self.machines:self.reserved[dest]+=1
        self.done[pick].append(("pickup",record));self.done[end].append(("drop",record))
        return True

    def charge(self,a):
        if a["busy"]>self.t or a["soc"]>=90:return False
        opts=[]
        for c in self.i["transport"]["chargers"]:
            legs,arrive=self.plan_legs(self.path(a["location"],c),self.t,False)
            cost=sum(l["end"]-l["start"] for l in legs)
            if cost>a["soc"]:continue
            length=math.ceil((160-a["soc"]+cost)/12);s=arrive
            while any(s<z and x<s+length for x,z in self.charger_use[c]):s+=1
            opts.append((s+length,c,legs,cost,s))
        if not opts:return False
        end,c,legs,cost,s=min(opts)
        if end>self.i["horizon_ticks"]:return False
        self.commit_legs(legs);self.charger_use[c].append((s,end))
        self.trace["moves"].append(dict(id=f'M{len(self.trace["moves"])}',unit_id=None,entity_type=None,
            agv_id=a["id"],start=self.t,pickup_tick=s,drop_tick=end,end=end,**{"from":a["location"],"to":c},
            legs=legs,soc_before=a["soc"],soc_after=160,kind="charge",charge_start=s))
        a.update(busy=end,soc=160,location=c);return True

    def available_worker(self,skill,hall,length,allow_walk=True,start=None):
        start=self.t if start is None else start
        choices=[]
        for w in self.workers.values():
            if skill not in w["skills"] or w["busy"]>start:continue
            if w["id"] in self.preparation_workers and w["hall"]!=hall:continue
            a,b=w["daily_shift"];x=start%self.i.get("day_ticks",96)
            if not(a<=x and x+length<=b):continue
            if any(x<z and s<x+length for s,z in w["breaks"]):continue
            choices.append(w)
        for w in choices:
            if w["hall"]==hall:return w
        if choices and allow_walk and choices[0]["busy"]<=self.t:
            w=choices[0];d=self.i["worker_travel_ticks"]
            if self.t+d>self.i["horizon_ticks"]:return None
            now=self.t%self.i.get("day_ticks",96);a,b=w["daily_shift"]
            if not(a<=now and now+d<=b) or any(now<z and s<now+d for s,z in w["breaks"]):return None
            self.trace["worker_moves"].append(dict(worker_id=w["id"],start=self.t,end=self.t+d,from_hall=w["hall"],to_hall=hall))
            w.update(busy=self.t+d,hall=hall)
        return None

    def next_step(self,p):
        if p["rework"]:return p["rework"][0]
        recipe=self.i["recipes"][p["recipe"]]
        return recipe[p["step"]] if p["step"]<len(recipe) else None

    def service_resources(self):
        for tool in self.tools.values():
            if tool["moving"] or tool["busy"]>self.t or tool["used"]<tool["life"]-8*self.i.get("time_scale",1):continue
            length=tool["service_ticks"];hall=self.hall(tool["location"])
            if self.t+length>self.i["horizon_ticks"]:continue
            w=self.available_worker("setup",hall,length)
            if not w:continue
            op=dict(id=f'O{len(self.trace["operations"])}',unit_ids=[],unit_id=None,order_id=None,
                process="TOOL_SERVICE",machine_id=None,station=tool["location"],start=self.t,end=self.t+length,
                mode="standard",worker_ids=[w["id"]],tool_ids=[tool["id"]],parent_unit_ids=[],setup_ticks=0,
                processing_ticks=length,power_kw=0,family=None,kind="tool_service")
            self.trace["operations"].append(op);self.done[op["end"]].append(("tool_service",op))
            tool["busy"]=op["end"];w["busy"]=op["end"]
        for m in self.machines.values():
            if m["busy"]>self.t or m["output"] or m["wear"]<self.i["maintenance"]["wear_limit"]-12*self.i.get("time_scale",1):continue
            length=self.i["maintenance"]["duration"];w=self.available_worker("maintenance",m["hall"],length)
            if self.t+length>self.i["horizon_ticks"]:continue
            if not w:continue
            op=dict(id=f'O{len(self.trace["operations"])}',unit_ids=[],unit_id=None,order_id=None,
                process="MAINTENANCE",machine_id=m["id"],start=self.t,end=self.t+length,mode="standard",
                worker_ids=[w["id"]],tool_ids=[],parent_unit_ids=[],setup_ticks=0,processing_ticks=length,
                power_kw=self.i["maintenance"]["power_kw"],family=m["family"],kind="maintenance")
            load=self.i["energy"]["base_load_kw"]+sum(x["power_kw"] for x in self.active if x["end"]>self.t)
            if load+op["power_kw"]>self.grid_cap:continue
            self.trace["operations"].append(op);self.active.append(op);self.done[op["end"]].append(("maintenance",op))
            m["busy"]=op["end"];w["busy"]=op["end"]

    def priority(self,p):
        o=self.orders[p["order_id"]]; remaining=len(self.i["recipes"][p["recipe"]])-p["step"]
        return (self.weights.get("due",1)*o["due_tick"]/self.i.get("time_scale",1)+self.weights.get("remaining",-4)*remaining
                + self.weights.get("family",0)*["alloy_A","alloy_B","alloy_C"].index(p["family"])
                + self.weights.get("noise",0)*uniform(self.weights.get("policy_seed",0),p["id"]))

    def choose_machine(self,p):
        step=self.next_step(p)
        if not step:return None
        process=step["process"];eligible=[m for m in self.machines.values() if m["process"]==process]
        def score(m):
            travel=sum(d for _,_,d in self.path(p["location"],m["id"]))
            tk=self.i["process_tools"].get(process)
            tools=[u for u in self.tools.values() if u["kind"]==tk]
            tool_distance=min((sum(d for _,_,d in self.path(u.get("target_location") if u["moving"] else u["location"],m["id"])) for u in tools),default=0)
            return (max(0,m["busy"]-self.t)+len(m["output"])*6+
                (self.input_count(m["id"])+self.reserved[m["id"]])*6+travel+
                self.weights.get("tool_distance",4)*tool_distance+
                (0 if m["family"] in (None,p["family"]) else self.weights.get("setup",3)))
        return min(eligible,key=lambda m:(score(m),m["id"])) if eligible else None

    def process(self,m,parts,mode="standard",parents=None,kind="process",preview=False,prepare_only=False):
        if m["busy"]>self.t or m["output"] or self.outages.get(m["id"],0)>self.t:return False
        p=parts[0];step=self.next_step(p);proc=step["process"]
        base=step["base_ticks"];dt=duration(self.i,proc,base,m,mode)
        setup=0 if m["family"] in (None,p["family"]) else self.i["setup_matrix"][m["family"]][p["family"]]
        total=dt+setup;power=self.i["modes"][proc][mode]["power_kw"]
        if self.t+total>self.i["horizon_ticks"]:return False
        # A robust controller guard uses only the public support of future
        # disruptions. It never inspects which hidden outcome will occur.
        for stage in self.i["uncertainty_stages"]:
            if stage["reveal_tick"]<=self.t:continue
            for outcome in stage["outcomes"]:
                for ev in outcome["events"]:
                    if ev["type"]=="machine_outage" and ev["machine"]==m["id"] and self.t<ev["start"]<self.t+total:return False
                    if ev["type"]=="grid_derating" and self.t<ev["start"]<self.t+total:
                        future=self.i["energy"]["base_load_kw"]+power+8+sum(x["power_kw"] for x in self.active if x["end"]>ev["start"])
                        if future>ev["grid_cap_kw"]:return False
        # Admission uses currently revealed cap and conservative minimum cap for
        # already announced derating. Future hidden outcomes never affect it.
        load=self.i["energy"]["base_load_kw"]+sum(x["power_kw"] for x in self.active if x["end"]>self.t)
        if load+power+8>self.grid_cap:return False
        if m["wear"]+dt*self.i["modes"][proc][mode]["wear"]>self.i["maintenance"]["wear_limit"]:return False
        tool_kind=self.i["process_tools"].get(proc);tool=None
        if tool_kind:
            if any(u["kind"]==tool_kind and u["moving"] and
                   (u.get("reserved_for")==p["id"] or u.get("target_location")==m["id"]) for u in self.tools.values()):return False
            tools=[u for u in self.tools.values() if u["kind"]==tool_kind and not u["moving"] and u["busy"]<=self.t and u["used"]+dt<=u["life"]
                   and u.get("reserved_for") in (None,p["id"])
                   and (u["id"] not in self.preparation_tools or u["location"]==m["id"])]
            tool=next((u for u in tools if u["location"]==m["id"]),None)
            if tool is None:
                if tools and not preview:
                    target=min(tools,key=lambda u:sum(d for _,_,d in self.path(u["location"],m["id"])))
                    if self.move(target["id"],m["id"],"tool"):target["reserved_for"]=p["id"]
                return False
        attendance=self.i.get("attendance",{}).get(proc,{"kind":"full"})
        attend=dt if attendance["kind"]=="full" else min(dt,attendance["ticks"])
        skill=self.i["process_skills"][proc]
        w=self.available_worker(skill,m["hall"],attend,start=self.t+setup,allow_walk=not preview)
        if w is None:return False
        intervals=[];crew={w["id"]:w};roles={w["id"]:[skill]}
        if setup:
            if "setup" in w["skills"] and w["busy"]<=self.t:
                # The combined interval must fit a shift and avoid breaks too.
                combined=self.available_worker(skill,m["hall"],setup+attend,allow_walk=False)
                if combined is not w:return False
                intervals.append(dict(worker_id=w["id"],start=self.t,end=self.t+setup+attend,role="combined",skills=[skill,"setup"]))
                roles[w["id"]].append("setup")
            else:
                sw=self.available_worker("setup",m["hall"],setup,allow_walk=not preview)
                if sw is None:return False
                intervals.append(dict(worker_id=sw["id"],start=self.t,end=self.t+setup,role="setup",skills=["setup"]))
                crew[sw["id"]]=sw;roles[sw["id"]]=["setup"]
                intervals.append(dict(worker_id=w["id"],start=self.t+setup,end=self.t+setup+attend,role="process",skills=[skill]))
        else:intervals.append(dict(worker_id=w["id"],start=self.t,end=self.t+attend,role="process",skills=[skill]))
        unit_ids=[u["id"] for u in parts]
        op=dict(id=f'O{len(self.trace["operations"])}',unit_ids=unit_ids,unit_id=p["id"],order_id=p["order_id"],
            process=proc,machine_id=m["id"],start=self.t,end=self.t+total,mode=mode,worker_ids=list(crew),
            worker_intervals=intervals,worker_roles=roles,
            tool_ids=[tool["id"]] if tool else [],parent_unit_ids=parents or [],setup_ticks=setup,
            processing_ticks=dt,power_kw=power,family=p["family"],kind=kind,recipe_step=p["step"],
            recipe_steps={u["id"]:u["step"] for u in parts},attempt=p["attempt"],
            is_rework=bool(p["rework"]),repair_step=(2-len(p["rework"])) if p["rework"] else None)
        op["wear_before"]=m["wear"]
        if preview:return op
        if prepare_only:return False
        self.trace["operations"].append(op);self.active.append(op);self.done[op["end"]].append(("process",op))
        m.update(busy=op["end"],family=p["family"],wear=m["wear"]+dt*self.i["modes"][proc][mode]["wear"])
        for interval in intervals:crew[interval["worker_id"]]["busy"]=max(crew[interval["worker_id"]]["busy"],interval["end"])
        if tool:tool.update(busy=op["end"],used=tool["used"]+dt,reserved_for=None)
        for u in parts:u.update(status="processing",busy=True)
        if parents:
            for uid in parents:
                self.parts[uid].update(status="consumed",location="CONSUMED",busy=True)
                self.event("consume",unit_id=uid,parent_operation=op["id"],order_id=p["order_id"])
        return True

    def complete(self,kind,r):
        if kind=="lease_delivery":
            tool=dict(r["resource"]);self.tools[tool["id"]]=dict(tool,location=tool["initial_location"],busy=0,used=0,moving=False)
            self.trace["resources"]["tools"].append(dict(tool,arrival_tick=self.t))
            self.event("lease_delivery",option_id=r["id"],tool=tool);return
        if kind=="tool_service":
            for tid in r["tool_ids"]:self.tools[tid]["used"]=0
            self.event("tool_service_complete",operation_id=r["id"],tool_ids=r["tool_ids"]);return
        if kind=="maintenance":
            self.machines[r["machine_id"]]["wear"]=0
            self.event("maintenance_complete",operation_id=r["id"],resource_id=r["machine_id"]);return
        if kind=="pickup":
            obj=self.parts[r["unit_id"]] if r["entity_type"]=="part" else self.tools[r["unit_id"]]
            source=r["from"]
            if r["entity_type"]=="part" and source in self.machines:self.machines[source]["output"].discard(r["unit_id"])
            obj["location"]="TRANSIT";return
        if kind=="drop":
            obj=self.parts[r["unit_id"]] if r["entity_type"]=="part" else self.tools[r["unit_id"]]
            obj.update(location=r["to"],moving=False,busy=False if r["entity_type"]=="part" else self.t)
            if r["entity_type"]=="part":
                if r["to"] in self.machines:self.reserved[r["to"]]-=1
                obj["status"]="waiting"
                if r["to"]=="SHIP_B":
                    obj["status"]="shipped";self.shipped[obj["order_id"]]=self.t
                    self.event("ship",unit_id=obj["id"],order_id=obj["order_id"])
                elif r["to"]=="SCRAP_B":obj["status"]="disposed"
            return
        if kind=="process":
            m=self.machines[r["machine_id"]]
            for uid in r["unit_ids"]:
                p=self.parts[uid]
                if p["rework"]:p["rework"].pop(0)
                else:p["step"]+=1
                p.update(status="waiting",busy=False,location=m["id"]);m["output"].add(uid)
                self.completed_steps+=1
                self.event("process_complete",unit_id=uid,operation_id=r["id"])
                if r["process"]!="QA" and self.i["quality"].get("risk_model")=="manufacturing_mode_history":
                    if r["is_rework"]:p["quality_risk"]=self.i["quality"]["repair_residual_probability"]
                    else:
                        probability=self.i["quality"]["manufacturing_defect_probabilities"][r["process"]][r["mode"]]
                        probability+=self.i["quality"]["wear_risk_coefficient"]*r["wear_before"]/self.i["maintenance"]["wear_limit"]
                        p["quality_risk"]=1-(1-p.get("quality_risk",0))*(1-probability)
                if r["process"]=="QA":
                    draw=uniform(self.i["seed"],f'quality:{uid}:{p["attempt"]}')
                    fail=self.i["quality"]["final_defect_probability"] if p["recipe"]=="pump" else self.i["quality"]["component_defect_probability"][r["mode"]]
                    if self.i["quality"].get("risk_model")=="manufacturing_mode_history":fail=p.get("quality_risk",0)
                    passed=draw>=fail;p["accepted"]=passed
                    self.event("qa_result",unit_id=uid,operation_id=r["id"],passed=passed,keyed_uniform=draw,defect_probability=fail)
                    if not passed and p["attempt"]==0:
                        p["attempt"]+=1;p["rework"]=[dict(process="ASSEMBLY" if p["recipe"]=="pump" else "T",base_ticks=self.i["quality"]["repair_ticks"]),dict(process="QA",base_ticks=self.i["recipes"]["pump"][-1]["base_ticks"])]
                        self.event("repair",unit_id=uid,attempt=p["attempt"])
                    elif not passed:
                        p["status"]="scrap";self.event("scrap",unit_id=uid)
                        if p["recipe"]!="pump" and p["replacement"]==0:
                            newid=uid+"~r1";q=dict(p,id=newid,step=0,status="unreleased",attempt=0,replacement=1,accepted=False,
                                rework=[],busy=False,location="RAW_A",initial_location="RAW_A",quality_risk=0,release_tick=self.t+self.i["quality"]["replacement_lead_ticks"])
                            self.parts[newid]=q
                            self.event("replacement",unit_id=uid,replacement_id=newid,release_tick=q["release_tick"])
                            self.event("new_unit",unit={k:q[k] for k in ("id","order_id","recipe","family","release_tick","initial_location")})

    def reveal(self):
        for idx,stage in enumerate(self.i["uncertainty_stages"]):
            if stage["reveal_tick"]!=self.t:continue
            draw=uniform(self.i["seed"],f"stage:{idx}");cum=0
            for out in stage["outcomes"]:
                a,b=out["probability"];cum+=a/b
                if draw<cum:break
            self.trace["audit"]["realized_stages"].append(dict(tick=self.t,outcome=out["id"]))
            self.event("reveal",outcome=out["id"])
            for ev in out["events"]:
                data={k:v for k,v in ev.items() if k!="type"}
                if ev["type"]=="machine_outage":self.outages[ev["machine"]]=ev["end"];self.event("outage",**data)
                elif ev["type"]=="grid_derating":self.grid_cap=ev["grid_cap_kw"];self.event("grid_derating",**data)
                elif ev["type"]=="delivery_delay":self.delivery_tick=ev["new_tick"];self.event("delivery_delay",**data)
                elif ev["type"]=="urgent_orders":
                    # New order graph is generated only on revelation.
                    for j in range(ev["count"]):
                        oid=f"U{j+1:02d}";o=dict(id=oid,family="alloy_C",release_tick=self.t,due_tick=288*self.i.get("time_scale",1),precision_required=True,urgent=True)
                        self.orders[oid]=o;self.event("urgent_order",order=o)
                        for recipe in ("housing","rotor","flange"):
                            uid=f"{oid}/{recipe}/1";p=dict(id=uid,order_id=oid,recipe=recipe,family=o["family"],release_tick=self.t,
                                initial_location="RAW_A",location="RAW_A",step=0,status="unreleased",attempt=0,replacement=0,
                                accepted=False,rework=[],busy=False,quality_risk=0)
                            self.parts[uid]=p;self.event("new_unit",unit={k:p[k] for k in ("id","order_id","recipe","family","release_tick","initial_location")})
        if self.t==144*self.i.get("time_scale",1):self.grid_cap=self.i["energy"]["normal_grid_cap_kw"]
        if self.t==self.delivery_tick and not self.delivery_received:
            for recipe,n in self.i["delivery"]["contents"].items():self.stock[recipe]+=n
            self.delivery_received=True;self.event("delivery",delivery_id=self.i["delivery"]["id"],contents=dict(self.i["delivery"]["contents"]))

    def capacity_decisions(self):
        if self.weights.get("lease_calibration",False) and not self.lease_requested:
            option=self.i["lease_options"][0]
            if self.investment_cost+option["cost"]<=self.i["investment_budget"] and self.t+option["lead_ticks"]<self.i["horizon_ticks"]:
                self.lease_requested=True;self.investment_cost+=option["cost"]
                self.done[self.t+option["lead_ticks"]].append(("lease_delivery",option))
                self.event("lease_request",option_id=option["id"],arrival_tick=self.t+option["lead_ticks"],cost=option["cost"])

    def assembly(self):
        for oid in sorted(self.orders,key=lambda x:self.orders[x]["due_tick"]):
            pump=f"{oid}/pump/1"
            if pump in self.parts:continue
            components=[p for p in self.parts.values() if p["order_id"]==oid and p["accepted"] and p["recipe"]!="pump" and p["status"]=="waiting" and not p["busy"]]
            if not components:continue
            target=self.assembly_target.setdefault(oid,min((m for m in self.machines.values() if m["process"]=="ASSEMBLY"),key=lambda m:self.input_count(m["id"])+self.reserved[m["id"]])["id"])
            for p in components:
                if p["location"]!=target:self.move(p["id"],target)
            if len(components)!=3:continue
            if not all(p["location"]==target and not p["busy"] for p in components):continue
            o=self.orders[oid];p=dict(id=pump,order_id=oid,recipe="pump",family=o["family"],release_tick=o["release_tick"],
                initial_location=target,location=target,step=0,status="waiting",attempt=0,replacement=0,accepted=False,rework=[],busy=False,quality_risk=0)
            self.parts[pump]=p
            if not self.process(self.machines[target],[p],parents=[u["id"] for u in components]):del self.parts[pump]

    def energy_tick(self):
        t=self.t;e=self.i["energy"];period=self.i.get("day_ticks",96);day=t%period;scale=period/96
        solar=round(e["solar_peak_kw"]*max(0,math.sin(math.pi*(day-24*scale)/(48*scale))),4)
        load=e["base_load_kw"]+sum(x["power_kw"] for x in self.active if x["start"]<=t<x["end"])
        load+=self.i["transport"]["charge_power_kw"]*sum(m["kind"]=="charge" and m["charge_start"]<=t<m["end"] for m in self.trace["moves"])
        before=self.soc;action="idle";charge=discharge=0
        if load-solar>self.grid_cap and self.soc-10>=e["stationary_soc_min"]:
            action="discharge";self.soc-=10;discharge=9
        elif self.soc+9<=e["stationary_soc_capacity"] and load-solar+10<=self.grid_cap and (day<24*scale or self.soc<e["stationary_soc_terminal_min"]):
            action="charge";self.soc+=9;charge=10
        grid=max(0,load-solar+charge-discharge);curtailed=max(0,solar-load-charge+discharge)
        self.trace["energy"].append(dict(tick=t,load_kw=load,grid_kw=grid,cap_kw=self.grid_cap,solar_kw=solar,
            curtailed_kw=curtailed,soc_before=before,soc=self.soc,battery_action=action,
            tariff=e["tariff_peak"] if 32*scale<=day<72*scale else e["tariff_low"],carbon_intensity=e["carbon_peak"] if 32*scale<=day<72*scale else e["carbon_low"]))
        self.energy_cost+=grid*self.i["tick_minutes"]/60*self.trace["energy"][-1]["tariff"]
        if grid>self.grid_cap+1e-6:self.event("infeasibility",reason="grid_cap",grid_kw=grid,cap_kw=self.grid_cap)

    def observation(self):
        obs=dict(tick=self.t,horizon_ticks=self.i["horizon_ticks"],tick_minutes=self.i["tick_minutes"],
            day_ticks=self.i.get("day_ticks",96),observed_orders=len(self.orders),shipped=len(self.shipped),
            completed_steps=self.completed_steps,active_operations=len(self.active),
            waiting_parts=sum(p["status"]=="waiting" and not p["busy"] for p in self.parts.values()),
            accepted_components=sum(p["accepted"] and p["recipe"]!="pump" and p["status"]=="waiting" for p in self.parts.values()),
            agvs_free=sum(a["busy"]<=self.t for a in self.agvs.values()),agvs_total=len(self.agvs),
            agv_soc_mean=sum(a["soc"] for a in self.agvs.values())/len(self.agvs),
            workers_free=sum(w["busy"]<=self.t for w in self.workers.values()),workers_total=len(self.workers),
            tools_free=sum(u["busy"]<=self.t and not u["moving"] for u in self.tools.values()),
            grid_cap_kw=self.grid_cap,normal_grid_cap_kw=self.i["energy"]["normal_grid_cap_kw"],
            stationary_soc=self.soc,stationary_soc_capacity=self.i["energy"]["stationary_soc_capacity"],
            machine_outages=sum(end>self.t for end in self.outages.values()),energy_cost=self.energy_cost,
            overdue_orders=sum(o["due_tick"]<self.t and o["id"] not in self.shipped for o in self.orders.values()))
        for proc in self.i["modes"]:
            obs[f"queue_{proc}"]=sum(p["status"]=="waiting" and not p["busy"] and self.next_step(p) is not None and self.next_step(p)["process"]==proc for p in self.parts.values())
        return obs

    def run(self):
        for t in range(self.i["horizon_ticks"]+1):
            self.t=t
            # Completions may enqueue pickups at the current boundary later.
            pending=self.done.pop(t,[])
            for kind,r in pending:self.complete(kind,r)
            self.active=[x for x in self.active if x["end"]>t]
            self.reveal()
            if t==self.i["horizon_ticks"]:break
            if self.controller and t%self.i.get("replan_ticks",4)==0:
                obs=self.observation();answer=self.controller(dict(obs))
                self.weights.update(answer.get("weights",{}))
                self.trace["decisions"].append(dict(tick=t,observation=obs,action_id=answer.get("action_id"),weights=dict(self.weights)))
            self.capacity_decisions()
            for p in list(self.parts.values()):
                if p["status"]=="unreleased" and p["release_tick"]<=t and self.stock[p["recipe"]]>0:
                    self.stock[p["recipe"]]-=1;p["status"]="waiting";self.event("release",unit_id=p["id"],recipe=p["recipe"])
                if p["status"]=="scrap" and not p["busy"]:self.move(p["id"],"SCRAP_B")
            self.assembly()
            self.service_resources()
            # CONWIP is a controller restriction, not a reduced physical model:
            # all released orders remain in the inventory and objective.
            self.admitted.difference_update(self.shipped)
            slots=max(0,int(self.weights.get("wip_limit",6))-len(self.admitted))
            # Known future releases occupy their place in the priority window.
            # Admitted orders retain WIP slots until completion; releasing a new
            # earlier-due order must never strand existing parts on machines.
            head=sorted((o for o in self.orders.values() if o["id"] not in self.shipped and o["id"] not in self.admitted),
                        key=lambda o:(o["due_tick"],o["release_tick"],o["id"]))[:slots]
            self.admitted.update(o["id"] for o in head if o["release_tick"]<=t)
            allowed=self.admitted
            ready=sorted((p for p in self.parts.values() if p["status"]=="waiting" and not p["busy"] and p["order_id"] in allowed),key=self.priority)
            considered=set();requests=[];self.preparation_workers=set();self.preparation_tools=set()
            for p in ready:
                if p["id"] in considered:continue
                if p["accepted"]:
                    if p["recipe"]=="pump":self.move(p["id"],"SHIP_B")
                    continue
                step=self.next_step(p)
                if not step:continue
                current=self.machines.get(p["location"])
                if current and current["process"]==step["process"] and p["id"] not in current["output"]:
                    batch=[p]
                    if step["process"]=="HEAT":
                        batch=[u for u in ready if u["location"]==current["id"] and u["family"]==p["family"] and self.next_step(u) and self.next_step(u)["process"]=="HEAT"][:current.get("batch_capacity",1)]
                    considered.update(u["id"] for u in batch)
                    mode=self.weights.get("mode","standard") if step["process"] in ("T","F") else ("precision" if step["process"]=="QA" and self.orders[p["order_id"]]["precision_required"] else "standard")
                    if self.orders[p["order_id"]]["precision_required"] and mode=="turbo":mode="standard"
                    initial_offer=self.process(current,batch,mode,preview=True)
                    if initial_offer:
                        self.preparation_workers.update(initial_offer["worker_ids"])
                        self.preparation_tools.update(initial_offer["tool_ids"])
                    else:self.process(current,batch,mode,prepare_only=True)
                    requests.append((current,batch,mode))
                else:
                    target=self.choose_machine(p)
                    if target:self.move(p["id"],target["id"])
            offers=[];valid_requests=[]
            for current,batch,mode in requests:
                offer=self.process(current,batch,mode,preview=True)
                if offer:offers.append(offer);valid_requests.append((current,batch,mode))
            method=self.weights.get("selector","priority")
            if offers and method!="priority":
                from .dispatch import choose
                selected,evidence=choose(offers,self.i,self.active,t,self.grid_cap,
                    [self.priority(parts[0]) for _,parts,_ in valid_requests],method,
                    seed=self.weights.get("policy_seed",0)+t)
                evidence.update(tick=t,offered_operations=offers,committed=[])
                self.trace["qubo_decisions"].append(evidence)
            else:selected=list(range(len(offers)));evidence=None
            for idx in selected:
                current,batch,mode=valid_requests[idx]
                if self.process(current,batch,mode) and evidence is not None:evidence["committed"].append(f"C{idx}")
            # Immediate pickups created this tick must release source now.
            for kind,r in self.done.pop(t,[]):self.complete(kind,r)
            for a in self.agvs.values():self.charge(a)
            self.energy_tick()
        self.finish();return self.trace

    def finish(self):
        horizon=self.i["horizon_ticks"]
        tardiness=sum(max(0,self.shipped.get(o["id"],horizon)-o["due_tick"]) for o in self.orders.values())
        hours=self.i["tick_minutes"]/60
        energy=sum(e["grid_kw"]*hours for e in self.trace["energy"])
        self.trace["metrics"]=dict(orders=len(self.orders),shipped=len(self.shipped),shipped_at=self.shipped,
            all_orders_fulfilled=len(self.shipped)==len(self.orders),total_tardiness_ticks=tardiness,
            grid_kwh=energy,energy_cost=sum(e["grid_kw"]*hours*e["tariff"] for e in self.trace["energy"]),
            carbon_kg=sum(e["grid_kw"]*hours*e["carbon_intensity"] for e in self.trace["energy"]),
            terminal_soc=self.soc,terminal_soc_satisfied=self.soc>=self.i["energy"]["stationary_soc_terminal_min"],
            investment_cost=self.investment_cost,total_cost=self.energy_cost+self.investment_cost,
            operations=len(self.trace["operations"]),moves=len(self.trace["moves"]),
            unfinished=sum(p["status"] not in ("consumed","shipped","scrap") for p in self.parts.values()),
            global_optimality_gap=None)
        self.trace["validation"]=dict(status="unchecked",description="Run independent checker before treating this as feasible")


def run(instance,weights=None,controller=None):
    return Factory(instance,weights,controller).run()
