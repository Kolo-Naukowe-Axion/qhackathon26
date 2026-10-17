"""Causal order admission over the unchanged physical simulation.

Factory.run has one admission-set update per tick. A small set adapter changes
only that algorithmic selection, retaining admitted orders until shipment. Every
order and material stays in the factory/objective; no physical WIP is erased.
The adapter also survives scenario deepcopy, so MPC continuations keep the rule.
"""
from copy import deepcopy

from .engine import Factory
from .advanced import AdvancedFactory
from .specialist import SpecialistFactory


class AdmissionSet(set):
    def __init__(self,factory,values=()):
        super().__init__(values);self.factory=factory;self.history=[]

    def __deepcopy__(self,memo):
        result=type(self).__new__(type(self));memo[id(self)]=result
        set.update(result,self)
        result.factory=deepcopy(self.factory,memo)
        result.history=deepcopy(self.history,memo)
        return result

    def update(self,values):
        f=self.factory;rule=f.weights.get('admission_rule','due')
        if rule=='due':return super().update(values)
        if rule not in ('family','priority','campaign'):raise ValueError('Unknown admission rule')
        slots=max(0,int(f.weights.get('wip_limit',6))-len(self))
        pending=[o for o in f.orders.values() if o['id'] not in self and o['id'] not in f.shipped]
        scale=f.i.get('time_scale',1)
        families=sorted(f.i['setup_matrix'])
        if rule=='campaign':
            # Prefer the family already occupying the most active WIP slots.
            # A known not-yet-released order retains its priority place, just
            # as in the baseline. No hidden urgent arrival is considered.
            counts={family:sum(f.orders[oid]['family']==family for oid in self) for family in families}
            anchor=min(families,key=lambda family:(-counts[family],
                min((o['due_tick'] for o in pending if o['family']==family),default=float('inf')),family))
        else:anchor=None
        def key(o):
            family=families.index(o['family'])
            if rule=='family':return (family,o['due_tick'],o['release_tick'],o['id'])
            if rule=='campaign':return (o['family']!=anchor,o['due_tick'],family,o['release_tick'],o['id'])
            score=(f.weights.get('admission_due',f.weights.get('due',1))*o['due_tick']/scale+
                   f.weights.get('admission_family',f.weights.get('family',0))*family-
                   f.weights.get('admission_urgent',0)*o.get('urgent',False))
            return (score,o['release_tick'],o['id'])
        head=sorted(pending,key=key)[:slots]
        chosen=[o['id'] for o in head if o['release_tick']<=f.t]
        super().update(chosen)
        if chosen:self.history.append(dict(tick=f.t,rule=rule,orders=chosen))


class AdmissionMixin:
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.admitted=AdmissionSet(self,self.admitted)
        self.trace['provenance']['admission']='causal order ranking; persistent admitted WIP'

    def finish(self):
        super().finish()
        self.trace['admission_history']=deepcopy(self.admitted.history)


class AdmissionFactory(AdmissionMixin,Factory):pass
class AdmissionAdvancedFactory(AdmissionMixin,AdvancedFactory):pass
class AdmissionSpecialistFactory(AdmissionMixin,SpecialistFactory):pass


def run(instance,weights=None,controller=None,*,backend='base'):
    classes=dict(base=AdmissionFactory,advanced=AdmissionAdvancedFactory,specialist=AdmissionSpecialistFactory)
    return classes[backend](instance,weights,controller).run()
