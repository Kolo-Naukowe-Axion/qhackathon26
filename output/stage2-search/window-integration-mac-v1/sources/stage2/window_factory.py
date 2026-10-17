"""Causal, advisory integration of complete planning-window QUBOs.

The window is a relaxation of the physical factory. Its next-machine advice is
subject to unchanged engine routing/transport/input/crew/tool/power guards.
Planned start times/workers are predictions, NOT committed physical executions.
The adapter does not inspect a seed, hidden outcomes or future event tables.
"""
from copy import deepcopy
import math
import time

from .engine import Factory
from .spec import duration
from .bounds import shortest_costs
from .window_qubo import compile_qubo,digest,solve_cp
from .window_search import constructive_multistart,anneal,block_search


def extract(factory,horizon=480,grid=15,max_parts=4,depth=2):
    f=factory;horizon=min(horizon,f.i['horizon_ticks']-f.t)
    if horizon<grid:raise ValueError('Insufficient remaining window')
    ready=sorted((p for p in f.parts.values()if p['status']=='waiting'and not p['busy']and not p['accepted']and not p['rework']and p['order_id']in f.admitted),
                 key=lambda p:(f.orders[p['order_id']]['due_tick'],Factory.priority(f,p),p['id']))[:max_parts]
    if not ready:raise ValueError('No admitted released idle parts with a standard remaining route')
    operations=[];distances=shortest_costs(f.i,lambda e:e['ticks']);handling=f.i['transport']['load_ticks']+f.i['transport']['unload_ticks']
    used=set()
    for part in ready:
        prior=[];route=f.i['recipes'][part['recipe']];order=f.orders[part['order_id']]
        remaining=route[part['step']:part['step']+depth]
        # Remaining outside-window processing is an explicitly disclosed lower bound.
        tail=sum(min(duration(f.i,s['process'],s['base_ticks'],m,'precision'if s['process']=='QA'and order['precision_required']else'standard')for m in f.machines.values()if m['process']==s['process'])for s in route[part['step']+depth:])
        for relative,step in enumerate(remaining):
            process=step['process'];mode=f.weights.get('mode','standard')if process in('T','F')else('precision'if process=='QA'and order['precision_required']else'standard')
            if order['precision_required']and mode=='turbo':mode='standard'
            durations={m['id']:duration(f.i,process,step['base_ticks'],m,mode)for m in f.machines.values()if m['process']==process};used.update(durations)
            initial={m:(0 if part['location']==m else distances[part['location']][m]+handling)for m in durations}if not prior else{}
            oid=f'{part["id"]}@{part["step"]+relative}';rule=f.i['attendance'][process]
            operations.append(dict(id=oid,unit_id=part['id'],recipe_step=part['step']+relative,durations=durations,skill=f.i['process_skills'][process],
                attendance=rule['kind'],start_attendance=rule['ticks'],release=0,machine_release=initial,due=order['due_tick']-f.t-tail,predecessors=list(prior)))
            prior=[oid]
    machines={}
    for mid in sorted(used):
        m=f.machines[mid];ready_tick=max(0,m['busy']-f.t,f.outages.get(mid,0)-f.t)
        if ready_tick<horizon:machines[mid]=dict(hall=m['hall'],available=[[ready_tick,horizon]])
        else:machines[mid]=dict(hall=m['hall'],available=[[horizon,horizon+1]])
    workers={}
    for wid,w in f.workers.items():
        active=[];begin=None
        for t in range(horizon+1):
            clock=(f.t+t)%f.i['day_ticks'];lo,hi=w['daily_shift'];legal=t<horizon and lo<=clock<hi and not any(a<=clock<b for a,b in w['breaks'])
            if legal and begin is None:begin=t
            if not legal and begin is not None:active.append([begin,t]);begin=None
        if active:workers[wid]=dict(skills=list(w['skills']),initial_hall=w['hall'],ready=max(0,w['busy']-f.t),available=active)
    public=dict(tick=f.t,parts=[deepcopy(p)for p in ready],machines={k:dict(busy=f.machines[k]['busy'],family=f.machines[k]['family'],output=sorted(f.machines[k]['output']))for k in machines},
        workers={k:dict(busy=w['busy'],hall=w['hall'])for k,w in f.workers.items()},outages=dict(f.outages))
    return dict(name='Observed causal factory planning window',horizon=horizon,grid=grid,operations=operations,machines=machines,workers=workers,
        transport_lags={a:{b:0 if a==b else distances[a][b]+handling for b in machines}for a in machines},worker_travel=f.i['worker_travel_ticks'],
        provenance=dict(actual_recorded_snapshot=True,tick=f.t,public_state=public,public_state_sha256=digest(public),
            scope='Next recipe prefix for idle admitted parts; no unrevealed random outcomes. Active machine and worker occupations anchored. No future assembly/BOM lookahead for uncreated pumps.',
            objective='Terminal prefix tardiness with minimum outside-prefix processing tail, then makespan; not full-factory shipment objective',
            excluded=['sequence-dependent setup','tools/service','AGV contention/empty motion','finite buffers/output blocking','energy','future quality/recovery','heat batching','unselected parts/future releases']))


class PlanningFactory(Factory):
    def __init__(self,instance,weights=None,method='compressed_qaoa',interval=240,max_parts=4,iterations=8):
        super().__init__(instance,weights);self.planning_method=method;self.plan_interval=interval;self.max_parts=max_parts;self.plan_iterations=iterations
        self.next_plan=0;self.advice={};self.planning_records=[];self.planner_busy=False;self.routing_advice_hits=0

    def refresh(self):
        if self.planner_busy or self.t<self.next_plan:return
        self.next_plan=self.t+self.plan_interval;self.planner_busy=True;began=time.perf_counter();record=dict(tick=self.t,method=self.planning_method)
        self.advice={}
        try:
            p=extract(self,max_parts=self.max_parts);record['problem']=p;q=compile_qubo(p,support_pruning=True,max_variables=1800);record['qubo']=q.metadata()
            if self.planning_method=='cp':
                result=solve_cp(p,.5,1);record['solver']=result;decoded=result.get('check');plan=result.get('plan',[])
            else:
                initial=constructive_multistart(q,12,101+self.t);record['initializer']=initial
                if not initial['valid']:raise ValueError('Window initializer failed; retain original dispatch')
                if self.planning_method=='constructive':result=initial
                elif self.planning_method=='anneal':result=anneal(q,101+self.t,6000,1,initial['bits'])
                else:result=block_search(q,initial['bits'],self.planning_method,101+self.t,self.plan_iterations,256,24)
                record['solver']=result;decoded=result.get('decoded');plan=decoded.get('plan',[])if decoded else[]
            if decoded and decoded['valid']:
                lookup={o['id']:o for o in p['operations']}
                for row in plan:
                    op=lookup[row['operation']];key=(op['unit_id'],op['recipe_step']);self.advice[key]=dict(row)
                record['valid_window_plan']=True
            else:record['valid_window_plan']=False
        except(ValueError,KeyError)as exc:record.update(valid_window_plan=False,fallback_reason=str(exc))
        finally:
            record['total_wall_seconds']=time.perf_counter()-began;self.planning_records.append(record);self.planner_busy=False

    def priority(self,p):
        self.refresh();row=self.advice.get((p['id'],p['step']))
        # Planned relative starts only order current ready work; never force execution.
        return row['start']-100000 if row else super().priority(p)

    def choose_machine(self,p):
        row=self.advice.get((p['id'],p['step']))
        if row:
            m=self.machines[row['machine']];step=self.next_step(p)
            if step and m['process']==step['process']and self.input_count(m['id'])+self.reserved[m['id']]<m['input_capacity']:
                self.routing_advice_hits+=1;return m
        return super().choose_machine(p)

    def finish(self):
        super().finish();self.trace['planning_windows']=self.planning_records
        self.trace['planning_scope']=dict(kind='advisory machine routing/priority, guarded by original physical engine',method=self.planning_method,
            window_calls=len(self.planning_records),valid_window_plans=sum(r['valid_window_plan']for r in self.planning_records),
            routing_advice_hits=self.routing_advice_hits,physical_qpu_calls=0,
            full_plans_committed=False,full_factory_optimality_claim=False)


def attach_planner(factory,method='compressed_qaoa',interval=240,max_parts=4,iterations=8):
    """Reversible runtime mixin, preserving the configured strong factory adapters."""
    factory.__class__=type('Window'+type(factory).__name__,(PlanningFactory,type(factory)),{})
    factory.planning_method=method;factory.plan_interval=interval;factory.max_parts=max_parts;factory.plan_iterations=iterations
    factory.next_plan=0;factory.advice={};factory.planning_records=[];factory.planner_busy=False;factory.routing_advice_hits=0
    return factory
