"""Protect scarce QA attendance from short upstream/assembly jobs.

This is an explicit heuristic restriction, not an added physical constraint.
All qualified assignments remain legal in the underlying factory. The guard
may deliberately leave a worker idle; experiments must retain regressions.
"""
from .advanced import AdvancedFactory


class SpecialistFactory(AdvancedFactory):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._qa_key=None;self._qa_count=0;self.qa_guard_calls=0
        self.trace['provenance']['solver']='scarce-QA-worker-guard'

    def qa_backlog(self):
        key=(self.t,len(self.trace['events']),len(self.trace['moves']),len(self.trace['operations']))
        if key!=self._qa_key:
            self._qa_count=sum(p['order_id'] in self.admitted and not p['accepted'] and
                (p['status']=='waiting' or p.get('moving',False)) and
                self.next_step(p) is not None and self.next_step(p)['process']=='QA'
                for p in self.parts.values())
            self._qa_key=key
        return self._qa_count

    def available_worker(self,skill,hall,length,allow_walk=True,start=None):
        threshold=int(self.weights.get('qa_guard_threshold',0))
        guarded=self.weights.get('qa_guard_skills',('machining','setup','assembly'))
        if threshold<=0 or skill not in guarded or self.qa_backlog()<threshold:
            return super().available_worker(skill,hall,length,allow_walk,start)
        # Replacing a worker's local list avoids mutating the numerical instance
        # or the immutable skill table. Restore it before any operation commit.
        saved={wid:w['skills'] for wid,w in self.workers.items()
               if 'qa' in w['skills'] and skill in w['skills']}
        try:
            for wid,skills in saved.items():self.workers[wid]['skills']=[s for s in skills if s!=skill]
            self.qa_guard_calls+=bool(saved)
            return super().available_worker(skill,hall,length,allow_walk,start)
        finally:
            for wid,skills in saved.items():self.workers[wid]['skills']=skills

    def finish(self):
        super().finish()
        self.trace['algorithm_audit']=dict(qa_guard_calls=self.qa_guard_calls,
            threshold=self.weights.get('qa_guard_threshold',0),
            scope='Algorithmic protected-skill dispatch restriction, no change to physical worker eligibility')


def run(instance,weights=None,controller=None):
    return SpecialistFactory(instance,weights,controller).run()
