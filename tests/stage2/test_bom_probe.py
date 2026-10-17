import unittest
from copy import deepcopy

from stage2.bom_probe import AdmissionBOMFactory,diagnostic_tasks,flow_metrics,run,variants
from stage2.check import check_trace,check_paired_causality
from stage2.recovery_routing import BASE_WEIGHTS,run as frozen_run
from stage2.spec import build


class BOMProbeTests(unittest.TestCase):
    def test_control_matches_existing_backend(self):
        instance=build(2,seed=0);weights=dict(BASE_WEIGHTS,bom_priority=False)
        options=dict(admission=True,tool_policy={'mode':'hard'},recovery_policy={'enabled':True},
            routing_policy={'eta_processes':['QA'],'free_buffer_processes':[]})
        expected=frozen_run(instance,weights,**options);actual=run(instance,weights,**options)
        for key in ('operations','moves','worker_moves','events','energy','metrics'):self.assertEqual(expected[key],actual[key],key)

    def test_predeclared_bounded_domains_and_scale_meaning(self):
        tasks=diagnostic_tasks();self.assertEqual(len(tasks),192)
        self.assertEqual({t['config']['orders'] for t in tasks},{16,24})
        self.assertEqual({t['config']['seed'] for t in tasks},set(range(8)))
        self.assertTrue(all(t['weights']['wip_limit']==4 and t['weights']['qa_guard_threshold']==4 for t in tasks))
        v={v['name']:v for v in variants()}
        for rule in ('join','critical','slack'):
            for key in ('bom_join_weight','bom_progress_weight','bom_tail_weight','bom_slack_weight'):
                self.assertEqual(v[f'{rule}-quarter']['weights'][key]*4,v[f'{rule}-default']['weights'][key])

    def test_actual_priority_rules_remain_physical_and_causal(self):
        for rule in ('join','critical','slack'):
            traces=[]
            for seed in (0,1,16):
                trace=run(build(2,seed=seed),dict(BASE_WEIGHTS,bom_priority=rule),admission=True,
                    tool_policy={'mode':'hard'},recovery_policy={'enabled':True},
                    routing_policy={'eta_processes':['QA'],'free_buffer_processes':[]})
                self.assertTrue(check_trace(trace)['valid']);traces.append(trace)
                flow=flow_metrics(trace)
                self.assertGreaterEqual(flow['accepted_kit_ready_to_initial_assembly_minutes'],0)
                self.assertEqual(flow['assembly_starts'],sum(o['process']=='ASSEMBLY' and bool(o['parent_unit_ids']) for o in trace['operations']))
            self.assertTrue(check_paired_causality(traces)['valid'])

    def test_public_bom_score_changes_after_observed_peer_acceptance(self):
        factory=AdmissionBOMFactory(build(2,seed=0),dict(BASE_WEIGHTS,bom_priority='join',bom_join_weight=6,bom_progress_weight=0))
        part=next(p for p in factory.parts.values() if p['recipe']=='housing')
        peer=next(p for p in factory.parts.values() if p['order_id']==part['order_id'] and p['recipe']=='rotor')
        before=factory.priority(part);peer['accepted']=True;factory._bom_key=None
        after=factory.priority(part);self.assertEqual(before-after,6)
        factory.i['seed']=987654;factory._bom_key=None;self.assertEqual(after,factory.priority(part))

    def test_flow_accounting_includes_censored_stranded_components(self):
        events=[dict(type='qa_result',unit_id=u,tick=t,passed=True) for u,t in [('O/housing/1',20),('O/rotor/1',25),('O/flange/1',30),('Z/rotor/1',40)]]
        events += [dict(type='consume',unit_id=u,tick=50) for u in ('O/housing/1','O/rotor/1','O/flange/1')]
        def op(process,start,end,units,parents=[]):return dict(id=f'O{start}',kind='process',process=process,start=start,end=end,
            unit_ids=units,parent_unit_ids=parents,worker_intervals=[dict(start=start,end=end)],order_id='O')
        trace=dict(instance={'horizon_ticks':100,'tick_minutes':1},events=events,operations=[
            op('T',0,5,['O/housing/1']),op('QA',10,20,['O/housing/1']),
            op('ASSEMBLY',50,60,['O/pump/1'],['O/housing/1','O/rotor/1','O/flange/1'])])
        flow=flow_metrics(trace)
        self.assertEqual(flow['accepted_component_wait_until_consumption_or_horizon_minutes'],135)
        self.assertEqual(flow['stranded_accepted_components'],1)
        self.assertEqual(flow['pre_qa_processing_completion_to_inspection_start_minutes'],5)
        self.assertEqual(flow['accepted_kit_ready_to_initial_assembly_minutes'],20)


if __name__=='__main__':unittest.main()
