import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from stage2 import final_eval as f,certify_evaluations as c


class MeasuredPrimaryCertificatesTests(unittest.TestCase):
    def test_unaudited_horizon_and_profile_rejected_before_evidence_is_read(self):
        for config in (dict(orders=12,horizon=480,profile='full'),
                       dict(orders=12,horizon=5760,profile='coarse')):
            with patch.object(c,'load_evidence') as load:
                with self.assertRaisesRegex(ValueError,'audited only'):
                    c.certify('absent','fixed',config,'unused')
                load.assert_not_called()

    def test_checked_full_witness_certifies_primary_and_false_bound_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);config=dict(orders=1,horizon=5760,profile='full')
            spec=dict(schema='stage2-selected-policy-spec.v1',configs=[config],actor_seeds=[91,92],
                selection_provenance=dict(data='DEVELOPMENT certificate integration'),
                methods=[dict(id='fixed',kind='static',weights=dict(wip_limit=3,lease_calibration=True),
                    selection_provenance=dict(data='DEVELOPMENT fixture'))])
            (root/'selection.json').write_text(json.dumps(spec))
            (root/'protocol.json').write_text(json.dumps(f.development_protocol([0])))
            f.freeze(root/'selection.json',root/'protocol.json',root/'manifest.json',development=True)
            f.evaluate(root/'manifest.json',root/'execution',workers=1)
            result=c.certify(root/'execution','fixed',config,root/'certificate')
            self.assertEqual(result['environment_tapes'],1)
            self.assertEqual(len(result['rows'][0]['actors']),2)
            self.assertEqual(result['weighted_primary_optimum_attainment'],1)
            self.assertEqual(result['weighted_mean_primary_gap_upper_bound'],0)
            path=root/'certificate'/result['rows'][0]['certificate_path']
            proof=json.loads(path.read_text());proof['unfulfilled_lower_bound']=1
            with patch.object(c,'certificate',return_value=proof):
                with self.assertRaisesRegex(ValueError,'witness violates'):c.certify(root/'execution','fixed',config,root/'contradiction')
            self.assertFalse((root/'contradiction/report.json').exists())


if __name__=='__main__':unittest.main()
