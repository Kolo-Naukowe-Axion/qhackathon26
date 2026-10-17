import json
from pathlib import Path
import tempfile
import unittest

from stage2.selected_run import execute


class SelectedReplayTests(unittest.TestCase):
    def test_one_selected_context_retains_anchored_physical_evidence_and_refuses_reserved_tapes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);config=dict(orders=1,horizon=5760,profile='full')
            spec=dict(schema='stage2-selected-policy-spec.v1',configs=[config],
                selection_provenance=dict(data='DEVELOPMENT integration fixture'),
                methods=[dict(id='fixed',kind='static',weights=dict(wip_limit=3,lease_calibration=True),
                    selection_provenance=dict(data='DEVELOPMENT fixture'))])
            path=root/'selection.json';path.write_text(json.dumps(spec))
            result=execute(path,'fixed',config,0,root/'replay')
            self.assertTrue(result['valid'],result)
            trace=json.loads(Path(result['trace_path']).read_text())
            self.assertTrue(trace['validation']['valid'])
            with self.assertRaisesRegex(ValueError,'Development seed'):execute(path,'fixed',config,10000,root/'forbidden')
            with self.assertRaisesRegex(ValueError,'not selected'):execute(path,'fixed',dict(config,orders=2),0,root/'unknown')


if __name__=='__main__':unittest.main()
