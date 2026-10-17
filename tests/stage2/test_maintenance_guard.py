import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

from stage2.check import check_trace,check_paired_causality
from stage2.maintenance_guard import AdmissionMaintenanceGuardFactory,public_outage_reasons,run
from stage2.recovery_routing import RecoveryRoutingFactory,BASE_WEIGHTS,run as frozen_run
from stage2.spec import build


class MaintenanceGuardTests(unittest.TestCase):
    def test_default_off_exact_physical_equivalence(self):
        instance=build(2,seed=0);opts=dict(admission=True,tool_policy={'mode':'hard'},recovery_policy={'enabled':True})
        old=frozen_run(instance,BASE_WEIGHTS,**opts);new=run(instance,BASE_WEIGHTS,**opts)
        for key in ('operations','moves','worker_moves','events','energy','metrics'):self.assertEqual(old[key],new[key],key)

    def test_half_open_boundaries_and_unrevealed_public_support(self):
        instance=build(2,seed=4);f=SimpleNamespace(i=instance,t=645,trace={'events':[]})
        self.assertFalse(public_outage_reasons(f,'F2',645,720))
        f.t=646;self.assertTrue(public_outage_reasons(f,'F2',646,721))
        f.t=720;self.assertFalse(public_outage_reasons(f,'F2',720,795)) # revealed mill_ok: no observed outage
        f.trace['events']=[dict(type='outage',tick=720,machine='F2',start=720,end=1080)]
        self.assertTrue(public_outage_reasons(f,'F2',720,795));f.t=1080
        self.assertFalse(public_outage_reasons(f,'F2',1080,1155))
        f.t=646;before=public_outage_reasons(f,'F2',646,721);instance['seed']=99999
        self.assertEqual(before,public_outage_reasons(f,'F2',646,721))

    def guarded_factory(self):
        f=AdmissionMaintenanceGuardFactory(build(2,seed=4),BASE_WEIGHTS,maintenance_outage_guard=True)
        f.t=720;f.trace['events'].append(dict(type='outage',tick=720,machine='F2',start=720,end=1080))
        f.machines['F2']['wear']=f.i['maintenance']['wear_limit'];return f

    def test_busy_hall_worker_tool_cache_restoration_on_service_exception(self):
        f=self.guarded_factory();busy=f.machines['F2']['busy'];workers=deepcopy(f.workers);tools=deepcopy(f.tools)
        machines_object=f.machines;workers_object=f.workers;tools_object=f.tools
        def fail(instance):
            self.assertEqual(instance.hall('F2'),'A');self.assertEqual(instance.machines['F2']['busy'],721)
            raise RuntimeError('injected')
        with patch.object(RecoveryRoutingFactory,'service_resources',fail):
            with self.assertRaisesRegex(RuntimeError,'injected'):f.service_resources()
        self.assertEqual(f.machines['F2']['busy'],busy);self.assertEqual(f.workers,workers);self.assertEqual(f.tools,tools)
        self.assertIs(f.machines,machines_object);self.assertIs(f.workers,workers_object);self.assertIs(f.tools,tools_object)

    def test_selection_exception_restores_previously_blocked_machine(self):
        f=self.guarded_factory();f.machines['S1']['wear']=f.i['maintenance']['wear_limit'];busy=f.machines['F2']['busy']
        def reasons(instance,mid,start,end):
            if mid=='S1':raise RuntimeError('selection failure')
            return [dict(source='observed',start=720,end=1080)]
        with patch('stage2.maintenance_guard.public_outage_reasons',reasons):
            with self.assertRaisesRegex(RuntimeError,'selection failure'):f.service_resources()
        self.assertEqual(f.machines['F2']['busy'],busy)

    def test_guard_does_not_rollback_legitimate_other_service_bookings(self):
        f=self.guarded_factory();wid=next(iter(f.workers));tid=next(iter(f.tools))
        def service(instance):
            instance.machines['F1']['busy']=820;instance.workers[wid]['busy']=820;instance.tools[tid]['busy']=820
        with patch.object(RecoveryRoutingFactory,'service_resources',service):f.service_resources()
        self.assertEqual(f.machines['F2']['busy'],0);self.assertEqual(f.machines['F1']['busy'],820)
        self.assertEqual(f.workers[wid]['busy'],820);self.assertEqual(f.tools[tid]['busy'],820)

    def test_no_outage_support_equivalence_and_actual_prefix_causality(self):
        instance=build(2,seed=0);instance['uncertainty_stages']=[]
        opts=dict(admission=True,tool_policy={'mode':'hard'},recovery_policy={'enabled':True})
        old=run(instance,BASE_WEIGHTS,**opts);new=run(instance,BASE_WEIGHTS,**opts,maintenance_outage_guard=True)
        for key in ('operations','moves','worker_moves','events','energy','metrics'):self.assertEqual(old[key],new[key],key)
        traces=[run(build(2,seed=s),BASE_WEIGHTS,**opts,maintenance_outage_guard=True) for s in (0,1,16)]
        self.assertTrue(all(check_trace(t)['valid'] for t in traces));self.assertTrue(check_paired_causality(traces)['valid'])

    def test_all_four_actual_invalids_are_preserved_and_guarded_runs_checked(self):
        for wip in (6,8):
            for guard in (0,4):
                weights=dict(BASE_WEIGHTS,wip_limit=wip,mode='turbo',due=1.,family=0.,tool_distance=8,qa_guard_threshold=guard)
                opts=dict(admission=True,tool_policy={'mode':'hard'},kit_reservation=False,recovery_policy={'enabled':True},
                    routing_policy={'eta_processes':[],'free_buffer_processes':[]})
                old=run(build(24,seed=4),weights,**opts);checked=check_trace(old)
                self.assertFalse(checked['valid']);self.assertTrue(any(x['code']=='machine_outage' for x in checked['issues']))
                new=run(build(24,seed=4),weights,**opts,maintenance_outage_guard=True)
                self.assertTrue(check_trace(new)['valid']);self.assertGreater(new['algorithm_audit']['maintenance_outage_guard']['blocked_eligible_calls'],0)


if __name__=='__main__':unittest.main()
