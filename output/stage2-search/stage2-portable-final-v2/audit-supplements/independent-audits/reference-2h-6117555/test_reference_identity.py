from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('reference_encounter_identity',HERE/'reference_identity.py')
R=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(R)
NSPEC=importlib.util.spec_from_file_location('reference_normalized_witness',HERE/'normalize_witness.py')
N=importlib.util.module_from_spec(NSPEC);NSPEC.loader.exec_module(N)
DATA=R.ROOT/'output/stage2-search/multi-reference-2h-axion/completed/multi-reference-2h-20261017T0116'


class ReferenceEncounterTests(unittest.TestCase):
    def setUp(self):
        self.instance=json.loads((DATA/'instance.json').read_text());self.trace=json.loads((DATA/'result/cp-trace.json').read_text())
    def test_parked_future_reservation_permitted_but_original_unchanged(self):
        before=deepcopy(self.trace);result=R.audit(self.trace,self.instance)
        self.assertTrue(result['valid']);self.assertEqual(self.trace,before)
        entry=result['prebirth_planned_reservations'][0]
        self.assertEqual((entry['move_id'],entry['dispatch_start'],entry['birth_tick'],entry['pickup_tick'],entry['first_loaded_tick']),('move74',1382,1420,1480,1481))
    def test_pickup_before_real_birth_rejected(self):
        next(m for m in self.trace['moves'] if m['id']=='move74')['pickup_tick']=1400
        result=R.audit(self.trace,self.instance);self.assertFalse(result['valid'])
        self.assertIn('pickup_before_birth',{i['code'] for i in result['issues']})
    def test_loaded_leg_before_birth_or_producer_completion_rejected(self):
        move=next(m for m in self.trace['moves'] if m['id']=='move74');move['legs'][0]['start']=1400
        result=R.audit(self.trace,self.instance);self.assertFalse(result['valid'])
        self.assertIn('loaded_before_birth',{i['code'] for i in result['issues']})
    def test_unknown_cargo_and_redrawn_qa_stream_rejected(self):
        self.trace['moves'][0]['unit_id']='P99/pump/redraw'
        event=next(e for e in self.trace['events'] if e['type']=='qa_result');event['keyed_uniform']=.123456789
        result=R.audit(self.trace,self.instance);self.assertFalse(result['valid'])
        codes={i['code'] for i in result['issues']};self.assertIn('unknown_cargo_identity',codes);self.assertIn('immutable_qa_stream_key',codes)
    def test_normalized_copy_has_exactly_one_field_change_and_passes_stock_identity(self):
        from stage2.identity_audit import audit_trace
        before=deepcopy(self.trace);normalized,provenance=N.normalize(self.trace,self.instance)
        self.assertEqual(self.trace,before);self.assertEqual(len(N.structural_diff(before,normalized)),1)
        self.assertFalse(provenance['original_stock_identity']['valid']);self.assertTrue(audit_trace(normalized,self.instance)['valid'])
    def test_normalizer_rejects_real_prebirth_travel_and_changed_instance(self):
        move=next(m for m in self.trace['moves'] if m['id']=='move74')
        move['legs'].insert(0,dict(start=1382,end=1383,loaded=False,**{'from':'HUB_B','to':'A1'}))
        with self.assertRaisesRegex(ValueError,'zero-empty-leg'):N.normalize(self.trace,self.instance)
        changed=deepcopy(self.instance);changed['worker_travel_ticks']=3
        with self.assertRaises(ValueError):R.audit(self.trace,changed)


if __name__=='__main__':unittest.main()
