import unittest
from copy import deepcopy
from unittest.mock import patch

from stage2.check import check_trace,check_paired_causality
from stage2.dispatch import choose
from stage2.kit_recovery import RecoveryFactory,run as original_run
from stage2.recovery_routing import BASE_WEIGHTS
from stage2.selector_domain import (AdmissionSelectorDomainFactory,CREW_RUN_SOURCE,
    assignment_payload,run,_derived_run)
from stage2.spec import build


class SelectorDomainTests(unittest.TestCase):
    def test_default_off_exact_physical_equivalence(self):
        instance=build(2,seed=0);weights=dict(BASE_WEIGHTS,selector='exact')
        opts=dict(admission=True,tool_policy={'mode':'hard'},recovery_policy={'enabled':True})
        expected=original_run(instance,weights,**opts);actual=run(instance,weights,**opts)
        for key in ('operations','moves','worker_moves','events','energy','metrics'):self.assertEqual(expected[key],actual[key],key)

    def test_derived_loop_has_only_audited_hooks_and_refuses_engine_drift(self):
        for name in ('expand_dispatch','prepare_selected_crews','verify_selected_commits'):self.assertEqual(CREW_RUN_SOURCE.count('self.'+name+'('),1)
        with patch('stage2.selector_domain.ENGINE_SHA256','wrong'):
            with self.assertRaises(RuntimeError):_derived_run()

    def test_real_worker_alternatives_restore_two_parallel_starts(self):
        factory=AdmissionSelectorDomainFactory(build(2,seed=0),dict(BASE_WEIGHTS,selector='exact'),
            tool_policy={'mode':'hard'},selector_domain={'mode':'expanded','audit_boundaries':0})
        parts=[p for p in factory.parts.values() if p['recipe']=='housing'][:2];requests=[];offers=[]
        for p,mid in zip(parts,('T1','T2')):
            p.update(location=mid,status='waiting');request=(factory.machines[mid],[p],'standard');requests.append(request)
            offers.append(factory.process(*request,preview=True))
        self.assertTrue(all(offers));self.assertEqual([o['worker_ids'] for o in offers],[['W01'],['W01']])
        priorities=[factory.priority(parts[0]) for _,parts,_ in requests]
        frozen,_=choose(offers,factory.i,[],factory.t,factory.grid_cap,priorities,'exact');self.assertEqual(len(frozen),1)
        expanded,requests=factory.expand_dispatch(offers,requests)
        selected,evidence=choose(expanded,factory.i,[],factory.t,factory.grid_cap,
            [factory.priority(parts[0]) for _,parts,_ in requests],'exact')
        self.assertEqual(len(selected),2);factory.prepare_selected_crews(expanded,selected);evidence['committed']=[]
        for idx in selected:
            self.assertTrue(factory.process(*requests[idx]));evidence['committed'].append(f'C{idx}')
            self.assertEqual(assignment_payload(expanded[idx]),assignment_payload(factory.trace['operations'][-1]))
        factory.verify_selected_commits(evidence)
        self.assertEqual({o['worker_ids'][0] for o in factory.trace['operations']},{'W01','W04'})

    def test_three_operations_two_worker_hall_cannot_start_three(self):
        # Explicit allocation fixture: every operation has two crew alternatives.
        instance=build(2,seed=0);offers=[]
        for job in range(3):
            for worker in ('W01','W04'):
                offers.append(dict(unit_ids=[f'unit{job}'],machine_id=f'M{job}',worker_ids=[worker],
                    worker_intervals=[dict(worker_id=worker,start=0,end=5)],worker_calendar_aware=True,
                    tool_ids=[],start=0,end=60,power_kw=1))
        selected,evidence=choose(offers,instance,[],0,100,[0]*6,'exact')
        self.assertEqual(len(selected),2)
        self.assertEqual(len({offers[idx]['unit_ids'][0] for idx in selected}),2)
        self.assertEqual(len({offers[idx]['worker_ids'][0] for idx in selected}),2)

    def test_worker_skill_and_context_restoration_on_exception(self):
        factory=AdmissionSelectorDomainFactory(build(2),BASE_WEIGHTS,selector_domain={'mode':'expanded'})
        saved=deepcopy({wid:w['skills'] for wid,w in factory.workers.items()})
        factory._crew_context=dict(primary='W01',setup='W02',_calls=0,_setup_ticks=0)
        with patch.object(RecoveryFactory,'available_worker',side_effect=RuntimeError('injected')):
            with self.assertRaises(RuntimeError):factory.available_worker('machining','A',5,False)
        self.assertEqual(saved,{wid:w['skills'] for wid,w in factory.workers.items()})

    def test_actual_full_checker_causal_assignments_and_explicit_fallback(self):
        traces=[]
        for seed in (0,1,16):
            trace=run(build(2,seed=seed),dict(BASE_WEIGHTS,selector='exact'),admission=True,
                tool_policy={'mode':'hard'},recovery_policy={'enabled':True},selector_domain={'mode':'expanded','audit_boundaries':0})
            self.assertTrue(check_trace(trace)['valid']);traces.append(trace)
            actual={(op['start'],op.get('dispatch_candidate_id')):op for op in trace['operations'] if op.get('dispatch_candidate_id')}
            for d in trace['qubo_decisions']:
                self.assertEqual(sorted(d['result']['selected']),sorted(d['committed']))
                for cid in d['result']['selected']:
                    offered=d['offered_operations'][int(cid[1:])]
                    self.assertEqual(assignment_payload(offered),assignment_payload(actual[(d['tick'],cid)]))
        self.assertTrue(check_paired_causality(traces)['valid'])
        fallback=run(build(2,seed=0),dict(BASE_WEIGHTS,selector='exact'),admission=True,
            tool_policy={'mode':'hard'},recovery_policy={'enabled':True},selector_domain={'mode':'expanded','max_candidates':1,'audit_boundaries':0})
        self.assertTrue(check_trace(fallback)['valid'])
        self.assertGreater(fallback['algorithm_audit']['selector_domain']['counts']['oversize_original_pool_fallbacks'],0)


if __name__=='__main__':unittest.main()
