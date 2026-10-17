from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import unittest

from stage2.identity_audit import audit_trace
from stage2.spec import build
from stage2.check import check_trace


def draw(seed,uid,attempt=0):return int.from_bytes(hashlib.sha256(f'{seed}:quality:{uid}:{attempt}'.encode()).digest()[:8],'big')/2**64


def renamed(value,before,after):
    if isinstance(value,str):return value.replace(before,after)
    if isinstance(value,list):return [renamed(x,before,after) for x in value]
    if isinstance(value,dict):return {renamed(k,before,after):renamed(v,before,after) for k,v in value.items()}
    return value


def structural_trace():
    instance=build(1,horizon=20,seed=0);pump='P01/pump/1'
    ops=[dict(id='A0',kind='process',process='ASSEMBLY',unit_id=pump,unit_ids=[pump],order_id='P01',
        start=1,end=2,is_rework=False,parent_unit_ids=[u['id'] for u in instance['units']],recipe_steps={pump:0},attempt=0),
        dict(id='Q0',kind='process',process='QA',unit_id=pump,unit_ids=[pump],order_id='P01',
        start=2,end=3,is_rework=False,parent_unit_ids=[],recipe_steps={pump:1},attempt=0)]
    return dict(schema='metaltech-stage2-trace.v1',instance=instance,operations=ops,moves=[],events=[
        dict(type='qa_result',tick=3,unit_id=pump,operation_id='Q0',passed=True,keyed_uniform=draw(0,pump))])


class IdentityTests(unittest.TestCase):
    def codes(self,trace,instance=None):return {r['code'] for r in audit_trace(trace,instance)['issues']}

    def test_canonical_partial_identity_and_legacy_metadata_note(self):
        trace=structural_trace();result=audit_trace(trace)
        self.assertTrue(result['valid'],result['issues'])
        self.assertIn('operation_id',result['metadata_notes'][0]['declared_value'])
        self.assertEqual(result['metadata_notes'][0]['actual_implemented_key'],'quality:{unit_id}:{attempt}')
        self.assertEqual(result['metrics']['initial_pump_births'],1)
        partial=deepcopy(trace);partial['operations']=[];partial['events']=[]
        self.assertTrue(audit_trace(partial)['valid'])

    def test_fully_rewritten_pump_identity_and_redrawn_qa_is_rejected(self):
        trace=renamed(structural_trace(),'P01/pump/1','P01/pump/777')
        trace['events'][0]['keyed_uniform']=draw(0,'P01/pump/777')
        self.assertIn('pump_birth_identity',self.codes(trace))
        self.assertNotIn('qa_stream_key',self.codes(trace))

    def test_initial_component_identity_duplicates_and_initial_pump_forbidden(self):
        trace=structural_trace();trace['instance']['units'].append(deepcopy(trace['instance']['units'][0]))
        self.assertIn('duplicate_initial_component',self.codes(trace))
        trace=renamed(structural_trace(),'P01/housing/1','P01/housing/2')
        self.assertIn('initial_component_identity',self.codes(trace))
        trace=structural_trace();trace['instance']['units'].append(dict(id='P01/pump/1',order_id='P01',recipe='pump'))
        self.assertIn('initial_component_identity',self.codes(trace))
        trace=structural_trace();trace['instance']['units'].pop()
        self.assertIn('initial_component_set',self.codes(trace))

    def test_urgent_order_and_three_components_cannot_be_renamed_together(self):
        trace=structural_trace();order=dict(id='U01',family='alloy_C',release_tick=10,due_tick=19,precision_required=True,urgent=True)
        trace['events'].append(dict(type='urgent_order',tick=10,order=order))
        trace['events'] += [dict(type='new_unit',tick=10,unit=dict(id=f'U01/{recipe}/1',order_id='U01',recipe=recipe,family='alloy_C',release_tick=10,initial_location='RAW_A')) for recipe in ('housing','rotor','flange')]
        self.assertTrue(audit_trace(trace)['valid'])
        altered=renamed(trace,'U01','U99')
        self.assertIn('urgent_order_identity',self.codes(altered))
        altered=renamed(trace,'U01/rotor/1','U01/rotor/54')
        self.assertIn('urgent_component_set',self.codes(altered))
        self.assertIn('unauthorized_component_birth',self.codes(altered))

    def test_replacement_is_exact_original_suffix_once_and_not_a_pump(self):
        trace=structural_trace();original=trace['instance']['units'][0];replacement=dict(original,id=original['id']+'~r1',release_tick=15)
        trace['events'] += [dict(type='replacement',tick=5,unit_id=original['id'],replacement_id=replacement['id'],release_tick=15),dict(type='new_unit',tick=5,unit=replacement)]
        self.assertTrue(audit_trace(trace)['valid'])
        altered=renamed(trace,'P01/housing/1~r1','P01/housing/1~r2')
        self.assertIn('replacement_identity',self.codes(altered))
        altered=deepcopy(trace);altered['events'].append(deepcopy(altered['events'][-2]))
        self.assertIn('replacement_identity',self.codes(altered))
        altered=deepcopy(trace);altered['events'][-2]['unit_id']='P01/pump/1';altered['events'][-2]['replacement_id']='P01/pump/1~r1'
        self.assertIn('replacement_identity',self.codes(altered))

    def test_one_initial_pump_birth_and_no_unknown_part_references(self):
        trace=structural_trace();extra=deepcopy(trace['operations'][0]);extra['id']='A1';extra['start']=4
        trace['operations'].append(extra)
        self.assertIn('duplicate_pump_birth',self.codes(trace))
        trace=structural_trace();trace['moves'].append(dict(id='M0',entity_type='part',unit_id='fresh-stream',start=4))
        self.assertIn('unknown_unit_reference',self.codes(trace))

    def test_operation_id_is_diagnostic_not_qa_random_key_and_attempt_is_bounded(self):
        trace=renamed(structural_trace(),'Q0','different-operation-ID')
        self.assertTrue(audit_trace(trace)['valid'])
        trace['events'][0]['keyed_uniform']=int.from_bytes(hashlib.sha256(b'0:quality:P01/pump/1:different-operation-ID:0').digest()[:8],'big')/2**64
        self.assertIn('qa_stream_key',self.codes(trace))
        trace=structural_trace();trace['operations'][1]['attempt']=2
        self.assertIn('qa_identity_reference',self.codes(trace))
        trace=structural_trace();trace['events'].append(deepcopy(trace['events'][0]))
        self.assertIn('duplicate_qa_identity',self.codes(trace))

    def test_retained_physical_trace_can_pass_legacy_checker_after_pump_rename_but_not_supplement(self):
        root=Path(__file__).resolve().parents[2]
        path=root/'output/stage2-search/adaptive-recovery-independent-audit/static-equivalence-n12-seed0-actor0.json.gz'
        if not path.exists():self.skipTest('Retained TRAIN trace unavailable')
        trace=json.loads(gzip.decompress(path.read_bytes()));instance=deepcopy(trace['instance'])
        self.assertTrue(check_trace(trace,instance)['valid']);self.assertTrue(audit_trace(trace,instance)['valid'])
        for suffix in range(2,100):
            candidate=f'P01/pump/{suffix}'
            if draw(instance['seed'],candidate)>.025:break
        altered=renamed(trace,'P01/pump/1',candidate)
        for event in altered['events']:
            if event.get('type')=='qa_result' and event.get('unit_id')==candidate:
                event['keyed_uniform']=draw(instance['seed'],candidate)
        legacy=check_trace(altered,instance)
        self.assertTrue(legacy['valid'],legacy['issues'])
        supplement=audit_trace(altered,instance)
        self.assertFalse(supplement['valid']);self.assertIn('pump_birth_identity',{i['code'] for i in supplement['issues']})


if __name__=='__main__':unittest.main()
