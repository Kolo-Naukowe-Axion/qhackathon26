"""Stronger scheduling over the same physical model: calendars and preposition.

Unlike the baseline decoder, workers may fill gaps before future reservations,
and an idle AGV may start its empty trip just before a known operation finishes.
Quality inspection outcomes are never anticipated.
"""
from .engine import Factory


class AdvancedFactory(Factory):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._ready_tick=None;self._calendar_key=None;self._bookings={}
        self.trace["provenance"]["solver"]="calendar-and-preposition-dispatch"

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

    def future_move(self,p,dest,ready_tick):
        if p.get("moving") or p["status"]!="processing":return False
        original=p["busy"];p["busy"]=False;self._ready_tick=ready_tick
        try:result=super().move(p["id"],dest)
        finally:self._ready_tick=None
        if not result:p["busy"]=original
        else:self.trace["moves"][-1].update(preposition=True,source_ready_tick=ready_tick)
        return result

    def charge(self,a):
        if a["busy"]<=self.t:
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
                if self.future_move(self.parts[uid],dest,ready):return True
        return super().charge(a)

    def complete(self,kind,record):
        super().complete(kind,record)
        if kind=="process":
            for uid in record["unit_ids"]:
                if self.parts[uid].get("moving"):self.parts[uid]["busy"]=True

    def observation(self):
        obs=super().observation()
        obs["workers_free"]=sum(self.fits(w,self.t,1) for w in self.workers.values())
        return obs


def run(instance,weights=None,controller=None):
    return AdvancedFactory(instance,weights,controller).run()
