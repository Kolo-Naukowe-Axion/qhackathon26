"""Independent boundary/guard tests; no optimization or factory execution."""
from copy import deepcopy
from fractions import Fraction as Q
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('guarded_reference_union_bound',HERE/'bound.py')
B=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(B)
INSTANCE=B.ROOT/'output/stage2-search/multi-reference-2h-axion/payload/instance.json'


class UnionBoundTests(unittest.TestCase):
    def setUp(self):self.instance=json.loads(INSTANCE.read_text())
    def test_identical_four_pump_fixture_has1482_bound(self):
        r=B.certificate(self.instance)
        self.assertEqual(r['lower_bound_ticks'],1482);self.assertEqual(r['previous_buffer_bound_ticks'],1480)
        self.assertEqual(r['improvement_ticks'],2)
    def test_overlap_offsets_for_integer_and_fractional_starts(self):
        for i in range(0,400):
            r=B.overlap_compensation(Q(i,4))
            self.assertGreaterEqual(r['post_prefix_gap_lower_bound'],r['overlap'])
        self.assertEqual(B.overlap_compensation(63)['overlap'],1)
        self.assertEqual(B.overlap_compensation(64)['overlap'],0)
    def test_material_changes_are_rejected(self):
        for change in ('Fduration','walk','buffer','initialhall','WIP','QAattendance'):
            x=deepcopy(self.instance)
            if change=='Fduration':x['recipes']['flange'][0]['base_ticks']=59
            elif change=='walk':x['worker_travel_ticks']=3
            elif change=='buffer':next(m for m in x['machines'] if m['process']=='ASSEMBLY')['input_capacity']=4
            elif change=='initialhall':x['workers'][0]['initial_hall']='B'
            elif change=='WIP':x['initial_accepted_units']=[]
            else:x['attendance']['QA']['kind']='start'
            with self.subTest(change=change),self.assertRaises(ValueError):B.certificate(x)


if __name__=='__main__':unittest.main()
