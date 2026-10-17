"""Legal mode substitution must be consistent in estimates, offers and commits."""
from copy import deepcopy
from unittest.mock import patch
import unittest

from stage2.advanced import AdvancedFactory
from stage2.check import check_trace,check_paired_causality
from stage2.kitting import AdmissionKitToolingSpecialistFactory
from stage2.process_modes import ProcessModesFactory,run
from stage2.spec import build


class ProcessModeTests(unittest.TestCase):
    weights=dict(wip_limit=4,mode='standard',lease_calibration=True,worker_calendar=True,
                 preposition=False,qa_guard_threshold=2,admission_rule='family')

    def factory(self,modes=None):
        return ProcessModesFactory(build(2),self.weights,process_modes=modes,tool_policy=dict(mode='hard'))

    def test_standard_default_reproduces_frozen_combination_exactly(self):
        instance=build(3,seed=0);before=deepcopy(instance)
        expected=AdmissionKitToolingSpecialistFactory(instance,self.weights,tool_policy=dict(mode='hard')).run()
        actual=run(instance,self.weights)
        for key in ('operations','moves','worker_moves','events','energy','metrics','admission_history'):
            self.assertEqual(actual[key],expected[key],key)
        self.assertEqual(instance,before)
        self.assertTrue(check_trace(actual)['valid'])

    def test_welding_preview_preparation_and_commit_use_same_mode_duration_and_power(self):
        f=self.factory({'S':'careful'});part=f.parts['P01/flange/1']
        part.update(step=1,status='waiting',location='S1',busy=False)
        f.tools['weld1'].update(location='S1',used=0,busy=0)
        preview=f.process(f.machines['S1'],[part],preview=True)
        self.assertEqual((preview['mode'],preview['processing_ticks'],preview['power_kw']),('careful',90,8))
        self.assertEqual(f.trace['operations'],[])
        self.assertFalse(f.process(f.machines['S1'],[part],prepare_only=True))
        self.assertEqual(f.trace['operations'],[])
        self.assertTrue(f.process(f.machines['S1'],[part]))
        committed=f.trace['operations'][-1]
        for key in ('mode','start','end','processing_ticks','power_kw','worker_intervals','tool_ids'):
            self.assertEqual(preview[key],committed[key],key)
        self.assertEqual(f.tools['weld1']['used'],90)

    def test_repair_keeps_standard_and_eta_context_is_restored(self):
        f=self.factory({'ASSEMBLY':'careful'})
        part=deepcopy(f.parts['P01/housing/1']);part.update(id='P01/pump/1',recipe='pump',step=1,
            location='A1',status='waiting',busy=False,rework=[dict(process='ASSEMBLY',base_ticks=45),dict(process='QA',base_ticks=45)])
        f.parts[part['id']]=part
        preview=f.process(f.machines['A1'],[part],preview=True)
        self.assertTrue(preview)
        self.assertEqual((preview['mode'],preview['processing_ticks']),('standard',45))
        with patch.object(AdvancedFactory,'estimated_machine_finish',side_effect=lambda *args:f.selected_mode('ASSEMBLY','P01')):
            self.assertEqual(f.estimated_machine_finish(part,f.machines['A1']),'standard')
        self.assertEqual(f.selected_mode('ASSEMBLY','P01'),'careful')
        with patch.object(AdvancedFactory,'remaining_processing',side_effect=RuntimeError('estimate failure')):
            with self.assertRaisesRegex(RuntimeError,'estimate failure'):f.remaining_processing(part)
        self.assertEqual(f.selected_mode('ASSEMBLY','P01'),'careful')

    def test_preparation_delegation_and_explicit_mode_are_preserved(self):
        f=self.factory({'S':'careful'});part=f.parts['P01/flange/1']
        part.update(step=1,status='waiting',location='S1',busy=False)
        with patch.object(AdmissionKitToolingSpecialistFactory,'process',return_value=False) as parent:
            f.process(f.machines['S1'],[part],prepare_only=True)
            self.assertEqual(parent.call_args.args[2],'careful')
            self.assertTrue(parent.call_args.args[-1])
            f.process(f.machines['S1'],[part],mode='careful',preview=True)
            self.assertEqual(parent.call_args.args[2],'careful')

    def test_precision_certification_and_turbo_guard_are_not_overridden(self):
        f=self.factory({'S':'careful','ASSEMBLY':'careful'});f.weights['mode']='turbo'
        f.orders['P01']['precision_required']=True
        self.assertEqual(f.selected_mode('T','P01'),'standard')
        self.assertEqual(f.selected_mode('F','P01'),'standard')
        self.assertEqual(f.selected_mode('QA','P01'),'precision')
        self.assertEqual(f.selected_mode('S','P01'),'careful')

    def test_all_variants_replay_and_paired_prefix_causality(self):
        for modes in ({},{'S':'careful'},{'ASSEMBLY':'careful'},{'S':'careful','ASSEMBLY':'careful'}):
            traces=[run(build(2,seed=seed),self.weights,process_modes=modes) for seed in (0,1)]
            for trace in traces:
                checked=check_trace(trace);self.assertTrue(checked['valid'],checked['issues'])
                self.assertTrue(checked['terminal_requirements_met'])
                for op in trace['operations']:
                    if op.get('is_rework') and op['process']=='ASSEMBLY':self.assertEqual(op['mode'],'standard')
                    if op.get('mode')=='careful':self.assertIn(op['process'],modes)
            causal=check_paired_causality(traces);self.assertTrue(causal['valid'],causal)

    def test_rejects_unsupported_mode_or_process(self):
        for modes in ({'S':'turbo'},{'T':'careful'}):
            with self.assertRaises(ValueError):self.factory(modes)


if __name__=='__main__':unittest.main()
