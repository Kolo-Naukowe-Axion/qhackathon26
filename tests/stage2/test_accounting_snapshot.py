import json,tempfile,unittest
from pathlib import Path
from stage2.accounting_snapshot import snapshot


class AccountingSnapshotTests(unittest.TestCase):
    def test_incomplete_final_evidence_cannot_mutate_live_ledger(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);ledger=root/'ledger.json';raw=root/'accounting.psv';report=root/'report';report.mkdir()
            original=json.dumps(dict(jobs=[dict(id=str(j),state='COMPLETED',cpus=32,allocated_cpu_seconds=32,reported_elapsed_seconds=1) for j in range(6117508,6117518)]))
            ledger.write_text(original);raw.write_text('6117517|unrelatedrawid|name|COMPLETED|2|32|cpu=32|00:00:00|0:0\n');(report/'all-groups.json').write_text('[]')
            with self.assertRaisesRegex(ValueError,'Complete ten-cohort'):snapshot(ledger,raw,report,root/'snapshot')
            self.assertEqual(ledger.read_text(),original)
            self.assertFalse((root/'snapshot-ledger.json').exists())

    def test_array_parent_and_child_cannot_both_be_counted(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);ledger=root/'ledger.json';raw=root/'raw';raw.write_text('')
            ledger.write_text(json.dumps(dict(jobs=[dict(id='123',state='COMPLETED'),dict(id='123_0',state='COMPLETED')])))
            with self.assertRaisesRegex(ValueError,'Double-counted'):snapshot(ledger,raw,root,root/'snapshot')


if __name__=='__main__':unittest.main()
