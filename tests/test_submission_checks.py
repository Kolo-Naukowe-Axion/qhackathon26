"""Adversarial checks of the submission's baseline eligibility verifier."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('submission_stage1',ROOT/'scripts/check-stage1.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class SubmissionChecks(unittest.TestCase):
    def copied_evidence(self,path):
        selection=json.loads((ROOT/'output/stage1-selected.json').read_text())
        files=['output/stage1-selected.json','schedule_2x2.json','schedule_3x3.json',
               'instances/instance_2x2.json','instances/instance_3x3.json']
        for directory in selection['selected_runs'].values():
            files += [directory+'/'+name for name in ['model.json','run.json','samples.json','schedule.json','raw-counts.json']]
        for name in files:
            dst=path/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dst)
        return selection

    def test_matching_but_forged_exports_fail_actual_sample_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);s=self.copied_evidence(root)
            for filename in ['schedule_3x3.json',s['selected_runs']['instance_3x3']+'/schedule.json']:
                p=root/filename;data=json.loads(p.read_text());data['schedule'][0]['end']+=1;p.write_text(json.dumps(data))
            with self.assertRaises(AssertionError):module.check_baselines(root)

    def test_measured_count_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);s=self.copied_evidence(root)
            p=root/s['selected_runs']['instance_2x2']/'raw-counts.json'
            data=json.loads(p.read_text());key=next(iter(data));data[key]+=1;p.write_text(json.dumps(data))
            with self.assertRaises(AssertionError):module.check_baselines(root)

    def test_model_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);s=self.copied_evidence(root)
            p=root/s['selected_runs']['instance_3x3']/'model.json'
            data=json.loads(p.read_text());data['linear'][0]+=1;p.write_text(json.dumps(data))
            with self.assertRaises(AssertionError):module.check_baselines(root)


if __name__=='__main__':unittest.main()
