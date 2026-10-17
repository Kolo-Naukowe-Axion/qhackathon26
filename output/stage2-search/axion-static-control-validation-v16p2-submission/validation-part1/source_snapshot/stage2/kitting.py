"""Reserve complete BOM space before sending partial kits to assembly.

This is a causal dispatch restriction over the unchanged factory. A conceptual
reservation does not create inventory, increase buffers, teleport parts or remove
any order from the objective. Actual moves and parent consumption use the original
engine. It prevents one partial-kit fragmentation pattern, not every deadlock.
"""
from collections import Counter
from copy import deepcopy

from .advanced import AdvancedFactory
from .specialist import SpecialistFactory
from .tooling import ToolingFactory,ToolingSpecialistFactory
from .admission import AdmissionMixin


class KitMixin:
    def __init__(self,*args,kit_reservation=True,**kwargs):
        super().__init__(*args,**kwargs)
        self.kit_reservation=bool(kit_reservation)
        self.kit_history=[];self.kit_deferred_ticks=0
        self.trace['provenance']['kit_space_reservation']=self.kit_reservation

    def pending_kit_assignments(self):
        return {oid:mid for oid,mid in self.assembly_target.items()
                if f'{oid}/pump/1' not in self.parts and oid not in self.shipped}

    def assembly(self):
        if not self.kit_reservation:return super().assembly()
        assigned=self.pending_kit_assignments();load=Counter(assigned.values())
        stations=[m for m in self.machines.values() if m['process']=='ASSEMBLY']
        # The engine's explicit BOM is housing + rotor + flange: three units.
        # Count conceptual whole-kit places, not just the first arrived parts.
        for oid in sorted(self.orders,key=lambda x:(self.orders[x]['due_tick'],x)):
            if oid in assigned or f'{oid}/pump/1' in self.parts:continue
            ready=[p for p in self.parts.values() if p['order_id']==oid and
                   p['accepted'] and p['recipe']!='pump' and
                   p['status']=='waiting' and not p['busy']]
            if not ready:continue
            eligible=[m for m in stations if 3*(load[m['id']]+1)<=m['input_capacity']]
            if not eligible:
                self.kit_deferred_ticks+=1;continue
            target=min(eligible,key=lambda m:(load[m['id']],
                self.input_count(m['id'])+self.reserved[m['id']],m['id']))['id']
            self.assembly_target[oid]=target;assigned[oid]=target;load[target]+=1
            self.kit_history.append(dict(tick=self.t,order_id=oid,station=target,places=3))
        # Only filter this scheduling pass. All observed orders remain in the
        # inventory, later dispatch, controller observations and final objective.
        original=self.orders
        self.orders={oid:order for oid,order in original.items() if oid in assigned}
        try:return super().assembly()
        finally:self.orders=original

    def finish(self):
        super().finish()
        self.trace.setdefault('algorithm_audit',{})['kit_reservation']=dict(
            enabled=self.kit_reservation,deferred_order_ticks=self.kit_deferred_ticks,
            history=deepcopy(self.kit_history),scope='Whole-kit admission restriction; original physical buffers and BOM')


class KitFactory(KitMixin,AdvancedFactory):pass
class KitSpecialistFactory(KitMixin,SpecialistFactory):pass
class KitToolingFactory(KitMixin,ToolingFactory):pass
class KitToolingSpecialistFactory(KitMixin,ToolingSpecialistFactory):pass
class AdmissionKitFactory(AdmissionMixin,KitFactory):pass
class AdmissionKitSpecialistFactory(AdmissionMixin,KitSpecialistFactory):pass
class AdmissionKitToolingFactory(AdmissionMixin,KitToolingFactory):pass
class AdmissionKitToolingSpecialistFactory(AdmissionMixin,KitToolingSpecialistFactory):pass


def run(instance,weights=None,controller=None,*,tool_policy=None,specialist=False,kit_reservation=True,admission=False):
    if admission:
        if tool_policy is None:cls=AdmissionKitSpecialistFactory if specialist else AdmissionKitFactory
        else:cls=AdmissionKitToolingSpecialistFactory if specialist else AdmissionKitToolingFactory
    elif tool_policy is None:cls=KitSpecialistFactory if specialist else KitFactory
    else:cls=KitToolingSpecialistFactory if specialist else KitToolingFactory
    options=dict(kit_reservation=kit_reservation)
    if tool_policy is not None:options['tool_policy']=tool_policy
    return cls(instance,weights,controller,**options).run()
