"""Stronger scheduling over the same physical model: calendars and preposition.

Unlike the baseline decoder, workers may fill gaps before future reservations,
and an idle AGV may start its empty trip just before a known operation finishes.
Quality inspection outcomes are never anticipated.
"""
from .engine import Factory
from .spec import duration


class AdvancedFactory(Factory):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._ready_tick=None;self._calendar_key=None;self._bookings={}
        self._bom_key=None;self._bom_orders={}
        self.trace["provenance"]["solver"]="calendar-and-preposition-dispatch"
        self.trace["provenance"]["initial_advanced_features"]=dict(
            worker_calendar=bool(self.weights.get("worker_calendar",True)),
            preposition=bool(self.weights.get("preposition",True)) and int(self.weights.get("preposition_ticks",10))>0,
            preposition_ticks=int(self.weights.get("preposition_ticks",10)),
            routing_free_buffers=bool(self.weights.get("routing_free_buffers",False)),
            routing_estimate_finish=bool(self.weights.get("routing_estimate_finish",False)),
            bom_priority=self.weights.get("bom_priority",False))

    def selected_mode(self,process,order_id):
        precise=self.orders[order_id]["precision_required"]
        if process in ("T","F"):
            mode=self.weights.get("mode","standard")
            return "standard" if precise and mode=="turbo" else mode
        return "precision" if process=="QA" and precise else "standard"

    def remaining_processing(self,p):
        """Known committed work plus optimistic remaining manufacturing ticks.

        Future stations use their fastest eligible duration under the current
        certified decoder mode. No future defect, urgent arrival or shock draw
        is read; this is a ranking estimate, not a completion-time guarantee.
        """
        if p.get("accepted") or p["status"] in ("consumed","shipped","scrap","disposed"):return 0
        route=p.get("rework") or self.i["recipes"][p["recipe"]][p["step"]:]
        remaining=0
        if p["status"]=="processing":
            active=next((op for op in self.active if p["id"] in op["unit_ids"] and op["end"]>self.t),None)
            if active is not None:remaining=active["end"]-self.t;route=route[1:]
        if p["status"]=="unreleased":remaining+=max(0,p["release_tick"]-self.t)
        for step in route:
            mode=self.selected_mode(step["process"],p["order_id"])
            remaining+=min(duration(self.i,step["process"],step["base_ticks"],m,mode)
                           for m in self.machines.values() if m["process"]==step["process"])
        return remaining

    def bom_orders(self):
        key=(self.t,len(self.trace["operations"]),len(self.trace["moves"]),self.weights.get("mode","standard"))
        if key==self._bom_key:return self._bom_orders
        result={}
        for oid in self.orders:
            parts=[p for p in self.parts.values() if p["order_id"]==oid and p["status"] not in ("scrap","disposed","consumed")]
            pumps=[p for p in parts if p["recipe"]=="pump"]
            components={}
            for recipe in ("housing","rotor","flange"):
                candidates=[p for p in parts if p["recipe"]==recipe]
                if candidates:
                    p=min(candidates,key=self.remaining_processing)
                    components[recipe]=dict(id=p["id"],accepted=bool(p.get("accepted")),
                        progress=min(1,p["step"]/len(self.i["recipes"][recipe])),remaining=self.remaining_processing(p))
            if pumps:
                pump=min(pumps,key=self.remaining_processing);critical=self.remaining_processing(pump)
                pump_remaining=critical
            else:
                pump_remaining=0
                for step in self.i["recipes"]["pump"]:
                    mode=self.selected_mode(step["process"],oid)
                    pump_remaining+=min(duration(self.i,step["process"],step["base_ticks"],m,mode)
                        for m in self.machines.values() if m["process"]==step["process"])
                critical=max((p["remaining"] for p in components.values()),default=0)+pump_remaining
            result[oid]=dict(components=components,critical_remaining=critical,pump_remaining=pump_remaining)
        self._bom_orders=result;self._bom_key=key
        return result

    def priority(self,p):
        base=super().priority(p);rule=self.weights.get("bom_priority",False)
        if not rule:return base
        if rule is True:rule="join"
        if rule not in ("join","critical","slack"):raise ValueError("Unknown BOM priority rule")
        info=self.bom_orders()[p["order_id"]];scale=self.i.get("time_scale",1)
        peers=[v for kind,v in info["components"].items() if kind!=p["recipe"]]
        accepted=sum(v["accepted"] for v in peers)
        progress=sum(v["progress"] for v in peers)
        score=base-self.weights.get("bom_join_weight",24)*accepted-self.weights.get("bom_progress_weight",4)*progress
        if rule in ("critical","slack"):
            score-=self.weights.get("bom_tail_weight",.5)*self.remaining_processing(p)/scale
        if rule=="slack":score-=self.weights.get("bom_slack_weight",1)*info["critical_remaining"]/scale
        return score

    def nominal_machine_score(self,p,m):
        travel=sum(d for _,_,d in self.path(p["location"],m["id"]))
        tool_kind=self.i["process_tools"].get(self.next_step(p)["process"])
        tools=[u for u in self.tools.values() if u["kind"]==tool_kind]
        tool_distance=min((sum(d for _,_,d in self.path(u.get("target_location") if u["moving"] else u["location"],m["id"])) for u in tools),default=0)
        return (max(0,m["busy"]-self.t)+len(m["output"])*6+
            (self.input_count(m["id"])+self.reserved[m["id"]])*6+travel+
            self.weights.get("tool_distance",4)*tool_distance+
            (0 if m["family"] in (None,p["family"]) else self.weights.get("setup",3)))

    def next_worker_interval(self,w,start,length):
        """Earliest fit in a known calendar, jumping over busy/break intervals."""
        period=self.i.get("day_ticks",96);tick=max(self.t,int(start));a,b=w["daily_shift"]
        if not self.weights.get("worker_calendar",True):tick=max(tick,w["busy"])
        while tick+length<=self.i["horizon_ticks"]:
            phase=tick%period;day=tick-phase
            if phase<a:tick=day+a;continue
            if phase>=b or phase+length>b:tick=day+period+a;continue
            breaks=[z for s,z in w["breaks"] if phase<z and s<phase+length]
            if breaks:tick=day+max(breaks);continue
            bookings=[z for s,z in self.calendars()[w["id"]] if tick<z and s<tick+length]
            if bookings:tick=max(bookings);continue
            return tick
        return self.i["horizon_ticks"]+period

    def skill_ready(self,skill,hall,start,length):
        times=[]
        for w in self.workers.values():
            if skill not in w["skills"]:continue
            earliest=start
            if w["hall"]!=hall:
                # The decoder does not walk away from future hall commitments.
                anchor=max((z for _,z in self.calendars()[w["id"]]),default=self.t)
                walk=self.next_worker_interval(w,max(self.t,anchor),self.i["worker_travel_ticks"])
                earliest=max(earliest,walk+self.i["worker_travel_ticks"])
            times.append(self.next_worker_interval(w,earliest,length))
        return min(times,default=self.i["horizon_ticks"]+self.i.get("day_ticks",96))

    def estimated_machine_finish(self,p,m):
        """Public-state ETA heuristic; joint crew/tool/traffic fits remain checked."""
        step=self.next_step(p);proc=step["process"];mode=self.selected_mode(proc,p["order_id"])
        dt=duration(self.i,proc,step["base_ticks"],m,mode)
        setup=0 if m["family"] in (None,p["family"]) else self.i["setup_matrix"][m["family"]][p["family"]]
        ready=max([self.t]+[op["end"] for op in self.active if p["id"] in op["unit_ids"]])
        vehicle=min(max(self.t,a["busy"])+sum(d for _,_,d in self.path(a["location"],p["location"])) for a in self.agvs.values())
        arrival=max(ready,vehicle)+self.i["transport"]["load_ticks"]+sum(d for _,_,d in self.path(p["location"],m["id"]))+self.i["transport"]["unload_ticks"]
        start=max(arrival,m["busy"],self.outages.get(m["id"],0))
        start+=(self.input_count(m["id"])+self.reserved[m["id"]])*dt+len(m["output"])*6
        tool_kind=self.i["process_tools"].get(proc)
        if tool_kind:
            tools=[u for u in self.tools.values() if u["kind"]==tool_kind]
            times=[]
            for tool in tools:
                location=tool.get("target_location") if tool["moving"] else tool["location"]
                transfer=0 if location==m["id"] else 2+sum(d for _,_,d in self.path(location,m["id"]))
                times.append(max(self.t,tool["busy"])+transfer)
            start=max(start,min(times,default=self.i["horizon_ticks"]))
        if setup:start=max(start,self.skill_ready("setup",m["hall"],start,setup))
        attendance=self.i.get("attendance",{}).get(proc,{"kind":"full"})
        attend=dt if attendance["kind"]=="full" else min(dt,attendance["ticks"])
        return self.skill_ready(self.i["process_skills"][proc],m["hall"],start+setup,attend)+dt

    def choose_machine(self,p):
        free=self.weights.get("routing_free_buffers",False);estimate=self.weights.get("routing_estimate_finish",False)
        if not free and not estimate:return super().choose_machine(p)
        step=self.next_step(p)
        if not step:return None
        eligible=[m for m in self.machines.values() if m["process"]==step["process"]]
        if free:eligible=[m for m in eligible if self.input_count(m["id"])+self.reserved[m["id"]]<m["input_capacity"]]
        if not eligible:return None
        score=self.estimated_machine_finish if estimate else self.nominal_machine_score
        return min(eligible,key=lambda m:(score(p,m),self.nominal_machine_score(p,m),m["id"]))

    def calendars(self):
        key=(len(self.trace["operations"]),len(self.trace["worker_moves"]))
        if key!=self._calendar_key:
            result={wid:[] for wid in self.workers}
            for op in self.trace["operations"]:
                intervals=op.get("worker_intervals") or [dict(worker_id=w,start=op["start"],end=op["end"]) for w in op["worker_ids"]]
                for v in intervals:result[v["worker_id"]].append((v["start"],v["end"]))
            for v in self.trace["worker_moves"]:result[v["worker_id"]].append((v["start"],v["end"]))
            self._bookings=result;self._calendar_key=key
        return self._bookings

    def fits(self,w,start,length):
        x=start%self.i.get("day_ticks",96);a,b=w["daily_shift"]
        if not(a<=x and x+length<=b):return False
        if any(x<z and s<x+length for s,z in w["breaks"]):return False
        return not any(start<z and s<start+length for s,z in self.calendars()[w["id"]])

    def available_worker(self,skill,hall,length,allow_walk=True,start=None):
        if not self.weights.get("worker_calendar",True):return super().available_worker(skill,hall,length,allow_walk,start)
        start=self.t if start is None else start
        choices=[w for w in self.workers.values() if skill in w["skills"] and self.fits(w,start,length)]
        for w in choices:
            if w["hall"]==hall:return w
        if not allow_walk:return None
        d=self.i["worker_travel_ticks"]
        for w in choices:
            if w["id"] in self.preparation_workers:continue
            # A future appointment anchors the worker's hall until it finishes.
            if any(z>self.t for _,z in self.calendars()[w["id"]]):continue
            if self.t+d>self.i["horizon_ticks"] or not self.fits(w,self.t,d):continue
            self.trace["worker_moves"].append(dict(worker_id=w["id"],start=self.t,end=self.t+d,
                from_hall=w["hall"],to_hall=hall))
            w.update(busy=max(w["busy"],self.t+d),hall=hall)
            break
        return None

    def plan_legs(self,path,start,loaded):
        legs,end=super().plan_legs(path,start,loaded)
        if not loaded and self._ready_tick is not None:end=max(end,self._ready_tick)
        return legs,end

    def future_move(self,p,dest,ready_tick,agv=None):
        if p.get("moving") or p["status"]!="processing":return False
        original=p["busy"];fleet=self.agvs;prior_ready=self._ready_tick
        p["busy"]=False;self._ready_tick=ready_tick;result=False
        # charge(a) is a decision for that particular vehicle.  The inherited
        # dispatch otherwise chooses globally and can consume another AGV while
        # silently leaving a low-SOC `a` without its charging opportunity.
        if agv is not None:self.agvs={agv["id"]:agv}
        try:result=super().move(p["id"],dest)
        finally:
            self.agvs=fleet;self._ready_tick=prior_ready
            if not result:p["busy"]=original
        if result:self.trace["moves"][-1].update(preposition=True,source_ready_tick=ready_tick)
        return result

    def charge(self,a):
        if self.weights.get("preposition",True) and a["busy"]<=self.t:
            lookahead=int(self.weights.get("preposition_ticks",10))
            candidates=[]
            for op in self.active:
                if op["process"]=="QA" or not self.t<op["end"]<=self.t+lookahead:continue
                for uid in op["unit_ids"]:
                    p=self.parts[uid]
                    if p.get("moving") or p["order_id"] not in self.admitted:continue
                    future=dict(p)
                    if p["rework"]:future["rework"]=p["rework"][1:]
                    else:future["step"]=p["step"]+1
                    if self.next_step(future) is None:continue
                    machine=self.choose_machine(future)
                    if machine:candidates.append((self.priority(p),op["end"],uid,machine["id"]))
            for _,ready,uid,dest in sorted(candidates):
                if self.future_move(self.parts[uid],dest,ready,agv=a):return True
        return super().charge(a)

    def process(self,*args,**kwargs):
        result=super().process(*args,**kwargs)
        if self.weights.get("worker_calendar",True) and result:
            offer=result if isinstance(result,dict) else self.trace["operations"][-1]
            # Gap filling can assign one worker to both disjoint setup and
            # processing intervals even when its busy-cache points farther
            # ahead.  Preserve both roles in the exported descriptive map.
            roles={}
            for interval in offer.get("worker_intervals",[]):
                roles.setdefault(interval["worker_id"],set()).update(interval["skills"])
            offer["worker_roles"]={wid:sorted(skills) for wid,skills in roles.items()}
            offer["worker_calendar_aware"]=True
        return result

    def complete(self,kind,record):
        super().complete(kind,record)
        if kind=="process":
            for uid in record["unit_ids"]:
                if self.parts[uid].get("moving"):self.parts[uid]["busy"]=True

    def observation(self):
        obs=super().observation()
        if self.weights.get("worker_calendar",True):
            obs["workers_free"]=sum(self.fits(w,self.t,1) for w in self.workers.values())
        return obs


def run(instance,weights=None,controller=None):
    return AdvancedFactory(instance,weights,controller).run()
