"""Bounded assembly-space borrowing to release a blocked inspection output.

Whole-kit reservations are conservative: four incomplete kits can hold only
eight actual assembly places yet deny an unrelated accepted QA output. Borrow
one physical place while leaving one free for a reserved kit's missing part.
Only that first component may enter until the reservation overbooking resolves.
This is a causal recovery heuristic, not a general deadlock-freedom theorem.
"""
from collections import Counter
from copy import deepcopy

from .admission import AdmissionMixin
from .kitting import KitToolingSpecialistFactory


class EscapeMixin:
    def __init__(self,*args,escape_policy=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.escape_policy=dict(enabled=True,quiet_ticks=60,quota=1)
        self.escape_policy.update(deepcopy(escape_policy or {}))
        if self.escape_policy['quiet_ticks']<0 or self.escape_policy['quota'] not in (1,2):
            raise ValueError('Nonnegative quiet interval and explicit quota1/2 required')
        self.escape_orders={};self.escape_history=[]
        self.trace['provenance']['kit_space_escape']=dict(self.escape_policy)

    def escape_occupancy(self,oid,mid):
        return sum(p['order_id']==oid and p['recipe']!='pump' and
            p['status'] not in ('consumed','shipped','scrap','disposed') and
            ((p.get('moving') and p.get('target_location')==mid) or
             (not p.get('moving') and p['location']==mid)) for p in self.parts.values())

    def move(self,unit,dest,entity_type='part'):
        if self.escape_policy['enabled'] and entity_type=='part' and dest in self.machines:
            p=self.parts[unit];oid=p['order_id']
            if self.escape_orders.get(oid)==dest and p['recipe']!='pump':
                assigned=Counter(self.pending_kit_assignments().values())
                if 3*assigned[dest]>self.machines[dest]['input_capacity'] and \
                   self.escape_occupancy(oid,dest)>=self.escape_policy['quota']:
                    return False
        return super().move(unit,dest,entity_type)

    def assembly(self):
        if self.escape_policy['enabled'] and self.kit_reservation:
            latest=max((op['start'] for op in self.trace['operations'] if op['kind']=='process'),default=0)
            if self.t-latest>=self.escape_policy['quiet_ticks']:
                assigned=self.pending_kit_assignments();loads=Counter(assigned.values())
                stations=[m for m in self.machines.values() if m['process']=='ASSEMBLY']
                # Borrow only when normal whole-kit admission has no room.
                full=not any(3*(loads[m['id']]+1)<=m['input_capacity'] for m in stations)
                blocked=[p for p in self.parts.values() if p['order_id'] not in assigned and
                    p['accepted'] and p['recipe']!='pump' and p['status']=='waiting' and
                    not p['busy'] and p['location'] in self.machines and
                    self.machines[p['location']]['process']=='QA' and
                    p['id'] in self.machines[p['location']]['output']]
                for p in sorted(blocked,key=lambda p:(self.orders[p['order_id']]['due_tick'],p['id'])) if full else ():
                    oid=p['order_id']
                    if oid in assigned:continue
                    eligible=[m for m in stations if
                        m['input_capacity']-self.input_count(m['id'])-self.reserved[m['id']]>=self.escape_policy['quota']+1
                        and not any(target==m['id'] and other in assigned and
                            3*loads[m['id']]>m['input_capacity'] for other,target in self.escape_orders.items())]
                    if not eligible:break
                    mid=min(eligible,key=lambda m:(self.input_count(m['id'])+self.reserved[m['id']],m['id']))['id']
                    self.assembly_target[oid]=mid;assigned[oid]=mid;loads[mid]+=1
                    self.escape_orders[oid]=mid
                    self.escape_history.append(dict(tick=self.t,order_id=oid,station=mid,blocked_unit=p['id'],quota=self.escape_policy['quota']))
        return super().assembly()

    def finish(self):
        super().finish()
        self.trace.setdefault('algorithm_audit',{})['kit_escape']=dict(
            policy=dict(self.escape_policy),history=deepcopy(self.escape_history),
            scope='Algorithm-only limited overbooking; every physical move and capacity check remains original')


class EscapeFactory(EscapeMixin,KitToolingSpecialistFactory):pass
class AdmissionEscapeFactory(AdmissionMixin,EscapeFactory):pass


def run(instance,weights=None,controller=None,*,tool_policy=None,kit_reservation=True,admission=False,escape_policy=None):
    cls=AdmissionEscapeFactory if admission else EscapeFactory
    return cls(instance,weights,controller,tool_policy=tool_policy,
        kit_reservation=kit_reservation,escape_policy=escape_policy).run()
